"""RMSNorm fusa per gfx906 (Radeon VII): un kernel in avanti e uno all'indietro, compilati con hipRTC.

2S, 20 ott 2026. Sostituisce, nel solo processo (monkeypatch):
  - torch.nn.functional.rms_norm   (usato da nn.RMSNorm): in PyTorch 2.5 sono
    5 kernel (pow, mean, add, rsqrt, mul) piu' la moltiplicazione per il peso;
  - Qwen3_5RMSNorm.forward          (fp32 interno, peso (1 + w));
  - Qwen3_5RMSNormGated.forward     (norma, arrotondamento al tipo d'ingresso, x w x silu(gate)).

Tre modalita' dello stesso kernel (MODO):
  0  F.rms_norm:   y = x * rstd * w            (w facoltativo)
  1  Qwen:         y = (x * rstd) * (1 + w)    in fp32, poi al tipo d'ingresso
  2  Qwen gate:    h = T(x * rstd); y = T(T(w * h) * silu(gate))   con gli stessi arrotondamenti del modello
rstd = 1 / sqrt(mean(x^2) + eps), riduzione SEMPRE in fp32 (F.rms_norm di PyTorch in fp16 riduce nel
tipo d'ingresso: qui il risultato e' un po' piu' preciso, non identico al bit).

Inoltre LayerNorm (F.layer_norm, quindi nn.LayerNorm e i TransformerEncoderLayer in addestramento):
avanti e indietro fusi, gruppi di 8-64 corsie per riga (righe corte: piu' righe per onda), dgamma e
dbeta accumulati nei registri.

Disegno: un'onda (64 corsie) per riga, riduzione con __shfl_xor; ogni onda scorre piu' righe.
Il gradiente del peso si accumula per onda in un buffer [onde, D] e si somma con torch (gfx906 non ha
atomiche fp32 globali). Avanti e indietro, fp16 e fp32.

    import norme_gfx906; norme_gfx906.aggancia()   # F.rms_norm + F.layer_norm + Qwen3.5 se importato
"""
import ctypes
import os
import sys
import threading

import torch
import torch.nn.functional as F

vp = ctypes.c_void_p

SORGENTE = r"""
typedef _Float16 f16;
#if TIPO == 16
typedef _Float16 T;
#else
typedef float T;
#endif
__device__ inline float somma_onda(float v) {
    #pragma unroll
    for (int m = 32; m >= 1; m >>= 1) v += __shfl_xor(v, m, 64);
    return v;
}
__device__ inline float sigm(float g) { return 1.0f / (1.0f + __expf(-g)); }

/* avanti: righe = R, colonne = D (contigue). w: fp32 o NULL. gate: stesso tipo di x (MODO 2). */
extern "C" __global__ __launch_bounds__(256)
void rms_avanti(const T* __restrict__ x, const float* __restrict__ w, const T* __restrict__ gate,
                T* __restrict__ y, float* __restrict__ rstd_out, long long R, int D, float eps)
{
    const int corsia = threadIdx.x & 63;
    const long long onda = (long long)blockIdx.x * 4 + (threadIdx.x >> 6);
    const long long onde = (long long)gridDim.x * 4;
    for (long long r = onda; r < R; r += onde) {
        const T* xr = x + r * D;
        float s = 0.0f;
        for (int c = corsia; c < D; c += 64) { const float v = (float)xr[c]; s += v * v; }
        s = somma_onda(s);
        const float rs = 1.0f / __builtin_sqrtf(s / (float)D + eps);
        if (corsia == 0 && rstd_out) rstd_out[r] = rs;
        T* yr = y + r * D;
        for (int c = corsia; c < D; c += 64) {
            const float xn = (float)xr[c] * rs;
#if MODO == 0
            yr[c] = (T)(w ? xn * w[c] : xn);
#elif MODO == 1
            yr[c] = (T)(xn * (1.0f + w[c]));
#else
            const T h = (T)xn;                                   /* hidden_states.to(input_dtype) */
            const T wh = (T)((float)(T)w[c] * (float)h);         /* weight * h nel tipo d'ingresso */
            const float g = (float)gate[r * D + c];
            yr[c] = (T)((float)wh * (g * sigm(g)));             /* * silu(gate.float()), poi al tipo */
#endif
        }
    }
}

/* indietro: dx, dgate (MODO 2) e il gradiente del peso per onda in dw_parz[onda * D + c] */
extern "C" __global__ __launch_bounds__(256)
void rms_indietro(const T* __restrict__ x, const float* __restrict__ w, const T* __restrict__ gate,
                  const T* __restrict__ dy, const float* __restrict__ rstd,
                  T* __restrict__ dx, T* __restrict__ dgate, float* __restrict__ dw_parz,
                  long long R, int D)
{
    const int corsia = threadIdx.x & 63;
    const long long onda = (long long)blockIdx.x * 4 + (threadIdx.x >> 6);
    const long long onde = (long long)gridDim.x * 4;
    float* dwp = dw_parz ? dw_parz + onda * D : 0;
    if (dwp) for (int c = corsia; c < D; c += 64) dwp[c] = 0.0f;
    for (long long r = onda; r < R; r += onde) {
        const T* xr = x + r * D;
        const T* dyr = dy + r * D;
        const float rs = rstd[r];
        /* dh = dL/d(x_hat) */
        float s = 0.0f;
        for (int c = corsia; c < D; c += 64) {
            const float xn = (float)xr[c] * rs, d = (float)dyr[c];
#if MODO == 0
            const float dh = w ? d * w[c] : d;
#elif MODO == 1
            const float dh = d * (1.0f + w[c]);
#else
            const float g = (float)gate[r * D + c];
            const float dh = d * w[c] * g * sigm(g);
#endif
            s += dh * xn;
        }
        s = somma_onda(s) / (float)D;
        for (int c = corsia; c < D; c += 64) {
            const float xn = (float)xr[c] * rs, d = (float)dyr[c];
#if MODO == 0
            const float dh = w ? d * w[c] : d;
            if (dwp) dwp[c] += d * xn;
#elif MODO == 1
            const float dh = d * (1.0f + w[c]);
            if (dwp) dwp[c] += d * xn;
#else
            const float g = (float)gate[r * D + c], sg = sigm(g), si = g * sg;
            const float dh = d * w[c] * si;
            if (dwp) dwp[c] += d * xn * si;
            dgate[r * D + c] = (T)(d * w[c] * xn * sg * (1.0f + g * (1.0f - sg)));
#endif
            dx[r * D + c] = (T)(rs * (dh - xn * s));
        }
    }
}
"""

_lock = threading.Lock()
_funzioni = {}
_hip = None
_rtc = None


def _carica_rtc():
    global _rtc
    if _rtc is None:
        lib = os.path.join(os.path.dirname(torch.__file__), "lib")
        for p in (os.path.join(lib, "hiprtc07013.dll"), r"C:\rocm_5_7_expansion_pack\bin\hiprtc07013.dll"):
            if os.path.exists(p):
                k32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
                k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, vp, ctypes.c_ulong]
                k32.LoadLibraryExW.restype = vp
                _rtc = ctypes.CDLL(p, handle=k32.LoadLibraryExW(p, None, 0x8))
                break
        else:
            raise RuntimeError("nessuna hipRTC")
    return _rtc


def _funzione(nome, tipo, modo, sorgente=None, extra=()):
    global _hip
    chiave = (nome, tipo, modo, extra)
    with _lock:
        if chiave not in _funzioni:
            if _hip is None:
                _hip = ctypes.CDLL("amdhip64.dll")
                _hip.hipModuleLaunchKernel.argtypes = [vp] + [ctypes.c_uint] * 7 + [vp, vp, vp]
            opz = [b"--offload-arch=gfx906", b"-O3", f"-DTIPO={tipo}".encode(), f"-DMODO={modo}".encode()]
            opz += [f"-D{k}={v}".encode() for k, v in extra]
            f = _lancio.funzione((sorgente or SORGENTE), opz, nome, "norme.hip")   # cache su disco + un modulo per sorgente
            codice = mod = None
            _funzioni[chiave] = (f, codice, mod)
        return _funzioni[chiave][0]


sys.path.insert(0, r"C:\LaRuota_workspace\lancio_gfx906")
from lancio_gfx906 import Kernel, ptr  # noqa: E402
import lancio_gfx906 as _lancio  # noqa: E402
_KERNEL = {}


def _kernel(chiave, firma):
    k = _KERNEL.get(chiave)
    if k is None:
        k = _KERNEL[chiave] = Kernel(_funzione(*chiave), firma)
    return k


def _onde(R, avanti=False):
    """Onde. Avanti: una riga per onda (fino a 2^20): una RMSNorm fp32 da 120 mila righe x 192 con 960 onde
    faceva 1,5 ms, con 2400 1,15, con un'onda per riga 0,63 (torch 1,17; la sola copia 0,29). Indietro 960,
    perche' ogni onda scrive una riga di parziali [onde, D] per il gradiente del peso."""
    return max(1, min(int(R), (1 << 20) if avanti else 960))


def _lancia(f, onde, argomenti):
    args = (vp * len(argomenti))(*[ctypes.cast(ctypes.byref(a), vp) for a in argomenti])
    rc = _hip.hipModuleLaunchKernel(f, (onde + 3) // 4, 1, 1, 256, 1, 1, 0,
                                    vp(torch.cuda.current_stream().cuda_stream), args, None)
    if rc != 0:
        raise RuntimeError(f"hipModuleLaunchKernel rc={rc}")


def _p(t):
    return vp(t.data_ptr() if t is not None else 0)


def _avanti(x2, w, g2, modo, eps):
    R, D = x2.shape
    tipo = 16 if x2.dtype == torch.float16 else 32
    y = torch.empty_like(x2)
    rstd = torch.empty(R, device=x2.device, dtype=torch.float32)
    onde = _onde(R, avanti=True)
    _kernel(("rms_avanti", tipo, modo), "pppppqif")(
        (onde + 3) // 4, (ptr(x2), ptr(w), ptr(g2), ptr(y), ptr(rstd), R, D, eps))
    return y, rstd


def _indietro(x2, w, g2, dy2, rstd, modo, serve_dw):
    R, D = x2.shape
    tipo = 16 if x2.dtype == torch.float16 else 32
    dx = torch.empty_like(x2)
    dg = torch.empty_like(x2) if modo == 2 else None
    onde = _onde(R)
    dwp = torch.empty(((onde + 3) // 4) * 4, D, device=x2.device, dtype=torch.float32) if serve_dw else None
    _kernel(("rms_indietro", tipo, modo), "ppppppppqi")(
        (onde + 3) // 4, (ptr(x2), ptr(w), ptr(g2), ptr(dy2), ptr(rstd), ptr(dx), ptr(dg), ptr(dwp), R, D))
    dw = dwp[:onde].sum(0) if serve_dw else None
    return dx, dg, dw


class _Norma(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, w, g, modo, eps):
        D = x.shape[-1]
        x2 = x.reshape(-1, D).contiguous()
        g2 = g.reshape(-1, D).contiguous() if g is not None else None
        wf = w.float().contiguous() if w is not None else None
        y, rstd = _avanti(x2, wf, g2, modo, eps)
        ctx.save_for_backward(x2, wf, g2, rstd)
        ctx.modo, ctx.forma, ctx.w_dtype = modo, x.shape, (w.dtype if w is not None else None)
        return y.reshape(x.shape)

    @staticmethod
    def backward(ctx, dy):
        x2, wf, g2, rstd = ctx.saved_tensors
        D = x2.shape[-1]
        serve_dw = ctx.needs_input_grad[1]
        dx, dg, dw = _indietro(x2, wf, g2, dy.reshape(-1, D).contiguous().to(x2.dtype), rstd, ctx.modo, serve_dw)
        return (dx.reshape(ctx.forma), dw.to(ctx.w_dtype) if dw is not None else None,
                dg.reshape(ctx.forma) if dg is not None else None, None, None)


_ORIG_RMS = F.rms_norm
# Sotto questa dimensione il lancio da Python (autograd.Function + ctypes, ~100 us) costa piu' del lavoro:
# misurato 20 ott, LayerNorm 3.840 x 64 0,08 ms torch contro 0,24 fusa; 25.600 x 32 0,62 -> 0,29.
SOGLIA = int(os.environ.get("NORME_SOGLIA", str(512 * 1024)))


def rms_norm(input, normalized_shape, weight=None, eps=None):
    """Sostituto di F.rms_norm (normalizzazione sull'ultima dimensione, fp16/fp32 su GPU)."""
    if (not input.is_cuda or input.dtype not in (torch.float16, torch.float32) or input.numel() < SOGLIA
            or len(normalized_shape) != 1 or input.shape[-1] != normalized_shape[0]
            or (weight is not None and weight.shape != input.shape[-1:])):
        return _ORIG_RMS(input, normalized_shape, weight, eps)
    if eps is None:
        eps = torch.finfo(input.dtype).eps
    return _Norma.apply(input, weight, None, 0, float(eps))


def qwen_rmsnorm_forward(self, x):
    if not x.is_cuda or x.dtype not in (torch.float16, torch.float32):
        return _ORIG_QWEN[0](self, x)
    return _Norma.apply(x, self.weight, None, 1, float(self.eps))


def qwen_rmsnorm_gated_forward(self, hidden_states, gate=None):
    if (gate is None or not hidden_states.is_cuda or hidden_states.dtype not in (torch.float16, torch.float32)
            or gate.shape != hidden_states.shape):
        return _ORIG_QWEN[1](self, hidden_states, gate)
    return _Norma.apply(hidden_states, self.weight, gate.to(hidden_states.dtype), 2, float(self.variance_epsilon))


_ORIG_QWEN = [None, None]


# ---------------------------------------------------------------------------------------------------
# LayerNorm fusa (F.layer_norm sull'ultima dimensione): un kernel avanti, uno indietro.
# Un gruppo di L corsie (L = 8..64, potenza di 2 >= D fino a 64) segue una riga: con D = 32 un'onda
# fa due righe. Media e varianza in due passate in fp32. All'indietro dgamma e dbeta si accumulano nei
# registri del gruppo (CPL colonne per corsia) e si scrivono una volta: torch somma i parziali.
SORGENTE_LN = r"""
#if TIPO == 16
typedef _Float16 T;
#else
typedef float T;
#endif
__device__ inline float somma_gruppo(float v) {
    #pragma unroll
    for (int m = L / 2; m >= 1; m >>= 1) v += __shfl_xor(v, m, 64);
    return v;
}

extern "C" __global__ __launch_bounds__(256)
void ln_avanti(const T* __restrict__ x, const float* __restrict__ w, const float* __restrict__ b,
               T* __restrict__ y, float* __restrict__ media, float* __restrict__ rstd,
               long long R, int D, float eps)
{
    const int corsia = threadIdx.x & (L - 1);
    const long long gruppo = ((long long)blockIdx.x * 256 + threadIdx.x) / L;
    const long long gruppi = (long long)gridDim.x * (256 / L);
    for (long long r = gruppo; r < R; r += gruppi) {
        const T* xr = x + r * D;
        float v[CPL];
        float s = 0.0f;
        #pragma unroll
        for (int i = 0; i < CPL; ++i) {
            const int c = corsia + i * L;
            v[i] = c < D ? (float)xr[c] : 0.0f;
            s += v[i];
        }
        const float m = somma_gruppo(s) / (float)D;
        float q = 0.0f;
        #pragma unroll
        for (int i = 0; i < CPL; ++i) {
            const int c = corsia + i * L;
            const float d = c < D ? v[i] - m : 0.0f;
            q += d * d;
        }
        const float rs = 1.0f / __builtin_sqrtf(somma_gruppo(q) / (float)D + eps);
        if (corsia == 0) { if (media) media[r] = m; if (rstd) rstd[r] = rs; }
        T* yr = y + r * D;
        #pragma unroll
        for (int i = 0; i < CPL; ++i) {
            const int c = corsia + i * L;
            if (c < D) {
                float o = (v[i] - m) * rs;
                if (w) o *= w[c];
                if (b) o += b[c];
                yr[c] = (T)o;
            }
        }
    }
}

/* parz: [gruppi][2][D] (dgamma, dbeta) oppure NULL */
extern "C" __global__ __launch_bounds__(256)
void ln_indietro(const T* __restrict__ x, const float* __restrict__ w, const T* __restrict__ dy,
                 const float* __restrict__ media, const float* __restrict__ rstd,
                 T* __restrict__ dx, float* __restrict__ parz, long long R, int D)
{
    const int corsia = threadIdx.x & (L - 1);
    const long long gruppo = ((long long)blockIdx.x * 256 + threadIdx.x) / L;
    const long long gruppi = (long long)gridDim.x * (256 / L);
    float dwa[CPL], dba[CPL], wc[CPL];
    #pragma unroll
    for (int i = 0; i < CPL; ++i) {
        const int c = corsia + i * L;
        dwa[i] = 0.0f; dba[i] = 0.0f;
        wc[i] = (c < D) ? (w ? w[c] : 1.0f) : 0.0f;
    }
    for (long long r = gruppo; r < R; r += gruppi) {
        const T* xr = x + r * D;
        const T* dyr = dy + r * D;
        const float m = media[r], rs = rstd[r];
        float xh[CPL], g[CPL];
        float sa = 0.0f, sb = 0.0f;
        #pragma unroll
        for (int i = 0; i < CPL; ++i) {
            const int c = corsia + i * L;
            float d = 0.0f;
            xh[i] = 0.0f;
            if (c < D) { xh[i] = ((float)xr[c] - m) * rs; d = (float)dyr[c]; }
            dwa[i] += d * xh[i];
            dba[i] += d;
            g[i] = d * wc[i];
            sa += g[i];
            sb += g[i] * xh[i];
        }
        sa = somma_gruppo(sa) / (float)D;
        sb = somma_gruppo(sb) / (float)D;
        T* dxr = dx + r * D;
        #pragma unroll
        for (int i = 0; i < CPL; ++i) {
            const int c = corsia + i * L;
            if (c < D) dxr[c] = (T)(rs * (g[i] - sa - xh[i] * sb));
        }
    }
    if (parz) {
        float* pg = parz + gruppo * 2 * D;
        #pragma unroll
        for (int i = 0; i < CPL; ++i) {
            const int c = corsia + i * L;
            if (c < D) { pg[c] = dwa[i]; pg[D + c] = dba[i]; }
        }
    }
}
"""


def _ln_geometria(R, D, avanti=False):
    L = 8
    while L < min(D, 64):
        L *= 2
    cpl = (D + L - 1) // L
    if avanti:
        onde = 1 << 20                              # niente parziali: una riga per gruppo, tutte in volo
    else:
        onde = 960 if D <= 256 else 240             # meno parziali [gruppi, 2, D] con righe lunghe
    blocchi = max(1, min((R * L + 255) // 256, onde // 4))
    return L, cpl, blocchi


def _ln_lancia(nome, x2, L, cpl, blocchi, valori, firma):
    tipo = 16 if x2.dtype == torch.float16 else 32
    chiave = (nome, tipo, L, cpl)
    k = _KERNEL.get(chiave)
    if k is None:
        k = _KERNEL[chiave] = Kernel(_funzione(nome, tipo, 0, SORGENTE_LN, (("L", L), ("CPL", cpl))), firma)
    k(blocchi, valori)


class _LayerNorm(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, w, b, eps):
        D = x.shape[-1]
        x2 = x.reshape(-1, D).contiguous()
        R = x2.shape[0]
        wf = w.float().contiguous() if w is not None else None
        bf = b.float().contiguous() if b is not None else None
        y = torch.empty_like(x2)
        media = torch.empty(R, device=x2.device, dtype=torch.float32)
        rstd = torch.empty(R, device=x2.device, dtype=torch.float32)
        L, cpl, blocchi = _ln_geometria(R, D, avanti=True)
        _ln_lancia("ln_avanti", x2, L, cpl, blocchi,
                   (ptr(x2), ptr(wf), ptr(bf), ptr(y), ptr(media), ptr(rstd), R, D, eps), "ppppppqif")
        ctx.save_for_backward(x2, wf, media, rstd)
        ctx.forma = x.shape
        ctx.tipi = (w.dtype if w is not None else None, b.dtype if b is not None else None)
        return y.reshape(x.shape)

    @staticmethod
    def backward(ctx, dy):
        x2, wf, media, rstd = ctx.saved_tensors
        R, D = x2.shape
        L, cpl, blocchi = _ln_geometria(R, D)
        serve = ctx.needs_input_grad[1] or ctx.needs_input_grad[2]
        gruppi = blocchi * (256 // L)
        parz = torch.empty(gruppi, 2, D, device=x2.device, dtype=torch.float32) if serve else None
        dx = torch.empty_like(x2)
        dy2 = dy.reshape(-1, D).contiguous().to(x2.dtype)
        _ln_lancia("ln_indietro", x2, L, cpl, blocchi,
                   (ptr(x2), ptr(wf), ptr(dy2), ptr(media), ptr(rstd), ptr(dx), ptr(parz), R, D), "pppppppqi")
        dw = db = None
        if serve:
            somme = parz.sum(0)
            if ctx.needs_input_grad[1]:
                dw = somme[0].to(ctx.tipi[0])
            if ctx.needs_input_grad[2]:
                db = somme[1].to(ctx.tipi[1])
        return dx.reshape(ctx.forma), dw, db, None


_ORIG_LN = F.layer_norm


def layer_norm(input, normalized_shape, weight=None, bias=None, eps=1e-5):
    """Sostituto di F.layer_norm (ultima dimensione, fp16/fp32 su GPU, D <= 2048: oltre, troppi registri)."""
    if isinstance(normalized_shape, int):
        normalized_shape = (normalized_shape,)
    if (not isinstance(input, torch.Tensor) or not input.is_cuda or input.numel() < SOGLIA
            or len(normalized_shape) != 1 or input.shape[-1] != normalized_shape[0] or input.shape[-1] > 2048
            or (weight is not None and tuple(weight.shape) != tuple(normalized_shape))
            or (bias is not None and tuple(bias.shape) != tuple(normalized_shape))):
        return _ORIG_LN(input, normalized_shape, weight, bias, eps)
    if torch.is_autocast_enabled() and input.dtype in (torch.float16, torch.bfloat16):
        input = input.float()                       # layer_norm sta nella lista fp32 dell'autocast
    if input.dtype not in (torch.float16, torch.float32):
        return _ORIG_LN(input, normalized_shape, weight, bias, eps)
    return _LayerNorm.apply(input, weight, bias, float(eps))


def aggancia(funzionale=True, qwen=True, layernorm=True):
    """Monkeypatch nel solo processo. Restituisce quanto agganciato."""
    fatto = []
    if funzionale:
        F.rms_norm = rms_norm
        torch.nn.functional.rms_norm = rms_norm
        fatto.append("F.rms_norm")
    if layernorm:
        F.layer_norm = layer_norm
        torch.nn.functional.layer_norm = layer_norm
        fatto.append("F.layer_norm")
    if qwen:
        try:
            from transformers.models.qwen3_5 import modeling_qwen3_5 as mq
            if _ORIG_QWEN[0] is None:
                _ORIG_QWEN[0], _ORIG_QWEN[1] = mq.Qwen3_5RMSNorm.forward, mq.Qwen3_5RMSNormGated.forward
            mq.Qwen3_5RMSNorm.forward = qwen_rmsnorm_forward
            mq.Qwen3_5RMSNormGated.forward = qwen_rmsnorm_gated_forward
            fatto.append("Qwen3_5RMSNorm, Qwen3_5RMSNormGated")
        except ImportError:
            pass
    return fatto

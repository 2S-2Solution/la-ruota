"""Adattatore LoRA fuso per gfx906: y = base(x) + scala * B(A(x)), A e B in fp32, base e x in fp16.

2S, 20 ott 2026. La forma "base fp16 congelata + adattatori fp32" (prova_lora_4b_reale.py,
classe Lora) in torch costa, per ogni modulo: x.float() [N, Din] fp32, due GEMM fp32 strette, * scala,
.to(fp16), somma; all'indietro altre copie fp32 [N, Dout] e [N, Din] e due conversioni. Qui:
  avanti:   y = base(x)                (GEMM rocBLAS fp16, come prima)
            u = x A^T                  kernel "giu": legge x fp16, accumula fp32           [N, r]
            y += scala * u B^T         kernel "su_somma": dentro y, un arrotondamento solo
  indietro: dx = dy W                  (GEMM rocBLAS fp16)
            g = scala * dy B           "giu" su dy                                          [N, r]
            dB = scala * dy^T u        kernel "rid" (parziali per pezzi di righe, somma torch)
            dA = g^T x                 "rid"
            dx += g A                  "su_somma" dentro dx
Niente tensori fp32 grandi; accumulo sempre in fp32 come l'originale. Non identico al bit: y + d si
somma in fp32 e si arrotonda una volta (l'originale arrotonda d a fp16 e poi la somma).

    import lora_gfx906
    y = lora_gfx906.lora(x, base.weight, base.bias, A, B, scala)          # uso diretto
    lora_gfx906.aggancia_classe(Lora)   # classi con .base (Linear congelato), .a, .b (Linear fp32), .scala
Rango: potenza di 2 fino a 64. Peso base congelato (altrimenti ricade sull'originale).
"""
import ctypes
import os
import sys
import threading

import torch
import torch.nn.functional as F

vp = ctypes.c_void_p

SORGENTE = r"""
#if TIPO == 16
typedef _Float16 T;
#else
typedef float T;
#endif
#define RIGHE (64 / R)

/* out[n, k] = scala * sum_c X[n, c] M[k, c]; M con passi (smk, smc). Un'onda per RIGHE righe; le
   RIGHE * R = 64 somme si riducono con uno scambio a meta' (reduce-scatter): la corsia j tiene la j-esima. */
extern "C" __global__ __launch_bounds__(256)
void giu(const T* __restrict__ X, const float* __restrict__ M, float* __restrict__ out,
         long long N, int K, long long smk, long long smc, float scala)
{
    const int corsia = threadIdx.x & 63;
    const long long n0 = ((long long)blockIdx.x * 4 + (threadIdx.x >> 6)) * RIGHE;
    if (n0 >= N) return;
    float v[64];
    #pragma unroll
    for (int i = 0; i < 64; ++i) v[i] = 0.0f;
    for (int c = corsia; c < K; c += 64) {
        float m[R];
        #pragma unroll
        for (int k = 0; k < R; ++k) m[k] = M[k * smk + c * smc];
        #pragma unroll
        for (int i = 0; i < RIGHE; ++i) {
            const long long n = n0 + i;
            const float x = n < N ? (float)X[n * K + c] : 0.0f;
            #pragma unroll
            for (int k = 0; k < R; ++k) v[i * R + k] += x * m[k];
        }
    }
    #pragma unroll
    for (int meta = 32; meta >= 1; meta >>= 1) {
        const bool alto = (corsia & meta) != 0;
        #pragma unroll
        for (int i = 0; i < meta; ++i) {
            const float a = v[i], b = v[i + meta];
            const float tieni = alto ? b : a, manda = alto ? a : b;
            v[i] = tieni + __shfl_xor(manda, meta, 64);
        }
    }
    const long long n = n0 + corsia / R;
    if (n < N) out[n * R + (corsia % R)] = scala * v[0];
}

/* Y[n, o] += scala * sum_k U[n, k] M[o, k]; M con passi (smo, smk). Blocco: 256 colonne x RB righe. */
#define RB 16
extern "C" __global__ __launch_bounds__(256)
void su_somma(T* __restrict__ Y, const float* __restrict__ U, const float* __restrict__ M,
              long long N, int O, long long smo, long long smk, float scala)
{
    const int o = blockIdx.x * 256 + threadIdx.x;
    const long long n0 = (long long)blockIdx.y * RB;
    if (o >= O) return;
    float m[R];
    #pragma unroll
    for (int k = 0; k < R; ++k) m[k] = M[o * smo + k * smk];
    #pragma unroll 4
    for (int i = 0; i < RB; ++i) {
        const long long n = n0 + i;
        if (n >= N) break;
        float s = 0.0f;
        #pragma unroll
        for (int k = 0; k < R; ++k) s += U[n * R + k] * m[k];
        T* y = Y + n * O + o;
        *y = (T)((float)*y + scala * s);
    }
}

/* parz[pezzo, k, c] = sum_{n nel pezzo} U[n, k] X[n, c] */
extern "C" __global__ __launch_bounds__(256)
void rid(const T* __restrict__ X, const float* __restrict__ U, float* __restrict__ parz,
         long long N, int K, int righe_pezzo)
{
    const int c = blockIdx.x * 256 + threadIdx.x;
    const int pezzo = blockIdx.y;
    if (c >= K) return;
    const long long n0 = (long long)pezzo * righe_pezzo;
    const long long n1 = n0 + righe_pezzo < N ? n0 + righe_pezzo : N;
    float acc[R];
    #pragma unroll
    for (int k = 0; k < R; ++k) acc[k] = 0.0f;
    for (long long n = n0; n < n1; ++n) {
        const float x = (float)X[n * K + c];
        #pragma unroll
        for (int k = 0; k < R; ++k) acc[k] += U[n * R + k] * x;
    }
    float* p = parz + ((long long)pezzo * R) * K + c;
    #pragma unroll
    for (int k = 0; k < R; ++k) p[(long long)k * K] = acc[k];
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


def _funzione(nome, tipo, R):
    global _hip
    chiave = (nome, tipo, R)
    with _lock:
        if chiave not in _funzioni:
            if _hip is None:
                _hip = ctypes.CDLL("amdhip64.dll")
                _hip.hipModuleLaunchKernel.argtypes = [vp] + [ctypes.c_uint] * 7 + [vp, vp, vp]
            rtc = _carica_rtc()
            prog = vp()
            assert rtc.hiprtcCreateProgram(ctypes.byref(prog), SORGENTE.encode(), b"lora.hip", 0, None, None) == 0
            opz = [b"--offload-arch=gfx906", b"-O3", f"-DTIPO={tipo}".encode(), f"-DR={R}".encode()]
            if rtc.hiprtcCompileProgram(prog, len(opz), (ctypes.c_char_p * len(opz))(*opz)) != 0:
                n = ctypes.c_size_t(); rtc.hiprtcGetProgramLogSize(prog, ctypes.byref(n))
                b = ctypes.create_string_buffer(n.value); rtc.hiprtcGetProgramLog(prog, b)
                raise RuntimeError(b.value.decode(errors="replace"))
            n = ctypes.c_size_t(); rtc.hiprtcGetCodeSize(prog, ctypes.byref(n))
            codice = ctypes.create_string_buffer(n.value); rtc.hiprtcGetCode(prog, codice)
            mod, f = vp(), vp()
            assert _hip.hipModuleLoadData(ctypes.byref(mod), codice) == 0
            assert _hip.hipModuleGetFunction(ctypes.byref(f), mod, nome.encode()) == 0
            _funzioni[chiave] = (f, codice, mod)
        return _funzioni[chiave][0]


def _lancia(nome, X, R, griglia, argomenti):
    f = _funzione(nome, 16 if X.dtype == torch.float16 else 32, R)
    a = (vp * len(argomenti))(*[ctypes.cast(ctypes.byref(v), vp) for v in argomenti])
    rc = _hip.hipModuleLaunchKernel(f, griglia[0], griglia[1], 1, 256, 1, 1, 0,
                                    vp(torch.cuda.current_stream().cuda_stream), a, None)
    if rc != 0:
        raise RuntimeError(f"hipModuleLaunchKernel rc={rc}")


sys.path.insert(0, r"C:\LaRuota_workspace\lancio_gfx906")
from lancio_gfx906 import Kernel  # noqa: E402
_KERNEL = {}


def _kernel(nome, X, R, firma):
    tipo = 16 if X.dtype == torch.float16 else 32
    chiave = (nome, tipo, R)
    k = _KERNEL.get(chiave)
    if k is None:
        k = _KERNEL[chiave] = Kernel(_funzione(nome, tipo, R), firma)
    return k


def _p(t):
    return vp(t.data_ptr())


def giu(X, M, smk, smc, scala, R):
    """out[N, R] = scala * X M^T, M[k, c] all'indirizzo k*smk + c*smc."""
    N, K = X.shape
    out = torch.empty(N, R, device=X.device, dtype=torch.float32)
    onde = (N + (64 // R) - 1) // (64 // R)
    _kernel("giu", X, R, "pppqiqqf")(((onde + 3) // 4, 1, 1),
                                      (X.data_ptr(), M.data_ptr(), out.data_ptr(), N, K, smk, smc, scala))
    return out


def su_somma(Y, U, M, smo, smk, scala):
    """Y[N, O] += scala * U M^T (in posto), M[o, k] all'indirizzo o*smo + k*smk."""
    N, O = Y.shape
    R = U.shape[1]
    _kernel("su_somma", Y, R, "pppqiqqf")(((O + 255) // 256, (N + 15) // 16, 1),
                                           (Y.data_ptr(), U.data_ptr(), M.data_ptr(), N, O, smo, smk, scala))


def rid(X, U):
    """[R, K] = U^T X, con parziali per pezzi di righe sommati da torch."""
    N, K = X.shape
    R = U.shape[1]
    blocchi_c = (K + 255) // 256
    pezzi = max(1, min((N + 15) // 16, (240 + blocchi_c - 1) // blocchi_c))
    righe = (N + pezzi - 1) // pezzi
    pezzi = (N + righe - 1) // righe
    parz = torch.empty(pezzi, R, K, device=X.device, dtype=torch.float32)
    _kernel("rid", X, R, "pppqii")((blocchi_c, pezzi, 1), (X.data_ptr(), U.data_ptr(), parz.data_ptr(), N, K, righe))
    return parz.sum(0) if pezzi > 1 else parz[0]


class _Lora(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, W, bias, A, B, scala):
        Din = x.shape[-1]
        x2 = x.reshape(-1, Din).to(W.dtype).contiguous()
        A, B = A.contiguous(), B.contiguous()
        R = A.shape[0]
        with torch.autocast("cuda", enabled=False):
            y = F.linear(x2, W, bias)
        u = giu(x2, A, Din, 1, 1.0, R)                       # M = A [R, Din]
        su_somma(y, u, B, R, 1, scala)                       # M = B [Dout, R]
        ctx.save_for_backward(x2, W, A, B, u)
        ctx.scala, ctx.forma, ctx.tipo_x = scala, x.shape, x.dtype
        return y.reshape(*x.shape[:-1], W.shape[0])

    @staticmethod
    def backward(ctx, dy):
        x2, W, A, B, u = ctx.saved_tensors
        scala = ctx.scala
        Dout, R = B.shape
        dy2 = dy.reshape(-1, Dout).to(W.dtype).contiguous()
        g = giu(dy2, B, 1, R, scala, R)                      # M[k, o] = B[o, k]
        dA = rid(x2, g) if ctx.needs_input_grad[3] else None
        dB = (rid(dy2, u) * scala).t().contiguous() if ctx.needs_input_grad[4] else None
        dx = None
        if ctx.needs_input_grad[0]:
            with torch.autocast("cuda", enabled=False):
                dx = dy2 @ W
            su_somma(dx, g, A, 1, A.shape[1], 1.0)           # M[c, k] = A[k, c]
            dx = dx.reshape(ctx.forma).to(ctx.tipo_x)
        return dx, None, None, dA, dB, None


def supportato(x, W, A, B):
    R = A.shape[0]
    return (x.is_cuda and W.is_cuda and not W.requires_grad and W.dtype in (torch.float16, torch.float32)
            and x.dtype in (torch.float16, torch.float32) and A.dtype == torch.float32 and B.dtype == torch.float32
            and R in (1, 2, 4, 8, 16, 32, 64) and A.dim() == 2 and B.shape[1] == R and x.numel() > 0)


def lora(x, W, bias, A, B, scala):
    """y = F.linear(x, W, bias) + scala * (x A^T) B^T, uscita nel tipo di W (come l'autocast fp16)."""
    return _Lora.apply(x, W, bias, A, B, float(scala))


_ORIG = {}


def aggancia_classe(cls):
    """Per moduli con .base (Linear congelato), .a e .b (Linear senza bias, fp32), .scala."""
    if cls in _ORIG:
        return
    orig = cls.forward

    def forward(self, x):
        W, A, B = self.base.weight, self.a.weight, self.b.weight
        if (self.a.bias is None and self.b.bias is None and supportato(x, W, A, B)
                and (self.base.bias is None or not self.base.bias.requires_grad)):
            return lora(x, W, self.base.bias, A, B, self.scala)
        return orig(self, x)

    forward.__wrapped__ = orig
    _ORIG[cls] = orig
    cls.forward = forward


def sgancia():
    for cls, orig in _ORIG.items():
        cls.forward = orig
    _ORIG.clear()

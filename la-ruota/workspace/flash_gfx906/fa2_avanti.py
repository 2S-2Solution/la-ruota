"""Flash attention per gfx906 — seconda versione dell'avanti, a TESSERE.

2S, 17 ott 2026. Modulo autonomo, kernel compilato a runtime con hipRTC.

PERCHE' UNA SECONDA VERSIONE
----------------------------
Il prototipo (fa_avanti.py) dava a ogni thread una riga di query intera: ogni
valore di K e V letto dalla memoria condivisa serviva a UNA sola istruzione.
Per D=128 una chiave costa a un'onda 16 letture ds_read_b128 (~128 cicli di LDS)
contro 64 v_dot2 (256 cicli di calcolo): con quattro onde per CU la LDS e' il
collo anche senza sversamenti. Dividere la riga su due corsie non cambia il
rapporto.

IL DISEGNO (come un GEMM a registri)
-----------------------------------
- Workgroup di 256 thread (4 onde) per 64 righe di query; blocchi di 64 chiavi.
- Q del blocco resta nella LDS per tutto il kernel; K e V passano a blocchi.
- S = Q·Kᵀ: il thread (tr, tc) calcola 4 righe {tr + 16i} × 4 chiavi {tc + 16j}.
  Ogni lettura b128 dalla LDS serve 16 v_dot2: riuso 4x rispetto al prototipo.
- Softmax online per riga: le 16 corsie che condividono una riga sono contigue
  nell'onda, massimo e somma si chiudono con 4 scambi __shfl_xor.
- P va nella LDS in fp16, come in FlashAttention-2 (P e' in [0, 1]).
- O = P·V anche con v_dot2: V e' salvata TRASPOSTA A COPPIE di chiavi,
  Vt[k/2][d] = (V[k][d], V[k+1][d]), cosi' il prodotto lungo le chiavi e' un
  dot2 con accumulo fp32. Lo stesso thread tiene le stesse 4 righe sia in S sia
  in O: la riscalatura dell'accumulatore resta locale.
- Esponenziali in base 2 con la scala gia' moltiplicata per log2(e).

Layout: Q, K, V, O contigui [B, H, S, D], fp16. D in {64, 128}.
"""
import ctypes
import os
import threading

import torch

vp = ctypes.c_void_p

SORGENTE = r"""
typedef _Float16 f16;
typedef _Float16 h2 __attribute__((ext_vector_type(2)));
typedef unsigned int u4 __attribute__((ext_vector_type(4)));

#define BR 64
#define BC 64
#define NT 256
#define D2 (HEAD_DIM / 2)
#define QSTR (D2 + 4)            /* passo delle righe di Q e K nella LDS, in dword */
#define VSTR (HEAD_DIM + 4)      /* passo di Vt, in dword (un h2 per d) */
#define PSTR (BC / 2 + 4)        /* passo di P, in dword (un h2 per coppia di chiavi) */
#define DU (HEAD_DIM / 16)       /* colonne di O per thread */

__device__ inline h2 come_h2(unsigned int x) { return __builtin_bit_cast(h2, x); }
__device__ inline unsigned int come_u(h2 x) { return __builtin_bit_cast(unsigned int, x); }

extern "C" __global__ __launch_bounds__(NT)
void fa2_avanti(const unsigned int* __restrict__ Q, const unsigned int* __restrict__ K,
                const unsigned int* __restrict__ V, f16* __restrict__ O,
                int S, float scala_log2, int causale, float* __restrict__ LSE2)
{
    __shared__ unsigned int Qs[BR * QSTR];
    __shared__ unsigned int Ks[BC * QSTR];
    __shared__ unsigned int Vt[(BC / 2) * VSTR];
    __shared__ unsigned int Ps[BR * PSTR];

    const int t = threadIdx.x;
    const int tr = t >> 4, tc = t & 15;
    const int bh = blockIdx.y;
    const int r0 = blockIdx.x * BR;
    const size_t base = (size_t)bh * S * D2;     /* in dword (h2) */

    /* Q del blocco nella LDS, a u4 (4 h2) */
    for (int idx = t; idx < BR * D2 / 4; idx += NT) {
        const int riga = idx / (D2 / 4), col = (idx - riga * (D2 / 4)) * 4;
        u4 x = {0u, 0u, 0u, 0u};
        if (r0 + riga < S) x = *(const u4*)(Q + base + (size_t)(r0 + riga) * D2 + col);
        *(u4*)(Qs + riga * QSTR + col) = x;
    }

    float o[4][DU];
    float m[4], l[4];
    #pragma unroll
    for (int i = 0; i < 4; ++i) {
        m[i] = -__builtin_inff(); l[i] = 0.0f;
        #pragma unroll
        for (int u = 0; u < DU; ++u) o[i][u] = 0.0f;
    }

    int n_blocchi = (S + BC - 1) / BC;
    if (causale) {
        const int ultimo = (r0 + BR - 1) / BC + 1;
        n_blocchi = n_blocchi < ultimo ? n_blocchi : ultimo;
    }

    for (int b = 0; b < n_blocchi; ++b) {
        const int c0 = b * BC;
        __syncthreads();                         /* il blocco precedente ha finito con Ks, Vt, Ps */
        for (int idx = t; idx < BC * D2 / 4; idx += NT) {
            const int riga = idx / (D2 / 4), col = (idx - riga * (D2 / 4)) * 4;
            u4 x = {0u, 0u, 0u, 0u};
            if (c0 + riga < S) x = *(const u4*)(K + base + (size_t)(c0 + riga) * D2 + col);
            *(u4*)(Ks + riga * QSTR + col) = x;
        }
        for (int idx = t; idx < (BC / 2) * D2; idx += NT) {
            const int kp = idx / D2, c = idx - kp * D2;
            const int k = c0 + 2 * kp;
            const h2 zero = {(f16)0.0f, (f16)0.0f};
            const h2 a = (k < S) ? come_h2(V[base + (size_t)k * D2 + c]) : zero;
            const h2 z = (k + 1 < S) ? come_h2(V[base + (size_t)(k + 1) * D2 + c]) : zero;
            const h2 lo = {a.x, z.x}, hi = {a.y, z.y};
            Vt[kp * VSTR + 2 * c] = come_u(lo);
            Vt[kp * VSTR + 2 * c + 1] = come_u(hi);
        }
        __syncthreads();

        /* S = Q K^T sulla tessera 4x4 */
        float s[4][4];
        #pragma unroll
        for (int i = 0; i < 4; ++i)
            #pragma unroll
            for (int j = 0; j < 4; ++j) s[i][j] = 0.0f;
        #pragma unroll 2
        for (int c = 0; c < D2; c += 4) {
            u4 qa[4], kb[4];
            #pragma unroll
            for (int i = 0; i < 4; ++i) qa[i] = *(const u4*)(Qs + (tr + 16 * i) * QSTR + c);
            #pragma unroll
            for (int j = 0; j < 4; ++j) kb[j] = *(const u4*)(Ks + (tc + 16 * j) * QSTR + c);
            #pragma unroll
            for (int i = 0; i < 4; ++i)
                #pragma unroll
                for (int j = 0; j < 4; ++j) {
                    s[i][j] = __builtin_amdgcn_fdot2(come_h2(qa[i].x), come_h2(kb[j].x), s[i][j], false);
                    s[i][j] = __builtin_amdgcn_fdot2(come_h2(qa[i].y), come_h2(kb[j].y), s[i][j], false);
                    s[i][j] = __builtin_amdgcn_fdot2(come_h2(qa[i].z), come_h2(kb[j].z), s[i][j], false);
                    s[i][j] = __builtin_amdgcn_fdot2(come_h2(qa[i].w), come_h2(kb[j].w), s[i][j], false);
                }
        }

        /* softmax online; P in fp16 nella LDS */
        f16* Ph = (f16*)Ps;
        #pragma unroll
        for (int i = 0; i < 4; ++i) {
            const int r = r0 + tr + 16 * i;
            float mx = -__builtin_inff();
            #pragma unroll
            for (int j = 0; j < 4; ++j) {
                const int c = c0 + tc + 16 * j;
                const bool valido = (c < S) && (!causale || c <= r);
                s[i][j] = valido ? s[i][j] * scala_log2 : -__builtin_inff();
                mx = fmaxf(mx, s[i][j]);
            }
            mx = fmaxf(mx, __shfl_xor(mx, 1, 16));
            mx = fmaxf(mx, __shfl_xor(mx, 2, 16));
            mx = fmaxf(mx, __shfl_xor(mx, 4, 16));
            mx = fmaxf(mx, __shfl_xor(mx, 8, 16));
            const float mn = fmaxf(m[i], mx);
            float corr = 1.0f, somma = 0.0f;
            if (mn != -__builtin_inff()) {
                corr = __builtin_amdgcn_exp2f(m[i] - mn);      /* m = -inf -> 0 */
                #pragma unroll
                for (int j = 0; j < 4; ++j) {
                    const float p = __builtin_amdgcn_exp2f(s[i][j] - mn);
                    s[i][j] = p;
                    somma += p;
                }
            } else {
                #pragma unroll
                for (int j = 0; j < 4; ++j) s[i][j] = 0.0f;
            }
            somma += __shfl_xor(somma, 1, 16);
            somma += __shfl_xor(somma, 2, 16);
            somma += __shfl_xor(somma, 4, 16);
            somma += __shfl_xor(somma, 8, 16);
            l[i] = l[i] * corr + somma;
            m[i] = mn;
            #pragma unroll
            for (int u = 0; u < DU; ++u) o[i][u] *= corr;
            #pragma unroll
            for (int j = 0; j < 4; ++j) Ph[(tr + 16 * i) * (2 * PSTR) + tc + 16 * j] = (f16)s[i][j];
        }
        __syncthreads();

        /* O += P V, dot2 lungo le coppie di chiavi */
        #pragma unroll 2
        for (int kp4 = 0; kp4 < BC / 2; kp4 += 4) {
            u4 pa[4];
            #pragma unroll
            for (int i = 0; i < 4; ++i) pa[i] = *(const u4*)(Ps + (tr + 16 * i) * PSTR + kp4);
            #pragma unroll
            for (int e = 0; e < 4; ++e) {
                #pragma unroll
                for (int u = 0; u < DU; ++u) {
                    const h2 vv = come_h2(Vt[(kp4 + e) * VSTR + tc + 16 * u]);
                    #pragma unroll
                    for (int i = 0; i < 4; ++i) {
                        const unsigned int pe = e == 0 ? pa[i].x : e == 1 ? pa[i].y : e == 2 ? pa[i].z : pa[i].w;
                        o[i][u] = __builtin_amdgcn_fdot2(come_h2(pe), vv, o[i][u], false);
                    }
                }
            }
        }
    }

    #pragma unroll
    for (int i = 0; i < 4; ++i) {
        const int r = r0 + tr + 16 * i;
        if (r < S) {
            const float inv = l[i] > 0.0f ? 1.0f / l[i] : 0.0f;
            f16* riga = O + ((size_t)bh * S + r) * HEAD_DIM;
            #pragma unroll
            for (int u = 0; u < DU; ++u) riga[tc + 16 * u] = (f16)(o[i][u] * inv);
            /* logsumexp in base 2 (scala gia' moltiplicata per log2 e): serve all'indietro */
            if (LSE2 && tc == 0) LSE2[(size_t)bh * S + r] = m[i] + __log2f(l[i]);
        }
    }
}
"""


def _percorsi_hiprtc():
    lib = os.path.join(os.path.dirname(torch.__file__), "lib")
    return [os.path.join(lib, "hiprtc07013.dll"),
            r"C:\rocm_5_7_expansion_pack\bin\hiprtc07013.dll",
            r"C:\Program Files\AMD\ROCm\5.7\bin\hiprtc0507.dll"]


def _carica(percorso):
    k32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
    k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, vp, ctypes.c_ulong]
    k32.LoadLibraryExW.restype = vp
    h = k32.LoadLibraryExW(percorso, None, 0x8)
    if not h:
        raise OSError(f"{percorso}: errore {ctypes.get_last_error()}")
    return ctypes.CDLL(percorso, handle=h)


_lock = threading.Lock()
_funzioni = {}
_hip = None


def compila(head_dim, extra=(), sorgente=None):
    """Restituisce il code object (buffer ctypes)."""
    rtc = None
    for p in _percorsi_hiprtc():
        if os.path.exists(p):
            rtc = _carica(p)
            break
    if rtc is None:
        raise RuntimeError("nessuna hipRTC trovata")
    prog = vp()
    src = (sorgente or SORGENTE).encode()
    assert rtc.hiprtcCreateProgram(ctypes.byref(prog), src, b"fa2.hip", 0, None, None) == 0
    opz = [b"--offload-arch=gfx906", b"-mcode-object-version=5", b"-O3",
           f"-DHEAD_DIM={head_dim}".encode()] + [x.encode() for x in extra]
    if rtc.hiprtcCompileProgram(prog, len(opz), (ctypes.c_char_p * len(opz))(*opz)) != 0:
        n = ctypes.c_size_t()
        rtc.hiprtcGetProgramLogSize(prog, ctypes.byref(n))
        b = ctypes.create_string_buffer(n.value)
        rtc.hiprtcGetProgramLog(prog, b)
        raise RuntimeError(b.value.decode(errors="replace"))
    n = ctypes.c_size_t()
    rtc.hiprtcGetCodeSize(prog, ctypes.byref(n))
    codice = ctypes.create_string_buffer(n.value)
    rtc.hiprtcGetCode(prog, codice)
    return codice


def _funzione(head_dim, extra=()):
    global _hip
    with _lock:
        chiave = (head_dim, tuple(extra))
        if chiave in _funzioni:
            return _funzioni[chiave]
        if _hip is None:
            _hip = ctypes.CDLL("amdhip64.dll")
            _hip.hipModuleLaunchKernel.argtypes = [
                vp, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                ctypes.c_uint, vp, vp, vp]
        codice = compila(head_dim, extra)
        mod, f = vp(), vp()
        assert _hip.hipModuleLoadData(ctypes.byref(mod), codice) == 0
        assert _hip.hipModuleGetFunction(ctypes.byref(f), mod, b"fa2_avanti") == 0
        _funzioni[chiave] = (f, codice, mod)
        return _funzioni[chiave]


def flash_avanti(q, k, v, is_causal=False, scale=None, extra=(), lse=False):
    """q, k, v: [B, H, S, D] fp16 su GPU, stessa forma. Restituisce O, oppure (O, LSE2) con
    lse=True: LSE2 [B, H, S] fp32 e' il logsumexp per riga in BASE 2 della scala per log2(e),
    cioe' logsumexp naturale = LSE2 * ln 2."""
    assert q.dtype == torch.float16 and q.is_cuda
    B, H, S, D = q.shape
    assert k.shape == q.shape and v.shape == q.shape, "Q, K, V della stessa forma"
    assert D in (64, 128), "head_dim 64 o 128"
    q, k, v = q.contiguous(), k.contiguous(), v.contiguous()
    o = torch.empty_like(q)
    lse2 = torch.empty(B, H, S, device=q.device, dtype=torch.float32) if lse else None
    f = _funzione(D, extra)[0]
    scala = (scale if scale is not None else D ** -0.5) * 1.4426950408889634
    a = [vp(q.data_ptr()), vp(k.data_ptr()), vp(v.data_ptr()), vp(o.data_ptr()),
         ctypes.c_int(S), ctypes.c_float(scala), ctypes.c_int(1 if is_causal else 0),
         vp(lse2.data_ptr() if lse else 0)]
    args = (vp * len(a))(*[ctypes.cast(ctypes.byref(x), vp) for x in a])
    stream = torch.cuda.current_stream().cuda_stream
    rc = _hip.hipModuleLaunchKernel(f, (S + 63) // 64, B * H, 1, 256, 1, 1, 0, vp(stream), args, None)
    if rc != 0:
        raise RuntimeError(f"hipModuleLaunchKernel rc={rc}")
    return (o, lse2) if lse else o

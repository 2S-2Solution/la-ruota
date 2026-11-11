"""Flash attention per gfx906 — PROTOTIPO del solo passo in avanti.

Studio di fattibilita' (rocm-marconi, 17 ott 2026). Non tocca la ruota: e' un
modulo autonomo, kernel compilato a runtime con hipRTC come la DCNv2.

PERCHE' UN KERNEL NOSTRO
------------------------
Su gfx906 non c'e' niente di pronto:
  - aotriton supporta solo gfx90a, gfx942, gfx950, gfx11, gfx12;
  - Composable Kernel ha la FMHA, ma il suo warp-gemm esiste solo in versione
    MFMA / SMFMAC / WMMA: tutte istruzioni matriciali che gfx906 non ha.

IL DISEGNO
----------
- Un workgroup di 64 thread (un wave) per 64 righe di query di una testa: ogni
  thread tiene la SUA riga di Q nei registri (fp16 a coppie) e il suo
  accumulatore di uscita (fp32).
- Chiavi e valori passano a blocchi di 64 righe in memoria condivisa; tutti i
  thread leggono la stessa riga di K/V nello stesso istante: e' una lettura in
  broadcast, la piu' economica che la LDS conosca.
- q.k con `v_dot2_f32_f16` (__builtin_amdgcn_fdot2): due prodotti fp16 per
  istruzione, accumulo in fp32. E' l'istruzione fp16 che gfx906 ha davvero.
- Softmax ONLINE (FlashAttention-2): massimo e somma correnti per riga. La
  riscalatura dell'accumulatore costa D moltiplicazioni: la si fa una volta ogni
  16 chiavi, non a ogni chiave.
- Causale: i blocchi di chiavi interamente sopra la diagonale non si caricano.

Layout: Q, K, V, O contigui [B, H, S, D], fp16. D in {64, 128}.
"""
import ctypes
import os
import threading

import torch

LOAD_WITH_ALTERED_SEARCH_PATH = 0x8
vp = ctypes.c_void_p

SORGENTE = r"""
typedef _Float16 h2 __attribute__((ext_vector_type(2)));
typedef _Float16 f16;

#define BR 64
#define BC 64
#ifndef CH
#define CH 16
#endif
#ifndef ONDE
#define ONDE 1
#endif

extern "C" __global__ __launch_bounds__(64, ONDE)
void fa_avanti(const h2* __restrict__ Q, const h2* __restrict__ K,
               const h2* __restrict__ V, h2* __restrict__ O,
               int S, float scala, int causale)
{
    const int D2 = HEAD_DIM / 2;
    const int bh = blockIdx.y;
    const int r0 = blockIdx.x * BR;
    const int t  = threadIdx.x;
    const int r  = r0 + t;
    const size_t base = (size_t)bh * S * D2;

    __shared__ h2 Ks[BC][HEAD_DIM / 2];
    __shared__ h2 Vs[BC][HEAD_DIM / 2];

    h2 q[HEAD_DIM / 2];
    float acc[HEAD_DIM];
    const h2 zero = {(f16)0.0f, (f16)0.0f};
    #pragma unroll
    for (int i = 0; i < D2; ++i) q[i] = (r < S) ? Q[base + (size_t)r * D2 + i] : zero;
    #pragma unroll
    for (int i = 0; i < HEAD_DIM; ++i) acc[i] = 0.0f;
    float m = -__builtin_inff();
    float l = 0.0f;

    int n_blocchi = (S + BC - 1) / BC;
    if (causale) {
        int ultimo = (r0 + BR - 1) / BC + 1;
        n_blocchi = n_blocchi < ultimo ? n_blocchi : ultimo;
    }

    for (int b = 0; b < n_blocchi; ++b) {
        const int c0 = b * BC;
        for (int idx = t; idx < BC * D2; idx += 64) {
            const int riga = idx / D2, col = idx - riga * D2;
            const int c = c0 + riga;
            Ks[riga][col] = (c < S) ? K[base + (size_t)c * D2 + col] : zero;
            Vs[riga][col] = (c < S) ? V[base + (size_t)c * D2 + col] : zero;
        }
        __syncthreads();

        for (int j0 = 0; j0 < BC; j0 += CH) {
            float s[CH];
            float mc = m;
            #pragma unroll
            for (int jj = 0; jj < CH; ++jj) {
                const int c = c0 + j0 + jj;
                float d = 0.0f;
                #pragma unroll
                for (int i = 0; i < D2; ++i)
                    d = __builtin_amdgcn_fdot2(q[i], Ks[j0 + jj][i], d, false);
                const bool valido = (c < S) && (!causale || c <= r);
                s[jj] = valido ? d * scala : -__builtin_inff();
                mc = fmaxf(mc, s[jj]);
            }
            if (mc == -__builtin_inff()) continue;      // niente di valido finora
            const float corr = __expf(m - mc);           // m = -inf -> 0
            l *= corr;
            #pragma unroll
            for (int i = 0; i < HEAD_DIM; ++i) acc[i] *= corr;
            m = mc;
            #pragma unroll
            for (int jj = 0; jj < CH; ++jj) {
                const float p = __expf(s[jj] - m);
                l += p;
                #pragma unroll
                for (int i = 0; i < D2; ++i) {
                    const h2 vv = Vs[j0 + jj][i];
                    acc[2 * i]     += p * (float)vv.x;
                    acc[2 * i + 1] += p * (float)vv.y;
                }
            }
        }
        __syncthreads();
    }

    if (r < S) {
        const float inv = (l > 0.0f) ? 1.0f / l : 0.0f;
        #pragma unroll
        for (int i = 0; i < D2; ++i) {
            h2 o = {(f16)(acc[2 * i] * inv), (f16)(acc[2 * i + 1] * inv)};
            O[base + (size_t)r * D2 + i] = o;
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
    h = k32.LoadLibraryExW(percorso, None, LOAD_WITH_ALTERED_SEARCH_PATH)
    if not h:
        raise OSError(f"{percorso}: errore {ctypes.get_last_error()}")
    return ctypes.CDLL(percorso, handle=h)


_lock = threading.Lock()
_funzioni = {}
_hip = None


def _compila(head_dim, extra=()):
    rtc = None
    for p in _percorsi_hiprtc():
        if os.path.exists(p):
            rtc = _carica(p)
            break
    if rtc is None:
        raise RuntimeError("nessuna hipRTC trovata")
    prog = vp()
    assert rtc.hiprtcCreateProgram(ctypes.byref(prog), SORGENTE.encode(), b"fa.hip", 0, None, None) == 0
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
        codice = _compila(head_dim, extra)
        mod, f = vp(), vp()
        assert _hip.hipModuleLoadData(ctypes.byref(mod), codice) == 0
        assert _hip.hipModuleGetFunction(ctypes.byref(f), mod, b"fa_avanti") == 0
        _funzioni[chiave] = (f, codice, mod)
        return _funzioni[chiave]


def flash_avanti(q, k, v, is_causal=False, scale=None, extra=()):
    """q, k, v: [B, H, S, D] fp16 su GPU. Restituisce O con la stessa forma."""
    assert q.dtype == torch.float16 and q.is_cuda
    B, H, S, D = q.shape
    assert k.shape == q.shape and v.shape == q.shape, "prototipo: Q, K, V della stessa forma"
    assert D in (64, 128), "prototipo: head_dim 64 o 128"
    q, k, v = q.contiguous(), k.contiguous(), v.contiguous()
    o = torch.empty_like(q)
    f = _funzione(D, extra)[0]
    scala = ctypes.c_float(scale if scale is not None else D ** -0.5)
    a = [vp(q.data_ptr()), vp(k.data_ptr()), vp(v.data_ptr()), vp(o.data_ptr()),
         ctypes.c_int(S), scala, ctypes.c_int(1 if is_causal else 0)]
    args = (vp * len(a))(*[ctypes.cast(ctypes.byref(x), vp) for x in a])
    rc = _hip.hipModuleLaunchKernel(f, (S + 63) // 64, B * H, 1, 64, 1, 1, 0, None, args, None)
    if rc != 0:
        raise RuntimeError(f"hipModuleLaunchKernel rc={rc}")
    return o

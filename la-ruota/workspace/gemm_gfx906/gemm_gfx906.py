"""GEMM fp16 (accumulo fp32) per gfx906, oltre Tensile sulle forme del passo LoRA di Qwen3.5.

2S, 20 ott 2026. C[M, N] = A[M, K] @ B[K, N], fp16 in ingresso e in uscita, accumulo fp32 con
v_dot2_f32_f16 (2 MAC per corsia per ciclo: il picco di gfx906 ~27 TFLOPS). Tensile a 512 token
rende 11-19 TFLOPS: parte del perso e' la quantizzazione in onde (512 x 2560 a tessere 128 x 128 =
80 tessere su 60 CU), parte i kernel stessi.

Kernel: tessera 128 x 128 x 32, 256 thread, 8 x 8 uscite per thread (righe ty*4+i e 64+ty*4+i, colonne
idem con tx). LDS impacchettata a coppie lungo K, S[k/2][riga] = half2(k, k+1), doppio buffer, la
tessera globale successiva in registri durante il calcolo, una sola barriera per passo. Ogni operando
puo' avere K contigua (riga di A, colonna di B = riga di W in y = x W^T) o no: la disposizione si
sistema nel caricamento in LDS, cosi' le tre GEMM di una Linear (avanti, dX, dW) usano lo stesso calcolo.
Split-K (asse z della griglia) per riempire i CU: parziali fp32 e un kernel di somma.

    import gemm_gfx906
    C = gemm_gfx906.mm(a, b)               # a [M, K], b [K, N] fp16 CUDA, viste trasposte ammesse
    gemm_gfx906.aggancia()                 # F.linear fp16 (avanti e indietro) passa da qui
Forme veloci: M, N multipli di 128, K multiplo di 32 (per ogni pezzo di split), passi multipli di 8.
Altrimenti torch.
"""
import ctypes
import os
import sys
import threading

import torch
import torch.nn.functional as F

vp = ctypes.c_void_p

SORGENTE = r"""
typedef _Float16 h2 __attribute__((ext_vector_type(2)));
typedef unsigned int u32;
typedef unsigned short u16;
struct __attribute__((aligned(16))) q4 { u32 x, y, z, w; };

#define BM 128
#define BN 128
#define BK 32
#define K2 (BK / 2)
#ifndef ORDINE_M
#define ORDINE_M 0
#endif
#ifndef UNROLL_K2
#define UNROLL_K2 8
#endif

__device__ inline float d2(u32 a, u32 b, float c) {
    return __builtin_amdgcn_fdot2(__builtin_bit_cast(h2, a), __builtin_bit_cast(h2, b), c, false);
}

/* Caricamento di una tessera [128 righe x 32 k] dell'operando X in registri (r0, r1: 2 x 16 byte).
   KCONT: X(riga, k) = X[riga * ld + k]  ->  chunk c = tid + 256 i: riga c % 128, k 8 * (c / 128)
   altrim.: X(riga, k) = X[k * ld + riga] ->  chunk: righe 8 * (tid % 16), coppia di k = tid / 16      */
template <int KCONT>
__device__ inline void carica(const u16* __restrict__ X, long long ld, int riga0, int k0, int tid, q4& r0, q4& r1) {
    if (KCONT) {
        const int c0 = tid, c1 = tid + 256;
        r0 = *(const q4*)(X + (long long)(riga0 + (c0 & 127)) * ld + k0 + 8 * (c0 >> 7));
        r1 = *(const q4*)(X + (long long)(riga0 + (c1 & 127)) * ld + k0 + 8 * (c1 >> 7));
    } else {
        const int rc = 8 * (tid & 15), kp = tid >> 4;
        r0 = *(const q4*)(X + (long long)(k0 + 2 * kp) * ld + riga0 + rc);
        r1 = *(const q4*)(X + (long long)(k0 + 2 * kp + 1) * ld + riga0 + rc);
    }
}

/* Scrittura in LDS: S[k2 * 128 + riga] = half2(k = 2 k2, 2 k2 + 1) */
template <int KCONT>
__device__ inline void deponi(u32* S, int tid, const q4& r0, const q4& r1) {
    if (KCONT) {
        const int c0 = tid, c1 = tid + 256;
        const int ra = c0 & 127, ka = 4 * (c0 >> 7), rb = c1 & 127, kb = 4 * (c1 >> 7);
        S[(ka + 0) * BM + ra] = r0.x; S[(ka + 1) * BM + ra] = r0.y;
        S[(ka + 2) * BM + ra] = r0.z; S[(ka + 3) * BM + ra] = r0.w;
        S[(kb + 0) * BM + rb] = r1.x; S[(kb + 1) * BM + rb] = r1.y;
        S[(kb + 2) * BM + rb] = r1.z; S[(kb + 3) * BM + rb] = r1.w;
    } else {
        const int rc = 8 * (tid & 15), kp = tid >> 4;
        q4 p, q;
        p.x = (r0.x & 0xFFFFu) | (r1.x << 16); p.y = (r0.x >> 16) | (r1.x & 0xFFFF0000u);
        p.z = (r0.y & 0xFFFFu) | (r1.y << 16); p.w = (r0.y >> 16) | (r1.y & 0xFFFF0000u);
        q.x = (r0.z & 0xFFFFu) | (r1.z << 16); q.y = (r0.z >> 16) | (r1.z & 0xFFFF0000u);
        q.z = (r0.w & 0xFFFFu) | (r1.w << 16); q.w = (r0.w >> 16) | (r1.w & 0xFFFF0000u);
        *(q4*)(S + kp * BM + rc) = p;
        *(q4*)(S + kp * BM + rc + 4) = q;
    }
}

extern "C" __global__ __launch_bounds__(256)
void gemm(const u16* __restrict__ A, const u16* __restrict__ B, u16* __restrict__ C, float* __restrict__ P,
          const _Float16* __restrict__ bias, int M, int N, int Kpezzo, long long lda, long long ldb, long long ldc)
{
    __shared__ u32 SA[2][K2 * BM];
    __shared__ u32 SB[2][K2 * BN];
    const int tid = threadIdx.x;
    const int tx = tid & 15, ty = tid >> 4;
#if ORDINE_M
    const int m0 = blockIdx.x * BM, n0 = blockIdx.y * BN;     /* le tessere M di una fetta di B vicine */
#else
    const int m0 = blockIdx.y * BM, n0 = blockIdx.x * BN;
#endif
    const int kini = blockIdx.z * Kpezzo;
    const int passi = Kpezzo / BK;
    float acc[8][8];
    #pragma unroll
    for (int i = 0; i < 8; ++i)
        #pragma unroll
        for (int j = 0; j < 8; ++j) acc[i][j] = 0.0f;

    q4 a0, a1, b0, b1;
    carica<A_KCONT>(A, lda, m0, kini, tid, a0, a1);
    carica<B_KCONT>(B, ldb, n0, kini, tid, b0, b1);
    deponi<A_KCONT>(SA[0], tid, a0, a1);
    deponi<B_KCONT>(SB[0], tid, b0, b1);
    __syncthreads();
    for (int p = 0; p < passi; ++p) {
        const int cur = p & 1;
        if (p + 1 < passi) {
            carica<A_KCONT>(A, lda, m0, kini + (p + 1) * BK, tid, a0, a1);
            carica<B_KCONT>(B, ldb, n0, kini + (p + 1) * BK, tid, b0, b1);
        }
        const u32* sa = SA[cur];
        const u32* sb = SB[cur];
        #pragma unroll UNROLL_K2
        for (int k2 = 0; k2 < K2; ++k2) {
            const q4 x0 = *(const q4*)(sa + k2 * BM + ty * 4);
            const q4 x1 = *(const q4*)(sa + k2 * BM + 64 + ty * 4);
            const q4 y0 = *(const q4*)(sb + k2 * BN + tx * 4);
            const q4 y1 = *(const q4*)(sb + k2 * BN + 64 + tx * 4);
            const u32 a[8] = {x0.x, x0.y, x0.z, x0.w, x1.x, x1.y, x1.z, x1.w};
            const u32 b[8] = {y0.x, y0.y, y0.z, y0.w, y1.x, y1.y, y1.z, y1.w};
            #pragma unroll
            for (int i = 0; i < 8; ++i)
                #pragma unroll
                for (int j = 0; j < 8; ++j) acc[i][j] = d2(a[i], b[j], acc[i][j]);
        }
        if (p + 1 < passi) {
            deponi<A_KCONT>(SA[cur ^ 1], tid, a0, a1);
            deponi<B_KCONT>(SB[cur ^ 1], tid, b0, b1);
        }
        __syncthreads();
    }
    #pragma unroll
    for (int i = 0; i < 8; ++i) {
        const int m = m0 + (i < 4 ? ty * 4 + i : 64 + ty * 4 + i - 4);
        #pragma unroll
        for (int g = 0; g < 2; ++g) {
            const int n = n0 + g * 64 + tx * 4;
            if (P) {
                float* d = P + ((long long)blockIdx.z * M + m) * N + n;
                *(float4*)d = make_float4(acc[i][4 * g], acc[i][4 * g + 1], acc[i][4 * g + 2], acc[i][4 * g + 3]);
            } else {
                typedef _Float16 h4 __attribute__((ext_vector_type(4)));
                float e0 = 0.0f, e1 = 0.0f, e2 = 0.0f, e3 = 0.0f;
                if (bias) { e0 = (float)bias[n]; e1 = (float)bias[n + 1]; e2 = (float)bias[n + 2]; e3 = (float)bias[n + 3]; }
                h4 v = {(_Float16)(acc[i][4 * g] + e0), (_Float16)(acc[i][4 * g + 1] + e1),
                        (_Float16)(acc[i][4 * g + 2] + e2), (_Float16)(acc[i][4 * g + 3] + e3)};
                *(h4*)(C + (long long)m * ldc + n) = v;
            }
        }
    }
}

/* ---- precisione mista (22 ott): A fp32 (K contigua) convertita in fp16 al caricamento, B = W fp16 [N][K],
   accumulo fp32 con v_dot2, uscita FP32 nei parziali P[s][M][N]; maschere su M e N (forme non multiple di 128). ---- */
__device__ inline u32 coppia_h(float lo, float hi) {
    const _Float16 l = (_Float16)lo, h = (_Float16)hi;
    return (u32)__builtin_bit_cast(u16, l) | ((u32)__builtin_bit_cast(u16, h) << 16);
}
__device__ inline void carica_a32(const float* __restrict__ X, long long ld, int riga0, int k0, int tid, int M,
                                  q4& r0, q4& r1) {
    const int c0 = tid, c1 = tid + 256;
    const int ra = riga0 + (c0 & 127), rb = riga0 + (c1 & 127);
    if (ra < M) {
        const float4 u = *(const float4*)(X + (long long)ra * ld + k0 + 8 * (c0 >> 7));
        const float4 v = *(const float4*)(X + (long long)ra * ld + k0 + 8 * (c0 >> 7) + 4);
        r0.x = coppia_h(u.x, u.y); r0.y = coppia_h(u.z, u.w); r0.z = coppia_h(v.x, v.y); r0.w = coppia_h(v.z, v.w);
    } else { r0.x = r0.y = r0.z = r0.w = 0u; }
    if (rb < M) {
        const float4 u = *(const float4*)(X + (long long)rb * ld + k0 + 8 * (c1 >> 7));
        const float4 v = *(const float4*)(X + (long long)rb * ld + k0 + 8 * (c1 >> 7) + 4);
        r1.x = coppia_h(u.x, u.y); r1.y = coppia_h(u.z, u.w); r1.z = coppia_h(v.x, v.y); r1.w = coppia_h(v.z, v.w);
    } else { r1.x = r1.y = r1.z = r1.w = 0u; }
}
__device__ inline void carica_w16(const u16* __restrict__ X, long long ld, int riga0, int k0, int tid, int N,
                                  q4& r0, q4& r1) {
    const int c0 = tid, c1 = tid + 256;
    const int ra = riga0 + (c0 & 127), rb = riga0 + (c1 & 127);
    if (ra < N) r0 = *(const q4*)(X + (long long)ra * ld + k0 + 8 * (c0 >> 7)); else { r0.x = r0.y = r0.z = r0.w = 0u; }
    if (rb < N) r1 = *(const q4*)(X + (long long)rb * ld + k0 + 8 * (c1 >> 7)); else { r1.x = r1.y = r1.z = r1.w = 0u; }
}

extern "C" __global__ __launch_bounds__(256)
void gemm_misto(const float* __restrict__ A, const u16* __restrict__ B, float* __restrict__ P,
                int M, int N, int Kpezzo, long long lda, long long ldb)
{
    __shared__ u32 SA[2][K2 * BM];
    __shared__ u32 SB[2][K2 * BN];
    const int tid = threadIdx.x;
    const int tx = tid & 15, ty = tid >> 4;
    const int m0 = blockIdx.y * BM, n0 = blockIdx.x * BN;
    const int kini = blockIdx.z * Kpezzo;
    const int passi = Kpezzo / BK;
    float acc[8][8];
    #pragma unroll
    for (int i = 0; i < 8; ++i)
        #pragma unroll
        for (int j = 0; j < 8; ++j) acc[i][j] = 0.0f;
    q4 a0, a1, b0, b1;
    carica_a32(A, lda, m0, kini, tid, M, a0, a1);
    carica_w16(B, ldb, n0, kini, tid, N, b0, b1);
    deponi<1>(SA[0], tid, a0, a1);
    deponi<1>(SB[0], tid, b0, b1);
    __syncthreads();
    for (int p = 0; p < passi; ++p) {
        const int cur = p & 1;
        if (p + 1 < passi) {
            carica_a32(A, lda, m0, kini + (p + 1) * BK, tid, M, a0, a1);
            carica_w16(B, ldb, n0, kini + (p + 1) * BK, tid, N, b0, b1);
        }
        const u32* sa = SA[cur];
        const u32* sb = SB[cur];
        #pragma unroll UNROLL_K2
        for (int k2 = 0; k2 < K2; ++k2) {
            const q4 x0 = *(const q4*)(sa + k2 * BM + ty * 4);
            const q4 x1 = *(const q4*)(sa + k2 * BM + 64 + ty * 4);
            const q4 y0 = *(const q4*)(sb + k2 * BN + tx * 4);
            const q4 y1 = *(const q4*)(sb + k2 * BN + 64 + tx * 4);
            const u32 a[8] = {x0.x, x0.y, x0.z, x0.w, x1.x, x1.y, x1.z, x1.w};
            const u32 b[8] = {y0.x, y0.y, y0.z, y0.w, y1.x, y1.y, y1.z, y1.w};
            #pragma unroll
            for (int i = 0; i < 8; ++i)
                #pragma unroll
                for (int j = 0; j < 8; ++j) acc[i][j] = d2(a[i], b[j], acc[i][j]);
        }
        if (p + 1 < passi) {
            deponi<1>(SA[cur ^ 1], tid, a0, a1);
            deponi<1>(SB[cur ^ 1], tid, b0, b1);
        }
        __syncthreads();
    }
    #pragma unroll
    for (int i = 0; i < 8; ++i) {
        const int m = m0 + (i < 4 ? ty * 4 + i : 64 + ty * 4 + i - 4);
        if (m >= M) continue;
        #pragma unroll
        for (int g = 0; g < 2; ++g) {
            #pragma unroll
            for (int q = 0; q < 4; ++q) {
                const int n = n0 + g * 64 + tx * 4 + q;
                if (n < N) P[((long long)blockIdx.z * M + m) * N + n] = acc[i][4 * g + q];
            }
        }
    }
}

/* C[m, n] = sum_s P[s, m, n]  (fp32 -> fp16), 4 elementi per thread */
extern "C" __global__ __launch_bounds__(256)
void somma_pezzi(const float* __restrict__ P, u16* __restrict__ C, const _Float16* __restrict__ bias,
                 int M, int N, int S, long long ldc)
{
    const long long i = ((long long)blockIdx.x * 256 + threadIdx.x) * 4;
    const long long tot = (long long)M * N;
    if (i >= tot) return;
    float4 s = *(const float4*)(P + i);
    for (int z = 1; z < S; ++z) {
        const float4 t = *(const float4*)(P + (long long)z * tot + i);
        s.x += t.x; s.y += t.y; s.z += t.z; s.w += t.w;
    }
    const long long m = i / N, n = i - m * N;
    if (bias) { s.x += (float)bias[n]; s.y += (float)bias[n + 1]; s.z += (float)bias[n + 2]; s.w += (float)bias[n + 3]; }
    typedef _Float16 h4 __attribute__((ext_vector_type(4)));
    h4 v = {(_Float16)s.x, (_Float16)s.y, (_Float16)s.z, (_Float16)s.w};
    *(h4*)(C + m * ldc + n) = v;
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


OPZIONI = []                # opzioni di compilazione in piu' (varianti: -DUNROLL_K2=4, ...)


def _funzione(nome, akc, bkc):
    global _hip
    chiave = (nome, akc, bkc, tuple(OPZIONI))
    with _lock:
        if chiave not in _funzioni:
            if _hip is None:
                _hip = ctypes.CDLL("amdhip64.dll")
                _hip.hipModuleLaunchKernel.argtypes = [vp] + [ctypes.c_uint] * 7 + [vp, vp, vp]
            rtc = _carica_rtc()
            prog = vp()
            assert rtc.hiprtcCreateProgram(ctypes.byref(prog), SORGENTE.encode(), b"gemm.hip", 0, None, None) == 0
            opz = [b"--offload-arch=gfx906", b"-O3", f"-DA_KCONT={akc}".encode(), f"-DB_KCONT={bkc}".encode()] + [o.encode() for o in OPZIONI]
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


def _lancia(f, griglia, argomenti):
    a = (vp * len(argomenti))(*[ctypes.cast(ctypes.byref(v), vp) for v in argomenti])
    rc = _hip.hipModuleLaunchKernel(f, griglia[0], griglia[1], griglia[2], 256, 1, 1, 0,
                                    vp(torch.cuda.current_stream().cuda_stream), a, None)
    if rc != 0:
        raise RuntimeError(f"hipModuleLaunchKernel rc={rc}")


sys.path.insert(0, r"C:\LaRuota_workspace\lancio_gfx906")
from lancio_gfx906 import Kernel  # noqa: E402
_KERNEL = {}


def _kernel(nome, akc, bkc, firma):
    chiave = (nome, akc, bkc, tuple(OPZIONI))
    k = _KERNEL.get(chiave)
    if k is None:
        k = _KERNEL[chiave] = Kernel(_funzione(nome, akc, bkc), firma)
    return k


def _disposizione(t, contigua_su):
    """(K contigua?, ld) per un operando 2D; None se nessuna delle due dimensioni e' contigua."""
    s0, s1 = t.stride()
    if contigua_su == "colonne":            # A [M, K]: K e' la dimensione 1
        if s1 == 1:
            return 1, s0
        if s0 == 1:
            return 0, s1
    else:                                   # B [K, N]: K e' la dimensione 0
        if s0 == 1:
            return 1, s1
        if s1 == 1:
            return 0, s0
    return None


CU = 60


SPLIT_FORZATO = None        # per i banchi
TARATURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tarature.json")
# (M, N, K, A K-contigua, B K-contigua) -> split migliore, 0 = rocBLAS. Si riempie con tara() a GPU libera.
# Forme non tarate: rocBLAS (GEMM_NON_TARATE=stima usa invece la stima di scegli_split).
SCELTE = {}
NON_TARATE = os.environ.get("GEMM_NON_TARATE", "rocblas")


def scelta_per_fascia(M, N, K, akc, bkc, fattore=1.5):
    """Forma non tarata: la voce tarata con le stesse disposizioni e due dimensioni uguali, con la terza (i token:
    M in avanti e in dX, K in dW) piu' vicina in scala logaritmica, entro `fattore`. Lo split si tiene solo se
    divide ancora K. None se non c'e' una voce abbastanza vicina."""
    import math
    migliore, dist = None, None
    for (m, n, k, a, b), sc in SCELTE.items():
        if a != akc or b != bkc:
            continue
        if n == N and k == K:
            d = abs(math.log(M / m))
        elif m == M and n == N:
            d = abs(math.log(K / k))
        else:
            continue
        if d <= math.log(fattore) and (dist is None or d < dist):
            migliore, dist = sc, d
    if migliore is None:
        return None
    if migliore and K % (32 * migliore):
        return 1
    return migliore


def _carica_tarature():
    import json
    if os.path.exists(TARATURE):
        with open(TARATURE, encoding="utf-8") as f:
            for chiave, s in json.load(f).items():
                SCELTE[tuple(int(v) for v in chiave.split(","))] = int(s)


_carica_tarature()


def scegli_split(M, N, K):
    """Stima: tempo ~ giri x (K / s) di una tessera (1 blocco per CU, 128 MAC/ciclo) + parziali fp32
    scritti e riletti (s + 1 passate di M N 4 byte a ~600 GB/s)."""
    tessere = (M // 128) * (N // 128)
    migliore, s_m = None, 1
    for s in (1, 2, 3, 4, 5, 6, 8):
        if K % (32 * s):
            continue
        giri = -(-(tessere * s) // CU)
        t = giri * 128 * 128 * (K / s) / 128 / 1.8e9
        if s > 1:
            t += (s + 1) * M * N * 4 / 600e9
        if migliore is None or t < migliore - 1e-12:
            migliore, s_m = t, s
    return s_m


def supportata(a, b):
    if not (a.is_cuda and b.is_cuda and a.dtype == torch.float16 and b.dtype == torch.float16):
        return False
    if a.dim() != 2 or b.dim() != 2 or a.shape[1] != b.shape[0]:
        return False
    M, K = a.shape
    N = b.shape[1]
    if M % 128 or N % 128 or K % 32 or K == 0:
        return False
    da, db = _disposizione(a, "colonne"), _disposizione(b, "righe")
    if da is None or db is None or da[1] % 8 or db[1] % 8:
        return False
    return a.data_ptr() % 16 == 0 and b.data_ptr() % 16 == 0


ALLINEA = os.environ.get("GEMM_ALLINEA", "1") == "1"      # predefinito: vedi allinea()
_DUE_MB = 2 << 20


def allinea(t):
    """Copia t (contiguo) in un blocco che parte a un multiplo di 2 MB, se non ci parte gia'.
    Misurato il 20 ott: la stessa GEMM rocBLAS 512x2560 @ 2560x4096 va da 14,6 a 10,2 TFLOPS secondo dove
    sta l'attivazione modulo 2 MB (lenta fra ~512 KB e 1,25 MB); con l'attivazione a 0 mod 2 MB tutte le
    GEMM del passo LoRA sono al massimo o quasi (diag_gemm/indirizzi3.py)."""
    if t.data_ptr() % _DUE_MB == 0 or not t.is_contiguous():
        return t
    n = t.numel() * t.element_size()
    grezzo = torch.empty(n + _DUE_MB, dtype=torch.uint8, device=t.device)
    spost = (-grezzo.data_ptr()) % _DUE_MB
    nuovo = grezzo[spost:spost + n].view(t.dtype).view(t.shape)
    nuovo.copy_(t)
    return nuovo


def mm(a, b, split=None, bias=None):
    """a [M, K] @ b [K, N] (+ bias [N]) in fp16, accumulo fp32; fuori dalle forme veloci torch."""
    if not supportata(a, b):
        return torch.addmm(bias, a, b) if bias is not None else torch.mm(a, b)
    if bias is not None:
        bias = bias.contiguous()
    M, K = a.shape
    N = b.shape[1]
    akc, lda = _disposizione(a, "colonne")
    bkc, ldb = _disposizione(b, "righe")
    s = split or SPLIT_FORZATO
    if not s:
        s = SCELTE.get((M, N, K, akc, bkc))
        if s is None:
            s = scelta_per_fascia(M, N, K, akc, bkc)
        if s is None:
            s = scegli_split(M, N, K) if NON_TARATE == "stima" else 0
        if s == 0:
            return torch.addmm(bias, a, b) if bias is not None else torch.mm(a, b)
    if K % (32 * s):
        s = 1
    C = torch.empty(M, N, device=a.device, dtype=torch.float16)
    P = torch.empty(s, M, N, device=a.device, dtype=torch.float32) if s > 1 else None
    griglia = (M // 128, N // 128, s) if "-DORDINE_M=1" in OPZIONI else (N // 128, M // 128, s)
    _kernel("gemm", akc, bkc, "pppppiiiqqq")(
        griglia, (a.data_ptr(), b.data_ptr(), C.data_ptr(), P.data_ptr() if P is not None else 0,
                  bias.data_ptr() if bias is not None else 0, M, N, K // s, lda, ldb, N))
    if P is not None:
        _kernel("somma_pezzi", akc, bkc, "pppiiiq")(
            (M * N // 4 + 255) // 256, (P.data_ptr(), C.data_ptr(), bias.data_ptr() if bias is not None else 0,
                                         M, N, s, N))
    return C


_PESI16 = {}


def _w16(W):
    """Peso fp16 in cache (per tensore e versione)."""
    chiave = (W.data_ptr(), tuple(W.shape), W._version)
    v = _PESI16.get(chiave)
    if v is None:
        if len(_PESI16) > 512:
            _PESI16.clear()
        v = _PESI16[chiave] = W.detach().half().contiguous()
    return v


def supportata_misto(x2, W):
    M, K = x2.shape
    N = W.shape[0]
    return (x2.is_cuda and x2.dtype == torch.float32 and W.dtype == torch.float32 and x2.stride(1) == 1
            and K % 32 == 0 and K > 0 and M > 0 and N > 0 and x2.stride(0) % 4 == 0 and x2.data_ptr() % 16 == 0)


def lineare_misto(x, W, bias=None, split=None):
    """y = x W^T + b con x fp32: x e W arrotondati a fp16, prodotto con accumulo fp32, USCITA FP32.
    Solo le moltiplicazioni in fp16; residui, norme, softmax e attenzione restano fp32.
    Fuori forma (K non multiplo di 32, x non contiguo sull'ultima dimensione) ricade su F.linear fp32."""
    x2 = x.reshape(-1, x.shape[-1])
    if not supportata_misto(x2, W):
        return torch.nn.functional.linear(x, W, bias)
    M, K = x2.shape
    N = W.shape[0]
    W16 = _w16(W)
    s = split or 1
    tessere = ((M + 127) // 128) * ((N + 127) // 128)
    if split is None:
        while s < 8 and tessere * s < 60 and K % (32 * s * 2) == 0:
            s *= 2
    P = torch.empty(s, M, N, device=x.device, dtype=torch.float32)
    _kernel("gemm_misto", 1, 1, "pppiiiqq")(
        ((N + 127) // 128, (M + 127) // 128, s),
        (x2.data_ptr(), W16.data_ptr(), P.data_ptr(), M, N, K // s, x2.stride(0), W16.stride(0)))
    y = P[0] if s == 1 else P.sum(0)
    if bias is not None:
        y = y + bias
    return y.reshape(*x.shape[:-1], N)


class _Lineare(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, W, bias):
        x2 = x.reshape(-1, x.shape[-1])
        if ALLINEA:
            x2 = allinea(x2.contiguous())
        y = mm(x2, W.t(), bias=bias)
        ctx.save_for_backward(x2, W)
        ctx.forma, ctx.ha_bias = x.shape, bias is not None
        return y.reshape(*x.shape[:-1], W.shape[0])

    @staticmethod
    def backward(ctx, dy):
        x2, W = ctx.saved_tensors
        dy2 = dy.reshape(-1, W.shape[0])
        if dy2.stride(-1) != 1:
            dy2 = dy2.contiguous()
        if ALLINEA:
            dy2 = allinea(dy2)
        dx = mm(dy2, W).reshape(ctx.forma) if ctx.needs_input_grad[0] else None
        dW = mm(dy2.t(), x2) if ctx.needs_input_grad[1] else None
        db = dy2.float().sum(0).to(dy2.dtype) if (ctx.ha_bias and ctx.needs_input_grad[2]) else None
        return dx, dW, db


_ORIG = []


def lineare(x, W, bias=None):
    """F.linear fp16 con le tre GEMM da qui (ricade su F.linear se le forme non sono veloci)."""
    if (torch.is_autocast_enabled() and x.is_cuda):
        x = x.to(torch.float16)
        W = W.to(torch.float16)
        bias = bias.to(torch.float16) if bias is not None else None
    if (x.dtype != torch.float16 or W.dtype != torch.float16 or not x.is_cuda or x.dim() < 2
            or (bias is not None and bias.dtype != torch.float16)):
        return _ORIG[0](x, W, bias)
    x2 = x.reshape(-1, x.shape[-1])
    if not supportata(x2, W.t()):
        return _ORIG[0](x, W, bias)
    with torch.autocast("cuda", enabled=False):
        return _Lineare.apply(x, W, bias)


def aggancia():
    if not _ORIG:
        _ORIG.append(F.linear)
        F.linear = lineare
        torch.nn.functional.linear = lineare


def sgancia():
    if _ORIG:
        F.linear = _ORIG.pop()
        torch.nn.functional.linear = F.linear


def tara(forme, lanci=20, giri=3, margine=0.03):
    """Per ogni forma (M, N, K, A K-contigua, B K-contigua): mediana di lanci intercalati di rocBLAS e di
    ogni split; sceglie lo split solo se batte rocBLAS di almeno `margine`. Salva in tarature.json.
    DA FARE A GPU LIBERA: con altri processi le misure sono rumorose (visti valori sopra il picco)."""
    import json
    risultati = []
    for M, N, K, akc, bkc in forme:
        a = torch.randn(M, K, device="cuda").half() if akc else torch.randn(K, M, device="cuda").half().t()
        b = torch.randn(N, K, device="cuda").half().t() if bkc else torch.randn(K, N, device="cuda").half()
        candidati = [0] + [s for s in (1, 2, 3, 4, 6, 8) if K % (32 * s) == 0]
        tempi = {s: [] for s in candidati}
        for _ in range(giri):
            for s in candidati:
                fn = (lambda: torch.mm(a, b)) if s == 0 else (lambda s=s: mm(a, b, split=s))
                for _ in range(3):
                    fn()
                for _ in range(lanci):
                    e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                    e0.record(); fn(); e1.record(); torch.cuda.synchronize()
                    tempi[s].append(e0.elapsed_time(e1))
        mediane = {s: sorted(t)[len(t) // 2] for s, t in tempi.items()}
        migliore = min((s for s in candidati if s), key=lambda s: mediane[s])
        scelta = migliore if mediane[migliore] < mediane[0] * (1 - margine) else 0
        SCELTE[(M, N, K, akc, bkc)] = scelta
        tf = lambda ms: 2 * M * N * K / ms / 1e9
        risultati.append((M, N, K, akc, bkc, tf(mediane[0]), migliore, tf(mediane[migliore]), scelta))
    with open(TARATURE, "w", encoding="utf-8") as f:
        json.dump({",".join(str(v) for v in k): s for k, s in sorted(SCELTE.items())}, f, indent=1)
    return risultati

"""Flash attention per gfx906 — passo all'INDIETRO (dQ, dK, dV). 2S, 19 ott 2026.

Con l'avanti di fa2_avanti.py, che restituisce anche il logsumexp per riga (LSE2, in base 2).

PERCHE' DUE KERNEL
------------------
FlashAttention-2 fa l'indietro in un kernel per blocco di chiavi e accumula dQ con addizioni
ATOMICHE fp32 in memoria globale. gfx906 non ha atomiche fp32 globali (solo a confronto e
scambio, troppo lente). Quindi:
  - fa2_dkdv: un workgroup per 32 chiavi, scorre i blocchi di 64 query: dK, dV;
  - fa2_dq:   un workgroup per 32 query, scorre i blocchi di 64 chiavi: dQ.
Entrambi ricalcolano P = exp2(S * scala_log2 - LSE2) dai dati dell'avanti.

  Dv[q] = sum_d dO[q][d] * O[q][d]      (fuori dai kernel, una riduzione di torch)
  dP    = dO V^T
  dS    = P * (dP - Dv)
  dV    = P^T dO,   dK = scala * dS^T Q,   dQ = scala * dS K

I prodotti lungo le query (dV, dK) e lungo le chiavi (dQ) usano v_dot2 su coppie fp16
composte al volo da due letture della LDS: niente copie trasposte, che non ci starebbero
nei 64 KB con D=128. P e dS passano in fp16 come in FlashAttention-2.

Layout: Q, K, V, O, dO contigui [B, H, S, D], fp16. D in {64, 128}.
"""
import ctypes
import threading

import torch

import fa2_avanti

vp = ctypes.c_void_p

COMUNE = r"""
typedef _Float16 f16;
typedef _Float16 h2 __attribute__((ext_vector_type(2)));
typedef unsigned int u4 __attribute__((ext_vector_type(4)));
#define D2 (HEAD_DIM / 2)
#define QSTR (D2 + 4)            /* passo delle righe in LDS, in dword (h2) */
#define DU (HEAD_DIM / 16)       /* colonne d per thread: d = tc + 16 u */
#define NT 128
__device__ inline h2 come_h2(unsigned int x) { return __builtin_bit_cast(h2, x); }
__device__ inline unsigned int el(u4 v, int e) { return e == 0 ? v.x : e == 1 ? v.y : e == 2 ? v.z : v.w; }
#define DOT2(a, b, c) __builtin_amdgcn_fdot2((a), (b), (c), false)

/* carica 'righe' righe da 'r0' (zeri oltre S) nella LDS a passo QSTR, a gruppi di 4 h2 */
__device__ inline void carica(unsigned int* dst, const unsigned int* src, size_t base, int r0, int righe, int S, int t) {
    for (int idx = t; idx < righe * D2 / 4; idx += NT) {
        const int riga = idx / (D2 / 4), col = (idx - riga * (D2 / 4)) * 4;
        u4 x = {0u, 0u, 0u, 0u};
        if (r0 + riga < S) x = *(const u4*)(src + base + (size_t)(r0 + riga) * D2 + col);
        *(u4*)(dst + riga * QSTR + col) = x;
    }
}
"""

SORGENTE_DKDV = COMUNE + r"""
#define BK 32                    /* chiavi per workgroup (ferme) */
#define BQ 64                    /* query per giro (scorrono) */
#define PST (BQ / 2 + 4)         /* passo di P^T e dS^T, in dword (h2 lungo q) */

extern "C" __global__ __launch_bounds__(NT)
void fa2_dkdv(const unsigned int* __restrict__ Q, const unsigned int* __restrict__ K,
              const unsigned int* __restrict__ V, const unsigned int* __restrict__ dO,
              const float* __restrict__ LSE2, const float* __restrict__ Dv,
              f16* __restrict__ dK, f16* __restrict__ dV,
              int S, float scala_log2, float scala, int causale)
{
    __shared__ unsigned int Ks[BK * QSTR], Vs[BK * QSTR], Qs[BQ * QSTR], dOs[BQ * QSTR];
    __shared__ unsigned int PT[BK * PST], dST[BK * PST];
    __shared__ float Ls[BQ], Ds[BQ];

    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;      /* chiavi tr + 8a, query tc + 16b */
    const int bh = blockIdx.y, k0 = blockIdx.x * BK;
    const size_t base = (size_t)bh * S * D2;

    carica(Ks, K, base, k0, BK, S, t);
    carica(Vs, V, base, k0, BK, S, t);

    float dk[4][DU], dv[4][DU];
    #pragma unroll
    for (int a = 0; a < 4; ++a)
        #pragma unroll
        for (int u = 0; u < DU; ++u) { dk[a][u] = 0.0f; dv[a][u] = 0.0f; }

    const int nq = (S + BQ - 1) / BQ;
    const int qb0 = causale ? k0 / BQ : 0;          /* blocchi di query tutti sopra la diagonale: saltati */
    const f16* Qh = (const f16*)Qs;
    const f16* dOh = (const f16*)dOs;

    for (int qb = qb0; qb < nq; ++qb) {
        const int q0 = qb * BQ;
        __syncthreads();
        carica(Qs, Q, base, q0, BQ, S, t);
        carica(dOs, dO, base, q0, BQ, S, t);
        for (int i = t; i < BQ; i += NT) {
            const bool ok = q0 + i < S;
            Ls[i] = ok ? LSE2[(size_t)bh * S + q0 + i] : __builtin_inff();
            Ds[i] = ok ? Dv[(size_t)bh * S + q0 + i] : 0.0f;
        }
        __syncthreads();

        float st[4][4], dpt[4][4];
        #pragma unroll
        for (int a = 0; a < 4; ++a)
            #pragma unroll
            for (int b = 0; b < 4; ++b) { st[a][b] = 0.0f; dpt[a][b] = 0.0f; }
        #pragma unroll 2
        for (int c = 0; c < D2; c += 4) {
            u4 ka[4], va[4], qa[4], oa[4];
            #pragma unroll
            for (int a = 0; a < 4; ++a) {
                ka[a] = *(const u4*)(Ks + (tr + 8 * a) * QSTR + c);
                va[a] = *(const u4*)(Vs + (tr + 8 * a) * QSTR + c);
            }
            #pragma unroll
            for (int b = 0; b < 4; ++b) {
                qa[b] = *(const u4*)(Qs + (tc + 16 * b) * QSTR + c);
                oa[b] = *(const u4*)(dOs + (tc + 16 * b) * QSTR + c);
            }
            #pragma unroll
            for (int a = 0; a < 4; ++a)
                #pragma unroll
                for (int b = 0; b < 4; ++b)
                    #pragma unroll
                    for (int e = 0; e < 4; ++e) {
                        st[a][b]  = DOT2(come_h2(el(ka[a], e)), come_h2(el(qa[b], e)), st[a][b]);
                        dpt[a][b] = DOT2(come_h2(el(va[a], e)), come_h2(el(oa[b], e)), dpt[a][b]);
                    }
        }

        f16* PTh = (f16*)PT;
        f16* dSTh = (f16*)dST;
        #pragma unroll
        for (int a = 0; a < 4; ++a) {
            const int key = k0 + tr + 8 * a;
            #pragma unroll
            for (int b = 0; b < 4; ++b) {
                const int ql = tc + 16 * b, q = q0 + ql;
                const bool valido = (q < S) && (key < S) && (!causale || q >= key);
                const float p = valido ? __builtin_amdgcn_exp2f(st[a][b] * scala_log2 - Ls[ql]) : 0.0f;
                PTh[(tr + 8 * a) * (2 * PST) + ql] = (f16)p;
                dSTh[(tr + 8 * a) * (2 * PST) + ql] = (f16)(p * (dpt[a][b] - Ds[ql]));
            }
        }
        __syncthreads();

        /* dV += P^T dO, dK += dS^T Q: dot2 lungo coppie di query */
        #pragma unroll 2
        for (int qp4 = 0; qp4 < BQ / 2; qp4 += 4) {
            u4 pa[4], sa[4];
            #pragma unroll
            for (int a = 0; a < 4; ++a) {
                pa[a] = *(const u4*)(PT + (tr + 8 * a) * PST + qp4);
                sa[a] = *(const u4*)(dST + (tr + 8 * a) * PST + qp4);
            }
            #pragma unroll
            for (int e = 0; e < 4; ++e) {
                const int q = 2 * (qp4 + e);
                #pragma unroll
                for (int u = 0; u < DU; ++u) {
                    const int d = tc + 16 * u;
                    const h2 o2 = {dOh[q * 2 * QSTR + d], dOh[(q + 1) * 2 * QSTR + d]};
                    const h2 q2 = {Qh[q * 2 * QSTR + d], Qh[(q + 1) * 2 * QSTR + d]};
                    #pragma unroll
                    for (int a = 0; a < 4; ++a) {
                        dv[a][u] = DOT2(come_h2(el(pa[a], e)), o2, dv[a][u]);
                        dk[a][u] = DOT2(come_h2(el(sa[a], e)), q2, dk[a][u]);
                    }
                }
            }
        }
    }

    #pragma unroll
    for (int a = 0; a < 4; ++a) {
        const int key = k0 + tr + 8 * a;
        if (key < S) {
            f16* rk = dK + ((size_t)bh * S + key) * HEAD_DIM;
            f16* rv = dV + ((size_t)bh * S + key) * HEAD_DIM;
            #pragma unroll
            for (int u = 0; u < DU; ++u) {
                rk[tc + 16 * u] = (f16)(dk[a][u] * scala);
                rv[tc + 16 * u] = (f16)dv[a][u];
            }
        }
    }
}
"""

SORGENTE_DQ = COMUNE + r"""
#define BQ 32                    /* query per workgroup (ferme) */
#define BK 64                    /* chiavi per giro (scorrono) */
#define SST (BK / 2 + 4)         /* passo di dS, in dword (h2 lungo le chiavi) */

extern "C" __global__ __launch_bounds__(NT)
void fa2_dq(const unsigned int* __restrict__ Q, const unsigned int* __restrict__ K,
            const unsigned int* __restrict__ V, const unsigned int* __restrict__ dO,
            const float* __restrict__ LSE2, const float* __restrict__ Dv,
            f16* __restrict__ dQ, int S, float scala_log2, float scala, int causale)
{
    __shared__ unsigned int Qs[BQ * QSTR], dOs[BQ * QSTR], Ks[BK * QSTR], Vs[BK * QSTR];
    __shared__ unsigned int dSs[BQ * SST];
    __shared__ float Ls[BQ], Ds[BQ];

    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;      /* query tr + 8i, chiavi tc + 16j */
    const int bh = blockIdx.y, q0 = blockIdx.x * BQ;
    const size_t base = (size_t)bh * S * D2;

    carica(Qs, Q, base, q0, BQ, S, t);
    carica(dOs, dO, base, q0, BQ, S, t);
    for (int i = t; i < BQ; i += NT) {
        const bool ok = q0 + i < S;
        Ls[i] = ok ? LSE2[(size_t)bh * S + q0 + i] : __builtin_inff();
        Ds[i] = ok ? Dv[(size_t)bh * S + q0 + i] : 0.0f;
    }

    float dq[4][DU];
    #pragma unroll
    for (int i = 0; i < 4; ++i)
        #pragma unroll
        for (int u = 0; u < DU; ++u) dq[i][u] = 0.0f;

    int nk = (S + BK - 1) / BK;
    if (causale) {
        const int ultimo = (q0 + BQ - 1) / BK + 1;
        nk = nk < ultimo ? nk : ultimo;
    }
    const f16* Kh = (const f16*)Ks;

    for (int kb = 0; kb < nk; ++kb) {
        const int k0 = kb * BK;
        __syncthreads();
        carica(Ks, K, base, k0, BK, S, t);
        carica(Vs, V, base, k0, BK, S, t);
        __syncthreads();

        float s[4][4], dp[4][4];
        #pragma unroll
        for (int i = 0; i < 4; ++i)
            #pragma unroll
            for (int j = 0; j < 4; ++j) { s[i][j] = 0.0f; dp[i][j] = 0.0f; }
        #pragma unroll 2
        for (int c = 0; c < D2; c += 4) {
            u4 qa[4], oa[4], ka[4], va[4];
            #pragma unroll
            for (int i = 0; i < 4; ++i) {
                qa[i] = *(const u4*)(Qs + (tr + 8 * i) * QSTR + c);
                oa[i] = *(const u4*)(dOs + (tr + 8 * i) * QSTR + c);
            }
            #pragma unroll
            for (int j = 0; j < 4; ++j) {
                ka[j] = *(const u4*)(Ks + (tc + 16 * j) * QSTR + c);
                va[j] = *(const u4*)(Vs + (tc + 16 * j) * QSTR + c);
            }
            #pragma unroll
            for (int i = 0; i < 4; ++i)
                #pragma unroll
                for (int j = 0; j < 4; ++j)
                    #pragma unroll
                    for (int e = 0; e < 4; ++e) {
                        s[i][j]  = DOT2(come_h2(el(qa[i], e)), come_h2(el(ka[j], e)), s[i][j]);
                        dp[i][j] = DOT2(come_h2(el(oa[i], e)), come_h2(el(va[j], e)), dp[i][j]);
                    }
        }

        f16* dSh = (f16*)dSs;
        #pragma unroll
        for (int i = 0; i < 4; ++i) {
            const int ql = tr + 8 * i, q = q0 + ql;
            #pragma unroll
            for (int j = 0; j < 4; ++j) {
                const int kl = tc + 16 * j, key = k0 + kl;
                const bool valido = (q < S) && (key < S) && (!causale || key <= q);
                const float p = valido ? __builtin_amdgcn_exp2f(s[i][j] * scala_log2 - Ls[ql]) : 0.0f;
                dSh[ql * (2 * SST) + kl] = (f16)(p * (dp[i][j] - Ds[ql]));
            }
        }
        __syncthreads();

        /* dQ += dS K: dot2 lungo coppie di chiavi */
        #pragma unroll 2
        for (int kp4 = 0; kp4 < BK / 2; kp4 += 4) {
            u4 sa[4];
            #pragma unroll
            for (int i = 0; i < 4; ++i) sa[i] = *(const u4*)(dSs + (tr + 8 * i) * SST + kp4);
            #pragma unroll
            for (int e = 0; e < 4; ++e) {
                const int key = 2 * (kp4 + e);
                #pragma unroll
                for (int u = 0; u < DU; ++u) {
                    const int d = tc + 16 * u;
                    const h2 k2 = {Kh[key * 2 * QSTR + d], Kh[(key + 1) * 2 * QSTR + d]};
                    #pragma unroll
                    for (int i = 0; i < 4; ++i) dq[i][u] = DOT2(come_h2(el(sa[i], e)), k2, dq[i][u]);
                }
            }
        }
    }

    #pragma unroll
    for (int i = 0; i < 4; ++i) {
        const int q = q0 + tr + 8 * i;
        if (q < S) {
            f16* rq = dQ + ((size_t)bh * S + q) * HEAD_DIM;
            #pragma unroll
            for (int u = 0; u < DU; ++u) rq[tc + 16 * u] = (f16)(dq[i][u] * scala);
        }
    }
}
"""

_lock = threading.Lock()
_funzioni = {}


def _funzione(nome, sorgente, head_dim):
    with _lock:
        chiave = (nome, head_dim)
        if chiave not in _funzioni:
            fa2_avanti._funzione(head_dim)              # inizializza fa2_avanti._hip
            hip = fa2_avanti._hip
            codice = fa2_avanti.compila(head_dim, sorgente=sorgente)
            mod, f = vp(), vp()
            assert hip.hipModuleLoadData(ctypes.byref(mod), codice) == 0
            assert hip.hipModuleGetFunction(ctypes.byref(f), mod, nome.encode()) == 0
            _funzioni[chiave] = (f, codice, mod)
        return _funzioni[chiave][0]


def _lancia(f, griglia, a):
    args = (vp * len(a))(*[ctypes.cast(ctypes.byref(x), vp) for x in a])
    stream = torch.cuda.current_stream().cuda_stream
    rc = fa2_avanti._hip.hipModuleLaunchKernel(f, griglia[0], griglia[1], 1, 128, 1, 1, 0, vp(stream), args, None)
    if rc != 0:
        raise RuntimeError(f"hipModuleLaunchKernel rc={rc}")


def flash_indietro(do, q, k, v, o, lse2, is_causal=False, scale=None):
    """Restituisce (dq, dk, dv), fp16, stessa forma di q."""
    B, H, S, D = q.shape
    q, k, v, o, do = (x.contiguous() for x in (q, k, v, o, do))
    sc = scale if scale is not None else D ** -0.5
    sl2 = sc * 1.4426950408889634
    dvec = (do.float() * o.float()).sum(-1).contiguous()
    dq, dk, dv = torch.empty_like(q), torch.empty_like(k), torch.empty_like(v)
    c = ctypes.c_int(1 if is_causal else 0)
    p = lambda t: vp(t.data_ptr())
    _lancia(_funzione("fa2_dkdv", SORGENTE_DKDV, D), ((S + 31) // 32, B * H),
            [p(q), p(k), p(v), p(do), p(lse2), p(dvec), p(dk), p(dv),
             ctypes.c_int(S), ctypes.c_float(sl2), ctypes.c_float(sc), c])
    _lancia(_funzione("fa2_dq", SORGENTE_DQ, D), ((S + 31) // 32, B * H),
            [p(q), p(k), p(v), p(do), p(lse2), p(dvec), p(dq),
             ctypes.c_int(S), ctypes.c_float(sl2), ctypes.c_float(sc), c])
    return dq, dk, dv


class FlashAttenzione(torch.autograd.Function):
    @staticmethod
    def forward(ctx, q, k, v, is_causal=False, scale=None):
        o, lse2 = fa2_avanti.flash_avanti(q, k, v, is_causal=is_causal, scale=scale, lse=True)
        ctx.save_for_backward(q, k, v, o, lse2)
        ctx.is_causal, ctx.scale = is_causal, scale
        return o

    @staticmethod
    def backward(ctx, do):
        q, k, v, o, lse2 = ctx.saved_tensors
        dq, dk, dv = flash_indietro(do, q, k, v, o, lse2, ctx.is_causal, ctx.scale)
        return dq, dk, dv, None, None


def flash_attenzione(q, k, v, is_causal=False, scale=None):
    return FlashAttenzione.apply(q, k, v, is_causal, scale)

"""Flash attention per gfx906 (Radeon VII) — avanti e indietro, versione da collegare.

2S, 19 ott 2026. Generalizza fa2_avanti.py / fa2_indietro.py (stesso disegno, vedi
STATO.md) con quello che serve a scaled_dot_product_attention:
  - stride qualunque per batch, testa e sequenza (ultima dimensione contigua);
  - S_q != S_k; maschera causale allineata IN ALTO A SINISTRA come in PyTorch: chiave <= query;
  - dropout: maschera da un hash deterministico di (seme, testa, query, chiave), rigenerata
    nell'indietro senza salvarla. Il denominatore del softmax usa P intera, P·V quella
    abbandonata e riscalata di 1/(1-p), come FlashAttention.
20 ott 2026: head_dim 256 (Qwen3.5-4B, kernel dedicati a 512 thread) e GQA (K/V con meno teste,
senza ripeterle in memoria; dK/dV sommano le teste di query del gruppo dentro il kernel).

Interfaccia:
    o, lse2 = avanti(q, k, v, causale=False, scala=None, dropout=0.0, seme=0)
    dq, dk, dv = indietro(do, q, k, v, o, lse2, causale=False, scala=None, dropout=0.0, seme=0)
    o = attenzione(q, k, v, causale=False, scala=None, dropout=0.0, seme=None)   # autograd
q: [B, H, S_q, D], k e v: [B, H_kv, S_k, D] con H multiplo di H_kv (la testa h legge h // (H/H_kv)),
fp16, D in {64, 128, 256}. lse2: [B, H, S_q] fp32, logsumexp in base 2 della scala per log2(e)
(naturale = lse2 * ln 2). Uscite e gradienti contigui; dk e dv hanno la forma di k e v.
"""
import ctypes
import os
import threading

import torch

vp = ctypes.c_void_p
LOG2E = 1.4426950408889634

COMUNE = r"""
typedef _Float16 f16;
typedef _Float16 h2 __attribute__((ext_vector_type(2)));
typedef unsigned int u4 __attribute__((ext_vector_type(4)));
typedef long long i64;
#define D2 (HEAD_DIM / 2)
#define QSTR (D2 + 4)            /* passo delle righe in LDS, in dword (h2) */
#define DU (HEAD_DIM / 16)       /* colonne d per thread: d = tc + 16 u */
__device__ inline h2 come_h2(unsigned int x) { return __builtin_bit_cast(h2, x); }
__device__ inline unsigned int come_u(h2 x) { return __builtin_bit_cast(unsigned int, x); }
__device__ inline unsigned int el(u4 v, int e) { return e == 0 ? v.x : e == 1 ? v.y : e == 2 ? v.z : v.w; }
#define DOT2(a, b, c) __builtin_amdgcn_fdot2((a), (b), (c), false)

/* hash a 32 bit (finalizzatore di tipo murmur); la stessa formula e' in Python per i banchi */
__device__ inline unsigned int mescola(unsigned int x) {
    x ^= x >> 16; x *= 0x7feb352du; x ^= x >> 15; x *= 0x846ca68bu; x ^= x >> 16; return x;
}
__device__ inline unsigned int seme_riga(unsigned int s0, unsigned int s1, int bh, int q) {
    return mescola(mescola(s0 ^ mescola((unsigned int)bh * 0x9E3779B9u + s1)) ^ ((unsigned int)q * 0x85EBCA6Bu));
}
__device__ inline bool tenuto(unsigned int sr, int k, unsigned int soglia) {
    return mescola(sr ^ ((unsigned int)k * 0xC2B2AE35u + 0x27D4EB2Fu)) >= soglia;
}

/* 'righe' righe da r0 di un tensore a passo di riga 'passo' (elementi) nella LDS, zeri oltre n */
__device__ inline void carica(unsigned int* dst, const f16* src, i64 passo, int r0, int righe, int n, int t, int nt) {
    for (int idx = t; idx < righe * D2 / 4; idx += nt) {
        const int riga = idx / (D2 / 4), col = (idx - riga * (D2 / 4)) * 4;
        u4 x = {0u, 0u, 0u, 0u};
        if (r0 + riga < n) x = *(const u4*)(src + (i64)(r0 + riga) * passo + 2 * col);
        *(u4*)(dst + riga * QSTR + col) = x;
    }
}
"""

SORGENTE_AVANTI = COMUNE + r"""
#define BR 64
#define BC 64
#define NT 256
#define VSTR (HEAD_DIM + 4)
#define PSTR (BC / 2 + 4)

extern "C" __global__ __launch_bounds__(NT)
void fa_avanti(const f16* __restrict__ Q, const f16* __restrict__ K, const f16* __restrict__ V,
               f16* __restrict__ O, float* __restrict__ LSE2,
               i64 qb_, i64 qh_, i64 qs_, i64 kb_, i64 kh_, i64 ks_, i64 vb_, i64 vh_, i64 vs_,
               int H, int G, int Sq, int Sk, float scala_log2, int causale,
               unsigned int s0, unsigned int s1, unsigned int soglia, float riscala)
{
    __shared__ unsigned int Qs[BR * QSTR];
    __shared__ unsigned int Ks[BC * QSTR];
    __shared__ unsigned int Vt[(BC / 2) * VSTR];
    __shared__ unsigned int Ps[BR * PSTR];

    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;
    const int bh = blockIdx.y, b = bh / H, h = bh - b * H;
    const int r0 = blockIdx.x * BR;
    const f16* Qp = Q + b * qb_ + h * qh_;
    const f16* Kp = K + b * kb_ + (h / G) * kh_;   /* GQA */
    const f16* Vp = V + b * vb_ + (h / G) * vh_;

    carica(Qs, Qp, qs_, r0, BR, Sq, t, NT);

    float o[4][DU], m[4], l[4];
    unsigned int sr[4];
    #pragma unroll
    for (int i = 0; i < 4; ++i) {
        m[i] = -__builtin_inff(); l[i] = 0.0f;
        sr[i] = seme_riga(s0, s1, bh, r0 + tr + 16 * i);
        #pragma unroll
        for (int u = 0; u < DU; ++u) o[i][u] = 0.0f;
    }

    int n_blocchi = (Sk + BC - 1) / BC;
    if (causale) {
        const int ultimo = (r0 + BR - 1) / BC + 1;
        n_blocchi = n_blocchi < ultimo ? n_blocchi : ultimo;
    }

    for (int bk = 0; bk < n_blocchi; ++bk) {
        const int c0 = bk * BC;
        __syncthreads();
        carica(Ks, Kp, ks_, c0, BC, Sk, t, NT);
        for (int idx = t; idx < (BC / 2) * D2; idx += NT) {
            const int kp = idx / D2, c = idx - kp * D2;
            const int k = c0 + 2 * kp;
            const unsigned int a = (k < Sk) ? *(const unsigned int*)(Vp + (i64)k * vs_ + 2 * c) : 0u;
            const unsigned int z = (k + 1 < Sk) ? *(const unsigned int*)(Vp + (i64)(k + 1) * vs_ + 2 * c) : 0u;
            const h2 ha = come_h2(a), hz = come_h2(z);
            const h2 lo = {ha.x, hz.x}, hi = {ha.y, hz.y};
            Vt[kp * VSTR + 2 * c] = come_u(lo);
            Vt[kp * VSTR + 2 * c + 1] = come_u(hi);
        }
        __syncthreads();

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
                for (int j = 0; j < 4; ++j)
                    #pragma unroll
                    for (int e = 0; e < 4; ++e)
                        s[i][j] = DOT2(come_h2(el(qa[i], e)), come_h2(el(kb[j], e)), s[i][j]);
        }

        f16* Ph = (f16*)Ps;
        #pragma unroll
        for (int i = 0; i < 4; ++i) {
            const int r = r0 + tr + 16 * i;
            float mx = -__builtin_inff();
            #pragma unroll
            for (int j = 0; j < 4; ++j) {
                const int c = c0 + tc + 16 * j;
                const bool valido = (c < Sk) && (!causale || c <= r);
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
                corr = __builtin_amdgcn_exp2f(m[i] - mn);
                #pragma unroll
                for (int j = 0; j < 4; ++j) {
                    const float p = __builtin_amdgcn_exp2f(s[i][j] - mn);
                    somma += p;
                    s[i][j] = (soglia == 0u || tenuto(sr[i], c0 + tc + 16 * j, soglia)) ? p * riscala : 0.0f;
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

        #pragma unroll 2
        for (int kp4 = 0; kp4 < BC / 2; kp4 += 4) {
            u4 pa[4];
            #pragma unroll
            for (int i = 0; i < 4; ++i) pa[i] = *(const u4*)(Ps + (tr + 16 * i) * PSTR + kp4);
            #pragma unroll
            for (int e = 0; e < 4; ++e)
                #pragma unroll
                for (int u = 0; u < DU; ++u) {
                    const h2 vv = come_h2(Vt[(kp4 + e) * VSTR + tc + 16 * u]);
                    #pragma unroll
                    for (int i = 0; i < 4; ++i) o[i][u] = DOT2(come_h2(el(pa[i], e)), vv, o[i][u]);
                }
        }
    }

    #pragma unroll
    for (int i = 0; i < 4; ++i) {
        const int r = r0 + tr + 16 * i;
        if (r < Sq) {
            const float inv = l[i] > 0.0f ? 1.0f / l[i] : 0.0f;
            f16* riga = O + ((i64)bh * Sq + r) * HEAD_DIM;
            #pragma unroll
            for (int u = 0; u < DU; ++u) riga[tc + 16 * u] = (f16)(o[i][u] * inv);
            if (tc == 0) LSE2[(i64)bh * Sq + r] = l[i] > 0.0f ? m[i] + __log2f(l[i]) : __builtin_inff();
        }
    }
}
"""

SORGENTE_DKDV = COMUNE + r"""
#define NT 256
#define BK 64                                   /* chiavi ferme: tr + 16a */
#define BQ (HEAD_DIM == 128 ? 32 : 64)          /* query che scorrono: tc + 16b, b < NB */
#define NB (BQ / 16)
#define PST (BQ / 2 + 4)

extern "C" __global__ __launch_bounds__(NT)
void fa_dkdv(const f16* __restrict__ Q, const f16* __restrict__ K, const f16* __restrict__ V,
             const f16* __restrict__ dO, const float* __restrict__ LSE2, const float* __restrict__ Dv,
             f16* __restrict__ dK, f16* __restrict__ dV,
             i64 qb_, i64 qh_, i64 qs_, i64 kb_, i64 kh_, i64 ks_, i64 vb_, i64 vh_, i64 vs_,
             i64 ob_, i64 oh_, i64 os_,
             int H, int G, int Sq, int Sk, float scala_log2, float scala, int causale,
             unsigned int s0, unsigned int s1, unsigned int soglia, float riscala)
{
    __shared__ unsigned int Ks[BK * QSTR], Vs[BK * QSTR], Qs[BQ * QSTR], dOs[BQ * QSTR];
    __shared__ unsigned int PT[BK * PST], dST[BK * PST];
    __shared__ float Ls[BQ], Ds[BQ];

    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;      /* chiavi tr + 16a, query tc + 16b */
    const int Hk = H / G, bk = blockIdx.y, b = bk / Hk, hk = bk - b * Hk, k0 = blockIdx.x * BK;
    const f16* Kp = K + b * kb_ + hk * kh_;   /* una testa di K/V (GQA: H/G teste) */
    const f16* Vp = V + b * vb_ + hk * vh_;

    carica(Ks, Kp, ks_, k0, BK, Sk, t, NT);
    carica(Vs, Vp, vs_, k0, BK, Sk, t, NT);

    float dk[4][DU], dv[4][DU];
    #pragma unroll
    for (int a = 0; a < 4; ++a)
        #pragma unroll
        for (int u = 0; u < DU; ++u) { dk[a][u] = 0.0f; dv[a][u] = 0.0f; }

    const int nq = (Sq + BQ - 1) / BQ;
    const int qb0 = causale ? k0 / BQ : 0;
    const f16* Qh = (const f16*)Qs;
    const f16* dOh = (const f16*)dOs;

    for (int g = 0; g < G; ++g) {            /* le G teste di query che leggono questa K/V */
        const int h = hk * G + g, bh = b * H + h;
        const f16* Qp = Q + b * qb_ + h * qh_;
        const f16* Op = dO + b * ob_ + h * oh_;
        for (int qb = qb0; qb < nq; ++qb) {
            const int q0 = qb * BQ;
            __syncthreads();
            carica(Qs, Qp, qs_, q0, BQ, Sq, t, NT);
            carica(dOs, Op, os_, q0, BQ, Sq, t, NT);
            for (int i = t; i < BQ; i += NT) {
                const bool ok = q0 + i < Sq;
                Ls[i] = ok ? LSE2[(i64)bh * Sq + q0 + i] : __builtin_inff();
                Ds[i] = ok ? Dv[(i64)bh * Sq + q0 + i] : 0.0f;
            }
            __syncthreads();

            float st[4][NB], dpt[4][NB];
            #pragma unroll
            for (int a = 0; a < 4; ++a)
                #pragma unroll
                for (int bb = 0; bb < NB; ++bb) { st[a][bb] = 0.0f; dpt[a][bb] = 0.0f; }
            #pragma unroll 2
            for (int c = 0; c < D2; c += 4) {
                u4 ka[4], va[4], qa[NB], oa[NB];
                #pragma unroll
                for (int a = 0; a < 4; ++a) {
                    ka[a] = *(const u4*)(Ks + (tr + 16 * a) * QSTR + c);
                    va[a] = *(const u4*)(Vs + (tr + 16 * a) * QSTR + c);
                }
                #pragma unroll
                for (int bb = 0; bb < NB; ++bb) {
                    qa[bb] = *(const u4*)(Qs + (tc + 16 * bb) * QSTR + c);
                    oa[bb] = *(const u4*)(dOs + (tc + 16 * bb) * QSTR + c);
                }
                #pragma unroll
                for (int a = 0; a < 4; ++a)
                    #pragma unroll
                    for (int bb = 0; bb < NB; ++bb)
                        #pragma unroll
                        for (int e = 0; e < 4; ++e) {
                            st[a][bb]  = DOT2(come_h2(el(ka[a], e)), come_h2(el(qa[bb], e)), st[a][bb]);
                            dpt[a][bb] = DOT2(come_h2(el(va[a], e)), come_h2(el(oa[bb], e)), dpt[a][bb]);
                        }
            }

            f16* PTh = (f16*)PT;
            f16* dSTh = (f16*)dST;
            #pragma unroll
            for (int bb = 0; bb < NB; ++bb) {
                const int ql = tc + 16 * bb, q = q0 + ql;
                const unsigned int sr = seme_riga(s0, s1, bh, q);
                #pragma unroll
                for (int a = 0; a < 4; ++a) {
                    const int key = k0 + tr + 16 * a;
                    const bool valido = (q < Sq) && (key < Sk) && (!causale || key <= q);
                    const float p = valido ? __builtin_amdgcn_exp2f(st[a][bb] * scala_log2 - Ls[ql]) : 0.0f;
                    const bool tiene = soglia == 0u || tenuto(sr, key, soglia);
                    const float pd = tiene ? p * riscala : 0.0f;               /* P abbandonata: per dV */
                    const float dp = tiene ? dpt[a][bb] * riscala : 0.0f;      /* gradiente rispetto a P */
                    PTh[(tr + 16 * a) * (2 * PST) + ql] = (f16)pd;
                    dSTh[(tr + 16 * a) * (2 * PST) + ql] = (f16)(p * (dp - Ds[ql]));
                }
            }
            __syncthreads();

            #pragma unroll 2
            for (int qp4 = 0; qp4 < BQ / 2; qp4 += 4) {
                u4 pa[4], sa[4];
                #pragma unroll
                for (int a = 0; a < 4; ++a) {
                    pa[a] = *(const u4*)(PT + (tr + 16 * a) * PST + qp4);
                    sa[a] = *(const u4*)(dST + (tr + 16 * a) * PST + qp4);
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
    }

    #pragma unroll
    for (int a = 0; a < 4; ++a) {
        const int key = k0 + tr + 16 * a;
        if (key < Sk) {
            f16* rk = dK + ((i64)bk * Sk + key) * HEAD_DIM;
            f16* rv = dV + ((i64)bk * Sk + key) * HEAD_DIM;
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
#define NT 256
#define BQ 64                                   /* query ferme: tr + 16i */
#define BK (HEAD_DIM == 128 ? 32 : 64)          /* chiavi che scorrono: tc + 16j, j < NJ */
#define NJ (BK / 16)
#define SST (BK / 2 + 4)

extern "C" __global__ __launch_bounds__(NT)
void fa_dq(const f16* __restrict__ Q, const f16* __restrict__ K, const f16* __restrict__ V,
           const f16* __restrict__ dO, const float* __restrict__ LSE2, const float* __restrict__ Dv,
           f16* __restrict__ dQ,
           i64 qb_, i64 qh_, i64 qs_, i64 kb_, i64 kh_, i64 ks_, i64 vb_, i64 vh_, i64 vs_,
           i64 ob_, i64 oh_, i64 os_,
           int H, int G, int Sq, int Sk, float scala_log2, float scala, int causale,
           unsigned int s0, unsigned int s1, unsigned int soglia, float riscala)
{
    __shared__ unsigned int Qs[BQ * QSTR], dOs[BQ * QSTR], Ks[BK * QSTR], Vs[BK * QSTR];
    __shared__ unsigned int dSs[BQ * SST];
    __shared__ float Ls[BQ], Ds[BQ];

    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;      /* query tr + 16i, chiavi tc + 16j */
    const int bh = blockIdx.y, b = bh / H, h = bh - b * H, q0 = blockIdx.x * BQ;
    const f16* Qp = Q + b * qb_ + h * qh_;
    const f16* Kp = K + b * kb_ + (h / G) * kh_;   /* GQA */
    const f16* Vp = V + b * vb_ + (h / G) * vh_;
    const f16* Op = dO + b * ob_ + h * oh_;

    carica(Qs, Qp, qs_, q0, BQ, Sq, t, NT);
    carica(dOs, Op, os_, q0, BQ, Sq, t, NT);
    for (int i = t; i < BQ; i += NT) {
        const bool ok = q0 + i < Sq;
        Ls[i] = ok ? LSE2[(i64)bh * Sq + q0 + i] : __builtin_inff();
        Ds[i] = ok ? Dv[(i64)bh * Sq + q0 + i] : 0.0f;
    }

    float dq[4][DU];
    unsigned int sr[4];
    #pragma unroll
    for (int i = 0; i < 4; ++i) {
        sr[i] = seme_riga(s0, s1, bh, q0 + tr + 16 * i);
        #pragma unroll
        for (int u = 0; u < DU; ++u) dq[i][u] = 0.0f;
    }

    int nk = (Sk + BK - 1) / BK;
    if (causale) {
        const int ultimo = (q0 + BQ - 1) / BK + 1;
        nk = nk < ultimo ? nk : ultimo;
    }
    const f16* Kh = (const f16*)Ks;

    for (int kb = 0; kb < nk; ++kb) {
        const int k0 = kb * BK;
        __syncthreads();
        carica(Ks, Kp, ks_, k0, BK, Sk, t, NT);
        carica(Vs, Vp, vs_, k0, BK, Sk, t, NT);
        __syncthreads();

        float s[4][NJ], dp[4][NJ];
        #pragma unroll
        for (int i = 0; i < 4; ++i)
            #pragma unroll
            for (int j = 0; j < NJ; ++j) { s[i][j] = 0.0f; dp[i][j] = 0.0f; }
        #pragma unroll 2
        for (int c = 0; c < D2; c += 4) {
            u4 qa[4], oa[4], ka[NJ], va[NJ];
            #pragma unroll
            for (int i = 0; i < 4; ++i) {
                qa[i] = *(const u4*)(Qs + (tr + 16 * i) * QSTR + c);
                oa[i] = *(const u4*)(dOs + (tr + 16 * i) * QSTR + c);
            }
            #pragma unroll
            for (int j = 0; j < NJ; ++j) {
                ka[j] = *(const u4*)(Ks + (tc + 16 * j) * QSTR + c);
                va[j] = *(const u4*)(Vs + (tc + 16 * j) * QSTR + c);
            }
            #pragma unroll
            for (int i = 0; i < 4; ++i)
                #pragma unroll
                for (int j = 0; j < NJ; ++j)
                    #pragma unroll
                    for (int e = 0; e < 4; ++e) {
                        s[i][j]  = DOT2(come_h2(el(qa[i], e)), come_h2(el(ka[j], e)), s[i][j]);
                        dp[i][j] = DOT2(come_h2(el(oa[i], e)), come_h2(el(va[j], e)), dp[i][j]);
                    }
        }

        f16* dSh = (f16*)dSs;
        #pragma unroll
        for (int i = 0; i < 4; ++i) {
            const int ql = tr + 16 * i, q = q0 + ql;
            #pragma unroll
            for (int j = 0; j < NJ; ++j) {
                const int kl = tc + 16 * j, key = k0 + kl;
                const bool valido = (q < Sq) && (key < Sk) && (!causale || key <= q);
                const float p = valido ? __builtin_amdgcn_exp2f(s[i][j] * scala_log2 - Ls[ql]) : 0.0f;
                const bool tiene = soglia == 0u || tenuto(sr[i], key, soglia);
                const float d = tiene ? dp[i][j] * riscala : 0.0f;
                dSh[ql * (2 * SST) + kl] = (f16)(p * (d - Ds[ql]));
            }
        }
        __syncthreads();

        #pragma unroll 2
        for (int kp4 = 0; kp4 < BK / 2; kp4 += 4) {
            u4 sa[4];
            #pragma unroll
            for (int i = 0; i < 4; ++i) sa[i] = *(const u4*)(dSs + (tr + 16 * i) * SST + kp4);
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
        const int q = q0 + tr + 16 * i;
        if (q < Sq) {
            f16* rq = dQ + ((i64)bh * Sq + q) * HEAD_DIM;
            #pragma unroll
            for (int u = 0; u < DU; ++u) rq[tc + 16 * u] = (f16)(dq[i][u] * scala);
        }
    }
}
"""

# ---------------------------------------------------------------------------------------------
# HEAD_DIM 256 (Qwen3.5-4B, attenzione piena). Una riga è 528 byte in LDS: Q, K e V a 64 righe
# (~100 KB) non stanno nei 64 KB, né K, V, Q, dO dell'indietro. Tre kernel dedicati:
#  - avanti: 64 query ferme (Q intera in LDS), 32 chiavi che scorrono; K e poi V^T nello stesso
#    spazio (V letta nei registri prima di Q·K e scritta in LDS dopo);
#  - dK/dV e dQ: la fase Q·K / dO·V scorre la dimensione d a pezzi di 64 colonne (tutti e quattro
#    gli operandi in LDS a pezzi, tessere 2x4 e 4x4 per thread); la fase di accumulo cambia
#    disposizione: ogni onda tiene 8 chiavi (16 query) x 4 colonne per corsia, così P/dS si leggono
#    in broadcast e le coppie lungo query/chiavi si compongono da due letture b64 con v_perm.
# ---------------------------------------------------------------------------------------------
COMUNE_256 = COMUNE + r"""
#define CH2 32                    /* dword (coppie di d) per pezzo nella fase Q·K */
#define CST (CH2 + 4)
typedef unsigned int u2 __attribute__((ext_vector_type(2)));
/* coppie (x, y) lungo righe vicine: x e y sono due dword (d, d+1) delle righe r e r+1 */
__device__ inline unsigned int basse(unsigned int x, unsigned int y) { return __builtin_amdgcn_perm(y, x, 0x05040100u); }
__device__ inline unsigned int alte(unsigned int x, unsigned int y) { return __builtin_amdgcn_perm(y, x, 0x07060302u); }

/* un pezzo di CH2 dword (da col0) di 'righe' righe, passo CST in LDS, zeri oltre n */
__device__ inline void pezzo(unsigned int* dst, const f16* src, i64 passo, int r0, int righe, int n, int col0, int t) {
    for (int idx = t; idx < righe * (CH2 / 4); idx += NT) {
        const int riga = idx / (CH2 / 4), col = (idx - riga * (CH2 / 4)) * 4;
        u4 x = {0u, 0u, 0u, 0u};
        if (r0 + riga < n) x = *(const u4*)(src + (i64)(r0 + riga) * passo + 2 * (col0 + col));
        *(u4*)(dst + riga * CST + col) = x;
    }
}

/* acc[r][s] += A[ra + PA r] · B[rb + PB s] lungo le CH2 dword di un pezzo (passo CST) */
template <int NR, int NS, int PA, int PB>
__device__ inline void tessera(float (&acc)[NR][NS], const unsigned int* A, int ra, const unsigned int* B, int rb) {
    #pragma unroll 2
    for (int c = 0; c < CH2; c += 4) {
        u4 x[NR], y[NS];
        #pragma unroll
        for (int r = 0; r < NR; ++r) x[r] = *(const u4*)(A + (ra + PA * r) * CST + c);
        #pragma unroll
        for (int q = 0; q < NS; ++q) y[q] = *(const u4*)(B + (rb + PB * q) * CST + c);
        #pragma unroll
        for (int r = 0; r < NR; ++r)
            #pragma unroll
            for (int q = 0; q < NS; ++q)
                #pragma unroll
                for (int e = 0; e < 4; ++e) acc[r][q] = DOT2(come_h2(el(x[r], e)), come_h2(el(y[q], e)), acc[r][q]);
    }
}
"""

SORGENTE_AVANTI_256 = COMUNE_256 + r"""
#define BR 64
#define BC 32
#define NJ (BC / 16)                       /* chiavi per thread: tc + 16j */
#define RS (NT / 16)                       /* righe per thread: tr + RS i, i < RI */
#define RI (BR / RS)
#define VSTR (HEAD_DIM + 4)
#define PSTR (BC / 2 + 4)
#define KVN (BC * QSTR > (BC / 2) * VSTR ? BC * QSTR : (BC / 2) * VSTR)
#define NV ((BC / 2) * D2 / NT)            /* coppie di righe di V portate da ogni thread */

extern "C" __global__ __launch_bounds__(NT)
void fa_avanti(const f16* __restrict__ Q, const f16* __restrict__ K, const f16* __restrict__ V,
               f16* __restrict__ O, float* __restrict__ LSE2,
               i64 qb_, i64 qh_, i64 qs_, i64 kb_, i64 kh_, i64 ks_, i64 vb_, i64 vh_, i64 vs_,
               int H, int G, int Sq, int Sk, float scala_log2, int causale,
               unsigned int s0, unsigned int s1, unsigned int soglia, float riscala)
{
    __shared__ unsigned int Qs[BR * QSTR];
    __shared__ unsigned int KV[KVN];       /* K, poi V trasposta a coppie di chiavi */
    __shared__ unsigned int Ps[BR * PSTR];

    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;
    const int bh = blockIdx.y, b = bh / H, h = bh - b * H;
    /* causale: prima i blocchi con più chiavi (gli ultimi), per accorciare la coda */
    const int r0 = (causale ? gridDim.x - 1 - blockIdx.x : blockIdx.x) * BR;
    const f16* Qp = Q + b * qb_ + h * qh_;
    const f16* Kp = K + b * kb_ + (h / G) * kh_;   /* GQA */
    const f16* Vp = V + b * vb_ + (h / G) * vh_;

    carica(Qs, Qp, qs_, r0, BR, Sq, t, NT);

    float o[RI][DU], m[RI], l[RI];
    unsigned int sr[RI];
    #pragma unroll
    for (int i = 0; i < RI; ++i) {
        m[i] = -__builtin_inff(); l[i] = 0.0f;
        sr[i] = seme_riga(s0, s1, bh, r0 + tr + RS * i);
        #pragma unroll
        for (int u = 0; u < DU; ++u) o[i][u] = 0.0f;
    }

    int n_blocchi = (Sk + BC - 1) / BC;
    if (causale) {
        const int ultimo = (r0 + BR - 1) / BC + 1;
        n_blocchi = n_blocchi < ultimo ? n_blocchi : ultimo;
    }
    const int vc = t & (D2 - 1), vk = t / D2;   /* colonna (dword) e coppia di partenza per V */

    for (int bk = 0; bk < n_blocchi; ++bk) {
        const int c0 = bk * BC;
        __syncthreads();
        carica(KV, Kp, ks_, c0, BC, Sk, t, NT);
        unsigned int va[NV], vz[NV];
        #pragma unroll
        for (int n = 0; n < NV; ++n) {
            const int k = c0 + 2 * (vk + n * (NT / D2));
            va[n] = (k < Sk) ? *(const unsigned int*)(Vp + (i64)k * vs_ + 2 * vc) : 0u;
            vz[n] = (k + 1 < Sk) ? *(const unsigned int*)(Vp + (i64)(k + 1) * vs_ + 2 * vc) : 0u;
        }
        __syncthreads();

        float s[RI][NJ];
        #pragma unroll
        for (int i = 0; i < RI; ++i)
            #pragma unroll
            for (int j = 0; j < NJ; ++j) s[i][j] = 0.0f;
        #pragma unroll 2
        for (int c = 0; c < D2; c += 4) {
            u4 qa[RI], kb[NJ];
            #pragma unroll
            for (int i = 0; i < RI; ++i) qa[i] = *(const u4*)(Qs + (tr + RS * i) * QSTR + c);
            #pragma unroll
            for (int j = 0; j < NJ; ++j) kb[j] = *(const u4*)(KV + (tc + 16 * j) * QSTR + c);
            #pragma unroll
            for (int i = 0; i < RI; ++i)
                #pragma unroll
                for (int j = 0; j < NJ; ++j)
                    #pragma unroll
                    for (int e = 0; e < 4; ++e)
                        s[i][j] = DOT2(come_h2(el(qa[i], e)), come_h2(el(kb[j], e)), s[i][j]);
        }

        f16* Ph = (f16*)Ps;
        #pragma unroll
        for (int i = 0; i < RI; ++i) {
            const int r = r0 + tr + RS * i;
            float mx = -__builtin_inff();
            #pragma unroll
            for (int j = 0; j < NJ; ++j) {
                const int c = c0 + tc + 16 * j;
                const bool valido = (c < Sk) && (!causale || c <= r);
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
                corr = __builtin_amdgcn_exp2f(m[i] - mn);
                #pragma unroll
                for (int j = 0; j < NJ; ++j) {
                    const float p = __builtin_amdgcn_exp2f(s[i][j] - mn);
                    somma += p;
                    s[i][j] = (soglia == 0u || tenuto(sr[i], c0 + tc + 16 * j, soglia)) ? p * riscala : 0.0f;
                }
            } else {
                #pragma unroll
                for (int j = 0; j < NJ; ++j) s[i][j] = 0.0f;
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
            for (int j = 0; j < NJ; ++j) Ph[(tr + RS * i) * (2 * PSTR) + tc + 16 * j] = (f16)s[i][j];
        }
        __syncthreads();                    /* K letta da tutti: lo spazio passa a V^T */
        #pragma unroll
        for (int n = 0; n < NV; ++n) {
            const h2 ha = come_h2(va[n]), hz = come_h2(vz[n]);
            const h2 lo = {ha.x, hz.x}, hi = {ha.y, hz.y};
            u2 x = {come_u(lo), come_u(hi)};
            *(u2*)(KV + (vk + n * (NT / D2)) * VSTR + 2 * vc) = x;
        }
        __syncthreads();

        #pragma unroll 2
        for (int kp4 = 0; kp4 < BC / 2; kp4 += 4) {
            u4 pa[RI];
            #pragma unroll
            for (int i = 0; i < RI; ++i) pa[i] = *(const u4*)(Ps + (tr + RS * i) * PSTR + kp4);
            #pragma unroll
            for (int e = 0; e < 4; ++e)
                #pragma unroll
                for (int u = 0; u < DU; ++u) {
                    const h2 vv = come_h2(KV[(kp4 + e) * VSTR + tc + 16 * u]);
                    #pragma unroll
                    for (int i = 0; i < RI; ++i) o[i][u] = DOT2(come_h2(el(pa[i], e)), vv, o[i][u]);
                }
        }
    }

    #pragma unroll
    for (int i = 0; i < RI; ++i) {
        const int r = r0 + tr + RS * i;
        if (r < Sq) {
            const float inv = l[i] > 0.0f ? 1.0f / l[i] : 0.0f;
            f16* riga = O + ((i64)bh * Sq + r) * HEAD_DIM;
            #pragma unroll
            for (int u = 0; u < DU; ++u) riga[tc + 16 * u] = (f16)(o[i][u] * inv);
            if (tc == 0) LSE2[(i64)bh * Sq + r] = l[i] > 0.0f ? m[i] + __log2f(l[i]) : __builtin_inff();
        }
    }
}
"""

SORGENTE_DKDV_256 = COMUNE_256 + r"""
#define BK 32                 /* chiavi ferme */
#define BQ 64                 /* query che scorrono */
#define QC 32                 /* query per pezzo nella fase di accumulo */
#define PST (BQ / 2 + 4)
#define NW (NT / 64)              /* onde */
#define QT (NT / 16)              /* fase S: query tc + QT b (b < NB), chiavi tr + 16a (a < NA) */
#define NA (BK / 16)
#define NB (BQ / QT)
#define AW (BK / NW)              /* accumulo: chiavi per onda */
#define SPAZIO_S ((2 * BK + 2 * BQ) * CST)
#define SPAZIO_A (2 * QC * QSTR)

extern "C" __global__ __launch_bounds__(NT)
void fa_dkdv(const f16* __restrict__ Q, const f16* __restrict__ K, const f16* __restrict__ V,
             const f16* __restrict__ dO, const float* __restrict__ LSE2, const float* __restrict__ Dv,
             f16* __restrict__ dK, f16* __restrict__ dV,
             i64 qb_, i64 qh_, i64 qs_, i64 kb_, i64 kh_, i64 ks_, i64 vb_, i64 vh_, i64 vs_,
             i64 ob_, i64 oh_, i64 os_,
             int H, int G, int Sq, int Sk, float scala_log2, float scala, int causale,
             unsigned int s0, unsigned int s1, unsigned int soglia, float riscala)
{
    __shared__ unsigned int buf[SPAZIO_S > SPAZIO_A ? SPAZIO_S : SPAZIO_A];
    __shared__ unsigned int PT[BK * PST], dST[BK * PST];
    __shared__ float Ls[BQ], Ds[BQ];
    unsigned int* Kc = buf;                 /* fase S: pezzi di CH2 dword */
    unsigned int* Vc = buf + BK * CST;
    unsigned int* Qc = buf + 2 * BK * CST;
    unsigned int* Oc = Qc + BQ * CST;
    unsigned int* Qa = buf;                 /* fase di accumulo: QC righe intere */
    unsigned int* Oa = buf + QC * QSTR;

    const int t = threadIdx.x;
    const int tr = t / QT, tc = t % QT;     /* fase S: chiavi tr + 16a, query tc + QT b */
    const int w = t >> 6, ln = t & 63;      /* accumulo: chiavi AW w + a, colonne 4 ln + x (x<4) */
    const int Hk = H / G, bk = blockIdx.y, b = bk / Hk, hk = bk - b * Hk, k0 = blockIdx.x * BK;
    const f16* Kp = K + b * kb_ + hk * kh_;   /* una testa di K/V (GQA: H/G teste) */
    const f16* Vp = V + b * vb_ + hk * vh_;

    float dk[AW][4], dv[AW][4];
    #pragma unroll
    for (int a = 0; a < AW; ++a)
        #pragma unroll
        for (int x = 0; x < 4; ++x) { dk[a][x] = 0.0f; dv[a][x] = 0.0f; }

    const int nq = (Sq + BQ - 1) / BQ;
    const int qb0 = causale ? k0 / BQ : 0;

    for (int g = 0; g < G; ++g) {            /* le G teste di query che leggono questa K/V */
        const int h = hk * G + g, bh = b * H + h;
        const f16* Qp = Q + b * qb_ + h * qh_;
        const f16* Op = dO + b * ob_ + h * oh_;
        for (int qb = qb0; qb < nq; ++qb) {
            const int q0 = qb * BQ;
            float st[NA][NB], dpt[NA][NB];
            #pragma unroll
            for (int a = 0; a < NA; ++a)
                #pragma unroll
                for (int bb = 0; bb < NB; ++bb) { st[a][bb] = 0.0f; dpt[a][bb] = 0.0f; }

            for (int ch = 0; ch < D2; ch += CH2) {
                __syncthreads();
                pezzo(Kc, Kp, ks_, k0, BK, Sk, ch, t);
                pezzo(Vc, Vp, vs_, k0, BK, Sk, ch, t);
                pezzo(Qc, Qp, qs_, q0, BQ, Sq, ch, t);
                pezzo(Oc, Op, os_, q0, BQ, Sq, ch, t);
                if (ch == 0)
                    for (int i = t; i < BQ; i += NT) {
                        const bool ok = q0 + i < Sq;
                        Ls[i] = ok ? LSE2[(i64)bh * Sq + q0 + i] : __builtin_inff();
                        Ds[i] = ok ? Dv[(i64)bh * Sq + q0 + i] : 0.0f;
                    }
                __syncthreads();
                tessera<NA, NB, 16, QT>(st, Kc, tr, Qc, tc);      /* due passate: meno operandi vivi */
                tessera<NA, NB, 16, QT>(dpt, Vc, tr, Oc, tc);
            }

            f16* PTh = (f16*)PT;
            f16* dSTh = (f16*)dST;
            #pragma unroll
            for (int bb = 0; bb < NB; ++bb) {
                const int ql = tc + QT * bb, q = q0 + ql;
                const unsigned int sr = seme_riga(s0, s1, bh, q);
                #pragma unroll
                for (int a = 0; a < NA; ++a) {
                    const int key = k0 + tr + 16 * a;
                    const bool valido = (q < Sq) && (key < Sk) && (!causale || key <= q);
                    const float p = valido ? __builtin_amdgcn_exp2f(st[a][bb] * scala_log2 - Ls[ql]) : 0.0f;
                    const bool tiene = soglia == 0u || tenuto(sr, key, soglia);
                    const float pd = tiene ? p * riscala : 0.0f;
                    const float dp = tiene ? dpt[a][bb] * riscala : 0.0f;
                    PTh[(tr + 16 * a) * (2 * PST) + ql] = (f16)pd;
                    dSTh[(tr + 16 * a) * (2 * PST) + ql] = (f16)(p * (dp - Ds[ql]));
                }
            }

            for (int qc = 0; qc < BQ / QC; ++qc) {
                __syncthreads();
                carica(Qa, Qp, qs_, q0 + qc * QC, QC, Sq, t, NT);
                carica(Oa, Op, os_, q0 + qc * QC, QC, Sq, t, NT);
                __syncthreads();
                #pragma unroll 1
                for (int qp4 = 0; qp4 < QC / 2; qp4 += 4) {
                    unsigned int q2[4][4], o2[4][4];     /* [coppia e][colonna x] */
                    #pragma unroll
                    for (int e = 0; e < 4; ++e) {
                        const int r = 2 * (qp4 + e);
                        const u2 qx = *(const u2*)(Qa + r * QSTR + 2 * ln), qy = *(const u2*)(Qa + (r + 1) * QSTR + 2 * ln);
                        const u2 ox = *(const u2*)(Oa + r * QSTR + 2 * ln), oy = *(const u2*)(Oa + (r + 1) * QSTR + 2 * ln);
                        q2[e][0] = basse(qx.x, qy.x); q2[e][1] = alte(qx.x, qy.x);
                        q2[e][2] = basse(qx.y, qy.y); q2[e][3] = alte(qx.y, qy.y);
                        o2[e][0] = basse(ox.x, oy.x); o2[e][1] = alte(ox.x, oy.x);
                        o2[e][2] = basse(ox.y, oy.y); o2[e][3] = alte(ox.y, oy.y);
                    }
                    #pragma unroll
                    for (int a = 0; a < AW; ++a) {
                        const int col = qc * (QC / 2) + qp4;
                        const u4 pa = *(const u4*)(PT + (AW * w + a) * PST + col);
                        const u4 sa = *(const u4*)(dST + (AW * w + a) * PST + col);
                        #pragma unroll
                        for (int e = 0; e < 4; ++e)
                            #pragma unroll
                            for (int x = 0; x < 4; ++x) {
                                dv[a][x] = DOT2(come_h2(el(pa, e)), come_h2(o2[e][x]), dv[a][x]);
                                dk[a][x] = DOT2(come_h2(el(sa, e)), come_h2(q2[e][x]), dk[a][x]);
                            }
                    }
                }
            }
        }
    }

    #pragma unroll
    for (int a = 0; a < AW; ++a) {
        const int key = k0 + AW * w + a;
        if (key < Sk) {
            const h2 k01 = {(f16)(dk[a][0] * scala), (f16)(dk[a][1] * scala)};
            const h2 k23 = {(f16)(dk[a][2] * scala), (f16)(dk[a][3] * scala)};
            const h2 v01 = {(f16)dv[a][0], (f16)dv[a][1]}, v23 = {(f16)dv[a][2], (f16)dv[a][3]};
            const u2 xk = {come_u(k01), come_u(k23)}, xv = {come_u(v01), come_u(v23)};
            *(u2*)(dK + ((i64)bk * Sk + key) * HEAD_DIM + 4 * ln) = xk;
            *(u2*)(dV + ((i64)bk * Sk + key) * HEAD_DIM + 4 * ln) = xv;
        }
    }
}
"""

SORGENTE_DQ_256 = COMUNE_256 + r"""
#define BQ 64                 /* query ferme */
#define BK 64                 /* chiavi che scorrono */
#define SST (BK / 2 + 4)
#define NW (NT / 64)              /* onde */
#define QS (NT / 16)              /* fase S: query tr + QS i (i < QI), chiavi tc + 16j (j < 4) */
#define QI (BQ / QS)
#define RW (BQ / NW)              /* accumulo: query per onda */
#define SPAZIO_S ((2 * BQ + 2 * BK) * CST)
#define SPAZIO_B (BK * QSTR)

extern "C" __global__ __launch_bounds__(NT)
void fa_dq(const f16* __restrict__ Q, const f16* __restrict__ K, const f16* __restrict__ V,
           const f16* __restrict__ dO, const float* __restrict__ LSE2, const float* __restrict__ Dv,
           f16* __restrict__ dQ,
           i64 qb_, i64 qh_, i64 qs_, i64 kb_, i64 kh_, i64 ks_, i64 vb_, i64 vh_, i64 vs_,
           i64 ob_, i64 oh_, i64 os_,
           int H, int G, int Sq, int Sk, float scala_log2, float scala, int causale,
           unsigned int s0, unsigned int s1, unsigned int soglia, float riscala)
{
    __shared__ unsigned int buf[SPAZIO_S > SPAZIO_B ? SPAZIO_S : SPAZIO_B];
    __shared__ unsigned int dSs[BQ * SST];
    __shared__ float Ls[BQ], Ds[BQ];
    unsigned int* Qc = buf;                 /* fase S: pezzi di CH2 dword */
    unsigned int* Oc = buf + BQ * CST;
    unsigned int* Kc = buf + 2 * BQ * CST;
    unsigned int* Vc = Kc + BK * CST;
    unsigned int* Ka = buf;                 /* fase di accumulo: le BK righe di K intere */

    const int t = threadIdx.x;
    const int tr = t >> 4, tc = t & 15;     /* fase S: query tr + QS i, chiavi tc + 16j */
    const int w = t >> 6, ln = t & 63;      /* accumulo: query RW w + i, colonne 4 ln + x (x<4) */
    const int bh = blockIdx.y, b = bh / H, h = bh - b * H;
    const int q0 = (causale ? gridDim.x - 1 - blockIdx.x : blockIdx.x) * BQ;   /* causale: prima i blocchi pesanti */
    const f16* Qp = Q + b * qb_ + h * qh_;
    const f16* Kp = K + b * kb_ + (h / G) * kh_;   /* GQA */
    const f16* Vp = V + b * vb_ + (h / G) * vh_;
    const f16* Op = dO + b * ob_ + h * oh_;

    for (int i = t; i < BQ; i += NT) {
        const bool ok = q0 + i < Sq;
        Ls[i] = ok ? LSE2[(i64)bh * Sq + q0 + i] : __builtin_inff();
        Ds[i] = ok ? Dv[(i64)bh * Sq + q0 + i] : 0.0f;
    }

    float dq[RW][4];
    #pragma unroll
    for (int i = 0; i < RW; ++i)
        #pragma unroll
        for (int x = 0; x < 4; ++x) dq[i][x] = 0.0f;
    unsigned int sr[QI];
    #pragma unroll
    for (int i = 0; i < QI; ++i) sr[i] = seme_riga(s0, s1, bh, q0 + tr + QS * i);

    int nk = (Sk + BK - 1) / BK;
    if (causale) {
        const int ultimo = (q0 + BQ - 1) / BK + 1;
        nk = nk < ultimo ? nk : ultimo;
    }

    for (int kb = 0; kb < nk; ++kb) {
        const int k0 = kb * BK;
        float s[QI][4], dp[QI][4];
        #pragma unroll
        for (int i = 0; i < QI; ++i)
            #pragma unroll
            for (int j = 0; j < 4; ++j) { s[i][j] = 0.0f; dp[i][j] = 0.0f; }

        for (int ch = 0; ch < D2; ch += CH2) {
            __syncthreads();
            pezzo(Qc, Qp, qs_, q0, BQ, Sq, ch, t);
            pezzo(Oc, Op, os_, q0, BQ, Sq, ch, t);
            pezzo(Kc, Kp, ks_, k0, BK, Sk, ch, t);
            pezzo(Vc, Vp, vs_, k0, BK, Sk, ch, t);
            __syncthreads();
            tessera<QI, 4, QS, 16>(s, Qc, tr, Kc, tc);        /* due passate: meno operandi vivi */
            tessera<QI, 4, QS, 16>(dp, Oc, tr, Vc, tc);
        }

        f16* dSh = (f16*)dSs;
        #pragma unroll
        for (int i = 0; i < QI; ++i) {
            const int ql = tr + QS * i, q = q0 + ql;
            #pragma unroll
            for (int j = 0; j < 4; ++j) {
                const int kl = tc + 16 * j, key = k0 + kl;
                const bool valido = (q < Sq) && (key < Sk) && (!causale || key <= q);
                const float p = valido ? __builtin_amdgcn_exp2f(s[i][j] * scala_log2 - Ls[ql]) : 0.0f;
                const bool tiene = soglia == 0u || tenuto(sr[i], key, soglia);
                const float d = tiene ? dp[i][j] * riscala : 0.0f;
                dSh[ql * (2 * SST) + kl] = (f16)(p * (d - Ds[ql]));
            }
        }
        __syncthreads();
        carica(Ka, Kp, ks_, k0, BK, Sk, t, NT);
        __syncthreads();

        #pragma unroll 1
        for (int kp4 = 0; kp4 < BK / 2; kp4 += 4) {
            unsigned int k2[4][4];               /* [coppia e][colonna x] */
            #pragma unroll
            for (int e = 0; e < 4; ++e) {
                const int r = 2 * (kp4 + e);
                const u2 kx = *(const u2*)(Ka + r * QSTR + 2 * ln), ky = *(const u2*)(Ka + (r + 1) * QSTR + 2 * ln);
                k2[e][0] = basse(kx.x, ky.x); k2[e][1] = alte(kx.x, ky.x);
                k2[e][2] = basse(kx.y, ky.y); k2[e][3] = alte(kx.y, ky.y);
            }
            #pragma unroll
            for (int i = 0; i < RW; ++i) {
                const u4 sa = *(const u4*)(dSs + (RW * w + i) * SST + kp4);
                #pragma unroll
                for (int e = 0; e < 4; ++e)
                    #pragma unroll
                    for (int x = 0; x < 4; ++x) dq[i][x] = DOT2(come_h2(el(sa, e)), come_h2(k2[e][x]), dq[i][x]);
            }
        }
    }

    #pragma unroll
    for (int i = 0; i < RW; ++i) {
        const int q = q0 + RW * w + i;
        if (q < Sq) {
            const h2 a01 = {(f16)(dq[i][0] * scala), (f16)(dq[i][1] * scala)};
            const h2 a23 = {(f16)(dq[i][2] * scala), (f16)(dq[i][3] * scala)};
            const u2 x = {come_u(a01), come_u(a23)};
            *(u2*)(dQ + ((i64)bh * Sq + q) * HEAD_DIM + 4 * ln) = x;
        }
    }
}
"""

KERNEL = {"fa_avanti": (SORGENTE_AVANTI, 256, 64), "fa_dkdv": (SORGENTE_DKDV, 256, 64),
          "fa_dq": (SORGENTE_DQ, 256, 64)}
SORGENTI_256 = {"fa_avanti": (SORGENTE_AVANTI_256, 64), "fa_dkdv": (SORGENTE_DKDV_256, 32),
                "fa_dq": (SORGENTE_DQ_256, 64)}
# thread per workgroup: 512 = due onde per SIMD (<= 128 VGPR), 1,26-1,38x su 256 (20 ott, prova_nt.py)
NT_256 = {"fa_avanti": 512, "fa_dkdv": 512, "fa_dq": 512}
KERNEL_256 = {}


def imposta_256(**nt):
    """Sceglie i thread per workgroup dei kernel D=256 (e svuota la cache dei compilati)."""
    NT_256.update(nt)
    for nome, (src, righe) in SORGENTI_256.items():
        KERNEL_256[nome] = (f"#define NT {NT_256[nome]}\n" + src, NT_256[nome], righe)
        _funzioni.pop((nome, 256), None)
DIMENSIONI = (64, 128, 256)


def kernel(nome, head_dim):
    """(sorgente, thread, righe per workgroup) del kernel 'nome' per questo head_dim."""
    return (KERNEL_256 if head_dim == 256 else KERNEL)[nome]


def _percorsi_hiprtc():
    lib = os.path.join(os.path.dirname(torch.__file__), "lib")
    return [os.path.join(lib, "hiprtc07013.dll"),
            r"C:\rocm_5_7_expansion_pack\bin\hiprtc07013.dll",
            r"C:\Program Files\AMD\ROCm\5.7\bin\hiprtc0507.dll"]


def _carica_dll(percorso):
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
_rtc = None

imposta_256()


def compila(sorgente, head_dim, extra=()):
    global _rtc
    if _rtc is None:
        for p in _percorsi_hiprtc():
            if os.path.exists(p):
                _rtc = _carica_dll(p)
                break
        else:
            raise RuntimeError("nessuna hipRTC trovata")
    prog = vp()
    assert _rtc.hiprtcCreateProgram(ctypes.byref(prog), sorgente.encode(), b"fa.hip", 0, None, None) == 0
    opz = [b"--offload-arch=gfx906", b"-mcode-object-version=5", b"-O3",
           f"-DHEAD_DIM={head_dim}".encode()] + [x.encode() for x in extra]
    if _rtc.hiprtcCompileProgram(prog, len(opz), (ctypes.c_char_p * len(opz))(*opz)) != 0:
        n = ctypes.c_size_t()
        _rtc.hiprtcGetProgramLogSize(prog, ctypes.byref(n))
        b = ctypes.create_string_buffer(n.value)
        _rtc.hiprtcGetProgramLog(prog, b)
        raise RuntimeError(b.value.decode(errors="replace"))
    n = ctypes.c_size_t()
    _rtc.hiprtcGetCodeSize(prog, ctypes.byref(n))
    codice = ctypes.create_string_buffer(n.value)
    _rtc.hiprtcGetCode(prog, codice)
    return codice


def _funzione(nome, head_dim):
    global _hip
    with _lock:
        if (nome, head_dim) not in _funzioni:
            if _hip is None:
                _hip = ctypes.CDLL("amdhip64.dll")
                _hip.hipModuleLaunchKernel.argtypes = [vp] + [ctypes.c_uint] * 7 + [vp, vp, vp]
            codice = compila(kernel(nome, head_dim)[0], head_dim)
            mod, f = vp(), vp()
            assert _hip.hipModuleLoadData(ctypes.byref(mod), codice) == 0
            assert _hip.hipModuleGetFunction(ctypes.byref(f), mod, nome.encode()) == 0
            _funzioni[(nome, head_dim)] = (f, codice, mod)
        return _funzioni[(nome, head_dim)][0]


def _lancia(nome, D, righe, BH, argomenti):
    f = _funzione(nome, D)
    _, nt, per_blocco = kernel(nome, D)
    args = (vp * len(argomenti))(*[ctypes.cast(ctypes.byref(x), vp) for x in argomenti])
    stream = torch.cuda.current_stream().cuda_stream
    rc = _hip.hipModuleLaunchKernel(f, (righe + per_blocco - 1) // per_blocco, BH, 1, nt, 1, 1, 0,
                                    vp(stream), args, None)
    if rc != 0:
        raise RuntimeError(f"{nome}: hipModuleLaunchKernel rc={rc}")


def _prepara(x):
    """Ultima dimensione contigua e righe allineate a 16 byte, altrimenti copia."""
    if x.stride(-1) != 1 or any(s % 8 for s in x.stride()[:-1]) or x.data_ptr() % 16:
        x = x.contiguous()
    return x


def _passi(x):
    return [ctypes.c_longlong(s) for s in x.stride()[:3]]


def _dropout(dropout, seme):
    if dropout <= 0.0:
        return [ctypes.c_uint(0), ctypes.c_uint(0), ctypes.c_uint(0), ctypes.c_float(1.0)]
    soglia = min(int(dropout * 2**32), 2**32 - 1)
    return [ctypes.c_uint(seme & 0xFFFFFFFF), ctypes.c_uint((seme >> 32) & 0xFFFFFFFF),
            ctypes.c_uint(soglia), ctypes.c_float(1.0 / (1.0 - dropout))]


def _controlla(q, k, v):
    assert q.dtype == torch.float16 and q.is_cuda and k.dtype == v.dtype == torch.float16
    assert q.dim() == 4 and k.shape == v.shape and q.shape[0] == k.shape[0] and q.shape[3] == k.shape[3]
    assert q.shape[1] % k.shape[1] == 0, "teste di query multiple di quelle di K/V (GQA)"
    assert q.shape[3] in DIMENSIONI, "head_dim 64, 128 o 256"


def avanti(q, k, v, causale=False, scala=None, dropout=0.0, seme=0):
    _controlla(q, k, v)
    q, k, v = _prepara(q), _prepara(k), _prepara(v)
    B, H, Sq, D = q.shape
    Sk = k.shape[2]
    sc = scala if scala is not None else D ** -0.5
    o = torch.empty(B, H, Sq, D, device=q.device, dtype=q.dtype)
    lse2 = torch.empty(B, H, Sq, device=q.device, dtype=torch.float32)
    p = lambda t: vp(t.data_ptr())
    _lancia("fa_avanti", D, Sq, B * H,
            [p(q), p(k), p(v), p(o), p(lse2)] + _passi(q) + _passi(k) + _passi(v)
            + [ctypes.c_int(H), ctypes.c_int(H // k.shape[1]), ctypes.c_int(Sq), ctypes.c_int(Sk),
               ctypes.c_float(sc * LOG2E), ctypes.c_int(1 if causale else 0)] + _dropout(dropout, seme))
    return o, lse2


def indietro(do, q, k, v, o, lse2, causale=False, scala=None, dropout=0.0, seme=0):
    _controlla(q, k, v)
    q, k, v, do = _prepara(q), _prepara(k), _prepara(v), _prepara(do)
    B, H, Sq, D = q.shape
    Sk = k.shape[2]
    sc = scala if scala is not None else D ** -0.5
    dvec = (do.float() * o.float()).sum(-1).contiguous()
    dq = torch.empty(B, H, Sq, D, device=q.device, dtype=q.dtype)
    Hk = k.shape[1]
    dk = torch.empty(B, Hk, Sk, D, device=q.device, dtype=q.dtype)
    dv = torch.empty_like(dk)
    p = lambda t: vp(t.data_ptr())
    coda = ([ctypes.c_int(H), ctypes.c_int(H // Hk), ctypes.c_int(Sq), ctypes.c_int(Sk), ctypes.c_float(sc * LOG2E),
             ctypes.c_float(sc), ctypes.c_int(1 if causale else 0)] + _dropout(dropout, seme))
    passi = _passi(q) + _passi(k) + _passi(v) + _passi(do)
    _lancia("fa_dkdv", D, Sk, B * Hk, [p(q), p(k), p(v), p(do), p(lse2), p(dvec), p(dk), p(dv)] + passi + coda)
    _lancia("fa_dq", D, Sq, B * H, [p(q), p(k), p(v), p(do), p(lse2), p(dvec), p(dq)] + passi + coda)
    return dq, dk, dv


class _Attenzione(torch.autograd.Function):
    @staticmethod
    def forward(ctx, q, k, v, causale, scala, dropout, seme):
        o, lse2 = avanti(q, k, v, causale, scala, dropout, seme)
        ctx.save_for_backward(q, k, v, o, lse2)
        ctx.opz = (causale, scala, dropout, seme)
        return o

    @staticmethod
    def backward(ctx, do):
        q, k, v, o, lse2 = ctx.saved_tensors
        dq, dk, dv = indietro(do, q, k, v, o, lse2, *ctx.opz)
        return dq, dk, dv, None, None, None, None


def attenzione(q, k, v, causale=False, scala=None, dropout=0.0, seme=None):
    """Con autograd. seme=None: ne estrae uno dal generatore di torch (riproducibile con manual_seed)."""
    if seme is None:
        seme = int(torch.randint(0, 2**62, (1,)).item()) if dropout > 0 else 0
    return _Attenzione.apply(q, k, v, causale, scala, dropout, seme)


def maschera_dropout(B, H, Sq, Sk, dropout, seme, device="cuda"):
    """La stessa maschera dei kernel, calcolata con torch (per i banchi). [B, H, Sq, Sk] bool: tenuto."""
    M = 0xFFFFFFFF

    def mescola(x):
        x = x ^ (x >> 16); x = (x * 0x7feb352d) & M
        x = x ^ (x >> 15); x = (x * 0x846ca68b) & M
        return x ^ (x >> 16)

    s0, s1 = seme & M, (seme >> 32) & M
    bh = torch.arange(B * H, device=device, dtype=torch.int64).view(B * H, 1, 1)
    q = torch.arange(Sq, device=device, dtype=torch.int64).view(1, Sq, 1)
    k = torch.arange(Sk, device=device, dtype=torch.int64).view(1, 1, Sk)
    sr = mescola(mescola(s0 ^ mescola((bh * 0x9E3779B9 + s1) & M)) ^ ((q * 0x85EBCA6B) & M))
    h = mescola(sr ^ ((k * 0xC2B2AE35 + 0x27D4EB2F) & M))
    soglia = min(int(dropout * 2**32), 2**32 - 1)
    return (h >= soglia).view(B, H, Sq, Sk)

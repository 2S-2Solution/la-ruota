"""Gated DeltaNet (chunked gated delta rule) per gfx906 — avanti e indietro, kernel HIP fusi.

2S, 20 ott 2026. Sostituisce `torch_chunk_gated_delta_rule` di transformers (Qwen3.5,
Qwen3-Next), che senza i kernel Triton di flash-linear-attention esegue ogni blocco di 64 token
come centinaia di operazioni torch (un ciclo di 63 righe per l'inversa triangolare) e nel passo
LoRA del 4B produce ~24 mila copy_ e migliaia di slice.

Matematica (per testa, blocco di C=64 righe, G = somma cumulata di g dentro il blocco):
    Γ_ij = exp(G_i - G_j) per i >= j, γ = exp(G), γC = exp(G_ultimo), γd = γC / γ
    A = strettamente_inferiore((β⊙K) K^T ⊙ Γ),  T = (I + A)^-1
    U = T (β⊙V),  W = T (βγ⊙K),  P = (Q K^T ⊙ Γ) inferiore con diagonale
    Vn = U - W S;  O = (γ⊙Q) S + P Vn;  S <- γC S + (γd⊙K)^T Vn
Tutto in fp32 come il riferimento: i FLOP sono pochi (S=256: ~1,4 GFLOP a strato), il costo vero
era il numero di lanci. Sette kernel, 256 thread, nessuna atomica (gfx906 non ne ha in fp32 globali;
quelle in LDS rendevano dg e dβ non deterministici, ora le somme hanno un ordine fisso):
  gdn_ingresso   (riga)               : l2norm in fp32, scala, [B,S,H,D] -> [B,H,Sp,D] fp32, padding
  gdn_prep       (blocco, testa)      : G, scale, A, T, P, U, W — i blocchi sono indipendenti
  gdn_ric        (fetta di Dv, testa) : la ricorrenza sugli stati, sequenziale sui blocchi; le colonne
                                        di Dv non si parlano, quindi 4 fette da 32; scrive o in
                                        [B, S, H, Dv] nel dtype d'ingresso
  gdn_converti   (riga)               : dO -> [B, H, Sp, Dv] fp32
  gdn_ric_ind    (fetta di Dv, testa) : la ricorrenza all'indietro di dS e dVn
  gdn_locale     (blocco, testa)      : dq, dk, dv, dβ, dg di ogni blocco, Dv intera
  gdn_uscita_ind (riga, testa di q/k) : indietro della l2norm, somma delle teste GQA, gradienti nel
                                        layout (passi qualunque) e dtype d'ingresso
In un secondo modulo (SORGENTE_CONV, compilato per K): conv_avanti / conv_indietro, la convoluzione
causale depthwise + SiLU dello strato sul layout [B, S, C], senza trasporre (gradienti di x, peso e
bias). GQA: q e k possono avere H/rap teste; la testa h legge la h/rap, come repeat_interleave.
Occupazione: 84 VGPR e <= 21 KB di LDS per kernel pesante -> 3 workgroup per CU, cosi' i 128
workgroup della forma del 4B (B1 S256 H32) girano in una tornata sola sui 60 CU. Stato e misure in
STATO.md.

Interfaccia:
    o, stato = chunk_gated_delta_rule(query, key, value, g, beta, chunk_size=64,
                                      initial_state=None, output_final_state=False,
                                      use_qk_l2norm_in_kernel=False)
stessa firma e stesse forme di transformers: query/key [B, S, H, Dk], value [B, S, H, Dv] a passo
qualunque (ultima dimensione contigua), g e beta [B, S, H]; fp16 o fp32 (anche misti); uscita
[B, S, H, Dv] nel dtype di query. Autograd completo, anche per initial_state e per lo stato finale.
Dk e Dv multipli di 64, al massimo 128 (Qwen3.5: 128 e 128). Non supportato: cu_seqlens.
    aggancia()   # monkeypatch nel solo processo: la funzione e il forward di Qwen3_5GatedDeltaNet
                 # (conv fusa, q/k/v viste dell'uscita della conv, niente trasposte né
                 # repeat_interleave); GDN_STRATO=0 nell'ambiente aggancia solo la funzione
    y = conv_causale(x, w, bias=None, silu=True)                 # x [B, S, C]
    o = gdn_impacchettato(qkv, g, beta, Hk, H, Dk, Dv)          # qkv [B, S, 2 Hk Dk + H Dv]
"""
import ctypes
import os
import threading

import torch

vp = ctypes.c_void_p
C = 64

SORGENTE = r"""
typedef long long i64;
typedef _Float16 f16;
#define C 64
#define DVB 32
#define NT 256
#define KT 32
#ifndef KUNR
#define KUNR 8
#endif
#define STR_(x) #x
#define STR(x) STR_(x)
#ifndef ONDE_RIC
#define ONDE_RIC 3
#endif
#ifndef ONDE_PREP
#define ONDE_PREP 3
#endif
#ifndef ONDE_LOC
#define ONDE_LOC 3
#endif
#ifndef KP
#define KP 16              /* tessere di k in gdn_prep */
#endif
#ifndef KL
#define KL 8               /* tessere di k in gdn_locale */
#endif

/* operando: matrice salvata per righe X[r][c] = p[r*ld + c]; tr=0 la usa com'e', tr=1 trasposta;
   sc (se non nullo) scala la riga r di sc[4*r], come le colonne del buffer SC; mult moltiplica tutto */
struct Opd { const float* p; int ld; int tr; const float* sc; float mult; };

__device__ inline Opd op(const float* p, int ld, int tr = 0, const float* sc = 0, float mult = 1.0f) {
    Opd o; o.p = p; o.ld = ld; o.tr = tr; o.sc = sc; o.mult = mult; return o;
}

/* tessera A(i, k0..k0+KK) -> la[k*(M+1) + i] */
template <int M, int KK> __device__ inline void carica_a(float* la, const Opd A, int k0, int t) {
    if (!A.tr) {
        for (int idx = t; idx < M * KK; idx += NT) {
            const int i = idx / KK, k = idx - i * KK;
            const float s = A.sc ? A.mult * A.sc[4 * i] : A.mult;
            la[k * (M + 1) + i] = A.p[(i64)i * A.ld + k0 + k] * s;
        }
    } else {
        for (int idx = t; idx < M * KK; idx += NT) {
            const int k = idx / M, i = idx - k * M;
            const float s = A.sc ? A.mult * A.sc[4 * (k0 + k)] : A.mult;
            la[k * (M + 1) + i] = A.p[(i64)(k0 + k) * A.ld + i] * s;
        }
    }
}

/* tessera B(k0..k0+KK, j) -> lb[k*(N+1) + j] */
template <int N, int KK> __device__ inline void carica_b(float* lb, const Opd B, int k0, int t) {
    if (!B.tr) {
        for (int idx = t; idx < N * KK; idx += NT) {
            const int k = idx / N, j = idx - k * N;
            const float s = B.sc ? B.mult * B.sc[4 * (k0 + k)] : B.mult;
            lb[k * (N + 1) + j] = B.p[(i64)(k0 + k) * B.ld + j] * s;
        }
    } else {
        for (int idx = t; idx < N * KK; idx += NT) {
            const int j = idx / KK, k = idx - j * KK;
            const float s = B.sc ? B.mult * B.sc[4 * j] : B.mult;
            lb[k * (N + 1) + j] = B.p[(i64)j * B.ld + k0 + k] * s;
        }
    }
}

/* acc[M x N] += A[M x K] B[K x N] a tessere di KK; il thread t ha le righe tr+16r e le colonne tc+16c */
template <int M, int N, int KK = KT>
__device__ inline void mm(float (&acc)[M / 16][N / 16], const Opd A, const Opd B, int K,
                          float* la, float* lb, int t) {
    const int tr = t >> 4, tc = t & 15;
    for (int k0 = 0; k0 < K; k0 += KK) {
        __syncthreads();
        carica_a<M, KK>(la, A, k0, t);
        carica_b<N, KK>(lb, B, k0, t);
        __syncthreads();
        _Pragma(STR(unroll KUNR))
        for (int k = 0; k < KK; ++k) {
            float a[M / 16], b[N / 16];
            #pragma unroll
            for (int r = 0; r < M / 16; ++r) a[r] = la[k * (M + 1) + tr + 16 * r];
            #pragma unroll
            for (int c = 0; c < N / 16; ++c) b[c] = lb[k * (N + 1) + tc + 16 * c];
            #pragma unroll
            for (int r = 0; r < M / 16; ++r)
                #pragma unroll
                for (int c = 0; c < N / 16; ++c) acc[r][c] = fmaf(a[r], b[c], acc[r][c]);
        }
    }
    __syncthreads();
}

template <int M, int N> __device__ inline void azzera(float (&acc)[M / 16][N / 16]) {
    #pragma unroll
    for (int r = 0; r < M / 16; ++r)
        #pragma unroll
        for (int c = 0; c < N / 16; ++c) acc[r][c] = 0.0f;
}

template <int M, int N> __device__ inline void salva(float* p, int ld, const float (&acc)[M / 16][N / 16], int t) {
    const int tr = t >> 4, tc = t & 15;
    #pragma unroll
    for (int r = 0; r < M / 16; ++r)
        #pragma unroll
        for (int c = 0; c < N / 16; ++c) p[(i64)(tr + 16 * r) * ld + tc + 16 * c] = acc[r][c];
}

/* somma fra le 16 corsie che condividono tr */
__device__ inline float somma16(float x) {
    x += __shfl_xor(x, 1, 16); x += __shfl_xor(x, 2, 16);
    x += __shfl_xor(x, 4, 16); x += __shfl_xor(x, 8, 16);
    return x;
}

/* ---------------------------------------------------------------- avanti: preparazione */
#define AST (C + 4)              /* passo di A nella LDS: multiplo di 4 per le letture b128 */
#define LDS_PREP (KP * (C + 1) + KP * (DMAX + 1) > C * AST ? KP * (C + 1) + KP * (DMAX + 1) : C * AST)

extern "C" __global__ __launch_bounds__(NT) __attribute__((amdgpu_waves_per_eu(ONDE_PREP, ONDE_PREP)))
void gdn_prep(const float* __restrict__ Q, const float* __restrict__ K, const float* __restrict__ V,
              const float* __restrict__ Gin, const float* __restrict__ Bt,
              float* __restrict__ Gc, float* __restrict__ SC, float* __restrict__ Tm,
              float* __restrict__ Am, float* __restrict__ Pm, float* __restrict__ Wm,
              float* __restrict__ Um, int NC)
{
    /* le tessere e A (per la sostituzione) condividono la LDS: A si scrive dopo l'ultimo mm che le usa */
    __shared__ __attribute__((aligned(16))) float buf[LDS_PREP];
    __shared__ float Gs[C];
    float* la = buf;
    float* lb = buf + KP * (C + 1);
    float* As = buf;
    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;
    const int n = blockIdx.x, bh = blockIdx.y;
    const i64 cc = (i64)bh * NC + n, r0 = cc * C;
    const float* Qc = Q + r0 * DK;
    const float* Kc = K + r0 * DK;
    const float* Vc = V + r0 * DV;
    float* scc = SC + r0 * 4;
    float* Tc = Tm + cc * C * C;

    if (t < C) {
        float s = 0.0f;
        for (int m = 0; m <= t; ++m) s += Gin[r0 + m];
        Gs[t] = s; Gc[r0 + t] = s;
    }
    __syncthreads();
    if (t < C) {
        const float G = Gs[t], b = Bt[r0 + t], gm = expf(G);
        scc[4 * t + 0] = gm; scc[4 * t + 1] = expf(Gs[C - 1] - G);
        scc[4 * t + 2] = b; scc[4 * t + 3] = b * gm;
    }
    __syncthreads();

    float a[4][4];
    azzera<64, 64>(a);
    mm<64, 64, KP>(a, op(Qc, DK), op(Kc, DK, 1), DK, la, lb, t);
    #pragma unroll
    for (int r = 0; r < 4; ++r)
        #pragma unroll
        for (int c = 0; c < 4; ++c) {
            const int i = tr + 16 * r, j = tc + 16 * c;
            Pm[cc * C * C + i * C + j] = i >= j ? a[r][c] * expf(Gs[i] - Gs[j]) : 0.0f;
        }
    azzera<64, 64>(a);
    mm<64, 64, KP>(a, op(Kc, DK, 0, scc + 2), op(Kc, DK, 1), DK, la, lb, t);
    #pragma unroll
    for (int r = 0; r < 4; ++r)
        #pragma unroll
        for (int c = 0; c < 4; ++c) {
            const int i = tr + 16 * r, j = tc + 16 * c;
            const float x = i > j ? a[r][c] * expf(Gs[i] - Gs[j]) : 0.0f;
            As[i * AST + j] = x; Am[cc * C * C + i * C + j] = x;
        }
    __syncthreads();

    /* T = (I + A)^-1 per sostituzione in avanti: la corsia j della prima onda tiene la colonna j
       a registri (cicli srotolati, A letta in broadcast dalla LDS); quattro somme parziali
       accorciano la catena di dipendenze */
    if (t < C) {
        const int j = t;
        float x[C];
        #pragma unroll
        for (int i = 0; i < C; ++i) {
            float s0 = 0.0f, s1 = 0.0f, s2 = 0.0f, s3 = 0.0f;
            #pragma unroll
            for (int m = 0; m + 3 < i; m += 4) {
                s0 = fmaf(As[i * AST + m], x[m], s0);
                s1 = fmaf(As[i * AST + m + 1], x[m + 1], s1);
                s2 = fmaf(As[i * AST + m + 2], x[m + 2], s2);
                s3 = fmaf(As[i * AST + m + 3], x[m + 3], s3);
            }
            #pragma unroll
            for (int m = i & ~3; m < i; ++m) s0 = fmaf(As[i * AST + m], x[m], s0);
            x[i] = i < j ? 0.0f : (i == j ? 1.0f : -((s0 + s1) + (s2 + s3)));
        }
        #pragma unroll
        for (int i = 0; i < C; ++i) Tc[i * C + j] = x[i];
    }
    __syncthreads();

    float u[4][DV / 16];
    azzera<64, DV>(u);
    mm<64, DV, KP>(u, op(Tc, C), op(Vc, DV, 0, scc + 2), C, la, lb, t);
    salva<64, DV>(Um + r0 * DV, DV, u, t);
    float w[4][DK / 16];
    azzera<64, DK>(w);
    mm<64, DK, KP>(w, op(Tc, C), op(Kc, DK, 0, scc + 3), C, la, lb, t);
    salva<64, DK>(Wm + r0 * DK, DK, w, t);
}

/* ---------------------------------------------------------------- avanti: ricorrenza */
extern "C" __global__ __launch_bounds__(NT) __attribute__((amdgpu_waves_per_eu(ONDE_RIC, ONDE_RIC)))
void gdn_ric(const float* __restrict__ Q, const float* __restrict__ K, const float* __restrict__ SC,
             const float* __restrict__ Pm, const float* __restrict__ Wm, const float* __restrict__ Um,
             const float* __restrict__ S0, float* __restrict__ Sst, float* __restrict__ Vn,
             void* __restrict__ O, float* __restrict__ Sfin, int NC,
             i64 ob, i64 os, i64 oh, int H, int S, int o16)
{
    __shared__ float la[KT * (DK + 1)], lb[KT * (DVB + 1)];
    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;
    const int vb = blockIdx.x * DVB, bh = blockIdx.y;

    float s[DK / 16][2];
    #pragma unroll
    for (int r = 0; r < DK / 16; ++r)
        #pragma unroll
        for (int c = 0; c < 2; ++c)
            s[r][c] = S0 ? S0[(i64)bh * DK * DV + (tr + 16 * r) * DV + vb + tc + 16 * c] : 0.0f;

    for (int n = 0; n < NC; ++n) {
        const i64 cc = (i64)bh * NC + n, r0 = cc * C;
        const float* scc = SC + r0 * 4;
        float* Sn = Sst + cc * DK * DV + vb;
        float* Vnc = Vn + r0 * DV + vb;
        salva<DK, 32>(Sn, DV, s, t);

        float x[4][2];
        azzera<64, 32>(x);
        mm<64, 32>(x, op(Wm + r0 * DK, DK), op(Sn, DV), DK, la, lb, t);
        #pragma unroll
        for (int r = 0; r < 4; ++r)
            #pragma unroll
            for (int c = 0; c < 2; ++c)
                x[r][c] = Um[(r0 + tr + 16 * r) * DV + vb + tc + 16 * c] - x[r][c];
        salva<64, 32>(Vnc, DV, x, t);

        azzera<64, 32>(x);
        mm<64, 32>(x, op(Q + r0 * DK, DK, 0, scc + 0), op(Sn, DV), DK, la, lb, t);
        mm<64, 32>(x, op(Pm + cc * C * C, C), op(Vnc, DV), C, la, lb, t);
        /* O col passo (ob, os, oh) e il dtype dell'uscita, solo le righe < S */
        {
            const int b = bh / H, h = bh - b * H;
            #pragma unroll
            for (int r = 0; r < 4; ++r) {
                const int s = n * C + tr + 16 * r;
                if (s < S) {
                    const i64 base = (i64)b * ob + (i64)s * os + (i64)h * oh + vb + tc;
                    #pragma unroll
                    for (int c = 0; c < 2; ++c) {
                        if (o16) ((f16*)O)[base + 16 * c] = (f16)x[r][c];
                        else ((float*)O)[base + 16 * c] = x[r][c];
                    }
                }
            }
        }

        const float gC = scc[4 * (C - 1)];
        #pragma unroll
        for (int r = 0; r < DK / 16; ++r)
            #pragma unroll
            for (int c = 0; c < 2; ++c) s[r][c] *= gC;
        mm<DK, 32>(s, op(K + r0 * DK, DK, 1, scc + 1), op(Vnc, DV), C, la, lb, t);
    }
    if (Sfin) salva<DK, 32>(Sfin + (i64)bh * DK * DV + vb, DV, s, t);
}

/* ---------------------------------------------------------------- indietro: ricorrenza */
extern "C" __global__ __launch_bounds__(NT) __attribute__((amdgpu_waves_per_eu(ONDE_RIC, ONDE_RIC)))
void gdn_ric_ind(const float* __restrict__ Q, const float* __restrict__ K, const float* __restrict__ SC,
                 const float* __restrict__ Pm, const float* __restrict__ Wm, const float* __restrict__ dO,
                 const float* __restrict__ dSfin, float* __restrict__ dSst, float* __restrict__ dVn,
                 float* __restrict__ dS0, int NC)
{
    __shared__ float la[KT * (DK + 1)], lb[KT * (DVB + 1)];
    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;
    const int vb = blockIdx.x * DVB, bh = blockIdx.y;

    float ds[DK / 16][2];
    #pragma unroll
    for (int r = 0; r < DK / 16; ++r)
        #pragma unroll
        for (int c = 0; c < 2; ++c)
            ds[r][c] = dSfin ? dSfin[(i64)bh * DK * DV + (tr + 16 * r) * DV + vb + tc + 16 * c] : 0.0f;

    for (int n = NC - 1; n >= 0; --n) {
        const i64 cc = (i64)bh * NC + n, r0 = cc * C;
        const float* scc = SC + r0 * 4;
        float* Dn = dSst + cc * DK * DV + vb;
        const float* dOc = dO + r0 * DV + vb;
        float* dVc = dVn + r0 * DV + vb;
        salva<DK, 32>(Dn, DV, ds, t);

        float x[4][2];
        azzera<64, 32>(x);
        mm<64, 32>(x, op(Pm + cc * C * C, C, 1), op(dOc, DV), C, la, lb, t);
        mm<64, 32>(x, op(K + r0 * DK, DK, 0, scc + 1), op(Dn, DV), DK, la, lb, t);
        salva<64, 32>(dVc, DV, x, t);

        const float gC = scc[4 * (C - 1)];
        #pragma unroll
        for (int r = 0; r < DK / 16; ++r)
            #pragma unroll
            for (int c = 0; c < 2; ++c) ds[r][c] *= gC;
        mm<DK, 32>(ds, op(Q + r0 * DK, DK, 1, scc + 0), op(dOc, DV), C, la, lb, t);
        mm<DK, 32>(ds, op(Wm + r0 * DK, DK, 1, 0, -1.0f), op(dVc, DV), C, la, lb, t);
    }
    if (dS0) salva<DK, 32>(dS0 + (i64)bh * DK * DV + vb, DV, ds, t);
}

/* ---------------------------------------------------------------- indietro: gradienti del blocco */
#define SCRATCH (4 * C * C + C * DK)

/* Y (64x64 a registri) mascherata: XS = Y⊙Γ; con m = Y⊙MAT, + somme di riga -> cr[S_RIGA][i]
   e - somme di colonna -> cp[F_COL][onda][j] (le 4 righe di thread di un'onda ridotte con shfl) */
template <bool STRETTA>
__device__ inline void righe_colonne(const float (&y)[4][4], const float* mat, float* xs, const float* Gs,
                                     float* cr_riga, float (*cp_col)[C], int t) {
    const int tr = t >> 4, tc = t & 15;
    float col[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    #pragma unroll
    for (int r = 0; r < 4; ++r) {
        const int i = tr + 16 * r;
        float riga = 0.0f;
        #pragma unroll
        for (int c = 0; c < 4; ++c) {
            const int j = tc + 16 * c;
            float d = 0.0f;
            if (STRETTA ? i > j : i >= j) {
                const float m = y[r][c] * mat[i * C + j];
                d = y[r][c] * expf(Gs[i] - Gs[j]);
                riga += m; col[c] += m;
            }
            xs[i * C + j] = d;
        }
        riga = somma16(riga);
        if (tc == 0) cr_riga[i] = riga;
    }
    #pragma unroll
    for (int c = 0; c < 4; ++c) {
        float x = col[c];
        x += __shfl_xor(x, 16, 64); x += __shfl_xor(x, 32, 64);
        if ((t & 63) < 16) cp_col[t >> 6][tc + 16 * c] = -x;
    }
}

extern "C" __global__ __launch_bounds__(NT) __attribute__((amdgpu_waves_per_eu(ONDE_LOC, ONDE_LOC)))
void gdn_locale(const float* __restrict__ Q, const float* __restrict__ K, const float* __restrict__ V,
                const float* __restrict__ Gc, const float* __restrict__ SC, const float* __restrict__ Tm,
                const float* __restrict__ Am, const float* __restrict__ Pm, const float* __restrict__ Sst,
                const float* __restrict__ dSst, const float* __restrict__ Vn, const float* __restrict__ dVn,
                const float* __restrict__ dO, float* __restrict__ scratch,
                float* __restrict__ dQ, float* __restrict__ dK, float* __restrict__ dV,
                float* __restrict__ dB, float* __restrict__ dG, int NC)
{
    __shared__ float la[KL * (C + 1)], lb[KL * (DMAX + 1)];
    /* contributi a dG e dβ senza atomiche (ordine di somma fisso, risultato deterministico):
       cr[s][i] uno scrittore per riga e per fase; cp[f][onda][j] le somme per colonna; red le onde */
    __shared__ float Gs[C], dGs[C];
    __shared__ float cr[8][C], cp[2][NT / 64][C], red[NT / 64];
    const int t = threadIdx.x, tr = t >> 4, tc = t & 15;
    const int n = blockIdx.x, bh = blockIdx.y;
    const i64 cc = (i64)bh * NC + n, r0 = cc * C;
    const float* scc = SC + r0 * 4;
    const float* Qc = Q + r0 * DK;
    const float* Kc = K + r0 * DK;
    const float* Vc = V + r0 * DV;
    const float* Tc = Tm + cc * C * C;
    const float* Sn = Sst + cc * DK * DV;
    const float* Dn = dSst + cc * DK * DV;
    const float* Vnc = Vn + r0 * DV;
    const float* dVc = dVn + r0 * DV;
    const float* dOc = dO + r0 * DV;
    float* dKc = dK + r0 * DK;              /* dk si accumula qui: ogni thread rilegge solo i suoi */
    float* X1 = scratch + cc * SCRATCH;     /* dP⊙Γ          C x C  */
    float* X3 = X1 + C * C;                 /* dT            C x C  */
    float* X4 = X3 + C * C;                 /* dT T^T        C x C  */
    float* X5 = X4 + C * C;                 /* dA⊙Γ          C x C  */
    float* X2 = X5 + C * C;                 /* dW            C x DK */
    if (t < C) Gs[t] = Gc[r0 + t];
    __syncthreads();

    float x[4][DMAX / 16];
    float y[4][4];

    /* (4) dP = dO Vn^T (inferiore con diagonale): X1 = dP⊙Γ; M = dP⊙P -> dG */
    azzera<64, 64>(y);
    mm<64, 64, KL>(y, op(dOc, DV), op(Vnc, DV, 1), DV, la, lb, t);
    righe_colonne<false>(y, Pm + cc * C * C, X1, Gs, cr[2], cp[0], t);

    /* (1) dq = γ⊙(dO S^T) + X1 K;  dG_i += γ_i <dO S^T, Q>_i */
    azzera<64, DK>(x);
    mm<64, DK, KL>(x, op(dOc, DV), op(Sn, DV, 1), DV, la, lb, t);
    #pragma unroll
    for (int r = 0; r < 4; ++r) {
        const int i = tr + 16 * r;
        const float gm = scc[4 * i];
        float p = 0.0f;
        #pragma unroll
        for (int c = 0; c < DK / 16; ++c) {
            p = fmaf(x[r][c], Qc[i * DK + tc + 16 * c], p);
            x[r][c] *= gm;
        }
        p = somma16(p);
        if (tc == 0) cr[0][i] = gm * p;
    }
    mm<64, DK, KL>(x, op(X1, C), op(Kc, DK), C, la, lb, t);
    salva<64, DK>(dQ + r0 * DK, DK, x, t);

    /* (2) dk = γd⊙(Vn dS'^T) + X1^T Q;  E_i = γd_i <Vn dS'^T, K>_i: dG_i -= E_i, dG_ultimo += E_i */
    azzera<64, DK>(x);
    mm<64, DK, KL>(x, op(Vnc, DV), op(Dn, DV, 1), DV, la, lb, t);
    #pragma unroll
    for (int r = 0; r < 4; ++r) {
        const int i = tr + 16 * r;
        const float gd = scc[4 * i + 1];
        float p = 0.0f;
        #pragma unroll
        for (int c = 0; c < DK / 16; ++c) {
            p = fmaf(x[r][c], Kc[i * DK + tc + 16 * c], p);
            x[r][c] *= gd;
        }
        p = somma16(p) * gd;
        if (tc == 0) cr[1][i] = -p;
    }
    mm<64, DK, KL>(x, op(X1, C, 1), op(Qc, DK), C, la, lb, t);
    salva<64, DK>(dKc, DK, x, t);

    /* (3) dG_ultimo += γC <dS', S> */
    {
        float p = 0.0f;
        for (int idx = t; idx < DK * DV; idx += NT) p = fmaf(Dn[idx], Sn[idx], p);
        p = somma16(p);
        p += __shfl_xor(p, 16, 64); p += __shfl_xor(p, 32, 64);
        if ((t & 63) == 0) red[t >> 6] = scc[4 * (C - 1)] * p;
    }

    /* (5) dW = -dVn S^T -> X2 */
    azzera<64, DK>(x);
    mm<64, DK, KL>(x, op(dVc, DV, 0, 0, -1.0f), op(Sn, DV, 1), DV, la, lb, t);
    salva<64, DK>(X2, DK, x, t);

    /* (6) dT = dVn (β⊙V)^T + dW (βγ⊙K)^T -> X3 */
    azzera<64, 64>(y);
    mm<64, 64, KL>(y, op(dVc, DV), op(Vc, DV, 1, scc + 2), DV, la, lb, t);
    mm<64, 64, KL>(y, op(X2, DK), op(Kc, DK, 1, scc + 3), DK, la, lb, t);
    salva<64, 64>(X3, C, y, t);

    /* (7) dVb = T^T dVn: dv = β dVb, dβ_i += <dVb_i, V_i> */
    azzera<64, DV>(x);
    mm<64, DV, KL>(x, op(Tc, C, 1), op(dVc, DV), C, la, lb, t);
    #pragma unroll
    for (int r = 0; r < 4; ++r) {
        const int i = tr + 16 * r;
        const float be = scc[4 * i + 2];
        float p = 0.0f;
        #pragma unroll
        for (int c = 0; c < DV / 16; ++c) {
            p = fmaf(x[r][c], Vc[i * DV + tc + 16 * c], p);
            dV[(r0 + i) * DV + tc + 16 * c] = be * x[r][c];
        }
        p = somma16(p);
        if (tc == 0) cr[5][i] = p;
    }

    /* (8) dKbg = T^T dW: dk += βγ dKbg; c_i = <dKbg_i, K_i>: dβ_i += γ_i c_i, dG_i += β_i γ_i c_i */
    azzera<64, DK>(x);
    mm<64, DK, KL>(x, op(Tc, C, 1), op(X2, DK), C, la, lb, t);
    #pragma unroll
    for (int r = 0; r < 4; ++r) {
        const int i = tr + 16 * r;
        const float gm = scc[4 * i], bg = scc[4 * i + 3];
        float p = 0.0f;
        #pragma unroll
        for (int c = 0; c < DK / 16; ++c) {
            float* d = dKc + i * DK + tc + 16 * c;
            p = fmaf(x[r][c], Kc[i * DK + tc + 16 * c], p);
            *d = fmaf(bg, x[r][c], *d);
        }
        p = somma16(p);
        if (tc == 0) { cr[6][i] = gm * p; cr[3][i] = bg * p; }
    }

    /* (9) dA = -T^T dT T^T (strettamente inferiore): X5 = dA⊙Γ; N = dA⊙A -> dG */
    azzera<64, 64>(y);
    mm<64, 64, KL>(y, op(X3, C), op(Tc, C, 1), C, la, lb, t);
    salva<64, 64>(X4, C, y, t);
    azzera<64, 64>(y);
    mm<64, 64, KL>(y, op(Tc, C, 1, 0, -1.0f), op(X4, C), C, la, lb, t);
    righe_colonne<true>(y, Am + cc * C * C, X5, Gs, cr[4], cp[1], t);

    /* (10) A = (β⊙K) K^T: dKb = X5 K -> dk += β dKb, dβ_i += <dKb_i, K_i>;  dk += X5^T (β⊙K) */
    azzera<64, DK>(x);
    mm<64, DK, KL>(x, op(X5, C), op(Kc, DK), C, la, lb, t);
    #pragma unroll
    for (int r = 0; r < 4; ++r) {
        const int i = tr + 16 * r;
        const float be = scc[4 * i + 2];
        float p = 0.0f;
        #pragma unroll
        for (int c = 0; c < DK / 16; ++c) {
            p = fmaf(x[r][c], Kc[i * DK + tc + 16 * c], p);
            x[r][c] = fmaf(be, x[r][c], dKc[i * DK + tc + 16 * c]);
        }
        p = somma16(p);
        if (tc == 0) cr[7][i] = p;
    }
    mm<64, DK, KL>(x, op(X5, C, 1), op(Kc, DK, 0, scc + 2), C, la, lb, t);
    salva<64, DK>(dKc, DK, x, t);

    __syncthreads();
    if (t < C) {
        float s = cr[0][t] + cr[1][t] + cr[2][t] + cr[3][t] + cr[4][t];
        for (int w = 0; w < NT / 64; ++w) s += cp[0][w][t] + cp[1][w][t];
        if (t == C - 1) {                       /* G_ultimo: dalla γC dello stato e da γd */
            for (int m = 0; m < C; ++m) s -= cr[1][m];
            for (int w = 0; w < NT / 64; ++w) s += red[w];
        }
        dGs[t] = s;
        dB[r0 + t] = cr[5][t] + cr[6][t] + cr[7][t];
    }
    __syncthreads();
    /* G e' la somma cumulata di g: dg_m = somma su i >= m di dG_i */
    if (t < C) {
        float s = 0.0f;
        for (int i = C - 1; i >= t; --i) s += dGs[i];
        dG[r0 + t] = s;
    }
}
/* ---------------------------------------------------------------- contorno: ingresso e uscita */
__device__ inline float leggi(const void* p, i64 i, int mezzo) {
    return mezzo ? (float)((const f16*)p)[i] : ((const float*)p)[i];
}
__device__ inline void scrivi(void* p, i64 i, float x, int mezzo) {
    if (mezzo) ((f16*)p)[i] = (f16)x; else ((float*)p)[i] = x;
}
__device__ inline float somma64(float x) {
    #pragma unroll
    for (int m = 32; m >= 1; m >>= 1) x += __shfl_xor(x, m, 64);
    return x;
}

/* un'onda per riga (bh, s): query/key [B, S, H/rap, D] (la testa h legge la h/rap, come
   repeat_interleave), value [B, S, H, D], a passo qualunque (d contiguo), g e beta
   [B, S, H]; fp16 o fp32 secondo i bit di 'tipi' (1 q, 2 k, 4 v, 8 g, 16 beta). Uscite fp32
   [BH, Sp, D] con zeri oltre S; norm: q e k divise per la norma L2 (eps 1e-6 come in FLA),
   q moltiplicata per 'scala'. RQ, RK: gli inversi delle norme, per l'indietro. */
extern "C" __global__ __launch_bounds__(NT)
void gdn_ingresso(const void* __restrict__ q, const void* __restrict__ k, const void* __restrict__ v,
                  const void* __restrict__ g, const void* __restrict__ be,
                  i64 qb, i64 qs, i64 qh, i64 kb, i64 ks, i64 kh, i64 vb, i64 vs, i64 vh,
                  i64 gb, i64 gs, i64 gh, i64 bb, i64 bs, i64 bhh,
                  int tipi, int BH, int H, int rap, int S, int Sp, int norm, float scala,
                  float* __restrict__ Qi, float* __restrict__ Ki, float* __restrict__ Vi,
                  float* __restrict__ Gi, float* __restrict__ Bi, float* __restrict__ RQ, float* __restrict__ RK)
{
    const int lane = threadIdx.x & 63;
    const i64 riga = (i64)blockIdx.x * (NT / 64) + (threadIdx.x >> 6);
    if (riga >= (i64)BH * Sp) return;
    const int bh = (int)(riga / Sp), s = (int)(riga - (i64)bh * Sp), b = bh / H, h = bh - b * H;
    const bool dentro = s < S;
    float xq[DK / 64], xk[DK / 64], xv[DV / 64];
    float sq = 0.0f, sk = 0.0f;
    #pragma unroll
    for (int u = 0; u < DK / 64; ++u) {
        const int d = lane + 64 * u;
        xq[u] = dentro ? leggi(q, b * qb + s * qs + (h / rap) * qh + d, tipi & 1) : 0.0f;
        xk[u] = dentro ? leggi(k, b * kb + s * ks + (h / rap) * kh + d, tipi & 2) : 0.0f;
        sq = fmaf(xq[u], xq[u], sq); sk = fmaf(xk[u], xk[u], sk);
    }
    #pragma unroll
    for (int u = 0; u < DV / 64; ++u)
        xv[u] = dentro ? leggi(v, b * vb + s * vs + h * vh + lane + 64 * u, tipi & 4) : 0.0f;
    float rq = 1.0f, rk = 1.0f;
    if (norm) {
        sq = somma64(sq); sk = somma64(sk);
        rq = 1.0f / sqrtf(sq + 1e-6f); rk = 1.0f / sqrtf(sk + 1e-6f);
    }
    #pragma unroll
    for (int u = 0; u < DK / 64; ++u) {
        Qi[riga * DK + lane + 64 * u] = xq[u] * rq * scala;
        Ki[riga * DK + lane + 64 * u] = xk[u] * rk;
    }
    #pragma unroll
    for (int u = 0; u < DV / 64; ++u) Vi[riga * DV + lane + 64 * u] = xv[u];
    if (lane == 0) {
        Gi[riga] = dentro ? leggi(g, b * gb + s * gs + h * gh, tipi & 8) : 0.0f;
        Bi[riga] = dentro ? leggi(be, b * bb + s * bs + h * bhh, tipi & 16) : 0.0f;
        RQ[riga] = rq; RK[riga] = rk;
    }
}

/* [B, S, H, DV] a passo qualunque, fp16 o fp32 -> [BH, Sp, DV] fp32 con zeri oltre S (per dO) */
extern "C" __global__ __launch_bounds__(NT)
void gdn_converti(const void* __restrict__ x, i64 xb, i64 xs, i64 xh, int mezzo,
                  int BH, int H, int S, int Sp, float* __restrict__ y)
{
    const int lane = threadIdx.x & 63;
    const i64 riga = (i64)blockIdx.x * (NT / 64) + (threadIdx.x >> 6);
    if (riga >= (i64)BH * Sp) return;
    const int bh = (int)(riga / Sp), s = (int)(riga - (i64)bh * Sp), b = bh / H, h = bh - b * H;
    #pragma unroll
    for (int u = 0; u < DV / 64; ++u)
        y[riga * DV + lane + 64 * u] = s < S ? leggi(x, b * xb + s * xs + h * xh + lane + 64 * u, mezzo) : 0.0f;
}

/* gradienti interni [BH, Sp, D] fp32 -> gradienti degli ingressi, ognuno col suo passo (b, s, h) e
   il suo dtype; un'onda per riga (b, s, testa di q/k): somma le rap teste di valore che la leggono.
   Con norm, l'indietro della L2: dx = r (dy - y <y, dy>) con y = x r */
extern "C" __global__ __launch_bounds__(NT)
void gdn_uscita_ind(const float* __restrict__ dQi, const float* __restrict__ dKi, const float* __restrict__ dVi,
                    const float* __restrict__ dGi, const float* __restrict__ dBi,
                    const float* __restrict__ Qi, const float* __restrict__ Ki,
                    const float* __restrict__ RQ, const float* __restrict__ RK,
                    void* __restrict__ dq, i64 qb, i64 qs, i64 qh, void* __restrict__ dk, i64 kb, i64 ks, i64 kh,
                    void* __restrict__ dv, i64 vb, i64 vs, i64 vh, void* __restrict__ dg, i64 gb, i64 gs, i64 gh,
                    void* __restrict__ db, i64 bb, i64 bs, i64 bhh,
                    int tipi, int B, int Hk, int rap, int S, int Sp, int norm, float scala)
{
    const int lane = threadIdx.x & 63;
    const i64 riga = (i64)blockIdx.x * (NT / 64) + (threadIdx.x >> 6);
    if (riga >= (i64)B * Hk * S) return;
    const int bhk = (int)(riga / S), s = (int)(riga - (i64)bhk * S), b = bhk / Hk, hk = bhk - b * Hk;
    const int H = Hk * rap;
    float aq[DK / 64], ak[DK / 64];
    #pragma unroll
    for (int u = 0; u < DK / 64; ++u) { aq[u] = 0.0f; ak[u] = 0.0f; }
    for (int r = 0; r < rap; ++r) {
        const int h = hk * rap + r;
        const i64 ri = (i64)(b * H + h) * Sp + s;
        float gq[DK / 64], gk[DK / 64], pq = 0.0f, pk = 0.0f;
        #pragma unroll
        for (int u = 0; u < DK / 64; ++u) {
            const i64 i = ri * DK + lane + 64 * u;
            gq[u] = dQi[i]; gk[u] = dKi[i];
            pq = fmaf(gq[u], Qi[i], pq); pk = fmaf(gk[u], Ki[i], pk);
        }
        if (norm) { pq = somma64(pq); pk = somma64(pk); }
        const float rq = RQ[ri], rk = RK[ri];
        #pragma unroll
        for (int u = 0; u < DK / 64; ++u) {
            const i64 i = ri * DK + lane + 64 * u;
            /* Qi = y scala: dy = dQi scala, y <y, dy> = Qi <Qi, dQi> / scala */
            aq[u] += norm ? rq * (gq[u] * scala - Qi[i] * (pq / scala)) : gq[u] * scala;
            ak[u] += norm ? rk * (gk[u] - Ki[i] * pk) : gk[u];
        }
        #pragma unroll
        for (int u = 0; u < DV / 64; ++u)
            scrivi(dv, b * vb + s * vs + h * vh + lane + 64 * u, dVi[ri * DV + lane + 64 * u], tipi & 4);
        if (lane == 0) {
            scrivi(dg, b * gb + s * gs + h * gh, dGi[ri], tipi & 8);
            scrivi(db, b * bb + s * bs + h * bhh, dBi[ri], tipi & 16);
        }
    }
    #pragma unroll
    for (int u = 0; u < DK / 64; ++u) {
        scrivi(dq, b * qb + s * qs + hk * qh + lane + 64 * u, aq[u], tipi & 1);
        scrivi(dk, b * kb + s * ks + hk * kh + lane + 64 * u, ak[u], tipi & 2);
    }
}
"""

SORGENTE_CONV = r"""
/* Convoluzione causale depthwise (+ SiLU) di Qwen3.5 / Mamba sul layout [B, S, C], senza trasporre:
   y[b, t, c] = silu(bias[c] + somma_j w[c, j] x[b, t + j - (K-1), c]), x = 0 per t < 0.
   Un thread per canale e TS istanti consecutivi; i canali vicini sono thread vicini (letture
   coalescenti). Conti in fp32, tipi fp16 o fp32 secondo i bit di 'tipi' (1 x, 2 w, 4 bias). */
typedef long long i64;
typedef _Float16 f16;
#define K KCONV
__device__ inline float leggi(const void* p, i64 i, int mezzo) {
    return mezzo ? (float)((const f16*)p)[i] : ((const float*)p)[i];
}
__device__ inline void scrivi(void* p, i64 i, float x, int mezzo) {
    if (mezzo) ((f16*)p)[i] = (f16)x; else ((float*)p)[i] = x;
}

extern "C" __global__ __launch_bounds__(256)
void conv_avanti(const void* __restrict__ x, i64 xb, i64 xs, const void* __restrict__ w, i64 wc,
                 const void* __restrict__ bias, void* __restrict__ y, int S, int Cn, int tipi, int silu)
{
    const int c = blockIdx.x * 256 + threadIdx.x;
    if (c >= Cn) return;
    const int t0 = blockIdx.y * TS, b = blockIdx.z;
    const int mx = tipi & 1;
    float wk[K];
    #pragma unroll
    for (int j = 0; j < K; ++j) wk[j] = leggi(w, (i64)c * wc + j, tipi & 2);
    const float bi = bias ? leggi(bias, c, tipi & 4) : 0.0f;
    const i64 base = (i64)b * xb + c;
    float fin[K];                       /* fin[j] = x[t + j - (K-1)] */
    #pragma unroll
    for (int j = 0; j < K - 1; ++j) {
        const int t = t0 + j - (K - 1);
        fin[j] = t >= 0 ? leggi(x, base + (i64)t * xs, mx) : 0.0f;
    }
    #pragma unroll
    for (int i = 0; i < TS; ++i) {
        const int t = t0 + i;
        if (t >= S) break;
        fin[K - 1] = leggi(x, base + (i64)t * xs, mx);
        float a = bi;
        #pragma unroll
        for (int j = 0; j < K; ++j) a = fmaf(wk[j], fin[j], a);
        if (silu) a = a / (1.0f + expf(-a));
        scrivi(y, ((i64)b * S + t) * Cn + c, a, mx);
        #pragma unroll
        for (int j = 0; j < K - 1; ++j) fin[j] = fin[j + 1];
    }
}

/* dz = dy silu'(z) (z ricalcolata), dx[t] = somma_j w[j] dz[t + (K-1) - j];
   con parz: dw e dbias parziali per blocco di TS istanti, [B * gridDim.y, Cn, K] e [.., Cn] */
extern "C" __global__ __launch_bounds__(256)
void conv_indietro(const void* __restrict__ x, i64 xb, i64 xs, const void* __restrict__ w, i64 wc,
                   const void* __restrict__ bias, const void* __restrict__ dy, i64 yb, i64 ys,
                   void* __restrict__ dx, float* __restrict__ dwp, float* __restrict__ dbp,
                   int S, int Cn, int tipi, int silu)
{
    const int c = blockIdx.x * 256 + threadIdx.x;
    if (c >= Cn) return;
    const int t0 = blockIdx.y * TS, b = blockIdx.z;
    const int mx = tipi & 1, my = tipi & 8;
    float wk[K];
    #pragma unroll
    for (int j = 0; j < K; ++j) wk[j] = leggi(w, (i64)c * wc + j, tipi & 2);
    const float bi = bias ? leggi(bias, c, tipi & 4) : 0.0f;
    const i64 base = (i64)b * xb + c, basey = (i64)b * yb + c;
    float xw[TS + 2 * K - 2];           /* xw[m] = x[t0 - (K-1) + m] */
    #pragma unroll
    for (int m = 0; m < TS + 2 * K - 2; ++m) {
        const int t = t0 - (K - 1) + m;
        xw[m] = (t >= 0 && t < S) ? leggi(x, base + (i64)t * xs, mx) : 0.0f;
    }
    float dz[TS + K - 1];               /* dz[m] = dz[t0 + m] */
    #pragma unroll
    for (int m = 0; m < TS + K - 1; ++m) {
        const int u = t0 + m;
        float d = 0.0f;
        if (u < S) {
            float z = bi;
            #pragma unroll
            for (int j = 0; j < K; ++j) z = fmaf(wk[j], xw[m + j], z);
            d = leggi(dy, basey + (i64)u * ys, my);
            if (silu) {
                const float sg = 1.0f / (1.0f + expf(-z));
                d *= sg * (1.0f + z * (1.0f - sg));
            }
        }
        dz[m] = d;
    }
    #pragma unroll
    for (int i = 0; i < TS; ++i) {
        const int t = t0 + i;
        if (t < S) {
            float a = 0.0f;
            #pragma unroll
            for (int j = 0; j < K; ++j) a = fmaf(wk[j], dz[i + (K - 1) - j], a);
            scrivi(dx, ((i64)b * S + t) * Cn + c, a, mx);
        }
    }
    if (dwp) {
        const i64 p = ((i64)b * gridDim.y + blockIdx.y) * Cn + c;
        #pragma unroll
        for (int j = 0; j < K; ++j) {
            float a = 0.0f;
            #pragma unroll
            for (int i = 0; i < TS; ++i) a = fmaf(dz[i], xw[i + j], a);     /* dz[i] = 0 oltre S */
            dwp[p * K + j] = a;
        }
        float a = 0.0f;
        #pragma unroll
        for (int i = 0; i < TS; ++i) a += dz[i];
        dbp[p] = a;
    }
}
"""

NOMI = ("gdn_prep", "gdn_ric", "gdn_ric_ind", "gdn_locale", "gdn_ingresso", "gdn_converti", "gdn_uscita_ind")


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
EXTRA = []          # opzioni di compilazione in piu' (prove)
_moduli = {}
_hip = None
_rtc = None


def compila(dk, dv, extra=(), sorgente=None):
    global _rtc
    if _rtc is None:
        for p in _percorsi_hiprtc():
            if os.path.exists(p):
                _rtc = _carica_dll(p)
                break
        else:
            raise RuntimeError("nessuna hipRTC trovata")
    prog = vp()
    assert _rtc.hiprtcCreateProgram(ctypes.byref(prog), (sorgente or SORGENTE).encode(), b"gdn.hip", 0, None, None) == 0
    opz = [b"--offload-arch=gfx906", b"-mcode-object-version=5", b"-O3",
           f"-DDK={dk}".encode(), f"-DDV={dv}".encode(), f"-DDMAX={max(dk, dv)}".encode()]
    opz += [x.encode() for x in extra]
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


def _funzioni(dk, dv):
    """Il modulo dei kernel gdn per (Dk, Dv), oppure quello della conv causale per dk="conv", dv=K."""
    global _hip
    with _lock:
        if (dk, dv) not in _moduli:
            if _hip is None:
                _hip = ctypes.CDLL("amdhip64.dll")
                _hip.hipModuleLaunchKernel.argtypes = [vp] + [ctypes.c_uint] * 7 + [vp, vp, vp]
            if dk == "conv":
                codice = compila(0, 0, [f"-DKCONV={dv}", f"-DTS={TS_CONV}"], sorgente=SORGENTE_CONV)
                nomi = ("conv_avanti", "conv_indietro")
            else:
                codice = compila(dk, dv, EXTRA)
                nomi = NOMI
            mod = vp()
            assert _hip.hipModuleLoadData(ctypes.byref(mod), codice) == 0
            f = {}
            for nome in nomi:
                h = vp()
                assert _hip.hipModuleGetFunction(ctypes.byref(h), mod, nome.encode()) == 0
                f[nome] = h
            _moduli[(dk, dv)] = (f, codice, mod)
        return _moduli[(dk, dv)][0]


def _lancia(dk, dv, nome, gx, gy, argomenti, gz=1):
    f = _funzioni(dk, dv)[nome]
    conv = []
    for a in argomenti:
        if isinstance(a, torch.Tensor):
            conv.append(vp(a.data_ptr()))
        elif a is None:
            conv.append(vp(0))
        else:
            conv.append(a)
    args = (vp * len(conv))(*[ctypes.cast(ctypes.byref(x), vp) for x in conv])
    stream = torch.cuda.current_stream().cuda_stream
    rc = _hip.hipModuleLaunchKernel(f, gx, gy, gz, 256, 1, 1, 0, vp(stream), args, None)
    if rc != 0:
        raise RuntimeError(f"{nome}: hipModuleLaunchKernel rc={rc}")


I = ctypes.c_int
L = ctypes.c_longlong


def avanti(q, k, v, g, beta, stato0=None, stato_finale=False, uscita=None):
    """Nucleo, senza autograd. q (già normalizzata e scalata), k: [B, H, Sp, Dk]; v: [B, H, Sp, Dv];
    g, beta: [B, H, Sp]; fp32 contigui, Sp multiplo di 64. uscita=None: o fp32 [B, H, Sp, Dv];
    altrimenti (o, H, S) con o [B, S, H, Dv] contiguo fp16 o fp32, scritto per le righe < S.
    Restituisce (o, stato_fin, salvati)."""
    B, H, Sp, dk = q.shape
    dv = v.shape[-1]
    NC = Sp // C
    BH = B * H
    e = lambda *forma: torch.empty(*forma, device=q.device, dtype=torch.float32)
    Gc, SC = e(B, H, Sp), e(B, H, Sp, 4)
    Tm, Am, Pm = e(BH, NC, C, C), e(BH, NC, C, C), e(BH, NC, C, C)
    Wm, Um = e(B, H, Sp, dk), e(B, H, Sp, dv)
    _lancia(dk, dv, "gdn_prep", NC, BH, [q, k, v, g, beta, Gc, SC, Tm, Am, Pm, Wm, Um, I(NC)])
    Sst, Vn = e(BH, NC, dk, dv), e(B, H, Sp, dv)
    if uscita is None:
        o = e(B, H, Sp, dv)
        passi, Hs, S, o16 = (H * Sp * dv, dv, Sp * dv), H, Sp, 0
    else:
        o, Hs, S = uscita
        passi, o16 = (S * Hs * dv, Hs * dv, dv), int(o.dtype == torch.float16)
    Sfin = e(B, H, dk, dv) if stato_finale else None
    _lancia(dk, dv, "gdn_ric", dv // 32, BH,
            [q, k, SC, Pm, Wm, Um, stato0, Sst, Vn, o, Sfin, I(NC)] + [L(x) for x in passi]
            + [I(Hs), I(S), I(o16)])
    return o, Sfin, (Gc, SC, Tm, Am, Pm, Wm, Sst, Vn)


def indietro(do, q, k, v, salvati, dstato_fin=None, con_stato0=False):
    """Nucleo dell'indietro, forme interne come avanti(); do fp32 [B, H, Sp, Dv] contiguo."""
    Gc, SC, Tm, Am, Pm, Wm, Sst, Vn = salvati
    B, H, Sp, dk = q.shape
    dv = v.shape[-1]
    NC = Sp // C
    BH = B * H
    e = lambda *forma: torch.empty(*forma, device=q.device, dtype=torch.float32)
    dSst, dVn = e(BH, NC, dk, dv), e(B, H, Sp, dv)
    dS0 = e(B, H, dk, dv) if con_stato0 else None
    _lancia(dk, dv, "gdn_ric_ind", dv // 32, BH,
            [q, k, SC, Pm, Wm, do, dstato_fin, dSst, dVn, dS0, I(NC)])
    scratch = e(BH * NC, 4 * C * C + C * dk)
    dq, dk_, dv_ = torch.empty_like(q), torch.empty_like(k), torch.empty_like(v)
    db, dg = e(B, H, Sp), e(B, H, Sp)
    _lancia(dk, dv, "gdn_locale", NC, BH,
            [q, k, v, Gc, SC, Tm, Am, Pm, Sst, dSst, Vn, dVn, do, scratch,
             dq, dk_, dv_, db, dg, I(NC)])
    return dq, dk_, dv_, dg, db, dS0


def _f32c(x):
    return None if x is None else x.to(torch.float32).contiguous()


def _passi_bsh(x):
    """Passi (b, s, h) in elementi di un tensore [B, S, H(, D)], ultima dimensione contigua."""
    if x.dim() == 4 and x.stride(-1) != 1:
        x = x.contiguous()
    return x, [L(x.stride(0)), L(x.stride(1)), L(x.stride(2))]


def _tipo(x):
    assert x.dtype in (torch.float16, torch.float32), f"dtype {x.dtype} non supportato (fp16 o fp32)"
    return int(x.dtype == torch.float16)


def _gdn_avanti(query, key, value, g, beta, stato0, stato_finale, norm):
    """query/key [B, S, Hk, Dk] (Hk divide H), value [B, S, H, Dv], g/beta [B, S, H]: viste a passo
    qualunque. Restituisce (o, Sfin, salvati, info)."""
    B, S, Hk, dk = key.shape
    H, dv = value.shape[2], value.shape[3]
    rap = H // Hk
    Sp = (S + C - 1) // C * C
    BH = B * H
    scala = dk ** -0.5
    e = lambda *forma: torch.empty(*forma, device=query.device, dtype=torch.float32)
    Qi, Ki, Vi = e(B, H, Sp, dk), e(B, H, Sp, dk), e(B, H, Sp, dv)
    Gi, Bi, RQ, RK = e(B, H, Sp), e(B, H, Sp), e(B, H, Sp), e(B, H, Sp)
    query, pq = _passi_bsh(query)
    key, pk = _passi_bsh(key)
    value, pv = _passi_bsh(value)
    g, pg = _passi_bsh(g)
    beta, pb = _passi_bsh(beta)
    tipi = _tipo(query) | _tipo(key) << 1 | _tipo(value) << 2 | _tipo(g) << 3 | _tipo(beta) << 4
    _lancia(dk, dv, "gdn_ingresso", (BH * Sp + 3) // 4, 1,
            [query, key, value, g, beta] + pq + pk + pv + pg + pb
            + [I(tipi), I(BH), I(H), I(rap), I(S), I(Sp), I(int(norm)), ctypes.c_float(scala),
               Qi, Ki, Vi, Gi, Bi, RQ, RK])
    o = torch.empty(B, S, H, dv, device=query.device, dtype=query.dtype)
    _, Sfin, salvati = avanti(Qi, Ki, Vi, Gi, Bi, _f32c(stato0), stato_finale, uscita=(o, H, S))
    info = (B, S, Hk, H, dk, dv, Sp, scala, int(norm), tipi, None if stato0 is None else stato0.dtype)
    return o, Sfin, (Qi, Ki, Vi, RQ, RK) + salvati, info


def _gdn_indietro(salvati, info, do, dSfin, dq, dk_, dv_, dg, db):
    """Scrive i gradienti nelle viste dq [B,S,Hk,Dk], dk_, dv_ [B,S,H,Dv], dg, db [B,S,H]; restituisce dS0."""
    Qi, Ki, Vi, RQ, RK, *resto = salvati
    B, S, Hk, H, dk, dv, Sp, scala, norm, tipi, dtipo0 = info
    BH = B * H
    do, pdo = _passi_bsh(do)
    dOi = torch.empty(B, H, Sp, dv, device=do.device, dtype=torch.float32)
    _lancia(dk, dv, "gdn_converti", (BH * Sp + 3) // 4, 1,
            [do] + pdo + [I(_tipo(do)), I(BH), I(H), I(S), I(Sp), dOi])
    dQi, dKi, dVi, dGi, dBi, dS0 = indietro(dOi, Qi, Ki, Vi, resto, _f32c(dSfin), dtipo0 is not None)
    passi = lambda x: [L(x.stride(0)), L(x.stride(1)), L(x.stride(2))]
    _lancia(dk, dv, "gdn_uscita_ind", (B * Hk * S + 3) // 4, 1,
            [dQi, dKi, dVi, dGi, dBi, Qi, Ki, RQ, RK, dq] + passi(dq) + [dk_] + passi(dk_)
            + [dv_] + passi(dv_) + [dg] + passi(dg) + [db] + passi(db)
            + [I(tipi), I(B), I(Hk), I(H // Hk), I(S), I(Sp), I(norm), ctypes.c_float(scala)])
    return None if dS0 is None else dS0.to(dtipo0)


class _GDN(torch.autograd.Function):
    @staticmethod
    def forward(ctx, query, key, value, g, beta, stato0, stato_finale, norm):
        o, Sfin, salvati, info = _gdn_avanti(query, key, value, g, beta, stato0, stato_finale, norm)
        ctx.save_for_backward(*salvati)
        ctx.info = info
        ctx.dtipi = [x.dtype for x in (query, key, value, g, beta)]
        return o if Sfin is None else (o, Sfin)

    @staticmethod
    def backward(ctx, do, dSfin=None):
        B, S, Hk, H, dk, dv = ctx.info[:6]
        dev = do.device
        dq = torch.empty(B, S, Hk, dk, device=dev, dtype=ctx.dtipi[0])
        dk_ = torch.empty(B, S, Hk, dk, device=dev, dtype=ctx.dtipi[1])
        dv_ = torch.empty(B, S, H, dv, device=dev, dtype=ctx.dtipi[2])
        dg = torch.empty(B, S, H, device=dev, dtype=ctx.dtipi[3])
        db = torch.empty(B, S, H, device=dev, dtype=ctx.dtipi[4])
        dS0 = _gdn_indietro(ctx.saved_tensors, ctx.info, do, dSfin, dq, dk_, dv_, dg, db)
        return dq, dk_, dv_, dg, db, dS0, None, None


def _viste_qkv(qkv, Hk, H, dk, dv):
    B, S, _ = qkv.shape
    q = qkv[..., :Hk * dk].unflatten(-1, (Hk, dk))
    k = qkv[..., Hk * dk:2 * Hk * dk].unflatten(-1, (Hk, dk))
    v = qkv[..., 2 * Hk * dk:].unflatten(-1, (H, dv))
    return q, k, v


class _GDNImpacchettato(torch.autograd.Function):
    """q, k, v come colonne di un solo tensore [B, S, 2 Hk Dk + H Dv] (l'uscita della conv dello
    strato): nessuna vista intermedia per l'autograd, e il gradiente torna in un solo tensore."""
    @staticmethod
    def forward(ctx, qkv, g, beta, forma, norm):
        q, k, v = _viste_qkv(qkv, *forma)
        o, _, salvati, info = _gdn_avanti(q, k, v, g, beta, None, False, norm)
        ctx.save_for_backward(*salvati)
        ctx.info, ctx.forma = info, forma
        ctx.dtipi = (qkv.dtype, g.dtype, beta.dtype)
        return o

    @staticmethod
    def backward(ctx, do):
        B, S = ctx.info[:2]
        H = ctx.info[3]
        dev = do.device
        dqkv = torch.empty(B, S, sum((2 * ctx.forma[0] * ctx.forma[2], ctx.forma[1] * ctx.forma[3])),
                           device=dev, dtype=ctx.dtipi[0])
        dq, dk_, dv_ = _viste_qkv(dqkv, *ctx.forma)
        dg = torch.empty(B, S, H, device=dev, dtype=ctx.dtipi[1])
        db = torch.empty(B, S, H, device=dev, dtype=ctx.dtipi[2])
        _gdn_indietro(ctx.saved_tensors, ctx.info, do, None, dq, dk_, dv_, dg, db)
        return dqkv, dg, db, None, None


def gdn_impacchettato(qkv, g, beta, Hk, H, dk, dv, norm=True):
    """o [B, S, H, Dv] da qkv [B, S, 2 Hk Dk + H Dv] (q e k a Hk teste, ripetute come
    repeat_interleave fino a H), g e beta [B, S, H]; blocchi da 64, senza stato."""
    assert qkv.stride(-1) == 1 and qkv.shape[-1] == 2 * Hk * dk + H * dv and H % Hk == 0
    assert dk % 64 == 0 and dv % 64 == 0 and max(dk, dv) <= 128
    return _GDNImpacchettato.apply(qkv, g, beta, (Hk, H, dk, dv), bool(norm))


# ---------------------------------------------------------------- convoluzione causale [B, S, C]
TS_CONV = 16


class _ConvCausale(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, w, bias, silu):
        if x.stride(-1) != 1:
            x = x.contiguous()
        B, S, Cn = x.shape
        K = w.shape[-1]
        y = torch.empty(B, S, Cn, device=x.device, dtype=x.dtype)
        tipi = _tipo(x) | _tipo(w) << 1 | (_tipo(bias) << 2 if bias is not None else 0)
        _lancia("conv", K, "conv_avanti", (Cn + 255) // 256, (S + TS_CONV - 1) // TS_CONV,
                [x, L(x.stride(0)), L(x.stride(1)), w, L(w.stride(0)), bias, y, I(S), I(Cn), I(tipi),
                 I(int(silu))], gz=B)
        ctx.save_for_backward(x, w, bias)
        ctx.opz = (tipi, int(silu))
        return y

    @staticmethod
    def backward(ctx, dy):
        x, w, bias = ctx.saved_tensors
        tipi, silu = ctx.opz
        if dy.stride(-1) != 1:
            dy = dy.contiguous()
        B, S, Cn = x.shape
        K = w.shape[-1]
        nt = (S + TS_CONV - 1) // TS_CONV
        dx = torch.empty_like(x, memory_format=torch.contiguous_format)
        parz = ctx.needs_input_grad[1] or ctx.needs_input_grad[2]
        dwp = torch.empty(B * nt, Cn, K, device=x.device, dtype=torch.float32) if parz else None
        dbp = torch.empty(B * nt, Cn, device=x.device, dtype=torch.float32) if parz else None
        _lancia("conv", K, "conv_indietro", (Cn + 255) // 256, nt,
                [x, L(x.stride(0)), L(x.stride(1)), w, L(w.stride(0)), bias, dy, L(dy.stride(0)),
                 L(dy.stride(1)), dx, dwp, dbp, I(S), I(Cn), I(tipi | _tipo(dy) << 3), I(silu)], gz=B)
        dw = dwp.sum(0).to(w.dtype) if parz and ctx.needs_input_grad[1] else None
        db = dbp.sum(0).to(bias.dtype) if parz and bias is not None and ctx.needs_input_grad[2] else None
        return dx, dw, db, None


def conv_causale(x, w, bias=None, silu=True):
    """Conv1d causale depthwise (+ SiLU) su x [B, S, C] (canali contigui): uguale a
    causal_conv1d_fn(x.transpose(1, 2), w, bias, "silu").transpose(1, 2) senza trasporre.
    w [C, K] (o [C, 1, K]); uscita nel dtype di x, conti in fp32."""
    if w.dim() == 3:
        w = w.squeeze(1)
    assert w.shape[0] == x.shape[-1] and w.shape[-1] <= 8
    return _ConvCausale.apply(x, w, bias, bool(silu))


# ---------------------------------------------------------------- lo strato Qwen3.5 senza permutazioni
_forward_originale = {}


def _forward_strato(self, hidden_states, cache_params=None, attention_mask=None, **kwargs):
    """Qwen3_5GatedDeltaNet.forward per l'addestramento (senza cache): conv causale su [B, S, C],
    q, k, v come colonne dell'uscita della conv (nessuna trasposta, nessun repeat_interleave),
    gated delta rule impacchettato. Con cache, sequenze impacchettate o attivazione diversa da
    SiLU ricade sull'originale."""
    if (cache_params is not None or kwargs.get("cu_seq_lens_q") is not None or self.activation not in ("silu", "swish")
            or not hidden_states.is_cuda):
        return _forward_originale[type(self)](self, hidden_states, cache_params, attention_mask, **kwargs)
    modulo = __import__(type(self).__module__, fromlist=["apply_mask_to_padding_states"])
    hidden_states = modulo.apply_mask_to_padding_states(hidden_states, attention_mask)
    B, S, _ = hidden_states.shape
    mixed_qkv = self.in_proj_qkv(hidden_states)
    z = self.in_proj_z(hidden_states).reshape(B, S, -1, self.head_v_dim)
    b = self.in_proj_b(hidden_states)
    a = self.in_proj_a(hidden_states)
    mixed_qkv = conv_causale(mixed_qkv, self.conv1d.weight, self.conv1d.bias, silu=True)
    beta = b.sigmoid()
    g = -self.A_log.float().exp() * torch.nn.functional.softplus(a.float() + self.dt_bias)
    core = gdn_impacchettato(mixed_qkv, g, beta, self.num_k_heads, self.num_v_heads,
                             self.head_k_dim, self.head_v_dim, norm=True)
    core = self.norm(core.reshape(-1, self.head_v_dim), z.reshape(-1, self.head_v_dim))
    return self.out_proj(core.reshape(B, S, -1))


def l2norm(x, dim=-1, eps=1e-6):
    """Come in transformers (allineata a FLA), nel dtype d'ingresso. (Il kernel la fa in fp32.)"""
    return x * torch.rsqrt((x * x).sum(dim=dim, keepdim=True) + eps)


def chunk_gated_delta_rule(query, key, value, g, beta, chunk_size=64, initial_state=None,
                           output_final_state=False, use_qk_l2norm_in_kernel=False, **kwargs):
    """Sostituto di transformers.models.qwen3_5.modeling_qwen3_5.torch_chunk_gated_delta_rule.
    La normalizzazione L2 di q e k (use_qk_l2norm_in_kernel) si fa in fp32 dentro il kernel: il
    riferimento la fa nel dtype d'ingresso (fp16), quindi le uscite differiscono a livello
    dell'arrotondamento fp16, con errore contro fp64 uguale o minore."""
    assert chunk_size == C, "blocchi da 64"
    assert kwargs.get("cu_seqlens") is None, "cu_seqlens (sequenze impacchettate) non supportato"
    B, S, H, dk = key.shape
    dv = value.shape[-1]
    assert query.shape == key.shape and value.shape[:3] == key.shape[:3], "stesse teste per q, k e v"
    assert g.shape == beta.shape == key.shape[:3], "g e beta [B, S, H]"
    assert dk % 64 == 0 and dv % 64 == 0 and max(dk, dv) <= 128, "Dk e Dv multipli di 64, al massimo 128"
    r = _GDN.apply(query, key, value, g, beta, initial_state, bool(output_final_state),
                   bool(use_qk_l2norm_in_kernel))
    return (r, None) if not output_final_state else r


def aggancia(modulo=None, strato=None):
    """Monkeypatch nel solo processo. Sempre: modulo.torch_chunk_gated_delta_rule -> questo kernel.
    Con strato (default; GDN_STRATO=0 nell'ambiente lo spegne): anche il forward di
    Qwen3_5GatedDeltaNet (o della classe *GatedDeltaNet del modulo), con la conv causale fusa e
    senza permutazioni. Restituisce la funzione originale."""
    if modulo is None:
        from transformers.models.qwen3_5 import modeling_qwen3_5 as modulo
    if strato is None:
        strato = os.environ.get("GDN_STRATO", "1") != "0"
    orig = modulo.torch_chunk_gated_delta_rule
    modulo.torch_chunk_gated_delta_rule = chunk_gated_delta_rule
    if strato:
        for nome in dir(modulo):
            cls = getattr(modulo, nome)
            if (isinstance(cls, type) and nome.endswith("GatedDeltaNet") and cls not in _forward_originale
                    and cls.__module__ == modulo.__name__):
                _forward_originale[cls] = cls.forward
                cls.forward = _forward_strato
    return orig


def sgancia(modulo, orig):
    modulo.torch_chunk_gated_delta_rule = orig
    for cls, f in list(_forward_originale.items()):
        if cls.__module__ == modulo.__name__:
            cls.forward = f
            del _forward_originale[cls]

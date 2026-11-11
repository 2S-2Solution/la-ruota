"""VEGA-PATCH 78: eigh e svd via rocSOLVER - casi oltre battuta_linalg_dimensioni.py.

    python -u prova_eigh_svd_78.py

Rettangolari alte e larghe, full_matrices si'/no, complessi, solo valori, gradienti
(contro la CPU), svd_lowrank / pca_lowrank, viste non contigue, ripetibilita'.
"""
import torch

torch.manual_seed(0)
esiti = []


def rel(a, b):
    a, b = a.detach().cpu().to(torch.complex128 if a.is_complex() else torch.float64), \
        b.detach().cpu().to(torch.complex128 if b.is_complex() else torch.float64)
    return ((a - b).abs().max() / b.abs().max().clamp_min(1e-30)).item()


def controlla(nome, d, tol):
    esiti.append(d < tol)
    print(f"  {'OK ' if d < tol else 'ERR'} {nome:58s} {d:.1e}", flush=True)


for dt, tol in ((torch.float32, 2e-4), (torch.float64, 1e-10), (torch.complex64, 2e-4), (torch.complex128, 1e-10)):
    nd = str(dt)[6:]
    for forma in ((100, 37), (37, 100), (3, 80, 64), (2, 64, 90), (130, 130)):
        A = torch.randn(*forma, dtype=dt)
        for full in (False, True):
            u, s, vh = torch.linalg.svd(A.cuda(), full_matrices=full)
            k = min(forma[-2:])
            ric = u[..., :, :k] @ torch.diag_embed(s).to(dt) @ vh[..., :k, :]
            ort_u = rel(u.mH @ u, torch.eye(u.shape[-1], dtype=dt).expand(u.mH.shape[:-1] + (u.shape[-1],)))
            ort_v = rel(vh @ vh.mH, torch.eye(vh.shape[-2], dtype=dt).expand(vh.shape[:-1] + (vh.shape[-2],)))
            controlla(f"svd {nd} {forma} full={full}: ricostruzione, U e V ortonormali",
                      max(rel(ric, A), ort_u, ort_v), tol)
        controlla(f"svdvals {nd} {forma}", rel(torch.linalg.svdvals(A.cuda()), torch.linalg.svdvals(A)), tol)
    for n in (5, 64, 129):
        B = torch.randn(2, n, n, dtype=dt)
        H = B @ B.mH + n * torch.eye(n, dtype=dt)
        for uplo in ("L", "U"):
            w, v = torch.linalg.eigh(H.cuda(), UPLO=uplo)
            controlla(f"eigh {nd} n={n} UPLO={uplo}: valori, ricostruzione",
                      max(rel(w, torch.linalg.eigvalsh(H)), rel(v @ torch.diag_embed(w).to(dt) @ v.mH, H)), tol)

# vista non contigua (trasposta) e gradienti
A = torch.randn(64, 90, dtype=torch.float64)
controlla("svdvals su vista trasposta", rel(torch.linalg.svdvals(A.cuda().mT), torch.linalg.svdvals(A.mT)), 1e-10)
H = A @ A.mT
controlla("eigvalsh su vista trasposta", rel(torch.linalg.eigvalsh(H.cuda().mT), torch.linalg.eigvalsh(H)), 1e-10)
g = {}
for dove in ("cpu", "cuda"):
    X = A.clone().to(dove).requires_grad_()
    u, s, vh = torch.linalg.svd(X, full_matrices=False)
    (s.sum() + (u[:, :3].abs().sum()) + vh[:3].abs().sum()).backward()
    Y = H.clone().to(dove).requires_grad_()
    w, v = torch.linalg.eigh(Y)
    (w[-5:].sum() + v[:, -3:].abs().sum()).backward()
    g[dove] = (X.grad, Y.grad)
controlla("gradiente della svd contro la CPU", rel(g["cuda"][0], g["cpu"][0]), 1e-8)
controlla("gradiente della eigh contro la CPU", rel(g["cuda"][1], g["cpu"][1]), 1e-8)

# svd_lowrank e pca_lowrank e ripetibilita'
M = torch.randn(2000, 64).cuda()
# svd_lowrank fa GEMM con K=2000 su operandi a colonne: con le atomiche di hipBLAS accese
# (predefinito di PyTorch su ROCm, CublasHandlePool.cpp) l'ordine delle somme varia, ~1e-4.
# Ripetibile solo con use_deterministic_algorithms(True), che le spegne.
torch.use_deterministic_algorithms(True)
r = []
for _ in range(4):
    torch.manual_seed(1)
    r.append(torch.svd_lowrank(M, q=16))
torch.use_deterministic_algorithms(False)
controlla("svd_lowrank, algoritmi deterministici: 4 corse uguali",
          max(max(rel(x, y) for x, y in zip(r[0], ri)) for ri in r[1:]), 1e-12)
r = [torch.linalg.svd(M, full_matrices=False) for _ in range(4)]
controlla("svd 2000x64 fp32: 4 corse uguali", max(max(rel(x, y) for x, y in zip(r[0], ri)) for ri in r[1:]), 1e-12)
S = (M.T @ M).double()
r = [torch.linalg.eigh(S) for _ in range(4)]
controlla("eigh 64 fp64: 4 corse uguali", max(max(rel(x, y) for x, y in zip(r[0], ri)) for ri in r[1:]), 1e-12)
# matrice vuota e lotto vuoto
controlla("svd su lotto vuoto", float(torch.linalg.svd(torch.randn(0, 4, 3).cuda())[1].numel() != 0), 0.5)
controlla("eigh su lotto vuoto", float(torch.linalg.eigh(torch.randn(0, 4, 4).cuda())[0].numel() != 0), 0.5)

print(f"\n{sum(esiti)} su {len(esiti)} giusti")

"""Le operazioni tipiche di una pre-elaborazione sulla GPU si ripetono uguali?

    python -u prova_determinismo_gpu.py

Ogni operazione due volte, con lo stesso seme e gli stessi dati: il risultato deve essere
identico bit a bit (sono operazioni deterministiche anche su NVIDIA).
"""
import torch

M = torch.randn(2000, 64, device="cuda")
esiti = []


def prova(nome, f):
    torch.manual_seed(123)
    a = f()
    torch.manual_seed(123)
    b = f()
    if isinstance(a, (tuple, list)):
        d = max((x - y).abs().max().item() for x, y in zip(a, b))
    else:
        d = (a - b).abs().max().item()
    esiti.append(d == 0)
    print(f"  {'OK ' if d == 0 else 'ERR'}  {nome:44s} differenza fra due corse {d:.1e}", flush=True)


prova("torch.randn sulla GPU", lambda: torch.randn(1000, 100, device="cuda"))
prova("torch.rand sulla GPU", lambda: torch.rand(1000, 100, device="cuda"))
prova("matmul", lambda: M.t() @ M)
prova("linalg.qr", lambda: torch.linalg.qr(M))
prova("linalg.svd (ridotta)", lambda: torch.linalg.svd(M, full_matrices=False))
prova("linalg.eigh", lambda: torch.linalg.eigh(M.t() @ M))
prova("svd_lowrank q=16", lambda: torch.svd_lowrank(M, q=16))
prova("svd_lowrank q=16, niter=4", lambda: torch.svd_lowrank(M, q=16, niter=4))
prova("pca_lowrank", lambda: torch.pca_lowrank(M, q=16))
prova("quantile", lambda: torch.quantile(M[:, 0], torch.linspace(0, 1, 50, device="cuda")))
prova("sort", lambda: torch.sort(M, dim=0)[0])
prova("argsort stabile", lambda: torch.argsort(M[:, 0], stable=True).float())
print(f"\n{sum(esiti)} su {len(esiti)} ripetibili", flush=True)

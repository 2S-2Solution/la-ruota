"""svd_lowrank sulla GPU: quale passo non si ripete? (randn, matmul, qr, svd piccola)

    python -u prova_lowrank_passi.py
"""
import torch

M = torch.randn(2000, 64).cuda()


def scarto(f, volte=4):
    r = [f() for _ in range(volte)]
    r = [x if isinstance(x, tuple) else (x,) for x in r]
    return max(max((a - b).abs().max().item() for a, b in zip(r[0], ri)) for ri in r[1:])


def randn():
    torch.manual_seed(1)
    return torch.randn(64, 16, device="cuda")


R = randn()
Y = M @ R
print(f"  randn seminato     {scarto(randn):.1e}")
print(f"  matmul 2000x64x16  {scarto(lambda: M @ R):.1e}")
print(f"  matmul M^T Y       {scarto(lambda: M.mT @ Y):.1e}")
print(f"  qr 2000x16         {scarto(lambda: torch.linalg.qr(Y)):.1e}")
print(f"  geqrf 2000x16      {scarto(lambda: torch.geqrf(Y)):.1e}")
Q = torch.linalg.qr(Y).Q
B = Q.mT @ M
print(f"  svd 16x64          {scarto(lambda: torch.linalg.svd(B, full_matrices=False)):.1e}")
for q in (16,):
    def lr():
        torch.manual_seed(1)
        return torch.svd_lowrank(M, q=q, niter=0)
    print(f"  svd_lowrank niter=0 {scarto(lr):.1e}")

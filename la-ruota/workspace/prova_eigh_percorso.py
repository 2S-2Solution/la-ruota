"""Quali operazioni chiama eigvalsh sulla GPU a n=48 (giusta) e a n=64 (sbagliata)?

    python -u prova_eigh_percorso.py
"""
import torch
from torch.profiler import ProfilerActivity, profile

for n in (48, 64):
    A = torch.randn(n, n, generator=torch.Generator().manual_seed(1), dtype=torch.float64)
    S = (A @ A.t() + n * torch.eye(n, dtype=torch.float64)).cuda()
    torch.linalg.eigvalsh(S)
    torch.cuda.synchronize()
    with profile(activities=[ProfilerActivity.CPU]) as p:
        torch.linalg.eigvalsh(S)
        torch.cuda.synchronize()
    nomi = [e.name for e in p.events() if e.name.startswith(("aten::", "linalg", "_linalg", "hip", "cuda"))]
    visti = []
    for x in nomi:
        if x not in visti:
            visti.append(x)
    print(f"n={n}: " + " -> ".join(visti))

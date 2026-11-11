"""eigh sulla GPU sbaglia da n=64: quale passo del percorso della ruota (via CPU) sbaglia?

    python -u prova_eigh_passi.py [n]
"""
import sys

import torch

n = int(sys.argv[1]) if len(sys.argv) > 1 else 64
A = torch.randn(n, n, generator=torch.Generator().manual_seed(1), dtype=torch.float64)
Sc = A @ A.t() + n * torch.eye(n, dtype=torch.float64)
wc = torch.linalg.eigvalsh(Sc)


def d(w):
    return ((w - wc).abs().max() / wc.abs().max()).item()


S = Sc.cuda()
E = S.mT.contiguous().mT                       # cloneBatchedColumnMajor sulla GPU
print("1. copia a colonne sulla GPU == S:", torch.equal(E.cpu(), Sc), E.stride())
Ec = E.to("cpu")
print("2. copia sulla CPU == S:", torch.equal(Ec, Sc), Ec.stride())
print(f"3. eigvalsh CPU, ingresso a colonne: {d(torch.linalg.eigvalsh(Ec)):.1e}")
w_out = torch.empty(n, dtype=torch.float64)
v_out = torch.empty(n, n, dtype=torch.float64).mT
torch.linalg.eigh(Ec, out=(w_out, v_out))
print(f"4. eigh CPU con out= a colonne: {d(w_out):.1e}")
print(f"5. eigvalsh GPU: {d(torch.linalg.eigvalsh(S).cpu()):.1e}")
w_g, v_g = torch.linalg.eigh(S)
print(f"6. eigh GPU (autovalori): {d(w_g.cpu()):.1e}")
torch.set_num_threads(1)
print(f"7. eigvalsh GPU con 1 thread CPU: {d(torch.linalg.eigvalsh(S).cpu()):.1e}")
print(f"8. eigvalsh CPU con 1 thread: {d(torch.linalg.eigvalsh(Ec)):.1e}")

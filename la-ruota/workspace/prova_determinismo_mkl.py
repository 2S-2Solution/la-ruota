"""svd ed eigh si ripetono uguali? Sulla CPU (MKL) e sulla GPU (che passa dalla CPU).

    python -u prova_determinismo_mkl.py            # com'e' oggi
    set MKL_CBWR=COMPATIBLE & python -u ...        # MKL in modalita' riproducibile
"""
import os

import torch

print("MKL_CBWR =", os.environ.get("MKL_CBWR"), "| thread", torch.get_num_threads(), flush=True)
esiti = []
for dev in ("cpu", "cuda"):
    M = torch.randn(2000, 64, generator=torch.Generator().manual_seed(0)).to(dev)
    S = M.t() @ M
    for nome, f in (("linalg.svd", lambda: torch.linalg.svd(M, full_matrices=False)),
                    ("linalg.eigh", lambda: torch.linalg.eigh(S)),
                    ("svd_lowrank", lambda: (torch.manual_seed(1), torch.svd_lowrank(M, q=16))[1])):
        r = [f() for _ in range(5)]
        d = max(max((x - y).abs().max().item() for x, y in zip(r[0], ri)) for ri in r[1:])
        esiti.append(d == 0)
        print(f"  {'OK ' if d == 0 else 'ERR'}  {dev:4s} {nome:12s} differenza massima su 5 corse {d:.1e}", flush=True)
print(f"\n{sum(esiti)} su {len(esiti)} ripetibili", flush=True)

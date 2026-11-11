"""Caratterizza il difetto muto sul gradiente pesi di Conv1d.

Trovato: cin=64 cout=64 k=1 L=256 -> forward corretto, gradiente pesi con
scarto relativo 1,08. Nessun errore, nessun NaN. Stessa famiglia del WrW3x3
gia' noto, ma un altro solver: MIOPEN_DEBUG_CONV_DIRECT_ASM_WRW3X3=0 e' gia'
attiva e non lo copre.
"""
import os
import torch
import torch.nn as nn

SENZA_MIOPEN = os.environ.get("SENZA_MIOPEN") == "1"
if SENZA_MIOPEN:
    torch.backends.cudnn.enabled = False


def caso(cin, cout, k, L, lotto=4):
    torch.manual_seed(0)
    x = torch.randn(lotto, cin, L)
    c = nn.Conv1d(cin, cout, k, padding=k // 2)
    cc = nn.Conv1d(cin, cout, k, padding=k // 2)
    cc.load_state_dict(c.state_dict())
    xc = x.clone().requires_grad_(True)
    cc(xc).sum().backward()
    xg = x.clone().cuda().requires_grad_(True)
    cg = c.cuda()
    cg(xg).sum().backward()
    rif, got = cc.weight.grad, cg.weight.grad.cpu()
    return (rif - got).abs().max().item() / max(rif.abs().max().item(), 1e-9)


print(f"MIOpen: {'DISATTIVATO' if SENZA_MIOPEN else 'attivo'}\n")
print("canali uguali, k=1, lotto=4, L=256:")
for c in (8, 16, 32, 48, 64, 96, 128, 256):
    r = caso(c, c, 1, 256)
    print(f"  cin=cout={c:4d}  rel {r:.2e}  {'ok' if r < 1e-4 else 'SBAGLIATO'}")

print("\ncin=64 cout=64 k=1, al variare della lunghezza:")
for L in (32, 64, 128, 256, 512, 1024):
    r = caso(64, 64, 1, L)
    print(f"  L={L:5d}  rel {r:.2e}  {'ok' if r < 1e-4 else 'SBAGLIATO'}")

print("\ncin=64 cout=64 k=1 L=256, al variare del lotto:")
for b in (1, 2, 4, 8, 16):
    r = caso(64, 64, 1, 256, lotto=b)
    print(f"  lotto={b:3d}  rel {r:.2e}  {'ok' if r < 1e-4 else 'SBAGLIATO'}")

print("\ncin=64 cout=64 L=256, al variare del kernel:")
for k in (1, 3, 5, 7):
    r = caso(64, 64, k, 256)
    print(f"  k={k}  rel {r:.2e}  {'ok' if r < 1e-4 else 'SBAGLIATO'}")

print("\ncanali diversi, k=1, L=256:")
for cin, cout in [(64, 32), (32, 64), (64, 128), (128, 64), (64, 65), (65, 64)]:
    r = caso(cin, cout, 1, 256)
    print(f"  cin={cin:4d} cout={cout:4d}  rel {r:.2e}  {'ok' if r < 1e-4 else 'SBAGLIATO'}")

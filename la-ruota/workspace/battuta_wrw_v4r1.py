"""Quanto e' diffuso il difetto del solver ConvAsmImplicitGemmV4R1DynamicWrw,
e quanto costa escluderlo.

Confronta il gradiente sui PESI contro CPU su un ventaglio di forme Conv1d e
Conv2d, e cronometra il backward. Si lancia due volte: senza e con
MIOPEN_DEBUG_CONV_IMPLICIT_GEMM_ASM_WRW_V4R1=0.
"""
import os
import time
import torch
import torch.nn as nn

ESCLUSO = os.environ.get("MIOPEN_DEBUG_CONV_IMPLICIT_GEMM_ASM_WRW_V4R1") == "0"


def prova(dim, cin, cout, k, spaziale, lotto=4):
    torch.manual_seed(0)
    forma = (lotto, cin) + (spaziale,) * dim
    x = torch.randn(*forma)
    Conv = nn.Conv1d if dim == 1 else nn.Conv2d
    c = Conv(cin, cout, k, padding=k // 2)
    cc = Conv(cin, cout, k, padding=k // 2)
    cc.load_state_dict(c.state_dict())
    cc(x.clone().requires_grad_(True)).sum().backward()
    cg = c.cuda()
    xg = x.clone().cuda().requires_grad_(True)
    for _ in range(2):
        cg.zero_grad(); cg(xg).sum().backward()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(5):
        cg.zero_grad(); cg(xg).sum().backward()
    torch.cuda.synchronize()
    dt = (time.perf_counter() - t0) / 5 * 1000
    rif, got = cc.weight.grad, cg.weight.grad.cpu()
    rel = (rif - got).abs().max().item() / max(rif.abs().max().item(), 1e-9)
    return rel, dt


FORME = [
    (1, 32, 32, 1, 256), (1, 64, 64, 1, 256), (1, 64, 64, 3, 256),
    (1, 64, 128, 1, 256), (1, 128, 128, 1, 512), (1, 16, 32, 5, 128),
    (1, 256, 256, 1, 256), (1, 8, 8, 1, 256),
    (2, 3, 16, 3, 32), (2, 32, 32, 1, 32), (2, 64, 64, 3, 32),
    (2, 64, 64, 1, 64), (2, 128, 128, 3, 16), (2, 16, 32, 5, 64),
]

print(f"solver V4R1 {'ESCLUSO' if ESCLUSO else 'attivo'}")
print(f"{'conv':>5} {'cin':>5} {'cout':>5} {'k':>3} {'sp':>5}  {'rel':>10}  {'ms':>7}  esito")
rotti = 0
for dim, cin, cout, k, sp in FORME:
    rel, dt = prova(dim, cin, cout, k, sp)
    ok = rel < 1e-4
    rotti += 0 if ok else 1
    print(f"{dim:4d}D {cin:5d} {cout:5d} {k:3d} {sp:5d}  {rel:10.2e}  {dt:7.2f}  {'ok' if ok else 'SBAGLIATO'}")
print(f"\nforme sbagliate: {rotti} su {len(FORME)}")

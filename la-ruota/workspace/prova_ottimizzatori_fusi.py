"""Ottimizzatori fused=True sulla ruota: quali crollano? Ogni caso in un processo suo, senza finestra d'errore.

    python -u prova_ottimizzatori_fusi.py

Ipotesi: multi_tensor_apply_for_fused_optimizer passa al kernel per valore una struttura di metadati
(FusedOptimizerTensorListMetadata) piu' grande di quella di foreach (~3,3 KB per Adam a 4 liste contro
~3,0 KB). Se il runtime HIP su Windows ha un limite di argomenti fra le due, il lancio crolla sul lato
host (0xC0000005 in torch_hip.dll). Confronto: SGD fusa (metadati piu' piccoli), Adam/AdamW fuse,
foreach. Tensori minuscoli: costo GPU trascurabile.
"""
import subprocess
import sys

CASI = {
    "AdamW foreach": "torch.optim.AdamW(p, lr=1e-3, foreach=True)",
    "SGD fused (momento)": "torch.optim.SGD(p, lr=1e-3, momentum=0.9, fused=True)",
    "SGD fused (senza momento)": "torch.optim.SGD(p, lr=1e-3, fused=True)",
    "Adam fused": "torch.optim.Adam(p, lr=1e-3, fused=True)",
    "AdamW fused": "torch.optim.AdamW(p, lr=1e-3, fused=True)",
    "AdamW fused amsgrad": "torch.optim.AdamW(p, lr=1e-3, fused=True, amsgrad=True)",
}

if len(sys.argv) > 1:
    import ctypes
    ctypes.windll.kernel32.SetErrorMode(0x0002 | 0x0001)   # SEM_NOGPFAULTERRORBOX | SEM_FAILCRITICALERRORS
    import torch
    torch.manual_seed(0)
    p = [torch.randn(100, device="cuda", requires_grad=True)]
    q = [t.detach().clone().requires_grad_(True) for t in p]
    opt = eval(CASI[sys.argv[1]])
    rif = torch.optim.SGD(q, lr=1e-3) if "SGD" in sys.argv[1] and "momento" not in sys.argv[1] else None
    for _ in range(3):
        for t in p + q:
            t.grad = torch.ones_like(t)
        opt.step()
        if rif:
            rif.step()
    torch.cuda.synchronize()
    print("PASSATO", (p[0] - q[0]).abs().max().item() if rif else "", flush=True)
    sys.exit(0)

for nome in CASI:
    try:
        r = subprocess.run([sys.executable, "-u", __file__, nome], capture_output=True, text=True, timeout=60)
        esito = "ok" if "PASSATO" in r.stdout else f"CROLLATO (codice {r.returncode & 0xFFFFFFFF:#x})"
    except subprocess.TimeoutExpired:
        esito = "BLOCCATO (oltre 60 s)"
    print(f"  {nome:28s} {esito}", flush=True)


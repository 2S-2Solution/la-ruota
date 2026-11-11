"""Battuta ampia sulle convoluzioni, in configurazione di PRODUZIONE.

Motivo: MIOpen memorizza in cache il solver scelto per ogni forma, quindi un
banco che passa non dimostra che la forma sia sana - solo che il solver in cache
oggi lo e'. Dopo aver svuotato la cache le forme vanno riprovate, ed e' cosi'
che va fatta la verifica.

Qui NON si disattiva nulla a mano: valgono le variabili che la build imposta da
sola (VEGA-PATCH 58 e 62). Se qualcosa cade, e' un difetto vivo in produzione.
Si confronta il gradiente sui PESI, che e' dove cadono tutti e tre i solver noti,
e anche quello sui dati e la forward.
"""
import itertools
import sys
import os

# I solver noti si RIACCENDONO esplicitamente quando si va a caccia: torch/__init__.py
# li spegne con setdefault, quindi un banco lanciato normalmente misura zero difetti
# per costruzione. Con RIACCENDI=1 si cerca un QUARTO solver difettoso; senza, si
# verifica la configurazione di produzione.
if os.environ.get("RIACCENDI") == "1":
    os.environ["MIOPEN_DEBUG_CONV_DIRECT_ASM_WRW3X3"] = "1"
    os.environ["MIOPEN_DEBUG_CONV_IMPLICIT_GEMM_ASM_WRW_V4R1"] = "1"

import torch
import torch.nn as nn


def esito(rif, got):
    g = got.detach().cpu()
    if torch.isnan(g).any():
        return "NaN", float("nan")
    if g.abs().max().item() == 0.0 and rif.abs().max().item() > 0:
        return "AZZERATO", 1.0
    rel = (rif - g).abs().max().item() / max(rif.abs().max().item(), 1e-9)
    return ("ok" if rel < 1e-4 else "SBAGLIATO"), rel


def caso(dim, cin, cout, k, sp, lotto, stride=1, groups=1):
    torch.manual_seed(0)
    forma = (lotto, cin) + (sp,) * dim
    x = torch.randn(*forma)
    Conv = nn.Conv1d if dim == 1 else nn.Conv2d
    c = Conv(cin, cout, k, padding=k // 2, stride=stride, groups=groups)
    cc = Conv(cin, cout, k, padding=k // 2, stride=stride, groups=groups)
    cc.load_state_dict(c.state_dict())
    xc = x.clone().requires_grad_(True)
    rif_out = cc(xc)
    rif_out.sum().backward()
    cg = c.cuda()
    xg = x.clone().cuda().requires_grad_(True)
    got_out = cg(xg)
    got_out.sum().backward()
    peggiore, quale = 0.0, "ok"
    for nome, r, g in (("avanti", rif_out, got_out),
                       ("grad dati", xc.grad, xg.grad),
                       ("grad pesi", cc.weight.grad, cg.weight.grad)):
        e, rel = esito(r, g)
        if e != "ok" and (quale == "ok" or (rel > peggiore)):
            quale, peggiore = f"{e} ({nome})", rel
        elif quale == "ok":
            peggiore = max(peggiore, rel)
    ris = (quale, peggiore)
    del cc, cg, xc, xg, rif_out, got_out, x, c
    torch.cuda.empty_cache()
    return ris


CANALI = [3, 16, 32, 64, 128]
KERNEL = [1, 3, 5]
SPAZIALI = {1: [128, 256], 2: [16, 32]}
LOTTI = [1, 4]

rotti, provati = [], 0
print("dim  cin cout   k    sp lotto   esito")
for dim in (1, 2):
    for cin, cout in itertools.product(CANALI, CANALI):
        for k in KERNEL:
            for sp in SPAZIALI[dim]:
                for lotto in LOTTI:
                    if cin * cout * sp ** dim * lotto > 40_000_000:
                        continue
                    provati += 1
                    try:
                        q, rel = caso(dim, cin, cout, k, sp, lotto)
                    except Exception as exc:
                        q, rel = f"ECCEZIONE {type(exc).__name__}", float("nan")
                    if q != "ok":
                        rotti.append((dim, cin, cout, k, sp, lotto, q, rel))
                        print(f"{dim}D {cin:5d} {cout:4d} {k:3d} {sp:5d} {lotto:5d}   {q}  rel={rel:.2e}", flush=True)

print(f"\nprovate {provati} configurazioni, sbagliate {len(rotti)}")
if not rotti:
    print("nessun difetto vivo in configurazione di produzione")

"""BatchNorm1d e LayerNorm (rete di prova, rete di prova) all'indietro: GPU fp32 e CPU fp32 contro fp64.

    python -u prova_norme_contro_double.py

un addestramento ha mostrato il gradiente di bn.bias 11x l'errore della CPU e di norm.weight 25x. Qui si misura l'errore RELATIVO di ciascuno contro il riferimento fp64: se la GPU sta
a ~1e-7..1e-6 relativo e' l'ordine delle somme, non un difetto.
"""
import torch
import torch.nn as nn

torch.manual_seed(0)


def prova(nome, fabbrica, forma, giri=3):
    peggiore = {"cpu": 0.0, "cuda": 0.0}
    for _ in range(giri):
        x = torch.randn(*forma, dtype=torch.float64) * 2 + 0.5
        g = torch.randn(*forma, dtype=torch.float64)
        rif = fabbrica().double()
        torch.nn.init.normal_(rif.weight, 1.0, 0.2)
        torch.nn.init.normal_(rif.bias, 0.0, 0.2)
        xr = x.clone().requires_grad_(True)
        (rif(xr) * g).sum().backward()
        for dove in ("cpu", "cuda"):
            m = fabbrica().to(dove)
            m.load_state_dict({k: v.float() for k, v in rif.state_dict().items()})
            xx = x.float().to(dove).requires_grad_(True)
            (m(xx) * g.float().to(dove)).sum().backward()
            for nome_p, a, b in (("dati", xx.grad, xr.grad), ("pesi", m.weight.grad, rif.weight.grad),
                                 ("bias", m.bias.grad, rif.bias.grad)):
                e = ((a.double().cpu() - b).abs().max() / b.abs().max()).item()
                peggiore[dove] = max(peggiore[dove], e)
                peggiore[(dove, nome_p)] = max(peggiore.get((dove, nome_p), 0.0), e)
    righe = []
    for p in ("dati", "pesi", "bias"):
        c, gg = peggiore[("cpu", p)], peggiore[("cuda", p)]
        righe.append(f"{p} CPU {c:.1e} GPU {gg:.1e} ({gg / max(c, 1e-30):.0f}x)")
    stato = "OK " if peggiore["cuda"] < 1e-5 else "ERR"
    print(f"  {stato} {nome:38s} " + " | ".join(righe), flush=True)


prova("BatchNorm1d(16), 128x16x96", lambda: nn.BatchNorm1d(16), (128, 16, 96))
prova("BatchNorm1d(64), 64x64x96", lambda: nn.BatchNorm1d(64), (64, 64, 96))
prova("BatchNorm1d(192), lotto 256", lambda: nn.BatchNorm1d(192), (256, 192))
prova("LayerNorm(32), 64x63x32", lambda: nn.LayerNorm(32), (64, 63, 32))
prova("LayerNorm(8), 64x63x8", lambda: nn.LayerNorm(8), (64, 63, 8))
prova("LayerNorm(64), 256x100x64", lambda: nn.LayerNorm(64), (256, 100, 64))
prova("LayerNorm(128), 32x90x128", lambda: nn.LayerNorm(128), (32, 90, 128))

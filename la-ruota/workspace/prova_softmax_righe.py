"""softmax / log_softmax sulla GPU contro CPU fp64: avanti e indietro, fp64/fp32/fp16, lunghezze 1-1100
e alcune grandi, ultima dimensione e dimensione interna. Copre la VEGA-PATCH 80.

    python -u prova_softmax_righe.py
"""
import torch

torch.manual_seed(0)
LUNG = list(range(1, 1101)) + [1500, 2047, 2048, 2049, 4097, 5000]
# fp16: l'arrotondamento dell'uscita vale ~1e-3 relativo (fino a 5e-3 all'indietro); il difetto della 80 vale 0,2-0,9
TOL = {torch.float64: 1e-12, torch.float32: 3e-6, torch.float16: 1e-2}
esiti = {}
for dt in (torch.float64, torch.float32, torch.float16):
    for nome in ("softmax", "log_softmax"):
        for verso in ("avanti", "indietro"):
            cattivi = []
            for n in LUNG:
                x = torch.randn(17, n, dtype=torch.float64) * 3     # 17 righe: righe dispari e disallineate
                g = torch.randn(17, n, dtype=torch.float64)
                xr = x.clone().requires_grad_(True)
                yr = getattr(xr, nome)(-1)
                xg = x.to(dt).cuda().requires_grad_(True)
                yg = getattr(xg, nome)(-1)
                if verso == "avanti":
                    a, b = yg.double().cpu(), yr.detach()
                else:
                    (yr * g).sum().backward()
                    (yg * g.to(dt).cuda()).sum().backward()
                    a, b = xg.grad.double().cpu(), xr.grad
                e = ((a - b).abs().max() / b.abs().max().clamp_min(1e-30)).item()
                if not e < TOL[dt]:
                    cattivi.append((n, e))
            esiti[(str(dt)[6:], nome, verso)] = cattivi
            print(f"  {'OK ' if not cattivi else 'ERR'} {str(dt)[6:]:8s} {nome:12s} {verso:9s} "
                  + ("tutte le lunghezze giuste" if not cattivi else
                     f"{len(cattivi)} sbagliate, da {cattivi[0][0]} a {cattivi[-1][0]}, max {max(e for _, e in cattivi):.1e}"),
                  flush=True)
# dimensione interna (percorso spaziale) e vista non contigua
x = torch.randn(5, 777, 3, dtype=torch.float64)
d = (x.cuda().softmax(1).cpu() - x.softmax(1)).abs().max().item()
v = torch.randn(9, 1600, dtype=torch.float64)[:, 1:778]
d2 = (v.cuda().softmax(-1).cpu() - v.softmax(-1)).abs().max().item()
ok3 = d < 1e-12 and d2 < 1e-12
esiti["altri"] = [] if ok3 else [("dim interna/vista", max(d, d2))]
print(f"  {'OK ' if ok3 else 'ERR'} fp64 dimensione interna 777 {d:.1e}, vista sfalsata 777 {d2:.1e}")
print(f"\n{sum(1 for v in esiti.values() if not v)} su {len(esiti)} giusti")

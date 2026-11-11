"""softmax/log_softmax sulla GPU contro CPU fp64, per lunghezza dell'ultima dimensione e dtype."""
import torch
torch.manual_seed(0)
cattivi = {}
for dt in (torch.float64, torch.float32):
    for n in list(range(1, 1100)) + [1024, 2048, 2049, 4096, 5000]:
        x = torch.randn(64, n, dtype=torch.float64) * 3
        r = x.softmax(-1)
        for nome, f in (("softmax", lambda y: y.softmax(-1)), ("log_softmax", lambda y: y.log_softmax(-1).exp())):
            g = f(x.to(dt).cuda()).double().cpu()
            e = (g - r).abs().max().item()
            if e > (1e-12 if dt == torch.float64 else 2e-6):
                cattivi.setdefault((str(dt), nome), []).append((n, e))
for k, l in cattivi.items():
    print(k, len(l), "lunghezze; prime:", [(n, f"{e:.1e}") for n, e in l[:12]], "ultime:", [n for n, _ in l[-5:]])
if not cattivi:
    print("nessun errore")

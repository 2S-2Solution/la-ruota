"""Algebra lineare sulla GPU contro la CPU, su dimensioni da 16 a 512.

    python -u battuta_linalg_dimensioni.py

Il censimento provava matrici piccole; eigh si e' scoperta sbagliata da n=64 in su (via
hipSOLVER syevj). Qui ogni operazione su piu' dimensioni, fp32 e fp64, singola e a lotti.
Si confrontano quantita' senza ambiguita' di segno: valori, ricostruzioni, soluzioni.
"""
import torch

torch.manual_seed(0)
DIM = (16, 33, 64, 100, 128, 200, 512)
esiti = {}


def spd(n, dt, lotto=()):
    A = torch.randn(*lotto, n, n, dtype=torch.float64)
    return (A @ A.mT + n * torch.eye(n, dtype=torch.float64)).to(dt)


def rel(a, b):
    a, b = a.double().cpu(), b.double().cpu()
    return ((a - b).abs().max() / b.abs().max().clamp_min(1e-30)).item()


PROVE = {
    "eigvalsh": lambda S: (torch.linalg.eigvalsh(S.cuda()), torch.linalg.eigvalsh(S)),
    "eigh ricostruzione": lambda S: ((lambda w, v: v @ torch.diag_embed(w) @ v.mT)(*torch.linalg.eigh(S.cuda())), S),
    "svdvals": lambda S: (torch.linalg.svdvals(S.cuda()), torch.linalg.svdvals(S)),
    "svd ricostruzione": lambda S: ((lambda u, s, vh: u @ torch.diag_embed(s) @ vh)(*torch.linalg.svd(S.cuda())), S),
    "qr ricostruzione": lambda S: ((lambda q, r: q @ r)(*torch.linalg.qr(S.cuda())), S),
    "lu ricostruzione": lambda S: ((lambda p, l, u: p @ l @ u)(*torch.linalg.lu(S.cuda())), S),
    "solve": lambda S: (torch.linalg.solve(S.cuda(), torch.ones(*S.shape[:-1], 1, dtype=S.dtype).cuda()),
                        torch.linalg.solve(S, torch.ones(*S.shape[:-1], 1, dtype=S.dtype))),
    "inv": lambda S: (torch.linalg.inv(S.cuda()), torch.linalg.inv(S)),
    "det (logdet)": lambda S: (torch.linalg.slogdet(S.cuda())[1], torch.linalg.slogdet(S)[1]),
    "cholesky": lambda S: (torch.linalg.cholesky(S.cuda()), torch.linalg.cholesky(S)),
    "pinv": lambda S: (torch.linalg.pinv(S.cuda()), torch.linalg.pinv(S)),
    "lstsq": lambda S: (torch.linalg.lstsq(S.cuda(), torch.ones(*S.shape[:-1], 1, dtype=S.dtype).cuda()).solution,
                        torch.linalg.lstsq(S, torch.ones(*S.shape[:-1], 1, dtype=S.dtype), driver="gelsd").solution),
    "householder (orgqr)": lambda S: ((lambda a, t: torch.linalg.householder_product(a, t))(*torch.geqrf(S.cuda())),
                                      (lambda a, t: torch.linalg.householder_product(a, t))(*torch.geqrf(S))),
}

for nome, f in PROVE.items():
    riga = []
    for dt, tol in ((torch.float32, 1e-3), (torch.float64, 1e-9)):
        for n in DIM:
            for lotto in ((), (3,)):
                try:
                    S = spd(n, dt, lotto)
                    g, c = f(S)
                    d = rel(g, c)
                    ok = d < tol
                except Exception as e:  # noqa: BLE001
                    d, ok = float("nan"), False
                    riga.append(f"ERR {str(dt)[6:]} n={n}{' lotto' if lotto else ''}: {type(e).__name__}")
                    continue
                if not ok:
                    riga.append(f"{str(dt)[6:]} n={n}{' lotto' if lotto else ''} {d:.0e}")
    esiti[nome] = riga
    stato = "OK " if not riga else "ERR"
    print(f"  {stato} {nome:22s} " + ("tutte le dimensioni giuste" if not riga else "sbagliate: " + ", ".join(riga[:8])
                                      + (f" ... (+{len(riga) - 8})" if len(riga) > 8 else "")), flush=True)
print(f"\n{sum(1 for r in esiti.values() if not r)} su {len(esiti)} operazioni giuste a tutte le dimensioni")

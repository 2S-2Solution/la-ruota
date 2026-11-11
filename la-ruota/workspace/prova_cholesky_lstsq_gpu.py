"""Verifica della VEGA-PATCH 67: cholesky, cholesky_solve, cholesky_inverse e lstsq su GPU.

    python prova_cholesky_lstsq_gpu.py

Ogni risultato GPU e' confrontato con la CPU (MKL) con uno scarto relativo a pavimento.
"""
import torch

torch.manual_seed(0)
esiti = []


def prova(nome, f):
    try:
        d = f()
        esiti.append(True)
        print(f"  OK    {nome:52s} {d}")
    except Exception as e:  # noqa: BLE001
        esiti.append(False)
        print(f"  ERR   {nome:52s} {type(e).__name__}: {str(e).splitlines()[0][:110]}")


def rel(x, y, tol):
    x, y = x.detach().cpu(), y.detach().cpu()
    d = ((x - y).abs().max() / y.abs().max().clamp_min(1e-30)).item()
    assert d < tol, f"scarto relativo {d:.2e} oltre {tol:.0e}"
    return f"scarto {d:.1e}"


def spd(*forma, dtype=torch.float32):
    n = forma[-1]
    a = torch.randn(*forma, n, dtype=dtype)
    return a @ a.mH + n * torch.eye(n, dtype=dtype)


TOL = {torch.float32: 1e-4, torch.float64: 1e-10, torch.complex64: 1e-4, torch.complex128: 1e-10}

for dt in (torch.float32, torch.float64, torch.complex64, torch.complex128):
    t = TOL[dt]
    nome_dt = str(dt)[6:]
    for forma in ((8,), (4, 8), (3, 2, 16), (512, 6)):
        A = spd(*forma, dtype=dt)
        for upper in (False, True):
            prova(f"cholesky {nome_dt} {tuple(A.shape)} upper={upper}",
                  lambda: rel(torch.linalg.cholesky(A.cuda(), upper=upper), torch.linalg.cholesky(A, upper=upper), t))

    A = spd(5, 12, dtype=dt)
    L = torch.linalg.cholesky(A)
    B = torch.randn(5, 12, 3, dtype=dt)
    prova(f"cholesky_solve {nome_dt} lotto 5",
          lambda: rel(torch.cholesky_solve(B.cuda(), L.cuda()), torch.cholesky_solve(B, L), t))
    U = torch.linalg.cholesky(A, upper=True)
    prova(f"cholesky_solve {nome_dt} upper",
          lambda: rel(torch.cholesky_solve(B.cuda(), U.cuda(), upper=True), torch.cholesky_solve(B, U, upper=True), t))
    prova(f"cholesky_inverse {nome_dt} singola",
          lambda: rel(torch.cholesky_inverse(L[0].cuda()), torch.cholesky_inverse(L[0]), t))
    prova(f"cholesky_inverse {nome_dt} lotto",
          lambda: rel(torch.cholesky_inverse(L.cuda()), torch.cholesky_inverse(L), t))

    M = torch.randn(4, 20, 6, dtype=dt)
    R = torch.randn(4, 20, 3, dtype=dt)
    prova(f"lstsq {nome_dt} sovradeterminato 20x6",
          lambda: rel(torch.linalg.lstsq(M.cuda(), R.cuda()).solution, torch.linalg.lstsq(M, R, driver="gelsd").solution, t * 10))
    Mu = torch.randn(3, 5, 9, dtype=dt)
    Ru = torch.randn(3, 5, 2, dtype=dt)
    prova(f"lstsq {nome_dt} sottodeterminato 5x9 (norma minima)",
          lambda: rel(torch.linalg.lstsq(Mu.cuda(), Ru.cuda()).solution, torch.linalg.lstsq(Mu, Ru, driver="gelsd").solution, t * 10))

# casi speciali
A = spd(6)
nonpd = A.clone()
nonpd[2, 2] = -100.0


def ex_non_pd():
    _, info = torch.linalg.cholesky_ex(nonpd.cuda())
    _, info_cpu = torch.linalg.cholesky_ex(nonpd)
    assert info.item() == info_cpu.item() and info.item() > 0, f"info GPU {info.item()} CPU {info_cpu.item()}"
    return f"info {info.item()} come la CPU"


prova("cholesky_ex su matrice non definita positiva", ex_non_pd)


def errore_non_pd():
    try:
        torch.linalg.cholesky(nonpd.cuda())
    except torch.linalg.LinAlgError as e:
        return f"LinAlgError: {str(e)[:50]}"
    raise AssertionError("nessun errore")


prova("cholesky su non definita positiva solleva errore", errore_non_pd)

# A a lotto 1, B a lotto 4: il lotto di A si allarga (una B con una dimensione in meno di
# A, per PyTorch, e' un lotto di vettori: non si prova qui)
Mb = torch.randn(1, 20, 6, dtype=torch.float64)
Rb = torch.randn(4, 20, 3, dtype=torch.float64)
prova("lstsq A lotto 1, B lotto 4 (broadcasting)",
      lambda: rel(torch.linalg.lstsq(Mb.cuda(), Rb.cuda()).solution, torch.linalg.lstsq(Mb, Rb, driver="gelsd").solution, 1e-9))
v = torch.randn(20, dtype=torch.float64)
prova("lstsq con B vettore",
      lambda: rel(torch.linalg.lstsq(Mb[0].cuda(), v.cuda().unsqueeze(-1)).solution,
                  torch.linalg.lstsq(Mb[0], v.unsqueeze(-1), driver="gelsd").solution, 1e-9))


def rango_non_pieno():
    # gels, sulla CPU come su rocSOLVER, segnala solo un elemento diagonale di R
    # ESATTAMENTE nullo: con una colonna nulla deve sollevare errore su entrambe
    D = torch.randn(10, 4, dtype=torch.float64)
    D[:, 3] = 0.0
    y = torch.randn(10, 2, dtype=torch.float64)
    for dev in ("cpu", "cuda"):
        try:
            torch.linalg.lstsq(D.to(dev), y.to(dev), driver="gels")
        except torch.linalg.LinAlgError:
            continue
        raise AssertionError(f"rango non pieno passato in silenzio su {dev}")
    return "LinAlgError su CPU e GPU, come gels"


prova("lstsq con colonna nulla solleva errore", rango_non_pieno)

# gradienti
Ag = spd(3, 7, dtype=torch.float64)
W = torch.randn(3, 7, 7, dtype=torch.float64)


def grad_chol(dev):
    x = Ag.to(dev).requires_grad_()
    (torch.linalg.cholesky(x) * W.to(dev)).sum().backward()
    return x.grad


prova("cholesky backward", lambda: rel(grad_chol("cuda"), grad_chol("cpu"), 1e-9))


def grad_lstsq(dev):
    x = torch.randn(15, 5, dtype=torch.float64, generator=torch.Generator().manual_seed(1)).to(dev).requires_grad_()
    y = torch.randn(15, 2, dtype=torch.float64, generator=torch.Generator().manual_seed(2)).to(dev)
    (torch.linalg.lstsq(x, y, driver="gels" if dev == "cuda" else "gelsd").solution ** 2).sum().backward()
    return x.grad


prova("lstsq backward", lambda: rel(grad_lstsq("cuda"), grad_lstsq("cpu"), 1e-8))

print(f"\n{sum(esiti)} su {len(esiti)} ok")

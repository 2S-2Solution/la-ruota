"""Verifica della patch 65: MKL sulla CPU e torch compatibile con numpy 1.x e 2.x.

    python verifica_mkl_numpy2.py

Va eseguito due volte: con numpy 1.26 (prima di aggiornare) e con numpy 2 (dopo).
"""
import time

import numpy as np
import torch

esiti = []


def prova(nome, f):
    try:
        dettaglio = f()
        esiti.append((nome, True))
        print(f"  OK    {nome}" + (f"  ({dettaglio})" if dettaglio else ""))
    except Exception as e:  # noqa: BLE001
        esiti.append((nome, False))
        print(f"  ERR   {nome}: {type(e).__name__}: {str(e).splitlines()[0][:150]}")


print(f"numpy {np.__version__} | torch {torch.__version__} | cuda {torch.cuda.is_available()}")
cfg = torch.__config__.show()
print("  BLAS:", [r.strip() for r in cfg.splitlines() if "BLAS_INFO" in r or "LAPACK_INFO" in r] or "?")
print("  MKL disponibile:", torch.backends.mkl.is_available(), "| thread:", torch.get_num_threads())


def gflops():
    a = torch.randn(4096, 4096)
    b = torch.randn(4096, 4096)
    a @ b
    t = time.perf_counter()
    for _ in range(5):
        a @ b
    s = (time.perf_counter() - t) / 5
    g = 2 * 4096 ** 3 / s / 1e9
    # Eigen faceva 1,4; MKL a 1 thread ~45; MKL su 16 core ben oltre 150
    assert g > 100, f"{g:.1f} GFLOPS: MKL e' a un solo thread (vedi VEGA-PATCH 66)"
    return f"{g:.0f} GFLOPS"


prova("matmul CPU fp32 4096", gflops)

g = torch.Generator().manual_seed(0)
A = torch.randn(64, 64, dtype=torch.float64, generator=g)
S = A @ A.T + 64 * torch.eye(64, dtype=torch.float64)
B = torch.randn(64, 3, dtype=torch.float64, generator=g)
An = A.numpy()


def vicino(x, y, tol=1e-8):
    d = float(np.max(np.abs(np.asarray(x) - np.asarray(y))))
    assert d <= tol, f"scarto {d:.2e}"
    return f"scarto {d:.1e}"


prova("CPU linalg.solve", lambda: vicino(torch.linalg.solve(A, B), np.linalg.solve(An, B.numpy())))
prova("CPU linalg.inv", lambda: vicino(torch.linalg.inv(A), np.linalg.inv(An)))
prova("CPU linalg.det", lambda: vicino(torch.linalg.det(A), np.linalg.det(An), 1e-6 * abs(np.linalg.det(An))))
prova("CPU cholesky", lambda: vicino(torch.linalg.cholesky(S), np.linalg.cholesky(S.numpy())))
prova("CPU qr (ricostruzione)", lambda: vicino((lambda q, r: q @ r)(*torch.linalg.qr(A)), An))
prova("CPU svd (valori)", lambda: vicino(torch.linalg.svdvals(A), np.linalg.svd(An, compute_uv=False)))
prova("CPU eigh", lambda: vicino(torch.linalg.eigvalsh(S), np.linalg.eigvalsh(S.numpy()), 1e-7))
prova("CPU eig (ricostruzione)", lambda: vicino(
    (lambda w, v: (v @ torch.diag(w) @ torch.linalg.inv(v)).real)(*torch.linalg.eig(A)), An, 1e-7))
prova("CPU lstsq", lambda: vicino(torch.linalg.lstsq(A, B).solution, np.linalg.lstsq(An, B.numpy(), rcond=None)[0]))
prova("CPU pinv", lambda: vicino(torch.linalg.pinv(A), np.linalg.pinv(An), 1e-7))

if torch.cuda.is_available():
    Ag = A.cuda()
    prova("GPU eig (passa dalla CPU)", lambda: vicino(
        (lambda w, v: (v @ torch.diag(w) @ torch.linalg.inv(v)).real)(*torch.linalg.eig(Ag)).cpu(), An, 1e-7))
    prova("GPU eigvals", lambda: vicino(
        np.sort_complex(torch.linalg.eigvals(Ag).cpu().numpy()), np.sort_complex(np.linalg.eigvals(An)), 1e-7))

# interoperabilita' con numpy: e' qui che numpy 2 rompeva torch
prova("torch.from_numpy", lambda: vicino(torch.from_numpy(An), An, 0))
prova("tensor.numpy()", lambda: vicino(A.numpy(), An, 0))
prova("torch.tensor(ndarray float32)", lambda: str(torch.tensor(np.ones(3, np.float32)).dtype))
prova("torch.as_tensor(scalare numpy)", lambda: str(torch.as_tensor(np.float64(2.5)).item()))
prova("indice con np.int64", lambda: str(torch.arange(10)[np.int64(3)].item()))
prova("dtype numpy bool/int8/fp16", lambda: ",".join(
    str(torch.from_numpy(np.zeros(2, d)).dtype) for d in (np.bool_, np.int8, np.float16)))
if torch.cuda.is_available():
    prova("ndarray -> GPU -> ndarray", lambda: vicino(torch.from_numpy(An).cuda().cpu().numpy(), An, 0))


def pandas_scipy():
    import pandas as pd
    import scipy.linalg
    df = pd.DataFrame({"x": np.arange(5.0)})
    t = torch.tensor(df["x"].to_numpy())
    return f"pandas {pd.__version__}, scipy {scipy.__version__}, somma {t.sum().item():.0f}, " \
           f"det scipy {scipy.linalg.det(An):.3g}"


prova("pandas/scipy accanto a torch", pandas_scipy)

ko = [n for n, e in esiti if not e]
print(f"\n{len(esiti) - len(ko)} su {len(esiti)} ok" + (f"; falliti: {', '.join(ko)}" if ko else ""))

"""Algebra lineare sulla GPU della ruota, con numpy come riferimento.

Il censimento_ruota.py non poteva giudicarla: la ruota e' compilata senza LAPACK,
quindi torch su CPU non fa solve/inv/qr/svd e il riferimento mancava. Qui il
riferimento e' numpy (che ha il suo LAPACK). Per le decomposizioni si confronta la
RICOSTRUZIONE, perche' i fattori sono definiti a meno di segni e rotazioni.
"""
import numpy as np
import torch

SOGLIA = 1e-3
torch.manual_seed(0)
rng = np.random.default_rng(0)
ESITI = []


def rel(rif, got):
    rif = np.asarray(rif, dtype=np.float64)
    got = np.asarray(got, dtype=np.float64)
    if rif.shape != got.shape:
        return float("inf")
    return float(np.abs(rif - got).max() / max(np.abs(rif).max(), 1e-6))


def prova(nome, fn):
    print(f"  .. {nome}", end="", flush=True)
    try:
        e = fn()
        stato = "ok" if e < SOGLIA else "SBAGLIATA"
        print(f"\r  {stato:9s} {nome:32s} scarto {e:.1e}", flush=True)
        ESITI.append((nome, stato, f"{e:.1e}"))
    except Exception as exc:
        msg = f"{type(exc).__name__}: {str(exc).splitlines()[0][:80]}"
        print(f"\r  ECCEZIONE {nome:32s} {msg}", flush=True)
        ESITI.append((nome, "ECCEZIONE", msg))


def g(a):
    return torch.from_numpy(np.ascontiguousarray(a, dtype=np.float32)).cuda()


A1 = rng.standard_normal((32, 32))
Ab = rng.standard_normal((8, 32, 32))
B1 = rng.standard_normal((32, 4))
Bb = rng.standard_normal((8, 32, 4))
M = rng.standard_normal((8, 32, 32))
SPD = M @ np.swapaxes(M, -1, -2) + 32 * np.eye(32)

print(f"{torch.cuda.get_device_name(0)}  torch {torch.__version__}  numpy {np.__version__}\n")
prova("solve", lambda: rel(np.linalg.solve(A1, B1), torch.linalg.solve(g(A1), g(B1)).cpu()))
prova("solve batch", lambda: rel(np.linalg.solve(Ab, Bb), torch.linalg.solve(g(Ab), g(Bb)).cpu()))
prova("inv", lambda: rel(np.linalg.inv(A1), torch.linalg.inv(g(A1)).cpu()))
prova("inv batch", lambda: rel(np.linalg.inv(Ab), torch.linalg.inv(g(Ab)).cpu()))
prova("det batch", lambda: rel(np.linalg.det(Ab), torch.linalg.det(g(Ab)).cpu()))
prova("slogdet batch", lambda: rel(np.linalg.slogdet(Ab)[1], torch.linalg.slogdet(g(Ab))[1].cpu()))
prova("cholesky batch", lambda: rel(np.linalg.cholesky(SPD), torch.linalg.cholesky(g(SPD)).cpu()))


def ricostr_qr(a):
    q, r = torch.linalg.qr(g(a))
    return rel(a, (q @ r).cpu())


prova("qr", lambda: ricostr_qr(A1))
prova("qr batch", lambda: ricostr_qr(Ab))


def ricostr_lu(a):
    lu, piv = torch.linalg.lu_factor(g(a))
    p, l, u = torch.lu_unpack(lu, piv)
    return rel(a, (p @ l @ u).cpu())


prova("lu_factor", lambda: ricostr_lu(A1))
prova("lu_factor batch", lambda: ricostr_lu(Ab))


def ricostr_svd(a):
    u, s, vh = torch.linalg.svd(g(a), full_matrices=False)
    return rel(a, (u @ torch.diag_embed(s) @ vh).cpu())


prova("svd", lambda: ricostr_svd(A1))
prova("svd batch", lambda: ricostr_svd(Ab))
prova("svdvals", lambda: rel(np.linalg.svd(Ab, compute_uv=False), torch.linalg.svdvals(g(Ab)).cpu()))


def ricostr_eigh(a):
    w, v = torch.linalg.eigh(g(a))
    return rel(a, (v @ torch.diag_embed(w) @ v.mT).cpu())


prova("eigh batch", lambda: ricostr_eigh(SPD))
prova("eigvalsh", lambda: rel(np.linalg.eigvalsh(SPD), torch.linalg.eigvalsh(g(SPD)).cpu()))
L = rng.standard_normal((64, 32))
R4 = rng.standard_normal((64, 4))
prova("lstsq", lambda: rel(np.linalg.lstsq(L, R4, rcond=None)[0], torch.linalg.lstsq(g(L), g(R4)).solution.cpu()))
P = rng.standard_normal((32, 16))
prova("pinv", lambda: rel(np.linalg.pinv(P), torch.linalg.pinv(g(P)).cpu()))
prova("matrix_norm nuc", lambda: rel(np.linalg.norm(Ab, "nuc", axis=(-2, -1)), torch.linalg.matrix_norm(g(Ab), "nuc").cpu()))


def grad_solve():
    a = g(A1).requires_grad_(True)
    b = g(B1).requires_grad_(True)
    torch.linalg.solve(a, b).sum().backward()
    # gradiente analitico: dL/db = A^-T 1,  dL/dA = -A^-T 1 x^T
    x = np.linalg.solve(A1, B1)
    gb = np.linalg.solve(A1.T, np.ones_like(B1))
    ga = -gb @ x.T
    return max(rel(gb, b.grad.cpu()), rel(ga, a.grad.cpu()))


prova("solve backward (analitico)", grad_solve)

print("\n" + "=" * 70)
ok = sum(1 for _, s, _ in ESITI if s == "ok")
print(f"  {ok} su {len(ESITI)} corrette sulla GPU")
for n, s, d in ESITI:
    if s != "ok":
        print(f"    {s:9s} {n:32s} {d}")

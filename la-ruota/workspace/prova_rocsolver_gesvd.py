"""rocSOLVER gesvd chiamato direttamente: giusto e ripetibile? Contro la svd attuale (hipSOLVER gesvdj).

    python -u prova_rocsolver_gesvd.py
"""
import ctypes
import os
import time

import torch

LIB = os.path.join(os.path.dirname(torch.__file__), "lib")
rocblas = ctypes.CDLL(os.path.join(LIB, "rocblas.dll"))
rocsolver = ctypes.CDLL(os.path.join(LIB, "rocsolver.dll"))
vp = ctypes.c_void_p
handle = vp()
assert rocblas.rocblas_create_handle(ctypes.byref(handle)) == 0
SINGULAR, OUTOFPLACE = 192, 201
I = ctypes.c_int
rocsolver.rocsolver_sgesvd.argtypes = [vp, I, I, I, I, vp, I, vp, vp, I, vp, I, vp, I, vp]


def gesvd(M):
    m, n = M.shape
    k = min(m, n)
    a = M.t().contiguous().t().clone()          # colonne (Fortran)
    a = M.t().contiguous()                      # memoria = M in colonne: a[j, i] = M[i, j]
    s = torch.zeros(k, device="cuda")
    u = torch.zeros(k, m, device="cuda")        # U m x k in colonne
    v = torch.zeros(n, k, device="cuda")        # V^T k x n in colonne
    e = torch.zeros(k, device="cuda")
    info = torch.zeros(1, dtype=torch.int32, device="cuda")
    rc = rocsolver.rocsolver_sgesvd(handle, SINGULAR, SINGULAR, m, n, vp(a.data_ptr()), m, vp(s.data_ptr()),
                                    vp(u.data_ptr()), m, vp(v.data_ptr()), k, vp(e.data_ptr()), OUTOFPLACE,
                                    vp(info.data_ptr()))
    torch.cuda.synchronize()
    assert rc == 0 and info.item() == 0, (rc, info.item())
    return u.t(), s, v.t()                      # U [m,k], S [k], Vh [k,n]


M = torch.randn(2000, 64, generator=torch.Generator().manual_seed(0))
Mg = M.cuda()
sc = torch.linalg.svdvals(M.double())
for nome, f in (("rocsolver gesvd", lambda: gesvd(Mg)),
                ("svd attuale (hipSOLVER)", lambda: torch.linalg.svd(Mg, full_matrices=False))):
    r = []
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(5):
        r.append(f())
    torch.cuda.synchronize()
    t = (time.perf_counter() - t0) / 5 * 1000
    u, s, vh = r[0]
    giusto = ((s.double().cpu() - sc).abs().max() / sc.abs().max()).item()
    ricostr = ((u @ torch.diag(s) @ vh).cpu() - M).abs().max().item() / M.abs().max().item()
    rip = max(max((x - y).abs().max().item() for x, y in zip(r[0], ri)) for ri in r[1:])
    print(f"  {nome:26s} valori vs CPU {giusto:.1e}  ricostruzione {ricostr:.1e}  ripetibilita' {rip:.1e}  {t:6.2f} ms")

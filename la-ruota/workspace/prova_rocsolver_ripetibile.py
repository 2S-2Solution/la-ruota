"""rocSOLVER syevd chiamato direttamente: si ripete uguale? E la svd di PyTorch sulla GPU?

    python -u prova_rocsolver_ripetibile.py
"""
import ctypes
import os

import torch

LIB = os.path.join(os.path.dirname(torch.__file__), "lib")
rocblas = ctypes.CDLL(os.path.join(LIB, "rocblas.dll"))
rocsolver = ctypes.CDLL(os.path.join(LIB, "rocsolver.dll"))
vp = ctypes.c_void_p
handle = vp()
assert rocblas.rocblas_create_handle(ctypes.byref(handle)) == 0
rocsolver.rocsolver_dsyevd.argtypes = [vp, ctypes.c_int, ctypes.c_int, ctypes.c_int, vp, ctypes.c_int, vp, vp, vp]

n = 128
A = torch.randn(n, n, generator=torch.Generator().manual_seed(0), dtype=torch.float64)
S = A @ A.t() + n * torch.eye(n, dtype=torch.float64)
uscite = []
for _ in range(5):
    a = S.clone().cuda()
    w = torch.zeros(n, dtype=torch.float64, device="cuda")
    e = torch.zeros(n, dtype=torch.float64, device="cuda")
    info = torch.zeros(1, dtype=torch.int32, device="cuda")
    rocsolver.rocsolver_dsyevd(handle, 211, 121, n, vp(a.data_ptr()), n, vp(w.data_ptr()), vp(e.data_ptr()),
                               vp(info.data_ptr()))
    torch.cuda.synchronize()
    uscite.append((w.cpu(), a.cpu()))
dw = max((u[0] - uscite[0][0]).abs().max().item() for u in uscite)
dv = max((u[1] - uscite[0][1]).abs().max().item() for u in uscite)
print(f"rocsolver_dsyevd, 5 corse: autovalori {dw:.1e}, autovettori {dv:.1e}")

M = torch.randn(2000, 64, generator=torch.Generator().manual_seed(0)).cuda()
for nome, f in (("svd GPU", lambda: torch.linalg.svd(M, full_matrices=False)),
                ("svdvals GPU", lambda: (torch.linalg.svdvals(M),))):
    r = [f() for _ in range(5)]
    d = max(max((x - y).abs().max().item() for x, y in zip(r[0], ri)) for ri in r[1:])
    print(f"{nome}, 5 corse: differenza {d:.1e}")

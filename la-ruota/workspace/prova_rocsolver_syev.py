"""rocSOLVER syevj e syevd chiamati DIRETTAMENTE (ctypes), senza PyTorch in mezzo.

    python -u prova_rocsolver_syev.py

eigh sulla GPU (che su ROCm usa sempre syevj via hipSOLVER) sbaglia da n=64 in su, in
silenzio. Qui si vede se il difetto e' gia' nella libreria: stesse matrici, rocsolver_dsyevj
e rocsolver_dsyevd, confronto con la CPU.
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
EVECT_ORIGINAL, FILL_UPPER, ESORT_ASC = 211, 121, 252
rocsolver.rocsolver_dsyevj.argtypes = [vp, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, vp, ctypes.c_int,
                                       ctypes.c_double, vp, ctypes.c_int, vp, vp, vp]
rocsolver.rocsolver_dsyevd.argtypes = [vp, ctypes.c_int, ctypes.c_int, ctypes.c_int, vp, ctypes.c_int, vp, vp, vp]

for n in (32, 48, 64, 100, 128, 256):
    A = torch.randn(n, n, generator=torch.Generator().manual_seed(n), dtype=torch.float64)
    S = A @ A.t() + n * torch.eye(n, dtype=torch.float64)
    wc = torch.linalg.eigvalsh(S)
    righe = []
    for nome in ("syevj", "syevd"):
        a = S.clone().cuda()
        w = torch.zeros(n, dtype=torch.float64, device="cuda")
        info = torch.zeros(1, dtype=torch.int32, device="cuda")
        torch.cuda.synchronize()
        if nome == "syevj":
            residuo = torch.zeros(1, dtype=torch.float64, device="cuda")
            passate = torch.zeros(1, dtype=torch.int32, device="cuda")
            rc = rocsolver.rocsolver_dsyevj(handle, ESORT_ASC, EVECT_ORIGINAL, FILL_UPPER, n, vp(a.data_ptr()), n,
                                            0.0, vp(residuo.data_ptr()), 100, vp(passate.data_ptr()),
                                            vp(w.data_ptr()), vp(info.data_ptr()))
            extra = f"passate {int(passate.item())}, residuo {residuo.item():.1e}"
        else:
            e = torch.zeros(n, dtype=torch.float64, device="cuda")
            rc = rocsolver.rocsolver_dsyevd(handle, EVECT_ORIGINAL, FILL_UPPER, n, vp(a.data_ptr()), n,
                                            vp(w.data_ptr()), vp(e.data_ptr()), vp(info.data_ptr()))
            extra = ""
        torch.cuda.synchronize()
        d = ((w.cpu() - wc).abs().max() / wc.abs().max()).item()
        righe.append(f"{nome} rc {rc} info {int(info.item())} scarto {d:.1e} {extra}")
    print(f"  n={n:4d}  " + "  |  ".join(righe), flush=True)

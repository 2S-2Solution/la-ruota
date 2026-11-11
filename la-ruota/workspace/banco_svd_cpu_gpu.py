"""svd: MKL sulla CPU (copie comprese) contro rocSOLVER gesvd sulla GPU, per decidere la soglia del ripiego.

    python -u banco_svd_cpu_gpu.py
"""
import time

import torch

import sys
EIGH = "--eigh" in sys.argv
FORME = [(64, 64), (128, 128), (512, 512), (1024, 1024), (2048, 2048), (8, 64, 64), (100, 32, 32)] if EIGH else \
    [(1000, 96), (2000, 20), (2000, 64), (5000, 96), (512, 512), (1024, 1024), (2048, 2048), (8, 64, 64),
     (100, 32, 32), (20000, 128)]


def tempo(f, giri=5):
    f()
    torch.cuda.synchronize()
    t = []
    for _ in range(giri):
        t0 = time.perf_counter()
        f()
        torch.cuda.synchronize()
        t.append(time.perf_counter() - t0)
    return sorted(t)[giri // 2] * 1000


for forma in FORME:
    for full in (False,):
        A = torch.randn(*forma).cuda()
        if EIGH:
            A = A @ A.mT
            gpu = tempo(lambda: torch.linalg.eigh(A))
            cpu = tempo(lambda: [t.cuda() for t in torch.linalg.eigh(A.cpu())])
        else:
            gpu = tempo(lambda: torch.linalg.svd(A, full_matrices=full))
            cpu = tempo(lambda: [t.cuda() for t in torch.linalg.svd(A.cpu(), full_matrices=full)])
        print(f"  {str(forma):18s} {"eigh" if EIGH else "svd"} GPU rocSOLVER {gpu:8.1f} ms   CPU MKL + copie {cpu:8.1f} ms   -> {gpu / cpu:5.1f}x",
              flush=True)

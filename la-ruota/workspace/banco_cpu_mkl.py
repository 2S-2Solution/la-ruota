"""Matmul CPU: torch (MKL) contro numpy (OpenBLAS), misurati nello stesso momento.

    python banco_cpu_mkl.py
"""
import os
import time

import numpy as np
import torch


def misura(f, n, ripeti=5):
    f()
    t = time.perf_counter()
    for _ in range(ripeti):
        f()
    return 2 * n ** 3 / ((time.perf_counter() - t) / ripeti) / 1e9


print(f"torch thread {torch.get_num_threads()} | MKL_NUM_THREADS={os.environ.get('MKL_NUM_THREADS')} "
      f"| MKL_ENABLE_INSTRUCTIONS={os.environ.get('MKL_ENABLE_INSTRUCTIONS')}")
for n in (1024, 2048, 4096):
    for dt, ndt in ((torch.float32, np.float32), (torch.float64, np.float64)):
        a, b = torch.randn(n, n, dtype=dt), torch.randn(n, n, dtype=dt)
        an, bn = a.numpy(), b.numpy()
        gt = misura(lambda: a @ b, n)
        gn = misura(lambda: an @ bn, n)
        print(f"  {n:5d} {str(dt)[6:]:8s} torch {gt:7.1f}  numpy {gn:7.1f} GFLOPS  ({gt / gn:.2f}x)")

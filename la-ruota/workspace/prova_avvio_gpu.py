"""Dove vanno i secondi del primo tensore sulla GPU (venv_build)? Una riga per fase.

    python -u prova_avvio_gpu.py
"""
import time

t0 = time.perf_counter()
import torch  # noqa: E402
t1 = time.perf_counter()
n = torch.cuda.device_count()
t2 = time.perf_counter()
torch.cuda.init()
t3 = time.perf_counter()
x = torch.zeros(1, device="cuda")
torch.cuda.synchronize()
t4 = time.perf_counter()
y = (x + 1).sum().item()
t5 = time.perf_counter()
a = torch.randn(256, 256, device="cuda")
(a @ a).sum().item()
t6 = time.perf_counter()
c = torch.nn.functional.conv2d(torch.randn(1, 8, 32, 32, device="cuda"), torch.randn(8, 8, 3, 3, device="cuda"))
c.sum().item()
t7 = time.perf_counter()
print(f"import torch {t1 - t0:.2f} s | device_count {t2 - t1:.2f} | cuda.init {t3 - t2:.2f} | "
      f"primo zeros {t4 - t3:.2f} | primo kernel elementwise {t5 - t4:.2f} | prima matmul (rocBLAS) {t6 - t5:.2f} | "
      f"prima conv (MIOpen) {t7 - t6:.2f} | totale {t7 - t0:.2f}")

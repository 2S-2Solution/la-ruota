"""Confronto di varianti di compilazione della GEMM (minimo su lanci intercalati).
    python varianti.py "-DUNROLL_K2=1" "-DUNROLL_K2=2" ..."""
import sys
import torch
sys.path.insert(0, r"C:\LaRuota_workspace\gemm_gfx906")
import gemm_gfx906 as gg
from banco import operandi, tempo

FORME = [(512, 9216, 2560, 1, 1, 1), (512, 2560, 9216, 1, 0, 3), (9216, 2560, 512, 0, 0, 1), (512, 2560, 9216, 1, 1, 6),
         (512, 4096, 2560, 1, 1, 4)]
varianti = sys.argv[1:] or ["-DUNROLL_K2=2"]
ris = {v: [] for v in varianti}
ops = [operandi(M, N, K, a, b) for M, N, K, a, b, _ in FORME]
for giro in range(3):
    for v in varianti:
        gg.OPZIONI[:] = v.split()
        for (M, N, K, _, _, s), (a, b) in zip(FORME, ops):
            t = tempo(lambda: gg.mm(a, b, split=s), n=15)[0]
            if giro == 0:
                ris[v].append(t)
            else:
                i = [f[:3] + (f[5],) for f in FORME].index((M, N, K, s))
                ris[v][i] = min(ris[v][i], t)
print("TFLOPS (minimo su 3 giri x 15 lanci)")
print(" " * 24 + "".join(f"{M}x{N}x{K} s{s}".rjust(22) for M, N, K, _, _, s in FORME))
for v in varianti:
    print(f"{v:24s}" + "".join(f"{2 * M * N * K / t / 1e9:22.1f}" for (M, N, K, *_), t in zip(FORME, ris[v])))

"""[VEGA-PATCH 48 1 ago] Sweep guidato dagli errori di link.

I sweep precedenti validavano i nomi contro i Register*.cpp (dispatch). Restano pero'
simboli INTERNI (host .cpp -> kernel .hip) che il dispatcher non nomina mai:
GeluCUDAKernelImpl, launch_poisson_cuda_kernel, launch_cummax_cuda_kernel, ...

Qui l'evidenza e' il log del linker: per ogni "undefined symbol" estraiamo il nome,
cerchiamo nel tree hip una definizione con la variante _hip/HIP e la rinominiamo alla
forma attesa. Nessuna euristica: si tocca solo cio' che il linker ha davvero chiesto.
"""
import os
import re
import sys

PROJ = r"C:\LaRuota_workspace\pytorch_src"
LOG = r"C:\LaRuota_workspace\build_log_20260801_resume.txt"
SRC = os.path.join(PROJ, "aten", "src", "ATen")

with open(LOG, encoding="utf-8", errors="ignore") as f:
    log = f.read()

# nomi non risolti, es. at::native::launch_poisson_cuda_kernel
wanted = set()
for m in re.finditer(r"undefined symbol:[^\n]*?at::native::([A-Za-z_][A-Za-z_0-9]*)", log):
    wanted.add(m.group(1))
print("simboli at::native mancanti:", len(wanted))

# per ognuno, la variante "hip" che potrebbe esistere nel tree
def hip_variants(name):
    out = set()
    if "_cuda" in name:
        out.add(name.replace("_cuda", "_hip"))
    if "CUDA" in name:
        out.add(name.replace("CUDA", "HIP"))
    return {v for v in out if v != name}

variant_to_target = {}
for w in wanted:
    for v in hip_variants(w):
        variant_to_target[v] = w

if not variant_to_target:
    print("nessuna variante da cercare")
    sys.exit(0)

pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in
                                       sorted(variant_to_target, key=len, reverse=True)) + r")\b")

total = 0
touched = []
for root, _dirs, files in os.walk(SRC):
    if "hip" not in root.replace(os.sep, "/").split("/"):
        continue
    for fn in files:
        if not fn.endswith((".hip", ".cuh", ".h", ".cpp")):
            continue
        p = os.path.join(root, fn)
        with open(p, encoding="utf-8", errors="surrogateescape") as f:
            src = f.read()
        new, n = pattern.subn(lambda m: variant_to_target[m.group(1)], src)
        if n:
            with open(p, "w", encoding="utf-8", errors="surrogateescape") as f:
                f.write(new)
            touched.append(f"{fn}({n})")
            total += n

print("sostituzioni:", total)
for t in touched:
    print("  ", t)

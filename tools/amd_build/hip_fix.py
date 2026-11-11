#!/usr/bin/env python3
# VEGA: ricrea i file core cancellati per errore, hipificandoli in una dir ISOLATA
# (cosi' non ci sono skip) e copiando i risultati al source. NON tocca altri file.
import os
import sys
import shutil

sys.path.append(r"C:/LaRuota_workspace/pytorch_src/torch/utils")
from hipify import hipify_python  # type: ignore[import]

proj = r"C:/LaRuota_workspace/pytorch_src"
work = r"C:/LaRuota_workspace/hip_fix"

# pulizia dir di lavoro
if os.path.isdir(work):
    shutil.rmtree(work, ignore_errors=True)

# copia i sorgenti cuda nella dir isolata (mantiene struttura relativa)
srcs = [
    "aten/src/ATen/cuda/CUDAGeneratorImpl.h",
    "aten/src/ATen/cuda/CUDAGeneratorImpl.cpp",
    "aten/src/ATen/native/cuda/DistributionTemplates.h",
]
for rel in srcs:
    s = os.path.join(proj, rel)
    d = os.path.join(work, rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy(s, d)

hipify_python.hipify(
    project_directory=work,
    output_directory=work,
    includes=[
        work + "/aten/src/ATen/cuda/*",
        work + "/aten/src/ATen/native/cuda/*",
    ],
    ignores=[],
    out_of_place_only=False,
    hip_clang_launch=True,
)

# copia i risultati hip generati al source
results = [
    "aten/src/ATen/hip/HIPGeneratorImpl.h",
    "aten/src/ATen/hip/HIPGeneratorImpl.cpp",
    "aten/src/ATen/native/hip/DistributionTemplates.h",
]
for rel in results:
    s = os.path.join(work, rel)
    d = os.path.join(proj, rel)
    if os.path.exists(s):
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(s, d)
        print("RIPRISTINATO: " + rel)
    else:
        print("MANCA output: " + rel)
print("=== HIP_FIX DONE ===")

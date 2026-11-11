#!/usr/bin/env python3
# VEGA: hipify VERO su output SEPARATO (temp), per rigenerare i file core cancellati per errore.
# Poi si copiano SOLO i file mancanti dal temp al source (i fix a mano non vengono toccati).
import os
import sys

sys.path.append(
    os.path.realpath(
        os.path.join(__file__, os.path.pardir, os.path.pardir, os.path.pardir, "torch", "utils")
    )
)
from hipify import hipify_python  # type: ignore[import]

proj = r"C:/LaRuota_workspace/pytorch_src"
out = r"C:/LaRuota_workspace/hipify_tmp"

includes = [
    proj + "/aten/src/ATen/cuda/*",
    proj + "/aten/src/ATen/cuda/detail/*",
    proj + "/aten/src/ATen/native/cuda/*",
]
ignores = [
    proj + "/aten/src/ATen/cuda/CUDAConfig.h",
]

hipify_python.hipify(
    project_directory=proj,
    output_directory=out,
    includes=includes,
    ignores=ignores,
    out_of_place_only=True,
    hip_clang_launch=True,
)
print("=== HIPIFY (output temp) DONE ===")

"""[VEGA-PATCH 47 28 lug] Hipify del sorgente ufunc GENERATO.

build/aten/src/ATen/UfuncCUDA_add.cu e' prodotto dal codegen ma nessuna regola lo
hipifica, quindi structured_ufunc_add_CUDA::impl resta undefined al link.
Lo copiamo temporaneamente in native/cuda/ (dove hipify sa mapparlo in
native/hip/UfuncCUDA_add.hip, raccolto dal glob "native/hip/*.hip") e poi
rimuoviamo la copia temporanea.
"""
import os
import sys

PROJ = r"C:\LaRuota_workspace\pytorch_src"
sys.path.append(os.path.join(PROJ, "torch", "utils"))

from hipify import hipify_python  # noqa: E402


def _norm(fn):
    def wrapper(rel_filepath, *a, **kw):
        return fn(rel_filepath.replace(os.sep, "/"), *a, **kw)
    return wrapper


for _n in ("is_pytorch_file", "is_out_of_place", "is_caffe2_gpu_file",
           "is_special_file", "is_cusparse_file"):
    if hasattr(hipify_python, _n):
        setattr(hipify_python, _n, _norm(getattr(hipify_python, _n)))

SRC = os.path.join(PROJ, "aten", "src")
tmp = os.path.join(SRC, "ATen", "native", "cuda", "UfuncCUDA_add.cu")

hipify_python.hipify(
    project_directory=PROJ,
    output_directory=PROJ,
    includes=[tmp],
    ignores=[],
    hip_clang_launch=True,
)

if os.path.exists(tmp):
    os.remove(tmp)
    print("copia temporanea rimossa")

out = os.path.join(SRC, "ATen", "native", "hip", "UfuncCUDA_add.hip")
print("generato:", os.path.exists(out), out)

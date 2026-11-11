"""[VEGA-PATCH 47 28 lug] Secondo giro di hipify per header/sorgenti emersi durante
la compilazione dei nuovi TU runtime (HIPHooks.cpp & co.)."""
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

WANTED = [
    "ATen/native/cuda/CuFFTPlanCache.h",
    "ATen/native/cuda/CuFFTUtils.h",
    # tunable/: inclusi da HIPBlas.cpp e Tunable.cpp
    "ATen/cuda/tunable/GemmCommon.h",
    "ATen/cuda/tunable/GemmHipblaslt.h",
    "ATen/cuda/tunable/GemmRocblas.h",
    "ATen/cuda/tunable/StreamTimer.h",
    "ATen/cuda/tunable/Tunable.h",
    "ATen/cuda/tunable/TunableGemm.h",
    "ATen/cuda/tunable/TunableOp.h",
]

includes = []
for rel in WANTED:
    p = os.path.join(SRC, rel.replace("/", os.sep))
    if os.path.exists(p):
        includes.append(p)
    else:
        print("SORGENTE ASSENTE (skip):", rel)

if includes:
    hipify_python.hipify(
        project_directory=PROJ,
        output_directory=PROJ,
        includes=includes,
        ignores=[],
        hip_clang_launch=True,
    )
print("DONE")

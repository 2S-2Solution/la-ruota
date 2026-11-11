"""[VEGA-PATCH 48 1 ago] Hipify IN PLACE di torch/ (torch_python & co.).

build_amd.py include "torch/*" e is_out_of_place() ritorna False per torch/: quei file
vanno hipificati sul posto. Col bug Windows dei separatori non e' mai successo, quindi
torch/csrc include ancora <cuda_runtime.h> e <ATen/native/cuda/Resize.h>, che in una
build ROCm non esistono.

Backup preventivo in C:\\LaRuota_workspace\\backup_torch_csrc_20260801.
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

includes = [os.path.join(PROJ, "torch", "*")]

# stessi ignores di build_amd.py per torch/
ignores = [
    os.path.join(PROJ, "torch", "lib", "tmp_install", "*"),
    os.path.join(PROJ, "torch", "include", "*"),
    os.path.join(PROJ, "torch", "utils", "hipify", "*"),
]

hipify_python.hipify(
    project_directory=PROJ,
    output_directory=PROJ,
    includes=includes,
    ignores=ignores,
    hip_clang_launch=True,
)
print("DONE")

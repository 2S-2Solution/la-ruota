"""[VEGA-PATCH 48 1 ago] Hipify dei .cpp HOST di native/cuda mai generati in native/hip.

Stessa classe di problema del runtime ATen/cuda/*.cpp: i file .cu erano stati
hipificati, i .cpp host no. Sono loro a definire i simboli rimasti undefined al link
(grid_sampler_*_cuda, resize_cuda_, cummax/cummin_helper_cuda, _fft_*_cufft,
cufft_*_plan_cache_*_impl, ...).

CMake li raccoglie da solo via file(GLOB native_hip_cpp "native/hip/*.cpp").
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
CUDA_DIR = os.path.join(SRC, "ATen", "native", "cuda")
HIP_DIR = os.path.join(SRC, "ATen", "native", "hip")

existing = {f for f in os.listdir(HIP_DIR) if f.endswith(".cpp")}
missing = [f for f in os.listdir(CUDA_DIR)
           if f.endswith(".cpp") and f not in existing]

print("da generare:", len(missing))
includes = [os.path.join(CUDA_DIR, f) for f in missing]

hipify_python.hipify(
    project_directory=PROJ,
    output_directory=PROJ,
    includes=includes,
    ignores=[],
    hip_clang_launch=True,
)

after = {f for f in os.listdir(HIP_DIR) if f.endswith(".cpp")}
print("native/hip .cpp totali ora:", len(after))

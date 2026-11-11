import os, sys
PROJ = r"C:\LaRuota_workspace\pytorch_src"
sys.path.append(os.path.join(PROJ, "torch", "utils"))
from hipify.hipify_python import matched_files_iter, is_pytorch_file, get_hip_file_path
SRC = os.path.join(PROJ, "aten", "src")
inc = [os.path.join(SRC, "ATen", "native", "cuda", "GridSampler.h")]
print("esiste:", os.path.exists(inc[0]))
rel = os.path.relpath(inc[0], PROJ)
print("rel:", rel)
print("is_pytorch_file:", is_pytorch_file(rel.replace(os.sep, "/")))
print("is_pytorch_file(sep nativo):", is_pytorch_file(rel))
print("hip path:", get_hip_file_path(rel))
got = list(matched_files_iter(PROJ, includes=inc, ignores=[]))
print("matched:", got)

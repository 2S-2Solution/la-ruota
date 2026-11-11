"""[VEGA-PATCH 48 1 ago] Ricognizione ESAUSTIVA: hipifica ogni sorgente/header sotto
una directory .../cuda/ che non abbia il corrispondente in .../hip/.

Finora li abbiamo scoperti a ondate (runtime ATen/cuda, native/cuda .cpp, native/cudnn,
tunable...). Questo script chiude il cerchio su TUTTO l'albero in un colpo solo, cosi'
non restano altre sorprese al link.
"""
import os
import sys

PROJ = r"C:\LaRuota_workspace\pytorch_src"
sys.path.append(os.path.join(PROJ, "torch", "utils"))

from hipify import hipify_python  # noqa: E402
from hipify.hipify_python import get_hip_file_path  # noqa: E402


def _norm(fn):
    def wrapper(rel_filepath, *a, **kw):
        return fn(rel_filepath.replace(os.sep, "/"), *a, **kw)
    return wrapper


for _n in ("is_pytorch_file", "is_out_of_place", "is_caffe2_gpu_file",
           "is_special_file", "is_cusparse_file"):
    if hasattr(hipify_python, _n):
        setattr(hipify_python, _n, _norm(getattr(hipify_python, _n)))

SRC = os.path.join(PROJ, "aten", "src")
EXT = (".cpp", ".h", ".cu", ".cuh")

missing = []
for root, dirs, files in os.walk(os.path.join(SRC, "ATen")):
    # QUALUNQUE file sotto un percorso che contiene una componente "cuda":
    # include anche le sottodirectory (cuda/linalg, cuda/detail, cuda/flash_attn...),
    # che la prima versione di questo script saltava perche' guardava solo
    # os.path.basename(root) == "cuda".
    parts = root.replace(os.sep, "/").split("/")
    if "cuda" not in parts:
        continue
    for fn in files:
        if not fn.endswith(EXT):
            continue
        abs_src = os.path.join(root, fn)
        rel = os.path.relpath(abs_src, PROJ)
        try:
            hip_rel = get_hip_file_path(rel.replace(os.sep, "/"))
        except AssertionError:
            continue
        abs_hip = os.path.join(PROJ, hip_rel.replace("/", os.sep))
        if not os.path.exists(abs_hip):
            missing.append(abs_src)

print("sorgenti senza corrispondente hip:", len(missing))
for m in missing[:60]:
    print("  ", os.path.relpath(m, SRC))

if missing:
    hipify_python.hipify(
        project_directory=PROJ,
        output_directory=PROJ,
        includes=missing,
        ignores=[],
        hip_clang_launch=True,
    )
print("DONE")

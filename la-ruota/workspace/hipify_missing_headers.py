"""[VEGA-PATCH 47 28 lug] Genera gli header hipificati mancanti eseguendo l'hipify
UFFICIALE (torch.utils.hipify) sui soli file cuda corrispondenti.

Raccomandazione del runbook: usare hipify vero invece di copie+replace a mano.
Scope ristretto ai file che NON esistono => nessun rischio di sovrascrivere i fix
manuali gia' presenti nel tree.
"""
import os
import sys

PROJ = r"C:\LaRuota_workspace\pytorch_src"
sys.path.append(os.path.join(PROJ, "torch", "utils"))

from hipify import hipify_python  # noqa: E402

# ---------------------------------------------------------------------------
# [VEGA-PATCH 47 28 lug] BUG WINDOWS DI HIPIFY — root cause del mistero annotato
# nel runbook 8 lug ("perche' hipify vero non rigenera questi file").
# is_pytorch_file/is_out_of_place/is_caffe2_gpu_file testano rel_filepath con
# startswith("aten/"), ma su Windows os.path.join produce "aten\src\...".
# Il test fallisce sempre => matched_files_iter scarta OGNI file del tree e
# hipify stampa "Successfully preprocessed" senza aver scritto nulla.
# Qui normalizziamo i separatori prima di delegare all'originale.
# ---------------------------------------------------------------------------
def _norm(fn):
    def wrapper(rel_filepath, *a, **kw):
        return fn(rel_filepath.replace(os.sep, "/"), *a, **kw)
    return wrapper


for _name in ("is_pytorch_file", "is_out_of_place", "is_caffe2_gpu_file", "is_special_file", "is_cusparse_file"):
    if hasattr(hipify_python, _name):
        setattr(hipify_python, _name, _norm(getattr(hipify_python, _name)))

SRC = os.path.join(PROJ, "aten", "src")

# header hip mancanti -> sorgente cuda da cui hipify li genera
MISSING = [
    "ATen/cuda/ATenCUDAGeneral.h",
    "ATen/native/cuda/Copy.h",
    "ATen/native/cuda/GridSampler.h",
    "ATen/native/cuda/IndexKernel.h",
    "ATen/native/cuda/ReduceOps.h",
    "ATen/native/cuda/Resize.h",
    "ATen/native/cuda/Sort.h",
    "ATen/native/cuda/Sorting.h",
    "ATen/native/cuda/SortStable.h",
    "ATen/native/cuda/TensorModeKernel.h",
    "ATen/native/cuda/TensorTopK.h",
    "ATen/native/sparse/cuda/ComputeSparseTile.h",
    "ATen/native/sparse/cuda/SparseBlasImpl.h",
    "ATen/native/sparse/cuda/SparseBlasLegacy.h",
    "ATen/native/sparse/cuda/SparseCUDABlas.h",
    "ATen/native/sparse/cuda/SparseSemiStructuredPack.h",
    "ATen/native/transformers/cuda/sdp_utils.h",
    # MHA: attention.hip/attention_backward.hip includono la versione hipificata
    "ATen/native/cudnn/MHA.h",
    "ATen/native/cudnn/MHA.cpp",
    # Sorgenti mancanti da torch_hip (undefined al link):
    # cudnn/* -> stub sotto !AT_CUDNN_ENABLED(), raccolti dal glob native/cudnn/hip/*.cpp
    "ATen/native/cudnn/AffineGridGenerator.cpp",
    "ATen/native/cudnn/BatchNorm.cpp",
    "ATen/native/cudnn/ConvPlaceholders.cpp",
    "ATen/native/cudnn/ConvShared.cpp",
    "ATen/native/cudnn/Conv_v7.cpp",
    "ATen/native/cudnn/Conv_v8.cpp",
    "ATen/native/cudnn/GridSampler.cpp",
    "ATen/native/cudnn/LossCTC.cpp",
    "ATen/native/cudnn/RNN.cpp",
    # Blas: addmv/bmm/baddbmm structured
    "ATen/native/cuda/Blas.cpp",
    # Runtime ATen/cuda/*.cpp mai hipificato: e' la causa dei simboli undefined
    # storici al link di torch_hip (device init, handle pool, allocator, blas...).
    # CMake li raccoglie via glob "hip/*.cpp" + "hip/detail/*.cpp" + "hip/tunable/*.cpp".
    "ATen/cuda/CachingHostAllocator.cpp",
    "ATen/cuda/CublasHandlePool.cpp",
    "ATen/cuda/CUDABlas.cpp",
    "ATen/cuda/CUDAContext.cpp",
    "ATen/cuda/CUDAGraph.cpp",
    "ATen/cuda/CUDASparseBlas.cpp",
    "ATen/cuda/CUDASparseDescriptors.cpp",
    "ATen/cuda/CuSparseHandlePool.cpp",
    "ATen/cuda/EmptyTensor.cpp",
    "ATen/cuda/Exceptions.cpp",
    "ATen/cuda/PeerToPeerAccess.cpp",
    "ATen/cuda/llvm_basic.cpp",
    "ATen/cuda/llvm_complex.cpp",
    # NB: l'header va rigenerato insieme al .cpp — la versione creata l'8 lug da
    # hip_fix2.py dichiarava "HIPHooks : at::HIPHooksInterface" mentre il .cpp
    # definisce at::cuda::detail::CUDAHooks + REGISTER_CUDA_HOOKS.
    "ATen/cuda/detail/CUDAHooks.h",
    "ATen/cuda/detail/CUDAHooks.cpp",
    "ATen/cuda/detail/LazyNVRTC.cpp",
    "ATen/cuda/tunable/StreamTimer.cpp",
    "ATen/cuda/tunable/Tunable.cpp",
]

includes = [os.path.join(SRC, p.replace("/", os.sep)) for p in MISSING]
for inc in includes:
    if not os.path.exists(inc):
        print("MANCA SORGENTE:", inc)
        sys.exit(1)

# NB: la root DEVE essere pytorch_src, non aten/src: matched_files_iter filtra con
# is_pytorch_file() che richiede il prefisso "aten/" nel path relativo.
hipify_python.hipify(
    project_directory=PROJ,
    output_directory=PROJ,
    includes=includes,
    ignores=[],
    hip_clang_launch=True,
)
print("HIPIFY DONE")

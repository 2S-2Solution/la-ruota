"""[VEGA-PATCH 48 1 ago] Catalogo COMPLETO delle correzioni namespace/macro, applicato
a TUTTE le directory hip dell'albero in un colpo solo.

Motivo: gli sweep parziali (una directory alla volta, una famiglia alla volta) hanno
fatto riemergere gli stessi difetti a ogni nuovo gruppo di file hipificati. Qui la
tabella e' unica e l'ambito e' l'intero tree, cosi' la categoria si chiude.

Regole ricavate empiricamente in questa sessione:
  at::hip::    -> funzioni/tipi dichiarati negli header ATen/hip (device props, blas,
                  sparse, allocator, thrust, data type)
  c10::hip::   -> stream, guard, device_count, current_device, caching allocator
  macro AT_/TORCH_ -> varianti HIP
"""
import os
import re

PROJ = r"C:\LaRuota_workspace\pytorch_src"
SRC = os.path.join(PROJ, "aten", "src", "ATen")

# sostituzioni letterali (non regex) applicate in ordine
RULES = [
    # --- at::cuda:: -> at::hip:: (dichiarati negli header ATen/hip) ---
    ("at::cuda::getCurrentDeviceProperties", "at::hip::getCurrentDeviceProperties"),
    ("at::cuda::getDeviceProperties", "at::hip::getDeviceProperties"),
    ("at::cuda::warp_size", "at::hip::warp_size"),
    ("at::cuda::ThrustAllocator", "at::hip::ThrustAllocator"),
    ("at::cuda::check_device", "at::hip::check_device"),
    ("at::cuda::getHIPDeviceAllocator", "at::hip::getHIPDeviceAllocator"),
    ("at::cuda::getCUDADeviceAllocator", "at::hip::getHIPDeviceAllocator"),
    ("at::cuda::getPinnedMemoryAllocator", "at::hip::getPinnedMemoryAllocator"),
    ("at::cuda::getCurrentCUDABlasHandle", "at::hip::getCurrentHIPBlasHandle"),
    ("at::cuda::getCurrentCUDABlasLtHandle", "at::hip::getCurrentHIPBlasLtHandle"),
    ("at::cuda::getCurrentHIPBlasHandle", "at::hip::getCurrentHIPBlasHandle"),
    ("at::cuda::getCurrentHIPBlasLtHandle", "at::hip::getCurrentHIPBlasLtHandle"),
    ("at::cuda::getCurrentCUDASparseHandle", "at::hip::getCurrentHIPSparseHandle"),
    ("at::cuda::getCurrentHIPSparseHandle", "at::hip::getCurrentHIPSparseHandle"),
    ("at::cuda::getCudaDataType", "at::hip::getCudaDataType"),
    ("at::cuda::ScalarTypeToCudaDataType", "at::hip::ScalarTypeToCudaDataType"),
    ("at::cuda::flush_icache", "at::hip::flush_icache"),
    ("at::cuda::getDeviceFromPtr", "at::hip::getDeviceFromPtr"),
    ("at::cuda::is_available", "at::hip::is_available"),
    ("at::cuda::blas::", "at::hip::blas::"),
    ("at::cuda::sparse::", "at::hip::sparse::"),
    ("at::cuda::solver::", "at::hip::solver::"),
    # --- c10::hip:: (stream / guard / device) ---
    ("at::hip::getCurrentHIPStreamMasqueradingAsCUDA",
     "c10::hip::getCurrentHIPStreamMasqueradingAsCUDA"),
    ("at::hip::getDefaultHIPStreamMasqueradingAsCUDA",
     "c10::hip::getDefaultHIPStreamMasqueradingAsCUDA"),
    ("at::hip::OptionalHIPGuard", "c10::hip::OptionalHIPGuard"),
    ("at::hip::device_count()", "c10::hip::device_count()"),
    ("at::cuda::device_count()", "c10::hip::device_count()"),
    # --- macro ---
    ("TORCH_CUDASPARSE_CHECK", "TORCH_HIPSPARSE_CHECK"),
    ("TORCH_CUDABLAS_CHECK", "TORCH_HIPBLAS_CHECK"),
    ("AT_CUDA_DRIVER_CHECK", "AT_HIP_DRIVER_CHECK"),
    ("AT_CUDA_NVRTC_CHECK", "AT_HIP_NVRTC_CHECK"),
    ("AT_CUDA_CHECK", "AT_HIP_CHECK"),
    ("TORCH_CUDA_CPP_API", "TORCH_HIP_CPP_API"),
    ("TORCH_CUDA_CU_API", "TORCH_HIP_CU_API"),
]

# non toccare: definizioni di macro (rischio auto-referenza) e il file Export.h
SKIP_LINE = re.compile(r"^\s*#\s*define\s+(TORCH_HIP|AT_HIP)")

total = 0
touched = []
for root, _dirs, files in os.walk(SRC):
    parts = root.replace(os.sep, "/").split("/")
    if "hip" not in parts:
        continue
    for fn in files:
        if not fn.endswith((".cpp", ".hip", ".h", ".cuh")):
            continue
        p = os.path.join(root, fn)
        with open(p, encoding="utf-8", errors="surrogateescape") as f:
            lines = f.readlines()
        changed = 0
        out = []
        for line in lines:
            if SKIP_LINE.match(line):
                out.append(line)
                continue
            new = line
            for a, b in RULES:
                if a in new:
                    new = new.replace(a, b)
            # ripulisci eventuali doppie qualificazioni
            new = new.replace("c10::hip::c10::hip::", "c10::hip::")
            new = new.replace("at::hip::at::hip::", "at::hip::")
            if new != line:
                changed += 1
            out.append(new)
        if changed:
            with open(p, "w", encoding="utf-8", errors="surrogateescape") as f:
                f.writelines(out)
            touched.append(f"{fn}({changed})")
            total += changed

print("righe modificate:", total, "in", len(touched), "file")
for t in touched:
    print("  ", t)

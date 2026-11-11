#pragma once
#include <c10/macros/Export.h>
#include <cstdint>

// [VEGA-PATCH 44 T08:25 25 giu] TORCH_HIP_CU_API undefined macro fix.
// Nota:00 25 giu: drop "CU" prefix → TORCH_HIP_API
// è il macro reale per HIP target. Fallback a TORCH_API se nemmeno quello esiste.
#ifndef TORCH_HIP_CU_API
  #ifdef TORCH_HIP_API
    #define TORCH_HIP_CU_API TORCH_HIP_API
  #else
    #define TORCH_HIP_CU_API TORCH_API
  #endif
#endif

namespace at::hip {

// enqueues a kernel that spins for the specified number of cycles
TORCH_HIP_CU_API void sleep(int64_t cycles);

// flushes instruction cache for ROCm; no-op for HIP
TORCH_HIP_CU_API void flush_icache();

}  // namespace at::hip

#pragma once
#include <ATen/cuda/CUDAConfig.h>
#include <string>

// AT_USE_JITERATOR(), controls whether we jit some elementwise kernels
// [VEGA-PATCH 46l 6 lug] Disabilitato su ROCm: gfx906 NON supporta il jiterator (JIT runtime
// via hiprtc/torch.compile). I kernel elementwise usano il path template diretto. Elimina la
// dipendenza da jit_utils.h (namespace/simboli JIT mal-hipificati).
#if defined(USE_ROCM)
#define AT_USE_JITERATOR() false
#else
#define AT_USE_JITERATOR() true
#endif
#define jiterator_stringify(...) std::string(#__VA_ARGS__);

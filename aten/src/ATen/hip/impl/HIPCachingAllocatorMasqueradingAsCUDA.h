#pragma once
// [VEGA-PATCH 48 1 ago] Guardia classica OLTRE a #pragma once: la junction
// build/aten/src/ATen/hip -> aten/src/ATen/hip espone questo file con due percorsi
// assoluti diversi, e #pragma once non deduplica (redefinition dei tipi guard).
#ifndef ATEN_HIP_IMPL_HIPCACHINGALLOC_MASQ_H_
#define ATEN_HIP_IMPL_HIPCACHINGALLOC_MASQ_H_
#include <c10/hip/HIPCachingAllocator.h>
#include <ATen/hip/impl/HIPAllocatorMasqueradingAsCUDA.h>
#include <ATen/hip/impl/HIPStreamMasqueradingAsCUDA.h>

namespace c10 {
// forward declaration
class DataPtr;
namespace hip {
namespace HIPCachingAllocatorMasqueradingAsCUDA {

C10_HIP_API Allocator* get();
C10_HIP_API void recordStreamMasqueradingAsCUDA(const DataPtr& ptr, HIPStreamMasqueradingAsCUDA stream);

} // namespace HIPCachingAllocatorMasqueradingAsCUDA
} // namespace hip
} // namespace c10

#endif  // ATEN_HIP_IMPL_HIPCACHINGALLOC_MASQ_H_

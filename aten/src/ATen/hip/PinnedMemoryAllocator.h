#pragma once

#include <c10/core/Allocator.h>
#include <ATen/hip/CachingHostAllocator.h>

namespace at::hip {

inline TORCH_HIP_CPP_API at::Allocator* getPinnedMemoryAllocator() {
  return getCachingHostAllocator();
}
} // namespace at::hip

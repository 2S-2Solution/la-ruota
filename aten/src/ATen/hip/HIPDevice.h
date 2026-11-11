#pragma once

#include <ATen/hip/Exceptions.h>

#include <hip/hip_runtime.h>
#include <hip/hip_runtime.h>

namespace at::hip {

inline Device getDeviceFromPtr(void* ptr) {
  hipPointerAttribute_t attr{};

  AT_HIP_CHECK(hipPointerGetAttributes(&attr, ptr));

#if !defined(USE_ROCM)
  TORCH_CHECK(attr.type != hipMemoryTypeUnregistered,
    "The specified pointer resides on host memory and is not registered with any HIP device.");
#endif

  // [VEGA-PATCH 52 1 ago] CUDA, non HIP: vedi nota in HIPUtils.h — i tensori
  // di questa build portano DeviceType::CUDA.
  return {c10::DeviceType::CUDA, static_cast<DeviceIndex>(attr.device)};
}

} // namespace at::hip

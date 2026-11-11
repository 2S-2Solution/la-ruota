#pragma once
#include <ATen/core/TensorBase.h>

// [VEGA-PATCH 47 31 lug] Basta includere Export.h: definisce TORCH_HIP_CPP_API in
// base a TORCH_HIP_BUILD_MAIN_LIB. Il vecchio blocco (VEGA-PATCH 29, 22 giu) era
// diventato un #define auto-referenziale dopo il rename delle macro di export.
#include <c10/macros/Export.h>

namespace at::detail {

TORCH_HIP_CPP_API TensorBase empty_cuda(
    IntArrayRef size,
    ScalarType dtype,
    std::optional<Device> device_opt,
    std::optional<c10::MemoryFormat> memory_format_opt);

TORCH_HIP_CPP_API TensorBase empty_cuda(
    IntArrayRef size,
    std::optional<ScalarType> dtype_opt,
    std::optional<Layout> layout_opt,
    std::optional<Device> device_opt,
    std::optional<bool> pin_memory_opt,
    std::optional<c10::MemoryFormat> memory_format_opt);

TORCH_HIP_CPP_API TensorBase empty_cuda(
    IntArrayRef size,
    const TensorOptions &options);

TORCH_HIP_CPP_API TensorBase empty_strided_cuda(
    IntArrayRef size,
    IntArrayRef stride,
    ScalarType dtype,
    std::optional<Device> device_opt);

TORCH_HIP_CPP_API TensorBase empty_strided_cuda(
    IntArrayRef size,
    IntArrayRef stride,
    std::optional<ScalarType> dtype_opt,
    std::optional<Layout> layout_opt,
    std::optional<Device> device_opt,
    std::optional<bool> pin_memory_opt);

TORCH_HIP_CPP_API TensorBase empty_strided_cuda(
    IntArrayRef size,
    IntArrayRef stride,
    const TensorOptions &options);

/* [VEGA-PATCH 47 28 lug] Rimosso il blocco di alias VEGA-PATCH 23 (22 giu):
   serviva quando le definizioni si chiamavano empty_hip/empty_strided_hip e il
   codegen RegisterCUDA.cpp cercava i nomi _cuda. Ora le definizioni SONO _cuda
   (sweep dispatch names), quindi quegli inline sarebbero ricorsivi + duplicati. */

}  // namespace at::detail

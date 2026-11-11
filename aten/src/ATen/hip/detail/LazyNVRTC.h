#pragma once
// [VEGA-PATCH 47 28 lug] namespace at::cuda (non at::hip): LazyNVRTC.cpp definisce
// at::cuda::detail::lazyNVRTC e l'interfaccia hooks usa at::cuda::NVRTC.
// L'include di HIPHooksInterface.h era un residuo dell'hipify approssimativo.
#include <ATen/detail/CUDAHooksInterface.h>
namespace at::cuda {
// Forward-declares at::cuda::NVRTC
struct NVRTC;

namespace detail {
extern NVRTC lazyNVRTC;
} // namespace detail

}  // namespace at::cuda

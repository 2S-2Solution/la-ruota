#pragma once

#include <ATen/hip/ATenHIPGeneral.h>
#include <hip/hip_runtime.h>
// [VEGA-PATCH 47 28 lug] ROCm installa l'header come hip/hiprtc.h
#include <hip/hiprtc.h>

namespace at { namespace cuda {


// NOTE [ USE OF HIPRTC AND DRIVER API ]
//
// ATen does not directly link to either libhiprtc or libcuda because they
// require libcuda to be installed, yet we want our GPU build to work on CPU
// machines as long as CUDA is not initialized.
//
// Normal CUDA code in torch uses the cuda runtime libraries which can be
// installed even if the driver is not installed, but sometimes we specifically
// need to use the driver API (e.g., to load JIT compiled code).
// To accomplish this, we lazily link libcaffe2_hiprtc which provides a struct
// at::hip::HIPRTC that contains function pointers to all of the apis we need.
//
// IT IS AN ERROR TO TRY TO CALL ANY hiprtc* or cu* FUNCTION DIRECTLY.
// INSTEAD USE, e.g.
//   detail::getCUDAHooks().hiprtc().cuLoadModule(...)
// or
//   globalContext().getHIPRTC().cuLoadModule(...)
//
// If a function is missing add it to the list in ATen/hip/hiprtc_stub/ATenHIPRTC.h
// and edit ATen/hip/detail/LazyHIPRTC.cpp accordingly (e.g., via one of the stub
// macros).

#if !defined(USE_ROCM)

#define AT_FORALL_HIPRTC_BASE(_)                  \
  _(hiprtcVersion)                                \
  _(hiprtcAddNameExpression)                      \
  _(hiprtcCreateProgram)                          \
  _(hiprtcDestroyProgram)                         \
  _(hiprtcGetPTXSize)                             \
  _(hiprtcGetPTX)                                 \
  _(hiprtcCompileProgram)                         \
  _(hiprtcGetErrorString)                         \
  _(hiprtcGetProgramLogSize)                      \
  _(hiprtcGetProgramLog)                          \
  _(hiprtcGetLoweredName)                         \
  _(hipModuleLoadData)                            \
  _(hipModuleLoadDataEx)                          \
  _(hipModuleGetFunction)                         \
  _(cuOccupancyMaxActiveBlocksPerMultiprocessor) \
  _(cuGetErrorString)                            \
  _(hipModuleLaunchKernel)                              \
  _(cuLaunchCooperativeKernel)                   \
  _(hipCtxGetCurrent)                             \
  _(cuCtxSetCurrent)                             \
  _(hipModuleUnload)                              \
  _(cuDevicePrimaryCtxGetState)                  \
  _(cuDevicePrimaryCtxRetain)                    \
  _(hiprtcLinkCreate)                                \
  _(hiprtcLinkAddData)                               \
  _(hiprtcLinkComplete)                              \
  _(hipFuncSetAttribute)                          \
  _(cuFuncGetAttribute)                          \

#if defined(CUDA_VERSION) && CUDA_VERSION >= 12000
#define AT_FORALL_HIPRTC_EXTENDED(_)              \
  AT_FORALL_HIPRTC_BASE(_)                        \
  _(cuTensorMapEncodeTiled)
#else
#define AT_FORALL_HIPRTC_EXTENDED(_)              \
  AT_FORALL_HIPRTC_BASE(_)
#endif

#if defined(CUDA_VERSION) && CUDA_VERSION >= 11010
#define AT_FORALL_HIPRTC(_) \
  AT_FORALL_HIPRTC_EXTENDED(_)  \
  _(hiprtcGetCUBINSize)     \
  _(hiprtcGetCUBIN)
#else
#define AT_FORALL_HIPRTC(_) \
  AT_FORALL_HIPRTC_EXTENDED(_)
#endif

#else

// NOTE [ ATen HIPRTC Stub and HIP ]
//
// ATen's HIPRTC stub library, caffe2_hiprtc, provides dynamic loading of both
// HIPRTC and driver APIs. While the former is not yet supported for HIP, the
// later is supported and needed (e.g., in CUDAHooks::getDeviceWithPrimaryContext()
// used by tensor.pin_memory()).
//
// The macro below strips out certain unsupported operations on HIP from the full
// list above.
//
// HIP doesn't have
//   cuGetErrorString  (maps to non-functional hipGetErrorString___)
//
// HIP from ROCm 3.5 on renamed hipOccupancyMaxActiveBlocksPerMultiprocessor
// to hipModuleOccupancyMaxActiveBlocksPerMultiprocessor.
#if TORCH_HIP_VERSION < 305
#define HIPOCCUPANCYMAXACTIVEBLOCKSPERMULTIPROCESSOR hipOccupancyMaxActiveBlocksPerMultiprocessor
#else
// [VEGA-PATCH 47 28 lug] era cuOccupancyMaxActiveBlocksPerMultiprocessor: gli alias
// driver cu* sono visibili solo in compilazione HIP (-x hip), non nei TU host come
// HIPHooks.cpp. Il nome HIP reale e' quello del commento qui sopra.
#define HIPOCCUPANCYMAXACTIVEBLOCKSPERMULTIPROCESSOR hipModuleOccupancyMaxActiveBlocksPerMultiprocessor
#endif

#define AT_FORALL_HIPRTC(_)                        \
  _(hiprtcVersion)                                 \
  _(hiprtcCreateProgram)                           \
  _(hiprtcAddNameExpression)                       \
  _(hiprtcDestroyProgram)                          \
  /* [VEGA-PATCH 47 28 lug] ROCm 5.7: hiprtcGetPTX{,Size} non esistono, si
     chiamano hiprtcGetCode{,Size}; cuDevicePrimaryCtxGetState non e' esposto
     dal runtime HIP Windows -> equivalente hipDevicePrimaryCtxGetState. */ \
  _(hiprtcGetCodeSize)                             \
  _(hiprtcGetCode)                                 \
  _(hipModuleLoadData)                             \
  _(hipModuleGetFunction)                          \
  _(HIPOCCUPANCYMAXACTIVEBLOCKSPERMULTIPROCESSOR) \
  _(hiprtcGetErrorString)                          \
  _(hiprtcGetProgramLogSize)                       \
  _(hiprtcGetProgramLog)                           \
  _(hipModuleLaunchKernel)                               \
  _(hiprtcCompileProgram)                          \
  _(hipCtxGetCurrent)                              \
  _(hiprtcGetLoweredName)                          \
  _(hipModuleUnload)                               \
  _(hipDevicePrimaryCtxGetState)

#endif

// [VEGA-PATCH 47 28 lug] La struct DEVE chiamarsi NVRTC: at::CUDAHooksInterface la
// forward-dichiara come at::cuda::NVRTC e nvrtc() ritorna const at::cuda::NVRTC&.
// hipify l'aveva rinominata in HIPRTC, che restava un tipo distinto e incompleto.
// Manteniamo HIPRTC come alias per i call site interni gia' hipificati.
extern "C" typedef struct NVRTC {
#define CREATE_MEMBER(name) decltype(&name) name;
  AT_FORALL_HIPRTC(CREATE_MEMBER)
#undef CREATE_MEMBER
} NVRTC;

using HIPRTC = NVRTC;

extern "C" TORCH_HIP_CPP_API NVRTC* load_hiprtc();
}} // at::cuda

// VEGA-PATCH 35 T00:20: Compat layer cuda* → hip* per torch/csrc/cuda/*.cpp non hipify-d
// Force-include via /FI in torch_hip target quando USE_ROCM=1.
// Mappa tipi + funzioni CUDA → HIP equivalenti (ROCm 6.4).
#pragma once

#ifdef USE_ROCM
#include <hip/hip_runtime.h>
#include <hip/hip_runtime_api.h>
#include <hipblas/hipblas.h>
#include <hipsparse/hipsparse.h>
#include <hipsolver/hipsolver.h>

// [VEGA-PATCH 46h T18:30 5 lug] hipStreamLegacy: define hip 6.x usato da rocprim 6.4, assente in
// hip 5.7 (che ha solo hipStreamPerThread). Solo costante header, nessun runtime richiesto.
#ifndef hipStreamLegacy
#define hipStreamLegacy ((hipStream_t)1)
#endif

// [VEGA-PATCH 46m 6 lug] CONSTEXPR_EXCEPT_WIN_HIP: hipify di CONSTEXPR_EXCEPT_WIN_CUDA (definito
// in c10/macros/Macros.h, NON hipified). Alias lazy: eredita il valore corretto per la piattaforma.
#ifndef CONSTEXPR_EXCEPT_WIN_HIP
#define CONSTEXPR_EXCEPT_WIN_HIP CONSTEXPR_EXCEPT_WIN_CUDA
#endif
#ifndef C10_HOST_CONSTEXPR_EXCEPT_WIN_HIP
#define C10_HOST_CONSTEXPR_EXCEPT_WIN_HIP C10_HOST_CONSTEXPR_EXCEPT_WIN_CUDA
#endif

// === TYPE ALIASES ===
#ifndef cudaError_t
#define cudaError_t hipError_t
#endif
#ifndef cudaStream_t
#define cudaStream_t hipStream_t
#endif
#ifndef cudaEvent_t
#define cudaEvent_t hipEvent_t
#endif
#ifndef cudaDeviceProp
#define cudaDeviceProp hipDeviceProp_t
#endif
#ifndef cudaMemcpyKind
#define cudaMemcpyKind hipMemcpyKind
#endif
#ifndef cudaStreamCaptureMode
#define cudaStreamCaptureMode hipStreamCaptureMode
#endif
#ifndef cudaStreamCaptureStatus
#define cudaStreamCaptureStatus hipStreamCaptureStatus
#endif
#ifndef cudaGraph_t
#define cudaGraph_t hipGraph_t
#endif
#ifndef cudaGraphExec_t
#define cudaGraphExec_t hipGraphExec_t
#endif
#ifndef cudaIpcMemHandle_t
#define cudaIpcMemHandle_t hipIpcMemHandle_t
#endif
#ifndef cudaIpcEventHandle_t
#define cudaIpcEventHandle_t hipIpcEventHandle_t
#endif
#ifndef cublasLtHandle_t
#define cublasLtHandle_t hipblasHandle_t
#endif
#ifndef cusolverDnHandle_t
#define cusolverDnHandle_t hipsolverHandle_t
#endif
#ifndef cublasHandle_t
#define cublasHandle_t hipblasHandle_t
#endif
#ifndef cusparseHandle_t
#define cusparseHandle_t hipsparseHandle_t
#endif
#ifndef cublasStatus_t
#define cublasStatus_t hipblasStatus_t
#endif
#ifndef cusparseStatus_t
#define cusparseStatus_t hipsparseStatus_t
#endif

// === FUNCTION ALIASES (selected commonly used) ===
#define cudaStreamSynchronize hipStreamSynchronize
#define cudaStreamWaitEvent hipStreamWaitEvent
#define cudaThreadExchangeStreamCaptureMode hipThreadExchangeStreamCaptureMode
#define cudaGetLastError hipGetLastError
#define cudaPeekAtLastError hipPeekAtLastError
#define cudaGetErrorString hipGetErrorString
#define cudaSuccess hipSuccess
#define cudaErrorNotReady hipErrorNotReady
#define cudaMemcpyHostToDevice hipMemcpyHostToDevice
#define cudaMemcpyDeviceToHost hipMemcpyDeviceToHost
#define cudaMemcpyDeviceToDevice hipMemcpyDeviceToDevice
#define cudaMemcpyDefault hipMemcpyDefault
#define cudaStreamDefault hipStreamDefault
#define cudaStreamNonBlocking hipStreamNonBlocking
#define cudaEventDefault hipEventDefault
#define cudaEventDisableTiming hipEventDisableTiming
#define cudaEventBlockingSync hipEventBlockingSync
#define cudaStreamCaptureStatusNone hipStreamCaptureStatusNone
#define cudaStreamCaptureStatusActive hipStreamCaptureStatusActive
#define cudaStreamCaptureStatusInvalidated hipStreamCaptureStatusInvalidated

// VEGA-PATCH 38 T01:55: extended function aliases for c10/cuda/CUDAStream.h + CUDAGuardImpl.h
#define cudaStreamIsCapturing hipStreamIsCapturing
#define cudaStreamQuery hipStreamQuery
#define cudaStreamGetPriority hipStreamGetPriority
#define cudaDeviceGetStreamPriorityRange hipDeviceGetStreamPriorityRange
#define cudaEventCreateWithFlags hipEventCreateWithFlags
#define cudaEventDestroy hipEventDestroy
#define cudaEventRecord hipEventRecord
#define cudaEventQuery hipEventQuery
#define cudaEventSynchronize hipEventSynchronize
#define cudaEventElapsedTime hipEventElapsedTime
#define cudaDeviceEnablePeerAccess hipDeviceEnablePeerAccess
#define cudaStreamCreateWithPriority hipStreamCreateWithPriority
#define cudaStreamDestroy hipStreamDestroy
#define cudaSetDevice hipSetDevice
#define cudaGetDevice hipGetDevice
#define cudaDeviceSynchronize hipDeviceSynchronize
#define cudaMemcpy hipMemcpy
#define cudaMemcpyAsync hipMemcpyAsync
#define cudaMalloc hipMalloc
#define cudaFree hipFree
#define cudaHostMalloc hipHostMalloc
#define cudaHostFree hipHostFree
#define cudaHostRegister hipHostRegister
#define cudaHostUnregister hipHostUnregister
#define cudaHostAlloc hipHostAlloc
#define cudaFreeHost hipFreeHost
#define cudaErrorPeerAccessAlreadyEnabled hipErrorPeerAccessAlreadyEnabled
#define cudaDeviceCanAccessPeer hipDeviceCanAccessPeer
#define cudaErrorPeerAccessNotEnabled hipErrorPeerAccessNotEnabled
#define cudaErrorInvalidDevice hipErrorInvalidDevice

// VEGA-PATCH 42 T03:40: nvrtc + cu* driver API + types
#include <hip/hiprtc.h>
#define nvrtcResult hiprtcResult
#define nvrtcProgram hiprtcProgram
#define nvrtcAddNameExpression hiprtcAddNameExpression
#define nvrtcCompileProgram hiprtcCompileProgram
#define nvrtcCreateProgram hiprtcCreateProgram
#define nvrtcDestroyProgram hiprtcDestroyProgram
#define nvrtcGetErrorString hiprtcGetErrorString
#define nvrtcGetLoweredName hiprtcGetLoweredName
#define nvrtcGetPTX hiprtcGetCode
#define nvrtcGetPTXSize hiprtcGetCodeSize
#define nvrtcGetProgramLog hiprtcGetProgramLog
#define nvrtcGetProgramLogSize hiprtcGetProgramLogSize
#define nvrtcVersion hiprtcVersion
#define nvrtcGetCUBIN hiprtcGetCode
#define nvrtcGetCUBINSize hiprtcGetCodeSize
#define NVRTC_SUCCESS HIPRTC_SUCCESS
#define cuCtxGetCurrent hipCtxGetCurrent
#define cuLaunchKernel hipModuleLaunchKernel
#define cuModuleGetFunction hipModuleGetFunction
#define cuModuleLoadData hipModuleLoadData
#define cuModuleLoadDataEx hipModuleLoadDataEx
#define cuModuleUnload hipModuleUnload
#define cuOccupancyMaxActiveBlocksPerMultiprocessor hipModuleOccupancyMaxActiveBlocksPerMultiprocessor
#define cuMemAlloc hipMalloc
#define cuMemFree hipFree
#define cuMemcpyHtoD hipMemcpyHtoD
#define cuMemcpyDtoH hipMemcpyDtoH
#define cuGetErrorString hipDrvGetErrorString
#define cuGetErrorName hipDrvGetErrorName
#define CUmodule hipModule_t
#define CUfunction hipFunction_t
#define CUcontext hipCtx_t
#define CUdeviceptr hipDeviceptr_t
#define CUresult hipError_t
#define CUDA_SUCCESS hipSuccess
#define CUstream hipStream_t

#endif // USE_ROCM

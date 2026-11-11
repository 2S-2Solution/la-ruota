#pragma once
#include <hip/hip_runtime.h>
#define NVML_NO_UNVERSIONED_FUNC_DEFS
#include <rocm_smi/rocm_smi.h>

#define C10_HIP_DRIVER_CHECK(EXPR)                                        \
  do {                                                                     \
    hipError_t __err = EXPR;                                                 \
    if (__err != hipSuccess) {                                           \
      const char* err_str;                                                 \
      hipError_t get_error_str_err C10_UNUSED =                              \
          c10::hip::DriverAPI::get()->cuGetErrorString_(__err, &err_str); \
      if (get_error_str_err != hipSuccess) {                             \
        AT_ERROR("HIP driver error: unknown error");                      \
      } else {                                                             \
        AT_ERROR("HIP driver error: ", err_str);                          \
      }                                                                    \
    }                                                                      \
  } while (0)

#define C10_LIBCUDA_DRIVER_API(_)   \
  _(hipDeviceGetAttribute)           \
  _(cuMemAddressReserve)            \
  _(cuMemRelease)                   \
  _(cuMemMap)                       \
  _(cuMemAddressFree)               \
  _(cuMemSetAccess)                 \
  _(cuMemUnmap)                     \
  _(cuMemCreate)                    \
  _(cuMemGetAllocationGranularity)  \
  _(cuMemExportToShareableHandle)   \
  _(cuMemImportFromShareableHandle) \
  _(hipDrvGetErrorString)

#if defined(HIP_VERSION) && (HIP_VERSION >= 12030)
#define C10_LIBCUDA_DRIVER_API_12030(_) \
  _(cuMulticastAddDevice)               \
  _(cuMulticastBindMem)                 \
  _(cuMulticastCreate)
#else
#define C10_LIBCUDA_DRIVER_API_12030(_)
#endif

#define C10_NVML_DRIVER_API(_)           \
  _(nvmlInit_v2)                         \
  _(nvmlDeviceGetHandleByPciBusId_v2)    \
  _(nvmlDeviceGetNvLinkRemoteDeviceType) \
  _(nvmlDeviceGetNvLinkRemotePciInfo_v2) \
  _(nvmlDeviceGetComputeRunningProcesses)

namespace c10::hip {

struct DriverAPI {
#define CREATE_MEMBER(name) decltype(&name) name##_;
  C10_LIBCUDA_DRIVER_API(CREATE_MEMBER)
  C10_LIBCUDA_DRIVER_API_12030(CREATE_MEMBER)
  C10_NVML_DRIVER_API(CREATE_MEMBER)
#undef CREATE_MEMBER
  static DriverAPI* get();
  static void* get_nvml_handle();
};

} // namespace c10::hip

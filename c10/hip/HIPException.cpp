#include <c10/hip/HIPException.h>

#include <c10/hip/HIPDeviceAssertionHost.h>
#include <c10/util/Exception.h>
#include <hip/hip_runtime.h>

#include <string>

namespace c10::hip {

void c10_cuda_check_implementation(
    const int32_t err,
    const char* filename,
    const char* function_name,
    const int line_number,
    const bool include_device_assertions) {
  const auto cuda_error = static_cast<hipError_t>(err);
  const auto cuda_kernel_failure = include_device_assertions
      ? c10::hip::CUDAKernelLaunchRegistry::get_singleton_ref().has_failed()
      : false;

  if (C10_LIKELY(cuda_error == hipSuccess && !cuda_kernel_failure)) {
    return;
  }

  auto error_unused C10_UNUSED = hipGetLastError();
  (void)error_unused;

  std::string check_message;
#ifndef STRIP_ERROR_MESSAGES
  check_message.append("HIP error: ");
  check_message.append(hipGetErrorString(cuda_error));
  check_message.append(c10::hip::get_cuda_check_suffix());
  check_message.append("\n");
  if (include_device_assertions) {
    check_message.append(c10_retrieve_device_side_assertion_info());
  } else {
    check_message.append(
        "Device-side assertions were explicitly omitted for this error check; the error probably arose while initializing the DSA handlers.");
  }
#endif

  TORCH_CHECK(false, check_message);
}

} // namespace c10::hip

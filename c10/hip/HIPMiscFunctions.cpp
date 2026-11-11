#include <c10/hip/HIPMiscFunctions.h>
#include <cstdlib>

namespace c10::hip {

const char* get_cuda_check_suffix() noexcept {
  static char* device_blocking_flag = getenv("HIP_LAUNCH_BLOCKING");
  static bool blocking_enabled =
      (device_blocking_flag && atoi(device_blocking_flag));
  if (blocking_enabled) {
    return "";
  } else {
    return "\nCUDA kernel errors might be asynchronously reported at some"
           " other API call, so the stacktrace below might be incorrect."
           "\nFor debugging consider passing AMD_SERIALIZE_KERNEL=3";
  }
}
std::mutex* getFreeMutex() {
  static std::mutex cuda_free_mutex;
  return &cuda_free_mutex;
}

} // namespace c10::hip

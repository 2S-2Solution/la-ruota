// Just a little test file to make sure that the HIP library works
// [VEGA-HIPIFY T03:55 20 giu] cuda_runtime.h → hip/hip_runtime.h, cudaGetDeviceCount → hipGetDeviceCount

#include <c10/hip/HIPException.h>
#include <c10/hip/impl/HIPTest.h>

#include <hip/hip_runtime.h>

namespace c10::hip::impl {

bool has_cuda_gpu() {
  int count = 0;
  C10_HIP_IGNORE_ERROR(hipGetDeviceCount(&count));

  return count != 0;
}

int c10_cuda_test() {
  int r = 0;
  if (has_cuda_gpu()) {
    C10_HIP_CHECK(hipGetDevice(&r));
  }
  return r;
}

// This function is not exported
int c10_cuda_private_test() {
  return 2;
}

} // namespace c10::hip::impl

#pragma once
#include <ATen/jit_macros.h>

#if AT_USE_JITERATOR()

#include <c10/macros/Export.h>
#include <c10/util/SmallVector.h>
#include <ATen/core/Tensor.h>

#include <string>
#include <vector>

namespace at::hip {

TORCH_HIP_CPP_API c10::SmallVector<at::Tensor> CompileAndLaunchKernel(
  const std::string& code_string,
  const std::string& kernel_name,
  const int num_outputs,
  const c10::SmallVector<at::Tensor>& tensors,
  const c10::SmallVector<at::Scalar>& extra_args,
  bool return_by_ref);

} // namespace at::hip

#else

namespace at::hip {

// [VEGA-PATCH 48 1 ago] Questo e' lo STUB con corpo inline (jiterator disattivato):
// non puo' essere marcato dllimport/dllexport. Serve "inline", non la macro di export.
inline c10::SmallVector<at::Tensor> CompileAndLaunchKernel(
  const std::string& code_string,
  const std::string& kernel_name,
  const int num_outputs,
  const c10::SmallVector<at::Tensor>& tensors,
  const c10::SmallVector<at::Scalar>& extra_args,
  bool return_by_ref) {
    TORCH_CHECK(false, "Jiterator is not supported");
  }
} // namespace at::hip

#endif // AT_USE_JITERATOR()

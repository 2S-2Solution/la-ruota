#pragma once

#include <ATen/hip/HIPContext.h>

namespace at::hip {

// Check if every tensor in a list of tensors matches the current
// device.
inline bool check_device(ArrayRef<Tensor> ts) {
  if (ts.empty()) {
    return true;
  }
  // [VEGA-PATCH 47 28 lug] qualificato: current_device() vive in c10::hip,
  // non in at::hip (lookup non qualificato risolveva a at::cuda::)
  // [VEGA-PATCH 52 1 ago] kCUDA, NON kHIP: in masquerading i tensori portano
  // DeviceType::CUDA, quindi con kHIP il confronto e' sempre falso e ogni
  // index_select/embedding fallisce con "must be on the current device".
  Device curDevice = Device(kCUDA, c10::hip::current_device());
  for (const Tensor& t : ts) {
    if (t.device() != curDevice) return false;
  }
  return true;
}

} // namespace at::hip

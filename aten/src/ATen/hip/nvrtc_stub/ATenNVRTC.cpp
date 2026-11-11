// [VEGA-PATCH 48 1 ago] hipify ha riscritto l'include come hiprtc_stub/ATenHIPRTC.h,
// ma directory e file non sono mai stati rinominati: restano nvrtc_stub/ATenNVRTC.h.
#include <ATen/hip/nvrtc_stub/ATenNVRTC.h>
#include <iostream>

namespace at { namespace cuda {

HIPRTC* load_hiprtc() {
  auto self = new HIPRTC();
#define CREATE_ASSIGN(name) self->name = name;
  AT_FORALL_HIPRTC(CREATE_ASSIGN)
  return self;
}

}} // at::cuda

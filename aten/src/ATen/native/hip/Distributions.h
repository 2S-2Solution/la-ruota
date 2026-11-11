// !!! Hipified a mano [VEGA-PATCH 47 28 lug] da ATen/native/cuda/Distributions.h
// (header mancante, pattern catalogo runbook: CUDAGeneratorImpl -> HIPGeneratorImpl)
#pragma once

namespace at {
struct HIPGeneratorImpl;
struct TensorIteratorBase;
class TensorBase;

namespace native {

void launch_poisson_cuda_kernel(
    const TensorBase &ret, const TensorBase &lambda, HIPGeneratorImpl *gen);

void launch_gamma_kernel(
    const TensorBase &ret, const TensorBase &alpha, HIPGeneratorImpl *gen);

void launch_binomial_cuda_kernel(
    TensorIteratorBase &iter, HIPGeneratorImpl *gen);

void launch_dirichlet_kernel(TensorIteratorBase &iter);

void launch_standard_gamma_grad_kernel(TensorIteratorBase &iter);

void launch_dirichlet_grad_kernel(TensorIteratorBase &iter);

}}  // namespace at::native

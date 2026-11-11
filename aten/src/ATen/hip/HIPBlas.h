#pragma once
/*
  Provides a subset of HIP BLAS functions as templates:

    gemm<Dtype>(transa, transb, m, n, k, alpha, a, lda, b, ldb, beta, c,
  ldc)

    gemv<Dtype>(transa, m, n, alpha, a, lda, x, incx, beta, y, incy)

    dot<Dtype>(n, x, incx, y, incy, result)

  where Dtype is double, float, at::Half or at::BFloat16 (ROCm, NOT for dot).
  The functions are available in at::hip::blas namespace.
 */

#include <ATen/hip/HIPContext.h>
#include <ATen/OpMathType.h>

namespace at::hip::blas {

// RAII guard that sets the CuBLAS pointer mode and restores it to
// its previous value when the guard is destroyed
class PointerModeGuard {
public:
  PointerModeGuard(hipblasHandle_t handle, hipblasPointerMode_t mode) :
      handle(handle) {
    TORCH_HIPBLAS_CHECK(hipblasGetPointerMode(handle, &previous_mode));
    TORCH_HIPBLAS_CHECK(hipblasSetPointerMode(handle, mode));
  }

  ~PointerModeGuard() {
    hipblasSetPointerMode(handle, previous_mode);
  }

private:
  hipblasHandle_t handle;
  hipblasPointerMode_t previous_mode;
};

/* LEVEL 3 BLAS FUNCTIONS */

#define HIPBLAS_GEMM_ARGTYPES(Dtype)                                                       \
  char transa, char transb, int64_t m, int64_t n, int64_t k, at::opmath_type<Dtype> alpha,  \
      const Dtype *a, int64_t lda, const Dtype *b, int64_t ldb, at::opmath_type<Dtype> beta,\
      Dtype *c, int64_t ldc

#define HIPBLAS_GEMM_ARGS(Dtype) transa, transb, m, n, k, alpha, a, lda, b, ldb, beta, c, ldc

template <typename Dtype>
inline void gemm(HIPBLAS_GEMM_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype),"at::hip::blas::gemm: not implemented");
}

template <>
void gemm<double>(HIPBLAS_GEMM_ARGTYPES(double));
template <>
void gemm<float>(HIPBLAS_GEMM_ARGTYPES(float));
template <>
void gemm<c10::complex<double>>(HIPBLAS_GEMM_ARGTYPES(c10::complex<double>));
template <>
void gemm<c10::complex<float>>(HIPBLAS_GEMM_ARGTYPES(c10::complex<float>));
template <>
void gemm<at::Half>(HIPBLAS_GEMM_ARGTYPES(at::Half));
template <>
void gemm<at::BFloat16>(HIPBLAS_GEMM_ARGTYPES(at::BFloat16));

template <typename Dtype>
inline void gemm_internal(HIPBLAS_GEMM_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype),"at::hip::blas::gemm_internal: not implemented");
}

template <>
void gemm_internal<double>(HIPBLAS_GEMM_ARGTYPES(double));
template <>
void gemm_internal<float>(HIPBLAS_GEMM_ARGTYPES(float));
template <>
void gemm_internal<c10::complex<double>>(HIPBLAS_GEMM_ARGTYPES(c10::complex<double>));
template <>
void gemm_internal<c10::complex<float>>(HIPBLAS_GEMM_ARGTYPES(c10::complex<float>));
template <>
void gemm_internal<at::Half>(HIPBLAS_GEMM_ARGTYPES(at::Half));
template <>
void gemm_internal<at::BFloat16>(HIPBLAS_GEMM_ARGTYPES(at::BFloat16));

enum GEMMAndBiasActivationEpilogue {
  None,
  RELU,
  GELU,
};

// NOTE: GELU activation is not supported prior to HIP 11.4 and will
// do nothing if passed in that case.
template <typename Dtype>
void gemm_and_bias(
    bool transpose_mat1,
    bool transpose_mat2,
    int64_t m,
    int64_t n,
    int64_t k,
    at::opmath_type<Dtype> alpha_val,
    const Dtype* mat1_ptr,
    int64_t mat1_ld,
    const Dtype* mat2_ptr,
    int64_t mat2_ld,
    const Dtype* bias,
    Dtype* result_ptr,
    int64_t result_ld,
    GEMMAndBiasActivationEpilogue activation = GEMMAndBiasActivationEpilogue::None);

void int8_gemm(
    bool transpose_mat1,
    bool transpose_mat2,
    int64_t m,
    int64_t n,
    int64_t k,
    const int8_t* mat1_ptr,
    int64_t mat1_ld,
    const int8_t* mat2_ptr,
    int64_t mat2_ld,
    int32_t* result_ptr,
    int64_t result_ld);

void scaled_gemm(
    char transa,
    char transb,
    int64_t m,
    int64_t n,
    int64_t k,
    const void* mat1_ptr,
    const void* mat1_scale_ptr,
    int64_t mat1_ld,
    ScalarType mat1_dtype,
    const void* mat2_ptr,
    const void* mat2_scale_ptr,
    int64_t mat2_ld,
    ScalarType mat2_dtype,
    const void* bias_ptr,
    ScalarType bias_dtype,
    void* result_ptr,
    const void* result_scale_ptr,
    int64_t result_ld,
    ScalarType result_dtype,
    void* amax_ptr,
    bool use_fast_accum);

#define HIPBLAS_BGEMM_ARGTYPES(Dtype)                                                        \
  char transa, char transb, int64_t m, int64_t n, int64_t k, at::opmath_type<Dtype> alpha,    \
      const Dtype *a, int64_t lda, int64_t stridea,                                           \
      const Dtype *b, int64_t ldb, int64_t strideb,                                           \
      at::opmath_type<Dtype> beta, Dtype *c, int64_t ldc, int64_t stridec, int64_t num_batches

#define HIPBLAS_BGEMM_ARGS(Dtype) \
  transa, transb, m, n, k, alpha, a, lda, stridea, b, ldb, strideb, beta, c, ldc, stridec, num_batches

template <typename Dtype>
inline void bgemm(HIPBLAS_BGEMM_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype),"at::hip::blas::bgemm: not implemented");
}

template <>
void bgemm<double>(HIPBLAS_BGEMM_ARGTYPES(double));
template <>
void bgemm<float>(HIPBLAS_BGEMM_ARGTYPES(float));
template <>
void bgemm<c10::complex<double>>(HIPBLAS_BGEMM_ARGTYPES(c10::complex<double>));
template <>
void bgemm<c10::complex<float>>(HIPBLAS_BGEMM_ARGTYPES(c10::complex<float>));
template <>
void bgemm<at::Half>(HIPBLAS_BGEMM_ARGTYPES(at::Half));
template <>
void bgemm<at::BFloat16>(HIPBLAS_BGEMM_ARGTYPES(at::BFloat16));

template <typename Dtype>
inline void bgemm_internal(HIPBLAS_BGEMM_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype),"at::hip::blas::bgemm_internal: not implemented");
}

template <>
void bgemm_internal<double>(HIPBLAS_BGEMM_ARGTYPES(double));
template <>
void bgemm_internal<float>(HIPBLAS_BGEMM_ARGTYPES(float));
template <>
void bgemm_internal<c10::complex<double>>(HIPBLAS_BGEMM_ARGTYPES(c10::complex<double>));
template <>
void bgemm_internal<c10::complex<float>>(HIPBLAS_BGEMM_ARGTYPES(c10::complex<float>));
template <>
void bgemm_internal<at::Half>(HIPBLAS_BGEMM_ARGTYPES(at::Half));
template <>
void bgemm_internal<at::BFloat16>(HIPBLAS_BGEMM_ARGTYPES(at::BFloat16));

#define HIPBLAS_TRSM_ARGTYPES(Dtype)                                  \
  hipblasHandle_t handle, hipblasSideMode_t side, hipblasFillMode_t uplo, \
      hipblasOperation_t trans, hipblasDiagType_t diag, int m, int n,    \
      const Dtype *alpha, const Dtype *A, int lda, Dtype *B, int ldb

template <typename Dtype>
inline void trsm(HIPBLAS_TRSM_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype), "at::hip::blas::trsm: not implemented");
}

template <>
TORCH_HIP_API void trsm<float>(HIPBLAS_TRSM_ARGTYPES(float));
template <>
TORCH_HIP_API void trsm<double>(HIPBLAS_TRSM_ARGTYPES(double));
template <>
TORCH_HIP_API void trsm<c10::complex<float>>(HIPBLAS_TRSM_ARGTYPES(c10::complex<float>));
template <>
TORCH_HIP_API void trsm<c10::complex<double>>(HIPBLAS_TRSM_ARGTYPES(c10::complex<double>));

#define HIPBLAS_TRSM_BATCHED_ARGTYPES(Dtype)                          \
  hipblasHandle_t handle, hipblasSideMode_t side, hipblasFillMode_t uplo, \
      hipblasOperation_t trans, hipblasDiagType_t diag, int m, int n,    \
      const Dtype *alpha, Dtype *A[], int lda, Dtype *B[], int ldb,    \
      int batchCount

template <typename Dtype>
inline void trsmBatched(HIPBLAS_TRSM_BATCHED_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype), "at::hip::blas::trsmBatched: not implemented");
}

template <>
TORCH_HIP_API void trsmBatched<float>(HIPBLAS_TRSM_BATCHED_ARGTYPES(float));
template <>
TORCH_HIP_API void trsmBatched<double>(HIPBLAS_TRSM_BATCHED_ARGTYPES(double));
template <>
TORCH_HIP_API void trsmBatched<c10::complex<float>>(HIPBLAS_TRSM_BATCHED_ARGTYPES(c10::complex<float>));
template <>
TORCH_HIP_API void trsmBatched<c10::complex<double>>(HIPBLAS_TRSM_BATCHED_ARGTYPES(c10::complex<double>));

/* LEVEL 2 BLAS FUNCTIONS */

#define HIPBLAS_GEMV_ARGTYPES(Dtype)                                         \
  char trans, int64_t m, int64_t n, Dtype alpha, const Dtype *a, int64_t lda, \
      const Dtype *x, int64_t incx, Dtype beta, Dtype *y, int64_t incy

template <typename Dtype>
inline void gemv(HIPBLAS_GEMV_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype), "at::hip::blas::gemv: not implemented");
}

template <>
void gemv<double>(HIPBLAS_GEMV_ARGTYPES(double));
template <>
void gemv<float>(HIPBLAS_GEMV_ARGTYPES(float));
template <>
void gemv<c10::complex<double>>(HIPBLAS_GEMV_ARGTYPES(c10::complex<double>));
template <>
void gemv<c10::complex<float>>(HIPBLAS_GEMV_ARGTYPES(c10::complex<float>));
template <>
void gemv<at::Half>(HIPBLAS_GEMV_ARGTYPES(at::Half));
template <>
void gemv<at::BFloat16>(HIPBLAS_GEMV_ARGTYPES(at::BFloat16));

/* LEVEL 1 BLAS FUNCTIONS */

#define HIPBLAS_DOT_ARGTYPES(Dtype)                                      \
  hipblasHandle_t handle, int n, const Dtype *x, int incx, const Dtype *y, \
      int incy, Dtype *result

template <typename Dtype>
inline void dot(HIPBLAS_DOT_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype),"at::hip::blas::dot: not implemented");
}

template <>
void dot<double>(HIPBLAS_DOT_ARGTYPES(double));
template <>
void dot<float>(HIPBLAS_DOT_ARGTYPES(float));
template <>
void dot<at::Half>(HIPBLAS_DOT_ARGTYPES(at::Half));
template <>
void dot<at::BFloat16>(HIPBLAS_DOT_ARGTYPES(at::BFloat16));
template <>
void dot<c10::complex<double>>(HIPBLAS_DOT_ARGTYPES(c10::complex<double>));
template <>
void dot<c10::complex<float>>(HIPBLAS_DOT_ARGTYPES(c10::complex<float>));

template <typename Dtype>
inline void vdot(HIPBLAS_DOT_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype),"at::hip::blas::vdot: not implemented");
}

template <>
void vdot<c10::complex<float>>(HIPBLAS_DOT_ARGTYPES(c10::complex<float>));
template <>
void vdot<c10::complex<double>>(HIPBLAS_DOT_ARGTYPES(c10::complex<double>));

#define HIPBLAS_GETRS_ARGTYPES(Dtype)  \
  hipblasHandle_t handle, hipblasOperation_t trans, \
  int n, int nrhs, Dtype** dA_array, int lda, int* ipiv_array, \
  Dtype** dB_array, int ldb, int* info_array, int batchsize

template<class Dtype>
void getrsBatched(HIPBLAS_GETRS_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype),"at::hip::blas::getrsBatched: not implemented");
}
template<>
TORCH_HIP_API void getrsBatched<float>(HIPBLAS_GETRS_ARGTYPES(float));
template<>
TORCH_HIP_API void getrsBatched<double>(HIPBLAS_GETRS_ARGTYPES(double));
template<>
TORCH_HIP_API void getrsBatched<c10::complex<float>>(HIPBLAS_GETRS_ARGTYPES(c10::complex<float>));
template<>
TORCH_HIP_API void getrsBatched<c10::complex<double>>(HIPBLAS_GETRS_ARGTYPES(c10::complex<double>));

#define HIPBLAS_GEQRF_BATCHED_ARGTYPES(Dtype)                   \
  hipblasHandle_t handle, int m, int n, Dtype **A_array, int lda, \
      Dtype **tau_array, int *info, int batchsize

template <class Dtype>
void geqrfBatched(HIPBLAS_GEQRF_BATCHED_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype), "at::hip::blas::geqrfBatched: not implemented");
}
template <>
TORCH_HIP_API void geqrfBatched<float>(HIPBLAS_GEQRF_BATCHED_ARGTYPES(float));
template <>
TORCH_HIP_API void geqrfBatched<double>(HIPBLAS_GEQRF_BATCHED_ARGTYPES(double));
template <>
TORCH_HIP_API void geqrfBatched<c10::complex<double>>(
    HIPBLAS_GEQRF_BATCHED_ARGTYPES(c10::complex<double>));
template <>
TORCH_HIP_API void geqrfBatched<c10::complex<float>>(
    HIPBLAS_GEQRF_BATCHED_ARGTYPES(c10::complex<float>));

#define HIPBLAS_GETRF_ARGTYPES(Dtype)  \
  int n, Dtype** dA_array, int ldda, int* ipiv_array, int* info_array, int batchsize

template<class Dtype>
void getrfBatched(HIPBLAS_GETRF_ARGTYPES(Dtype)) {
  TORCH_CHECK(false, "at::hip::blas::getrfBatched: not implemented");
}
template<>
TORCH_HIP_API void getrfBatched<float>(HIPBLAS_GETRF_ARGTYPES(float));
template<>
TORCH_HIP_API void getrfBatched<double>(HIPBLAS_GETRF_ARGTYPES(double));
template<>
TORCH_HIP_API void getrfBatched<c10::complex<double>>(HIPBLAS_GETRF_ARGTYPES(c10::complex<double>));
template<>
TORCH_HIP_API void getrfBatched<c10::complex<float>>(HIPBLAS_GETRF_ARGTYPES(c10::complex<float>));

#define HIPBLAS_GELS_BATCHED_ARGTYPES(Dtype)  \
  hipblasHandle_t handle, hipblasOperation_t trans, int m, int n, int nrhs, Dtype** dA_array, int ldda, Dtype** dC_array, int lddc, int* info, int *devInfoArray, int batchSize

template <class Dtype>
void gelsBatched(HIPBLAS_GELS_BATCHED_ARGTYPES(Dtype)) {
  static_assert(false&&sizeof(Dtype),"at::hip::blas::gelsBatched: not implemented");
}

template<>
TORCH_HIP_API void gelsBatched<double>(HIPBLAS_GELS_BATCHED_ARGTYPES(double));
template<>
TORCH_HIP_API void gelsBatched<float>(HIPBLAS_GELS_BATCHED_ARGTYPES(float));
template<>
TORCH_HIP_API void gelsBatched<c10::complex<double>>(HIPBLAS_GELS_BATCHED_ARGTYPES(c10::complex<double>));
template<>
TORCH_HIP_API void gelsBatched<c10::complex<float>>(HIPBLAS_GELS_BATCHED_ARGTYPES(c10::complex<float>));

} // namespace at::hip::blas


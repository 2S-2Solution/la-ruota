#pragma once

#include <hipblas/hipblas.h>
#include <hipsparse/hipsparse.h>
#include <c10/macros/Export.h>

#ifdef HIPRT_VERSION
#include <rocsolver/rocsolver.h>
#endif

#if defined(USE_CUDSS)
#include <hipsparse/hipsparse.h>
#endif

#include <ATen/Context.h>
#include <c10/util/Exception.h>
#include <c10/hip/HIPException.h>


namespace c10 {

class CuDNNError : public c10::Error {
  using Error::Error;
};

}  // namespace c10

#define AT_CUDNN_FRONTEND_CHECK(EXPR, ...)                                                      \
  do {                                                                                          \
    auto error_object = EXPR;                                                                   \
    if (!error_object.is_good()) {                                                              \
      TORCH_CHECK_WITH(CuDNNError, false,                                                       \
            "cuDNN Frontend error: ", error_object.get_message());                              \
    }                                                                                           \
  } while (0)                                                                                   \

#define AT_CUDNN_CHECK_WITH_SHAPES(EXPR, ...) AT_CUDNN_CHECK(EXPR, "\n", ##__VA_ARGS__)

// See Note [CHECK macro]
#define AT_CUDNN_CHECK(EXPR, ...)                                                               \
  do {                                                                                          \
    cudnnStatus_t status = EXPR;                                                                \
    if (status != CUDNN_STATUS_SUCCESS) {                                                       \
      if (status == CUDNN_STATUS_NOT_SUPPORTED) {                                               \
        TORCH_CHECK_WITH(CuDNNError, false,                                                     \
            "cuDNN error: ",                                                                    \
            cudnnGetErrorString(status),                                                        \
            ". This error may appear if you passed in a non-contiguous input.", ##__VA_ARGS__); \
      } else {                                                                                  \
        TORCH_CHECK_WITH(CuDNNError, false,                                                     \
            "cuDNN error: ", cudnnGetErrorString(status), ##__VA_ARGS__);                       \
      }                                                                                         \
    }                                                                                           \
  } while (0)

namespace at::hip::blas {
C10_EXPORT const char* _cublasGetErrorEnum(hipblasStatus_t error);
} // namespace at::hip::blas

#define TORCH_HIPBLAS_CHECK(EXPR)                              \
  do {                                                          \
    hipblasStatus_t __err = EXPR;                                \
    TORCH_CHECK(__err == HIPBLAS_STATUS_SUCCESS,                 \
                "HIP error: ",                                 \
                at::hip::blas::_cublasGetErrorEnum(__err),     \
                " when calling `" #EXPR "`");                   \
  } while (0)

const char *cusparseGetErrorString(hipsparseStatus_t status);

#define TORCH_HIPSPARSE_CHECK(EXPR)                            \
  do {                                                          \
    hipsparseStatus_t __err = EXPR;                              \
    TORCH_CHECK(__err == HIPSPARSE_STATUS_SUCCESS,               \
                "HIP error: ",                                 \
                cusparseGetErrorString(__err),                  \
                " when calling `" #EXPR "`");                   \
  } while (0)

#if defined(USE_CUDSS)
namespace at::hip::cudss {
C10_EXPORT const char* cudssGetErrorMessage(cudssStatus_t error);
} // namespace at::hip::solver

#define TORCH_CUDSS_CHECK(EXPR)                                         \
  do {                                                                  \
    cudssStatus_t __err = EXPR;                                         \
    if (__err == CUDSS_STATUS_EXECUTION_FAILED) {                       \
      TORCH_CHECK_LINALG(                                               \
          false,                                                        \
          "cudss error: ",                                              \
          at::hip::cudss::cudssGetErrorMessage(__err),                 \
          ", when calling `" #EXPR "`",                                 \
          ". This error may appear if the input matrix contains NaN. ");\
    } else {                                                            \
      TORCH_CHECK(                                                      \
          __err == CUDSS_STATUS_SUCCESS,                                \
          "cudss error: ",                                              \
          at::hip::cudss::cudssGetErrorMessage(__err),                 \
          ", when calling `" #EXPR "`. ");                              \
    }                                                                   \
  } while (0)
#else
#define TORCH_CUDSS_CHECK(EXPR) EXPR
#endif

// cusolver related headers are only supported on hip now
#ifdef HIPRT_VERSION

namespace at::hip::solver {
C10_EXPORT const char* cusolverGetErrorMessage(cusolverStatus_t status);

constexpr const char* _cusolver_backend_suggestion =            \
  "If you keep seeing this error, you may use "                 \
  "`torch.backends.hip.preferred_linalg_library()` to try "    \
  "linear algebra operators with other supported backends. "    \
  "See https://pytorch.org/docs/stable/backends.html#torch.backends.hip.preferred_linalg_library";

} // namespace at::hip::solver

// When hip < 11.5, cusolver raises CUSOLVER_STATUS_EXECUTION_FAILED when input contains nan.
// When hip >= 11.5, cusolver normally finishes execution and sets info array indicating convergence issue.
#define TORCH_CUSOLVER_CHECK(EXPR)                                      \
  do {                                                                  \
    cusolverStatus_t __err = EXPR;                                      \
    if ((HIP_VERSION < 11500 &&                                        \
         __err == CUSOLVER_STATUS_EXECUTION_FAILED) ||                  \
        (HIP_VERSION >= 11500 &&                                       \
         __err == CUSOLVER_STATUS_INVALID_VALUE)) {                     \
      TORCH_CHECK_LINALG(                                               \
          false,                                                        \
          "cusolver error: ",                                           \
          at::hip::solver::cusolverGetErrorMessage(__err),             \
          ", when calling `" #EXPR "`",                                 \
          ". This error may appear if the input matrix contains NaN. ", \
          at::hip::solver::_cusolver_backend_suggestion);              \
    } else {                                                            \
      TORCH_CHECK(                                                      \
          __err == CUSOLVER_STATUS_SUCCESS,                             \
          "cusolver error: ",                                           \
          at::hip::solver::cusolverGetErrorMessage(__err),             \
          ", when calling `" #EXPR "`. ",                               \
          at::hip::solver::_cusolver_backend_suggestion);              \
    }                                                                   \
  } while (0)

#else
#define TORCH_CUSOLVER_CHECK(EXPR) EXPR
#endif

#define AT_HIP_CHECK(EXPR) C10_HIP_CHECK(EXPR)

// For HIP Driver API
//
// This is here instead of in c10 because NVRTC is loaded dynamically via a stub
// in ATen, and we need to use its nvrtcGetErrorString.
// See NOTE [ USE OF NVRTC AND DRIVER API ].
#if !defined(USE_ROCM)

#define AT_HIP_DRIVER_CHECK(EXPR)                                                                               \
  do {                                                                                                           \
    CUresult __err = EXPR;                                                                                       \
    if (__err != HIP_SUCCESS) {                                                                                 \
      const char* err_str;                                                                                       \
      CUresult get_error_str_err C10_UNUSED = at::globalContext().getNVRTC().cuGetErrorString(__err, &err_str);  \
      if (get_error_str_err != HIP_SUCCESS) {                                                                   \
        AT_ERROR("HIP driver error: unknown error");                                                            \
      } else {                                                                                                   \
        AT_ERROR("HIP driver error: ", err_str);                                                                \
      }                                                                                                          \
    }                                                                                                            \
  } while (0)

#else

#define AT_HIP_DRIVER_CHECK(EXPR)                                                \
  do {                                                                            \
    CUresult __err = EXPR;                                                        \
    if (__err != HIP_SUCCESS) {                                                  \
      AT_ERROR("HIP driver error: ", static_cast<int>(__err));                   \
    }                                                                             \
  } while (0)

#endif

// For HIP NVRTC
//
// Note: As of HIP 10, nvrtc error code 7, NVRTC_ERROR_BUILTIN_OPERATION_FAILURE,
// incorrectly produces the error string "NVRTC unknown error."
// The following maps it correctly.
//
// This is here instead of in c10 because NVRTC is loaded dynamically via a stub
// in ATen, and we need to use its nvrtcGetErrorString.
// See NOTE [ USE OF NVRTC AND DRIVER API ].
#define AT_HIP_NVRTC_CHECK(EXPR)                                                                   \
  do {                                                                                              \
    nvrtcResult __err = EXPR;                                                                       \
    if (__err != NVRTC_SUCCESS) {                                                                   \
      if (static_cast<int>(__err) != 7) {                                                           \
        AT_ERROR("HIP NVRTC error: ", at::globalContext().getNVRTC().nvrtcGetErrorString(__err));  \
      } else {                                                                                      \
        AT_ERROR("HIP NVRTC error: NVRTC_ERROR_BUILTIN_OPERATION_FAILURE");                        \
      }                                                                                             \
    }                                                                                               \
  } while (0)

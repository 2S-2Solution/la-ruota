#pragma once
// [VEGA-PATCH 47 31 lug] TORCH_HIP_CPP_API la definisce c10/macros/Export.h in base
// a TORCH_HIP_BUILD_MAIN_LIB. Qui c'era un #define AUTO-REFERENZIALE che la annullava,
// rendendola un identificatore sconosciuto in ogni TU che includeva questo header.
#include <c10/macros/Export.h>
// Light-weight version of HIPContext.h with fewer transitive includes

#include <cstdint>

#include <hip/hip_runtime_api.h>
#include <hipsparse/hipsparse.h>
#include <hipblas/hipblas.h>

// cublasLT was introduced in HIP 10.1 but we enable only for 11.1 that also
// added bf16 support
#include <hipblaslt/hipblaslt.h>

#ifdef HIPRT_VERSION
#include <rocsolver/rocsolver.h>
#endif

#if defined(USE_CUDSS)
#include <hipsparse/hipsparse.h>
#endif

#if defined(USE_ROCM)
#include <hipsolver/hipsolver.h>
#endif

#include <c10/core/Allocator.h>
#include <c10/hip/HIPFunctions.h>

namespace c10 {
struct Allocator;
}

namespace at::hip {

/*
A common HIP interface for ATen.

This interface is distinct from HIPHooks, which defines an interface that links
to both CPU-only and HIP builds. That interface is intended for runtime
dispatch and should be used from files that are included in both CPU-only and
HIP builds.

HIPContext, on the other hand, should be preferred by files only included in
HIP builds. It is intended to expose HIP functionality in a consistent
manner.

This means there is some overlap between the HIPContext and HIPHooks, but
the choice of which to use is simple: use HIPContext when in a HIP-only file,
use HIPHooks otherwise.

Note that HIPContext simply defines an interface with no associated class.
It is expected that the modules whose functions compose this interface will
manage their own state. There is only a single HIP context/state.
*/

/**
 * DEPRECATED: use device_count() instead
 */
inline int64_t getNumGPUs() {
    return c10::hip::device_count();
}

/**
 * HIP is available if we compiled with HIP, and there are one or more
 * devices.  If we compiled with HIP but there is a driver problem, etc.,
 * this function will report HIP is not available (rather than raise an error.)
 */
inline bool is_available() {
    return c10::hip::device_count() > 0;
}

TORCH_HIP_CPP_API hipDeviceProp_t* getCurrentDeviceProperties();

TORCH_HIP_CPP_API int warp_size();

TORCH_HIP_CPP_API hipDeviceProp_t* getDeviceProperties(c10::DeviceIndex device);

TORCH_HIP_CPP_API bool canDeviceAccessPeer(
    c10::DeviceIndex device,
    c10::DeviceIndex peer_device);

TORCH_HIP_CPP_API c10::Allocator* getHIPDeviceAllocator();

/* Handles */
TORCH_HIP_CPP_API hipsparseHandle_t getCurrentHIPSparseHandle();
TORCH_HIP_CPP_API hipblasHandle_t getCurrentHIPBlasHandle();
TORCH_HIP_CPP_API hipblasLtHandle_t getCurrentHIPBlasLtHandle();

TORCH_HIP_CPP_API void clearCublasWorkspaces();

#if defined(HIPRT_VERSION) || defined(USE_ROCM)
TORCH_HIP_CPP_API hipblasHandle_t getCurrentHIPSolverDnHandle();
#endif

#if defined(USE_CUDSS)
TORCH_HIP_CPP_API cudssHandle_t getCurrentCudssHandle();
#endif

} // namespace at::hip

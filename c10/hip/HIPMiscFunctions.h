#pragma once
// this file is to avoid circular dependency between HIPFunctions.h and
// HIPExceptions.h

#include <c10/hip/HIPMacros.h>

#include <mutex>

namespace c10::hip {
C10_HIP_API const char* get_cuda_check_suffix() noexcept;
C10_HIP_API std::mutex* getFreeMutex();
} // namespace c10::hip

#pragma once

#include <ATen/hip/HIPContextLight.h>

// Preserved for BC, as many files depend on these includes
#include <ATen/Context.h>
#include <c10/hip/HIPStream.h>
#include <c10/util/Logging.h>
#include <ATen/hip/Exceptions.h>

// [VEGA-PATCH 47 28 lug] compat: molti kernel del tree qualificano lo stream
// come at::hip::X ma i tipi vivono in c10::hip. Solo simboli di HIPStream.h
// (gia' incluso sopra): aggiungere qui c10/hip/HIPGuard.h fa collidere
// HIPMultiStreamGuardMasqueradingAsCUDA nei TU Register*.cpp.
namespace at::hip {
using c10::hip::HIPStream;
using c10::hip::getCurrentHIPStream;
} // namespace at::hip

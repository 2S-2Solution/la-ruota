// VEGA-PATCH 46n: wrapper con #pragma once attorno al raw (che intenzionalmente NON ha guard).
// Il sorgente cuda ATen/cuda/PhiloxCudaState.h non e' presente in questo checkout, quindi il
// wrapper e' ricreato a mano. Tutti i file devono includere QUESTO (non il Raw direttamente).
#pragma once
#include <ATen/hip/detail/PhiloxCudaStateRaw.cuh>

#pragma once

// [VEGA-PATCH 69 - 17 ott 2026] stream nullo che aspetta un evento.
// Il runtime HIP del driver Adrenalin (HIP 5.7.31541, e il Marconi che lo inoltra)
// rifiuta hipStreamWaitEvent con hipErrorInvalidValue quando lo stream che aspetta e'
// lo stream NULLO; con ogni altro stream funziona. In PyTorch lo stream nullo e'
// quello predefinito.
//
// Ponte (proposto da rocm-marconi): l'attesa va su uno stream BLOCCANTE di servizio,
// uno per scheda. Per specifica HIP lo stream nullo si sincronizza con gli stream
// bloccanti, quindi il lavoro accodato dopo sullo stream nullo aspetta l'evento, e la
// CPU non si ferma. La prima versione usava hipEventSynchronize: corretta, ma fermava
// la CPU per tutta l'attesa (341-388 ms su un lavoro di 375). Resta come ripiego se il
// ponte non si puo' creare. Spiegazione:
// la-ruota/workspace/patch_stream_nullo_e_torchscript.py

#include <hip/hip_runtime_api.h>

#include <mutex>

namespace c10::hip {

namespace vega_detail {

constexpr int kVegaMaxSchede = 64;

// lo stream ponte della scheda corrente, creato alla prima richiesta
inline hipStream_t vega_ponte(int scheda) {
  static std::once_flag creato[kVegaMaxSchede];
  static hipStream_t ponti[kVegaMaxSchede] = {};
  if (scheda < 0 || scheda >= kVegaMaxSchede) {
    return nullptr;
  }
  std::call_once(creato[scheda], [scheda] {
    hipStream_t s = nullptr;
    // flag 0 = hipStreamDefault: BLOCCANTE, e' questo che lo lega allo stream nullo
    if (hipStreamCreateWithFlags(&s, hipStreamDefault) == hipSuccess) {
      ponti[scheda] = s;
    }
  });
  return ponti[scheda];
}

} // namespace vega_detail

inline hipError_t vega_stream_wait_event(
    hipStream_t stream,
    hipEvent_t event,
    unsigned int flags) {
  if (stream != nullptr) {
    return hipStreamWaitEvent(stream, event, flags);
  }
  // chi chiama ha gia' impostato la scheda dello stream (guard)
  int scheda = -1;
  if (hipGetDevice(&scheda) == hipSuccess) {
    hipStream_t ponte = vega_detail::vega_ponte(scheda);
    if (ponte != nullptr) {
      return hipStreamWaitEvent(ponte, event, flags);
    }
  }
  return hipEventSynchronize(event);  // ripiego: corretto, ma ferma la CPU
}

} // namespace c10::hip

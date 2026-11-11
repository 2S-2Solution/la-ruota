"""VEGA-PATCH 69 - stream nullo che aspetta un evento, e torch.cuda dentro TorchScript.

1. STREAM NULLO (difetto del runtime HIP del driver Adrenalin, HIP 5.7.31541)
   hipStreamWaitEvent(stream, evento, 0) restituisce hipErrorInvalidValue quando lo
   stream che aspetta e' lo stream NULLO, qualunque sia l'evento (con o senza tempi,
   registrato sul nullo o su un altro stream). Con ogni altro stream funziona. Su Linux
   la stessa chiamata e' valida. In PyTorch lo stream nullo e' lo stream predefinito,
   quindi falliva ogni torch.cuda.Stream.wait_stream / wait_event / Event.wait verso
   lo stream corrente ("HIP error: invalid argument"). Riprodotto fuori da PyTorch con
   ctypes su amdhip64.dll: C:\\LaRuota_workspace\\riproduci_stream_nullo_hip.py.
   Rimedio: c10/hip/VegaStreamWait.h. Se chi aspetta e' lo stream nullo, l'attesa va
   su uno stream BLOCCANTE di servizio (ponte proposto da rocm-marconi): per specifica
   lo stream nullo si sincronizza con gli stream bloccanti, e la CPU non si ferma. La
   prima versione usava hipEventSynchronize e fermava la CPU per tutta l'attesa
   (341-388 ms su 375: banco_attesa_stream.py); resta come ripiego. Usato nei tre punti
   che fanno aspettare uno stream (HIPEvent::block e i due guard).
   StorageSharing.cpp (IPC fra processi) non si tocca: su Windows l'IPC GPU non esiste.

2. TORCHSCRIPT (scelta di upstream, sbagliata per noi)
   ir.cpp considera "con effetti collaterali" cuda::set_stream, _set_device,
   _current_device e synchronize solo #if !defined(USE_ROCM): su ROCm il codice morto
   di TorchScript li elimina, e torch.cuda.synchronize() o `with torch.cuda.stream(s)`
   dentro uno script spariscono dal grafo. I simboli esistono anche su ROCm
   (interned_strings.h); upstream li escludeva perche' su ROCm non compilava
   register_cuda_ops.cpp, che la ruota invece compila dalla VEGA-PATCH 68.

    python patch_stream_nullo_e_torchscript.py --prova
    python patch_stream_nullo_e_torchscript.py --applica
"""
import io
import os
import shutil
import sys

R = r"C:\LaRuota_workspace\pytorch_src"
NUOVO_H = os.path.join(R, r"c10\hip\VegaStreamWait.h")
applica = "--applica" in sys.argv
MARCA = "[VEGA-PATCH 69]"

HEADER = r'''#pragma once

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
// C:\LaRuota_workspace\patch_stream_nullo_e_torchscript.py

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
'''

lavori = {
    os.path.join(R, r"aten\src\ATen\hip\HIPEvent.h"): [
        ("      AT_HIP_CHECK(hipStreamWaitEvent(stream, event_, 0));",
         "      AT_HIP_CHECK(c10::hip::vega_stream_wait_event(stream, event_, 0));  // [VEGA-PATCH 69]"),
    ],
    os.path.join(R, r"aten\src\ATen\hip\impl\HIPGuardImplMasqueradingAsCUDA.h"): [
        ("""    C10_HIP_CHECK(hipStreamWaitEvent(
      hip_stream,
      hip_event,
      /*flags (must be zero)=*/ 0));""",
         """    C10_HIP_CHECK(c10::hip::vega_stream_wait_event(  // [VEGA-PATCH 69] stream nullo
      hip_stream,
      hip_event,
      /*flags (must be zero)=*/ 0));"""),
    ],
    os.path.join(R, r"c10\hip\impl\HIPGuardImpl.h"): [
        ("""    C10_HIP_CHECK(hipStreamWaitEvent(
        hip_stream,
        cuda_event,
        /*flags (must be zero)=*/0));""",
         """    C10_HIP_CHECK(c10::hip::vega_stream_wait_event(  // [VEGA-PATCH 69] stream nullo
        hip_stream,
        cuda_event,
        /*flags (must be zero)=*/0));"""),
    ],
    os.path.join(R, r"torch\csrc\jit\ir\ir.cpp"): [
        ("""#if !defined(USE_ROCM)
    case cuda::set_stream:
    case cuda::_set_device:
    case cuda::_current_device:
    case cuda::synchronize:
#endif""",
         """    // [VEGA-PATCH 69] upstream le escludeva su ROCm: senza, il codice morto di
    // TorchScript elimina synchronize e set_stream. Nome completo perche' su ROCm un
    // namespace torch::jit::cuda nasconde quello dei simboli
    case c10::cuda::set_stream:
    case c10::cuda::_set_device:
    case c10::cuda::_current_device:
    case c10::cuda::synchronize:"""),
    ],
}
# l'include del nuovo header, in testa ai tre file che lo usano
INCLUDE = '#include <c10/hip/VegaStreamWait.h>  // [VEGA-PATCH 69]\n'

testi, errori = {}, 0
for f, sost in lavori.items():
    t = io.open(f, encoding="utf-8", newline="").read()
    if MARCA in t:
        print(f"  {os.path.basename(f)}: gia' applicata")
        continue
    crlf = "\r\n" in t
    for vecchio, nuovo in sost:
        if crlf:
            vecchio, nuovo = vecchio.replace("\n", "\r\n"), nuovo.replace("\n", "\r\n")
        n = t.count(vecchio)
        if n != 1:
            print(f"  ERRORE {os.path.basename(f)}: trovato {n} volte: {vecchio.strip().splitlines()[0][:70]}")
            errori += 1
            continue
        t = t.replace(vecchio, nuovo)
        print(f"  ok {os.path.basename(f)}: {vecchio.strip().splitlines()[0][:70]}")
    if not f.endswith("ir.cpp"):
        nl = "\r\n" if crlf else "\n"
        primo = t.find("#include")
        if primo < 0:
            print(f"  ERRORE {os.path.basename(f)}: nessun #include a cui agganciarsi")
            errori += 1
        else:
            t = t[:primo] + INCLUDE.replace("\n", nl) + t[primo:]
    testi[f] = t

if errori:
    print(f"{errori} errori: nulla scritto")
    sys.exit(1)
if applica:
    if not os.path.exists(NUOVO_H) or io.open(NUOVO_H, encoding="utf-8").read() != HEADER:
        io.open(NUOVO_H, "w", encoding="utf-8", newline="\n").write(HEADER)
        print(f"  creato {NUOVO_H}")
    for f, t in testi.items():
        if not os.path.exists(f + ".bak_pre_vega69"):
            shutil.copy2(f, f + ".bak_pre_vega69")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

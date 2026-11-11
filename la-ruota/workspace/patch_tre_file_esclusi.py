"""VEGA-PATCH 68 - rientrano i tre file esclusi da torch_hip a giugno (VEGA-PATCH 44).

  torch/csrc/inductor/aoti_torch/shim_cuda.cpp     parte GPU dello shim di AOTInductor
  torch/csrc/profiler/stubs/cuda.cpp                tempi GPU del profiler classico
                                                    (use_cuda=True / record_function)
  torch/csrc/jit/runtime/register_cuda_ops.cpp      torch.cuda.* (stream, synchronize,
                                                    eventi) dentro TorchScript

A giugno erano fuori perche' torch/csrc non era hipificato (bug Windows di hipify). Ora
lo e': shim_cuda e register_cuda_ops sono gia' puliti. Il profiler include
<roctracer/roctx.h>, che ROCm 5.7 su Windows non ha: i tre marcatori roctx (mark,
rangePush, rangePop) diventano vuoti. Tempi e sincronizzazione restano, perche' usano
gli eventi HIP. Si perdono solo le etichette per gli strumenti esterni di AMD, che su
Windows non esistono.

    python patch_tre_file_esclusi.py --prova
    python patch_tre_file_esclusi.py --applica
"""
import io
import os
import shutil
import sys

R = r"C:\LaRuota_workspace\pytorch_src"
BZL = os.path.join(R, "build_variables.bzl")
PROF = os.path.join(R, r"torch\csrc\profiler\stubs\cuda.cpp")
CUDA_H = os.path.join(R, r"torch\csrc\jit\cuda\cuda.h")
CMAKELISTS = os.path.join(R, "CMakeLists.txt")
applica = "--applica" in sys.argv

lavori = {
    BZL: [
        ('    # "torch/csrc/inductor/aoti_torch/shim_cuda.cpp",  # VEGA-PATCH 44: excluded\n',
         '    "torch/csrc/inductor/aoti_torch/shim_cuda.cpp",  # [VEGA-PATCH 68] rientrato\n'),
        ('    # "torch/csrc/profiler/stubs/cuda.cpp",  # VEGA-PATCH 44: excluded\n',
         '    "torch/csrc/profiler/stubs/cuda.cpp",  # [VEGA-PATCH 68] rientrato, senza roctx\n'),
        ('    # "torch/csrc/jit/runtime/register_cuda_ops.cpp",  # VEGA-PATCH 44b T06:25: excluded\n',
         '    "torch/csrc/jit/runtime/register_cuda_ops.cpp",  # [VEGA-PATCH 68] rientrato\n'),
    ],
    PROF: [
        ("""#ifdef TORCH_CUDA_USE_NVTX3
#include <roctracer/roctx.h>
#else
#include <roctracer/roctx.h>
#endif
""",
         """// [VEGA-PATCH 68] niente <roctracer/roctx.h>: ROCm 5.7 su Windows non ha roctracer.
// I marcatori roctx qui sotto sono vuoti; tempi ed eventi usano HIP e funzionano.
"""),
        ("""  void mark(const char* name) const override {
    ::roctxMark(name);
  }

  void rangePush(const char* name) const override {
    ::roctxRangePushA(name);
  }

  void rangePop() const override {
    ::roctxRangePop();
  }
""",
         """  // [VEGA-PATCH 68] marcatori per gli strumenti esterni di AMD: vuoti senza roctracer
  void mark(const char* /*name*/) const override {}

  void rangePush(const char* /*name*/) const override {}

  void rangePop() const override {}
"""),
    ],
    # register_cuda_ops.cpp include torch/csrc/jit/cuda/cuda.h, hipificato a meta':
    #  - la VEGA-PATCH 47 "definiva" hipEventDisableTiming & c. come se stessi senza
    #    includere l'header che li dichiara davvero;
    #  - at::hip::HIPEvent vuole un HIPStream, qui arriva un HIPStreamMasqueradingAsCUDA:
    #    il passaggio giusto e' .hip_stream().
    CUDA_H: [
        ("""#if defined(USE_ROCM) || defined(__HIP_PLATFORM_AMD__)
#define hipEventDisableTiming  hipEventDisableTiming
#define hipEventDefault        hipEventDefault
#define hipEventBlockingSync   hipEventBlockingSync
#define hipEventInterprocess   hipEventInterprocess
#define hipIpcEventHandle_t    hipIpcEventHandle_t
#endif
""",
         """// [VEGA-PATCH 68] le #define della 47 (ogni nome definito come se stesso) non
// dichiaravano nulla: serve l'header HIP che porta le costanti degli eventi.
#include <hip/hip_runtime_api.h>
"""),
        ("""inline void HIPStreamMasqueradingAsCUDA::waitEvent(const c10::intrusive_ptr<CUDAEvent>& event) {
  event->event_->block(*stream_);
}""",
         """inline void HIPStreamMasqueradingAsCUDA::waitEvent(const c10::intrusive_ptr<CUDAEvent>& event) {
  event->event_->block(stream_->hip_stream());  // [VEGA-PATCH 68]
}"""),
        ("""inline void CUDAEvent::record(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream) {
  event_->record(*stream->stream_);
}

inline void CUDAEvent::recordInternal(HIPStreamMasqueradingAsCUDA* stream) {
  event_->record(*stream->stream_);
}

inline void CUDAEvent::wait(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream) {
  event_->block(*stream->stream_);
}""",
         """inline void CUDAEvent::record(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream) {
  event_->record(stream->stream_->hip_stream());  // [VEGA-PATCH 68]
}

inline void CUDAEvent::recordInternal(HIPStreamMasqueradingAsCUDA* stream) {
  event_->record(stream->stream_->hip_stream());  // [VEGA-PATCH 68]
}

inline void CUDAEvent::wait(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream) {
  event_->block(stream->stream_->hip_stream());  // [VEGA-PATCH 68]
}"""),
    ],
}

testi, errori = {}, 0
for f, sost in lavori.items():
    t = io.open(f, encoding="utf-8", newline="").read()
    if "[VEGA-PATCH 68]" in t:
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
    testi[f] = t

if errori:
    print(f"{errori} errori: nulla scritto")
    sys.exit(1)
if applica:
    for f, t in testi.items():
        if not os.path.exists(f + ".bak_pre_vega68"):
            shutil.copy2(f, f + ".bak_pre_vega68")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
    # l'elenco dei sorgenti si legge al configure: si forza la riconfigurazione
    os.utime(CMAKELISTS, None)
    print("applicata (CMakeLists.txt toccato per la riconfigurazione)")
else:
    print("prova a vuoto riuscita")

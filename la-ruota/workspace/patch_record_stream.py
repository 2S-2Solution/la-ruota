"""VEGA-PATCH 70 - tensor.record_stream(stream) su GPU.

record_stream falliva sempre con "Expected stream_.device_type() == DeviceType::HIP".
hipify ha tradotto RecordStream.cu con c10::hip::HIPStream::unpack3(..., device_type),
ma lo stream che arriva da Python porta DeviceType::CUDA (masquerading), e HIPStream
accetta solo HIP. La forma giusta passa da HIPStreamMasqueradingAsCUDA, che converte
CUDA -> HIP, e poi da .hip_stream(). Emerso dopo la VEGA-PATCH 69: prima gli stream
secondari non funzionavano proprio, e record_stream serve solo con quelli.

    python patch_record_stream.py --prova
    python patch_record_stream.py --applica
"""
import io
import os
import shutil
import sys

F = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\RecordStream.hip"
applica = "--applica" in sys.argv

vecchio_inc = "#include <c10/hip/HIPCachingAllocator.h>\n"
nuovo_inc = vecchio_inc + "#include <ATen/hip/impl/HIPStreamMasqueradingAsCUDA.h>  // [VEGA-PATCH 70]\n"
vecchio = ("  c10::hip::HIPCachingAllocator::recordStream(self.storage().data_ptr(), "
           "c10::hip::HIPStream::unpack3(data.stream_id, data.device_index, data.device_type));\n")
nuovo = ("  // [VEGA-PATCH 70] lo stream arriva come CUDA (masquerading): la conversione la fa\n"
         "  // HIPStreamMasqueradingAsCUDA; HIPStream::unpack3 accetta solo DeviceType::HIP\n"
         "  c10::hip::HIPCachingAllocator::recordStream(self.storage().data_ptr(),\n"
         "      at::hip::HIPStreamMasqueradingAsCUDA::unpack3(\n"
         "          data.stream_id, data.device_index, data.device_type).hip_stream());\n")

t = io.open(F, encoding="utf-8", newline="").read()
if "[VEGA-PATCH 70]" in t:
    print("gia' applicata")
    sys.exit(0)
crlf = "\r\n" in t
errori = 0
for v, n in ((vecchio_inc, nuovo_inc), (vecchio, nuovo)):
    if crlf:
        v, n = v.replace("\n", "\r\n"), n.replace("\n", "\r\n")
    if t.count(v) != 1:
        print(f"  ERRORE: trovato {t.count(v)} volte: {v.strip()[:70]}")
        errori += 1
        continue
    t = t.replace(v, n)
    print(f"  ok: {v.strip()[:70]}")
if errori:
    sys.exit(1)
if applica:
    if not os.path.exists(F + ".bak_pre_vega70"):
        shutil.copy2(F, F + ".bak_pre_vega70")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

"""VEGA-PATCH 63 - i kHIP rimasti dopo hipify.

hipify traduce kCUDA -> kHIP, DeviceType::CUDA -> DeviceType::HIP, Backend::CUDA ->
Backend::HIP, DispatchKey::CUDA -> DispatchKey::HIP. In questa build i tensori
portano DeviceType::CUDA (masquerading), e il backend HIP non ha kernel registrati:
ogni tensore creato su HIP fa fallire la prima operazione con
"Could not run 'aten::empty.memory_format' with arguments from the 'HIP' backend".

Sintomi misurati prima della patch: histc, bincount e bincount con pesi in eccezione;
torch.cuda.Event().device == hip:0 mentre i tensori stanno su cuda:0.

Si cambiano solo le righe elencate, verificando che contengano il token atteso.
NON si tocca HIPStreamMasqueradingAsCUDA.h: li' la conversione a HIP e' voluta.

    python patch_khip_masquerading.py --prova
    python patch_khip_masquerading.py --applica
"""
import io
import os
import shutil
import sys

ATEN = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen"
MARCA = "  // [VEGA-PATCH 63] CUDA: masquerading"

# (file relativo, riga 1-based, token vecchio, token nuovo)
MODIFICHE = [
    (r"native\hip\Copy.hip", 320, "kHIP", "kCUDA"),
    (r"native\hip\SummaryOps.hip", 185, "Backend::HIP", "Backend::CUDA"),
    (r"native\hip\SummaryOps.hip", 187, "Backend::HIP", "Backend::CUDA"),
    (r"native\hip\SummaryOps.hip", 263, "kHIP", "kCUDA"),
    (r"native\hip\SummaryOps.hip", 301, "DeviceType::HIP", "DeviceType::CUDA"),
    (r"native\hip\SummaryOps.hip", 323, "DeviceType::HIP", "DeviceType::CUDA"),
    (r"native\hip\TensorFactories.hip", 76, "DispatchKey::HIP", "DispatchKey::CUDA"),
    (r"native\nested\hip\NestedTensorBinaryOps.hip", 88, "kHIP", "kCUDA"),
    (r"native\nested\hip\NestedTensorTransformerFunctions.hip", 1346, "at::kHIP", "at::kCUDA"),
    (r"native\nested\hip\NestedTensorTransformerFunctions.hip", 1350, "at::kHIP", "at::kCUDA"),
    (r"native\transformers\hip\attention.hip", 457, "kHIP", "kCUDA"),
    (r"native\transformers\hip\attention.hip", 797, "kHIP", "kCUDA"),
    (r"native\transformers\hip\attention.hip", 798, "kHIP", "kCUDA"),
    (r"native\transformers\hip\attention.hip", 1105, "kHIP", "kCUDA"),
    (r"native\transformers\hip\attention.hip", 1123, "kHIP", "kCUDA"),
    (r"hip\HIPEvent.h", 51, "at::kHIP", "at::kCUDA"),
    (r"hip\HIPEvent.h", 78, "at::kHIP", "at::kCUDA"),
    (r"hip\HIPEvent.h", 125, "at::kHIP", "at::kCUDA"),
    (r"hip\HIPEvent.h", 141, "at::kHIP", "at::kCUDA"),
    (r"hip\HIPEvent.h", 168, "at::kHIP", "at::kCUDA"),
    (r"hip\HIPEvent.h", 198, "at::kHIP", "at::kCUDA"),
]

applica = "--applica" in sys.argv
per_file = {}
for rel, riga, vecchio, nuovo in MODIFICHE:
    per_file.setdefault(rel, []).append((riga, vecchio, nuovo))

errori = 0
fatte = 0
for rel, lista in per_file.items():
    percorso = os.path.join(ATEN, rel)
    testo = io.open(percorso, encoding="utf-8-sig").read()
    bom = io.open(percorso, "rb").read(3) == b"\xef\xbb\xbf"
    righe = testo.split("\n")
    for riga, vecchio, nuovo in lista:
        linea = righe[riga - 1]
        if "VEGA-PATCH 63" in linea:
            print(f"  gia' fatta  {rel}:{riga}")
            continue
        if vecchio not in linea:
            print(f"  ERRORE      {rel}:{riga}  manca '{vecchio}': {linea.strip()[:70]}")
            errori += 1
            continue
        righe[riga - 1] = linea.replace(vecchio, nuovo).rstrip("\r") + MARCA + ("\r" if linea.endswith("\r") else "")
        print(f"  {'cambiata' if applica else 'da fare '}    {rel}:{riga}  {vecchio} -> {nuovo}")
        fatte += 1
    if applica and errori == 0:
        if not os.path.exists(percorso + ".bak_pre_vega63"):
            shutil.copy2(percorso, percorso + ".bak_pre_vega63")
        dati = "\n".join(righe).encode("utf-8")
        io.open(percorso, "wb").write((b"\xef\xbb\xbf" if bom else b"") + dati)

print(f"\nmodifiche {'applicate' if applica else 'da applicare'}: {fatte}   errori: {errori}")
if errori:
    print("NULLA scritto nei file con errori: le righe non corrispondono, ricontrollare")
    sys.exit(1)

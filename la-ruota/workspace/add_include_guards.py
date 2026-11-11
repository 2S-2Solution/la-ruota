"""[VEGA-PATCH 48 1 ago] Guardia di inclusione classica sugli header masquerading.

La junction build/aten/src/ATen/hip -> aten/src/ATen/hip fa vedere lo stesso file
con due percorsi assoluti diversi: #pragma once non deduplica e il compilatore
segnala "redefinition of HIPMultiStreamGuardMasqueradingAsCUDA".
"""
import os

TARGETS = {
    r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip\impl\HIPGuardImplMasqueradingAsCUDA.h":
        "ATEN_HIP_IMPL_HIPGUARDIMPL_MASQ_H_",
    r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip\impl\HIPStreamMasqueradingAsCUDA.h":
        "ATEN_HIP_IMPL_HIPSTREAM_MASQ_H_",
    r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip\impl\HIPAllocatorMasqueradingAsCUDA.h":
        "ATEN_HIP_IMPL_HIPALLOC_MASQ_H_",
    r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip\impl\HIPCachingAllocatorMasqueradingAsCUDA.h":
        "ATEN_HIP_IMPL_HIPCACHINGALLOC_MASQ_H_",
}

HEADER = """#pragma once
// [VEGA-PATCH 48 1 ago] Guardia classica OLTRE a #pragma once: la junction
// build/aten/src/ATen/hip -> aten/src/ATen/hip espone questo file con due percorsi
// assoluti diversi, e #pragma once non deduplica (redefinition dei tipi guard).
#ifndef {g}
#define {g}
"""

for path, guard in TARGETS.items():
    if not os.path.exists(path):
        print("assente:", os.path.basename(path))
        continue
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        src = f.read()
    if guard in src:
        print("gia' presente:", os.path.basename(path))
        continue
    if not src.lstrip().startswith("#pragma once"):
        print("niente #pragma once, salto:", os.path.basename(path))
        continue
    idx = src.index("#pragma once") + len("#pragma once")
    new = HEADER.format(g=guard) + src[idx:].lstrip("\r\n")
    new = new.rstrip() + "\n\n#endif  // " + guard + "\n"
    with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(new)
    print("guardia aggiunta:", os.path.basename(path))

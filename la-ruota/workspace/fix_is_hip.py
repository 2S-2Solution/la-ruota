"""[VEGA-PATCH 48 1 ago] .is_hip() -> .is_cuda() nel tree hip.

In questa build i tensori GPU hanno DeviceType::CUDA (e' il senso del masquerading:
ROCm si presenta come "cuda" all'utente). hipify ha pero' riscritto i controlli
Device::is_cuda() in Device::is_hip(), che verifica DeviceType::HIP e quindi risulta
sempre falso: la prima copia host->device falliva con
"unsupported devices in GPU copy_()".
"""
import os
import re

DIRS = [
    r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip",
    r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip",
    r"C:\LaRuota_workspace\pytorch_src\torch\csrc",
]

pat = re.compile(r"\.is_hip\(\)")
total, touched = 0, []
for d in DIRS:
    for root, _dirs, files in os.walk(d):
        for fn in files:
            if not fn.endswith((".hip", ".cuh", ".h", ".cpp")):
                continue
            if ".bak" in fn or ".disabled" in fn:
                continue
            p = os.path.join(root, fn)
            with open(p, encoding="utf-8", errors="surrogateescape") as f:
                src = f.read()
            new, n = pat.subn(".is_cuda()", src)
            if n:
                with open(p, "w", encoding="utf-8", errors="surrogateescape") as f:
                    f.write(new)
                touched.append(f"{fn}({n})")
                total += n

print("sostituzioni:", total)
for t in touched:
    print("  ", t)

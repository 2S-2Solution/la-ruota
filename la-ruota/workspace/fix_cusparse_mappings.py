"""[VEGA-PATCH 47 28 lug] Applica le mappature cuSPARSE/cuBLAS "special" di hipify
ai file gia' hipificati di sparse/hip e linalg.

Perche' servono: is_special_file() -> is_pytorch_file() soffre dello stesso bug
Windows dei separatori (vedi hipify_missing_headers.py). Risultato: i file sparse
sono stati hipificati con la mappa PYTORCH normale invece della PYTORCH_SPECIAL,
lasciando i simboli cusparse*/CUSPARSE_* non convertiti.

Applichiamo SOLO le voci cusparse/CUSPARSE della mappa ufficiale, in-place, cosi'
i fix manuali accumulati nei file restano intatti (rigenerare li perderebbe).
"""
import os
import re
import sys

PROJ = r"C:\LaRuota_workspace\pytorch_src"
sys.path.append(os.path.join(PROJ, "torch", "utils"))

from hipify.cuda_to_hip_mappings import CUDA_SPECIAL_MAP  # noqa: E402

TARGET_DIRS = [
    os.path.join(PROJ, "aten", "src", "ATen", "native", "sparse", "hip"),
    os.path.join(PROJ, "aten", "src", "ATen", "hip"),
    os.path.join(PROJ, "aten", "src", "ATen", "native", "hip"),
]

# mappa cusparse -> hipsparse dalla tabella ufficiale hipify.
# Filtriamo alle sole voci cusparse/CUSPARSE: il resto della SPECIAL map tocca
# cublas/cusolver, gia' gestiti altrove nel tree.
mapping = {}
for src, val in CUDA_SPECIAL_MAP.items():
    if not src.lower().startswith("cusparse"):
        continue
    dst = val[0] if isinstance(val, (tuple, list)) else val
    if src != dst:
        mapping[src] = dst

# ordina per lunghezza decrescente: evita che un prefisso mangi un nome piu' lungo
keys = sorted(mapping, key=len, reverse=True)
pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in keys) + r")\b")

total = 0
for d in TARGET_DIRS:
    if not os.path.isdir(d):
        continue
    for root, _dirs, files in os.walk(d):
        for fn in files:
            if not fn.endswith((".hip", ".cuh", ".h", ".cpp")):
                continue
            p = os.path.join(root, fn)
            with open(p, encoding="utf-8", errors="surrogateescape") as f:
                src = f.read()
            new, n = pattern.subn(lambda m: mapping[m.group(1)], src)
            if n:
                with open(p, "w", encoding="utf-8", errors="surrogateescape") as f:
                    f.write(new)
                print(f"{fn}: {n} sostituzioni")
                total += n

print(f"TOTALE: {total} sostituzioni su {len(keys)} mappature disponibili")

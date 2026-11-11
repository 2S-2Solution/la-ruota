"""[VEGA-PATCH 48 1 ago] Guard: usare le varianti MasqueradingAsCUDA.

c10::hip::HIPGuard / OptionalHIPGuard usano HIPGuardImpl, che asserisce
DeviceType::HIP. In questa build i tensori GPU hanno DeviceType::CUDA, quindi va usata
la coppia HIPGuardMasqueradingAsCUDA / OptionalHIPGuardMasqueradingAsCUDA dichiarata in
ATen/hip/impl/HIPGuardImplMasqueradingAsCUDA.h, che accetta CUDA.
"""
import os
import re

DIRS = [
    r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip",
    r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip",
]

INCLUDE = "#include <ATen/hip/impl/HIPGuardImplMasqueradingAsCUDA.h>"

# non toccare i nomi gia' masquerading
rules = [
    (re.compile(r"c10::hip::OptionalHIPGuard\b(?!MasqueradingAsCUDA)"),
     "c10::hip::OptionalHIPGuardMasqueradingAsCUDA"),
    (re.compile(r"c10::hip::HIPGuard\b(?!MasqueradingAsCUDA)(?!Impl)"),
     "c10::hip::HIPGuardMasqueradingAsCUDA"),
]

total, touched = 0, []
for d in DIRS:
    for root, _dirs, files in os.walk(d):
        for fn in files:
            if not fn.endswith((".hip", ".cuh", ".h", ".cpp")):
                continue
            if ".bak" in fn or ".disabled" in fn:
                continue
            # l'header che DEFINISCE i guard non va toccato
            if fn in ("HIPGuardImplMasqueradingAsCUDA.h",):
                continue
            p = os.path.join(root, fn)
            with open(p, encoding="utf-8", errors="surrogateescape") as f:
                src = f.read()
            new, n = src, 0
            for pat, rep in rules:
                new, k = pat.subn(rep, new)
                n += k
            if not n:
                continue
            if "HIPGuardImplMasqueradingAsCUDA.h" not in new:
                m = re.search(r"^#include [^\n]*\n", new, re.MULTILINE)
                if m:
                    new = new[:m.end()] + INCLUDE + "\n" + new[m.end():]
            with open(p, "w", encoding="utf-8", errors="surrogateescape") as f:
                f.write(new)
            touched.append(f"{fn}({n})")
            total += n

print("sostituzioni:", total)
for t in touched:
    print("  ", t)

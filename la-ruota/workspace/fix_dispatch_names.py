"""[VEGA-PATCH 47 28 lug] Sweep generico dei nomi di dispatch _hip -> _cuda.

Il dispatch key resta CUDA anche in build ROCm: i Register*.cpp generati chiamano
at::native::<nome>_cuda*, mentre hipify ha rinominato le definizioni in _hip.
I sweep precedenti erano posizionali (suffisso, infisso, macro) e lasciavano fuori
casi come `arange_cuda_out` (il `_cuda` non e' a fine identificatore).

Qui: raccogliamo TUTTI gli identificatori attesi dai Register*.cpp, poi per ogni
identificatore contenente `_hip` nei sorgenti hip proviamo la sostituzione
`_hip` -> `_cuda` e la applichiamo SOLO se il risultato e' un nome atteso.
Niente euristiche: o il simbolo serve al dispatcher, o non si tocca.
"""
import os
import re
import sys

PROJ = r"C:\LaRuota_workspace\pytorch_src"
BUILD_ATEN = os.path.join(PROJ, "build", "aten", "src", "ATen")
SRC_ATEN = os.path.join(PROJ, "aten", "src", "ATen")

# 1) nomi attesi dai file di registrazione generati
expected = set()
for fn in os.listdir(BUILD_ATEN):
    if not (fn.startswith("Register") and fn.endswith(".cpp")):
        continue
    with open(os.path.join(BUILD_ATEN, fn), encoding="utf-8", errors="surrogateescape") as f:
        txt = f.read()
    expected.update(re.findall(r"at::native::([A-Za-z_][A-Za-z_0-9]*)", txt))
    expected.update(re.findall(r"\b(structured_[A-Za-z_0-9]+)", txt))
print(f"identificatori attesi dai Register*.cpp: {len(expected)}")

# 2) directory dei sorgenti hipificati
targets = []
for root, dirs, files in os.walk(SRC_ATEN):
    if os.path.basename(root) != "hip":
        continue
    for r2, _d2, f2 in os.walk(root):
        for fn in f2:
            if fn.endswith((".hip", ".cuh", ".h", ".cpp")):
                targets.append(os.path.join(r2, fn))
print(f"file hip da controllare: {len(targets)}")

ident_re = re.compile(r"\b[A-Za-z_][A-Za-z_0-9]*_hip[A-Za-z_0-9]*\b")
total = 0
for p in targets:
    with open(p, encoding="utf-8", errors="surrogateescape") as f:
        src = f.read()
    names = {m for m in ident_re.findall(src)}
    subs = {}
    for n in names:
        cand = n.replace("_hip", "_cuda")
        if cand in expected and cand != n:
            subs[n] = cand
    if not subs:
        continue
    new = src
    for n, c in sorted(subs.items(), key=lambda kv: -len(kv[0])):
        new = re.sub(r"\b" + re.escape(n) + r"\b", c, new)
    if new != src:
        with open(p, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(new)
        print(f"{os.path.basename(p)}: {', '.join(sorted(subs))}")
        total += len(subs)

print(f"TOTALE identificatori rinominati: {total}")

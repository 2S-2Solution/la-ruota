"""Identifica il formato dei fat binary device dentro torch_hip.dll.

- '__CLANG_OFFLOAD_BUNDLE__' = bundle non compresso (leggibile dai comgr vecchi)
- 'CCOB'                     = bundle COMPRESSO, introdotto dai compilatori ROCm 6.x+
                               e NON leggibile dal comgr 5.7 del driver Adrenalin
Stampa anche le stringhe ISA (gfx...) trovate.
"""
import re
import sys

PATH = r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib\torch_hip.dll"

MAGICS = {
    b"__CLANG_OFFLOAD_BUNDLE__": 0,
    b"CCOB": 0,
    b"__CLANG_OFFLOAD_BUNDLET": 0,
}
isa = {}
CHUNK = 8 << 20
OVERLAP = 64

with open(PATH, "rb") as f:
    prev = b""
    while True:
        buf = f.read(CHUNK)
        if not buf:
            break
        data = prev + buf
        for m in MAGICS:
            MAGICS[m] += data.count(m)
        for match in re.finditer(rb"hipv4-amdgcn[^\x00\s]{0,60}|hip-amdgcn[^\x00\s]{0,60}", data):
            s = match.group().decode("ascii", "replace")
            isa[s] = isa.get(s, 0) + 1
        prev = data[-OVERLAP:]

print(f"file: {PATH}")
for m, c in MAGICS.items():
    print(f"  {m.decode():28s} -> {c}")

print("\ntriple/ISA trovati:")
for s, c in sorted(isa.items(), key=lambda kv: -kv[1])[:10]:
    print(f"  {c:6d}  {s}")

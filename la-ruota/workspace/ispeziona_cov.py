"""Legge la code object version degli ELF AMDGPU incorporati in torch_hip.dll.

Nell'header ELF: e_ident[7] = OSABI (64 = ELFOSABI_AMDGPU_HSA),
                e_ident[8] = ABIVERSION -> 1=COv3, 2=COv4, 3=COv5, 4=COv6.
Il comgr del driver Adrenalin 23.19 legge fino a COv4.
"""
from collections import Counter

PATH = r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib\torch_hip.dll"
NOMI = {0: "COv2", 1: "COv3", 2: "COv4", 3: "COv5", 4: "COv6"}

CHUNK = 8 << 20
OVERLAP = 32
conteggio = Counter()
osabi_visti = Counter()

with open(PATH, "rb") as f:
    prev = b""
    while True:
        buf = f.read(CHUNK)
        if not buf:
            break
        data = prev + buf
        i = 0
        while True:
            i = data.find(b"\x7fELF", i)
            if i < 0 or i + 16 > len(data):
                break
            osabi = data[i + 7]
            abiver = data[i + 8]
            osabi_visti[osabi] += 1
            if osabi == 64:  # AMDGPU HSA
                conteggio[abiver] += 1
            i += 4
        prev = data[-OVERLAP:]

print(f"file: {PATH}")
print(f"ELF trovati per OSABI: {dict(osabi_visti)}  (64 = AMDGPU_HSA)")
print("\ncode object version degli ELF AMDGPU:")
for v, c in sorted(conteggio.items()):
    print(f"  {NOMI.get(v, f'ABIVERSION {v}'):6s} -> {c} oggetti")
if not conteggio:
    print("  nessuno")

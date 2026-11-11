"""Legge le e_flags degli ELF AMDGPU dentro torch_hip.dll.

Decodifica (offset 48 dell'header ELF, 4 byte little-endian):
  mach    = ef & 0xff        0x2f = gfx906
  xnack   = (ef >> 8)  & 3   0=nessuno 1=any 2=off 3=on
  sramecc = (ef >> 10) & 3   idem
La Radeon VII non ha ECC sulla SRAM: un binario con sramecc ON viene rifiutato
dal runtime anche se la code object version e' giusta.
"""
import struct
from collections import Counter

PATH = r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib\torch_hip.dll"
FEAT = {0: "nessuno", 1: "any", 2: "off", 3: "on"}
COV = {2: "v4", 3: "v5", 4: "v6"}

conteggio = Counter()
CHUNK = 8 << 20

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
            if i < 0 or i + 52 > len(data):
                break
            if data[i + 7] == 64:  # OSABI AMDGPU_HSA
                cov = data[i + 8]
                ef = struct.unpack_from("<I", data, i + 48)[0]
                conteggio[(cov, ef)] += 1
            i += 4
        prev = data[-64:]

print(f"file: {PATH}\n")
for (cov, ef), n in sorted(conteggio.items()):
    mach = ef & 0xFF
    xnack = (ef >> 8) & 3
    sramecc = (ef >> 10) & 3
    stato = "OK" if sramecc != 3 else "RIFIUTATO da questa scheda"
    print(f"  {n:4d} oggetti  code object {COV.get(cov, cov)}  e_flags 0x{ef:x}  "
          f"mach 0x{mach:x}  xnack {FEAT[xnack]}  sramecc {FEAT[sramecc]}  -> {stato}")

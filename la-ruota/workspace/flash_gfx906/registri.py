"""Registri, sversamenti e LDS di un kernel, dal code object (nessuna GPU)."""
import re, subprocess, sys
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import importlib
OBJDUMP = r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-objdump.exe"
READELF = r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-readobj.exe"

def analizza(modulo, hd, extra=()):
    m = importlib.import_module(modulo)
    codice = (m.compila if hasattr(m, "compila") else m._compila)(hd, extra)
    p = rf"C:\LaRuota_workspace\flash_gfx906\tmp_{modulo}_{hd}.co"
    open(p, "wb").write(codice.raw)
    s = subprocess.run([OBJDUMP, "-d", "--mcpu=gfx906", p], capture_output=True, text=True).stdout
    v = max((int(x) for x in re.findall(r"\bv\[?(\d+)", s)), default=0) + 1
    spill = len(re.findall(r"scratch_|buffer_store_dword|buffer_load_dword", s))
    note = subprocess.run([READELF, "--notes", p], capture_output=True, text=True).stdout
    lds = re.findall(r"\.group_segment_fixed_size:\s*(\d+)", note)
    return v, spill, lds, len(s.splitlines())

if __name__ == "__main__":
    for modulo in sys.argv[1:]:
        for hd in (64, 128):
            print(modulo, hd, "VGPR=%d spill=%d LDS=%s righe_asm=%d" % analizza(modulo, hd))

"""[VEGA-PATCH 48 1 ago] Diagnosi del gap ABI fra torch_hip.dll e lo stack runtime 5.7.

torch_hip e' stato LINKATO contro TheRock 7.14 (hipblas V2, API tunable di rocblas),
ma l'unico MIOpen che carica su questa macchina e' quello Marconi patchato, che
richiede rocblas 5.7. Qui elenchiamo esattamente quali simboli importati da torch_hip
non esistono nelle DLL 5.7, cosi' la scelta successiva e' informata.
"""
import os
import re
import subprocess

LIB = r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib"

DUMPBIN = None
for root, _d, files in os.walk(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC"):
    if "dumpbin.exe" in files and "Hostx64\\x64" in root:
        DUMPBIN = os.path.join(root, "dumpbin.exe")
        break


def imports_by_dll(path):
    out = subprocess.run([DUMPBIN, "/IMPORTS", path],
                         capture_output=True, text=True, timeout=900).stdout
    res, cur = {}, None
    for line in out.splitlines():
        m = re.match(r"^\s{4}(\S+\.dll)\s*$", line)
        if m:
            cur = m.group(1).lower()
            res.setdefault(cur, set())
            continue
        m2 = re.match(r"^\s+[0-9A-F]+\s+([A-Za-z_][A-Za-z_0-9]*)\s*$", line)
        if m2 and cur:
            res[cur].add(m2.group(1))
    return res


def exports_of(path):
    out = subprocess.run([DUMPBIN, "/EXPORTS", path],
                         capture_output=True, text=True, timeout=900).stdout
    return set(re.findall(r"^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\S+)", out, re.MULTILINE))


imps = imports_by_dll(os.path.join(LIB, "torch_hip.dll"))
print("DLL importate da torch_hip.dll:", len(imps))

for dll in ("rocblas.dll", "hipblas.dll", "libhipsparse.dll", "hipsolver.dll",
            "miopen.dll", "libhipblaslt.dll"):
    if dll not in imps:
        continue
    p = os.path.join(LIB, dll)
    if not os.path.exists(p):
        # nome con maiuscole diverse
        for f in os.listdir(LIB):
            if f.lower() == dll:
                p = os.path.join(LIB, f)
                break
    if not os.path.exists(p):
        print(f"\n{dll}: FILE ASSENTE")
        continue
    exp = exports_of(p)
    missing = sorted(imps[dll] - exp)
    print(f"\n{dll}: richiesti {len(imps[dll])}, mancanti {len(missing)}")
    for m in missing[:15]:
        print("   MANCA:", m)

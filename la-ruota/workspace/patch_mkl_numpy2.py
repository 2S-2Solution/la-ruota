"""VEGA-PATCH 65 - MKL statico per la CPU, e torch_python contro gli header di numpy 2.

MKL: la ruota era compilata con BLAS=MKL ma senza MKL installato, quindi ripiegava su
Eigen: matmul su CPU a 1,4 GFLOPS contro i 167 di numpy, e niente LAPACK (tutta
l'algebra lineare su CPU assente, ed `eig` assente anche su GPU perche' passa dalla
CPU). Si installa MKL STATICO via pip (mkl-static, mkl-include, intel-openmp) in una
cartella separata - C:\\LaRuota_workspace\\mkl_prefix - cosi' MKL finisce dentro
torch_cpu.dll e a runtime serve solo libiomp5md.dll. Solo statico: FindMKL su MSVC
cerca prima la variante _dll e, se ci fossero entrambe, collegherebbe quella dinamica.

numpy 2: un'estensione compilata contro gli header di numpy 1.x NON funziona con
numpy 2; una compilata contro quelli di numpy 2 funziona con ENTRAMBI. torch_python
prende gli header dal bersaglio importato Python::NumPy: lo si punta agli header di
numpy 2.2.6 installati in C:\\LaRuota_workspace\\numpy2_headers, SENZA cambiare il
numpy dell'ambiente (chi usa la ruota durante la build non se ne accorge). Non si
tocca _Python_NumPy_INCLUDE_DIR in cache: FindPython lo lega con una firma
all'interprete e alla riconfigurazione lo rimetterebbe su numpy 1.26.

    python patch_mkl_numpy2.py --prova
    python patch_mkl_numpy2.py --applica
"""
import io
import os
import re
import shutil
import sys

RADICE = r"C:\LaRuota_workspace"
DEPS = os.path.join(RADICE, r"pytorch_src\cmake\Dependencies.cmake")
SCRIPT = os.path.join(RADICE, "build_laruota_canonical.cmd")
CACHE = os.path.join(RADICE, r"pytorch_src\build\CMakeCache.txt")
MKL_LIB = r"C:/LaRuota_workspace/mkl_prefix/Library"
NUMPY2 = r"C:/LaRuota_workspace/numpy2_headers/numpy/_core/include"

applica = "--applica" in sys.argv
errori = 0


def scrivi(percorso, testo):
    if not os.path.exists(percorso + ".bak_pre_vega65"):
        shutil.copy2(percorso, percorso + ".bak_pre_vega65")
    io.open(percorso, "w", encoding="utf-8", newline="").write(testo)


# ---- prerequisiti
for p in (MKL_LIB + "/lib/mkl_core.lib", MKL_LIB + "/lib/mkl_intel_lp64.lib",
          MKL_LIB + "/lib/libiomp5md.lib", MKL_LIB + "/include/mkl.h",
          NUMPY2 + "/numpy/arrayobject.h"):
    if not os.path.exists(p):
        print(f"  ERRORE prerequisito mancante: {p}")
        errori += 1
if os.path.exists(MKL_LIB + "/lib/mkl_intel_lp64_dll.lib"):
    print("  ERRORE: c'e' anche la variante _dll di MKL, verrebbe collegata quella dinamica")
    errori += 1

# ---- 1. Dependencies.cmake: torch_python contro numpy 2
dep = io.open(DEPS, encoding="utf-8").read()
ancora = "        caffe2_update_option(USE_NUMPY ON)\n"
blocco = ancora + f'''        # [VEGA-PATCH 65 - 16 ott 2026] torch_python contro gli header di NUMPY 2.
        # Compilato contro numpy 1.x, torch non funziona con numpy 2; compilato contro
        # numpy 2 funziona con entrambi. Si cambia solo il bersaglio Python::NumPy, non
        # _Python_NumPy_INCLUDE_DIR in cache (FindPython lo rimetterebbe su quello
        # dell'interprete). Spiegazione: C:\\LaRuota_workspace\\patch_mkl_numpy2.py
        set(_vega_numpy2 "{NUMPY2}")
        if(EXISTS "${{_vega_numpy2}}/numpy/arrayobject.h")
          set_target_properties(Python::NumPy PROPERTIES
            INTERFACE_INCLUDE_DIRECTORIES "${{_vega_numpy2}}")
          message(STATUS "[VEGA-PATCH 65] torch_python contro numpy 2: ${{_vega_numpy2}}")
        else()
          message(FATAL_ERROR "[VEGA-PATCH 65] header di numpy 2 assenti: ${{_vega_numpy2}}")
        endif()
'''
if "VEGA-PATCH 65" in dep:
    print("  Dependencies.cmake: gia' applicata")
elif dep.count(ancora) != 1:
    print(f"  ERRORE Dependencies.cmake: ancora trovata {dep.count(ancora)} volte, attesa 1")
    errori += 1
else:
    print("  Dependencies.cmake: torch_python contro numpy 2 " + ("applicato" if applica else "da applicare"))
    if applica and not errori:
        scrivi(DEPS, dep.replace(ancora, blocco))

# ---- 2. script di build: MKL in CMAKE_PREFIX_PATH
scr = io.open(SCRIPT, encoding="utf-8", errors="replace").read()
riga_cpp = re.search(r'^set "CMAKE_PREFIX_PATH=([^"]*)"\s*$', scr, re.M)
if "mkl_prefix" in scr:
    print("  build script: gia' applicata")
elif not riga_cpp:
    print("  ERRORE build script: riga CMAKE_PREFIX_PATH non trovata")
    errori += 1
else:
    vecchia = riga_cpp.group(0)
    nuova = (':: [VEGA-PATCH 65 - 16 ott 2026] MKL statico (pip, in mkl_prefix): FindMKL lo trova\n'
             ':: in <prefix>/lib e <prefix>/include. Vedi patch_mkl_numpy2.py\n'
             f'set "CMAKE_PREFIX_PATH={MKL_LIB.replace("/", chr(92))};{riga_cpp.group(1)}"')
    print("  build script: mkl_prefix in CMAKE_PREFIX_PATH " + ("aggiunto" if applica else "da aggiungere"))
    if applica and not errori:
        scrivi(SCRIPT, scr.replace(vecchia, nuova))

# ---- 3. cache: via i "non trovato" di MKL, cartelle Intel puntate a mkl_prefix
righe = io.open(CACHE, encoding="utf-8").read().split("\n")
tolte, cambiate, nuove = 0, 0, []
for r in righe:
    if re.match(r"^MKL_LIBRARIES_\w+_LIBRARY(-ADVANCED)?:", r):
        tolte += 1
        # via anche il commento che la precede: un "//..." seguito da una riga vuota
        # e' un errore di sintassi per CMake, e lascia il configure "incomplete"
        if nuove and nuove[-1].startswith("//"):
            nuove.pop()
        continue
    m = re.match(r"^(INTEL_MKL_DIR|INTEL_OMP_DIR):STRING=(.*)$", r)
    if m and m.group(2) != MKL_LIB:
        r = f"{m.group(1)}:STRING={MKL_LIB}"
        cambiate += 1
    nuove.append(r)
print(f"  cache: {tolte} voci MKL 'non trovato' da togliere, {cambiate} cartelle Intel da ripuntare")
if applica and not errori:
    scrivi(CACHE, "\n".join(nuove))  # UTF-8 senza BOM: con il BOM setup.py fallisce

if errori:
    print(f"\n{errori} errori: nulla e' stato scritto")
    sys.exit(1)
print("\napplicata" if applica else "\nprova a vuoto riuscita")

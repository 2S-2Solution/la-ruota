"""[VEGA-PATCH 48 1 ago] Deploy dello stack runtime COERENTE ROCm 5.7.

TheRock 7.14 e Marconi/5.7 non si mescolano: MIOpen del Marconi (patchato, l'unico che
carica) richiede rocblas 5.7 da 190 MB, mentre hipblas/hipsolver di TheRock richiedono
il rocblas 7.x. Qui si usa un solo mondo: Marconi per cio' che ha, ROCm 5.7 per il resto.
"""
import os
import shutil

DEST = r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib"
MARCONI = r"C:\rocm_5_7_expansion_pack\bin"
ROCM57 = r"C:\Program Files\AMD\ROCm\5.7\bin"
PROXY = r"C:\Strumenti\fa_gfx906_port\strada_C_proxy"

# nome nel torch/lib -> sorgente
PLAN = [
    ("amdhip64_6.dll", PROXY),          # proxy forwarder (nome richiesto da c10_hip)
    ("amdhip64_7.dll", MARCONI),        # shim Marconi
    ("amd_cmgr3.dll", MARCONI),
    ("amd_comgr_3.dll", MARCONI),
    ("hiprtc07013.dll", MARCONI),
    ("hiprtc-builtins07013.dll", MARCONI),
    ("hiprtc0701.dll", MARCONI),
    ("hiprtc-builtins0701.dll", MARCONI),
    ("MIOpen.dll", MARCONI),
    ("rocblas.dll", MARCONI),
    ("hipblaslt.dll", MARCONI),
    ("libhipblaslt.dll", MARCONI),
    ("hipblas.dll", ROCM57),
    ("libhipsparse.dll", ROCM57),
    ("hipsparse.dll", ROCM57),
    ("hipsolver.dll", ROCM57),
    ("hipfft.dll", ROCM57),
    ("rocfft.dll", ROCM57),
    ("rocsolver.dll", ROCM57),
    ("rocsparse.dll", ROCM57),
    ("hiprtc0507.dll", ROCM57),
    ("amd_comgr0507.dll", ROCM57),
]

done, skip = [], []
for name, src_dir in PLAN:
    src = os.path.join(src_dir, name)
    if not os.path.exists(src):
        skip.append(f"{name} (assente in {os.path.basename(src_dir)})")
        continue
    shutil.copy2(src, os.path.join(DEST, name))
    done.append(f"{name:28s} <- {src_dir}")

# amd_comgr.dll: MIOpen Marconi importa amd_cmgr3.dll, ma altri possono volere il nome piano
src = os.path.join(MARCONI, "amd_comgr_3.dll")
if os.path.exists(src):
    shutil.copy2(src, os.path.join(DEST, "amd_comgr.dll"))
    done.append("amd_comgr.dll (da amd_comgr_3)")

print(f"DEPLOYATE ({len(done)}):")
for d in done:
    print("  ", d)
if skip:
    print("SALTATE:")
    for s in skip:
        print("  ", s)

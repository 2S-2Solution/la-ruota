"""VEGA-PATCH 75 - via le esclusioni 58, 62 e 72: MIOpen e' corretta alla radice.

Il 20 ott la ruota usa una MIOpen ricompilata con le tre patch di miopen-gfx906
(backup_miopen_pre_patch_rocm_2026_10_20\\, miopen_ricompila.cmd, miopen_rinomina_comgr.py):
  - WrW3x3 (conv_sizes.inc, ramo reverse_inout): forzato il solver, C=3/5 -> 16/64,
    scarto 2,5-2,8e-07 (prima 1,2)                          -> via la VEGA-PATCH 58
  - V4R1 Dynamic WrW (argomenti trasposti, regressione 24815807e1): forzato il solver,
    5 forme compresa lotto 1 e Conv1d, <= 1,6e-06 (prima NaN) -> via la VEGA-PATCH 62
  - sotto-campionamento (lotto nella chiave): solver 1x1 riaccesi, lotti 2,4 / 4,2 /
    8,2,8 giusti (prima scarto 3,1)                         -> via la VEGA-PATCH 72
Le righe restano nel file, commentate, per poterle riaccendere in un attimo se servisse
(per esempio tornando alla MIOpen vecchia).

    python patch_togli_esclusioni_miopen.py --prova
    python patch_togli_esclusioni_miopen.py --applica
"""
import io
import os
import shutil
import sys

FILE = [
    r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\__init__.py",
    r"C:\LaRuota_workspace\pytorch_src\torch\__init__.py",
]
applica = "--applica" in sys.argv
NOTA = "# [VEGA-PATCH 75 - 20 ott 2026] spenta: MIOpen corretta alla radice (patch_togli_esclusioni_miopen.py)\n# "
RIGHE = [
    '_os_vega.environ.setdefault("MIOPEN_DEBUG_CONV_DIRECT_ASM_WRW3X3", "0")\n',
    '_os_vega.environ.setdefault("MIOPEN_DEBUG_CONV_IMPLICIT_GEMM_ASM_WRW_V4R1", "0")\n',
    '_os_vega.environ.setdefault("MIOPEN_DEBUG_CONV_DIRECT_ASM_WRW1X1", "0")\n',
    '_os_vega.environ.setdefault("MIOPEN_DEBUG_CONV_DIRECT_ASM_1X1U", "0")\n',
]

errori, nuovi = 0, {}
for f in FILE:
    t = io.open(f, encoding="utf-8", newline="").read()
    if "[VEGA-PATCH 75" in t:
        print(f"  {f}: gia' applicata")
        continue
    crlf = "\r\n" in t
    for riga in RIGHE:
        r, n = (riga, NOTA + riga) if not crlf else (riga.replace("\n", "\r\n"), (NOTA + riga).replace("\n", "\r\n"))
        if t.count(r) != 1:
            print(f"  ERRORE {f}: riga trovata {t.count(r)} volte: {riga.strip()}")
            errori += 1
            continue
        t = t.replace(r, n)
    nuovi[f] = t
    print(f"  ok: {f}")
if errori:
    sys.exit(1)
if applica:
    for f, t in nuovi.items():
        if not os.path.exists(f + ".bak_pre_vega75"):
            shutil.copy2(f, f + ".bak_pre_vega75")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

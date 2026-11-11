"""VEGA-PATCH 74 - una cache MIOpen propria per la ruota.

Dal 20 ott la ruota usa una MIOpen ricompilata con le tre patch di miopen-gfx906
(WrW3x3, V4R1, sotto-campionamento). La cache dei kernel di MIOpen ha per chiave il nome
del kernel, le opzioni e la VERSIONE di MIOpen, non il contenuto del sorgente: nella cache
condivisa (%USERPROFILE%\\.miopen) un conv3x3wrw compilato dalla MIOpen vecchia verrebbe
riusato, con il difetto dentro. E quella cache e' condivisa con ZLUDA, che usa la MIOpen
vecchia del pack con lo stesso numero di versione.

Quindi alla ruota una cache sua, nuova: MIOPEN_CUSTOM_CACHE_DIR (kernel compilati) e
MIOPEN_USER_DB_PATH (scelte dei solver e sintonizzazioni). Con setdefault: chi la imposta
a mano vince. Costo: la prima volta ogni forma si ricompila e si ricerca.

    python patch_miopen_cache_ruota.py --prova
    python patch_miopen_cache_ruota.py --applica
"""
import io
import os
import shutil
import sys

FILE = [
    r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\__init__.py",
    r"C:\LaRuota_workspace\pytorch_src\torch\__init__.py",
]
CARTELLA = r"C:\LaRuota_workspace\miopen_cache_ruota"
applica = "--applica" in sys.argv

ANCORA = '_os_vega.environ.setdefault("MIOPEN_DEBUG_CONV_DIRECT_ASM_1X1U", "0")\n'
AGGIUNTA = ANCORA + '''
# [VEGA-PATCH 74 - 20 ott 2026] cache MIOpen propria della ruota. La chiave dei kernel in
# cache e' nome + opzioni + versione di MIOpen, non il sorgente: nella cache condivisa con
# ZLUDA (stessa versione, MIOpen vecchia) un kernel corretto dalla MIOpen nuova verrebbe
# sostituito da quello vecchio. Spiegazione: C:\\LaRuota_workspace\\patch_miopen_cache_ruota.py
_os_vega.environ.setdefault("MIOPEN_CUSTOM_CACHE_DIR", r"C:\\LaRuota_workspace\\miopen_cache_ruota\\cache")
_os_vega.environ.setdefault("MIOPEN_USER_DB_PATH", r"C:\\LaRuota_workspace\\miopen_cache_ruota\\db")
'''

errori, nuovi = 0, {}
for f in FILE:
    t = io.open(f, encoding="utf-8", newline="").read()
    if "[VEGA-PATCH 74" in t:
        print(f"  {f}: gia' applicata")
        continue
    crlf = "\r\n" in t
    a, b = (ANCORA, AGGIUNTA) if not crlf else (ANCORA.replace("\n", "\r\n"), AGGIUNTA.replace("\n", "\r\n"))
    if t.count(a) != 1:
        print(f"  ERRORE {f}: ancora trovata {t.count(a)} volte (serve la VEGA-PATCH 72 prima)")
        errori += 1
        continue
    nuovi[f] = t.replace(a, b)
    print(f"  ok: {f}")
if errori:
    sys.exit(1)
if applica:
    for sotto in ("cache", "db"):
        os.makedirs(os.path.join(CARTELLA, sotto), exist_ok=True)
    for f, t in nuovi.items():
        if not os.path.exists(f + ".bak_pre_vega74"):
            shutil.copy2(f, f + ".bak_pre_vega74")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

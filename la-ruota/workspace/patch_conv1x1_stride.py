"""VEGA-PATCH 72 - conv 1x1 con stride > 1: due solver MIOpen esclusi.

Trovato con rocm-marconi il 20 ott. ConvAsmBwdWrW1x1 e ConvAsm1x1U, quando la
conv e' 1x1 con stride > 1, sotto-campionano con kernel SubSample/UpSample la cui cache NON
ha il lotto nella chiave. Se la stessa forma passa con un secondo lotto nello stesso
processo (basta l'ultimo lotto piu' corto di un'epoca su una rete con scorciatoie 1x1
stride 2):
  - lotto piu' grande dopo -> gradiente dei pesi sbagliato;
  - lotto piu' piccolo dopo -> scrittura oltre lo spazio di lavoro, memoria sporcata.
Nessun errore. Resta ConvAsm1x1UV2, che non sotto-campiona.
Banco: diag_battuta\\ordine_lotti.py <cache privata> 2,4  e  4,2.
Correzione vera: una patch a MIOpen (diag_battuta\\VEGA_sottocampiona_lotto_nella_chiave.patch,
da ricompilare e verificare); finche' non c'e', queste due esclusioni.

    python patch_conv1x1_stride.py --prova
    python patch_conv1x1_stride.py --applica
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

ANCORA = '_os_vega.environ.setdefault("MIOPEN_RNNFWD_EXP", "0")\n'
AGGIUNTA = ANCORA + '''
# [VEGA-PATCH 72 - 20 ott 2026] conv 1x1 con stride > 1: ConvAsmBwdWrW1x1 e ConvAsm1x1U
# sotto-campionano con una cache di kernel che non ha il lotto nella chiave. Se la stessa
# forma torna con un lotto diverso nello stesso processo (l'ultimo lotto corto di ogni
# epoca), il gradiente dei pesi esce sbagliato o la memoria vicina viene sporcata, senza
# errori. Resta ConvAsm1x1UV2. Spiegazione: C:\\LaRuota_workspace\\patch_conv1x1_stride.py
_os_vega.environ.setdefault("MIOPEN_DEBUG_CONV_DIRECT_ASM_WRW1X1", "0")
_os_vega.environ.setdefault("MIOPEN_DEBUG_CONV_DIRECT_ASM_1X1U", "0")
'''

errori, nuovi = 0, {}
for f in FILE:
    t = io.open(f, encoding="utf-8", newline="").read()
    if "[VEGA-PATCH 72" in t:
        print(f"  {f}: gia' applicata")
        continue
    crlf = "\r\n" in t
    a, b = (ANCORA, AGGIUNTA) if not crlf else (ANCORA.replace("\n", "\r\n"), AGGIUNTA.replace("\n", "\r\n"))
    if t.count(a) != 1:
        print(f"  ERRORE {f}: ancora trovata {t.count(a)} volte (serve la VEGA-PATCH 71 prima)")
        errori += 1
        continue
    nuovi[f] = t.replace(a, b)
    print(f"  ok: {f}")
if errori:
    sys.exit(1)
if applica:
    for f, t in nuovi.items():
        if not os.path.exists(f + ".bak_pre_vega72"):
            shutil.copy2(f, f + ".bak_pre_vega72")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

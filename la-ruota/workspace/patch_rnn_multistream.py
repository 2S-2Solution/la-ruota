"""VEGA-PATCH 71 - LSTM di MIOpen: niente soluzioni RNN a piu' stream.

Segnalato da un utente il 17 ott:
LSTM a uno strato, >= 32 passi, dal SECONDO indietro i gradienti dei pesi escono a zero.

Causa (MIOpen, src/rnn/selector.cpp): con seqLen >= 32 MIOpen sceglie
RNNModularMultiStreamBWD e RNNModularMultiStreamBWWeights, che distribuiscono il lavoro su
stream di servizio e poi fanno ASPETTARE lo stream di partenza. In PyTorch quello e' lo
stream nullo, e il runtime del driver rifiuta hipStreamWaitEvent sullo stream nullo
(VEGA-PATCH 69). Le attese partono da dentro MIOpen, quindi il ponte della 69 non le
copre; l'errore viene ignorato e lo stream nullo legge il risultato prima che sia pronto.
Prova: prova_lstm_multistream.py, 5 indietro su 5 giusti con le variabili, 1 su 5 senza.

Rimedio: le variabili di MIOpen che fanno scegliere la soluzione a uno stream.
  MIOPEN_RNNBWDMS_EXP=0   indietro sui dati
  MIOPEN_RNNBWMS_EXP=0    indietro sui pesi
  MIOPEN_RNNFWD_EXP=0     avanti (MIOpen lo usa solo per LSTM a piu' strati, che la
                          VEGA-PATCH 59 gia' esclude: qui per sicurezza)
Come le 58 e 62, in torch/__init__.py con setdefault, prima di ogni uso di MIOpen.

    python patch_rnn_multistream.py --prova
    python patch_rnn_multistream.py --applica
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

ANCORA = '_os_vega.environ.setdefault("MIOPEN_DEBUG_CONV_IMPLICIT_GEMM_ASM_WRW_V4R1", "0")\n'
AGGIUNTA = ANCORA + '''
# [VEGA-PATCH 71 - 17 ott 2026] LSTM di MIOpen: niente soluzioni RNN a piu' stream.
# Con >= 32 passi MIOpen distribuisce l'indietro su stream di servizio e poi fa aspettare
# lo stream di partenza, che in PyTorch e' lo stream NULLO: il runtime del driver rifiuta
# quell'attesa (vedi VEGA-PATCH 69) e i gradienti dei pesi escono a zero dal secondo
# indietro in poi, senza alcun errore. Con queste tre la soluzione e' a uno stream.
# Spiegazione: C:\\LaRuota_workspace\\patch_rnn_multistream.py
_os_vega.environ.setdefault("MIOPEN_RNNBWDMS_EXP", "0")
_os_vega.environ.setdefault("MIOPEN_RNNBWMS_EXP", "0")
_os_vega.environ.setdefault("MIOPEN_RNNFWD_EXP", "0")
'''

errori = 0
nuovi = {}
for f in FILE:
    t = io.open(f, encoding="utf-8", newline="").read()
    if "[VEGA-PATCH 71" in t:
        print(f"  {f}: gia' applicata")
        continue
    crlf = "\r\n" in t
    a, b = (ANCORA, AGGIUNTA) if not crlf else (ANCORA.replace("\n", "\r\n"), AGGIUNTA.replace("\n", "\r\n"))
    if t.count(a) != 1:
        print(f"  ERRORE {f}: ancora trovata {t.count(a)} volte")
        errori += 1
        continue
    nuovi[f] = t.replace(a, b)
    print(f"  ok: {f}")
if errori:
    sys.exit(1)
if applica:
    for f, t in nuovi.items():
        if not os.path.exists(f + ".bak_pre_vega71"):
            shutil.copy2(f, f + ".bak_pre_vega71")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

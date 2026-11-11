"""Tutti i banchi della ruota, in fila, con una riga di esito ciascuno.

    python regressione_completa.py

Le convoluzioni si provano con il banco di miopen-gfx906 (banchi\\prova_conv_miopen.py): indicare
la cartella del repository con la variabile MIOPEN_GFX906, altrimenti quel banco si salta.

Ogni banco gira in un processo suo (come lo lancerebbe un utente); si conserva solo la
riga che riassume l'esito. Il log completo di ciascuno va in regressione_log\\.
"""
import os
import re
import subprocess
import sys
import time

QUI = r"C:\LaRuota_workspace"
PY = os.path.join(QUI, r"venv_build\Scripts\python.exe")
LOG = os.path.join(QUI, "regressione_log")
os.makedirs(LOG, exist_ok=True)

BANCHI = [
    ("allocazione, matmul, GEMM fp16", ["prova_allocazione_gpu.py"], r"gemm fp16:.*|ERR.*|FAIL.*"),
    ("conv MIOpen (9 prove)", [os.path.join(os.environ.get("MIOPEN_GFX906", ""), "banchi", "prova_conv_miopen.py")], r"^\s*(OK|ERR|FAIL)"),
    ("ricorrenti, 13 varianti", ["prova_lstm_gradzki.py"], r"superate.*"),
    ("LSTM, indietro ripetuti", ["prova_lstm_passi_ripetuti.py"], r"\d+ su \d+ ok"),
    ("LSTM caso minimo", ["prova_lstm_multistream.py"], r"ESITO.*"),
    ("RNN a piu' strati in MIOpen", ["prova_rnn_multistrato.py"], r"\d+ su \d+ ok|MIOpen .* ms.*"),
    ("censimento della ruota (98)", ["censimento_ruota.py"], r"^\s*(ok|SBAGLIATA|ECCEZIONE)\s+\d+"),
    ("algebra lineare GPU (20)", ["censimento_linalg_gpu.py"], r"\d+ su \d+ corrette.*"),
    ("cholesky e lstsq (63)", ["prova_cholesky_lstsq_gpu.py"], r"\d+ su \d+ ok"),
    ("algebra lineare, n da 16 a 512 (13)", ["battuta_linalg_dimensioni.py"], r"\d+ su \d+ operazioni.*|^\s*ERR.*"),
    ("eigh e svd (93)", ["prova_eigh_svd_78.py"], r"\d+ su \d+ giusti|^\s*ERR.*"),
    ("softmax/log_softmax, 3 tipi, avanti e indietro (13)", ["prova_softmax_righe.py"], r"\d+ su \d+ giusti|^\s*ERR.*"),
    ("stream ed eventi (9)", ["prova_stream_eventi.py"], r"\d+ su \d+ ok"),
    ("TorchScript torch.cuda (2)", ["prova_torchscript_cuda.py"], r"\d+ su \d+ ok"),
    ("MKL, LAPACK, numpy (21)", ["verifica_mkl_numpy2.py"], r"matmul CPU.*|\d+ su \d+ ok.*"),
    ("flash attention collegata (11)", [r"ruota_flash\prova_ruota_flash.py"], r"\d+ su \d+ ok|B2 H16.*"),
    ("conv 1x1 stride, lotti 2,4 (produzione)", [r"diag_battuta\ordine_lotti.py", os.path.join(LOG, "cache_ordine"), "2,4"], r"ESITO.*"),
]

inizio = time.time()
for nome, argomenti, filtro in BANCHI:
    if "ordine_lotti" in argomenti[0]:
        os.makedirs(argomenti[1], exist_ok=True)
    if not os.path.isfile(os.path.join(QUI, argomenti[0])):
        print(f"== {nome}  SALTATO: {argomenti[0]} non trovato", flush=True)
        continue
    t0 = time.time()
    p = subprocess.run([PY, "-u"] + [os.path.join(QUI, argomenti[0])] + argomenti[1:],
                       cwd=os.path.dirname(os.path.join(QUI, argomenti[0])),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    testo = p.stdout + p.stderr
    file_log = os.path.join(LOG, re.sub(r"\W+", "_", nome) + ".log")
    open(file_log, "w", encoding="utf-8").write(testo)
    righe = [r.strip() for r in testo.splitlines() if re.search(filtro, r)]
    print(f"== {nome}  ({time.time() - t0:.0f} s, rc {p.returncode})", flush=True)
    for r in righe[-4:]:
        print(f"     {r[:150]}", flush=True)
print(f"\nfine in {(time.time() - inizio) / 60:.1f} minuti", flush=True)

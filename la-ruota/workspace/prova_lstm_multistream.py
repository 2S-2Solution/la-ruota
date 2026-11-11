"""Il caso minimo delun utente: LSTM a uno strato, 35 passi, tre indietro di fila.

    python -u prova_lstm_multistream.py

Con >= 32 passi MIOpen sceglie le soluzioni RNN a PIU' STREAM (rnn/selector.cpp:
RNNBwdMSIsFast, RNNBwWeightMSIsFast), che fanno aspettare lo stream nullo: il runtime
del driver rifiuta l'attesa e i gradienti escono a zero. MIOPEN_RNNBWDMS_EXP=0 e
MIOPEN_RNNBWMS_EXP=0 fanno scegliere la soluzione a uno stream.
"""
import copy
import os

import torch

print("MIOPEN_RNNBWDMS_EXP =", os.environ.get("MIOPEN_RNNBWDMS_EXP"),
      "| MIOPEN_RNNBWMS_EXP =", os.environ.get("MIOPEN_RNNBWMS_EXP"), flush=True)
torch.manual_seed(0)
m = torch.nn.LSTM(1, 20, batch_first=True)
x, w = torch.randn(64, 35, 1), torch.randn(64, 35, 20)
r = copy.deepcopy(m).double()
(r(x.double())[0] * w.double()).sum().backward()
g = copy.deepcopy(m).cuda()
peggiore = 0.0
for i in range(5):
    g.zero_grad()
    (g(x.cuda())[0] * w.cuda()).sum().backward()
    d = max(((p.grad.double().cpu() - q.grad).abs().max() / q.grad.abs().max()).item()
            for p, q in zip(g.parameters(), r.parameters()))
    peggiore = max(peggiore, d)
    print(f"  indietro {i}: peggior scarto relativo sui pesi {d:.1e}", flush=True)
print("ESITO:", "giusto" if peggiore < 1e-4 else "SBAGLIATO", flush=True)

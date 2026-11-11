"""LSTM a uno strato (percorso MIOpen) su piu' passi all'indietro, GPU contro CPU.

    python prova_lstm_passi_ripetuti.py

Segnalato dalun utente il 17 ott: con sequenze >= 32 passi, dal SECONDO passo
all'indietro i gradienti dei pesi escono a zero. prova_lstm_gradzki.py faceva un solo
passo, per questo non lo vedeva.
"""
import copy

import torch
import torch.nn as nn

torch.manual_seed(0)
esiti = []


def scarto(a, b):
    return ((a - b).abs().max() / b.abs().max().clamp_min(1e-6)).item()


def prova(nome, T, passi=3, strati=1, batch_first=True, bidir=False, stream=False):
    lstm_cpu = nn.LSTM(16, 32, num_layers=strati, batch_first=batch_first, bidirectional=bidir)
    lstm_gpu = copy.deepcopy(lstm_cpu).cuda()
    s = torch.cuda.Stream() if stream else None
    peggiore, zeri = 0.0, False
    for passo in range(passi):
        x = torch.randn(4, T, 16) if batch_first else torch.randn(T, 4, 16)
        w = torch.randn(4, T, 32 * (2 if bidir else 1)) if batch_first else torch.randn(T, 4, 32 * (2 if bidir else 1))
        for m in (lstm_cpu, lstm_gpu):
            m.zero_grad()
        (lstm_cpu(x)[0] * w).sum().backward()
        if s is not None:
            s.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(s):
                (lstm_gpu(x.cuda())[0] * w.cuda()).sum().backward()
            torch.cuda.current_stream().wait_stream(s)
        else:
            (lstm_gpu(x.cuda())[0] * w.cuda()).sum().backward()
        for (n, pc), pg in zip(lstm_cpu.named_parameters(), lstm_gpu.parameters()):
            d = scarto(pg.grad.cpu(), pc.grad)
            peggiore = max(peggiore, d)
            if pg.grad.abs().max().item() == 0.0:
                zeri = True
    ok = peggiore < 1e-3 and not zeri
    esiti.append(ok)
    print(f"  {'OK ' if ok else 'ERR'}  {nome:46s} peggior scarto {peggiore:.1e}" + ("  GRADIENTI A ZERO" if zeri else ""))


for T in (16, 32, 64, 128):
    prova(f"1 strato, T={T}, 3 passi", T)
prova("1 strato, T=64, batch_first=False", 64, batch_first=False)
prova("1 strato, T=64, bidirezionale", 64, bidir=True)
prova("1 strato, T=64, su stream secondario", 64, stream=True)
print(f"\n{sum(esiti)} su {len(esiti)} ok")

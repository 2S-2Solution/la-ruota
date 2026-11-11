"""Verifica della VEGA-PATCH 73: RNN a piu' strati di nuovo in MIOpen (la 59 e' tolta).

    python -u prova_rnn_multistrato.py

LSTM, GRU e RNN a 2-3 strati, alle soglie di agosto per cui era nata la 59 (hidden >= 160,
passi >= 32, lotto >= 4), tre indietro di fila, contro la CPU; bidirezionale e sequenze
impacchettate; poi il tempo contro il percorso nativo (cudnn spento).
"""
import copy
import time

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

torch.manual_seed(0)
esiti = []


def scarto(a, b):
    return ((a - b).abs().max() / b.abs().max().clamp_min(1e-6)).item()


def caso(nome, tipo, I=16, H=32, strati=2, T=16, B=4, bidir=False, impacchetta=False, passi=3):
    cpu = tipo(I, H, num_layers=strati, batch_first=True, bidirectional=bidir)
    gpu = copy.deepcopy(cpu).cuda()
    peggiore = 0.0
    for _ in range(passi):
        x = torch.randn(B, T, I)
        lun = torch.randint(T // 2, T + 1, (B,))
        lun[0] = T
        for m in (cpu, gpu):
            m.zero_grad()
        uscite = []
        for m, dev in ((cpu, "cpu"), (gpu, "cuda")):
            xx = x.to(dev)
            if impacchetta:
                p = pack_padded_sequence(xx, lun, batch_first=True, enforce_sorted=False)
                y, _ = m(p)
                y, _ = pad_packed_sequence(y, batch_first=True, total_length=T)
            else:
                y, _ = m(xx)
            w = torch.randn_like(y, device="cpu").to(dev) if dev == "cpu" else w_g
            if dev == "cpu":
                w_g = w.cuda()
            (y * w).sum().backward()
            uscite.append(y)
        peggiore = max(peggiore, scarto(uscite[1].detach().cpu(), uscite[0].detach()))
        for pc, pg in zip(cpu.parameters(), gpu.parameters()):
            peggiore = max(peggiore, scarto(pg.grad.cpu(), pc.grad))
    ok = peggiore < 1e-3
    esiti.append(ok)
    print(f"  {'OK ' if ok else 'ERR'}  {nome:52s} peggior scarto {peggiore:.1e}", flush=True)


# le soglie di agosto
caso("LSTM 2 strati, hidden 160", nn.LSTM, H=160)
caso("LSTM 2 strati, hidden 256, lotto 32", nn.LSTM, H=256, B=32)
caso("LSTM 2 strati, 48 passi, lotto 32", nn.LSTM, T=48, B=32)
caso("LSTM 3 strati, hidden 256, 64 passi, lotto 16", nn.LSTM, H=256, T=64, B=16, strati=3)
caso("GRU 2 strati, hidden 256, 48 passi, lotto 16", nn.GRU, H=256, T=48, B=16)
caso("RNN tanh 2 strati, hidden 256, 48 passi, lotto 16", nn.RNN, H=256, T=48, B=16)
caso("LSTM 2 strati bidirezionale, hidden 160, 48 passi", nn.LSTM, H=160, T=48, B=8, bidir=True)
caso("LSTM 2 strati, sequenze impacchettate, 40 passi", nn.LSTM, H=64, T=40, B=8, impacchetta=True)

# tempo: MIOpen (ora) contro il percorso nativo (quello della 59)
m = nn.LSTM(128, 256, num_layers=2, batch_first=True).cuda()
x = torch.randn(32, 64, 128, device="cuda")


def passo():
    m.zero_grad()
    y, _ = m(x)
    y.sum().backward()


def misura():
    for _ in range(3):
        passo()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(10):
        passo()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) / 10 * 1000


t_miopen = misura()
torch.backends.cudnn.enabled = False
t_nativo = misura()
torch.backends.cudnn.enabled = True
print(f"\n  LSTM 2x256, lotto 32, 64 passi, avanti+indietro: MIOpen {t_miopen:.1f} ms, "
      f"nativo {t_nativo:.1f} ms -> {t_nativo / t_miopen:.2f}x", flush=True)

# sleep
torch.cuda.synchronize()
t0 = time.perf_counter()
torch.cuda._sleep(200_000_000)
torch.cuda.synchronize()
dt = (time.perf_counter() - t0) * 1000
ok_sleep = dt > 20
esiti.append(ok_sleep)
print(f"  {'OK ' if ok_sleep else 'ERR'}  torch.cuda._sleep(2e8 cicli): {dt:.1f} ms (prima: 0)", flush=True)

# ricerca dei solver con lo spazio di lavoro col ripiego
torch.backends.cudnn.benchmark = True
c = nn.Conv2d(64, 128, 3, padding=1).cuda()
y = c(torch.randn(16, 64, 56, 56, device="cuda"))
y.sum().backward()
torch.cuda.synchronize()
esiti.append(True)
print("  OK   conv con cudnn.benchmark=True (ricerca dei solver): eseguita", flush=True)

print(f"\n{sum(esiti)} su {len(esiti)} ok", flush=True)

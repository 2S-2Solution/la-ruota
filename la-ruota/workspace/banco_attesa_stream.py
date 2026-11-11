"""Quanto resta ferma la CPU in un wait_stream verso lo stream predefinito (nullo).

    python banco_attesa_stream.py

Su uno stream secondario si accoda ~300 ms di lavoro; poi lo stream predefinito lo
aspetta (wait_stream / wait_event) e consuma il risultato. Si misura:
  - quanto dura la chiamata di attesa sulla CPU (con la VEGA-PATCH 69 originale, che
    usava hipEventSynchronize, durava tutto il lavoro; con il ponte deve essere ~0);
  - che il risultato letto dallo stream predefinito sia quello finito.
"""
import time

import torch

# UN SOLO lancio lungo: una matmul grande (rocBLAS la fa in un kernel). Con tante
# matmul piccole la CPU resterebbe indietro gia' durante l'accodamento (la coda dei
# comandi e' limitata) e l'attesa misurerebbe solo la coda finale. torch.cuda._sleep
# qui non serve: su questa build esce subito.
M = torch.randn(12288, 12288, device="cuda")
x = torch.randn(256, 256, device="cuda")
M @ M
torch.cuda.synchronize()
t0 = time.perf_counter()
M @ M
torch.cuda.synchronize()
DURATA = (time.perf_counter() - t0) * 1000


def lavoro_lungo(s):
    with torch.cuda.stream(s):
        acc = torch.zeros_like(x)
        P = M @ M
        acc.fill_(7.0)   # ultimo passo: chi legge deve vedere 7
        acc.add_(P[0, 0] * 0)
    return acc


esiti = []
for nome, attesa in (("wait_stream", lambda cur, s, ev: cur.wait_stream(s)),
                     ("wait_event", lambda cur, s, ev: cur.wait_event(ev)),
                     ("Event.wait", lambda cur, s, ev: ev.wait(cur))):
    cpu, giusti = [], 0
    for _ in range(5):
        torch.cuda.synchronize()
        s = torch.cuda.Stream()
        s.wait_stream(torch.cuda.current_stream())
        acc = lavoro_lungo(s)
        ev = s.record_event()
        cur = torch.cuda.current_stream()
        t0 = time.perf_counter()
        attesa(cur, s, ev)
        cpu.append((time.perf_counter() - t0) * 1000)
        letto = acc.sum().item() / acc.numel()   # sullo stream predefinito
        giusti += int(letto == 7.0)
    esiti.append(giusti == 5)
    print(f"  {nome:12s} lavoro {DURATA:.0f} ms | CPU ferma nell'attesa: "
          f"max {max(cpu):6.1f} ms, min {min(cpu):6.1f} ms | risultato finito {giusti}/5")
print(f"\n{sum(esiti)} su {len(esiti)} con il risultato giusto")

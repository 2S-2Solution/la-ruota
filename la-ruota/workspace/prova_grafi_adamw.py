"""Grafi HIP (torch.cuda.CUDAGraph) e AdamW fuso / foreach sulla ruota: correttezza e tempi per le MLP applicativi.

    python -u prova_grafi_adamw.py [--tempi]

MLP 31 -> 128 -> 64 -> 32 -> 1 con BatchNorm1d e ReLU, lotto 256, BCE, AdamW.
Correttezza: 20 passi con ciascun modo contro il ciclo normale (stessi pesi, stessi lotti).
"""
import sys
import time

import torch
import torch.nn as nn

TEMPI = "--tempi" in sys.argv
torch.manual_seed(0)
X = torch.randn(64, 256, 31, device="cuda")
Y = (torch.rand(64, 256, 1, device="cuda") > 0.5).float()


def rete():
    torch.manual_seed(1)
    strati, d = [], 31
    for h in (128, 64, 32):
        strati += [nn.Linear(d, h), nn.BatchNorm1d(h), nn.ReLU()]
        d = h
    strati += [nn.Linear(d, 1), nn.Sigmoid()]
    return nn.Sequential(*strati).cuda()


def normale(passi, **opz):
    m = rete()
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, **opz)
    for i in range(passi):
        opt.zero_grad(set_to_none=True)
        nn.functional.binary_cross_entropy(m(X[i % 64]), Y[i % 64]).backward()
        opt.step()
    return m


def con_grafo(passi):
    m = rete()
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, capturable=True, foreach=True)
    xs, ys = X[0].clone(), Y[0].clone()
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s):            # riscaldamento fuori dal grafo, come da documentazione
        for i in range(3):
            opt.zero_grad(set_to_none=True)
            nn.functional.binary_cross_entropy(m(xs), ys).backward()
            opt.step()
    torch.cuda.current_stream().wait_stream(s)
    # ricomincio dagli stessi pesi e stato del normale: ricreo tutto e catturo
    m2 = rete()
    m.load_state_dict(m2.state_dict())
    opt.state.clear()
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, capturable=True, foreach=True)
    g = torch.cuda.CUDAGraph()
    opt.zero_grad(set_to_none=True)
    with torch.cuda.graph(g):
        perdita = nn.functional.binary_cross_entropy(m(xs), ys)
        perdita.backward()
        opt.step()
    # la cattura non esegue: il primo passo vero e' il primo replay
    m.load_state_dict(m2.state_dict())
    for st in opt.state.values():
        for k, v in st.items():
            if torch.is_tensor(v):
                v.zero_()
    for i in range(passi):
        xs.copy_(X[i % 64])
        ys.copy_(Y[i % 64])
        g.replay()
    return m, g, xs, ys


def scarto(a, b):
    return max((p - q).abs().max().item() for p, q in zip(a.state_dict().values(), b.state_dict().values())
               if p.is_floating_point())


rif = normale(20, foreach=False)
torch.use_deterministic_algorithms(True)   # confronti esatti: niente atomiche di hipBLAS
rif = normale(20, foreach=False)
# fused=True escluso: manda in crash il processo (0xC0000005), vedi guida A3
for nome, f in (("foreach", lambda: normale(20, foreach=True)),):
    try:
        print(f"  AdamW {nome:10s} contro ciclo semplice: scarto pesi {scarto(f(), rif):.1e}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"  AdamW {nome:10s} ERRORE {type(e).__name__}: {str(e)[:150]}", flush=True)
try:
    mg, g, xs, ys = con_grafo(20)
    print(f"  grafo HIP (avanti+indietro+AdamW catturati) contro ciclo: scarto pesi {scarto(mg, rif):.1e}", flush=True)
except Exception as e:  # noqa: BLE001
    g = None
    print(f"  grafo HIP ERRORE {type(e).__name__}: {str(e)[:200]}", flush=True)

if TEMPI:
    def cronometra(f, n=200):
        f()
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(n):
            f()
        torch.cuda.synchronize()
        return (time.perf_counter() - t0) / n * 1000
    for nome, opz in (("normale", {"foreach": False}), ("foreach", {"foreach": True})):
        m = rete()
        opt = torch.optim.AdamW(m.parameters(), lr=1e-3, **opz)

        def passo():
            opt.zero_grad(set_to_none=True)
            nn.functional.binary_cross_entropy(m(X[0]), Y[0]).backward()
            opt.step()
        print(f"  passo {nome:8s} {cronometra(passo):.2f} ms", flush=True)
    if g is not None:
        print(f"  passo grafo    {cronometra(g.replay):.2f} ms", flush=True)

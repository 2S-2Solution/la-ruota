"""Verifica della VEGA-PATCH 76: copy_ di un tensore trasposto con il kernel a tessere.

    python -u prova_copia_trasposta.py

Correttezza contro la CPU (copia bit a bit: deve coincidere ESATTAMENTE) per i tipi da 2 e
4 byte, nei due versi (sorgente trasposta / destinazione trasposta), forme irregolari, a
lotti, sotto e sopra la soglia di 1 MB; poi la banda sulle forme del passo di Qwen3.5.
"""
import time

import torch

torch.manual_seed(0)
esiti = []


def prova(nome, f):
    try:
        d = f()
        esiti.append(True)
        print(f"  OK    {nome:58s} {d}", flush=True)
    except Exception as e:  # noqa: BLE001
        esiti.append(False)
        print(f"  ERR   {nome:58s} {type(e).__name__}: {str(e)[:120]}", flush=True)


def dati(forma, dt):
    if dt.is_floating_point:
        return torch.randn(*forma, dtype=torch.float32).to(dt)
    return torch.randint(-1000, 1000, forma, dtype=dt)


def verso_a(forma, dt):
    # sorgente trasposta, destinazione contigua: x.transpose(-1,-2).contiguous()
    x = dati(forma, dt)
    g = x.cuda().transpose(-1, -2).contiguous()
    assert torch.equal(g.cpu(), x.transpose(-1, -2).contiguous()), "valori diversi"
    return "identico"


def verso_b(forma, dt):
    # sorgente contigua, destinazione trasposta: y.transpose(-1,-2).copy_(x)
    x = dati(forma, dt)
    *b, r, c = forma
    y = torch.empty(*b, c, r, dtype=dt, device="cuda")
    y.transpose(-1, -2).copy_(x.cuda())
    assert torch.equal(y.cpu(), x.transpose(-1, -2).contiguous()), "valori diversi"
    return "identico"


for dt in (torch.float16, torch.bfloat16, torch.float32, torch.int32, torch.int16):
    n = str(dt)[6:]
    prova(f"{n} 1024x2048, verso a", lambda: verso_a((1024, 2048), dt))
    prova(f"{n} 1024x2048, verso b", lambda: verso_b((1024, 2048), dt))
for forma in ((1001, 1537), (1537, 1001), (4097, 255), (63, 70000), (8, 300, 513), (3, 2, 511, 1023)):
    prova(f"fp16 {forma} irregolare, verso a", lambda: verso_a(forma, torch.float16))
    prova(f"fp32 {forma} irregolare, verso b", lambda: verso_b(forma, torch.float32))
prova("fp16 64x64 (sotto 1 MB: percorso di sempre)", lambda: verso_a((64, 64), torch.float16))
prova("fp16 [1, 8192, 512] (Qwen3.5)", lambda: verso_a((1, 8192, 512), torch.float16))


def sovrapposizione():
    x = torch.randn(1024, 1024, device="cuda", dtype=torch.float16)
    atteso = x.t().contiguous().cpu()
    x.copy_(x.t().clone())          # niente sovrapposizione: clone
    assert torch.equal(x.cpu(), atteso)
    return "identico"


prova("copia su se' stesso tramite clone", sovrapposizione)


def banda(forma, dt=torch.float16, ripeti=20):
    x = torch.randn(*forma, device="cuda", dtype=torch.float32).to(dt)
    s = x.transpose(-1, -2)
    y = torch.empty(s.shape, device="cuda", dtype=dt)
    y.copy_(s)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(ripeti):
        y.copy_(s)
    torch.cuda.synchronize()
    dt_s = (time.perf_counter() - t0) / ripeti
    return 2 * x.numel() * x.element_size() / dt_s / 1e9, dt_s * 1000


print("\n  banda della copia trasposta (lettura + scrittura):", flush=True)
for forma in ((4096, 8192), (1, 8192, 512), (16, 1024, 1024), (2048, 2048)):
    gbs, ms = banda(forma)
    print(f"    fp16 {str(forma):18s} {gbs:7.1f} GB/s  ({ms:.3f} ms)", flush=True)
gbs, ms = banda((4096, 4096), torch.float32)
print(f"    fp32 (4096, 4096)       {gbs:7.1f} GB/s  ({ms:.3f} ms)", flush=True)
print(f"\n{sum(esiti)} su {len(esiti)} ok", flush=True)

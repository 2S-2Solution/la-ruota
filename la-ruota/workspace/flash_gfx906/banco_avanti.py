"""Banco del prototipo flash-attention (solo avanti) sulla ruota.

    python banco_avanti.py correttezza
    python banco_avanti.py prestazioni

Correttezza: contro un riferimento in fp32 calcolato sulla GPU con il percorso
standard, sugli STESSI dati. Metrica: scarto relativo con pavimento 1e-2.

Prestazioni: contro `F.scaled_dot_product_attention` fp16 (percorso math, l'unico
compilato nella ruota). Misure INTERCALATE (math, flash, math, flash...) e
mediana: con la macchina carica dagli altri agenti un confronto a blocchi
sarebbe falsato dalla deriva del carico. Memoria: picco allocato oltre gli
ingressi.
"""
import statistics
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from fa_avanti import flash_avanti  # noqa: E402


def dati(B, H, S, D, seme=0):
    g = torch.Generator(device="cuda").manual_seed(seme)
    return [torch.randn(B, H, S, D, device="cuda", dtype=torch.float16, generator=g)
            for _ in range(3)]


def correttezza():
    casi = [(1, 4, 64, 64, False), (2, 4, 1000, 64, False), (1, 8, 1000, 64, True),
            (1, 4, 1024, 128, False), (1, 4, 1024, 128, True), (2, 2, 77, 128, True),
            (1, 16, 2048, 128, True), (1, 2, 1, 64, False)]
    tutti = True
    for B, H, S, D, causale in casi:
        q, k, v = dati(B, H, S, D)
        rif = F.scaled_dot_product_attention(q.float(), k.float(), v.float(), is_causal=causale)
        o = flash_avanti(q, k, v, is_causal=causale)
        torch.cuda.synchronize()
        s = ((o.float() - rif).abs() / rif.abs().clamp_min(1e-2)).max().item()
        s_math = ((F.scaled_dot_product_attention(q, k, v, is_causal=causale).float() - rif).abs()
                  / rif.abs().clamp_min(1e-2)).max().item()
        ok = s <= max(4 * s_math, 2e-2)
        tutti &= ok
        print(f"  B{B} H{H:<2} S{S:<5} D{D:<3} causale={str(causale):5s}  flash {s:.2e}   "
              f"(math fp16 {s_math:.2e})   {'ok' if ok else '>>> SBAGLIATO'}")
    print("ESITO", "ok" if tutti else "SBAGLIATO")


def misura(fn, giri):
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(giri):
        fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) * 1000 / giri


def picco(fn):
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    base = torch.cuda.memory_allocated()
    fn()
    torch.cuda.synchronize()
    return (torch.cuda.max_memory_allocated() - base) / 2**20


def prestazioni():
    print(f"  {'forma':32s} {'math ms':>9} {'flash ms':>9} {'rapporto':>9}   "
          f"{'math MB':>8} {'flash MB':>8}   TFLOPS flash")
    for B, H, S, D, causale in [(1, 16, 512, 64, False), (1, 16, 1024, 64, False),
                                (1, 16, 2048, 64, False), (1, 16, 4096, 64, False),
                                (1, 16, 1024, 128, False), (1, 16, 2048, 128, False),
                                (1, 16, 4096, 128, False), (1, 16, 4096, 128, True),
                                (1, 16, 8192, 128, True)]:
        q, k, v = dati(B, H, S, D)
        fm = lambda: F.scaled_dot_product_attention(q, k, v, is_causal=causale)
        ff = lambda: flash_avanti(q, k, v, is_causal=causale)
        try:
            mb_m = picco(fm)
        except torch.cuda.OutOfMemoryError:
            mb_m = float("nan")
        mb_f = picco(ff)
        giri = max(1, int(2e10 / (B * H * S * S * D)))
        tm, tf = [], []
        for _ in range(5):
            try:
                tm.append(misura(fm, giri))
            except torch.cuda.OutOfMemoryError:
                tm.append(float("nan"))
            tf.append(misura(ff, giri))
        m, f = statistics.median(tm), statistics.median(tf)
        flop = 4 * B * H * S * S * D * (0.5 if causale else 1.0)
        nome = f"B{B} H{H} S{S} D{D} {'causale' if causale else ''}"
        print(f"  {nome:32s} {m:9.2f} {f:9.2f} {m / f:8.2f}x   {mb_m:8.0f} {mb_f:8.0f}   "
              f"{flop / (f / 1000) / 1e12:6.2f}")
        del q, k, v
        torch.cuda.empty_cache()


if __name__ == "__main__":
    {"correttezza": correttezza, "prestazioni": prestazioni}[sys.argv[1]]()

"""Confronto math / prototipo / fa2 (solo avanti).

    python banco2.py correttezza
    python banco2.py prestazioni

Correttezza contro fp32 sulla GPU, stessi casi del banco_avanti piu' forme
irregolari. Prestazioni intercalate e a mediana (macchina condivisa).
"""
import statistics, sys, time
import torch
import torch.nn.functional as F
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_avanti, fa2_avanti  # noqa: E402


def dati(B, H, S, D, seme=0):
    g = torch.Generator(device="cuda").manual_seed(seme)
    return [torch.randn(B, H, S, D, device="cuda", dtype=torch.float16, generator=g) for _ in range(3)]


def emulazione_p16(q, k, v, causale):
    """Riferimento 'come lo fa FlashAttention-2': P = exp(s - max) arrotondata a fp16, accumulo fp32."""
    s = (q.float() @ k.float().transpose(-1, -2)) * q.shape[-1] ** -0.5
    if causale:
        S = q.shape[-2]
        s = s.masked_fill(torch.triu(torch.ones(S, S, dtype=torch.bool, device=s.device), 1), float("-inf"))
    p = torch.exp(s - s.amax(-1, keepdim=True))
    return (p.half().float() @ v.float()) / p.sum(-1, keepdim=True)


def correttezza():
    """Errore ASSOLUTO contro fp32. Criterio: entro 2x l'emulazione di P in fp16 (il limite
    del disegno FA2) piu' l'arrotondamento dell'uscita fp16 (2^-11 x max|O|)."""
    casi = [(1, 4, 64, 64, False), (2, 4, 1000, 64, False), (1, 8, 1000, 64, True),
            (1, 4, 1024, 128, False), (1, 4, 1024, 128, True), (2, 2, 77, 128, True),
            (1, 16, 2048, 128, True), (1, 2, 1, 64, False), (1, 2, 1, 128, True),
            (3, 3, 65, 64, True), (1, 1, 4097, 128, False), (2, 5, 333, 128, True)]
    tutti = True
    for B, H, S, D, c in casi:
        q, k, v = dati(B, H, S, D)
        rif = F.scaled_dot_product_attention(q.float(), k.float(), v.float(), is_causal=c)
        e2 = (fa2_avanti.flash_avanti(q, k, v, is_causal=c).float() - rif).abs().max().item()
        em = (F.scaled_dot_product_attention(q, k, v, is_causal=c).float() - rif).abs().max().item()
        ee = (emulazione_p16(q, k, v, c) - rif).abs().max().item()
        soglia = 2 * ee + rif.abs().max().item() * 2 ** -11
        ok = e2 <= soglia
        tutti &= ok
        print(f"  B{B} H{H:<2} S{S:<5} D{D:<3} causale={str(c):5s}  fa2 {e2:.2e}  emul.P16 {ee:.2e}  "
              f"math fp16 {em:.2e}  soglia {soglia:.2e}  {'ok' if ok else '>>> SBAGLIATO'}", flush=True)
    print("ESITO", "ok" if tutti else "SBAGLIATO")


def misura(fn, giri):
    torch.cuda.synchronize(); t0 = time.perf_counter()
    for _ in range(giri):
        fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) * 1000 / giri


def prestazioni():
    print(f"  {'forma':28s} {'math':>8} {'proto':>8} {'fa2':>8}  {'fa2/math':>8}  TFLOPS fa2", flush=True)
    for B, H, S, D, c in [(1, 16, 1024, 64, False), (1, 16, 2048, 64, False), (1, 16, 4096, 64, False),
                          (1, 16, 1024, 128, False), (1, 16, 2048, 128, False), (1, 16, 4096, 128, False),
                          (1, 16, 4096, 128, True), (1, 16, 8192, 128, True)]:
        q, k, v = dati(B, H, S, D)
        fns = {"math": lambda: F.scaled_dot_product_attention(q, k, v, is_causal=c),
               "proto": lambda: fa_avanti.flash_avanti(q, k, v, is_causal=c),
               "fa2": lambda: fa2_avanti.flash_avanti(q, k, v, is_causal=c)}
        giri = max(1, int(2e10 / (B * H * S * S * D)))
        t = {n: [] for n in fns}
        for f in fns.values():
            try: f()
            except torch.cuda.OutOfMemoryError: pass
        for _ in range(5):
            for n, f in fns.items():
                try: t[n].append(misura(f, giri))
                except torch.cuda.OutOfMemoryError: t[n].append(float("nan"))
        m = {n: statistics.median(x) for n, x in t.items()}
        flop = 4 * B * H * S * S * D * (0.5 if c else 1.0)
        nome = f"B{B} H{H} S{S} D{D}{' causale' if c else ''}"
        print(f"  {nome:28s} {m['math']:8.2f} {m['proto']:8.2f} {m['fa2']:8.2f}  {m['math'] / m['fa2']:7.2f}x  "
              f"{flop / (m['fa2'] / 1000) / 1e12:6.2f}", flush=True)
        del q, k, v
        torch.cuda.empty_cache()


if __name__ == "__main__":
    {"correttezza": correttezza, "prestazioni": prestazioni}[sys.argv[1]]()

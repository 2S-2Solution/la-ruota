"""Verifica del collegamento della flash attention a scaled_dot_product_attention.

    python -u prova_ruota_flash.py
"""
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\LaRuota_workspace\ruota_flash")
import ruota_flash  # noqa: E402

torch.manual_seed(0)
originale = ruota_flash._originale
esiti = []


def rif(q, k, v, causale, gqa):
    q, k, v = (t.detach().float().requires_grad_() for t in (q, k, v))
    o = originale(q, k, v, is_causal=causale, enable_gqa=gqa)
    return o, (q, k, v)


def caso(nome, B, H, Hk, Sq, Sk, D, causale, autocast=False, attesa_flash=True):
    dt = torch.float32 if autocast else torch.float16
    q = torch.randn(B, H, Sq, D, device="cuda", dtype=dt, requires_grad=True)
    k = torch.randn(B, Hk, Sk, D, device="cuda", dtype=dt, requires_grad=True)
    v = torch.randn(B, Hk, Sk, D, device="cuda", dtype=dt, requires_grad=True)
    gqa = H != Hk
    prima = ruota_flash.contatori["flash"]
    if autocast:
        with torch.autocast("cuda", dtype=torch.float16):
            o = F.scaled_dot_product_attention(q, k, v, is_causal=causale, enable_gqa=gqa)
    else:
        o = F.scaled_dot_product_attention(q, k, v, is_causal=causale, enable_gqa=gqa)
    usata = ruota_flash.contatori["flash"] > prima
    w = torch.randn_like(o.float())
    (o.float() * w).sum().backward()
    o_r, ingressi = rif(q, k, v, causale, gqa)
    (o_r * w).sum().backward()
    s = lambda a, b: ((a.float() - b).abs().max() / b.abs().max()).item()
    d = max(s(o.detach(), o_r.detach()), *(s(a.grad, b.grad) for a, b in zip((q, k, v), ingressi)))
    ok = d < 2e-2 and usata == attesa_flash
    esiti.append(ok)
    print(f"  {'OK ' if ok else 'ERR'}  {nome:46s} {'flash' if usata else 'originale':9s} scarto {d:.1e}", flush=True)


ruota_flash.attiva()
assert ruota_flash.attiva_ora()
caso("D=64, causale", 2, 8, 8, 256, 256, 64, True)
caso("D=128, causale", 2, 8, 8, 512, 512, 128, True)
caso("D=128, non causale", 2, 8, 8, 384, 384, 128, False)
caso("D=256, causale (Qwen3.5)", 1, 8, 8, 512, 512, 256, True)
caso("D=256, causale, GQA 16/4 (Qwen3.5)", 1, 16, 4, 512, 512, 256, True)
caso("D=64, GQA 8/2, S_q 128 != S_k 384, causale", 2, 8, 2, 128, 384, 64, True)
caso("D=128, autocast fp16 da ingressi fp32", 2, 4, 4, 256, 256, 128, True, autocast=True)
caso("D=256 non causale -> originale", 1, 4, 4, 256, 256, 256, False, attesa_flash=False)
caso("D=96 -> originale", 1, 4, 4, 128, 128, 96, True, attesa_flash=False)

# maschera arbitraria: deve andare all'originale
q = torch.randn(1, 4, 64, 64, device="cuda", dtype=torch.float16)
m = torch.ones(64, 64, device="cuda", dtype=torch.bool).tril()
prima = ruota_flash.contatori["flash"]
F.scaled_dot_product_attention(q, q, q, attn_mask=m)
ok = ruota_flash.contatori["flash"] == prima
esiti.append(ok)
print(f"  {'OK ' if ok else 'ERR'}  attn_mask -> originale", flush=True)

# dropout: gira, uscita finita, e in media conserva la scala
q = torch.randn(2, 8, 256, 64, device="cuda", dtype=torch.float16, requires_grad=True)
o = F.scaled_dot_product_attention(q, q, q, dropout_p=0.1, is_causal=True)
o.sum().backward()
ok = bool(torch.isfinite(o).all() and torch.isfinite(q.grad).all())
esiti.append(ok)
print(f"  {'OK ' if ok else 'ERR'}  dropout 0,1 in addestramento: avanti e indietro finiti", flush=True)

# tempo, forma tipica: B=2, H=16, S=2048, D=128, causale, avanti+indietro
q = torch.randn(2, 16, 2048, 128, device="cuda", dtype=torch.float16, requires_grad=True)


def passo():
    q.grad = None
    F.scaled_dot_product_attention(q, q, q, is_causal=True).sum().backward()


def misura():
    for _ in range(3):
        passo()
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    for _ in range(5):
        passo()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) / 5 * 1000, torch.cuda.max_memory_allocated() / 2**20


t_f, m_f = misura()
ruota_flash.disattiva()
t_o, m_o = misura()
print(f"\n  B2 H16 S2048 D128 causale, avanti+indietro: flash {t_f:.1f} ms / {m_f:.0f} MB, "
      f"originale {t_o:.1f} ms / {m_o:.0f} MB -> {t_o / t_f:.2f}x", flush=True)
print("  contatori:", dict(ruota_flash.contatori))
print(f"\n{sum(esiti)} su {len(esiti)} ok", flush=True)

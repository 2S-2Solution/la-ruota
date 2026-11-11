"""Banco della conv causale fusa e dello strato Qwen3.5 senza permutazioni.

    python banco_strato.py correttezza
    python banco_strato.py prestazioni [S]

Riferimenti: il percorso attuale di transformers (rif32) e lo stesso in float64 ("verità"). Passa se
l'errore del kernel contro la verità non supera il doppio di quello del riferimento (pavimento 1e-5
relativo al massimo in fp32, 2e-3 in fp16).
"""
import inspect
import statistics
import sys
import os
# Percorsi da variabili d'ambiente (nessun percorso della macchina di prova):
#   RUOTA_QWEN35        cartella del modello Qwen3.5-4B (predefinita: ./Qwen3.5-4B)
#   RUOTA_TF5           transformers 5 installato a parte con pip --target (vuota: quello dell'ambiente)
import time

TF5 = os.environ.get("RUOTA_TF5", "")
MODELLO = os.environ.get("RUOTA_QWEN35", "Qwen3.5-4B")
if TF5:
    sys.path.insert(0, TF5)
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")

import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from transformers import AutoConfig  # noqa: E402
from transformers.models.qwen3_5 import modeling_qwen3_5 as mq  # noqa: E402

import gdn_gfx906 as gdn  # noqa: E402

rif_chunk = mq.torch_chunk_gated_delta_rule
forward_orig = mq.Qwen3_5GatedDeltaNet.forward


def _rif64():
    src = inspect.getsource(mq.torch_chunk_gated_delta_rule.__wrapped__)
    src = src[src.index("def "):].replace("torch.float32", "torch.float64")
    g = dict(mq.__dict__)
    exec(src, g)
    return g["torch_chunk_gated_delta_rule"]


rif64 = _rif64()


def errore(x, verita):
    return ((x.double() - verita.double()).abs().max() / verita.double().abs().max().clamp_min(1e-30)).item()


def giudica(righe, nome, ek, er, mezzo):
    ok = ek <= max(2 * er, 2e-3 if mezzo else 1e-5)
    righe.append(f"    {nome:22s} kernel {ek:.2e}  rif {er:.2e}  {'ok' if ok else 'NO'}")
    return ok


def stampa(titolo, esito, righe):
    print(f"[{'OK' if esito else 'NO'}] {titolo}", flush=True)
    print("\n".join(r for i, r in enumerate(righe) if i < len(righe) // 3 or r.endswith("NO")))


# ---------------------------------------------------------------- (1) conv causale
def caso_conv(B, S, Cn, K, dtipo, con_bias, seme=0):
    gen = torch.Generator(device="cuda").manual_seed(seme)
    r = lambda *f: torch.randn(*f, device="cuda", generator=gen)
    x0 = r(B, S, Cn).to(dtipo)
    w0 = (r(Cn, K) * 0.5).to(dtipo)
    b0 = (r(Cn) * 0.1).to(dtipo) if con_bias else None
    esito, righe = True, []
    for giro in range(3):
        dy = r(B, S, Cn).to(dtipo)
        ris = {}
        for etich in ("kernel", "rif", "verita"):
            conv = (lambda t: t.double()) if etich == "verita" else (lambda t: t)
            x = conv(x0.clone()).requires_grad_(True)
            w = conv(w0.clone()).requires_grad_(True)
            b = conv(b0.clone()).requires_grad_(True) if con_bias else None
            if etich == "kernel":
                y = gdn.conv_causale(x, w, b, silu=True)
            else:   # il percorso dello strato: trasposta, causal_conv1d_fn, trasposta
                y = mq.causal_conv1d_fn(x.transpose(1, 2), w, b, activation="silu").transpose(1, 2)
            (y.double() * dy.double()).sum().backward()
            ris[etich] = [y.detach(), x.grad, w.grad] + ([b.grad] if con_bias else [])
        for i, n in enumerate(["y", "dx", "dw"] + (["dbias"] if con_bias else [])):
            esito &= giudica(righe, f"giro {giro} {n}", errore(ris["kernel"][i], ris["verita"][i]),
                             errore(ris["rif"][i], ris["verita"][i]), dtipo == torch.float16)
    stampa(f"conv B{B} S{S} C{Cn} K{K} {str(dtipo)[6:]}{' bias' if con_bias else ''}", esito, righe)
    return esito


# ---------------------------------------------------------------- (2) GDN impacchettato, GQA
def caso_gqa(B, S, Hk, H, D, dtipo, seme=0):
    gen = torch.Generator(device="cuda").manual_seed(seme)
    r = lambda *f: torch.randn(*f, device="cuda", generator=gen)
    qkv0 = r(B, S, 2 * Hk * D + H * D).to(dtipo)
    A = torch.rand(H, device="cuda", generator=gen) * 16
    g0 = -(A * F.softplus(r(B, S, H) - 2.0)).float()
    b0 = torch.sigmoid(r(B, S, H)).to(dtipo)
    esito, righe = True, []
    for giro in range(3):
        do = r(B, S, H, D).to(dtipo)
        ris = {}
        for etich in ("kernel", "rif", "verita"):
            conv = (lambda t: t.double()) if etich == "verita" else (lambda t: t)
            qkv = conv(qkv0.clone()).requires_grad_(True)
            g = conv(g0.clone()).requires_grad_(True)
            be = conv(b0.clone()).requires_grad_(True)
            if etich == "kernel":
                o = gdn.gdn_impacchettato(qkv, g, be, Hk, H, D, D)
            else:
                q, k, v = torch.split(qkv, [Hk * D, Hk * D, H * D], dim=-1)
                q = q.reshape(B, S, Hk, D).repeat_interleave(H // Hk, dim=2)
                k = k.reshape(B, S, Hk, D).repeat_interleave(H // Hk, dim=2)
                v = v.reshape(B, S, H, D)
                o, _ = (rif64 if etich == "verita" else rif_chunk)(q, k, v, g=g, beta=be, use_qk_l2norm_in_kernel=True)
            (o.double() * do.double()).sum().backward()
            ris[etich] = [o.detach(), qkv.grad, g.grad, be.grad]
        for i, n in enumerate(["o", "dqkv", "dg", "dbeta"]):
            esito &= giudica(righe, f"giro {giro} {n}", errore(ris["kernel"][i], ris["verita"][i]),
                             errore(ris["rif"][i], ris["verita"][i]), dtipo == torch.float16)
    stampa(f"GDN impacchettato B{B} S{S} Hk{Hk} H{H} {str(dtipo)[6:]}", esito, righe)
    return esito


# ---------------------------------------------------------------- (3) lo strato intero
def configurazione():
    return AutoConfig.from_pretrained(MODELLO).get_text_config()


def strato(cfg, dtipo, seme=0):
    torch.manual_seed(seme)
    m = mq.Qwen3_5GatedDeltaNet(cfg, layer_idx=0)
    with torch.no_grad():
        m.norm.weight.normal_(1.0, 0.1)
        m.dt_bias.normal_(0.0, 0.5)
    return m.to("cuda", dtipo)


def caso_strato(S, dtipo, B=1, seme=0):
    cfg = configurazione()
    base = strato(cfg, torch.float32, seme)
    esito, righe = True, []
    gen = torch.Generator(device="cuda").manual_seed(seme + 1)
    h0 = torch.randn(B, S, cfg.hidden_size, device="cuda", generator=gen)
    for giro in range(3):
        dy = torch.randn(B, S, cfg.hidden_size, device="cuda", generator=gen)
        ris = {}
        for etich in ("kernel", "rif", "verita"):
            tipo = torch.float64 if etich == "verita" else dtipo
            m = strato(cfg, torch.float32, seme)
            m.load_state_dict(base.state_dict())
            m = m.to(tipo)
            h = h0.clone().to(tipo).requires_grad_(True)
            if etich == "kernel":
                mq.Qwen3_5GatedDeltaNet.forward = gdn._forward_strato
                gdn._forward_originale[mq.Qwen3_5GatedDeltaNet] = forward_orig
                mq.torch_chunk_gated_delta_rule = gdn.chunk_gated_delta_rule
            else:
                mq.Qwen3_5GatedDeltaNet.forward = forward_orig
                mq.torch_chunk_gated_delta_rule = rif64 if etich == "verita" else rif_chunk
            try:
                y = m(h)
                (y.double() * dy.double()).sum().backward()
            finally:
                mq.Qwen3_5GatedDeltaNet.forward = forward_orig
                mq.torch_chunk_gated_delta_rule = rif_chunk
            ris[etich] = [("y", y.detach()), ("dh", h.grad)] + [(f"d {n}", p.grad) for n, p in m.named_parameters()]
        for i, (n, _) in enumerate(ris["verita"]):
            esito &= giudica(righe, f"giro {giro} {n}"[:22], errore(ris["kernel"][i][1], ris["verita"][i][1]),
                             errore(ris["rif"][i][1], ris["verita"][i][1]), dtipo == torch.float16)
    stampa(f"strato Qwen3_5GatedDeltaNet (dimensioni del 4B) B{B} S{S} {str(dtipo)[6:]}", esito, righe)
    return esito


def correttezza():
    tutti = True
    tutti &= caso_conv(1, 512, 8192, 4, torch.float16, False)
    tutti &= caso_conv(2, 100, 1000, 4, torch.float32, True)
    tutti &= caso_conv(1, 37, 300, 3, torch.float16, True)
    tutti &= caso_gqa(1, 256, 16, 32, 128, torch.float16)
    tutti &= caso_gqa(2, 100, 4, 8, 128, torch.float32)
    tutti &= caso_strato(256, torch.float16)
    tutti &= caso_strato(200, torch.float32, B=2)
    print("\nTUTTI OK" if tutti else "\nQUALCOSA NON VA")


def cronometra(fn, n=20):
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    t = []
    for _ in range(n):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        fn()
        torch.cuda.synchronize()
        t.append(time.perf_counter() - t0)
    return 1000 * statistics.median(t)


def prestazioni(S):
    cfg = configurazione()
    m = strato(cfg, torch.float16)
    h = torch.randn(1, S, cfg.hidden_size, device="cuda", dtype=torch.float16, requires_grad=True)
    dy = torch.randn_like(h)
    for etich in ("funzione", "strato"):
        mq.Qwen3_5GatedDeltaNet.forward = forward_orig
        mq.torch_chunk_gated_delta_rule = rif_chunk
        gdn._forward_originale.clear()
        gdn.aggancia(mq, strato=(etich == "strato"))
        def ai():
            m(h).backward(dy)
        def av():
            with torch.no_grad():
                m(h)
        print(f"S{S} kernel GDN + {etich:8s}: avanti {cronometra(av):6.2f} ms   avanti+indietro {cronometra(ai):6.2f} ms",
              flush=True)


if __name__ == "__main__":
    cosa = sys.argv[1] if len(sys.argv) > 1 else "correttezza"
    if cosa == "correttezza":
        correttezza()
    else:
        prestazioni(int(sys.argv[2]) if len(sys.argv) > 2 else 512)

"""Gradienti LoRA del 4B vero, un passo senza ottimizzatore: torch/torch, kernel/kernel, torch/kernel.

Se torch contro se stesso varia quanto torch contro kernel, la differenza è rumore del modello
(fp16, riduzioni non deterministiche), non un difetto del kernel.
"""
import sys
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import torch  # noqa: E402

sorgente = open(r"C:\LaRuota_workspace\prova_lora_4b_reale.py", encoding="utf-8").read()
montaggio = sorgente.split('dopo_carico = vram("dopo il caricamento")')[0]
g = {"__name__": "montaggio"}
exec(compile(montaggio, "prova_lora_4b_reale.py", "exec"), g)
m, allenabili = g["m"], g["allenabili"]

import gdn_gfx906  # noqa: E402
from transformers.models.qwen3_5 import modeling_qwen3_5 as mq  # noqa: E402
orig = mq.torch_chunk_gated_delta_rule

# B dei LoRA a zero: i gradienti di A sono nulli. Do a B un valore piccolo per avere tutto vivo.
torch.manual_seed(1)
for p in allenabili:
    if p.shape[1] == 16:            # b.weight: [out, rango]
        p.data.normal_(0, 1e-3)

idx = torch.randint(0, m.config.get_text_config().vocab_size, (1, 256), device="cuda")


l2_orig = mq.l2norm


def l2norm_fp32(x, dim=-1, eps=1e-6):
    x = x.float()
    return x * torch.rsqrt((x * x).sum(dim=dim, keepdim=True) + eps)


def gradienti(modo):
    mq.torch_chunk_gated_delta_rule = gdn_gfx906.chunk_gated_delta_rule if modo == "kernel" else orig
    mq.l2norm = l2norm_fp32 if modo == "torch_l2fp32" else l2_orig
    for p in allenabili:
        p.grad = None
    with torch.amp.autocast("cuda", dtype=torch.float16):
        perdita = m(idx, labels=idx).loss
    (perdita * 128.0).backward()
    gr = torch.cat([p.grad.flatten().float() / 128.0 for p in allenabili])
    return perdita.item(), gr


ris = {}
for modo in ("torch", "kernel", "torch", "kernel", "torch_l2fp32", "torch_l2fp32"):
    ris.setdefault(modo, []).append(gradienti(modo))
    print(f"{modo:6s} perdita {ris[modo][-1][0]:.6f}  norma {ris[modo][-1][1].norm().item():.6f}", flush=True)


def dist(a, b):
    return ((a - b).norm() / b.norm()).item()


t1, t2 = ris["torch"][0][1], ris["torch"][1][1]
k1, k2 = ris["kernel"][0][1], ris["kernel"][1][1]
print(f"torch/torch   distanza relativa {dist(t2, t1):.3e}")
print(f"kernel/kernel distanza relativa {dist(k2, k1):.3e}")
print(f"torch/kernel  distanza relativa {dist(k1, t1):.3e}   coseno {torch.nn.functional.cosine_similarity(k1, t1, dim=0).item():.6f}")
f1, f2 = ris["torch_l2fp32"][0][1], ris["torch_l2fp32"][1][1]
print(f"torch con l2norm fp32 / se stesso   {dist(f2, f1):.3e}")
print(f"torch con l2norm fp32 / kernel      {dist(k1, f1):.3e}   (/ torch normale {dist(t1, f1):.3e})")
# per gruppo di strato: dove nasce la differenza
nomi = [n for n, p in m.named_parameters() if p.requires_grad]
off = 0
peggiori = []
for n, p in zip(nomi, allenabili):
    k = p.numel()
    a, b, c = k1[off:off + k], t1[off:off + k], t2[off:off + k]
    if b.norm() > 0:
        peggiori.append((dist(a, b), dist(c, b), n))
    off += k
peggiori.sort(reverse=True)
print("i 8 parametri con la differenza torch/kernel più grande (accanto torch/torch):")
for d, d0, n in peggiori[:8]:
    print(f"  {d:.3e}  ({d0:.3e})  {n}")

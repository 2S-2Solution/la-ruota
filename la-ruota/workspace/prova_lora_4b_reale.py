"""LoRA sul Qwen3.5-4B VERO: base fp16 congelata, adattatori fp32, autocast.

In fp32 il modello riempie la scheda al 99% e non resta memoria per i gradienti.
Qui si misura quanto costa in fp16 e se un passo di addestramento LoRA sta dentro
i 15,98 GB, con i gradienti finiti.
"""
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

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from transformers import AutoModelForCausalLM  # noqa: E402


def vram(etichetta):
    libera, totale = torch.cuda.mem_get_info()
    usata = (totale - libera) / 2 ** 30
    print(f"  [{etichetta:34s}] usata {usata:6.2f} GB   libera {libera / 2 ** 30:5.2f} GB", flush=True)
    return usata


class Lora(nn.Module):
    """Avvolge un Linear congelato: y = base(x) + B(A(x)) * scala, con A e B in fp32."""

    def __init__(self, base: nn.Linear, rango=16, alpha=32):
        super().__init__()
        self.base = base
        self.a = nn.Linear(base.in_features, rango, bias=False, dtype=torch.float32)
        self.b = nn.Linear(rango, base.out_features, bias=False, dtype=torch.float32)
        nn.init.kaiming_uniform_(self.a.weight, a=5 ** 0.5)
        nn.init.zeros_(self.b.weight)
        self.scala = alpha / rango

    def forward(self, x):
        y = self.base(x)
        with torch.amp.autocast("cuda", enabled=False):
            d = self.b(self.a(x.float())) * self.scala
        return y + d.to(y.dtype)


BERSAGLI = ("q_proj", "k_proj", "v_proj", "o_proj")

print("=" * 70)
vram("all'avvio")

print("\n[1] caricamento in fp16", flush=True)
t0 = time.perf_counter()
m = AutoModelForCausalLM.from_pretrained(MODELLO, dtype=torch.float16, low_cpu_mem_usage=True)
print(f"  caricato da disco in {time.perf_counter() - t0:.0f} s", flush=True)

for p in m.parameters():
    p.requires_grad_(False)

n_lora = 0
for mod in list(m.modules()):
    for nome, figlio in list(mod.named_children()):
        if isinstance(figlio, nn.Linear) and nome in BERSAGLI:
            setattr(mod, nome, Lora(figlio))
            n_lora += 1

m = m.cuda()
for mod in m.modules():
    if isinstance(mod, Lora):
        mod.a.float()
        mod.b.float()
m.train()
if hasattr(m, "gradient_checkpointing_enable"):
    m.gradient_checkpointing_enable()
    print("  checkpointing dei gradienti attivo", flush=True)

allenabili = [p for p in m.parameters() if p.requires_grad]
totali = sum(p.numel() for p in m.parameters())
print(f"  {n_lora} moduli LoRA   allenabili {sum(p.numel() for p in allenabili)/1e6:.2f}M "
      f"su {totali/1e9:.2f}G ({100*sum(p.numel() for p in allenabili)/totali:.3f}%)", flush=True)
dopo_carico = vram("dopo il caricamento")

print("\n[2] passo di addestramento", flush=True)
opt = torch.optim.AdamW(allenabili, lr=1e-4)
scaler = torch.amp.GradScaler("cuda", init_scale=128.0)

LOTTO, LUNGHEZZA = 1, 256
idx = torch.randint(0, m.config.get_text_config().vocab_size, (LOTTO, LUNGHEZZA), device="cuda")
print(f"  lotto {LOTTO} x {LUNGHEZZA} token", flush=True)

picco = dopo_carico
for passo in range(4):
    t0 = time.perf_counter()
    opt.zero_grad(set_to_none=True)
    with torch.amp.autocast("cuda", dtype=torch.float16):
        perdita = m(idx, labels=idx).loss
    scaler.scale(perdita).backward()
    scaler.unscale_(opt)
    finiti = all(torch.isfinite(p.grad).all().item() for p in allenabili if p.grad is not None)
    norma = torch.nn.utils.clip_grad_norm_(allenabili, 1.0)
    s0 = scaler.get_scale()
    scaler.step(opt)
    scaler.update()
    torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    picco = max(picco, (torch.cuda.mem_get_info()[1] - torch.cuda.mem_get_info()[0]) / 2 ** 30)
    print(f"  passo {passo}: loss {perdita.item():.4f}  gradienti finiti: {finiti}  "
          f"norma {norma.item():.4f}  scala {scaler.get_scale():.0f}"
          f"{'  SALTATO' if scaler.get_scale() < s0 else ''}  {dt:.2f} s", flush=True)

print()
vram("a regime")
print(f"  picco osservato: {picco:.2f} GB su 15.98")
print("\nfine")

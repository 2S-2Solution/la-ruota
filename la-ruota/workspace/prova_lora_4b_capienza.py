"""Quanto contesto e quanto lotto reggono, addestrando in LoRA il Qwen3.5-4B.

Serve a sapere in anticipo dove si sbatte contro i 15,98 GB, invece di scoprirlo
a meta' di un addestramento. Ogni combinazione fa un passo completo e riporta
picco di memoria e tempo; quando la memoria finisce, lo dice e prosegue.
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


class Lora(nn.Module):
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

m = AutoModelForCausalLM.from_pretrained(MODELLO, dtype=torch.float16, low_cpu_mem_usage=True)
for p in m.parameters():
    p.requires_grad_(False)
for mod in list(m.modules()):
    for nome, figlio in list(mod.named_children()):
        if isinstance(figlio, nn.Linear) and nome in BERSAGLI:
            setattr(mod, nome, Lora(figlio))
m = m.cuda()
for mod in m.modules():
    if isinstance(mod, Lora):
        mod.a.float()
        mod.b.float()
m.train()
m.gradient_checkpointing_enable()
allenabili = [p for p in m.parameters() if p.requires_grad]
opt = torch.optim.AdamW(allenabili, lr=1e-4)
scaler = torch.amp.GradScaler("cuda", init_scale=128.0)
vocab = m.config.get_text_config().vocab_size

base = (torch.cuda.mem_get_info()[1] - torch.cuda.mem_get_info()[0]) / 2 ** 30
print(f"modello caricato: {base:.2f} GB\n")
print(f"{'lotto':>5} {'token':>6} {'totali':>7}  {'picco GB':>9}  {'s/passo':>8}  esito")
print("-" * 62)

for lotto, lungh in [(1, 256), (1, 512), (1, 1024), (2, 512), (1, 2048), (4, 512), (2, 1024), (1, 4096)]:
    try:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        idx = torch.randint(0, vocab, (lotto, lungh), device="cuda")
        t0 = time.perf_counter()
        opt.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda", dtype=torch.float16):
            perdita = m(idx, labels=idx).loss
        scaler.scale(perdita).backward()
        scaler.unscale_(opt)
        finiti = all(torch.isfinite(p.grad).all().item() for p in allenabili if p.grad is not None)
        torch.nn.utils.clip_grad_norm_(allenabili, 1.0)
        scaler.step(opt)
        scaler.update()
        torch.cuda.synchronize()
        dt = time.perf_counter() - t0
        picco = (torch.cuda.mem_get_info()[1] - torch.cuda.mem_get_info()[0]) / 2 ** 30
        nota = "ok" if finiti else "GRADIENTI NON FINITI"
        print(f"{lotto:5d} {lungh:6d} {lotto*lungh:7d}  {picco:9.2f}  {dt:8.2f}  {nota}")
        del idx
    except torch.cuda.OutOfMemoryError:
        print(f"{lotto:5d} {lungh:6d} {lotto*lungh:7d}  {'—':>9}  {'—':>8}  memoria esaurita")
        torch.cuda.empty_cache()
    except Exception as exc:
        print(f"{lotto:5d} {lungh:6d} {lotto*lungh:7d}  {'—':>9}  {'—':>8}  {type(exc).__name__}: {str(exc)[:50]}")
        torch.cuda.empty_cache()

print("\nfine")

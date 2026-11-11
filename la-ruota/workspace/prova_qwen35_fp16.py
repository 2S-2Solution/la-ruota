"""Dove nascono i NaN di Qwen3.5 in fp16, e AMP li evita?

Il modello e' nato in bf16, che su gfx906 non esiste. In fp16 puro i gradienti
vanno a NaN. Qui si stabilisce:
  1. QUALI parametri diventano NaN (gli strati ad attenzione lineare o tutti?)
  2. se il forward e' gia' NaN o lo diventa solo all'indietro
  3. se l'assetto reale di addestramento - pesi maestri in fp32 + autocast fp16
     + GradScaler - regge dove il fp16 puro non regge
"""
import sys
import os
# Percorsi da variabili d'ambiente (nessun percorso della macchina di prova):
#   RUOTA_QWEN35        cartella del modello Qwen3.5-4B (predefinita: ./Qwen3.5-4B)
#   RUOTA_TF5           transformers 5 installato a parte con pip --target (vuota: quello dell'ambiente)
import copy
from collections import Counter

TF5 = os.environ.get("RUOTA_TF5", "")
MODELLO = os.environ.get("RUOTA_QWEN35", "Qwen3.5-4B")
if TF5:
    sys.path.insert(0, TF5)

import torch  # noqa: E402
from transformers import AutoConfig, AutoModelForCausalLM  # noqa: E402

cfg = AutoConfig.from_pretrained(MODELLO)


def piccolo(n_lin=3, n_pieni=1):
    c = copy.deepcopy(cfg)
    t = c.get_text_config()
    base = list(t.layer_types)
    lineari = [x for x in base if "linear" in x]
    piene = [x for x in base if "linear" not in x]
    nuovi = lineari[:n_lin] + piene[:n_pieni]
    t.layer_types = nuovi
    t.num_hidden_layers = len(nuovi)
    for k, v in [("hidden_size", 256), ("intermediate_size", 512),
                 ("num_attention_heads", 4), ("num_key_value_heads", 2),
                 ("vocab_size", 1024), ("head_dim", 64),
                 ("linear_num_value_heads", 4), ("linear_num_key_heads", 2),
                 ("linear_key_head_dim", 64), ("linear_value_head_dim", 64)]:
        if hasattr(t, k):
            setattr(t, k, v)
    c.vocab_size = 1024
    c.tie_word_embeddings = True
    return c


def costruisci(conf, dtype):
    torch.manual_seed(0)
    return AutoModelForCausalLM.from_config(conf).to(dtype).cuda()


def dati():
    torch.manual_seed(1)
    idx = torch.randint(0, 1024, (2, 16), device="cuda")
    return idx


print("=" * 66)
print("1. fp16 puro: forward gia' rotto, o solo il backward?")
print("=" * 66)
m = costruisci(piccolo(), torch.float16)
idx = dati()
out = m(idx, labels=idx)
print(f"  loss forward: {out.loss.item():.4f}  finita: {torch.isfinite(out.loss).item()}")
out.loss.backward()
rotti, sani = [], []
for nome, p in m.named_parameters():
    if p.grad is None:
        continue
    (rotti if not torch.isfinite(p.grad).all() else sani).append(nome)
print(f"  gradienti NON finiti: {len(rotti)} su {len(rotti) + len(sani)}")


def famiglia(n):
    # "model.layers.2.qualcosa" -> indice di strato, se c'e'
    parti = n.split(".")
    for i, p in enumerate(parti):
        if p == "layers" and i + 1 < len(parti):
            return f"strato {parti[i + 1]}"
    return "fuori dagli strati"


if rotti:
    print("  distribuzione dei rotti:")
    for k, v in sorted(Counter(famiglia(n) for n in rotti).items()):
        print(f"    {k:22s} {v}")
    print("  primi cinque nomi:")
    for n in rotti[:5]:
        print(f"    {n}")
if sani:
    print("  distribuzione dei sani:")
    for k, v in sorted(Counter(famiglia(n) for n in sani).items()):
        print(f"    {k:22s} {v}")

del m
torch.cuda.empty_cache()

print()
print("=" * 66)
print("2. solo strati ad attenzione PIENA, fp16 (isola la causa)")
print("=" * 66)
m = costruisci(piccolo(n_lin=0, n_pieni=4), torch.float16)
out = m(idx, labels=idx)
out.loss.backward()
n_rotti = sum(1 for _, p in m.named_parameters() if p.grad is not None and not torch.isfinite(p.grad).all())
print(f"  loss {out.loss.item():.4f}  gradienti non finiti: {n_rotti}")
del m
torch.cuda.empty_cache()

print()
print("=" * 66)
print("3. solo strati ad attenzione LINEARE, fp16")
print("=" * 66)
try:
    m = costruisci(piccolo(n_lin=4, n_pieni=0), torch.float16)
    out = m(idx, labels=idx)
    out.loss.backward()
    n_rotti = sum(1 for _, p in m.named_parameters() if p.grad is not None and not torch.isfinite(p.grad).all())
    print(f"  loss {out.loss.item():.4f}  gradienti non finiti: {n_rotti}")
    del m
    torch.cuda.empty_cache()
except Exception as exc:
    # NB: limite di transformers, non della scheda. Un modello di soli strati
    # lineari non ha una cache di attenzione e get_seq_length solleva. Il modello
    # vero ha 8 strati pieni su 32, quindi il caso non si presenta.
    print(f"  non provabile in isolamento: {type(exc).__name__}: {str(exc)[:90]}")

print()
print("=" * 66)
print("4. assetto REALE: pesi in fp32 + autocast fp16 + GradScaler")
print("=" * 66)
m = costruisci(piccolo(), torch.float32)
scaler = torch.amp.GradScaler("cuda")
opt = torch.optim.AdamW(m.parameters(), lr=1e-4)
for passo in range(5):
    opt.zero_grad(set_to_none=True)
    with torch.amp.autocast("cuda", dtype=torch.float16):
        perdita = m(idx, labels=idx).loss
    scaler.scale(perdita).backward()
    scaler.unscale_(opt)
    norma = torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
    scaler.step(opt)
    scaler.update()
    print(f"  passo {passo}: loss {perdita.item():.4f}  norma gradienti {norma.item():.4f}  "
          f"scala {scaler.get_scale():.0f}")

print("\nfine")

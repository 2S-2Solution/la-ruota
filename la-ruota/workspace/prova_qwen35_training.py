"""Qwen3.5 in precisione mista su LA RUOTA: addestra davvero?

Sappiamo che con autocast fp16 e senza scala i gradienti sono tutti finiti, quindi
una scala bassa deve funzionare. Il GradScaler parte da 65536 e dimezza a ogni passo
saltato: da li' servono molte iterazioni solo per arrivare a un valore utile.
Qui si parte basso e si guarda se la perdita scende.
"""
import copy
import sys
import os
# Percorsi da variabili d'ambiente (nessun percorso della macchina di prova):
#   RUOTA_QWEN35        cartella del modello Qwen3.5-4B (predefinita: ./Qwen3.5-4B)
#   RUOTA_TF5           transformers 5 installato a parte con pip --target (vuota: quello dell'ambiente)

TF5 = os.environ.get("RUOTA_TF5", "")
MODELLO = os.environ.get("RUOTA_QWEN35", "Qwen3.5-4B")
if TF5:
    sys.path.insert(0, TF5)

import torch  # noqa: E402
from transformers import AutoConfig, AutoModelForCausalLM  # noqa: E402

cfg = AutoConfig.from_pretrained(MODELLO)


def piccolo():
    c = copy.deepcopy(cfg)
    t = c.get_text_config()
    base = list(t.layer_types)
    lin = [x for x in base if "linear" in x]
    pien = [x for x in base if "linear" not in x]
    t.layer_types = lin[:3] + pien[:1]
    t.num_hidden_layers = 4
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


torch.manual_seed(0)
idx = torch.randint(0, 1024, (2, 32), device="cuda")


def addestra(nome, dtype_autocast, scala_iniziale, passi=15):
    torch.manual_seed(0)
    m = AutoModelForCausalLM.from_config(piccolo()).float().cuda()
    opt = torch.optim.AdamW(m.parameters(), lr=3e-4)
    scaler = torch.amp.GradScaler("cuda", init_scale=scala_iniziale) if dtype_autocast else None
    print(f"\n--- {nome} ---")
    prima = ultima = None
    saltati = 0
    for p in range(passi):
        opt.zero_grad(set_to_none=True)
        if dtype_autocast:
            with torch.amp.autocast("cuda", dtype=dtype_autocast):
                perdita = m(idx, labels=idx).loss
            scaler.scale(perdita).backward()
            scala_prima = scaler.get_scale()
            scaler.step(opt)
            scaler.update()
            saltato = scaler.get_scale() < scala_prima
            saltati += int(saltato)
        else:
            perdita = m(idx, labels=idx).loss
            perdita.backward()
            torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
            opt.step()
            saltato = False
        v = perdita.item()
        if prima is None:
            prima = v
        ultima = v
        if p < 3 or p >= passi - 3:
            extra = f"  scala {scaler.get_scale():.0f}{'  SALTATO' if saltato else ''}" if scaler else ""
            print(f"  passo {p:2d}: loss {v:.4f}{extra}")
    print(f"  perdita {prima:.4f} -> {ultima:.4f}   passi saltati: {saltati}/{passi}")
    return prima, ultima


addestra("fp32 puro (riferimento)", None, None)
addestra("autocast fp16 + GradScaler (scala iniziale 128)", torch.float16, 128.0)

print("\nfine")

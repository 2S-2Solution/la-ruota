"""LoRA su Qwen3.5: base congelata in fp16 + adattatori fp32 + autocast.

E' l'assetto che serve davvero: in fp32 il 4B riempie la scheda al 99% e non
resta memoria per i gradienti. Non e' pero' lo stesso di model.half(), che nei
miei test dava NaN: li' TUTTI i parametri erano in fp16 e allenabili.

La domanda aperta: i gradienti attraversano comunque gli strati ad attenzione
lineare calcolati in fp16. Bastano gli adattatori in fp32 a tenerli finiti?

Adattatori scritti a mano: nessuna dipendenza da peft, e si controlla esattamente
dove sono attaccati.
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
import torch.nn as nn  # noqa: E402
from transformers import AutoConfig, AutoModelForCausalLM  # noqa: E402

cfg = AutoConfig.from_pretrained(MODELLO)


class Lora(nn.Module):
    """Avvolge un nn.Linear congelato aggiungendo B(A(x)) in fp32."""

    def __init__(self, base: nn.Linear, rango=8, alpha=16):
        super().__init__()
        self.base = base
        for p in self.base.parameters():
            p.requires_grad_(False)
        self.a = nn.Linear(base.in_features, rango, bias=False, dtype=torch.float32)
        self.b = nn.Linear(rango, base.out_features, bias=False, dtype=torch.float32)
        nn.init.kaiming_uniform_(self.a.weight, a=5 ** 0.5)
        nn.init.zeros_(self.b.weight)
        self.scala = alpha / rango

    def forward(self, x):
        y = self.base(x)
        # gli adattatori lavorano in fp32 anche sotto autocast
        with torch.amp.autocast("cuda", enabled=False):
            d = self.b(self.a(x.float())) * self.scala
        return y + d.to(y.dtype)


def applica_lora(modello, bersagli=("q_proj", "k_proj", "v_proj", "o_proj")):
    n = 0
    for nome, mod in list(modello.named_modules()):
        for figlio_nome, figlio in list(mod.named_children()):
            if isinstance(figlio, nn.Linear) and figlio_nome in bersagli:
                setattr(mod, figlio_nome, Lora(figlio))
                n += 1
    return n


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


def esegui(nome, dtype_base, usa_autocast, passi=12, init_scale=128.0):
    torch.manual_seed(0)
    m = AutoModelForCausalLM.from_config(piccolo())
    # PRIMA si congela tutto: altrimenti restano allenabili embedding, norme e
    # tutto il resto, che in fp16 hanno gradienti fp16 e lo scaler li rifiuta
    # ("Attempting to unscale FP16 gradients"). Gli adattatori nascono dopo,
    # quindi conservano requires_grad=True.
    for q in m.parameters():
        q.requires_grad_(False)
    n_lora = applica_lora(m)
    # base nel dtype scelto, adattatori sempre in fp32
    m = m.to(dtype_base).cuda()
    for mod in m.modules():
        if isinstance(mod, Lora):
            mod.a.float()
            mod.b.float()
    allenabili = [p for p in m.parameters() if p.requires_grad]
    n_par = sum(p.numel() for p in allenabili)

    opt = torch.optim.AdamW(allenabili, lr=1e-3)
    scaler = torch.amp.GradScaler("cuda", init_scale=init_scale) if usa_autocast else None

    print(f"\n--- {nome} ---")
    print(f"  {n_lora} moduli LoRA, {n_par/1e3:.1f}k parametri allenabili su "
          f"{sum(p.numel() for p in m.parameters())/1e6:.2f}M")

    prima = ultima = None
    saltati = 0
    non_finiti = 0
    for p in range(passi):
        opt.zero_grad(set_to_none=True)
        if usa_autocast:
            with torch.amp.autocast("cuda", dtype=torch.float16):
                perdita = m(idx, labels=idx).loss
            scaler.scale(perdita).backward()
            scaler.unscale_(opt)
            if not all(torch.isfinite(q.grad).all().item() for q in allenabili if q.grad is not None):
                non_finiti += 1
            s0 = scaler.get_scale()
            scaler.step(opt)
            scaler.update()
            saltati += int(scaler.get_scale() < s0)
        else:
            perdita = m(idx, labels=idx).loss
            perdita.backward()
            if not all(torch.isfinite(q.grad).all().item() for q in allenabili if q.grad is not None):
                non_finiti += 1
            opt.step()
        v = perdita.item()
        prima = v if prima is None else prima
        ultima = v
        if p < 2 or p >= passi - 2:
            print(f"    passo {p:2d}: loss {v:.4f}")
    print(f"  perdita {prima:.4f} -> {ultima:.4f}   passi con gradienti non finiti: "
          f"{non_finiti}/{passi}   saltati dallo scaler: {saltati}")
    del m
    torch.cuda.empty_cache()


esegui("base fp32 + LoRA fp32, senza autocast (riferimento)", torch.float32, False)
esegui("base fp16 congelata + LoRA fp32 + autocast fp16", torch.float16, True)

print("\nfine")

"""Qwen3.5 su LA RUOTA: transformers 5.x vede torch? E il modello gira?

Il blocco era la stringa di versione: la build produceva "2.5.0a0+...", che PEP 440
legge come pre-release di 2.5.0 e quindi MINORE di 2.5 -> transformers disattivava
torch del tutto. Ora i metadati dicono "2.5.0+gita8d6afb".

NB: transformers 5.x sta in un albero separato installato con --target, per non
toccare il venv de LA RUOTA che regge Qwen3 con la 4.51.3.
"""
import os
import sys
# Percorsi da variabili d'ambiente (nessun percorso della macchina di prova):
#   RUOTA_QWEN35        cartella del modello Qwen3.5-4B (predefinita: ./Qwen3.5-4B)
#   RUOTA_TF5           transformers 5 installato a parte con pip --target (vuota: quello dell'ambiente)
import traceback

TF5 = os.environ.get("RUOTA_TF5", "")
MODELLO = os.environ.get("RUOTA_QWEN35", "Qwen3.5-4B")

if TF5:
    sys.path.insert(0, TF5)

import torch  # noqa: E402

print(f"torch      {torch.__version__}")
import importlib.metadata as _m  # noqa: E402
print(f"metadati   {_m.version('torch')}")
print(f"GPU        {torch.cuda.get_device_name(0)}")

import transformers  # noqa: E402
print(f"transformers {transformers.__version__}  (da {os.path.dirname(transformers.__file__)})")
print(f"torch visto da transformers: {transformers.utils.is_torch_available()}")

if not transformers.utils.is_torch_available():
    sys.exit("torch ancora disattivato: il resto non ha senso")

print("\n[1] configurazione")
from transformers import AutoConfig  # noqa: E402

cfg = AutoConfig.from_pretrained(MODELLO)
# NB: Qwen3.5 e' multimodale, quindi la configurazione e' composita: i parametri
# del ramo testuale stanno in un sotto-oggetto, non sull'oggetto esterno.
testo = cfg.get_text_config() if hasattr(cfg, "get_text_config") else getattr(cfg, "text_config", cfg)
print(f"  esterna: {type(cfg).__name__}   testo: {type(testo).__name__}")
tipi = getattr(testo, "layer_types", None)
if tipi:
    from collections import Counter
    print(f"  {testo.num_hidden_layers} strati, {dict(Counter(tipi))}")
else:
    print(f"  {testo.num_hidden_layers} strati")
print(f"  dtype dichiarato: {getattr(cfg, 'torch_dtype', getattr(cfg, 'dtype', '?'))}")

print("\n[2] la classe del modello e' raggiungibile?")
try:
    from transformers import AutoModelForCausalLM
    arch = cfg.architectures[0] if getattr(cfg, "architectures", None) else "?"
    cls = getattr(transformers, arch, None)
    print(f"  architettura {arch}: {'presente' if cls else 'NON esposta in transformers'}")
except Exception:
    traceback.print_exc()

print("\n[3] modello minuscolo dalla stessa architettura, su GPU, in fp16")
print("    (niente pesi da 8,7 GB: qui interessa se i kernel girano)")


def piccolo():
    import copy
    c = copy.deepcopy(cfg)
    t = c.get_text_config() if hasattr(c, "get_text_config") else c

    # si rimpicciolisce tutto MANTENENDO la miscela di tipi di strato: e' proprio
    # l'attenzione lineare (24 strati su 32 nel modello vero) il punto da provare
    base = list(getattr(t, "layer_types", []))
    if base:
        lineari = [x for x in base if "linear" in x]
        piene = [x for x in base if "linear" not in x]
        nuovi = (lineari[:3] + piene[:1]) if (lineari and piene) else base[:4]
        t.layer_types = nuovi
        t.num_hidden_layers = len(nuovi)
    else:
        t.num_hidden_layers = 4

    for k, v in [("hidden_size", 256), ("intermediate_size", 512),
                 ("num_attention_heads", 4), ("num_key_value_heads", 2),
                 ("vocab_size", 1024), ("head_dim", 64),
                 ("linear_num_value_heads", 4), ("linear_num_key_heads", 2),
                 ("linear_key_head_dim", 64), ("linear_value_head_dim", 64)]:
        if hasattr(t, k):
            setattr(t, k, v)
    if hasattr(c, "vocab_size"):
        c.vocab_size = 1024
    c.tie_word_embeddings = True
    return c


for dtype, nome in [(torch.float32, "fp32"), (torch.float16, "fp16")]:
    try:
        from transformers import AutoModelForCausalLM
        torch.manual_seed(0)
        m = AutoModelForCausalLM.from_config(piccolo()).to(dtype).cuda()
        n = sum(p.numel() for p in m.parameters())
        idx = torch.randint(0, 1024, (2, 16), device="cuda")
        out = m(idx, labels=idx)
        out.loss.backward()
        gr = [p.grad for p in m.parameters() if p.grad is not None]
        nan = any(torch.isnan(g).any().item() for g in gr)
        norma = sum(g.float().norm().item() for g in gr)
        stato = "NaN NEI GRADIENTI" if nan else "gradienti sani"
        print(f"  {nome}: {n/1e6:.2f}M parametri, loss {out.loss.item():.4f}, "
              f"somma norme {norma:.2f} -> {stato}")
        del m
        torch.cuda.empty_cache()
    except Exception as exc:
        print(f"  {nome}: FALLITO -> {type(exc).__name__}: {str(exc)[:200]}")
        traceback.print_exc(limit=3)

print("\nfine")

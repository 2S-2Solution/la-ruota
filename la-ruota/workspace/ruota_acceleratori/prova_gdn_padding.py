"""Strato Gated DeltaNet fuso (rocm-marconi) contro l'originale, CON padding a destra.

    python -u prova_gdn_padding.py

Come in train_qwen35.py: lotto di 2 con lunghezze diverse, attention_mask con zeri in coda.
Uno strato con la configurazione vera del 4B e pesi casuali; si confrontano uscita (sulle
posizioni vere) e gradienti di pesi e ingresso.
"""
import copy
import sys
import os
# Percorsi da variabili d'ambiente (nessun percorso della macchina di prova):
#   RUOTA_QWEN35        cartella del modello Qwen3.5-4B (predefinita: ./Qwen3.5-4B)
#   RUOTA_TF5           transformers 5 installato a parte con pip --target (vuota: quello dell'ambiente)

if os.environ.get("RUOTA_TF5"):
    sys.path.insert(0, os.environ["RUOTA_TF5"])
import torch  # noqa: E402
from transformers import AutoConfig  # noqa: E402
from transformers.models.qwen3_5 import modeling_qwen3_5 as mq  # noqa: E402

sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import gdn_gfx906  # noqa: E402

cfg = AutoConfig.from_pretrained(os.environ.get("RUOTA_QWEN35", "Qwen3.5-4B"))
cfg = getattr(cfg, "text_config", cfg)
classe = next(getattr(mq, n) for n in dir(mq) if n.endswith("GatedDeltaNet") and isinstance(getattr(mq, n), type))
torch.manual_seed(0)
originale_forward = classe.forward
strato = classe(cfg, layer_idx=0).cuda().half()
fuso = copy.deepcopy(strato)

B, S = 2, 300
lunghezze = [300, 173]
x = (torch.randn(B, S, cfg.hidden_size, device="cuda") * 0.5).half()
maschera = torch.zeros(B, S, dtype=torch.long, device="cuda")
for i, n in enumerate(lunghezze):
    maschera[i, :n] = 1
w = torch.randn(B, S, cfg.hidden_size, device="cuda").half()
vere = maschera.bool().unsqueeze(-1)

esiti = []
for passo in range(3):
    risultati = []
    for m, aggancia in ((strato, False), (fuso, True)):
        if aggancia:
            # aggancia() sostituisce il forward solo la prima volta: qui lo si imposta a mano
            gdn_gfx906.aggancia(mq)
            classe.forward = gdn_gfx906._forward_strato
        else:
            classe.forward = originale_forward
        assert (classe.forward is gdn_gfx906._forward_strato) == aggancia
        m.zero_grad()
        xi = x.clone().requires_grad_()
        with torch.autocast("cuda", dtype=torch.float16):
            y = m(xi, attention_mask=maschera)
        ((y.float() * w.float()) * vere).sum().backward()
        risultati.append((y.detach().float() * vere, xi.grad.float() * vere,
                          [p.grad.float() for p in m.parameters() if p.grad is not None]))
    classe.forward = originale_forward
    (yo, gxo, gpo), (yf, gxf, gpf) = risultati
    s = lambda a, b: ((a - b).abs().max() / b.abs().max().clamp_min(1e-6)).item()
    d = max(s(yf, yo), s(gxf, gxo), *(s(a, b) for a, b in zip(gpf, gpo)))
    esiti.append(d < 2e-2)
    print(f"  passo {passo}: peggior scarto (uscita, d ingresso, d pesi) {d:.1e}", flush=True)
print("ESITO:", "giusto" if all(esiti) else "SBAGLIATO", flush=True)

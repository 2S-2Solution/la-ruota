"""Un passo LoRA di Qwen3.5-4B CON UN'IMMAGINE sulla ruota (torchvision installato dal 22 ott).

    python -u prova_qwen35_immagine.py [--passi N] [--lato 448]

Stessa ricetta di train_qwen35.py (fp16, base congelata, adattatori peft r=32 fp32 su q/k/v/o/gate/up/down del
modello di LINGUA, checkpointing, autocast fp16, GradScaler 128, acceleratori della ruota), ma con il modello
multimodale (Qwen3_5ForConditionalGeneration) e il processore d'immagini. Etichette: solo la risposta.
Controlla: avanti e indietro della torre visiva sulla GPU, perdita finita, tempo e picco di memoria.
"""
import importlib.util
import statistics
import sys
import os
# Percorsi da variabili d'ambiente (nessun percorso della macchina di prova):
#   RUOTA_QWEN35        cartella del modello Qwen3.5-4B (predefinita: ./Qwen3.5-4B)
#   RUOTA_TF5           transformers 5 installato a parte con pip --target (vuota: quello dell'ambiente)
#   RUOTA_TRAIN_QWEN35  percorso di train_qwen35.py (script di addestramento, non incluso)
import time

if os.environ.get("RUOTA_TF5"):
    sys.path.insert(0, os.environ["RUOTA_TF5"])
import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "train_qwen35", os.environ.get("RUOTA_TRAIN_QWEN35", "train_qwen35.py"))
tq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tq)
from transformers import AutoModelForImageTextToText, AutoProcessor  # noqa: E402
from peft import LoraConfig, get_peft_model  # noqa: E402

sys.path.insert(0, r"C:\LaRuota_workspace\ruota_acceleratori")
import ruota_acceleratori  # noqa: E402

ruota_acceleratori.attiva()
BASE = os.environ.get("RUOTA_QWEN35", "Qwen3.5-4B")
LATO = int(sys.argv[sys.argv.index("--lato") + 1]) if "--lato" in sys.argv else 448
PASSI = int(sys.argv[sys.argv.index("--passi") + 1]) if "--passi" in sys.argv else 4

proc = AutoProcessor.from_pretrained(BASE)
model = AutoModelForImageTextToText.from_pretrained(BASE, dtype=torch.float16, device_map="cuda:0",
                                                    low_cpu_mem_usage=True)
print("modello:", type(model).__name__, flush=True)
model.config.use_cache = False
model.requires_grad_(False)
tq.applica_lora_in_fp32()
model = get_peft_model(model, LoraConfig(r=32, lora_alpha=64, lora_dropout=0.0, bias="none",
                                         target_modules=r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)"))
for p in model.parameters():
    if p.requires_grad:
        p.data = p.data.float()
ruota_acceleratori.aggancia_lora_peft()
model.gradient_checkpointing_enable()
model.enable_input_require_grads()
model.train()
params = [p for p in model.parameters() if p.requires_grad]
print(f"allenabili {sum(p.numel() for p in params) / 1e6:.1f} M", flush=True)

rng = np.random.default_rng(0)
img = Image.fromarray((rng.random((LATO, LATO, 3)) * 255).astype("uint8"))
domanda = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": "Descrivi la foto."}]}]
risposta = "Una foto di rumore colorato, senza soggetti riconoscibili."
prompt = proc.apply_chat_template(domanda, add_generation_prompt=True)
intero = prompt + risposta + "<|im_end|>"
enc = proc(text=[intero], images=[img], return_tensors="pt")
n_prompt = proc(text=[prompt], images=[img], return_tensors="pt")["input_ids"].shape[1]
labels = enc["input_ids"].clone()
labels[:, :n_prompt] = -100
enc = {k: v.to("cuda") for k, v in enc.items()}
labels = labels.to("cuda")
print(f"token {enc['input_ids'].shape[1]} (risposta {int((labels != -100).sum())}), pixel {tuple(enc['pixel_values'].shape)}",
      flush=True)

opt = torch.optim.AdamW(params, lr=6e-5)
scaler = torch.amp.GradScaler("cuda", init_scale=128)
tempi, perdite = [], []
torch.cuda.reset_peak_memory_stats()
for _ in range(PASSI):
    torch.cuda.synchronize()
    t = time.perf_counter()
    with torch.amp.autocast("cuda", dtype=torch.float16):
        loss = model(**enc, labels=labels).loss
    scaler.scale(loss).backward()
    scaler.step(opt)
    scaler.update()
    opt.zero_grad(set_to_none=True)
    torch.cuda.synchronize()
    tempi.append(time.perf_counter() - t)
    perdite.append(loss.item())
gv = sum(1 for n, p in model.named_parameters() if "visual" in n)
print(f"RISULTATO perdite {' '.join(f'{x:.3f}' for x in perdite)} | passo {statistics.median(tempi[1:]):.2f} s "
      f"| picco {torch.cuda.max_memory_allocated() / 2**30:.2f} GB | parametri della torre visiva {gv} (congelati)",
      flush=True)
print("lora:", ruota_acceleratori.contatori_lora(), "| flash:", ruota_acceleratori.contatori_flash(), flush=True)

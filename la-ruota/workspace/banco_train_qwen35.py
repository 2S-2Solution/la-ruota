"""Passo d'addestramento di train_qwen35.py (4B) con gli acceleratori scelti dall'ambiente.

    python -u banco_train_qwen35.py [--passi N] [--senza-checkpointing] [--lunghezze 768,640] [--peft-originale]

Stesso montaggio dello script vero: transformers 5 dall'albero separato, 4B fp16, peft r=32 alpha 64 su
q/k/v/o/gate/up/down, adattatori fp32 (applica_lora_in_fp32), checkpointing, lotto 2 con padding a
destra e labels -100 sul prompt e sul padding, autocast fp16, GradScaler(128), AdamW. Agganci:
RUOTA_GDN / RUOTA_FLASH / RUOTA_NORME / RUOTA_PERDITA / RUOTA_GEMM / RUOTA_LORA = 0|1.
"""
import importlib.util
import os
import statistics
import sys
# Percorsi da variabili d'ambiente (nessun percorso della macchina di prova):
#   RUOTA_QWEN35        cartella del modello Qwen3.5-4B (predefinita: ./Qwen3.5-4B)
#   RUOTA_TF5           transformers 5 installato a parte con pip --target (vuota: quello dell'ambiente)
#   RUOTA_TRAIN_QWEN35  percorso di train_qwen35.py (script di addestramento, non incluso)
import time

if os.environ.get("RUOTA_TF5"):
    sys.path.insert(0, os.environ["RUOTA_TF5"])
import torch  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "train_qwen35", os.environ.get("RUOTA_TRAIN_QWEN35", "train_qwen35.py"))
tq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tq)
from transformers import AutoModelForCausalLM  # noqa: E402
from peft import LoraConfig, get_peft_model, TaskType  # noqa: E402

sys.path.insert(0, r"C:\LaRuota_workspace\ruota_acceleratori")
import ruota_acceleratori  # noqa: E402

stati = ruota_acceleratori.attiva()
BASE = os.environ.get("RUOTA_QWEN35", "Qwen3.5-4B")
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float16, device_map="cuda:0", low_cpu_mem_usage=True)
model.config.use_cache = False
model.requires_grad_(False)
if "--peft-originale" not in sys.argv:
    tq.applica_lora_in_fp32()
model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM, r=32, lora_alpha=64, lora_dropout=0.0,
                                         target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                                         "gate_proj", "up_proj", "down_proj"], bias="none"))
for p in model.parameters():
    if p.requires_grad:
        p.data = p.data.float()
if os.environ.get("RUOTA_LORA", "1") != "0":
    ruota_acceleratori.aggancia_lora_peft()
if "--senza-checkpointing" not in sys.argv:
    model.gradient_checkpointing_enable()
model.enable_input_require_grads()
model.train()
params = [p for p in model.parameters() if p.requires_grad]

lung = [int(v) for v in (sys.argv[sys.argv.index("--lunghezze") + 1] if "--lunghezze" in sys.argv else "768,640").split(",")]
L = max(lung)
torch.manual_seed(0)
vocab = model.config.get_text_config().vocab_size
ids = torch.full((len(lung), L), 0, dtype=torch.long)
lab = torch.full((len(lung), L), -100, dtype=torch.long)
att = torch.zeros((len(lung), L), dtype=torch.long)
for k, n in enumerate(lung):
    ids[k, :n] = torch.randint(0, vocab, (n,))
    att[k, :n] = 1
    lab[k, int(n * 0.4):n] = ids[k, int(n * 0.4):n]       # prompt mascherato, risposta allenata
ids, lab, att = ids.cuda(), lab.cuda(), att.cuda()

if "--confronto" in sys.argv:
    # stessa perdita con e senza attention_mask? (padding a destra, labels -100 sul padding)
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.float16):
        con = model(ids, attention_mask=att, labels=lab).loss.item()
        flash_prima = dict(ruota_acceleratori.contatori_flash())
        senza = model(ids, labels=lab).loss.item()
    print(f"CONFRONTO perdita con maschera {con:.6f}, senza maschera {senza:.6f}, differenza {abs(con - senza):.2e}")
    print("flash con maschera:", flash_prima, "| dopo anche senza:", ruota_acceleratori.contatori_flash(), flush=True)
    sys.exit(0)
MASCHERA = None if "--senza-maschera" in sys.argv else att
opt = torch.optim.AdamW(params, lr=6e-5, weight_decay=0.01)
scaler = torch.amp.GradScaler("cuda", init_scale=128)
PASSI = int(sys.argv[sys.argv.index("--passi") + 1]) if "--passi" in sys.argv else 8
tempi, perdite = [], []
torch.cuda.reset_peak_memory_stats()
for passo in range(PASSI):
    torch.cuda.synchronize()
    t = time.perf_counter()
    with torch.amp.autocast("cuda", dtype=torch.float16):
        loss = model(ids, attention_mask=MASCHERA, labels=lab).loss
    scaler.scale(loss).backward()
    scaler.unscale_(opt)
    torch.nn.utils.clip_grad_norm_(params, 1.0)
    scaler.step(opt)
    scaler.update()
    opt.zero_grad(set_to_none=True)
    torch.cuda.synchronize()
    tempi.append(time.perf_counter() - t)
    perdite.append(loss.item())
token = sum(lung)
med = statistics.median(tempi[2:])
print(f"agganci: {', '.join(k for k, v in stati.items() if v.startswith('acceso'))}"
      f"{' + lora' if os.environ.get('RUOTA_LORA', '1') != '0' else ''}"
      f"{' | SENZA checkpointing' if '--senza-checkpointing' in sys.argv else ''}"
      f"{' | SENZA attention_mask' if '--senza-maschera' in sys.argv else ''}")
print(f"RISULTATO token/passo {token}: {token / med:.0f} token/s, passo mediano {med:.3f} s (min {min(tempi[2:]):.3f}), "
      f"picco {torch.cuda.max_memory_allocated() / 2**30:.2f} GB")
print("perdite:", " ".join(f"{p:.4f}" for p in perdite))
print("flash:", ruota_acceleratori.contatori_flash(), "| lora:", ruota_acceleratori.contatori_lora(), flush=True)

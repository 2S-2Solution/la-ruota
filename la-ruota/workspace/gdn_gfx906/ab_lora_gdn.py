"""A/B sul passo LoRA Qwen3.5-4B (stesso montaggio di diag_gemm\\ab_lora.py): torch puro contro kernel gdn.

    python ab_lora_gdn.py torch|kernel [passi]

Il kernel si aggancia con un monkeypatch nel solo processo (gdn_gfx906.aggancia()).
"""
import statistics
import sys
import time

modo = sys.argv[1]
passi = int(sys.argv[2]) if len(sys.argv) > 2 else 8
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import torch  # noqa: E402

sorgente = open(r"C:\LaRuota_workspace\prova_lora_4b_reale.py", encoding="utf-8").read()
montaggio = sorgente.split('dopo_carico = vram("dopo il caricamento")')[0]
torch.manual_seed(1234)   # stessa inizializzazione dei LoRA in tutti i processi
g = {"__name__": "montaggio"}
exec(compile(montaggio, "prova_lora_4b_reale.py", "exec"), g)
m, allenabili = g["m"], g["allenabili"]

if modo == "kernel":
    import gdn_gfx906
    from transformers.models.qwen3_5 import modeling_qwen3_5 as mq
    gdn_gfx906.aggancia(mq)
    print("kernel gdn agganciato:", mq.torch_chunk_gated_delta_rule.__module__, flush=True)
else:
    print("percorso torch puro", flush=True)

torch.manual_seed(0)
opt = torch.optim.AdamW(allenabili, lr=1e-4)
scaler = torch.amp.GradScaler("cuda", init_scale=128.0)
idx = torch.randint(0, m.config.get_text_config().vocab_size, (1, 256), device="cuda")
tempi, perdite, norme = [], [], []
for passo in range(passi):
    torch.cuda.synchronize(); t = time.perf_counter()
    opt.zero_grad(set_to_none=True)
    with torch.amp.autocast("cuda", dtype=torch.float16):
        perdita = m(idx, labels=idx).loss
    scaler.scale(perdita).backward()
    scaler.unscale_(opt)
    norme.append(torch.nn.utils.clip_grad_norm_(allenabili, 1e9).item())
    scaler.step(opt); scaler.update()
    torch.cuda.synchronize(); tempi.append(time.perf_counter() - t); perdite.append(perdita.item())
print("perdite:", " ".join(f"{p:.4f}" for p in perdite))
print("norme  :", " ".join(f"{n:.4f}" for n in norme))
print(f"passo mediano (dal 3o): {statistics.median(tempi[2:]):.3f} s   tutti: " + " ".join(f"{t:.2f}" for t in tempi))
print(f"picco memoria: {torch.cuda.max_memory_allocated() / 2**30:.2f} GB", flush=True)

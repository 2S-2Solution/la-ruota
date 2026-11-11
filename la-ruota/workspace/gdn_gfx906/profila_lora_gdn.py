"""Profilo del passo LoRA Qwen3.5-4B col kernel gdn agganciato (come diag_gemm\profila_lora.py)."""
import sys, time
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import torch
sorgente = open(r"C:\LaRuota_workspace\prova_lora_4b_reale.py", encoding="utf-8").read()
montaggio = sorgente.split('dopo_carico = vram("dopo il caricamento")')[0]
torch.manual_seed(1234)
g = {"__name__": "montaggio"}
exec(compile(montaggio, "prova_lora_4b_reale.py", "exec"), g)
m, allenabili = g["m"], g["allenabili"]
if len(sys.argv) < 2 or sys.argv[1] != "torch":
    import gdn_gfx906
    from transformers.models.qwen3_5 import modeling_qwen3_5 as mq
    gdn_gfx906.aggancia(mq)
opt = torch.optim.AdamW(allenabili, lr=1e-4)
scaler = torch.amp.GradScaler("cuda", init_scale=128.0)
idx = torch.randint(0, m.config.get_text_config().vocab_size, (1, 256), device="cuda")
def passo():
    opt.zero_grad(set_to_none=True)
    with torch.amp.autocast("cuda", dtype=torch.float16):
        perdita = m(idx, labels=idx).loss
    scaler.scale(perdita).backward()
    scaler.step(opt); scaler.update()
for _ in range(3):
    passo()
torch.cuda.synchronize()
t = time.perf_counter(); passo(); torch.cuda.synchronize(); print(f"passo senza profiler: {time.perf_counter() - t:.2f} s", flush=True)
from torch.profiler import profile, ProfilerActivity
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
    passo(); torch.cuda.synchronize()
tab = prof.key_averages()
campo = "self_device_time_total" if hasattr(tab[0], "self_device_time_total") else "self_cuda_time_total"
tot_gpu = sum(getattr(e, campo) for e in tab)
print(f"tempo GPU totale (somma self): {tot_gpu/1e3:.1f} ms")
print(tab.table(sort_by=campo, row_limit=25, max_name_column_width=60))
print(tab.table(sort_by="self_cpu_time_total", row_limit=12, max_name_column_width=60))

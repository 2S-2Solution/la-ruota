"""Operazioni GPU di uno strato Qwen3_5GatedDeltaNet (pesi congelati, come nel LoRA), col profiler."""
import sys
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import torch
import banco_strato as bs
from torch.profiler import profile, ProfilerActivity
S = int(sys.argv[1]) if len(sys.argv) > 1 else 512
modo = sys.argv[2] if len(sys.argv) > 2 else "strato"
cfg = bs.configurazione()
m = bs.strato(cfg, torch.float16)
for p in m.parameters():
    p.requires_grad_(False)
bs.gdn.aggancia(bs.mq, strato=(modo == "strato"))
h = torch.randn(1, S, cfg.hidden_size, device="cuda", dtype=torch.float16, requires_grad=True)
dy = torch.randn_like(h)
for _ in range(3): m(h).backward(dy)
torch.cuda.synchronize()
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA], record_shapes=True) as prof:
    for _ in range(5): m(h).backward(dy)
    torch.cuda.synchronize()
tab = prof.key_averages(group_by_input_shape=True)
campo = "self_device_time_total" if hasattr(tab[0], "self_device_time_total") else "self_cuda_time_total"
tot = sum(getattr(e, campo) for e in tab) / 5
print(f"{modo} S{S}: tempo GPU per avanti+indietro {tot/1e3:.2f} ms")
for e in sorted(tab, key=lambda e: -getattr(e, campo))[:14]:
    if getattr(e, campo) > 0:
        print(f"  {getattr(e, campo)/5/1e3:7.3f} ms  x{e.count//5:<3} {e.key[:34]:34s} {str(e.input_shapes)[:70]}")

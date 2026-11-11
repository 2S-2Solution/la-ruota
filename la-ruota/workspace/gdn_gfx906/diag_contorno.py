"""Quanto tempo GPU va nel contorno torch di chunk_gated_delta_rule (forma del 4B), col profiler."""
import sys
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import torch, gdn_gfx906 as gdn
from torch.profiler import profile, ProfilerActivity
B, S, H, D = 1, 256, 32, 128
q = torch.randn(B, S, H, D, device="cuda", dtype=torch.float16, requires_grad=True)
k = torch.randn(B, S, H, D, device="cuda", dtype=torch.float16, requires_grad=True)
v = torch.randn(B, S, H, D, device="cuda", dtype=torch.float16, requires_grad=True)
g = (-torch.rand(B, S, H, device="cuda")).requires_grad_(True)
beta = torch.rand(B, S, H, device="cuda", dtype=torch.float16, requires_grad=True)
do = torch.randn(B, S, H, D, device="cuda", dtype=torch.float16)
def passo():
    o, _ = gdn.chunk_gated_delta_rule(q, k, v, g, beta, use_qk_l2norm_in_kernel=True)
    o.backward(do)
for _ in range(5): passo()
torch.cuda.synchronize()
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
    for _ in range(10): passo()
    torch.cuda.synchronize()
tab = prof.key_averages()
campo = "self_device_time_total" if hasattr(tab[0], "self_device_time_total") else "self_cuda_time_total"
tot = sum(getattr(e, campo) for e in tab) / 10
print(f"tempo GPU a chiamata (avanti+indietro): {tot/1e3:.3f} ms")
for e in sorted(tab, key=lambda e: -getattr(e, campo))[:14]:
    if getattr(e, campo) > 0:
        print(f"  {e.key[:50]:50s} {getattr(e, campo)/10/1e3:7.3f} ms  {e.count//10:4d} chiamate")

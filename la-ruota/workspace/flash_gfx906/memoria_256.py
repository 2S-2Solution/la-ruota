"""Memoria di picco in più di avanti+indietro, math contro fa, D=256 (B1, 16 teste di query)."""
import sys, torch
import torch.nn.functional as F
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_gfx906 as fa  # noqa: E402


def picco(fn):
    torch.cuda.synchronize(); torch.cuda.empty_cache()
    base = torch.cuda.memory_allocated()
    torch.cuda.reset_peak_memory_stats()
    fn(); torch.cuda.synchronize()
    return (torch.cuda.max_memory_allocated() - base) / 2**20


for S, Hk in ((1024, 16), (4096, 16), (4096, 4), (8192, 4)):
    H, D = 16, 256
    q, do = (torch.randn(1, H, S, D, device="cuda", dtype=torch.float16) for _ in range(2))
    k, v = (torch.randn(1, Hk, S, D, device="cuda", dtype=torch.float16) for _ in range(2))
    rip = lambda x: x.repeat_interleave(H // Hk, dim=1)

    def gm():
        a, b, d = (x.detach().requires_grad_() for x in (q, k, v))
        F.scaled_dot_product_attention(a, rip(b), rip(d), is_causal=True).backward(do)

    def gf():
        a, b, d = (x.detach().requires_grad_() for x in (q, k, v))
        fa.attenzione(a, b, d, causale=True).backward(do)
    print(f"  S{S} H{H}/{Hk} D{D} causale: math {picco(gm):8.0f} MB, fa {picco(gf):6.0f} MB", flush=True)

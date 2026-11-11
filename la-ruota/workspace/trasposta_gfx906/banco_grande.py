import sys, torch
sys.path.insert(0, r"C:\LaRuota_workspace\trasposta_gfx906")
from trasposta_gfx906 import trasposta
def gbs(fn, byte, n=20):
    for _ in range(3): fn()
    e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    e0.record()
    for _ in range(n): fn()
    e1.record(); torch.cuda.synchronize(); return 2 * byte / (e0.elapsed_time(e1) / n / 1e3) / 1e9
for forma, dt in (((8, 512, 8192), torch.float16), ((8, 8192, 512), torch.float16), ((4, 512, 8192), torch.float32), ((1, 4096, 8192), torch.float16)):
    x = torch.randn(forma, device="cuda", dtype=dt); nb = x.numel() * x.element_size()
    print(f"  {str(forma):16s} {str(dt)[-7:]} {nb >> 20} MB  torch {gbs(lambda: x.transpose(-1, -2).contiguous(), nb):5.0f}   tessere {gbs(lambda: trasposta(x), nb):5.0f}   contigua {gbs(lambda: x.clone(), nb):5.0f} GB/s", flush=True)

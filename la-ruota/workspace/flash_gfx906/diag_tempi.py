import time, sys, torch, torch.nn.functional as F
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa2_avanti
for S, D in ((1024, 64), (4096, 64), (4096, 128)):
    q, k, v = [torch.randn(1, 16, S, D, device="cuda", dtype=torch.float16) for _ in range(3)]
    for nome, fn in (("math", lambda: F.scaled_dot_product_attention(q, k, v)),
                     ("fa2", lambda: fa2_avanti.flash_avanti(q, k, v)),
                     ("matmul QK", lambda: q @ k.transpose(-1, -2))):
        fn(); torch.cuda.synchronize()
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        t = time.perf_counter(); e0.record(); fn(); e1.record(); t_inv = time.perf_counter() - t
        torch.cuda.synchronize(); t_tot = time.perf_counter() - t
        print(f"  S{S} D{D} {nome:10s} eventi GPU {e0.elapsed_time(e1):8.2f} ms   invio CPU {t_inv*1000:8.2f} ms   totale {t_tot*1000:8.2f} ms", flush=True)

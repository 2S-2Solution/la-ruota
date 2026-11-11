import sys, time, torch
sys.path.insert(0, r"C:\LaRuota_workspace\trasposta_gfx906")
from trasposta_gfx906 import trasposta
def gbs(fn, byte, n=50):
    for _ in range(3): fn()
    torch.cuda.synchronize(); t = time.perf_counter()
    for _ in range(n): fn()
    torch.cuda.synchronize(); return 2 * byte / ((time.perf_counter() - t) / n) / 1e9
tutto_ok = True
for forma, dt in (((1, 512, 8192), torch.float16), ((1, 8192, 512), torch.float16), ((1, 512, 8192), torch.float32),
                  ((4, 1000, 777), torch.float16), ((1, 8192, 515), torch.float16), ((32, 64, 128), torch.float32), ((3, 5, 7), torch.float16)):
    x = torch.randn(forma, device="cuda", dtype=dt)
    ok = torch.equal(trasposta(x), x.transpose(-1, -2).contiguous()); tutto_ok &= ok
    nb = x.numel() * x.element_size()
    t = gbs(lambda: x.transpose(-1, -2).contiguous(), nb); n = gbs(lambda: trasposta(x), nb); c = gbs(lambda: x.clone(), nb)
    print(f"  {str(forma):16s} {str(dt)[-7:]}  torch {t:5.0f} GB/s   tessere {n:5.0f} GB/s ({n / t:4.1f}x)   copia contigua {c:5.0f}   {'giusto' if ok else 'SBAGLIATO'}", flush=True)
print("ESITO", "giusto" if tutto_ok else "SBAGLIATO")

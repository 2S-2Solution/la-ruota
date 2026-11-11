import time, torch
a = torch.randn(4096, 4096, device="cuda", dtype=torch.float16); b = torch.randn_like(a)
for _ in range(3): a @ b
torch.cuda.synchronize()
for giro in range(3):
    t = time.perf_counter()
    for _ in range(20): a @ b
    torch.cuda.synchronize(); dt = (time.perf_counter() - t) / 20
    print(f"  matmul fp16 4096^3: {dt*1000:.2f} ms  {2*4096**3/dt/1e12:.2f} TFLOPS", flush=True)

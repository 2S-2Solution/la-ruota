"""Il blocco residuo della RUOTA: l'allocazione GPU.
Si sale per gradi, cosi' si vede esattamente dove si ferma."""
import faulthandler, sys
faulthandler.enable()
import torch
print(f"  torch {torch.__version__}")
print(f"  is_available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    sys.exit(1)
print(f"  device: {torch.cuda.get_device_name(0)}")
p = torch.cuda.get_device_properties(0)
print(f"  proprieta': {p.name}  {p.total_memory/2**30:.2f} GB  {p.multi_processor_count} CU")
sys.stdout.flush()

passi = [
    ("torch.empty(16)",        lambda: torch.empty(16, device="cuda")),
    ("torch.zeros(1024)",      lambda: torch.zeros(1024, device="cuda")),
    ("copia CPU->GPU",         lambda: torch.arange(1024).cuda()),
    ("copia GPU->CPU",         lambda: torch.arange(1024).cuda().cpu()),
    ("somma elementwise",      lambda: torch.ones(1024, device="cuda") + 1),
    ("riduzione sum",          lambda: torch.ones(4096, device="cuda").sum()),
    ("matmul 256",             lambda: torch.randn(256, 256, device="cuda") @ torch.randn(256, 256, device="cuda")),
    ("matmul 1024 fp16",       lambda: (torch.randn(1024,1024,device="cuda",dtype=torch.float16) @
                                        torch.randn(1024,1024,device="cuda",dtype=torch.float16))),
    ("backward",               lambda: (lambda x: (x.pow(2).sum().backward(), x.grad))(
                                        torch.randn(64, device="cuda", requires_grad=True))),
]
for nome, fn in passi:
    sys.stdout.flush()
    try:
        r = fn()
        torch.cuda.synchronize()
        if torch.is_tensor(r):
            v = float(r.flatten()[0].float()) if r.numel() else 0.0
            print(f"  {nome:<24} OK   primo valore {v:.4f}")
        else:
            print(f"  {nome:<24} OK")
    except Exception as e:
        print(f"  {nome:<24} {type(e).__name__}: {str(e)[:90]}")
        break
    sys.stdout.flush()
print("  --- fine")

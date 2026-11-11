"""Verifica dell'allocazione GPU dopo il passaggio al runtime Adrenalin (amdhip64.dll).

Il blocco storico era un access violation (0xC0000005) su torch.empty(...device='cuda'),
causato dagli stub del proxy amdhip64_6.dll. Qui si controlla, in ordine crescente di
impegno, che la catena allocazione -> copia -> calcolo regga.
"""
import os
import sys
import traceback

import torch


def step(nome, fn):
    try:
        out = fn()
        print(f"  OK   {nome}: {out}")
        return True
    except Exception as exc:
        print(f"  FAIL {nome}: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return False


print(f"torch {torch.__version__}")
print(f"is_available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    sys.exit("GPU non disponibile: stop")

print(f"device: {torch.cuda.get_device_name(0)}")
props = torch.cuda.get_device_properties(0)
print(f"arch: {props.gcnArchName}  VRAM: {props.total_memory / 2**30:.2f} GB  CU: {props.multi_processor_count}")

print("\n[1] allocazione")
if not step("empty(16)", lambda: torch.empty(16, device="cuda").shape):
    sys.exit("allocazione fallita: stop")

print("\n[2] host -> device -> host")
def roundtrip():
    a = torch.arange(1024, dtype=torch.float32)
    g = a.to("cuda")
    b = g.cpu()
    assert torch.equal(a, b), "roundtrip alterato"
    return "1024 elementi identici"
step("roundtrip", roundtrip)

print("\n[3] elementwise su GPU")
def elementwise():
    g = torch.arange(1024, dtype=torch.float32, device="cuda")
    r = (g * 2 + 1).cpu()
    exp = torch.arange(1024, dtype=torch.float32) * 2 + 1
    assert torch.equal(r, exp), "risultato errato"
    return "mul+add corretti"
step("elementwise", elementwise)

print("\n[4] matmul vs CPU")
def matmul():
    torch.manual_seed(0)
    a = torch.randn(512, 512)
    b = torch.randn(512, 512)
    ref = a @ b
    got = (a.cuda() @ b.cuda()).cpu()
    err = (ref - got).abs().max().item()
    assert err < 1e-3, f"scostamento {err}"
    return f"errore max {err:.2e}"
step("matmul 512", matmul)

print("\n[5] autograd")
def autograd():
    x = torch.randn(256, 256, device="cuda", requires_grad=True)
    (x * x).sum().backward()
    err = (x.grad - 2 * x).abs().max().item()
    assert err < 1e-4, f"gradiente errato {err}"
    return f"grad corretto (err {err:.2e})"
step("autograd", autograd)

print("\n[6] benchmark fp16 4096^3 (baseline ZLUDA ~2.3 TFLOPS)")
def bench():
    import time
    n = 4096
    a = torch.randn(n, n, device="cuda", dtype=torch.float16)
    b = torch.randn(n, n, device="cuda", dtype=torch.float16)
    for _ in range(3):
        a @ b
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    iters = 10
    for _ in range(iters):
        a @ b
    torch.cuda.synchronize()
    dt = (time.perf_counter() - t0) / iters
    tflops = 2 * n**3 / dt / 1e12
    return f"{tflops:.2f} TFLOPS ({dt*1000:.1f} ms/iter)"
step("gemm fp16", bench)

print("\nfine")

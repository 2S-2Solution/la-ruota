"""LA RUOTA — smoke test post-build di torch ROCm nativo Windows gfx906.

Esegue una scala di verifiche dalla piu' semplice alla piu' impegnativa e si ferma
al primo fallimento REALE, distinguendo pero' cio' che e' atteso non funzionare su
gfx906 (aotriton/SDPA) da cio' che sarebbe un difetto della build.

Uso (venv di test pulito, NON quello di build):
    python smoke_laruota.py
"""
import os
import sys
import time
import traceback

# gfx906 non ha aotriton: SDPA flash/mem-efficient non esistono in questa build.
os.environ.setdefault("HSA_OVERRIDE_GFX_VERSION", "9.0.6")
os.environ.setdefault("PYTORCH_JIT_DISABLE_JITERATOR", "1")

RESULTS = []


def step(name, fn, fatal=True):
    t0 = time.time()
    try:
        detail = fn()
        RESULTS.append(("PASS", name, detail, time.time() - t0))
        print(f"[PASS] {name}: {detail}")
        return True
    except Exception as exc:  # noqa: BLE001
        RESULTS.append(("FAIL", name, repr(exc), time.time() - t0))
        print(f"[FAIL] {name}: {exc}")
        if os.environ.get("SMOKE_VERBOSE"):
            traceback.print_exc()
        if fatal:
            print("\n>>> fallimento bloccante, mi fermo qui")
            summary()
            sys.exit(1)
        return False


def summary():
    print("\n" + "=" * 60)
    npass = sum(1 for r in RESULTS if r[0] == "PASS")
    nfail = sum(1 for r in RESULTS if r[0] == "FAIL")
    print(f"RISULTATO: {npass} PASS, {nfail} FAIL")
    for status, name, detail, dt in RESULTS:
        print(f"  [{status}] {name} ({dt:.2f}s) — {detail}")
    print("=" * 60)


# ---------------------------------------------------------------- import
import torch  # noqa: E402


def t_import():
    return f"torch {torch.__version__}, file={os.path.dirname(torch.__file__)}"


def t_hip_build():
    # su build ROCm torch.version.hip e' valorizzato e torch.version.cuda e' None
    return f"version.hip={torch.version.hip}, version.cuda={torch.version.cuda}"


def t_available():
    ok = torch.cuda.is_available()
    if not ok:
        raise RuntimeError(
            "torch.cuda.is_available() == False — device detection ISA fallita "
            "(vedi TheRock issue #1300/#1904): controlla HSA_OVERRIDE_GFX_VERSION "
            "e che amdhip64.dll del driver sia raggiungibile"
        )
    return f"device_count={torch.cuda.device_count()}"


def t_device_name():
    return f"{torch.cuda.get_device_name(0)}"


def t_vram():
    gb = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
    if gb < 15.0:
        raise RuntimeError(f"VRAM attesa ~16 GB, letta {gb:.2f} GB")
    return f"{gb:.2f} GB"


def t_arch():
    props = torch.cuda.get_device_properties(0)
    arch = getattr(props, "gcnArchName", "?")
    return f"gcnArch={arch}, MP={props.multi_processor_count}"


# ---------------------------------------------------------------- tensori
def t_h2d():
    a = torch.ones(1024, 1024)
    b = a.cuda()
    if abs(b.sum().item() - 1024 * 1024) > 1:
        raise RuntimeError(f"somma errata dopo copia H2D: {b.sum().item()}")
    return "copia host->device + reduction OK"


def t_elementwise():
    a = torch.randn(4096, 4096, device="cuda")
    b = (a * 2.0 + 1.0)
    ref = (a.cpu() * 2.0 + 1.0)
    err = (b.cpu() - ref).abs().max().item()
    if err > 1e-4:
        raise RuntimeError(f"errore elementwise {err}")
    return f"max_err={err:.2e}"


def t_matmul_fp32():
    a = torch.randn(1024, 1024, device="cuda")
    b = torch.randn(1024, 1024, device="cuda")
    c = a @ b
    ref = a.cpu() @ b.cpu()
    err = (c.cpu() - ref).abs().max().item()
    if err > 1e-2:
        raise RuntimeError(f"errore matmul fp32 {err}")
    return f"max_err={err:.2e}"


def t_bench_fp16():
    a = torch.randn(4096, 4096, dtype=torch.float16, device="cuda")
    b = torch.randn(4096, 4096, dtype=torch.float16, device="cuda")
    for _ in range(5):
        _ = a @ b
    torch.cuda.synchronize()
    t0 = time.time()
    iters = 20
    for _ in range(iters):
        _ = a @ b
    torch.cuda.synchronize()
    dur = (time.time() - t0) / iters
    tflops = 2 * 4096 ** 3 / dur / 1e12
    return f"{dur*1000:.2f} ms/iter, {tflops:.2f} TFLOPS (ZLUDA baseline ~2.3, target 18-22)"


# ---------------------------------------------------------------- autograd
def t_backward():
    x = torch.randn(256, 256, device="cuda", requires_grad=True)
    y = (x * x).sum()
    y.backward()
    if x.grad is None:
        raise RuntimeError("grad None dopo backward")
    err = (x.grad.cpu() - 2 * x.detach().cpu()).abs().max().item()
    if err > 1e-3:
        raise RuntimeError(f"gradiente errato, err={err}")
    return f"grad OK, max_err={err:.2e}"


def t_linear_train():
    torch.manual_seed(0)
    net = torch.nn.Linear(512, 512).cuda()
    opt = torch.optim.AdamW(net.parameters(), lr=1e-3)
    lossfn = torch.nn.MSELoss()
    x = torch.randn(32, 512, device="cuda")
    tgt = torch.randn(32, 512, device="cuda")
    first = last = None
    for i in range(20):
        out = net(x)
        loss = lossfn(out, tgt)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if i == 0:
            first = loss.item()
        last = loss.item()
    if not (last < first):
        raise RuntimeError(f"loss non scende: {first:.4f} -> {last:.4f}")
    return f"loss {first:.4f} -> {last:.4f} in 20 step"


def t_layernorm():
    ln = torch.nn.LayerNorm(512).cuda()
    x = torch.randn(16, 512, device="cuda", requires_grad=True)
    y = ln(x).sum()
    y.backward()
    return "LayerNorm forward+backward OK"


def t_softmax():
    x = torch.randn(64, 1000, device="cuda")
    p = torch.softmax(x, dim=-1)
    s = p.sum(dim=-1)
    err = (s - 1.0).abs().max().item()
    if err > 1e-3:
        raise RuntimeError(f"softmax non normalizzata, err={err}")
    return f"max_err={err:.2e}"


def t_conv2d():
    conv = torch.nn.Conv2d(3, 16, 3, padding=1).cuda()
    x = torch.randn(4, 3, 32, 32, device="cuda")
    y = conv(x)
    y.sum().backward()
    return f"MIOpen conv2d OK, out={tuple(y.shape)}"


def main():
    print("=" * 60)
    print("LA RUOTA — smoke test torch ROCm nativo Windows gfx906")
    print("=" * 60)

    step("import torch", t_import)
    step("build ROCm", t_hip_build, fatal=False)
    step("cuda.is_available", t_available)
    step("device name", t_device_name)
    step("VRAM", t_vram, fatal=False)
    step("arch", t_arch, fatal=False)

    step("copia H2D + reduction", t_h2d)
    step("elementwise", t_elementwise)
    step("matmul fp32 correttezza", t_matmul_fp32)
    step("bench matmul fp16 4096^3", t_bench_fp16, fatal=False)

    step("autograd backward", t_backward)
    step("softmax", t_softmax, fatal=False)
    step("LayerNorm fwd+bwd", t_layernorm, fatal=False)
    step("conv2d MIOpen", t_conv2d, fatal=False)
    step("training Linear+AdamW 20 step", t_linear_train, fatal=False)

    summary()
    nfail = sum(1 for r in RESULTS if r[0] == "FAIL")
    if nfail == 0:
        print("\nLA RUOTA GIRA")
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()

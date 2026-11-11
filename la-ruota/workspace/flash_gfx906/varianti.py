"""Varianti del kernel: blocco di tasti CH e onde minime ONDE. Per ognuna:
correttezza contro fp32, registri usati (dal disassemblato), tempo mediano."""
import re
import statistics
import subprocess
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_avanti  # noqa: E402

OBJDUMP = r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-objdump.exe"


def registri(extra, hd):
    codice = fa_avanti._compila(hd, extra)
    p = r"C:\LaRuota_workspace\flash_gfx906\tmp.co"
    open(p, "wb").write(codice.raw)
    s = subprocess.run([OBJDUMP, "-d", "--mcpu=gfx906", p], capture_output=True, text=True).stdout
    v = max((int(x) for x in re.findall(r"\bv\[?(\d+)", s)), default=0) + 1
    spill = len(re.findall(r"scratch_|buffer_store_dword|buffer_load_dword", s))
    return v, spill


def misura(fn, giri=5):
    torch.cuda.synchronize(); t0 = time.perf_counter()
    for _ in range(giri):
        fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) * 1000 / giri


for hd, S in ((64, 2048), (128, 2048)):
    g = torch.Generator(device="cuda").manual_seed(0)
    q, k, v = [torch.randn(1, 16, S, hd, device="cuda", dtype=torch.float16, generator=g) for _ in range(3)]
    rif = F.scaled_dot_product_attention(q.float(), k.float(), v.float())
    fm = lambda: F.scaled_dot_product_attention(q, k, v)
    print(f"\n  HEAD_DIM={hd} S={S}")
    print(f"  {'variante':16s} {'VGPR':>5} {'spill':>6} {'scarto':>9} {'ms flash':>9} {'ms math':>8} {'rapporto':>9}")
    for ch in (4, 8, 16):
        for onde in (1, 2, 4):
            extra = (f"-DCH={ch}", f"-DONDE={onde}")
            try:
                vg, sp = registri(extra, hd)
                o = fa_avanti.flash_avanti(q, k, v, extra=extra)
                torch.cuda.synchronize()
                s = ((o.float() - rif).abs() / rif.abs().clamp_min(1e-2)).max().item()
                ff = lambda: fa_avanti.flash_avanti(q, k, v, extra=extra)
                tf, tm = [], []
                for _ in range(5):
                    tm.append(misura(fm)); tf.append(misura(ff))
                f, m = statistics.median(tf), statistics.median(tm)
                print(f"  CH={ch:<2} ONDE={onde:<4} {vg:5d} {sp:6d} {s:9.2e} {f:9.2f} {m:8.2f} {m / f:8.2f}x")
            except Exception as e:
                print(f"  CH={ch:<2} ONDE={onde:<4} ERRORE {type(e).__name__}: {str(e)[:70]}")

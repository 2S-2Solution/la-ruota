"""Banco di gemm_gfx906.lineare_misto (fp16 x fp16 -> accumulo e uscita fp32) su forme di un modello tabellare. A GPU LIBERA.
Correttezza: contro F.linear fp64 (stessi valori fp32 d'ingresso) e confronto con F.linear fp32 (rocBLAS) e con il
fp16 dell'autocast (uscita fp16). Tempi: contro F.linear fp32 (Tensile instradato) e fp16 autocast.
    python prova_misto.py [--tempi]
"""
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\LaRuota_workspace\gemm_gfx906")
import gemm_gfx906 as gg  # noqa: E402

# (righe, ingressi, uscite, con bias) - forme registrate da un modello tabellare
FORME = [(1256, 1024, 512, 0), (1256, 512, 512, 0), (1000, 512, 512, 0), (1256, 512, 1024, 0), (8000, 64, 64, 1),
         (2048, 64, 64, 1), (157000, 128, 128, 0), (126856, 128, 128, 0), (151976, 256, 128, 0), (151976, 128, 256, 0),
         (15488, 128, 128, 0), (1000, 512, 384, 1), (123904, 64, 16, 1), (37, 96, 77, 1)]


def correttezza():
    tutti = True
    for R, K, N, cb in FORME:
        torch.manual_seed(R + K + N)
        x = torch.randn(R, K, device="cuda")
        W = torch.randn(N, K, device="cuda") / K ** 0.5
        b = torch.randn(N, device="cuda") * 0.1 if cb else None
        y = gg.lineare_misto(x, W, b)
        r = F.linear(x.double(), W.double(), b.double() if b is not None else None)
        e = ((y.double() - r).abs().max() / r.abs().max()).item()
        e32 = ((F.linear(x, W, b).double() - r).abs().max() / r.abs().max()).item()
        with torch.autocast("cuda", dtype=torch.float16):
            y16 = F.linear(x, W, b)
        e16 = ((y16.double() - r).abs().max() / r.abs().max()).item()
        # atteso: arrotondamento degli ingressi a fp16 (~ 2^-11 / sqrt(K) relativo), meglio del fp16 con uscita fp16
        ok = y.dtype == torch.float32 and y.shape == r.shape and e < max(4e-3, 0.8 * e16)
        print(f"  [{R},{K}] -> {N}{' +b' if cb else '   '}: misto {e:.1e} | fp32 {e32:.1e} | fp16 autocast {e16:.1e}"
              f"  {'ok' if ok else '>>> SBAGLIATO'}", flush=True)
        tutti &= ok
    print("ESITO", "ok" if tutti else "SBAGLIATO")


def tempi():
    def ms(fn, n=20):
        for _ in range(3):
            fn()
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        e0.record()
        for _ in range(n):
            fn()
        e1.record(); torch.cuda.synchronize()
        return e0.elapsed_time(e1) / n
    print("\n  ms: fp32 (rocBLAS) | misto | fp16 autocast")
    for R, K, N, cb in FORME:
        x = torch.randn(R, K, device="cuda"); W = torch.randn(N, K, device="cuda"); b = torch.randn(N, device="cuda") if cb else None
        t32 = ms(lambda: F.linear(x, W, b))
        tmi = ms(lambda: gg.lineare_misto(x, W, b))

        def a16():
            with torch.autocast("cuda", dtype=torch.float16):
                return F.linear(x, W, b)
        t16 = ms(a16)
        print(f"  [{R},{K}] -> {N}: {t32:7.3f} | {tmi:7.3f} ({t32 / tmi:4.2f}x) | {t16:7.3f}", flush=True)


if __name__ == "__main__":
    correttezza()
    if "--tempi" in sys.argv:
        tempi()

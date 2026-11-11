"""Banco della GEMM gfx906.
    python banco.py              # correttezza: 4 disposizioni x split, Linear avanti/indietro, contro fp64 e rocBLAS
    python banco.py --tempi      # TFLOPS per forma del passo LoRA (512 token): rocBLAS contro ogni split
                                 # (minimo su lanci intercalati: indicativo anche a GPU occupata)
    python banco.py --tara       # A GPU LIBERA: sceglie per forma rocBLAS o split, scrive tarature.json
"""
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\LaRuota_workspace\gemm_gfx906")
import gemm_gfx906 as gg  # noqa: E402


def operandi(M, N, K, akc, bkc, seme=0):
    torch.manual_seed(seme)
    a = torch.randn(M, K, device="cuda").half() if akc else torch.randn(K, M, device="cuda").half().t()
    b = torch.randn(N, K, device="cuda").half().t() if bkc else torch.randn(K, N, device="cuda").half()
    return a, b


def errore(c, rif):
    return ((c.double() - rif).abs().max() / rif.abs().max()).item()


def correttezza():
    tutti = True
    for M, N, K in ((512, 2560, 4096), (256, 384, 160), (1024, 1024, 2560), (128, 128, 32)):
        for akc in (1, 0):
            for bkc in (1, 0):
                a, b = operandi(M, N, K, akc, bkc, M + N + K)
                rif = a.double().cpu() @ b.double().cpu()
                eo = errore(torch.mm(a, b).cpu(), rif)
                riga = f"  M{M:<5} N{N:<5} K{K:<5} A {'K-contigua' if akc else 'M-contigua'} B {'K-contigua' if bkc else 'N-contigua'}  rocBLAS {eo:.1e}  "
                for s in (1, 2, 3, 4, 8):
                    if K % (32 * s):
                        continue
                    ef = errore(gg.mm(a, b, split=s).cpu(), rif)
                    buono = ef <= max(1.5 * eo, 1e-3)
                    tutti &= buono
                    riga += f" s{s} {ef:.1e}{'' if buono else '!'}"
                print(riga, flush=True)
    # Linear completa
    torch.manual_seed(1)
    x = torch.randn(512, 2560, device="cuda", dtype=torch.float16, requires_grad=True)
    W = (torch.randn(4096, 2560, device="cuda") * 0.02).half().requires_grad_()
    bias = torch.randn(4096, device="cuda", dtype=torch.float16, requires_grad=True)
    dy = torch.randn(512, 4096, device="cuda", dtype=torch.float16)
    gg.sgancia()
    y0 = F.linear(x, W, bias); y0.backward(dy); g0 = (x.grad.clone(), W.grad.clone(), bias.grad.clone())
    x.grad = W.grad = bias.grad = None
    gg.aggancia(); gg.NON_TARATE = "stima"            # forza il kernel nuovo anche sulle forme non tarate
    y1 = F.linear(x, W, bias); y1.backward(dy); g1 = (x.grad, W.grad, bias.grad)
    gg.sgancia(); gg.NON_TARATE = "rocblas"
    x64, W64, b64 = (t.detach().double().cpu().requires_grad_() for t in (x, W, bias))
    y64 = torch.nn.functional.linear(x64, W64, b64); y64.backward(dy.double().cpu())
    riga = "  Linear 512x2560 -> 4096 con bias:"
    for nome, a0, a1, r in (("y", y0, y1, y64), ("dx", g0[0], g1[0], x64.grad), ("dW", g0[1], g1[1], W64.grad),
                            ("db", g0[2], g1[2], b64.grad)):
        eo, ef = errore(a0.detach().cpu(), r.detach()), errore(a1.detach().cpu(), r.detach())
        buono = ef <= max(1.5 * eo, 1e-3)
        tutti &= buono
        riga += f"  {nome} {ef:.1e}/{eo:.1e}{'' if buono else '!'}"
    print(riga, flush=True)
    print("ESITO", "ok" if tutti else "SBAGLIATO", "  (errore fusa/rocBLAS relativo a CPU fp64)")


def tempo(fn, n=30):
    """Minimo e mediana su n lanci isolati (eventi), dopo riscaldamento."""
    for _ in range(3):
        fn()
    t = []
    for _ in range(n):
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        e0.record(); fn(); e1.record(); torch.cuda.synchronize()
        t.append(e0.elapsed_time(e1))
    t.sort()
    return t[0], t[len(t) // 2]


# forme del passo LoRA a 512 token: (M, N, K, A K-contigua, B K-contigua, nome)
FORME = [
    (512, 9216, 2560, 1, 1, "gate/up avanti   x W^T"),
    (512, 2560, 9216, 1, 0, "gate/up dX       dY W"),
    (9216, 2560, 512, 0, 0, "gate/up dW       dY^T X"),
    (512, 2560, 4096, 1, 1, "o_proj avanti"),
    (512, 4096, 2560, 1, 0, "o_proj dX"),
    (512, 4096, 2560, 1, 1, "q avanti 2560->4096"),
    (512, 2560, 4096, 1, 0, "q dX"),
    (512, 8192, 2560, 1, 1, "2560->8192 avanti"),
    (512, 2560, 8192, 1, 0, "2560->8192 dX"),
    (512, 2560, 9216, 1, 1, "down avanti 9216->2560"),
    (512, 9216, 2560, 1, 0, "down dX"),
]


def tempi():
    print("  TFLOPS (minimo | mediana): rocBLAS  contro  split 1/2/3/4/6 della GEMM nuova (* = scelta automatica)")
    for M, N, K, akc, bkc, nome in FORME:
        a, b = operandi(M, N, K, akc, bkc)
        flop = 2 * M * N * K
        tf = lambda ms: flop / ms / 1e9
        r = tempo(lambda: torch.mm(a, b))
        riga = f"  {nome:24s} {M:>5}x{N:<5}x{K:<5} rocBLAS {tf(r[0]):5.1f} | {tf(r[1]):5.1f}   "
        scelta = gg.scegli_split(M, N, K)
        for s in (1, 2, 3, 4, 6):
            if K % (32 * s):
                continue
            t = tempo(lambda: gg.mm(a, b, split=s))
            riga += f" s{s}{'*' if s == scelta else ' '} {tf(t[0]):5.1f}|{tf(t[1]):5.1f}"
        print(riga, flush=True)


def tara_qwen4b_ruota():
    """Forme del passo vero di train_qwen35 (Ruota), base fp16 congelata: solo avanti e dX.
    4B: lotto 2, L multiplo di 128 -> righe 256..1536 a passi di 128; q 2560->8192, k/v 2560->1024,
        o 4096->2560, gate/up 2560->9216, down 9216->2560.
    9B: lotto 1 -> righe 128..768 a passi di 128; q 4096->8192, k/v 4096->1024, o 4096->4096,
        gate/up 4096->12288, down 12288->4096.   A GPU LIBERA (~20-25 minuti)."""
    forme = set()
    for righe, moduli in ((range(256, 1537, 128), ((2560, 8192), (2560, 1024), (4096, 2560), (2560, 9216), (9216, 2560))),
                          (range(128, 769, 128), ((4096, 8192), (4096, 1024), (4096, 4096), (4096, 12288), (12288, 4096)))):
        for T in righe:
            for din, dout in moduli:
                forme |= {(T, dout, din, 1, 1), (T, din, dout, 1, 0)}
    forme = sorted(f for f in forme if gg.supportata(*operandi(*f[:3], *f[3:])))
    print(f"  tarature di {len(forme)} forme del passo vero 4B + 9B (aggiunte a tarature.json)", flush=True)
    for M, N, K, akc, bkc, t_roc, s, t_s, scelta in gg.tara(forme):
        print(f"  {M:>6}x{N:<6}x{K:<6} A{akc} B{bkc}  rocBLAS {t_roc:5.1f}  migliore s{s} {t_s:5.1f}  -> "
              f"{'rocBLAS' if scelta == 0 else 'split ' + str(scelta)}", flush=True)


def tara():
    """Tarature a GPU libera: le forme del passo LoRA a 256, 512 e 1024 token (avanti, dX, dW)."""
    forme = set()
    for T in (256, 512, 1024):
        for din, dout in ((2560, 9216), (9216, 2560), (2560, 4096), (4096, 2560), (2560, 8192), (8192, 2560),
                          (2560, 1024), (2560, 248320)):
            forme |= {(T, dout, din, 1, 1), (T, din, dout, 1, 0), (dout, din, T, 0, 0)}
    forme = sorted(f for f in forme if gg.supportata(*operandi(*f[:3], *f[3:])) and f[0] * f[1] * f[2] < 2 ** 34)
    print(f"  tarature di {len(forme)} forme (rocBLAS contro split; scelta se >= 3% meglio)", flush=True)
    for M, N, K, akc, bkc, t_roc, s, t_s, scelta in gg.tara(forme):
        print(f"  {M:>6}x{N:<6}x{K:<6} A{akc} B{bkc}  rocBLAS {t_roc:5.1f}  migliore s{s} {t_s:5.1f}  -> "
              f"{'rocBLAS' if scelta == 0 else 'split ' + str(scelta)}", flush=True)


if __name__ == "__main__":
    correttezza()
    if "--tempi" in sys.argv:
        tempi()
    if "--tara" in sys.argv:
        tara()
    if "--tara-ruota" in sys.argv:
        tara_qwen4b_ruota()

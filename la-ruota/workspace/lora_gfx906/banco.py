"""Banco del LoRA fuso: y, dx, dA, dB contro la classe Lora di prova_lora_4b_reale.py (GPU, autocast fp16)
e contro CPU fp64 con gli stessi valori arrotondati.
    python banco.py            # correttezza
    python banco.py --tempi    # avanti+indietro per le forme di Qwen3.5-4B a 512 token (GPU libera)
"""
import sys
import time

import torch
import torch.nn as nn

sys.path.insert(0, r"C:\LaRuota_workspace\lora_gfx906")
import lora_gfx906 as lg  # noqa: E402


class Lora(nn.Module):
    """Copia della classe di prova_lora_4b_reale.py."""

    def __init__(self, base, rango=16, alpha=32):
        super().__init__()
        self.base = base
        self.a = nn.Linear(base.in_features, rango, bias=False, dtype=torch.float32)
        self.b = nn.Linear(rango, base.out_features, bias=False, dtype=torch.float32)
        nn.init.kaiming_uniform_(self.a.weight, a=5 ** 0.5)
        nn.init.normal_(self.b.weight, std=0.02)       # non zero: altrimenti dA e il ramo LoRA sono nulli
        self.scala = alpha / rango

    def forward(self, x):
        y = self.base(x)
        with torch.amp.autocast("cuda", enabled=False):
            d = self.b(self.a(x.float())) * self.scala
        return y + d.to(y.dtype)


def caso(N, Din, Dout, R, bias=False):
    torch.manual_seed(N + Din + R)
    base = nn.Linear(Din, Dout, bias=bias).half().cuda().requires_grad_(False)
    m = Lora(base, R).cuda()
    x = torch.randn(N, Din, device="cuda", dtype=torch.float16)
    dy = torch.randn(N, Dout, device="cuda", dtype=torch.float16)

    def gira(fusa):
        m.a.weight.grad = m.b.weight.grad = None
        xx = x.clone().requires_grad_()
        with torch.autocast("cuda", dtype=torch.float16):
            y = lg.lora(xx, base.weight, base.bias, m.a.weight, m.b.weight, m.scala) if fusa else m(xx)
        y.backward(dy)
        return y.detach(), xx.grad, m.a.weight.grad.clone(), m.b.weight.grad.clone()

    ori, fus = gira(False), gira(True)
    # fp64 con gli stessi valori
    W, A, B = (t.detach().double().cpu() for t in (base.weight, m.a.weight, m.b.weight))
    x64 = x.double().cpu().requires_grad_()
    A64, B64 = A.clone().requires_grad_(), B.clone().requires_grad_()
    y64 = x64 @ W.t() + (base.bias.double().cpu() if bias else 0) + (x64 @ A64.t()) @ B64.t() * m.scala
    y64.backward(dy.double().cpu())
    rif = (y64.detach(), x64.grad, A64.grad, B64.grad)
    riga, ok = f"  N{N:<5} Din{Din:<5} Dout{Dout:<5} R{R:<3} bias={bias!s:5s}", True
    for nome, i in (("y", 0), ("dx", 1), ("dA", 2), ("dB", 3)):
        r = rif[i]
        ef = ((fus[i].double().cpu() - r).abs().max() / r.abs().max()).item()
        eo = ((ori[i].double().cpu() - r).abs().max() / r.abs().max()).item()
        buono = ef <= max(1.5 * eo, 1e-5)
        ok &= buono
        riga += f"  {nome} {ef:.0e}/{eo:.0e}{'' if buono else '!'}"
    print(riga + ("  ok" if ok else "  >>> SBAGLIATO"), flush=True)
    return ok


def tempi():
    print("\n  avanti+indietro, ms (Lora torch -> fusa), 512 token, rango 16")
    for nome, Din, Dout in (("q_proj 2560->8192", 2560, 8192), ("k/v_proj 2560->1024", 2560, 1024),
                            ("o_proj 4096->2560", 4096, 2560)):
        base = nn.Linear(Din, Dout, bias=False).half().cuda().requires_grad_(False)
        m = Lora(base, 16).cuda()
        x = torch.randn(512, Din, device="cuda", dtype=torch.float16, requires_grad=True)
        dy = torch.randn(512, Dout, device="cuda", dtype=torch.float16)

        def passo(fusa):
            with torch.autocast("cuda", dtype=torch.float16):
                y = lg.lora(x, base.weight, None, m.a.weight, m.b.weight, m.scala) if fusa else m(x)
            y.backward(dy)

        risultati = []
        for fusa in (False, True):
            for _ in range(3):
                passo(fusa)
            torch.cuda.synchronize(); t = time.perf_counter()
            for _ in range(20):
                passo(fusa)
            torch.cuda.synchronize(); risultati.append((time.perf_counter() - t) / 20 * 1e3)
        print(f"  {nome:22s} {risultati[0]:7.3f} -> {risultati[1]:7.3f} ms", flush=True)


tutti = True
for N, Din, Dout, R in ((512, 2560, 8192, 16), (512, 2560, 1024, 16), (512, 4096, 2560, 16),
                        (37, 100, 77, 16), (1000, 64, 300, 8), (129, 300, 513, 32), (64, 256, 128, 64),
                        (3, 2560, 1024, 4), (1024, 2560, 1024, 1)):
    tutti &= caso(N, Din, Dout, R)
tutti &= caso(77, 333, 222, 16, bias=True)
print("ESITO", "ok" if tutti else "SBAGLIATO", "  (errore fusa/torch, relativo a CPU fp64)")
if "--tempi" in sys.argv:
    tempi()

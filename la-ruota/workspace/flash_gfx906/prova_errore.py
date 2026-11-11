"""Errore della fa contro math fp16 (stessa maschera), rispetto a fp32: massimo e RMS su più semi."""
import sys, torch
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_gfx906 as fa  # noqa: E402
from banco_fa import riferimento  # noqa: E402

casi = [(1, 2, 100, 250, 256, True, 0.5, True), (2, 3, 100, 100, 256, True, 0.0, False),
        (2, 2, 300, 300, 256, True, 0.2, False), (2, 2, 333, 77, 256, True, 0.0, False),
        (1, 2, 100, 250, 128, True, 0.5, True), (2, 3, 100, 100, 128, True, 0.0, False)]
for B, H, Sq, Sk, D, c, p, strani in casi:
    acc = {n: [0.0, 0.0, 0.0, 0.0, 0] for n in ("o", "dq", "dk", "dv")}   # max fa, max math, ss fa, ss math, n
    vinte = {n: 0 for n in acc}
    for seme in range(8):
        torch.manual_seed(100 + seme)
        if strani:
            q = torch.randn(B, Sq, H, D, device="cuda", dtype=torch.float16).transpose(1, 2)
            k = torch.randn(B, Sk, H, D, device="cuda", dtype=torch.float16).transpose(1, 2)
            v = torch.randn(B, Sk, H, D, device="cuda", dtype=torch.float16).transpose(1, 2)
        else:
            q, k, v = (torch.randn(B, H, n, D, device="cuda", dtype=torch.float16) for n in (Sq, Sk, Sk))
        do = torch.randn(B, H, Sq, D, device="cuda", dtype=torch.float16)
        sm = 987654321 + seme
        sc = D ** -0.5
        m = fa.maschera_dropout(B, H, Sq, Sk, p, sm) if p > 0 else None
        qq, kk, vv = (x.float().detach().requires_grad_() for x in (q, k, v))
        orif = riferimento(qq, kk, vv, c, sc, m, p); orif.backward(do.float())
        q16, k16, v16 = (x.detach().clone().requires_grad_() for x in (q, k, v))
        o16 = riferimento(q16, k16, v16, c, sc, m, p); o16.backward(do)
        qf, kf, vf = (x.detach().clone().requires_grad_() for x in (q, k, v))
        of = fa.attenzione(qf, kf, vf, causale=c, dropout=p, seme=sm); of.backward(do)
        for nome, a, b16, r in (("o", of, o16, orif), ("dq", qf.grad, q16.grad, qq.grad),
                                ("dk", kf.grad, k16.grad, kk.grad), ("dv", vf.grad, v16.grad, vv.grad)):
            ef, em = (a.float() - r), (b16.float() - r)
            x = acc[nome]
            x[0] = max(x[0], ef.abs().max().item()); x[1] = max(x[1], em.abs().max().item())
            x[2] += ef.pow(2).sum().item(); x[3] += em.pow(2).sum().item(); x[4] += r.numel()
            vinte[nome] += ef.abs().max().item() <= em.abs().max().item()
    riga = f"  B{B} H{H} Sq{Sq} Sk{Sk} D{D} c={int(c)} p={p}:"
    for n, x in acc.items():
        riga += f" {n} max {x[0]:.1e}/{x[1]:.1e} rms {(x[2] / x[4]) ** .5:.1e}/{(x[3] / x[4]) ** .5:.1e} ({vinte[n]}/8)"
    print(riga, flush=True)

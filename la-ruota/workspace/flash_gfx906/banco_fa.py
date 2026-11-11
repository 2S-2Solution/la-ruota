"""Banco di fa_gfx906: registri | correttezza | prestazioni."""
import math, re, statistics, subprocess, sys, time
import torch, torch.nn.functional as F
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_gfx906 as fa  # noqa: E402

OBJDUMP = r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-objdump.exe"
READOBJ = r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-readobj.exe"


def registri(dimensioni=fa.DIMENSIONI):
    for nome in fa.KERNEL:
        for hd in dimensioni:
            p = rf"C:\LaRuota_workspace\flash_gfx906\tmp_{nome}_{hd}.co"
            open(p, "wb").write(fa.compila(fa.kernel(nome, hd)[0], hd).raw)
            s = subprocess.run([OBJDUMP, "-d", "--mcpu=gfx906", p], capture_output=True, text=True).stdout
            v = max((int(x) for x in re.findall(r"\bv\[?(\d+)", s)), default=0) + 1
            sp = len(re.findall(r"scratch_|buffer_store_dword|buffer_load_dword", s))
            note = subprocess.run([READOBJ, "--notes", p], capture_output=True, text=True).stdout
            lds = re.findall(r"\.group_segment_fixed_size:\s*(\d+)", note)
            print(f"  {nome} D{hd}: VGPR {v}, sversamenti {sp}, LDS {lds[0] if lds else '?'} byte", flush=True)


def riferimento(q, k, v, causale, scala, maschera, p):
    """fp32, foglie fp32; maschera di dropout esplicita (True = tenuto). GQA: K/V ripetute."""
    if k.shape[1] != q.shape[1]:
        g = q.shape[1] // k.shape[1]
        k, v = k.repeat_interleave(g, dim=1), v.repeat_interleave(g, dim=1)
    s = (q @ k.transpose(-1, -2)) * scala
    if causale:
        Sq, Sk = s.shape[-2:]
        s = s.masked_fill(~torch.ones(Sq, Sk, dtype=torch.bool, device=s.device).tril(), float("-inf"))
    a = torch.softmax(s, -1)
    if maschera is not None:
        a = a * maschera / (1 - p)
    return a @ v


def correttezza(dimensioni=fa.DIMENSIONI):
    torch.manual_seed(0)
    # (B, H, Sq, Sk, D, causale, dropout, stride strani[, teste di K/V])
    casi = [(1, 2, 64, 64, 64, False, 0.0, False), (2, 3, 100, 100, 128, True, 0.0, False),
            (1, 2, 64, 200, 64, False, 0.0, False), (1, 2, 200, 64, 128, False, 0.0, False),
            (2, 2, 77, 333, 64, True, 0.0, False), (2, 2, 333, 77, 128, True, 0.0, False),
            (2, 4, 256, 256, 64, True, 0.0, True), (1, 3, 130, 190, 128, False, 0.0, True),
            (1, 2, 256, 256, 64, False, 0.1, False), (2, 2, 300, 300, 128, True, 0.2, False),
            (1, 2, 100, 250, 64, True, 0.5, True), (1, 1, 1, 1, 64, False, 0.0, False)]
    # D=256 (Qwen3.5-4B): gli stessi dodici casi
    casi = [x for x in casi if x[4] in dimensioni] + ([x[:4] + (256,) + x[5:] for x in casi] if 256 in dimensioni else [])
    # GQA (Qwen3.5-4B: 16 teste di query, 4 di K/V), anche MQA
    casi += [(1, 8, 100, 130, d, True, 0.0, False, 2) for d in dimensioni]
    casi += [(2, 4, 77, 200, d, False, 0.2, True, 1) for d in dimensioni]
    casi += [(1, 16, 256, 256, d, True, 0.0, True, 4) for d in dimensioni]
    tutti = True
    for B, H, Sq, Sk, D, c, p, strani, *hk in casi:
        Hk = hk[0] if hk else H
        if strani:   # layout [B, S, H, D] come esce da una proiezione: stride non contigui
            q = torch.randn(B, Sq, H, D, device="cuda", dtype=torch.float16).transpose(1, 2)
            k = torch.randn(B, Sk, Hk, D, device="cuda", dtype=torch.float16).transpose(1, 2)
            v = torch.randn(B, Sk, Hk, D, device="cuda", dtype=torch.float16).transpose(1, 2)
        else:
            q, k, v = (torch.randn(B, h, n, D, device="cuda", dtype=torch.float16) for h, n in ((H, Sq), (Hk, Sk), (Hk, Sk)))
        do = torch.randn(B, H, Sq, D, device="cuda", dtype=torch.float16)
        seme = 12345678901 + Sq
        sc = D ** -0.5
        m = fa.maschera_dropout(B, H, Sq, Sk, p, seme) if p > 0 else None
        # riferimento fp32
        qq, kk, vv = (x.float().detach().requires_grad_() for x in (q, k, v))
        orif = riferimento(qq, kk, vv, c, sc, m, p); orif.backward(do.float())
        # math fp16 (stessa maschera), per la scala dell'errore
        q16, k16, v16 = (x.detach().clone().requires_grad_() for x in (q, k, v))
        o16 = riferimento(q16, k16, v16, c, sc, m, p); o16.backward(do)
        # fa
        qf, kf, vf = (x.detach().clone().requires_grad_() for x in (q, k, v))
        of = fa.attenzione(qf, kf, vf, causale=c, dropout=p, seme=seme); of.backward(do)
        riga = (f"  B{B} H{H:<2}{'/' + str(Hk) if Hk != H else '  '} Sq{Sq:<4} Sk{Sk:<4} D{D:<3} c={int(c)} p={p:.1f} "
                f"{'stride' if strani else '      '}")
        ok_caso = True
        for nome, a, b16, r in (("o", of, o16, orif), ("dq", qf.grad, q16.grad, qq.grad),
                                ("dk", kf.grad, k16.grad, kk.grad), ("dv", vf.grad, v16.grad, vv.grad)):
            ef = (a.float() - r).abs().max().item()
            em = (b16.float() - r).abs().max().item()
            ok = math.isfinite(ef) and ef <= max(2.5 * em, 1e-3 * r.abs().max().item(), 1e-5)
            ok_caso &= ok
            riga += f" {nome} {ef:.1e}/{em:.1e}{'' if ok else '!'}"
        tutti &= ok_caso
        print(riga + f"  {'ok' if ok_caso else '>>> SBAGLIATO'}", flush=True)
    print("  (errore assoluto fa / math fp16 con la stessa maschera, contro fp32)")
    print("ESITO", "ok" if tutti else "SBAGLIATO")


def misura(fn, giri=3):
    torch.cuda.synchronize(); t = time.perf_counter()
    for _ in range(giri):
        fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t) * 1000 / giri


def prestazioni(dimensioni=fa.DIMENSIONI):
    print(f"  {'forma':30s} {'math av':>8} {'fa av':>7} {'math a+i':>9} {'fa a+i':>8}  {'av':>6} {'a+i':>6}", flush=True)
    forme = [(1, 16, 1024, 64, False), (1, 16, 4096, 64, True), (1, 16, 1024, 128, False),
             (1, 16, 2048, 128, True), (1, 16, 4096, 128, True),
             # D=256: attenzione piena di Qwen3.5-4B (16 teste di query)
             (1, 16, 256, 256, True), (1, 16, 1024, 256, False), (1, 16, 1024, 256, True),
             (1, 16, 2048, 256, True), (1, 16, 4096, 256, False), (1, 16, 4096, 256, True)]
    for B, H, S, D, c in [x for x in forme if x[3] in dimensioni]:
        q, k, v, do = (torch.randn(B, H, S, D, device="cuda", dtype=torch.float16) for _ in range(4))
        def gm():
            a, b, d = (x.detach().requires_grad_() for x in (q, k, v))
            F.scaled_dot_product_attention(a, b, d, is_causal=c).backward(do)
        def gf():
            a, b, d = (x.detach().requires_grad_() for x in (q, k, v))
            fa.attenzione(a, b, d, causale=c).backward(do)
        am = lambda: F.scaled_dot_product_attention(q, k, v, is_causal=c)
        af = lambda: fa.avanti(q, k, v, causale=c)
        for f in (am, af, gm, gf):
            f()
        t = {n: [] for n in ("am", "af", "gm", "gf")}
        for _ in range(5):
            for n, f in (("am", am), ("af", af), ("gm", gm), ("gf", gf)):
                t[n].append(misura(f))
        m = {n: statistics.median(x) for n, x in t.items()}
        nome = f"B{B} H{H} S{S} D{D}{' causale' if c else ''}"
        print(f"  {nome:30s} {m['am']:8.2f} {m['af']:7.2f} {m['gm']:9.2f} {m['gf']:8.2f}  "
              f"{m['am'] / m['af']:5.2f}x {m['gm'] / m['gf']:5.2f}x", flush=True)


def prestazioni_gqa(dimensioni=(256,)):
    """Qwen3.5-4B: 16 teste di query, 4 di K/V. math e fa con K/V ripetute contro fa GQA nativa."""
    print(f"  {'forma':34s} {'math av':>8} {'fa rip':>7} {'fa gqa':>7} {'math a+i':>9} {'fa rip':>7} {'fa gqa':>7}"
          f"  {'av':>6} {'a+i':>6}", flush=True)
    for B, H, Hk, S, D, c in [(1, 16, 4, S, d, True) for d in dimensioni for S in (1024, 2048, 4096)]:
        q, do = (torch.randn(B, H, S, D, device="cuda", dtype=torch.float16) for _ in range(2))
        k, v = (torch.randn(B, Hk, S, D, device="cuda", dtype=torch.float16) for _ in range(2))
        rip = lambda x: x.repeat_interleave(H // Hk, dim=1)

        def gm():
            a, b, d = (x.detach().requires_grad_() for x in (q, k, v))
            F.scaled_dot_product_attention(a, rip(b), rip(d), is_causal=c).backward(do)

        def gr():
            a, b, d = (x.detach().requires_grad_() for x in (q, k, v))
            fa.attenzione(a, rip(b), rip(d), causale=c).backward(do)

        def gg():
            a, b, d = (x.detach().requires_grad_() for x in (q, k, v))
            fa.attenzione(a, b, d, causale=c).backward(do)
        f = {"am": lambda: F.scaled_dot_product_attention(q, rip(k), rip(v), is_causal=c),
             "ar": lambda: fa.avanti(q, rip(k), rip(v), causale=c), "ag": lambda: fa.avanti(q, k, v, causale=c),
             "gm": gm, "gr": gr, "gg": gg}
        for x in f.values():
            x()
        t = {n: [] for n in f}
        for _ in range(5):
            for n, x in f.items():
                t[n].append(misura(x))
        m = {n: statistics.median(x) for n, x in t.items()}
        nome = f"B{B} H{H}/{Hk} S{S} D{D}{' causale' if c else ''}"
        print(f"  {nome:34s} {m['am']:8.2f} {m['ar']:7.2f} {m['ag']:7.2f} {m['gm']:9.2f} {m['gr']:7.2f} {m['gg']:7.2f}"
              f"  {m['am'] / m['ag']:5.2f}x {m['gm'] / m['gg']:5.2f}x", flush=True)


if __name__ == "__main__":
    dims = tuple(int(x) for x in sys.argv[2:]) or fa.DIMENSIONI
    {"registri": registri, "correttezza": correttezza, "prestazioni": prestazioni,
     "prestazioni_gqa": prestazioni_gqa}[sys.argv[1]](dims)

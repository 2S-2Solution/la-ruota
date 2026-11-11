"""Banco dell'indietro fa2.   python banco_indietro.py [registri|correttezza|prestazioni]"""
import math, re, statistics, subprocess, sys, time
import torch, torch.nn.functional as F
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa2_avanti, fa2_indietro  # noqa: E402

OBJDUMP = r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-objdump.exe"


def registri():
    for nome, src in (("fa2_dkdv", fa2_indietro.SORGENTE_DKDV), ("fa2_dq", fa2_indietro.SORGENTE_DQ)):
        for hd in (64, 128):
            c = fa2_avanti.compila(hd, sorgente=src)
            p = rf"C:\LaRuota_workspace\flash_gfx906\tmp_{nome}_{hd}.co"
            open(p, "wb").write(c.raw)
            s = subprocess.run([OBJDUMP, "-d", "--mcpu=gfx906", p], capture_output=True, text=True).stdout
            v = max((int(x) for x in re.findall(r"\bv\[?(\d+)", s)), default=0) + 1
            sp = len(re.findall(r"scratch_|buffer_store_dword|buffer_load_dword", s))
            print(f"  {nome} D{hd}: VGPR {v}, sversamenti {sp}", flush=True)


def dati(B, H, S, D, seme=0):
    g = torch.Generator(device="cuda").manual_seed(seme)
    return [torch.randn(B, H, S, D, device="cuda", dtype=torch.float16, generator=g) for _ in range(4)]


def gradienti(fn, q, k, v, do):
    qq, kk, vv = (x.detach().clone().requires_grad_() for x in (q, k, v))
    o = fn(qq, kk, vv)
    o.backward(do)
    return o.detach(), qq.grad, kk.grad, vv.grad


def correttezza():
    casi = [(1, 2, 64, 64, False), (1, 2, 64, 64, True), (2, 3, 100, 64, True), (1, 4, 256, 128, False),
            (1, 4, 256, 128, True), (2, 2, 77, 128, True), (1, 8, 1024, 64, True), (1, 4, 1024, 128, True),
            (1, 2, 1, 64, False), (1, 2, 33, 128, False), (1, 2, 4097, 64, True)]
    tutti = True
    for B, H, S, D, c in casi:
        q, k, v, do = dati(B, H, S, D)
        rif = gradienti(lambda a, b, d: F.scaled_dot_product_attention(a, b, d, is_causal=c),
                        q.float(), k.float(), v.float(), do.float())        # foglie fp32: gradienti fp32
        m16 = gradienti(lambda a, b, d: F.scaled_dot_product_attention(a, b, d, is_causal=c), q, k, v, do)
        fa = gradienti(lambda a, b, d: fa2_indietro.flash_attenzione(a, b, d, is_causal=c), q, k, v, do)
        riga = f"  B{B} H{H} S{S:<5} D{D:<3} causale={str(c):5s}"
        ok_caso = True
        for nome, i in (("dq", 1), ("dk", 2), ("dv", 3)):
            ef = (fa[i].float() - rif[i]).abs().max().item()
            em = (m16[i].float() - rif[i]).abs().max().item()
            soglia = max(2 * em, 1e-3 * rif[i].abs().max().item(), 1e-5)
            ok = ef <= soglia and math.isfinite(ef)
            ok_caso &= ok
            riga += f"  {nome} {ef:.1e}/{em:.1e} (max {rif[i].abs().max().item():.1e}){'' if ok else '!'}"
        _, lse2 = fa2_avanti.flash_avanti(q, k, v, is_causal=c, lse=True)
        s = (q.float() @ k.float().transpose(-1, -2)) * D ** -0.5
        if c:
            s = s.masked_fill(torch.triu(torch.ones(S, S, dtype=torch.bool, device="cuda"), 1), float("-inf"))
        el = (lse2 * math.log(2) - torch.logsumexp(s, -1)).abs().max().item()
        ok_caso &= el < 1e-3
        tutti &= ok_caso
        print(riga + f"  lse {el:.1e}  {'ok' if ok_caso else '>>> SBAGLIATO'}", flush=True)
    print("  (per ogni gradiente: errore assoluto fa2 / errore math fp16, contro fp32)")
    print("ESITO", "ok" if tutti else "SBAGLIATO")


def misura(fn, giri=3):
    torch.cuda.synchronize(); t = time.perf_counter()
    for _ in range(giri):
        fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t) * 1000 / giri


def prestazioni():
    print(f"  {'forma':28s} {'math av+ind':>12} {'fa2 av+ind':>11} {'rapporto':>9}  {'math MB':>8} {'fa2 MB':>7}", flush=True)
    for B, H, S, D, c in [(1, 16, 1024, 64, False), (1, 16, 2048, 64, True), (1, 16, 1024, 128, False),
                          (1, 16, 2048, 128, True), (1, 16, 4096, 128, True)]:
        q, k, v, do = dati(B, H, S, D)
        fm = lambda: gradienti(lambda a, b, d: F.scaled_dot_product_attention(a, b, d, is_causal=c), q, k, v, do)
        ff = lambda: gradienti(lambda a, b, d: fa2_indietro.flash_attenzione(a, b, d, is_causal=c), q, k, v, do)
        mem = {}
        for n, f in (("m", fm), ("f", ff)):
            f(); torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats(); b0 = torch.cuda.memory_allocated()
            f(); torch.cuda.synchronize(); mem[n] = (torch.cuda.max_memory_allocated() - b0) / 2**20
        tm, tf = [], []
        for _ in range(5):
            tm.append(misura(fm)); tf.append(misura(ff))
        m, f = statistics.median(tm), statistics.median(tf)
        nome = f"B{B} H{H} S{S} D{D}{' causale' if c else ''}"
        print(f"  {nome:28s} {m:12.2f} {f:11.2f} {m / f:8.2f}x  {mem['m']:8.0f} {mem['f']:7.0f}", flush=True)


if __name__ == "__main__":
    {"registri": registri, "correttezza": correttezza, "prestazioni": prestazioni}[sys.argv[1]]()

"""Banco della perdita fusa: perdita e dh contro cross_entropy in CPU fp64 (e contro il percorso torch su
GPU), vocabolari irregolari, etichette ignorate, blocchi piccoli, num_items_in_batch.
    python banco.py            # correttezza
    python banco.py --tempi    # tempo e memoria di picco a forma Qwen3.5 (512 token, V 248.320), GPU libera
"""
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\LaRuota_workspace\perdita_gfx906")
import perdita_gfx906 as pv  # noqa: E402


def caso(N, D, V, dt, mega=256, num_items=None, frazione_ignorate=0.1):
    torch.manual_seed(N + V)
    h = torch.randn(N, D) * 1.0
    W = torch.randn(V, D) * (0.5 / D ** 0.5) * 4
    et = torch.randint(0, V, (N,))
    et[torch.rand(N) < frazione_ignorate] = -100
    # riferimento fp64 (stessi valori arrotondati al tipo)
    h64 = h.to(dt).double().requires_grad_()
    W64 = W.to(dt).double()
    l64 = F.cross_entropy(h64 @ W64.t(), et, ignore_index=-100, reduction="sum" if num_items else "mean")
    if num_items:
        l64 = l64 / num_items
    l64.backward()
    # torch su GPU, come transformers (logit nel tipo, poi .float())
    hg = h.to(dt).cuda().requires_grad_()
    Wg = W.to(dt).cuda()
    lt = F.cross_entropy((hg @ Wg.t()).float(), et.cuda(), ignore_index=-100, reduction="sum" if num_items else "mean")
    if num_items:
        lt = lt / num_items
    lt.backward()
    # fusa
    pv.MEGA_BLOCCO = mega
    hf = h.to(dt).cuda().requires_grad_()
    lf = pv.perdita_vocabolario(hf, Wg, et.cuda(), num_items)
    (lf * 3.0).backward()                     # grad_out diverso da 1
    pv.MEGA_BLOCCO = 256
    e_l = abs(lf.item() - l64.item()) / abs(l64.item())
    e_lt = abs(lt.item() - l64.item()) / abs(l64.item())
    r = h64.grad * 3.0
    e_d = ((hf.grad.double().cpu() - r).abs().max() / r.abs().max()).item()
    e_dt = ((hg.grad.double().cpu() * 3.0 - r).abs().max() / r.abs().max()).item()
    # fp32: la GEMM di rocBLAS su K = V lunghi sbaglia ~sqrt(K)*eps (2e-5 a V 50.021 anche col gradiente
    # esatto arrotondato; torch scala prima per 1/n e cade a 1e-5 per caso): il kernel da solo fa 4e-7
    tol = 5e-5 if dt == torch.float32 else 3e-3
    ok = e_l <= max(2 * e_lt, tol) and e_d <= max(2 * e_dt, tol)
    print(f"  {str(dt)[-7:]} N{N:<5} D{D:<5} V{V:<7} blocco {mega:>3} MB num_items={num_items!s:5s} "
          f"perdita {e_l:.0e}/{e_lt:.0e}  dh {e_d:.0e}/{e_dt:.0e}  {'ok' if ok else '>>> SBAGLIATO'}", flush=True)
    return ok


def tempi():
    N, D, V = 512, 2560, 248320
    torch.manual_seed(0)
    h = torch.randn(N, D, device="cuda", dtype=torch.float16, requires_grad=True)
    W = (torch.randn(V, D, device="cuda", dtype=torch.float16) * 0.02)
    et = torch.randint(0, V, (N,), device="cuda")

    def originale():
        l = F.cross_entropy((h @ W.t()).float(), et, ignore_index=-100)
        l.backward()

    def fusa():
        pv.perdita_vocabolario(h, W, et).backward()

    for nome, fn in (("transformers (logit fp16 -> fp32)", originale), ("fusa", fusa)):
        fn(); torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats(); base = torch.cuda.memory_allocated()
        t = time.perf_counter()
        for _ in range(5):
            fn()
        torch.cuda.synchronize()
        ms = (time.perf_counter() - t) / 5 * 1e3
        picco = (torch.cuda.max_memory_allocated() - base) / 2**20
        print(f"  {nome:36s} {ms:7.1f} ms   memoria in piu' al picco {picco:7.0f} MB", flush=True)
        h.grad = None


tutti = True
for dt in (torch.float32, torch.float16):
    tutti &= caso(300, 256, 50021, dt)
    tutti &= caso(300, 256, 50021, dt, mega=1)               # ~10 righe per blocco
    tutti &= caso(77, 128, 1000, dt, num_items=50)
    tutti &= caso(64, 256, 248320, dt, frazione_ignorate=0.3)
print("ESITO", "ok" if tutti else "SBAGLIATO", "  (errore fusa/torch su GPU, relativo a CPU fp64)")
if "--tempi" in sys.argv:
    tempi()

"""Banco di norme_gfx906: correttezza (avanti, dx, dw, dgate) e tempi contro gli originali."""
import sys, time, statistics, torch, torch.nn.functional as F
sys.path.insert(0, r"C:\LaRuota_workspace\norme_gfx906")
sys.path.insert(0, r"%USERPROFILE%\Documents\2SAI\Memoria\working\prova_tf_nuovo")
import norme_gfx906 as nm
SOGLIA_VERA = nm.SOGLIA
nm.SOGLIA = 0          # correttezza: il kernel anche sui tensori piccoli
from transformers.models.qwen3_5 import modeling_qwen3_5 as mq
ORIG_RMS, ORIG_Q, ORIG_QG = F.rms_norm, mq.Qwen3_5RMSNorm.forward, mq.Qwen3_5RMSNormGated.forward

def caso(modo, R, D, dt, peso_grad=True):
    torch.manual_seed(R + D)
    x = torch.randn(R, D, device="cuda", dtype=dt) * 2
    g = torch.randn(R, D, device="cuda", dtype=dt) if modo == 2 else None
    w = (torch.randn(D, device="cuda") * 0.5 + (1 if modo != 1 else 0)).to(dt if modo != 1 else torch.float32)
    dy = torch.randn(R, D, device="cuda", dtype=dt)
    def gira(fusa, x, w, g, dev, dtype):
        xx = x.detach().to(dev, dtype).requires_grad_(); ww = torch.nn.Parameter(w.detach().to(dev, dtype if modo != 1 else torch.float64 if dtype == torch.float64 else torch.float32), requires_grad=peso_grad)
        gg = g.detach().to(dev, dtype).requires_grad_() if g is not None else None
        if modo == 0:
            y = (nm.rms_norm if fusa else ORIG_RMS)(xx, (D,), ww, 1e-6)
        else:
            mod = (mq.Qwen3_5RMSNorm(D, eps=1e-6) if modo == 1 else mq.Qwen3_5RMSNormGated(D, eps=1e-6)).to(dev)
            mod.weight = ww
            if modo == 1: y = (nm.qwen_rmsnorm_forward if fusa else ORIG_Q)(mod, xx)
            else: y = (nm.qwen_rmsnorm_gated_forward if fusa else ORIG_QG)(mod, xx, gg)
        y.backward(dy.to(dev, y.dtype))
        return y.detach(), xx.grad, ww.grad, (gg.grad if gg is not None else None)
    rif = gira(False, x, w, g, "cpu", torch.float64)
    ori = gira(False, x, w, g, "cuda", dt)
    fus = gira(True, x, w, g, "cuda", dt)
    riga = f"  modo {modo} {str(dt)[-7:]} R{R:<5} D{D:<5}"
    ok = True
    for nome, i in (("y", 0), ("dx", 1), ("dw", 2), ("dg", 3)):
        if rif[i] is None: continue
        r = rif[i].double(); ef = ((fus[i].double().cpu() - r).abs().max() / r.abs().max()).item(); eo = ((ori[i].double().cpu() - r).abs().max() / r.abs().max()).item()
        buono = ef <= max(2 * eo, 2e-6 if dt == torch.float32 else 2e-3)
        ok &= buono
        riga += f"  {nome} {ef:.0e}/{eo:.0e}{'' if buono else '!'}"
    print(riga + ("  ok" if ok else "  >>> SBAGLIATO"), flush=True)
    return ok

def tempi():
    def ms(fn, n=50):
        for _ in range(3): fn()
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True); e0.record()
        for _ in range(n): fn()
        e1.record(); torch.cuda.synchronize(); return e0.elapsed_time(e1) / n
    print("\n  tempi avanti+indietro (ms): originale -> fusa")
    for nome, modo, R, D, dt in (("Qwen RMSNorm strato 512 tok", 1, 512, 2560, torch.float16), ("Qwen q_norm 512 tok x16 teste", 1, 512 * 16, 256, torch.float16),
                                  ("Qwen norma con gate 512 x 32 teste", 2, 512 * 32, 128, torch.float16), ("F.rms_norm fp32 1256 x 96 x 192", 0, 1256 * 96, 192, torch.float32)):
        x = torch.randn(R, D, device="cuda", dtype=dt, requires_grad=True); g = torch.randn(R, D, device="cuda", dtype=dt, requires_grad=True)
        w = torch.ones(D, device="cuda", dtype=torch.float32 if modo == 1 else dt); dy = torch.randn(R, D, device="cuda", dtype=dt)
        mod = mq.Qwen3_5RMSNorm(D).cuda() if modo == 1 else mq.Qwen3_5RMSNormGated(D).cuda().to(dt)
        def fo():
            if modo == 0: y = ORIG_RMS(x, (D,), w, 1e-6)
            elif modo == 1: y = ORIG_Q(mod, x)
            else: y = ORIG_QG(mod, x, g)
            y.backward(dy)
        def ff():
            if modo == 0: y = nm.rms_norm(x, (D,), w, 1e-6)
            elif modo == 1: y = nm.qwen_rmsnorm_forward(mod, x)
            else: y = nm.qwen_rmsnorm_gated_forward(mod, x, g)
            y.backward(dy)
        with torch.no_grad():
            av_o = ms(lambda: ORIG_RMS(x, (D,), w, 1e-6) if modo == 0 else (ORIG_Q(mod, x) if modo == 1 else ORIG_QG(mod, x, g)))
            av_f = ms(lambda: nm.rms_norm(x, (D,), w, 1e-6) if modo == 0 else (nm.qwen_rmsnorm_forward(mod, x) if modo == 1 else nm.qwen_rmsnorm_gated_forward(mod, x, g)))
        print(f"  {nome:42s} avanti {av_o:7.3f} -> {av_f:7.3f} ({av_o / av_f:4.1f}x)   avanti+indietro {ms(fo):7.3f} -> {ms(ff):7.3f}", flush=True)

ORIG_LN = F.layer_norm

def caso_ln(R, D, dt, affine=True):
    torch.manual_seed(R * 7 + D)
    x = torch.randn(R, D, device="cuda", dtype=dt) * 2 + 3          # media lontana da zero: prova le due passate
    w = torch.randn(D, device="cuda", dtype=dt) * 0.5 + 1
    b = torch.randn(D, device="cuda", dtype=dt) * 0.1
    dy = torch.randn(R, D, device="cuda", dtype=dt)
    def gira(fusa, dev, dtype):
        xx = x.detach().to(dev, dtype).requires_grad_()
        ww = w.detach().to(dev, dtype).requires_grad_() if affine else None
        bb = b.detach().to(dev, dtype).requires_grad_() if affine else None
        y = (nm.layer_norm if fusa else ORIG_LN)(xx, (D,), ww, bb, 1e-5)
        y.backward(dy.to(dev, dtype))
        return y.detach(), xx.grad, ww.grad if affine else None, bb.grad if affine else None
    rif, ori, fus = gira(False, "cpu", torch.float64), gira(False, "cuda", dt), gira(True, "cuda", dt)
    riga, ok = f"  layernorm {str(dt)[-7:]} R{R:<6} D{D:<5}", True
    for nome, i in (("y", 0), ("dx", 1), ("dw", 2), ("db", 3)):
        if rif[i] is None: continue
        r = rif[i].double(); ef = ((fus[i].double().cpu() - r).abs().max() / r.abs().max()).item(); eo = ((ori[i].double().cpu() - r).abs().max() / r.abs().max()).item()
        buono = ef <= max(2 * eo, 2e-6 if dt == torch.float32 else 2e-3)
        ok &= buono
        riga += f"  {nome} {ef:.0e}/{eo:.0e}{'' if buono else '!'}"
    print(riga + ("  ok" if ok else "  >>> SBAGLIATO"), flush=True)
    return ok

def tempi_ln():
    def ms(fn, n=50):
        for _ in range(3): fn()
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True); e0.record()
        for _ in range(n): fn()
        e1.record(); torch.cuda.synchronize(); return e0.elapsed_time(e1) / n
    print("\n  LayerNorm, tempi (ms): originale -> fusa")
    for nome, R, D in (("rete di prova 256 x 100 x 32", 25600, 32), ("rete di prova 64 x 60 x 64", 3840, 64), ("rete di prova 64 x 63 x 32", 4032, 32),
                       ("fp32 1256 x 96 x 192", 1256 * 96, 192)):
        x = torch.randn(R, D, device="cuda", requires_grad=True); w = torch.ones(D, device="cuda", requires_grad=True)
        b = torch.zeros(D, device="cuda", requires_grad=True); dy = torch.randn(R, D, device="cuda")
        fo = lambda: ORIG_LN(x, (D,), w, b, 1e-5).backward(dy)
        ff = lambda: nm.layer_norm(x, (D,), w, b, 1e-5).backward(dy)
        with torch.no_grad():
            av_o, av_f = ms(lambda: ORIG_LN(x, (D,), w, b, 1e-5)), ms(lambda: nm.layer_norm(x, (D,), w, b, 1e-5))
        print(f"  {nome:42s} avanti {av_o:7.3f} -> {av_f:7.3f}   avanti+indietro {ms(fo):7.3f} -> {ms(ff):7.3f}", flush=True)

tutti = True
for dt in (torch.float32, torch.float16):
    for R, D in ((25600, 32), (3840, 64), (777, 100), (1000, 7), (64, 2048), (300, 1500), (5, 3)):
        tutti &= caso_ln(R, D, dt)
tutti &= caso_ln(1234, 48, torch.float32, affine=False)
for modo in (0, 1, 2):
    for dt in (torch.float32, torch.float16):
        for R, D in ((64, 2560), (300, 256), (1000, 128), (777, 192), (33, 100)):
            tutti &= caso(modo, R, D, dt)
tutti &= caso(0, 64, 192, torch.float32, peso_grad=False)
print("ESITO", "ok" if tutti else "SBAGLIATO", "  (per ogni grandezza: errore fusa/originale contro CPU fp64)")
if "--tempi" in sys.argv:
    nm.SOGLIA = SOGLIA_VERA   # tempi con la regola vera (sotto soglia = torch)
    tempi(); tempi_ln()

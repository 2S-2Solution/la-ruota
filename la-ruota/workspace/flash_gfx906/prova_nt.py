"""D=256: ogni kernel a 256 e a 512 thread per workgroup, misure intercalate (mediane), B1 H16."""
import ctypes, statistics, sys, torch
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_gfx906 as fa  # noqa: E402

def tempo(fn, giri=3):
    a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    a.record()
    for _ in range(giri):
        fn()
    b.record(); b.synchronize()
    return a.elapsed_time(b) / giri

D, H = 256, 16
vp = ctypes.c_void_p
for S, c in ((1024, False), (1024, True), (4096, False), (4096, True)):
    q, k, v, do = (torch.randn(1, H, S, D, device="cuda", dtype=torch.float16) for _ in range(4))
    o, lse = fa.avanti(q, k, v, causale=c)
    sc = D ** -0.5
    dvec = (do.float() * o.float()).sum(-1).contiguous()
    dq, dk, dv = torch.empty_like(q), torch.empty_like(k), torch.empty_like(v)
    p = lambda t: vp(t.data_ptr())
    coda = ([ctypes.c_int(H), ctypes.c_int(1), ctypes.c_int(S), ctypes.c_int(S), ctypes.c_float(sc * fa.LOG2E),
             ctypes.c_float(sc), ctypes.c_int(1 if c else 0)] + fa._dropout(0.0, 0))
    passi = fa._passi(q) + fa._passi(k) + fa._passi(v) + fa._passi(do)
    lav = {"fa_avanti": (lambda: fa.avanti(q, k, v, causale=c), 4),
           "fa_dkdv": (lambda: fa._lancia("fa_dkdv", D, S, H, [p(q), p(k), p(v), p(do), p(lse), p(dvec), p(dk), p(dv)] + passi + coda), 8),
           "fa_dq": (lambda: fa._lancia("fa_dq", D, S, H, [p(q), p(k), p(v), p(do), p(lse), p(dvec), p(dq)] + passi + coda), 6)}
    t = {(n, nt): [] for n in lav for nt in (256, 512)}
    ris = {}
    for giro in range(6):
        for nt in (256, 512):
            fa.imposta_256(fa_avanti=nt, fa_dkdv=nt, fa_dq=nt)
            for n, (f, _) in lav.items():
                f()
                if giro:
                    t[(n, nt)].append(tempo(f))
                else:
                    torch.cuda.synchronize()
            torch.cuda.synchronize()
            ris[nt] = (fa.avanti(q, k, v, causale=c)[0].clone(), dq.clone(), dk.clone(), dv.clone())
    coppie = S * S * H * (0.5 if c else 1.0)
    riga = f"  S{S}{' c' if c else '  '}"
    for n, (_, fl) in lav.items():
        a, b = (statistics.median(t[(n, nt)]) for nt in (256, 512))
        riga += f" | {n[3:]:6s} {a:6.2f} -> {b:6.2f} ms ({fl * coppie * D / b / 1e9:4.1f} TF, {a / b:4.2f}x)"
    diff = max((x.float() - y.float()).abs().max().item() for x, y in zip(ris[256], ris[512]))
    print(riga + f" | diff {diff:.1e}", flush=True)

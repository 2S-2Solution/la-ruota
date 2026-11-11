"""Tempo e TFLOPS dei tre kernel separati (D=256 o altro), B1 H16."""
import statistics, sys, torch
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_gfx906 as fa  # noqa: E402

def tempo(fn, giri=5, rip=5):
    v = []
    for _ in range(rip):
        a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        a.record()
        for _ in range(giri):
            fn()
        b.record(); b.synchronize()
        v.append(a.elapsed_time(b) / giri)
    return statistics.median(v)


def principale():
    D = int(sys.argv[1]) if len(sys.argv) > 1 else 256
    for S, c in ((1024, False), (4096, False), (4096, True)):
        H = 16
        q, k, v, do = (torch.randn(1, H, S, D, device="cuda", dtype=torch.float16) for _ in range(4))
        o, lse = fa.avanti(q, k, v, causale=c)
        fa.indietro(do, q, k, v, o, lse, causale=c)
        coppie = S * S * H * (0.5 if c else 1.0)
        ta = tempo(lambda: fa.avanti(q, k, v, causale=c))
        ti = tempo(lambda: fa.indietro(do, q, k, v, o, lse, causale=c))
        # kernel singoli
        sc = D ** -0.5
        import ctypes
        dvec = (do.float() * o.float()).sum(-1).contiguous()
        dq = torch.empty_like(q); dk = torch.empty_like(k); dv = torch.empty_like(v)
        p = lambda t: ctypes.c_void_p(t.data_ptr())
        coda = ([ctypes.c_int(H), ctypes.c_int(1), ctypes.c_int(S), ctypes.c_int(S), ctypes.c_float(sc * fa.LOG2E),
                 ctypes.c_float(sc), ctypes.c_int(1 if c else 0)] + fa._dropout(0.0, 0))
        passi = fa._passi(q) + fa._passi(k) + fa._passi(v) + fa._passi(do)
        tk = tempo(lambda: fa._lancia("fa_dkdv", D, S, H, [p(q), p(k), p(v), p(do), p(lse), p(dvec), p(dk), p(dv)] + passi + coda))
        tq = tempo(lambda: fa._lancia("fa_dq", D, S, H, [p(q), p(k), p(v), p(do), p(lse), p(dvec), p(dq)] + passi + coda))
        tf = lambda fl, t: fl * coppie * D / t / 1e9
        print(f"  S{S} D{D}{' c' if c else '  '}: avanti {ta:7.2f} ms {tf(4, ta):5.1f} TF | dkdv {tk:7.2f} ms {tf(8, tk):5.1f} TF"
              f" | dq {tq:7.2f} ms {tf(6, tq):5.1f} TF | indietro {ti:7.2f} ms (resto {ti - tk - tq:5.2f})", flush=True)


if __name__ == "__main__":
    principale()

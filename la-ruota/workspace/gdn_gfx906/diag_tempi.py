"""Tempo di ogni kernel e del contorno torch, forma del 4B (B1 S256 H32 D128)."""
import statistics, sys, time
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import torch
import gdn_gfx906 as gdn
gdn.EXTRA = sys.argv[2:]

S = int(sys.argv[1]) if len(sys.argv) > 1 else 256
B, H, D = 1, 32, 128
q = torch.randn(B, H, S, D, device="cuda") * D ** -0.5
k = torch.nn.functional.normalize(torch.randn(B, H, S, D, device="cuda"), dim=-1)
v = torch.randn(B, H, S, D, device="cuda")
g = -torch.rand(B, H, S, device="cuda")
beta = torch.rand(B, H, S, device="cuda")
do = torch.randn(B, H, S, D, device="cuda")

def t_ms(fn, n=30):
    for _ in range(3): fn()
    torch.cuda.synchronize()
    ev = [(torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)) for _ in range(n)]
    for a, b in ev:
        a.record(); fn(); b.record()
    torch.cuda.synchronize()
    return statistics.median(a.elapsed_time(b) for a, b in ev)

o, _, salvati = gdn.avanti(q, k, v, g, beta)
NC, BH = S // 64, B * H
Gc, SC, Tm, Am, Pm, Wm, Sst, Vn = salvati
Um = torch.empty_like(v)
import ctypes
ci = ctypes.c_int(NC)
print("prep     ", t_ms(lambda: gdn._lancia(D, D, "gdn_prep", NC, BH, [q, k, v, g, beta, Gc, SC, Tm, Am, Pm, Wm, Um, ci])))
O2 = torch.empty_like(v)
L = ctypes.c_longlong
print("ric      ", t_ms(lambda: gdn._lancia(D, D, "gdn_ric", D // 32, BH, [q, k, SC, Pm, Wm, Um, None, Sst, Vn, O2, None, ci, L(H * S * D), L(D), L(S * D), ctypes.c_int(H), ctypes.c_int(S), ctypes.c_int(0)])))
dSst, dVn = torch.empty_like(Sst), torch.empty_like(v)
print("ric_ind  ", t_ms(lambda: gdn._lancia(D, D, "gdn_ric_ind", D // 32, BH, [q, k, SC, Pm, Wm, do, None, dSst, dVn, None, ci])))
scratch = torch.empty(BH * NC, 4 * 64 * 64 + 64 * D, device="cuda")
dq, dk, dv, db, dg = [torch.empty_like(x) for x in (q, k, v, beta, g)]
print("locale   ", t_ms(lambda: gdn._lancia(D, D, "gdn_locale", NC, BH, [q, k, v, Gc, SC, Tm, Am, Pm, Sst, dSst, Vn, dVn, do, scratch, dq, dk, dv, db, dg, ci])))
print("avanti() ", t_ms(lambda: gdn.avanti(q, k, v, g, beta)))
print("indietro()", t_ms(lambda: gdn.indietro(do, q, k, v, salvati)))
# tempo CPU d'invio di un lancio
torch.cuda.synchronize(); t0 = time.perf_counter()
for _ in range(100): gdn._lancia(D, D, "gdn_prep", NC, BH, [q, k, v, g, beta, Gc, SC, Tm, Am, Pm, Wm, Um, ci])
t1 = time.perf_counter(); torch.cuda.synchronize()
print(f"invio CPU per lancio {1e3*(t1-t0)/100:.3f} ms, fino alla fine {1e3*(time.perf_counter()-t0)/100:.3f} ms")

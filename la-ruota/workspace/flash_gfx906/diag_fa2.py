import sys, torch, torch.nn.functional as F
sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa2_avanti
torch.manual_seed(0)
for S, D, c in ((64, 64, False), (64, 128, False), (128, 64, True)):
    q, k, v = [torch.randn(1, 1, S, D, device="cuda", dtype=torch.float16) for _ in range(3)]
    rif = F.scaled_dot_product_attention(q.float(), k.float(), v.float(), is_causal=c)[0, 0].cpu()
    o = fa2_avanti.flash_avanti(q, k, v, is_causal=c)[0, 0].float().cpu()
    e = (o - rif).abs()
    print(f"S{S} D{D} causale={c}: err max {e.max():.2e}  medio {e.mean():.2e}  |rif| medio {rif.abs().mean():.2e}")
    print("  err medio per gruppo di 16 righe:", [f"{x:.1e}" for x in e.reshape(-1, 16, D).mean((1, 2)).tolist()])
    print("  err medio per colonna d%16:", [f"{x:.1e}" for x in e.reshape(S, -1, 16).mean((0, 1)).tolist()][:16])
    print("  err medio per riga mod 16 (tr):", [f"{x:.1e}" for x in e.reshape(-1, 16, D).mean((0, 2)).tolist()])
    # P in fp16 non normalizzata: quanto errore da sola?
    s = (q.float() @ k.float().transpose(-1, -2))[0, 0].cpu() / D ** 0.5
    if c: s = s.masked_fill(torch.triu(torch.ones(S, S, dtype=torch.bool), 1), float("-inf"))
    p = torch.exp(s - s.max(-1, keepdim=True).values)
    o16 = (p.half().float() @ v[0, 0].float().cpu()) / p.sum(-1, keepdim=True)
    print(f"  emulazione 'P fp16 non normalizzata' err max {(o16 - rif).abs().max():.2e}")

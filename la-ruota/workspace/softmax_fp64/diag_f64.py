"""Isola l'errore muto in fp64 sulla GPU (scoperto confrontando un'attenzione D=128 con fp64)."""
import torch
torch.manual_seed(0)
q = torch.randn(1, 200, 4, 128, dtype=torch.float64); k = torch.randn(1, 517, 4, 128, dtype=torch.float64)
v = torch.randn_like(k)
qt, kt, vt = (x.transpose(1, 2) for x in (q, k, v))
def err(nome, f):
    c = f(lambda x: x); g = f(lambda x: x.cuda()).cpu()
    print(f"{nome:45s} {(g - c).abs().max().item():.3e}")
err("qt @ kt^T (viste)", lambda d: d(qt) @ d(kt).transpose(-1, -2))
err("qt.contig @ kt.contig^T", lambda d: d(qt.contiguous()) @ d(kt.contiguous()).transpose(-1, -2))
s = (qt @ kt.transpose(-1, -2)) * 128 ** -0.5
err("softmax fp64 [1,4,200,517]", lambda d: d(s).softmax(-1))
p = s.softmax(-1)
err("p @ vt (vista)", lambda d: d(p) @ d(vt))
err("p @ vt.contig", lambda d: d(p) @ d(vt.contiguous()))
err("p[0] @ vt[0].contig (3D)", lambda d: d(p[0]) @ d(vt[0].contiguous()))
err("p[0,0] @ vt[0,0] (2D)", lambda d: d(p[0, 0]) @ d(vt[0, 0].contiguous()))
for K in (64, 128, 256, 500, 512, 517, 1000):
    a = torch.randn(4, 200, K, dtype=torch.float64); b = torch.randn(4, K, 128, dtype=torch.float64)
    err(f"bmm 4x200x{K} @ 4x{K}x128", lambda d: d(a) @ d(b))
for K in (64, 517, 1000):
    a = torch.randn(4, 200, K, dtype=torch.float32); b = torch.randn(4, K, 128, dtype=torch.float32)
    err(f"fp32 bmm 4x200x{K} @ 4x{K}x128", lambda d: d(a) @ d(b))

"""Stessa conv 1x1 stride 2, prima con lotto A poi con lotto B nello stesso processo."""
import os, sys
os.environ["MIOPEN_USER_DB_PATH"] = os.environ["MIOPEN_CUSTOM_CACHE_DIR"] = sys.argv[1]
if "--log" in sys.argv:
    os.environ["MIOPEN_ENABLE_LOGGING"] = "1"; os.environ["MIOPEN_LOG_LEVEL"] = "5"
import torch
lotti = [int(v) for v in sys.argv[2].split(",")]
cin, cout, sp = 16, 16, 16
for lotto in lotti:
    torch.manual_seed(0)
    ref = torch.nn.Conv2d(cin, cout, 1, stride=2, bias=False).double()
    x = torch.randn(lotto, cin, sp, sp).double(); xr = x.clone().requires_grad_()
    yr = ref(xr); w = torch.randn_like(yr); (yr * w).sum().backward()
    g = torch.nn.Conv2d(cin, cout, 1, stride=2, bias=False).cuda()
    with torch.no_grad(): g.weight.copy_(ref.weight.float())
    xg = x.float().cuda().requires_grad_(); yg = g(xg); (yg * w.float().cuda()).sum().backward(); torch.cuda.synchronize()
    sc = lambda r, v: ((v.detach().double().cpu() - r).abs().max() / r.abs().max()).item()
    print(f"ESITO lotto {lotto}: avanti {sc(yr, yg):.1e}  dati {sc(xr.grad, xg.grad):.1e}  pesi {sc(ref.weight.grad, g.weight.grad):.1e}", file=sys.stderr, flush=True)

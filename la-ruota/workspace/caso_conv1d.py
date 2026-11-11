"""Un solo caso Conv1d per processo: niente contaminazione fra prove.
Uso: caso_conv1d.py <cin> <cout> <k> <L> <lotto>"""
import sys
import torch
import torch.nn as nn

cin, cout, k, L, lotto = (int(a) for a in sys.argv[1:6])
torch.manual_seed(0)
x = torch.randn(lotto, cin, L)
c = nn.Conv1d(cin, cout, k, padding=k // 2)
cc = nn.Conv1d(cin, cout, k, padding=k // 2)
cc.load_state_dict(c.state_dict())
cc(x.clone().requires_grad_(True)).sum().backward()
cg = c.cuda()
cg(x.clone().cuda().requires_grad_(True)).sum().backward()
rif, got = cc.weight.grad, cg.weight.grad.cpu()
rel = (rif - got).abs().max().item() / max(rif.abs().max().item(), 1e-9)
print(f"rel={rel:.3e} {'ok' if rel < 1e-4 else 'SBAGLIATO'}")

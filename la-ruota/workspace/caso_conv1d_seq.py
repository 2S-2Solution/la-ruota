"""Esegue N casi Conv1d IN SEQUENZA nello stesso processo e riporta ognuno.

Serve a distinguere due ipotesi:
  A) un solver sbagliato per certe forme  -> l'esito dipende solo dalla forma
  B) contaminazione fra chiamate          -> la stessa forma cambia esito a
                                             seconda di cosa e' girato prima
Uso: caso_conv1d_seq.py "cin,cout,k,L,lotto" "..." ...
"""
import sys
import torch
import torch.nn as nn


def caso(cin, cout, k, L, lotto):
    torch.manual_seed(0)
    x = torch.randn(lotto, cin, L)
    c = nn.Conv1d(cin, cout, k, padding=k // 2)
    cc = nn.Conv1d(cin, cout, k, padding=k // 2)
    cc.load_state_dict(c.state_dict())
    cc(x.clone().requires_grad_(True)).sum().backward()
    cg = c.cuda()
    cg(x.clone().cuda().requires_grad_(True)).sum().backward()
    rif, got = cc.weight.grad, cg.weight.grad.cpu()
    return (rif - got).abs().max().item() / max(rif.abs().max().item(), 1e-9)


for spec in sys.argv[1:]:
    p = [int(v) for v in spec.split(",")]
    r = caso(*p)
    print(f"  {spec:22s} rel={r:.3e} {'ok' if r < 1e-4 else 'SBAGLIATO'}", flush=True)

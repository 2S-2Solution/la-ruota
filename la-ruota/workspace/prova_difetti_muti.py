"""I due difetti MUTI dell'ondata 3, verificati sulla build attuale.

Diversi da quelli riparati il 29 ago: quelli erano segfault, questi non danno
alcun segnale. Qui si cercano due cose distinte:
  - uscita AZZERATA (il sintomo riferito per l'LSTM)
  - uscita SBAGLIATA ma non nulla
  - NaN (il sintomo riferito per Conv1d 1x1)
La VEGA-PATCH 59 rifiuta MIOpen solo sopra UNO strato: se il difetto vive a un
solo strato, e' ancora li'.
"""
import torch
import torch.nn as nn

print(f"torch {torch.__version__} | MIOpen abilitato: {torch.backends.cudnn.enabled}\n")


def verdetto(rif, got):
    got_c = got.detach().cpu()
    if torch.isnan(got_c).any():
        return "NaN", float("nan")
    if got_c.abs().max().item() == 0.0 and rif.abs().max().item() > 0:
        return "AZZERATA", 1.0
    rel = (rif - got_c).abs().max().item() / max(rif.abs().max().item(), 1e-9)
    return ("ok" if rel < 1e-4 else "SBAGLIATA"), rel


print("=== 1. LSTM: forward contro CPU, a UNO e piu' strati ===")
print(f"{'strati':>6} {'h':>5} {'seq':>5} {'lotto':>6}  {'esito':>10}  {'rel':>10}")
for strati in (1, 2):
    for h, seq, lotto in [(64, 16, 4), (256, 32, 8), (256, 64, 32), (512, 64, 32), (1024, 128, 16)]:
        torch.manual_seed(0)
        x = torch.randn(seq, lotto, h)
        m = nn.LSTM(h, h, strati)
        g = nn.LSTM(h, h, strati)
        g.load_state_dict(m.state_dict())
        g = g.cuda()
        with torch.no_grad():
            rif = m(x)[0]
            got = g(x.cuda())[0]
        e, rel = verdetto(rif, got)
        print(f"{strati:6d} {h:5d} {seq:5d} {lotto:6d}  {e:>10}  {rel:10.2e}")

print("\n=== 2. Conv1d, con attenzione al kernel 1x1 ===")
print(f"{'cin':>5} {'cout':>5} {'k':>3} {'L':>6}  {'avanti':>10} {'rel':>9}  {'grad pesi':>10} {'rel':>9}")
for cin, cout, k, L in [(1, 8, 1, 64), (3, 8, 1, 64), (8, 16, 1, 128), (64, 64, 1, 256),
                        (3, 8, 3, 64), (8, 16, 5, 128), (128, 128, 1, 512)]:
    torch.manual_seed(0)
    x = torch.randn(4, cin, L)
    c = nn.Conv1d(cin, cout, k, padding=k // 2)
    xc = x.clone().requires_grad_(True)
    cc = nn.Conv1d(cin, cout, k, padding=k // 2)
    cc.load_state_dict(c.state_dict())
    rif = cc(xc)
    rif.sum().backward()
    xg = x.clone().cuda().requires_grad_(True)
    cg = c.cuda()
    got = cg(xg)
    got.sum().backward()
    e_av, r_av = verdetto(rif, got)
    e_pe, r_pe = verdetto(cc.weight.grad, cg.weight.grad)
    print(f"{cin:5d} {cout:5d} {k:3d} {L:6d}  {e_av:>10} {r_av:9.2e}  {e_pe:>10} {r_pe:9.2e}")

print("\n=== 3. Conv1d 1x1 senza MIOpen (per attribuire la colpa) ===")
torch.backends.cudnn.enabled = False
for cin, cout, L in [(1, 8, 64), (64, 64, 256), (128, 128, 512)]:
    torch.manual_seed(0)
    x = torch.randn(4, cin, L)
    c = nn.Conv1d(cin, cout, 1)
    cc = nn.Conv1d(cin, cout, 1)
    cc.load_state_dict(c.state_dict())
    with torch.no_grad():
        rif = cc(x)
        got = c.cuda()(x.cuda())
    e, rel = verdetto(rif, got)
    print(f"  cin={cin:4d} cout={cout:4d} L={L:4d}  {e:>10}  {rel:.2e}")
torch.backends.cudnn.enabled = True

print("\nfine")

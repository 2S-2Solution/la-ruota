"""LSTM: le varianti che il banco precedente non copriva.

Il difetto muto riferito dall'ondata 3 era "MIOpen RNN azzera in silenzio la
forward". La VEGA-PATCH 59 rifiuta MIOpen sopra UNO strato: se il difetto vive
a un solo strato, o in una variante non provata, e' ancora li'. Si controlla
esplicitamente anche l'AZZERAMENTO, non solo lo scarto.
"""
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


def esito(rif, got):
    g = got.detach().cpu()
    if torch.isnan(g).any():
        return "NaN", float("nan")
    if g.abs().max().item() == 0.0 and rif.abs().max().item() > 0:
        return "AZZERATA", 1.0
    rel = (rif - g).abs().max().item() / max(rif.abs().max().item(), 1e-9)
    return ("ok" if rel < 1e-4 else "SBAGLIATA"), rel


def confronta(nome, costruisci, x, impacchetta=False, lunghezze=None):
    torch.manual_seed(0)
    m = costruisci()
    g = costruisci()
    g.load_state_dict(m.state_dict())
    g = g.cuda()
    with torch.no_grad():
        if impacchetta:
            pc = pack_padded_sequence(x, lunghezze, enforce_sorted=False, batch_first=True)
            pg = pack_padded_sequence(x.cuda(), lunghezze, enforce_sorted=False, batch_first=True)
            rif = pad_packed_sequence(m(pc)[0], batch_first=True)[0]
            got = pad_packed_sequence(g(pg)[0], batch_first=True)[0]
        else:
            rif = m(x)[0]
            got = g(x.cuda())[0]
    e, rel = esito(rif, got)
    print(f"  {e:>10}  {rel:10.2e}  {nome}")
    return e == "ok"


print("forward contro CPU, cercando anche l'azzeramento\n")
x = torch.randn(64, 32, 256)
tutti = []
tutti.append(confronta("1 strato, h=256", lambda: nn.LSTM(256, 256, 1), x))
tutti.append(confronta("1 strato bidirezionale", lambda: nn.LSTM(256, 256, 1, bidirectional=True), x))
tutti.append(confronta("1 strato, hidden diverso dall'ingresso", lambda: nn.LSTM(256, 512, 1), x))
tutti.append(confronta("1 strato, h=1024", lambda: nn.LSTM(256, 1024, 1), torch.randn(32, 16, 256)))
tutti.append(confronta("1 strato, sequenza lunga (512)", lambda: nn.LSTM(128, 128, 1), torch.randn(512, 8, 128)))
tutti.append(confronta("1 strato, lotto 1", lambda: nn.LSTM(256, 256, 1), torch.randn(64, 1, 256)))
xb = torch.randn(32, 64, 256)
tutti.append(confronta("1 strato batch_first", lambda: nn.LSTM(256, 256, 1, batch_first=True), xb))
tutti.append(confronta("2 strati batch_first", lambda: nn.LSTM(256, 256, 2, batch_first=True), xb))
tutti.append(confronta("2 strati bidirezionali", lambda: nn.LSTM(256, 256, 2, bidirectional=True), x))
tutti.append(confronta("3 strati", lambda: nn.LSTM(256, 256, 3), x))
tutti.append(confronta("GRU 1 strato", lambda: nn.GRU(256, 256, 1), x))
tutti.append(confronta("RNN relu 1 strato", lambda: nn.RNN(256, 256, 1, nonlinearity="relu"), x))
lung = torch.tensor([64, 48, 32, 16] * 8)
tutti.append(confronta("sequenze impacchettate, 1 strato",
                       lambda: nn.LSTM(256, 256, 1, batch_first=True), xb,
                       impacchetta=True, lunghezze=lung))

print(f"\nsuperate: {sum(tutti)} su {len(tutti)}")

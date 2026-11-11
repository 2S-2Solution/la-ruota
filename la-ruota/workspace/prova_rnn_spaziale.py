"""RNN/LSTM/GRU e spatial transformer su LA RUOTA, contro CPU.

Motivo: rocm-marconi ha trovato che MIOpen differisce da cuDNN su cose che NON
danno errore ma cambiano i numeri:
  - ordine delle porte: LSTM cuDNN (i, f, g, o) vs MIOpen (i, f, o, g);
    GRU cuDNN (r, z, n) vs MIOpen (z, r, n)
  - disposizione dei pesi: cuDNN raggruppa per strato, MIOpen tutte le matrici
    e poi tutte le polarizzazioni -> coincidono solo a UNO strato
  - dropout a probabilita' zero, descrittori a 3 dimensioni, descrittori nulli
Se il percorso MIOpen nativo di PyTorch sbagliasse la traduzione, una LSTM a due
strati si addestrerebbe con le porte scambiate senza dare alcun segnale.
Qui si confronta con la CPU, che e' l'unico riferimento affidabile.
"""
import torch
import torch.nn as nn

print(f"torch {torch.__version__} | {torch.cuda.get_device_name(0)}")
print(f"MIOpen abilitato: {torch.backends.cudnn.enabled}\n")


def confronta(nome, costruisci, ingresso, extra=None):
    """Esegue lo stesso modello su CPU e GPU dagli stessi pesi, avanti e indietro."""
    try:
        torch.manual_seed(0)
        m_cpu = costruisci()
        torch.manual_seed(0)
        m_gpu = costruisci()
        m_gpu.load_state_dict(m_cpu.state_dict())
        m_gpu = m_gpu.cuda()

        x_cpu = ingresso.clone().requires_grad_(True)
        x_gpu = ingresso.clone().cuda().requires_grad_(True)

        o_cpu = m_cpu(x_cpu)
        o_gpu = m_gpu(x_gpu)
        if isinstance(o_cpu, tuple):
            o_cpu, o_gpu = o_cpu[0], o_gpu[0]

        e_avanti = (o_cpu - o_gpu.cpu()).abs().max().item()
        o_cpu.sum().backward()
        o_gpu.sum().backward()
        e_ingr = (x_cpu.grad - x_gpu.grad.cpu()).abs().max().item()
        e_pesi = max(
            (a.grad - b.grad.cpu()).abs().max().item()
            for a, b in zip(m_cpu.parameters(), m_gpu.parameters())
            if a.grad is not None and b.grad is not None
        )
        peggiore = max(e_avanti, e_ingr, e_pesi)
        esito = "OK  " if peggiore < 1e-4 else "FAIL"
        print(f"  {esito} {nome:34s} avanti {e_avanti:.2e}  grad ingr {e_ingr:.2e}  grad pesi {e_pesi:.2e}")
        return peggiore < 1e-4
    except Exception as exc:
        print(f"  FAIL {nome:34s} {type(exc).__name__}: {str(exc)[:110]}")
        return False


print("[1] ricorrenti - il caso a 2 strati e' quello che smaschera la disposizione dei pesi")
x = torch.randn(6, 4, 16)  # (seq, lotto, ingresso)

confronta("LSTM 1 strato", lambda: nn.LSTM(16, 24, 1), x)
confronta("LSTM 2 strati", lambda: nn.LSTM(16, 24, 2), x)
confronta("LSTM 2 strati bidirezionale", lambda: nn.LSTM(16, 24, 2, bidirectional=True), x)
confronta("LSTM 3 strati", lambda: nn.LSTM(16, 24, 3), x)
confronta("GRU 1 strato", lambda: nn.GRU(16, 24, 1), x)
confronta("GRU 2 strati", lambda: nn.GRU(16, 24, 2), x)
confronta("RNN tanh 2 strati", lambda: nn.RNN(16, 24, 2, nonlinearity="tanh"), x)
confronta("RNN relu 2 strati", lambda: nn.RNN(16, 24, 2, nonlinearity="relu"), x)
confronta("LSTM batch_first", lambda: nn.LSTM(16, 24, 2, batch_first=True), torch.randn(4, 6, 16))

print("\n[2] dropout nelle ricorrenti (p=0 e' il caso che fa cadere MIOpen)")
confronta("LSTM 2 strati, dropout 0.0", lambda: nn.LSTM(16, 24, 2, dropout=0.0), x)


def lstm_dropout_valutazione():
    # con dropout > 0 il confronto ha senso solo in eval, dove il dropout e' inattivo
    torch.manual_seed(0)
    m = nn.LSTM(16, 24, 2, dropout=0.5).eval()
    torch.manual_seed(0)
    g = nn.LSTM(16, 24, 2, dropout=0.5)
    g.load_state_dict(m.state_dict())
    g = g.cuda().eval()
    with torch.no_grad():
        err = (m(x)[0] - g(x.cuda())[0].cpu()).abs().max().item()
    assert err < 1e-4, f"scarto {err}"
    return err


try:
    print(f"  OK   {'LSTM dropout 0.5 (eval)':34s} scarto {lstm_dropout_valutazione():.2e}")
except Exception as exc:
    print(f"  FAIL {'LSTM dropout 0.5 (eval)':34s} {type(exc).__name__}: {str(exc)[:110]}")

print("\n[3] spatial transformer (affine_grid + grid_sample)")


def spaziale():
    torch.manual_seed(0)
    theta_cpu = torch.randn(4, 2, 3).requires_grad_(True)
    inp_cpu = torch.randn(4, 3, 16, 16).requires_grad_(True)
    theta_gpu = theta_cpu.detach().clone().cuda().requires_grad_(True)
    inp_gpu = inp_cpu.detach().clone().cuda().requires_grad_(True)

    def passo(theta, inp):
        g = torch.nn.functional.affine_grid(theta, inp.shape, align_corners=False)
        return torch.nn.functional.grid_sample(inp, g, align_corners=False)

    o_cpu = passo(theta_cpu, inp_cpu)
    o_gpu = passo(theta_gpu, inp_gpu)
    o_cpu.sum().backward()
    o_gpu.sum().backward()

    # NB: criterio RELATIVO. I gradienti su theta hanno modulo ~3e+02, quindi una
    # soglia assoluta di 1e-4 li boccia per il solo arrotondamento fp32 (verificato:
    # in float64 lo scarto scende a 1e-15). Il divisore ha un pavimento per non
    # ricadere nella trappola opposta, l'errore relativo su un riferimento nullo.
    def rel(a, b):
        return (a - b).abs().max().item() / max(a.abs().max().item(), 1e-6)

    e_av = rel(o_cpu, o_gpu.cpu())
    e_in = rel(inp_cpu.grad, inp_gpu.grad.cpu())
    e_th = rel(theta_cpu.grad, theta_gpu.grad.cpu())
    peggiore = max(e_av, e_in, e_th)
    assert peggiore < 1e-5, f"scarto relativo {peggiore}"
    return f"rel: avanti {e_av:.2e}  grad ingresso {e_in:.2e}  grad theta {e_th:.2e}"


try:
    print(f"  OK   {'affine_grid + grid_sample':34s} {spaziale()}")
except Exception as exc:
    print(f"  FAIL {'affine_grid + grid_sample':34s} {type(exc).__name__}: {str(exc)[:110]}")

print("\n[4] CTC loss")


def ctc():
    torch.manual_seed(0)
    T, N, C = 20, 4, 8
    lp_cpu = torch.randn(T, N, C).log_softmax(2).requires_grad_(True)
    lp_gpu = lp_cpu.detach().clone().cuda().requires_grad_(True)
    bers = torch.randint(1, C, (N, 6))
    li = torch.full((N,), T, dtype=torch.long)
    lb = torch.full((N,), 6, dtype=torch.long)
    l_cpu = torch.nn.functional.ctc_loss(lp_cpu, bers, li, lb)
    l_gpu = torch.nn.functional.ctc_loss(lp_gpu, bers.cuda(), li.cuda(), lb.cuda())
    l_cpu.backward()
    l_gpu.backward()
    e_l = abs(l_cpu.item() - l_gpu.item())
    e_g = (lp_cpu.grad - lp_gpu.grad.cpu()).abs().max().item()
    assert max(e_l, e_g) < 1e-4, f"perdita {e_l}, gradiente {e_g}"
    return f"perdita {e_l:.2e}  gradiente {e_g:.2e}"


try:
    print(f"  OK   {'ctc_loss':34s} {ctc()}")
except Exception as exc:
    print(f"  FAIL {'ctc_loss':34s} {type(exc).__name__}: {str(exc)[:110]}")

print("\nfine")

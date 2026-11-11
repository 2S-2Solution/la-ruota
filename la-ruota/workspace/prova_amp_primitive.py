"""Restringe il difetto: quali primitive AMP funzionano e quale cade.

torch._amp_foreach_non_finite_check_and_unscale_ provoca un access violation con
offset 0x0 dentro torch_hip.dll - cioe' una chiamata a un puntatore nullo, sul
lato host, prima di qualunque lancio di kernel (il log del runtime si ferma su
hipGetDevice). Qui si stabilisce il confine esatto del guasto.
"""
import torch


def prova(nome, fn):
    try:
        r = fn()
        torch.cuda.synchronize()
        print(f"  OK   {nome}: {r}", flush=True)
    except Exception as e:
        print(f"  FAIL {nome}: {type(e).__name__} {str(e)[:110]}", flush=True)


print("1. _amp_update_scale_ (stesso file sorgente, altra funzione)", flush=True)


def aggiorna_scala():
    s = torch.full((1,), 256.0, device="cuda")
    t = torch.zeros(1, device="cuda")
    f = torch.zeros(1, device="cuda")
    torch._amp_update_scale_(s, t, f, 2.0, 0.5, 1)
    return f"scala -> {s.item()}"


prova("_amp_update_scale_", aggiorna_scala)

print("2. unscale_ su CPU (verifica che il dispatch sia sano)", flush=True)


def su_cpu():
    g = [torch.randn(8, 8)]
    t = torch.zeros(1)
    i = torch.full((1,), 0.5)
    torch._amp_foreach_non_finite_check_and_unscale_(g, t, i)
    return f"trovato_inf={t.item()}"


prova("unscale_ CPU", su_cpu)

print("3. unscale_ su GPU con lista vuota (esce prima di ogni calcolo)", flush=True)


def lista_vuota():
    t = torch.zeros(1, device="cuda")
    i = torch.full((1,), 0.5, device="cuda")
    torch._amp_foreach_non_finite_check_and_unscale_([], t, i)
    return "uscita anticipata riuscita"


prova("unscale_ GPU, lista vuota", lista_vuota)

print("4. unscale_ su GPU con un tensore (il caso che cade)", flush=True)


def uno():
    g = [torch.randn(8, 8, device="cuda")]
    t = torch.zeros(1, device="cuda")
    i = torch.full((1,), 0.5, device="cuda")
    torch._amp_foreach_non_finite_check_and_unscale_(g, t, i)
    return f"trovato_inf={t.item()}"


prova("unscale_ GPU", uno)

print("fine", flush=True)

"""Verifica della VEGA-PATCH 69: piu' stream ed eventi, in Python e dentro TorchScript.

    python prova_stream_eventi.py

Prima della patch tutte le prove con uno stream nuovo fallivano con "HIP error: invalid
argument" (hipStreamWaitEvent sullo stream nullo), e dentro TorchScript
torch.cuda.synchronize() spariva dal grafo.
"""
import torch

x = torch.randn(512, 512, device="cuda")
esiti = []


def prova(nome, f):
    try:
        d = f()
        esiti.append(True)
        print(f"  OK    {nome:55s} {d}")
    except Exception as e:  # noqa: BLE001
        esiti.append(False)
        righe = [r for r in str(e).splitlines() if "error" in r.lower()] or str(e).splitlines()
        print(f"  ERR   {nome:55s} {righe[0][:120]}")


def stream_nuovo_wait_stream():
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s):
        y = x @ x
    torch.cuda.current_stream().wait_stream(s)
    d = (y - x @ x).abs().max().item()
    assert d < 1e-3, d
    return f"scarto {d:.1e}"


def evento_wait_event():
    s = torch.cuda.Stream()
    with torch.cuda.stream(s):
        y = x * 3
        e = torch.cuda.Event()
        e.record(s)
    torch.cuda.current_stream().wait_event(e)
    assert torch.equal(y, x * 3)
    return "ok"


def evento_wait():
    s = torch.cuda.Stream()
    with torch.cuda.stream(s):
        y = x + 1
    e = s.record_event()
    e.wait(torch.cuda.current_stream())
    assert torch.equal(y, x + 1)
    return "ok"


def tanti_stream_in_catena():
    # 8 stream in catena: ogni passo aspetta il precedente
    acc = x.clone()
    prec = torch.cuda.current_stream()
    for _ in range(8):
        s = torch.cuda.Stream()
        s.wait_stream(prec)
        with torch.cuda.stream(s):
            acc = acc * 1.0 + 1.0
        prec = s
    torch.cuda.current_stream().wait_stream(prec)
    assert torch.allclose(acc, x + 8)
    return "8 stream ok"


def copia_non_bloccante_su_stream():
    h = torch.randn(1 << 20).pin_memory()
    s = torch.cuda.Stream()
    with torch.cuda.stream(s):
        g = h.to("cuda", non_blocking=True)
    torch.cuda.current_stream().wait_stream(s)
    g.record_stream(torch.cuda.current_stream())
    assert torch.equal(g.cpu(), h)
    return "ok"


def tempi_con_eventi():
    a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    a.record()
    y = x @ x
    b.record()
    torch.cuda.synchronize()
    return f"{a.elapsed_time(b):.3f} ms"


for n, f in (("stream nuovo + wait_stream (andata e ritorno)", stream_nuovo_wait_stream),
             ("evento su stream nuovo + wait_event", evento_wait_event),
             ("record_event + Event.wait", evento_wait),
             ("8 stream in catena", tanti_stream_in_catena),
             ("copia pinned non bloccante su stream secondario", copia_non_bloccante_su_stream),
             ("tempi con eventi sullo stream corrente", tempi_con_eventi)):
    prova(n, f)


@torch.jit.script
def ts_synchronize(a: torch.Tensor) -> bool:
    s = torch.cuda.current_stream(a.device.index)
    f = torch.cuda.Event(True, False, False)
    b = a @ a
    f.record(s)
    torch.cuda.synchronize(a.device.index)
    return f.query()


@torch.jit.script
def ts_tempi(a: torch.Tensor) -> float:
    s = torch.cuda.current_stream(a.device.index)
    i = torch.cuda.Event(True, False, False)
    f = torch.cuda.Event(True, False, False)
    i.record(s)
    b = a @ a
    f.record(s)
    torch.cuda.synchronize(a.device.index)
    return i.elapsed_time(f)


@torch.jit.script
def ts_stream_nuovo(a: torch.Tensor) -> torch.Tensor:
    s = torch.cuda.Stream(a.device, 0)
    s.wait_stream(torch.cuda.current_stream(a.device.index))
    with torch.cuda.stream(s):
        b = a * 3
    torch.cuda.current_stream(a.device.index).wait_stream(s)
    return b


def ts_sync():
    assert ts_synchronize(x), "evento non concluso dopo synchronize"
    return "evento concluso"


def ts_stream():
    assert torch.equal(ts_stream_nuovo(x), x * 3)
    return "ok"


prova("TorchScript: synchronize() resta nel grafo e sincronizza", ts_sync)
prova("TorchScript: eventi con tempi", lambda: f"{ts_tempi(x):.3f} ms")
prova("TorchScript: stream nuovo, with torch.cuda.stream, wait_stream", ts_stream)

print(f"\n{sum(esiti)} su {len(esiti)} ok")

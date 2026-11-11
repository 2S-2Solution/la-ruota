"""Verifica della VEGA-PATCH 68: torch.cuda dentro TorchScript (register_cuda_ops.cpp).

    python prova_torchscript_cuda.py
"""
import torch


@torch.jit.script
def con_stream_ed_eventi(a: torch.Tensor) -> torch.Tensor:
    indice = a.device.index
    s = torch.cuda.current_stream(indice)
    inizio = torch.cuda.Event(enable_timing=True)
    fine = torch.cuda.Event(enable_timing=True)
    inizio.record(s)
    b = a @ a
    fine.record(s)
    torch.cuda.synchronize(indice)
    assert inizio.elapsed_time(fine) >= 0.0
    return b


@torch.jit.script
def con_stream_nuovo(a: torch.Tensor) -> torch.Tensor:
    s = torch.cuda.Stream(a.device, 0)
    with torch.cuda.stream(s):
        b = a * 3
    torch.cuda.current_stream(a.device.index).wait_stream(s)
    return b


x = torch.randn(256, 256, device="cuda")
esiti = []
for nome, f, atteso in (("stream corrente, eventi con tempo, synchronize", con_stream_ed_eventi, x @ x),
                        ("stream nuovo, with torch.cuda.stream, wait_stream", con_stream_nuovo, x * 3)):
    try:
        d = (f(x) - atteso).abs().max().item()
        assert d < 1e-3, f"scarto {d}"
        esiti.append(True)
        print(f"  OK    {nome}  (scarto {d:.1e})")
    except Exception as e:  # noqa: BLE001
        esiti.append(False)
        righe = [r for r in str(e).splitlines() if r.strip()]
        print(f"  ERR   {nome}: {type(e).__name__}:")
        for r in righe[:12]:
            print(f"          {r[:160]}")
print(f"\n{sum(esiti)} su {len(esiti)} ok")

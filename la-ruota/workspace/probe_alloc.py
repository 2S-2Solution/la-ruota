"""Sonda graduale del percorso di allocazione PyTorch.

Uso: probe_alloc.py <indice>   -- esegue UN solo passo, cosi' un access
violation non nasconde i passi successivi (ognuno gira in un processo suo).
"""
import sys

import torch

PASSI = [
    ("cuda.init", lambda: torch.cuda.init()),
    ("current_device", lambda: torch.cuda.current_device()),
    ("device_count", lambda: torch.cuda.device_count()),
    ("current_stream", lambda: torch.cuda.current_stream()),
    ("synchronize", lambda: torch.cuda.synchronize()),
    ("mem_get_info", lambda: torch.cuda.mem_get_info()),
    ("memory_allocated", lambda: torch.cuda.memory_allocated()),
    ("caching_allocator_alloc", lambda: torch.cuda.caching_allocator_alloc(64)),
    ("empty(16)", lambda: torch.empty(16, device="cuda")),
    ("empty(16) pinned-free path", lambda: torch.empty(16, device="cuda").fill_(0)),
]

i = int(sys.argv[1])
nome, fn = PASSI[i]
print(f"[{i}] {nome} ...", flush=True)
r = fn()
print(f"[{i}] {nome}: OK -> {r}", flush=True)

"""Precisione mista per i Linear di UN modello (22 ott 2026).

Solo le moltiplicazioni in fp16 (ingresso e pesi arrotondati), accumulo fp32 e USCITA FP32 (gemm_gfx906.lineare_misto):
residui, norme, softmax, attenzione e tutto il resto restano fp32. Diverso dall'autocast fp16
globale (uscite fp16), che su un modello di prova dava 0,007 sulle probabilita'.
Aggancio per ISTANZA, non globale: tocca solo i Linear del modulo dato (le altre reti del processo restano fp32).
Ricade sul Linear fp32 originale con gradiente attivo, fuori da CUDA fp32, o con K non multiplo di 32.

    import lineari_misti
    n = lineari_misti.aggancia(modello)      # numero di Linear agganciati
    lineari_misti.sgancia(modello)
"""
import sys
import types

import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, r"C:\LaRuota_workspace\gemm_gfx906")
import gemm_gfx906 as gg  # noqa: E402

CONTATORI = {"misti": 0, "fp32": 0}


def _avanti_misto(self, x):
    if (not torch.is_grad_enabled() or not (self.weight.requires_grad or x.requires_grad)) and x.is_cuda \
            and x.dtype == torch.float32 and self.weight.dtype == torch.float32 and not torch.is_autocast_enabled():
        x2 = x.reshape(-1, x.shape[-1])
        if not x2.is_contiguous():
            x2 = x2.contiguous()
        if gg.supportata_misto(x2, self.weight):
            CONTATORI["misti"] += 1
            y = gg.lineare_misto(x2, self.weight, self.bias)
            return y.reshape(*x.shape[:-1], self.out_features)
    CONTATORI["fp32"] += 1
    return F.linear(x, self.weight, self.bias)


def aggancia(modulo, escludi=()):
    """Sostituisce il forward dei nn.Linear dentro `modulo` (per istanza). `escludi`: nomi (o prefissi) da lasciare fp32."""
    n = 0
    for nome, m in modulo.named_modules():
        if type(m) is nn.Linear and not any(nome.startswith(e) for e in escludi) and "forward" not in m.__dict__:
            m.forward = types.MethodType(_avanti_misto, m)
            n += 1
    return n


def sgancia(modulo):
    for _, m in modulo.named_modules():
        if type(m) is nn.Linear and "forward" in m.__dict__:
            del m.forward

"""Flash attention di rocm-marconi collegata a scaled_dot_product_attention — su richiesta.

    import sys; sys.path.insert(0, r"C:\\LaRuota_workspace\\ruota_flash")
    import ruota_flash
    ruota_flash.attiva()        # da qui in poi F.scaled_dot_product_attention passa di qui
    ruota_flash.disattiva()     # torna l'originale
    ruota_flash.contatori       # quante chiamate sono andate alla flash e quante no, e perche'

Il kernel (C:\\LaRuota_workspace\\flash_gfx906\\fa_gfx906.py, rocm-marconi) copre: fp16, head
dim 64/128/256, GQA, S_q != S_k, maschera causale (allineata in alto a sinistra come
PyTorch), dropout, avanti e indietro. Memoria O(S) invece di O(S^2).

Tutto il resto va al percorso ORIGINALE, invariato: attn_mask, fp32 senza autocast, altre
head dim, tensori non 4D, e D=256 non causale (li' il kernel e' piu' lento del percorso
standard: 0,77x, misura di rocm-marconi). Sotto autocast fp16 gli ingressi fp32 vengono
convertiti in fp16, come farebbe autocast per sdpa.

Il dropout usa una maschera propria (hash di seme, testa, query, chiave), non la sequenza
casuale di PyTorch: stessa distribuzione, numeri diversi. Il seme viene dal generatore di
torch, quindi torch.manual_seed rende il risultato riproducibile.
"""
import sys
from collections import Counter

import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_gfx906 as _fa  # noqa: E402

_originale = F.scaled_dot_product_attention
contatori = Counter()


def _motivo_per_non_usarla(q, k, v, attn_mask, enable_gqa, is_causal):
    if attn_mask is not None:
        return "attn_mask"
    if not (q.is_cuda and k.is_cuda and v.is_cuda):
        return "non GPU"
    if q.dim() != 4 or k.dim() != 4 or v.dim() != 4:
        return "non 4D"
    if k.shape != v.shape or q.shape[0] != k.shape[0] or q.shape[3] != k.shape[3]:
        return "forme"
    D = q.shape[3]
    if D not in _fa.DIMENSIONI:
        return f"head_dim {D}"
    if q.shape[1] != k.shape[1]:
        if not enable_gqa or q.shape[1] % k.shape[1]:
            return "teste diverse senza enable_gqa"
    if D == 256 and not is_causal:
        return "D=256 non causale (piu' lenta)"
    if 0 in q.shape or 0 in k.shape:
        return "vuoto"
    return None


def _dtype_di_lavoro(q, k, v):
    tipi = {q.dtype, k.dtype, v.dtype}
    if tipi == {torch.float16}:
        return torch.float16
    if torch.is_autocast_enabled("cuda") and torch.get_autocast_dtype("cuda") == torch.float16:
        return torch.float16
    return None


def scaled_dot_product_attention(query, key, value, attn_mask=None, dropout_p=0.0,
                                 is_causal=False, scale=None, enable_gqa=False):
    motivo = _motivo_per_non_usarla(query, key, value, attn_mask, enable_gqa, is_causal)
    if motivo is None and _dtype_di_lavoro(query, key, value) is None:
        motivo = "non fp16"
    if motivo is not None:
        contatori[f"originale: {motivo}"] += 1
        return _originale(query, key, value, attn_mask=attn_mask, dropout_p=dropout_p,
                          is_causal=is_causal, scale=scale, enable_gqa=enable_gqa)
    contatori["flash"] += 1
    q, k, v = (t.to(torch.float16) for t in (query, key, value))
    return _fa.attenzione(q, k, v, causale=is_causal, scala=scale, dropout=float(dropout_p))


def attiva():
    """Da qui in poi F.scaled_dot_product_attention passa dall'instradatore."""
    F.scaled_dot_product_attention = scaled_dot_product_attention
    torch.nn.functional.scaled_dot_product_attention = scaled_dot_product_attention


def disattiva():
    F.scaled_dot_product_attention = _originale
    torch.nn.functional.scaled_dot_product_attention = _originale


def attiva_ora():
    return F.scaled_dot_product_attention is scaled_dot_product_attention

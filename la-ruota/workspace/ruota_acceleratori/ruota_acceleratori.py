"""Acceleratori della ruota, da accendere con una riga in un addestramento.

    import sys; sys.path.insert(0, r"C:\\LaRuota_workspace\\ruota_acceleratori")
    import ruota_acceleratori
    ruota_acceleratori.attiva()      # dopo aver importato transformers, prima del modello
    ...
    ruota_acceleratori.aggancia_lora_peft()   # DOPO aver sistemato LoraLinear.forward (peft)

Accende (kernel di rocm-marconi, guida Rocm sezioni 4b-4j):
  - gdn:     Gated DeltaNet (attenzione lineare di Qwen3.5) con la conv causale fusa;
  - flash:   flash attention collegata a scaled_dot_product_attention (ruota_flash);
  - norme:   Qwen3_5RMSNorm / RMSNormGated / F.rms_norm / F.layer_norm fuse (norme_gfx906);
  - perdita: lm_head + cross-entropy a blocchi, senza i logit fp32 (perdita_gfx906). L'uscita del
             modello ha logits=None quando si passano le labels: spegnerla se servono i logit;
  - gemm:    F.linear fp16 con le forme tarate e il riallineamento a 2 MB (gemm_gfx906);
  - aggancia_lora_peft(): ramo LoRA di peft in tre kernel, senza copie fp32 [N, D] (lora_gfx906).
Interruttori d'ambiente: RUOTA_ACCELERATORI=0 (tutti), RUOTA_GDN / RUOTA_FLASH / RUOTA_NORME /
RUOTA_PERDITA / RUOTA_GEMM / RUOTA_LORA = 0. Misure: guida della ruota, A6.
"""
import os
import sys

_attivi = {}
_W = r"C:\LaRuota_workspace"


def _spento(nome):
    return os.environ.get("RUOTA_ACCELERATORI", "1") == "0" or os.environ.get(nome, "1") == "0"


def _importa(cartella, modulo):
    percorso = os.path.join(_W, cartella)
    if percorso not in sys.path:
        sys.path.insert(0, percorso)
    return __import__(modulo)


def attiva(verboso=True):
    """Accende quello che si puo'. Restituisce {nome: stato} e lo stampa."""
    try:
        from transformers.models.qwen3_5 import modeling_qwen3_5
    except ImportError:
        modeling_qwen3_5 = None
    for nome, chiave in (("gdn", "RUOTA_GDN"), ("flash", "RUOTA_FLASH"), ("norme", "RUOTA_NORME"),
                         ("perdita", "RUOTA_PERDITA"), ("gemm", "RUOTA_GEMM")):
        if nome in _attivi:
            continue
        if _spento(chiave):
            _attivi[nome] = "spento dall'ambiente"
            continue
        if nome in ("gdn", "perdita") and modeling_qwen3_5 is None:
            _attivi[nome] = "saltato: transformers senza Qwen3.5"
            continue
        if nome == "gdn":
            _importa("gdn_gfx906", "gdn_gfx906").aggancia(modeling_qwen3_5)
            _attivi[nome] = "acceso" + (" (solo la funzione: GDN_STRATO=0)"
                                        if os.environ.get("GDN_STRATO", "1") == "0" else "")
        elif nome == "flash":
            _importa("ruota_flash", "ruota_flash").attiva()
            _attivi[nome] = "acceso"
        elif nome == "norme":
            _importa("norme_gfx906", "norme_gfx906").aggancia()
            _attivi[nome] = "acceso"
        elif nome == "perdita":
            _importa("perdita_gfx906", "perdita_gfx906").aggancia()
            _attivi[nome] = "acceso (logits=None con le labels)"
        elif nome == "gemm":
            g = _importa("gemm_gfx906", "gemm_gfx906")
            g.aggancia()
            _attivi[nome] = f"acceso ({len(g.SCELTE)} forme tarate, riallineamento " \
                            f"{'spento' if os.environ.get('GEMM_ALLINEA', '1') == '0' else 'acceso'})"
    if verboso:
        print("[ruota] acceleratori: " + ", ".join(f"{k} {v}" for k, v in _attivi.items()), flush=True)
    return dict(_attivi)


def aggancia_lora_peft(verboso=True):
    """Ramo LoRA di peft (Linear) nei kernel di lora_gfx906, sopra il forward gia' in uso.

    Va chiamata DOPO eventuali sostituzioni di LoraLinear.forward (es. applica_lora_in_fp32 di
    train_qwen35): le avvolge. Percorso veloce solo se: un adattatore attivo, dropout nullo,
    A e B fp32 senza bias, base Linear congelata su GPU, nessuna fusione (merged); altrimenti il
    forward avvolto, invariato.
    """
    if "lora" in _attivi:
        return _attivi["lora"]
    if _spento("RUOTA_LORA"):
        _attivi["lora"] = "spento dall'ambiente"
        return _attivi["lora"]
    lg = _importa("lora_gfx906", "lora_gfx906")
    from peft.tuners.lora.layer import Linear as LoraLinear
    import torch
    precedente = LoraLinear.forward
    conteggio = {"veloce": 0, "originale": 0}

    def forward(self, x, *args, **kwargs):
        if not args and not kwargs and not self.disable_adapters and not getattr(self, "merged", False):
            attivi = [n for n in self.active_adapters if n in self.lora_A]
            if len(attivi) == 1:
                n = attivi[0]
                base, a, b, d = self.base_layer, self.lora_A[n], self.lora_B[n], self.lora_dropout[n]
                senza_dropout = isinstance(d, torch.nn.Identity) or getattr(d, "p", 1.0) == 0.0
                if (senza_dropout and isinstance(base, torch.nn.Linear) and a.bias is None and b.bias is None
                        and not getattr(self, "use_dora", {}).get(n, False)
                        and (base.bias is None or not base.bias.requires_grad)
                        and lg.supportato(x, base.weight, a.weight, b.weight)):
                    conteggio["veloce"] += 1
                    return lg.lora(x, base.weight, base.bias, a.weight, b.weight, self.scaling[n])
        conteggio["originale"] += 1
        return precedente(self, x, *args, **kwargs)

    forward._ruota = conteggio
    LoraLinear.forward = forward
    _attivi["lora"] = "acceso (peft)"
    if verboso:
        print("[ruota] LoRA peft fuso agganciato", flush=True)
    return _attivi["lora"]


def aggancia_torchvision_gpu(verboso=True):
    """Operazioni di torchvision sulla GPU che la ruota compila solo per la CPU.

    torchvision della ruota (0.20.0+ruota) ha le operazioni proprie solo CPU: PyTorch 2.5 rifiuta le
    estensioni HIP su Windows. Qui si registra sulla chiave CUDA il kernel hipRTC di rocm-marconi per
    torchvision::deform_conv2d (DCNv2 con maschera: DCNv2Pack di basicsr, BasicVSR++), verificato contro
    fp64 e contro torchvision CPU (6,2e-7). Solo l'avanti (inferenza); groups=1, C multiplo di 16.
    Da chiamare dopo import torchvision. RUOTA_TORCHVISION_GPU=0 lo spegne.
    """
    if "torchvision_gpu" in _attivi:
        return _attivi["torchvision_gpu"]
    if _spento("RUOTA_TORCHVISION_GPU"):
        _attivi["torchvision_gpu"] = "spento dall'ambiente"
    else:
        try:
            import torchvision  # noqa: F401  (definisce lo schema torchvision::deform_conv2d)
        except ImportError:
            _attivi["torchvision_gpu"] = "saltato: torchvision non installato"
        else:
            _importa("restauro_gfx906", "vsr_dcn").registra()
            _attivi["torchvision_gpu"] = "acceso (deform_conv2d)"
    if verboso:
        print(f"[ruota] torchvision GPU: {_attivi['torchvision_gpu']}", flush=True)
    return _attivi["torchvision_gpu"]


def contatori_flash():
    """Quante chiamate a sdpa sono andate alla flash, e perche' le altre no."""
    if "ruota_flash" in sys.modules:
        return dict(sys.modules["ruota_flash"].contatori)
    return {}


def contatori_lora():
    try:
        from peft.tuners.lora.layer import Linear as LoraLinear
        return dict(getattr(LoraLinear.forward, "_ruota", {}))
    except ImportError:
        return {}

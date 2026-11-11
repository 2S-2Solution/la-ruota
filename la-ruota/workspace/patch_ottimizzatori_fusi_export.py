"""VEGA-PATCH 83 - ottimizzatori fused=True (Adam, AdamW, SGD) in crash: 0xC0000005 all'avvio di torch_hip.

Sintomo (20-22 ott): torch.optim.{Adam,AdamW,SGD}(fused=True).step() su GPU fa crollare il processo
senza messaggio; foreach e CPU funzionano. Pila presa con un gestore vettoriale (diag_fused\\pila_al_crollo.py):
l'istruzione che fallisce sta all'indirizzo BASE di torch_hip.dll, cioe' una chiamata attraverso una voce
d'import nulla. Causa: lo stesso difetto delle «20 operazioni che saltavano a zero» del 29 ago
(memoria export-mancante-venti-op-rotte). FusedAdamKernel.hip, FusedAdamWKernel.hip e FusedSgdKernel.hip
DEFINISCONO _fused_{adam,adamw,sgd}_kernel_cuda_ senza includere il proprio ATen/ops/<op>_native.h,
quindi senza export; RegisterCUDA.cpp (stessa DLL) le dichiara dllimport e chiama la voce d'import,
che resta vuota. dumpbin /exports: le tre funzioni NON esportate. Rimedio: includere l'header (con la
dichiarazione TORCH_API, clang-cl aggiunge dllexport alla definizione: «redeclared without dllimport»).
Nei .hip e nei .cu (questa build compila i .hip gia' generati).

    python patch_ottimizzatori_fusi_export.py --prova | --applica
"""
import io
import os
import shutil
import sys

BASE = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native"
MARCA = "[VEGA-PATCH 83"
LAVORI = [
    ("hip\\FusedAdamKernel.hip", "#include <ATen/TypeDefault.h>\n", "_fused_adam"),
    ("hip\\FusedAdamWKernel.hip", "#include <ATen/TypeDefault.h>\n", "_fused_adamw"),
    ("hip\\FusedSgdKernel.hip", "#include <ATen/Dispatch.h>\n", "_fused_sgd"),
    ("cuda\\FusedAdamKernel.cu", "#include <ATen/TypeDefault.h>\n", "_fused_adam"),
    ("cuda\\FusedAdamWKernel.cu", "#include <ATen/TypeDefault.h>\n", "_fused_adamw"),
    ("cuda\\FusedSgdKernel.cu", "#include <ATen/Dispatch.h>\n", "_fused_sgd"),
]
applica = "--applica" in sys.argv
errori = 0
for rel, ancora, op in LAVORI:
    f = os.path.join(BASE, rel)
    t = io.open(f, encoding="utf-8", newline="").read()
    if MARCA in t:
        print(f"{rel}: gia' applicata")
        continue
    crlf = "\r\n" in t
    a = ancora.replace("\n", "\r\n") if crlf else ancora
    nl = "\r\n" if crlf else "\n"
    nuovo = (a + f"#include <ATen/ops/{op}_native.h>  // [VEGA-PATCH 83] senza, la funzione non e' esportata"
             f" e RegisterCUDA salta a una voce d'import nulla{nl}")
    if t.count(a) != 1:
        print(f"  ERRORE {rel}: ancora trovata {t.count(a)} volte")
        errori += 1
        continue
    t = t.replace(a, nuovo)
    if applica:
        if not os.path.exists(f + ".bak_pre_vega83"):
            shutil.copy2(f, f + ".bak_pre_vega83")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
        print(f"{rel}: applicata")
    else:
        print(f"{rel}: prova a vuoto riuscita")
sys.exit(1 if errori else 0)

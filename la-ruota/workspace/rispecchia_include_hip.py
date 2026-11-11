"""Porta nei .hip gli include aggiunti da Rocm nei .cu.

Serve perche' questa build compila i .hip GIA' generati nell'albero, non
riesegue hipify: patchare i .cu da solo non avrebbe alcun effetto. Si evita
anche di rilanciare hipify, che su Windows puo' riportare successo senza
scrivere nulla.

Traduzione dei percorsi: cuda -> hip, .cu -> .hip. Il contenuto degli include
non cambia: ATen/ops/<op>_native.h e' lo stesso per entrambi i rami.
"""
import io
import os
import re
import shutil
import sys

sys.path.insert(0, r"C:\LaRuota_workspace")
from applica_patch_export_2026_08_29 import PATCH, RADICE  # stessa mappa, una fonte sola

RIGA_OPS = re.compile(r"^#include <ATen/ops/[^>]+>\s*$")
applica = "--applica" in sys.argv


def in_hip(rel):
    # NB: hipify rinomina anche i NOMI dei file, non solo le cartelle:
    # SparseCUDATensorMath.cu -> SparseHIPTensorMath.hip
    return (rel.replace("cuda\\", "hip\\")
               .replace("CUDA", "HIP")
               .replace(".cu", ".hip"))


def sistema(percorso, header):
    testo = io.open(percorso, encoding="utf-8", errors="replace").read()
    riga = f"#include <ATen/ops/{header}>"
    if riga in testo:
        return None  # gia' presente
    linee = testo.splitlines(keepends=True)
    # inserimento in ordine alfabetico fra gli altri ATen/ops
    indici = [i for i, l in enumerate(linee) if RIGA_OPS.match(l)]
    if indici:
        pos = indici[-1] + 1
        for i in indici:
            if linee[i].strip() > riga:
                pos = i
                break
    else:
        # nessun blocco ATen/ops: si mette dopo l'ultimo #include
        inc = [i for i, l in enumerate(linee) if l.startswith("#include")]
        if not inc:
            return "NESSUN INCLUDE TROVATO"
        pos = inc[-1] + 1
    linee.insert(pos, riga + "\n")
    if applica:
        io.open(percorso, "w", encoding="utf-8", newline="").write("".join(linee))
    return "aggiunto"


totale = mancanti = 0
for rel, headers in sorted(PATCH.items()):
    rel_hip = in_hip(rel)
    percorso = os.path.join(RADICE, rel_hip)
    if not os.path.exists(percorso):
        print(f"  ASSENTE  {rel_hip}")
        mancanti += 1
        continue
    if applica and not os.path.exists(percorso + ".bak_pre_export"):
        shutil.copy2(percorso, percorso + ".bak_pre_export")
    fatti = []
    for h in headers:
        esito = sistema(percorso, h)
        if esito == "aggiunto":
            fatti.append(h)
            totale += 1
        elif esito:
            print(f"  {esito}  {rel_hip}  {h}")
    stato = ("aggiunti " + str(len(fatti))) if fatti else "gia' a posto"
    print(f"  {stato:14s} {rel_hip}")

print(f"\ninclude {'aggiunti' if applica else 'da aggiungere'}: {totale}"
      + (f"   file .hip assenti: {mancanti}" if mancanti else ""))
if not applica:
    print("prova a vuoto: nulla e' stato scritto. Rilancia con --applica")

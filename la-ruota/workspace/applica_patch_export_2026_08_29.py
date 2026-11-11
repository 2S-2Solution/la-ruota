"""Aggiunge gli #include ATen/ops mancanti che lasciano funzioni senza dllexport.

    python applica_patch_export_2026_08_29.py --prova     # non scrive, dice cosa farebbe
    python applica_patch_export_2026_08_29.py --applica   # scrive, con copia .bak

PERCHE'
Un file .cu che DEFINISCE una funzione senza includere il proprio
`ATen/ops/<op>_native.h` la compila senza `TORCH_API`, cioe' senza dllexport.
`RegisterCUDA.cpp` — che sta nella STESSA DLL — la vede dichiarata dllimport e
genera una chiamata indiretta; il corpo resta non referenziato, il linker lo
scarta, la voce di import resta nulla, e la chiamata salta a zero.
Su Linux e' innocuo. Su Windows e' un access violation.

E' la stessa famiglia della VEGA-PATCH 48 (lug) e della 60 (ago). Qui e' la
battuta sistematica: 14 file, 24 include.

L'inserimento avviene nel ramo `#else` di `AT_PER_OPERATOR_HEADERS`, in ordine
alfabetico fra gli altri `ATen/ops/`. E' idempotente: se l'include c'e' gia',
salta.
"""
import io
import os
import re
import shutil
import sys

RADICE = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native"

PATCH = {
    r"cuda\AdaptiveAveragePooling.cu": ["adaptive_avg_pool2d_native.h"],
    r"cuda\AdaptiveAveragePooling3d.cu": ["_adaptive_avg_pool3d_backward_native.h",
                                          "_adaptive_avg_pool3d_native.h"],
    r"cuda\Dropout.cu": ["_fused_dropout_native.h", "native_dropout_native.h"],
    r"cuda\MultiLabelMarginCriterion.cu": ["multilabel_margin_loss_backward_native.h",
                                           "multilabel_margin_loss_forward_native.h"],
    r"cuda\Normalization.cu": ["_native_batch_norm_legit_native.h"],
    r"cuda\SoftMax.cu": ["_masked_softmax_backward_native.h"],
    r"cuda\TensorCompare.cu": ["_assert_async_native.h"],
    r"cuda\ValidateCompressedIndicesKernel.cu": ["_validate_compressed_sparse_indices_native.h"],
    r"quantized\cuda\FusedObsFakeQuant.cu": ["_fused_moving_avg_obs_fq_helper_native.h"],
    r"sparse\cuda\SoftMax.cu": ["_sparse_log_softmax_backward_data_native.h",
                                "_sparse_log_softmax_native.h",
                                "_sparse_softmax_backward_data_native.h",
                                "_sparse_softmax_native.h"],
    r"sparse\cuda\SparseCUDATensorMath.cu": ["_sparse_sum_backward_native.h",
                                             "mul_native.h"],
    r"sparse\cuda\SparseCsrTensorMath.cu": ["_sparse_csr_prod_native.h",
                                            "_sparse_csr_sum_native.h"],
    r"transformers\cuda\attention.cu": ["_scaled_dot_product_cudnn_attention_native.h",
                                        "_transform_bias_rescale_qkv_native.h"],
    r"transformers\cuda\attention_backward.cu": [
        "_scaled_dot_product_cudnn_attention_backward_native.h",
        "_scaled_dot_product_efficient_attention_backward_native.h"],
}

RIGA_OPS = re.compile(r"^#include <ATen/ops/[^>]+>\s*$")


def sistema(percorso, header, applica):
    testo = io.open(percorso, encoding="utf-8", errors="replace").read()
    aggiunti = []
    for h in header:
        if f"<ATen/ops/{h}>" in testo:
            continue
        righe = testo.split("\n")
        indici = [i for i, r in enumerate(righe) if RIGA_OPS.match(r)]
        if not indici:
            # Il file non ha affatto il blocco per-operatore: lo si crea
            # nella forma canonica di upstream, dopo l'ultimo #include.
            ultimi = [i for i, r in enumerate(righe) if r.startswith("#include")]
            if not ultimi:
                return None, f"nessun #include in {os.path.basename(percorso)}"
            blocco = ["",
                      "#ifndef AT_PER_OPERATOR_HEADERS",
                      "#include <ATen/NativeFunctions.h>",
                      "#else",
                      f"#include <ATen/ops/{h}>",
                      "#endif"]
            righe[ultimi[-1] + 1:ultimi[-1] + 1] = blocco
            testo = chr(10).join(righe)
            aggiunti.append(h)
            continue
        nuova = f"#include <ATen/ops/{h}>"
        # inserimento in ordine alfabetico fra gli altri
        dove = indici[-1] + 1
        for i in indici:
            if righe[i] > nuova:
                dove = i
                break
        righe.insert(dove, nuova)
        testo = "\n".join(righe)
        aggiunti.append(h)
    if aggiunti and applica:
        if not os.path.exists(percorso + ".bak_pre_export"):
            shutil.copy2(percorso, percorso + ".bak_pre_export")
        io.open(percorso, "w", encoding="utf-8", newline="\n").write(testo)
    return aggiunti, None


def main():
    applica = "--applica" in sys.argv
    if not applica and "--prova" not in sys.argv:
        print(__doc__)
        return 1
    print("MODO:", "SCRITTURA" if applica else "prova (non scrive niente)")
    print()
    tot = 0
    for rel, header in sorted(PATCH.items()):
        p = os.path.join(RADICE, rel)
        if not os.path.exists(p):
            print(f"  ASSENTE  {rel}")
            continue
        aggiunti, errore = sistema(p, header, applica)
        if errore:
            print(f"  ERRORE   {rel}: {errore}")
        elif aggiunti:
            print(f"  {'scritto' if applica else 'da fare'}  {rel}")
            for h in aggiunti:
                print(f"             + ATen/ops/{h}")
            tot += len(aggiunti)
        else:
            print(f"  gia' ok  {rel}")
    print()
    print(f"include {'aggiunti' if applica else 'da aggiungere'}: {tot}")
    if applica:
        print("copie di sicurezza: <file>.bak_pre_export")
        print()
        print("ATTENZIONE: questi .cu vengono HIPIFICATI in .hip prima di compilare.")
        print("Su Windows hipify puo' riportare successo SENZA scrivere nulla.")
        print("Verifica che la modifica sia arrivata nei .hip generati prima di")
        print("dare la colpa alla patch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

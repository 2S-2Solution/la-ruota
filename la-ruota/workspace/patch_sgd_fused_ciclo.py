"""VEGA-PATCH 84 - SGD fused=True si blocca sulla GPU: ciclo infinito per `auto i_start = threadIdx.x`.

Trovato il 22 ott col registro HIP (diag_fused\\sgd_fused_registro.py): ultimo lancio il kernel di
multi_tensor_apply {1}x{512}, poi hipDeviceSynchronize non torna piu'. In HIP 5.7 threadIdx.x NON e' un
intero ma un oggetto coordinata (amd_hip_runtime.h:282-285) con
    __device__ R operator+=(const R& rhs) { return F{}(0) + rhs; }
che RESTITUISCE la somma ma non modifica nulla. Con `auto i_start = threadIdx.x` si copia l'oggetto, e
`i_start += blockDim.x` non fa avanzare il ciclo: infinito. FusedSgdKernel.hip:94 (percorso veloce,
tensori allineati) e' l'unico punto di ATen in cui una variabile `auto` copiata da una coordinata viene poi
incrementata (gli altri `auto x = threadIdx.x` sono solo letti). Rimedio come in ForeachFunctors:
`int64_t i_start = threadIdx.x`.

    python patch_sgd_fused_ciclo.py --prova | --applica
"""
import io
import os
import shutil
import sys

FILES = [r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\FusedSgdKernel.hip",
         r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\cuda\FusedSgdKernel.cu"]
VECCHIO = "      for (auto i_start = threadIdx.x;"
NUOVO = ("      // [VEGA-PATCH 84] int64_t, non auto: in HIP threadIdx.x e' un oggetto il cui += non modifica\n"
         "      for (int64_t i_start = threadIdx.x;")
errori = 0
for f in FILES:
    t = io.open(f, encoding="utf-8", newline="").read()
    if "[VEGA-PATCH 84" in t:
        print(f"{os.path.basename(f)}: gia' applicata")
        continue
    nuovo = NUOVO.replace("\n", "\r\n") if "\r\n" in t else NUOVO
    if t.count(VECCHIO) != 1:
        print(f"  ERRORE {os.path.basename(f)}: trovato {t.count(VECCHIO)} volte")
        errori += 1
        continue
    t = t.replace(VECCHIO, nuovo)
    if "--applica" in sys.argv:
        if not os.path.exists(f + ".bak_pre_vega84"):
            shutil.copy2(f, f + ".bak_pre_vega84")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
        print(f"{os.path.basename(f)}: applicata")
    else:
        print(f"{os.path.basename(f)}: prova a vuoto riuscita")
sys.exit(1 if errori else 0)

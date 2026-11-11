"""VEGA-PATCH 80 - softmax / log_softmax fp64 sulla GPU sbagliate per righe dispari 513-1021.

Trovato da rocm-marconi il 20 ott (softmax_fp64\\diag_softmax.py): errore 0,2-0,5, muto,
su 248 lunghezze su 255; fp32/fp16, pari, <= 512, >= 1023 giuste.

Causa (anche upstream in 2.5): con righe oltre la soglia del kernel persistente (fp64: > 512
elementi) si va in cunn_SoftMaxForward con blocco = lunghezza arrotondata al multiplo di 64
(SoftMaxForward_getBlockSize). Se la riga non e' allineata a 16 byte (fp64, lunghezza dispari:
una riga su due) ilpReduce e WriteFpropResultsVectorized fanno un primo giro "un elemento per
thread" che presuppone riga+shift >= blockDim: con 513..1021 non e' cosi', e i thread in
eccesso LEGGONO (max e somma) e SCRIVONO la riga successiva. 1023 torna giusta perche'
1023+1 = 1024 = blocco. Rimedio: nel primo giro anche `threadIdx.x < size`, nei tre punti
(avanti: riduzione e scrittura; indietro: scrittura). Upstream ha la stessa guardia in seguito.

    python patch_softmax_fp64_righe_corte.py --prova | --applica
"""
import io
import os
import shutil
import sys

FILES = [r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\SoftMax.hip",
         r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\cuda\SoftMax.cu"]
MARCA = "[VEGA-PATCH 80"
SOSTITUZIONI = [
    ("    if(threadIdx.x >= shift){\n      threadVal = r(threadVal, data[offset]);",
     "    if(threadIdx.x >= shift && threadIdx.x < size){  // [VEGA-PATCH 80] riga piu' corta del blocco\n"
     "      threadVal = r(threadVal, data[offset]);"),
    ("    if (threadIdx.x >= shift) {\n      output[offset] = epilogue(input[offset]);",
     "    if (threadIdx.x >= shift && threadIdx.x < size) {  // [VEGA-PATCH 80]\n"
     "      output[offset] = epilogue(input[offset]);"),
    ("    if (threadIdx.x >= shift) {\n      gradInput[offset] = epilogue(gradOutput[offset], output[offset]);",
     "    if (threadIdx.x >= shift && threadIdx.x < size) {  // [VEGA-PATCH 80]\n"
     "      gradInput[offset] = epilogue(gradOutput[offset], output[offset]);"),
]
# 80b (stesso giorno): la guardia sopra NON bastava. Dopo il primo giro `size -= blockDim.x` rende
# size NEGATIVO (es. 642 - 704 = -62), e `size % (ILP * blockDim.x)` si calcola in UNSIGNED perche'
# blockDim.x e' unsigned: -62 diventa 4294967234, `last` esce a caso, e il ciclo di coda
# (offset = size - last + threadIdx.x, offset < size) legge e scrive ALL'INDIETRO, nella riga
# precedente. Verificato: la riga 0 prendeva i valori della riga 1; una riga sfalsata da sola
# sbagliava lo stesso. Rimedio: modulo con segno. La quarta occorrenza (classes, sempre >= 0) resta.
MARCA_B = "[VEGA-PATCH 80b"
SOSTITUZIONI_B = [
    ("  index_t last = size % (ILP * blockDim.x);\n",
     "  index_t last = size % (ILP * static_cast<index_t>(blockDim.x));  // [VEGA-PATCH 80b] con segno: size puo' essere < 0\n"),
    ("  const int last = size % (ILP * blockDim.x);\n",
     "  const int last = size % (ILP * static_cast<int>(blockDim.x));  // [VEGA-PATCH 80b]\n"),
    ("  const index_t last = size % (ILP * blockDim.x);\n",
     "  const index_t last = size % (ILP * static_cast<index_t>(blockDim.x));  // [VEGA-PATCH 80b]\n"),
]
applica = "--applica" in sys.argv
errori = 0
for f in FILES:
    t = io.open(f, encoding="utf-8", newline="").read()
    if MARCA in t:
        if MARCA_B in t:
            print(f"{os.path.basename(f)}: gia' applicata (80 e 80b)")
            continue
        crlf = "\r\n" in t
        for vecchio, nuovo in SOSTITUZIONI_B:
            if crlf:
                vecchio, nuovo = vecchio.replace("\n", "\r\n"), nuovo.replace("\n", "\r\n")
            n = t.count(vecchio)
            if n != 1:
                print(f"  ERRORE {os.path.basename(f)}: trovato {n} volte: {vecchio.strip()[:60]}")
                errori += 1
                continue
            t = t.replace(vecchio, nuovo)
        if applica and not errori:
            if not os.path.exists(f + ".bak_pre_vega80b"):
                shutil.copy2(f, f + ".bak_pre_vega80b")
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            print(f"{os.path.basename(f)}: applicata la 80b")
        elif not errori:
            print(f"{os.path.basename(f)}: 80b, prova a vuoto riuscita")
        continue
    crlf = "\r\n" in t
    for vecchio, nuovo in SOSTITUZIONI:
        if crlf:
            vecchio, nuovo = vecchio.replace("\n", "\r\n"), nuovo.replace("\n", "\r\n")
        n = t.count(vecchio)
        if n != 1:
            print(f"  ERRORE {os.path.basename(f)}: trovato {n} volte: {vecchio.strip()[:60]}")
            errori += 1
            continue
        t = t.replace(vecchio, nuovo)
    if applica and not errori:
        if not os.path.exists(f + ".bak_pre_vega80"):
            shutil.copy2(f, f + ".bak_pre_vega80")
        io.open(f, "w", encoding="utf-8", newline="").write(t)
        print(f"{os.path.basename(f)}: applicata")
    elif not errori:
        print(f"{os.path.basename(f)}: prova a vuoto riuscita")
sys.exit(1 if errori else 0)

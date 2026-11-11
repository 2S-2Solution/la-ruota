# Perdita fusa sul vocabolario per gfx906 — stato al 20 ottobre 2026 (rocm-marconi)

`perdita_gfx906.py`: lm_head + cross-entropy a blocchi di token (~256 MB di logit per blocco,
`PERDITA_MB_BLOCCO`). Per blocco: GEMM rocBLAS dei logit, un kernel per riga (lse in fp32, perdita,
gradiente softmax − onehot scritto SOPRA i logit), GEMM verso dh. Niente copia fp32 dei logit né
tensori [N, V] all'indietro; il modello restituisce `logits = None`. lm_head congelato (LoRA): dW non
si calcola (con lm_head allenabile ricade sull'originale).
`perdita_gfx906.aggancia()` avvolge `Qwen3_5ForCausalLM.forward` e `Qwen3_5ForConditionalGeneration.forward`
(solo con `labels`, `logits_to_keep = 0`, senza `shift_labels`). Convenzioni di transformers:
etichette spostate di uno, ignore_index −100, media sui validi o somma / num_items_in_batch.

**Correttezza** (`banco.py`): 8/8 contro cross_entropy in CPU fp64, fp32 e fp16, V 1.000 / 50.021 /
248.320, blocchi da 10 righe, etichette ignorate fino al 30%, num_items_in_batch, grad_out ≠ 1.
fp16: dh con metà dell'errore di torch (gradiente non scalato, niente sottoflusso). fp32: il kernel
sbaglia 4e-7 sul gradiente dei logit; dh eredita ~2e-5 dalla GEMM rocBLAS su K = V (anche col gradiente
esatto), soglia 5e-5.

**Da misurare** (GPU libera): tempo e picco (`banco.py --tempi`, 512 × 248.320) e passo LoRA vero
(`diag_gemm\ab_lora.py --perdita`, perdite uguali e memoria di picco; 1024 token senza checkpointing?).

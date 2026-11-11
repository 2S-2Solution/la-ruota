# RMSNorm fusa per gfx906 — stato al 20 ottobre 2026 (rocm-marconi)

`norme_gfx906.py`: un kernel in avanti e uno all'indietro (hipRTC), tre modalità:
- **MODO 0** `F.rms_norm` (lo usa `nn.RMSNorm`): `y = x · rstd · w`;
- **MODO 1** `Qwen3_5RMSNorm`: `(x · rstd) · (1 + w)` in fp32, poi al tipo d'ingresso;
- **MODO 2** `Qwen3_5RMSNormGated`: stessi arrotondamenti del modello (`T(x·rstd)`, `T(w·h)`, `· silu(gate)`).

Un'onda per riga, riduzione in fp32 con `__shfl_xor`; gradiente del peso per somme parziali per onda
(niente atomiche fp32 su gfx906). Aggancio nel solo processo: `norme_gfx906.aggancia()` sostituisce
`F.rms_norm` e i due `forward` di Qwen3.5 (ricade sull'originale fuori da fp16/fp32 su GPU o con
forme non supportate).

**Correttezza** (`banco.py`): 31/31 — tre modalità × fp32/fp16 × D 2560/256/128/192/100, avanti, dx,
dw e dgate contro CPU fp64. In fp16 l'errore è uguale o minore dell'originale (riduzione in fp32:
`F.rms_norm` di PyTorch 2.5 riduce nel tipo d'ingresso, quindi non è identico al bit).

**Tempi** (`banco.py --tempi`, 20 ott, GPU OCCUPATA da altri processi: indicativi). Solo avanti:
RMSNorm di strato 512 tok 0,247 → 0,040 ms (6×); q_norm 512×16 teste 0,148 → 0,036 (4×); norma con
gate 512×32 teste 0,615 → 0,062 (10×); `F.rms_norm` fp32 forma 1256×96×192 1,51 → 1,15 (1,3×).
Avanti+indietro: incoerenti a GPU occupata, da rimisurare.

**Da fare:** A/B sul passo LoRA vero (`diag_gemm\ab_lora.py`, opzione da aggiungere) e su un
modello fp32, a GPU libera.

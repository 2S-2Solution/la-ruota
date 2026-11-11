# LoRA fuso per gfx906 — stato al 20 ottobre 2026 (rocm-marconi)

`lora_gfx906.py`: y = base(x) + scala · B(A(x)) con base fp16 congelata e A, B fp32 (la forma della
classe `Lora` di `prova_lora_4b_reale.py`). GEMM base a rocBLAS; il ramo LoRA in tre kernel per rango
piccolo (giu: x Aᵀ leggendo fp16 e accumulando fp32, riduzione a metà fra le corsie; su_somma: scala ·
u Bᵀ sommato DENTRO y o dx; rid: dA e dB a parziali). Spariscono x.float(), d.to(fp16), * scala, la
somma, e all'indietro le copie fp32 [N, Dout] e [N, Din].
`lora_gfx906.aggancia_classe(Lora)` oppure `lora_gfx906.lora(x, W, bias, A, B, scala)`.
Rango potenza di 2 fino a 64; peso base congelato.

**Correttezza** (`banco.py`): 10/10 contro la classe Lora su GPU e CPU fp64 — forme q/k/v/o di
Qwen3.5-4B a 512 token, ranghi 1-64, forme irregolari, bias. y e dx come torch; dA e dB più precisi.

**Da misurare** (GPU libera): `banco.py --tempi` e passo vero `diag_gemm\ab_lora.py --lora`.

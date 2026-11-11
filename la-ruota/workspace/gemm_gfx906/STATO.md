# GEMM gfx906 — stato al 20 ottobre 2026 (rocm-marconi)

`gemm_gfx906.py`: C = A @ B fp16, accumulo fp32 con v_dot2_f32_f16. Tessera 128x128x32, 256 thread,
8x8 uscite per thread, LDS a coppie lungo K, doppio buffer, una barriera per passo, bias nella chiusura
del kernel, split-K (asse z) con parziali fp32 e un kernel di somma. Quattro disposizioni (A e B con K
contigua o no): avanti x W^T, dX = dY W, dW = dY^T X. `aggancia()` sostituisce F.linear fp16 (avanti e
indietro, autograd proprio).

**Correttezza** (`banco.py`): 4 disposizioni x split 1-8 x 4 forme, errore uguale a rocBLAS;
Linear 512x2560→4096 con bias: y, dx, dW, db uguali a rocBLAS (contro CPU fp64).

**Registri**: con il ciclo interno srotolato tutto il compilatore sversava (256 VGPR, 251 sversamenti,
~1 TFLOPS); `UNROLL_K2` 2-8 → 120-126 VGPR, 0 sversamenti, 2 onde/SIMD (`registri.py`).

**Tempi a GPU CONDIVISA** (altri processi attivi; minimi, indicativi; anche valori impossibili sopra il picco
nei minimi, quindi da rifare): nucleo ~20-20,6 TFLOPS sulle forme grandi senza split (rocBLAS ~20-21);
sulle forme deboli lo split-K vince: down avanti 512x2560x9216 13,5 → 16,8, q 512x4096x2560 14,4 → 16,2,
o_proj 512x2560x4096 12,6 → 13,3. L'ordine delle tessere (M più veloce) e lo srotolamento non spostano
il nucleo (`varianti.py`).

**Uso sicuro**: `mm()` usa il kernel solo per le forme in `tarature.json` (scelta ≥3% meglio di rocBLAS);
le altre vanno a rocBLAS (`GEMM_NON_TARATE=stima` per la stima). Il file NON esiste ancora: si crea con
`banco.py --tara` A GPU LIBERA (forme del passo LoRA a 256/512/1024 token).

**Per salire oltre ~20 sul nucleo** (a GPU libera, con misure pulite): tessere 128x256 o 256x128 per
le M grandi, letture LDS della fase successiva in anticipo nei registri, stream-K al posto dello split.

# Flash attention per gfx906 — stato al 20 ottobre 2026

> Oggi: `fa_gfx906.py`, avanti e indietro, D ∈ {64, 128, 256}, GQA. Lo stato attuale è nelle
> sezioni del 19 e del 20 ottobre; quelle prima sono la storia del prototipo.

2S. Studio di fattibilità con prototipo del solo passo in avanti.
Non tocca la ruota: modulo autonomo, kernel compilato a runtime con hipRTC.

## Perché un kernel nostro

Non c'è niente di pronto per gfx906, verificato nei sorgenti di TheRock:

- **aotriton** (quello che PyTorch usa su ROCm): supporta solo `gfx90a`, `gfx942`,
  `gfx950`, `gfx11`, `gfx12` (`external-builds/pytorch/build_prod_wheels.py:956`).
- **Composable Kernel** ha la FMHA (`example/ck_tile/01_fmha`), e il filtro della build
  accetta qualunque «gfx9». Ma il warp-gemm di ck_tile esiste solo come MFMA, SMFMAC e
  WMMA: tutte istruzioni matriciali che gfx906 non ha.

## Cosa c'è

| file | cosa |
|---|---|
| `fa_avanti.py` | il prototipo: `flash_avanti(q, k, v, is_causal, scale)`, fp16, `[B, H, S, D]`, D ∈ {64, 128} |
| `banco_avanti.py` | `correttezza` e `prestazioni` contro il percorso standard |
| `varianti.py` | griglia su blocco di tasti `CH` e onde minime `ONDE`, con registri e sversamenti |

## Esito

**Correttezza: 8 casi su 8**, al primo tentativo — forme non multiple di 64, causale,
D=64 e 128, lotti multipli, S=1. Scarto 4,9e-4 contro fp32, identico al percorso fp16
attuale (è l'arrotondamento dell'uscita).

**Memoria: la vittoria è netta.**

| forma | percorso attuale | flash |
|---|---:|---:|
| B1 H16 S4096 D128 | 3.456 MB | 16 MB |
| B1 H16 S8192 D128 causale | **13.824 MB** | **32 MB** |

A 8192 token l'attenzione di uno strato occupa quasi tutta la scheda da 16 GB.

**Tempo: alla pari** (da 0,89x a 1,31x), con un kernel ancora inefficiente:
**0,35–1,1 TFLOPS** contro un tetto teorico attorno ai 17 per `v_dot2_f32_f16`.

## Perché è lento, misurato sul disassemblato

- Le istruzioni sono quelle giuste: `v_dot2_f32_f16` per Q·K, `v_fma_mix_f32` per P·V
  (il valore fp16 entra direttamente nella FMA fp32), letture `ds_read_b128`.
- **Ma i registri vettoriali sono saturi** (256 anche con D=64), quindi una sola onda per
  SIMD e nessuna latenza nascosta. E con D=128 **ci sono sversamenti** in memoria: da 156
  a 234 istruzioni `buffer_store_dword`/`buffer_load_dword`.
- `__launch_bounds__(64, ONDE)` non cambia l'allocazione dei registri: con hipRTC il
  secondo parametro qui non vincola niente.

⚠️ Per cercare gli sversamenti bisogna cercare `buffer_store_dword`, non `buffer_store`:
la prima analisi li aveva mancati per questo.


## 19 ottobre: fa2, l'avanti a tessere — FATTO

`fa2_avanti.py`. Il prototipo era limitato dalla LDS, non solo dai registri: ogni thread aveva
una riga intera di Q, quindi ogni valore di K/V letto dalla LDS serviva una sola istruzione.
La fa2 lavora come un GEMM a registri: workgroup di 256 thread per 64 righe, ogni thread
calcola 4 righe x 4 chiavi (riuso 4x), softmax online con 4 `__shfl_xor` fra le 16 corsie di
una riga, P in fp16 nella LDS, e P·V anch'esso con `v_dot2` grazie a V salvata trasposta a
coppie di chiavi (`Vt[k/2][d] = (V[k][d], V[k+1][d])`). 134/177 VGPR (D 64/128), zero
sversamenti.

**Correttezza: 12/12** (`banco2.py correttezza`). Errore assoluto contro fp32 uguale al
percorso math fp16 (es. 9,8e-4 contro 9,7e-4 causale): il limite e' P in fp16, come in
FlashAttention-2 (emulato su CPU: 1,4-4e-4). ⚠️ Il vecchio criterio "4x lo scarto relativo di
math con pavimento 1e-2" bocciava due casi: era il criterio, non il kernel.

**Tempi (GPU sana, 19 ott, `banco2.py prestazioni`, B1 H16):**

| forma | math ms | prototipo ms | fa2 ms | fa2/math | TFLOPS fa2 |
|---|---:|---:|---:|---:|---:|
| S1024 D64 | 1,55 | 1,91 | 0,75 | 2,07x | 5,7 |
| S4096 D64 | 24,58 | 19,19 | 10,03 | 2,45x | 6,9 |
| S2048 D128 | 10,31 | 18,48 | 4,57 | 2,26x | 7,5 |
| S4096 D128 | 34,57 | 63,14 | 18,19 | 1,90x | 7,6 |
| S4096 D128 causale | 38,81 | 35,00 | 8,49 | 4,57x | 8,1 |
| S8192 D128 causale | 130,77 | 130,13 | 32,08 | 4,08x | 8,6 |

⚠️ Il 17 ott sera la GPU aveva ~350 ms di ritardo fisso per lotto (stato del driver, sparito
col riavvio): i tempi di quella sera erano tutti uguali e vanno buttati. Prima di misurare,
`diag_stream_nullo\latenza2.py` (non incluso nel repository).

## 19 ottobre: l'indietro — FATTO (prima versione)

`fa2_indietro.py`: `flash_indietro(do, q, k, v, o, lse2, is_causal, scale)` e
`flash_attenzione(q, k, v, is_causal, scale)` (una `autograd.Function`). L'avanti restituisce
il logsumexp per riga (`flash_avanti(..., lse=True)`, base 2). Due kernel perche' gfx906 non
ha atomiche fp32 globali: `fa2_dkdv` (32 chiavi ferme, 64 query che scorrono) e `fa2_dq` (32
query ferme, 64 chiavi che scorrono), entrambi ricalcolano P. Le coppie fp16 per `v_dot2`
lungo query/chiavi si compongono al volo da due letture LDS (le copie trasposte non stanno
nei 64 KB a D=128). 204-228 VGPR, zero sversamenti.

**Correttezza 11/11** (`banco_indietro.py correttezza`): errore assoluto dei gradienti contro
fp32 dello stesso ordine del percorso math fp16 (≤ 1,6e-3 su gradienti fino a ~5); logsumexp
≤ 2e-6. ⚠️ Il riferimento va fatto con FOGLIE fp32: con foglie fp16 i gradienti "fp32"
tornano arrotondati a fp16 e math fp16 sembra perfetto.

**Avanti+indietro, B1 H16:**

| forma | math ms | fa2 ms | rapporto | memoria math → fa2 |
|---|---:|---:|---:|---|
| S1024 D64 | 7,18 | 5,35 | 1,34x | 276 → 20 MB |
| S2048 D64 causale | 17,91 | 9,55 | 1,88x | 1064 → 40 MB |
| S1024 D128 | 8,43 | 10,66 | 0,79x | 296 → 40 MB |
| S2048 D128 causale | 24,88 | 19,50 | 1,28x | 1104 → 80 MB |
| S4096 D128 causale | 91,77 | 71,95 | 1,28x | 4256 → 160 MB |

L'indietro gira a ~3,8 TFLOPS (l'avanti 8): un'onda per SIMD per i registri, e le coppie
composte al volo costano istruzioni.

## 19 ottobre (sera): `fa_gfx906.py`, la versione da collegare — FATTA

Un modulo unico con i tre kernel (avanti, dK/dV, dQ) generalizzati:
- **stride qualunque** per batch/testa/sequenza (ultima dimensione contigua; righe allineate a
  16 byte, altrimenti copia), **S_q ≠ S_k**, maschera causale **in alto a sinistra** come
  `scaled_dot_product_attention` (chiave ≤ query);
- **dropout**: maschera da un hash deterministico di (seme, testa, query, chiave), rigenerata
  nell'indietro senza salvarla; denominatore con P intera, P·V con P abbandonata e riscalata.
  `maschera_dropout(...)` la ricalcola in torch per i banchi.
- **indietro a 256 thread** (4 onde): con 128 thread e un solo workgroup per CU (LDS) due SIMD
  su quattro restavano fermi. 64 righe ferme; a D=128 il blocco che scorre scende a 32 righe
  per stare nei 64 KB (massimo ~62,7 KB).

Interfaccia: `avanti(q, k, v, causale, scala, dropout, seme) -> (o, lse2)`,
`indietro(do, q, k, v, o, lse2, causale, scala, dropout, seme) -> (dq, dk, dv)`,
`attenzione(q, k, v, causale, scala, dropout, seme=None)` (autograd).

**Correttezza 12/12** (`banco_fa.py correttezza`): S_q ≠ S_k nei due versi, stride da layout
[B, S, H, D], dropout 0,1/0,2/0,5 contro la stessa maschera in torch, causale; errore assoluto
della fa mai sopra quello del calcolo fp16 diretto.

**Tempi (B1 H16, `banco_fa.py prestazioni`):**

| forma | math avanti | fa avanti | math a+i | fa a+i | avanti | a+i |
|---|---:|---:|---:|---:|---:|---:|
| S1024 D64 | 1,67 | 0,85 | 7,08 | 4,13 | 1,96x | 1,72x |
| S4096 D64 causale | 29,04 | 5,48 | 60,25 | 25,53 | 5,30x | 2,36x |
| S1024 D128 | 2,07 | 1,39 | 8,41 | 7,09 | 1,49x | 1,19x |
| S2048 D128 causale | 11,53 | 2,65 | 24,93 | 13,54 | 4,35x | 1,84x |
| S4096 D128 causale | 39,32 | 8,84 | 91,56 | 45,82 | 4,45x | 2,00x |

### Prossimi passi
1. ~~Indietro~~ fatto; da accelerare: meno registri (2 onde per SIMD), coppie
   pre-trasposte dove la LDS lo consente (D=64).
1b. **Indietro (nota storica)** (dQ, dK, dV) con logsumexp salvato dall'avanti; gfx906 non ha atomiche fp32
   in memoria globale, quindi due kernel: uno per dK/dV (per blocco di chiavi), uno per dQ
   (per blocco di query), ricalcolando P.
2. Logsumexp in uscita dall'avanti, stride qualunque, S_q != S_k, dropout (Philox con seme e
   offset, rigenerato nell'indietro).
3. Interfaccia per la Ruota (sotto).

## 20 ottobre: head_dim 256 (Qwen3.5-4B) e GQA — FATTO

Qwen3.5-4B usa D=256 nell'attenzione piena (16 teste di query, 4 di K/V). A D=256 una riga occupa
528 byte in LDS: con le tessere di D=128 l'avanti chiedeva ~100 KB (Q, K, V^T a 64 righe) e
l'indietro K, V, Q, dO interi insieme. Tre kernel dedicati in `fa_gfx906.py` (`SORGENTE_*_256`),
stessa interfaccia:

- **avanti**: 64 query ferme (Q intera in LDS, 33,8 KB), 32 chiavi che scorrono; K e poi V^T
  nello stesso spazio. V si legge nei registri prima di Q·K e si scrive in LDS dopo il softmax,
  così la sua latenza sta sotto il calcolo. LDS 55,8 KB.
- **dK/dV** (32 chiavi ferme, 64 query che scorrono) e **dQ** (64 query ferme, 64 chiavi che
  scorrono): la fase Q·K / dO·V scorre la dimensione d a **pezzi di 64 colonne**, con tutti e
  quattro gli operandi in LDS a pezzi (anche il lato "fermo" si rilegge a ogni blocco, dalla L2).
  La fase di accumulo cambia disposizione: ogni onda tiene un gruppo di chiavi (dK/dV) o di query
  (dQ) e ogni corsia 4 colonne d, così P e dS si leggono in broadcast e le coppie lungo
  query/chiavi si compongono da due letture b64 con `v_perm_b32` (a D=128 erano quattro letture a
  16 bit per coppia). Q e dO (dK/dV) o K (dQ) per l'accumulo stanno nello spazio dei pezzi.
  LDS 43,5 e 46,6 KB.
- **512 thread (8 onde, 2 per SIMD) invece di 256: 1,26-1,38x su tutti e tre**, risultati identici
  bit per bit (`prova_nt.py`). A 256 thread c'era una sola onda per SIMD: il limite era la latenza,
  non la LDS (che a 512 thread lavora di più per FLOP). Il tetto di 128 VGPR faceva sversare dK/dV
  e dQ (10-11 istruzioni) finché Q·K e dO·V si calcolavano insieme: separati in due passate sul
  pezzo (`tessera<>`), zero sversamenti. `imposta_256(fa_dq=256, ...)` riporta un kernel a 256.
- causale: avanti e dQ lanciano per primi i blocchi di query con più chiavi (fino a +6%,
  `prova_ordine.py`).

**Registri** (`banco_fa.py registri`): avanti 109, dK/dV 126, dQ 122 VGPR, **zero sversamenti**.

**GQA, in tutti e sei i kernel** (D=64/128/256): k e v `[B, H_kv, S_k, D]`, la testa di query h
legge la testa h // (H/H_kv). dK/dV: un workgroup per blocco di chiavi di una testa di K/V scorre le
G teste di query del gruppo e somma dentro i registri (nessuna atomica, nessuna copia). Firma dei
kernel con un `int G` dopo `H`.

**Correttezza 33/33** (`banco_fa.py correttezza`): i 12 casi di prima a D=64/128, gli stessi 12 a
D=256, e 3 GQA per ogni D (H8/2 causale, MQA H4/1 con dropout 0,2 e stride, H16/4 causale con
stride come Qwen). Errore assoluto contro fp32 della fa ≤ quello di math fp16 in tutte le righe.
⚠️ Il massimo di un singolo seme è rumoroso: con altri dati casuali una riga su ~10 scavalca di poco
(es. dk 2,3e-3 contro 1,2e-3, dropout 0,5), anche a D=128. Su 8 semi (`prova_errore.py`) l'errore
quadratico della fa è 0,5-0,65 volte quello di math in ogni caso, e il massimo sugli 8 semi è
sempre sotto: è P in fp16 contro dP e P arrotondati a fp16 da math.

**Tempi D=256 (B1 H16, `banco_fa.py prestazioni 256`, GPU sana, 20 ott):**

| forma | math avanti | fa avanti | math a+i | fa a+i | avanti | a+i |
|---|---:|---:|---:|---:|---:|---:|
| S256 causale | 0,81 | 0,34 | 1,91 | 1,29 | 2,38x | 1,48x |
| S1024 | 2,97 | 2,54 | 10,97 | 9,52 | 1,17x | 1,15x |
| S1024 causale | 3,29 | 1,53 | 11,28 | 5,94 | 2,15x | 1,90x |
| S2048 causale | 12,27 | 4,93 | 29,11 | 18,86 | 2,49x | 1,54x |
| S4096 | 40,10 | 35,54 | 102,88 | 132,79 | 1,13x | **0,77x** |
| S4096 causale | 44,21 | 17,13 | 106,39 | 67,23 | 2,58x | 1,58x |

Kernel separati a S4096 (`diag_256.py`/`prova_nt.py`, TFLOPS contando il ricalcolo di P e dP):
avanti 7,7-8,1, dK/dV 9,3, dQ 10,5-11,1 (a D=128, 256 thread: 7,3-7,9 / 6,0 / 7,7).

⚠️ **Non causale lungo, indietro sotto math**: a D=256 math passa più tempo nei GEMM di rocBLAS
(11,6 TFLOPS) e meno nel softmax, e il nostro indietro fa 14·S²·D FLOP (Q·K e dO·V ricalcolati in
entrambi i kernel) contro i 10 di math. Il caso di Qwen è causale.

**GQA, forma di Qwen (H16/4, causale, `banco_fa.py prestazioni_gqa`)**: math e "fa rip" con K/V
ripetute da `repeat_interleave`, "fa gqa" senza.

| forma | math avanti | fa rip | fa gqa | math a+i | fa rip | fa gqa | avanti | a+i |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1024 | 3,40 | 1,65 | 1,47 | 11,69 | 6,32 | 6,43 | 2,31x | 1,82x |
| S2048 | 12,48 | 5,20 | 4,84 | 30,41 | 19,48 | 19,15 | 2,58x | 1,59x |
| S4096 | 44,65 | 17,43 | 17,01 | 108,67 | 68,42 | 68,20 | 2,62x | 1,59x |

Il GQA nativo costa come ripetere (a S1024 dK/dV ha un quarto dei workgroup: 128 per 60 CU) ma
non alloca K/V ripetute né i loro gradienti.

**Memoria** (`memoria_256.py`, picco in più di avanti+indietro causale, D=256):

| forma | math | fa |
|---|---:|---:|
| S1024 H16 | 312 MB | 56 MB |
| S4096 H16 | 4.320 MB | 224 MB |
| S4096 H16/4 | 4.320 MB | 224 MB |
| S8192 H16/4 | 16.832 MB | 448 MB |

### Prossimi passi (20 ott)
1. **512 thread anche a D=64/128**: oggi 141-237 VGPR, un'onda per SIMD; a D=256 il passaggio a
   due onde ha dato 1,26-1,38x senza cambiare i risultati.
2. Indietro D=256 non causale: sotto math da S≈2048 in su (vedi sopra).
3. GQA a S corte: dK/dV con un workgroup per testa di K/V lascia CU ferme (128 workgroup a S1024).

## (storico) Prossimi passi del 17 ottobre

1. **Dividere ogni riga di query su due corsie**: ogni corsia tiene metà di Q (32
   coppie fp16 per D=128) e metà dell'accumulatore (64 fp32), e il prodotto scalare si
   chiude con uno scambio fra corsie vicine (DPP / `__shfl_xor`). Metà dei registri,
   niente sversamenti, due onde per SIMD.
2. **Misurare a macchina tranquilla.** Il 17 ott il percorso standard, sulla STESSA
   forma, oscillava da 22 a 62 ms: con quel rumore le differenze fra varianti non si
   vedono. Confronti sempre intercalati e a mediana.
3. **Il passo all'indietro.** Serve per addestrare (il caso d'uso della ruota è LoRA su
   Qwen3.5). È circa il doppio del lavoro dell'avanti: ricalcola P blocco per blocco e
   accumula dQ, dK, dV.
4. **Integrazione in PyTorch**: spetta all'agente della ruota, collegando i kernel a
   `scaled_dot_product_attention` e verificandoli contro il percorso attuale.

Da valutare insieme: l'avanti da solo serve già all'**inferenza** con contesti lunghi,
dove il guadagno di memoria vale anche senza guadagno di tempo.

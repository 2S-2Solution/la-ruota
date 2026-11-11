# Gated DeltaNet per gfx906: stato al 20 ottobre 2026

2S. Kernel HIP fusi, compilati a runtime con hipRTC come la flash attention
(`..\flash_gfx906\fa_gfx906.py`), per il passo «chunked gated delta rule» dell'attenzione
lineare di Qwen3.5, avanti e indietro (Qwen3-Next e Qwen3.5-MoE usano la stessa funzione, non
provati). Modulo autonomo: non tocca la ruota,
gli shim o ZLUDA. Si aggancia al modello con un monkeypatch nel solo processo.

## Perché

Il profilo del passo LoRA sul 4B (`diag_gemm\profila_lora.py`, lotto 1 x 256) dava GEMM 34% e
poi `copy_` 25% in ~24 mila chiamate, `sum` 10%, `mul` 7%, `fill_` 7%: è
`torch_chunk_gated_delta_rule` di transformers, la ricaduta in torch puro quando mancano i kernel
Triton di flash-linear-attention. Ogni blocco di 64 token è una sequenza di operazioni piccole,
più un ciclo di 63 righe per l'inversa triangolare, e l'autograd registra tutto (`CopySlices`).
24 strati su 32 del 4B sono così.

## Cosa c'è

| file | cosa |
|---|---|
| `gdn_gfx906.py` | il modulo: `chunk_gated_delta_rule(...)` (stessa firma di transformers), `aggancia()`, e i nuclei `avanti` / `indietro` sulle forme interne |
| `banco_gdn.py` | `correttezza` (11 casi contro transformers fp32 e contro una sua copia in fp64) e `prestazioni` |
| `banco_strato.py` | conv causale, GDN impacchettato con GQA e strato `Qwen3_5GatedDeltaNet` intero: `correttezza` (7 casi) e `prestazioni S` |
| `diag_strato.py` | operazioni GPU di uno strato coi pesi congelati (`funzione` o `strato`), col profiler |
| `ab_lora_gdn.py` | A/B sul passo LoRA vero, stesso montaggio di `diag_gemm\ab_lora.py`, non incluso (`torch` o `kernel`) |
| `profila_lora_gdn.py` | profilo del passo col kernel agganciato (`torch` come argomento per il percorso puro) |
| `diag_grad_modello.py` | gradienti LoRA del 4B: torch/torch, kernel/kernel, torch/kernel, torch con l2norm fp32 |
| `diag_tempi.py` | tempo di ogni kernel (eventi GPU); accetta opzioni di compilazione (`-DKL=16` ...) |
| `diag_contorno.py` | tempo GPU di una chiamata col profiler: kernel contro operazioni torch intorno |
| `note_kernel.py` | VGPR, LDS e scratch di ogni kernel dal code object |
| `gdn_gfx906.py.bak_v1_corretto` | la prima versione verificata (4 kernel, contorno in torch): più semplice da leggere |

## Matematica e decomposizione

Per testa, blocco di C=64 righe, G = somma cumulata di g dentro il blocco:

    Γ_ij = exp(G_i - G_j) (i >= j),  γ = exp(G),  γC = exp(G_63),  γd = γC / γ
    A = strettamente_inferiore((β⊙K) Kᵀ ⊙ Γ),   T = (I + A)⁻¹     (il ciclo di 63 righe)
    U = T (β⊙V),   W = T (βγ⊙K),   P = (Q Kᵀ ⊙ Γ) inferiore con diagonale
    Vn = U - W S;   O = (γ⊙Q) S + P Vn;   S ← γC S + (γd⊙K)ᵀ Vn

**Tutto in fp32**, come il riferimento. I FLOP sono pochi (~1,4 GFLOP a strato a S=256): il
costo era il numero di lanci, non l'aritmetica, quindi `v_dot2_f32_f16` non serviva e fp32 evita
ogni discussione sulla precisione. Sette kernel da 256 thread:

| kernel | griglia | cosa |
|---|---|---|
| `gdn_ingresso` | un'onda per riga | l2norm di q e k **in fp32**, scala, `[B,S,H,D]` a passo qualunque → `[B,H,Sp,D]` fp32, padding a 64 |
| `gdn_prep` | (blocco, testa) | G, scale, A, P, T (sostituzione a registri, una colonna per corsia), U, W |
| `gdn_ric` | (fetta di 32 colonne di Dv, testa) | la ricorrenza sugli stati, sequenziale sui blocchi; scrive o in `[B,S,H,Dv]` fp16 |
| `gdn_converti` | un'onda per riga | dO → fp32 interno |
| `gdn_ric_ind` | (fetta di Dv, testa) | la ricorrenza all'indietro: dS e dVn |
| `gdn_locale` | (blocco, testa) | dq, dk, dv, dβ, dg di ogni blocco (le contrazioni su Dv intera) |
| `gdn_uscita_ind` | un'onda per riga | indietro della l2norm, gradienti nel layout e dtype degli ingressi |

Le colonne di Dv dello stato non si parlano: per questo la ricorrenza si divide in 4 fette e i
workgroup sono 128 invece di 32. Le quantità che contraggono su Dv (dO Sᵀ, Vn dS'ᵀ, dO Vnᵀ ...) le
fa `gdn_locale`, che ha Dv intera: così non servono atomiche globali (gfx906 non ne ha in fp32).
L'avanti salva per l'indietro gli stati all'ingresso di ogni blocco (`[BH, NC, 128, 128]`, 8 MB a
strato a S=256) e Vn; l'indietro salva dS dopo ogni blocco e dVn.

## Esito

### Correttezza: 11/11 (`banco_gdn.py correttezza`)

Errore massimo relativo al massimo, contro la copia fp64 del riferimento, su uscita, stato finale
e i gradienti di q, k, v, g, β (e dello stato iniziale), **tre indietro di fila** per caso, ognuno
con avanti nuovo e dO diverso; più tre indietro sullo **stesso grafo** (`retain_graph`):
gradienti identici bit a bit.

| caso | uscita kernel / rif32 | gradienti, il peggiore kernel / rif32 |
|---|---|---|
| B1 S256 H32 D128 fp32, decadimento forte | 2,5e-6 / 3,6e-6 | dv 2,7e-6 / 2,9e-6 |
| S200, S1000, S64, B2 S130 decadimento debole, D64 | dello stesso ordine | dello stesso ordine |
| stato iniziale e finale, B2 S150 | 2,1e-6 / 2,0e-6 | ds0 4,5e-7 / 4,0e-7 |
| ingressi fp16, S256 H32 | **2,2e-4 / 8,2e-4** | dk **4,0e-4 / 1,2e-3** |
| layout del modello (v vista di `mixed_qkv`, q/k da `repeat_interleave`), fp16 | 4,0e-4 / 6,3e-4 | dq 4,0e-4 / 1,25e-3 |

Con ingressi fp16 il kernel è 2-4x **più vicino** a fp64 del riferimento: il riferimento fa la
l2norm nel dtype d'ingresso (fp16) e solo dopo passa a fp32; il kernel la fa in fp32.

### Tempi della funzione (`banco_gdn.py prestazioni`, H32 D128, fp16, mediana)

| forma | torch avanti | kernel avanti | torch a+i | kernel a+i |
|---|---:|---:|---:|---:|
| B1 S256 (il 4B in LoRA) | 7,05 ms | **0,94 ms** (7,5x) | 23,5 ms | **2,62 ms** (9,0x) |
| B1 S1024 | 10,98 ms | 3,15 ms (3,5x) | 61,6 ms | 8,63 ms (7,1x) |
| B1 S4096 | — | 13,5 ms | — | 35,3 ms |

Tempo GPU per kernel a S256 (`diag_tempi.py`): ingresso+prep+ric ~0,64 ms, ric_ind 0,37,
locale 0,76; il contorno fuso costa ~0,1 ms in tutto (era 1,74 ms in operazioni torch).

### A/B sul passo LoRA vero (`ab_lora_gdn.py`, 10 passi, due giri intercalati, seme fisso)

| | passo mediano | perdite (passi 0, 4, 9) | picco memoria |
|---|---:|---|---:|
| torch puro, giro 1 | 1,347 s | 14,3594  13,8604  13,0169 | 8,72 GB |
| kernel, giro 1 | **0,841 s** | 14,3592  13,8604  13,0166 | 8,72 GB |
| torch puro, giro 2 | 1,326 s | 14,3594  13,8603  13,0167 | 8,72 GB |
| kernel, giro 2 | **0,853 s** | 14,3592  13,8606  13,0166 | 8,72 GB |

**−37% sul passo.** Le perdite coincidono alla quarta cifra in tutti i 10 passi; la differenza
kernel/torch è dello stesso ordine di quella fra due giri di torch.

**Gradienti del modello** (`diag_grad_modello.py`, un passo, B dei LoRA non nulli): torch contro
se stesso 6,4e-4 (il modello non è deterministico), kernel contro torch 1,7e-3, coseno 0,999998.
La parte in più non è del kernel: **cambiare solo la precisione della l2norm nel percorso torch**
(fp32 invece di fp16) sposta i gradienti di 1,66e-3, quanto il kernel. È la scala di qualunque
perturbazione al livello dell'arrotondamento fp16 nell'uscita dell'attenzione lineare,
amplificata da 24 strati.

**Dove va adesso il tempo** (profilo col kernel, `profila_lora_gdn.py`): tempo GPU 960 ms;
GEMM 688 ms (72%, vicine al tetto per queste forme magre, vedi §7 delle risposte del 17 ott),
`copy_` 71 ms (in 2.693 chiamate, non più 24 mila), Gated DeltaNet 63 ms (6,6%).

## 20 ottobre (sera): lo strato senza permutazioni e la conv causale fusa

Richiesta di rocm-marconi dal profilo a 512 token (`diag_gemm\profila_lora.py --gdn --copie`):
`copy_` era il 12,5% del tempo GPU, quasi tutto trasposte che torch fa a ~30 GB/s. Nel modeling
corrispondono a:

| copia | dove, in `Qwen3_5GatedDeltaNet.forward` |
|---|---|
| `[1, 8192, 512]` x96, 51,7 ms | `mixed_qkv.transpose(1, 2)` resa contigua per `F.conv1d` (MIOpen), e il ritorno nell'indietro |
| `[1, 512, 16, 2, 128]` x96, 24,9 ms | `repeat_interleave` di q e k da 16 a 32 teste |
| `[1, 512, 32, 128]` x48, 12,5 ms | `value.reshape`: dall'uscita trasposta della conv non può essere una vista |

**Cosa c'è adesso** (`aggancia()` lo fa di default; `GDN_STRATO=0` torna alla sola funzione):
- `conv_causale(x, w, bias, silu)`: conv1d causale depthwise + SiLU **su `[B, S, C]`**, un thread per
  canale e 16 istanti (letture coalescenti, finestra a registri), conti in fp32; l'indietro ricalcola
  la pre-attivazione e dà dx, e dw/dbias (parziali per blocco sommati con una `sum`) solo se servono.
- `gdn_impacchettato(qkv, g, beta, Hk, H, Dk, Dv)`: il GDN legge q, k, v come colonne dell'uscita della
  conv, con **q e k a 16 teste** (la testa h legge la h/2, come `repeat_interleave`), e restituisce un
  solo gradiente `[B, S, C]` (somma delle due teste di valore nel kernel `gdn_uscita_ind`).
- `_forward_strato`: il forward di `Qwen3_5GatedDeltaNet` senza trasposte, `reshape` di copia né
  `repeat_interleave`. Con cache (decodifica), `cu_seq_lens_q` o attivazione diversa da SiLU ricade
  sul forward originale.

**Correttezza: 7/7** (`banco_strato.py correttezza`, tre indietro di fila per caso, verità fp64):
conv (fp16 S512 C8192 K4; fp32 con bias B2; fp16 K3 con bias), GDN impacchettato con GQA (fp16 Hk16
H32; fp32 B2), e lo **strato intero alle dimensioni del 4B** (fp16 S256; fp32 B2 S200) con i gradienti
dell'ingresso e di tutti i pesi (`in_proj_*`, `conv1d.weight`, `A_log`, `dt_bias`, `norm`,
`out_proj`). Conv fp16: errore 2,4e-4 contro 4,8e-4 del percorso MIOpen. `banco_gdn.py` resta 11/11.

**Tempi.** Uno strato coi pesi congelati, 512 token (`diag_strato.py`): tempo GPU per avanti+indietro
14,62 → 11,45 ms; la conv costa 0,07 + 0,15 ms (prima MIOpen + SiLU + le trasposte, ~2,8 ms).
A/B col montaggio di `diag_gemm\ab_lora.py --gdn` (Tensile instradato, 8 passi, due giri
intercalati per modo):

| token | solo funzione | funzione + strato | |
|---|---:|---:|---:|
| 512 | 448 / 448 token/s (1,143 s) | **479 / 478 token/s** (1,070 s) | +7% |
| 1024 | 465 / 464 token/s (2,202 s) | **545 / 545 token/s** (1,880 s) | +17% |

Picco di memoria invariato (9,5 e 11,0 GB). Le perdite al passo 0 coincidono (14,1627/14,1628,
14,0001/13,9999); dopo divergono fra giri anche a parità di modo, perché `ab_lora.py` non semina
l'inizializzazione dei LoRA.

Resta nello strato: la `RMSNormGated` in torch (conversioni fp32 e ritorno, `mean`, `mul`: ~0,8 ms a
strato a 512 token) e le GEMM. La norma con gate si può fondere in un kernel avanti/indietro.

## Lezioni

- **Occupazione, non aritmetica.** La prima versione corretta girava a 1 workgroup per CU (150-254
  VGPR, 33-50 KB di LDS): 128 workgroup in 3 tornate sui 60 CU, ciascuno fermo sulla latenza delle
  tessere. Con **84 VGPR e ≤ 21 KB di LDS** stanno 3 workgroup per CU e i 128 girano in una
  tornata: ricorrenze 0,87 → 0,41 ms, prep 0,56 → 0,20, locale 1,44 → 0,76. 128 è il caso
  scomodo: 2 per CU fanno 120 posti, quindi servono 3.
- **`__attribute__((amdgpu_waves_per_eu(N, N)))` funziona con hipRTC**, a differenza del secondo
  parametro di `__launch_bounds__` (vedi STATO della flash). A 3 onde il compilatore taglia a 84
  VGPR con pochi byte di scratch (44-288 B), ed è comunque il punto migliore; a 4 onde (64 VGPR)
  locale peggiora (0,88 ms).
- **Le tessere di k piccole aiutano** quando liberano LDS per un workgroup in più: KL=8 in
  locale, KP=16 in prep. Lo srotolamento del ciclo interno non conta.
- **Il contorno costava più dei kernel**: l2norm, trasposte, conversioni, padding e i loro
  indietro erano 1,74 ms di GPU a chiamata contro 1,75 ms dei kernel. Fusi in tre kernel piccoli.
- **Le `atomicAdd` in LDS rendono i gradienti non deterministici** (l'ordine delle somme cambia):
  il banco «tre indietro sullo stesso grafo» le ha prese su dg e dβ. Sostituite con slot a
  scrittore unico per fase, sommati in ordine fisso.
- **Le note del code object vanno lette per voce**: i campi di un kernel stanno prima e dopo
  `.name`, e spezzando su `.name` la LDS finiva attribuita al kernel accanto. `note_kernel.py`
  spezza su `- .args:`.
- Il riferimento giusto per i gradienti è una copia **fp64** della funzione di transformers
  (sostituendo `torch.float32` con `torch.float64`): il confronto diretto con rif32 non dice chi
  dei due sbaglia.

## Limiti e prossimi passi

- Con `aggancia()` lo strato ricade sul forward originale con cache, `cu_seq_lens_q` o attivazione
  non SiLU; la conv fusa e il GDN impacchettato valgono solo per l'addestramento/prefill senza cache.
- Non coperti: `cu_seqlens` (sequenze impacchettate: assert), blocchi diversi da 64, Dk/Dv non
  multipli di 64 o sopra 128, dtype diversi da fp16/fp32. Il percorso di **decodifica a un token**
  (`torch_recurrent_gated_delta_rule`, inferenza con cache) resta in torch.
- La ricorrenza è ancora legata alla latenza (12 tessere sequenziali per blocco). Riscrivibile come
  S ← M S + B con M = γC I − (γd⊙K)ᵀ W e B = (γd⊙K)ᵀ U calcolate in parallelo per blocco (e
  l'indietro come dS ← Mᵀ dS + Eᵀ dO): 4 tessere per blocco invece di 12. Stimato a S=256: −0,2 ms
  a strato, ~5 ms a passo. Non fatto: il guadagno è piccolo rispetto alle GEMM.
- Per il passo LoRA la leva restante sono le GEMM (72%) e le `copy_` dei LoRA fp32 (7%), non più
  l'attenzione lineare.

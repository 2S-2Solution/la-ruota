# LA RUOTA — guida

**PyTorch 2.5 ROCm nativo su Windows · Radeon VII (gfx906) · macchina di prova**
**Stato al 20 ottobre 2026, aggiornata l'11 novembre.** Niente ZLUDA, niente traduzione PTX: i
kernel sono compilati dai sorgenti.

> I percorsi `C:\LaRuota_workspace\...` sono quelli della **macchina di costruzione**
> (`venv_build` è l'ambiente in cui è compilata). Con il pacchetto della pagina Releases
> l'interprete è `%LOCALAPPDATA%\2S\la-ruota\venv\Scripts\python.exe` (o `python.cmd` nella
> stessa cartella), la cache di MIOpen è in `%LOCALAPPDATA%\2S\la-ruota\miopen` e i
> vincoli in `vincoli.txt` del pacchetto. Molti banchi e script citati qui non sono nel
> repository: quelli inclusi sono in `la-ruota/workspace/`.

**Novità del 20 ottobre, in breve** (per chi usava già la ruota):
- **MIOpen ricompilata** con le correzioni di miopen-gfx906: tre difetti silenziosi delle
  convoluzioni sono corretti alla radice. La ruota ha una **cache MIOpen nuova**: la prima
  volta ogni forma si ricompila, quindi **i primi passi sono lenti**;
- **le RNN a più strati (LSTM, GRU) passano da MIOpen**: 2,86x più veloci, e giuste;
- **la LSTM con ≥ 32 passi** e **la conv 1×1 con stride al cambio di lotto** davano numeri
  sbagliati senza errori: corrette;
- copie di tensori trasposti fino a 194x più veloci; flash attention e kernel per Qwen3.5
  (A6).
- Chi aveva collaudato reti sulla GPU prima del 20 ottobre **rifaccia il collaudo** (A2.4).
- **`torch.linalg.eigh` / `eigvalsh` sulla GPU sbagliavano in silenzio da n=64 in su**
  (hipSOLVER): corrette dalla VEGA-PATCH 78, che passa eigh e svd a rocSOLVER. Chi ha usato
  eigh sulla GPU (PCA, whitening, covarianze) con matrici ≥ 64 **rifaccia quei calcoli**.
- **`softmax` / `log_softmax` in fp64 sulla GPU sbagliavano in silenzio** (errore 0,2-0,9)
  con l'ultima dimensione dispari fra 513 e 1021, avanti e indietro: corrette dalla VEGA-PATCH
  80/80b (trovato con rocm-marconi). Chi collauda in fp64 sulla GPU rifaccia quei confronti.
- **`eigh` e `svd` di tensori GPU si calcolano con MKL sulla CPU** (VEGA-PATCH 81): rocSOLVER su
  gfx906 era da 20 a 114 volte più lento (svd 1000×96 da 209 a 3 ms).
- **`torch.optim.Adam/AdamW/SGD(fused=True)`** mandava in crash il processo: corretto il 22 ott
  (VEGA-PATCH 83 e 84, A3). `foreach=True` resta il consigliato: il fuso non rende sulle reti
  piccole.

La guida ha due parti:

- **Parte A — per chi la usa** (un utente, addestramenti Qwen, qualunque script):
  come lanciarla, le regole, cosa funziona, cosa fare quando qualcosa non va.
- **Parte B — per chi la mantiene**: stack runtime, difetti noti, ricompilazione,
  diagnostica, banchi, cronologia delle patch.

---

# PARTE A — PER CHI LA USA

## A1. In un minuto

L'interprete della ruota:

```
:: installata dal pacchetto
%LOCALAPPDATA%\2S\la-ruota\venv\Scripts\python.exe
:: sulla macchina di costruzione
C:\LaRuota_workspace\venv_build\Scripts\python.exe
```

Si usa come un PyTorch qualunque con `device="cuda"`. **Non serve impostare nessuna
variabile d'ambiente**: quelle che servono sono già dentro la build.

Prova che funziona:

```python
import torch
print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))
# atteso: 2.5.0+gita8d6afb True AMD Radeon VII
x = torch.randn(1024, 1024, device="cuda")
print((x @ x).sum().item())
```

⚠️ **Per riconoscere la GPU usare `torch.cuda.is_available()`, mai `torch.version.hip`.**
La ruota si presenta come CUDA («masquerading»): i tensori stanno su `cuda`, e
`torch.version.hip` vale `None`.

Cosa c'è:

| | |
|---|---|
| GPU | Radeon VII, 15,98 GB, fp32 e **fp16** (non bf16, vedi A3) |
| MIOpen (convoluzioni, RNN, normalizzazioni) | 3.5.2 **ricompilata il 20 ott** con le correzioni di miopen-gfx906; cache propria in `%LOCALAPPDATA%\2S\la-ruota\miopen` (VEGA-PATCH 85; prima `miopen_cache_ruota`) |
| CPU | Ryzen 9 5950X, 16 core; torch su CPU usa **MKL**: matmul 160–830 GFLOPS (a seconda del carico), sopra numpy |
| numpy | **2.2.6** (torch funziona anche con la 1.26) |
| pandas / scipy / pyarrow | 3.0.6 / 1.17.1 / 21.0.0 |
| transformers / peft / accelerate | 4.51.3 / 0.15.2 / 0.33.0 (Qwen3); per Qwen3.5 vedi A6 |
| assenti | torchvision, torchaudio, Pillow, scikit-learn, LightGBM, CatBoost |

## A2. Le regole

1. **Installare pacchetti solo con i vincoli:**

   ```
   C:\LaRuota_workspace\venv_build\Scripts\python.exe -m pip install -c C:\LaRuota_workspace\vincoli_ruota.txt <pacchetto>
   ```

   Senza vincoli, un pacchetto che chiede un altro torch fa **scaricare il torch
   ufficiale sopra la ruota**: provato il 17 ott, `pip install torchvision` avrebbe
   installato `torch-2.6.0`, che non vede la Radeon VII. Con i vincoli pip si ferma con un
   conflitto. Dopo ogni installazione **importare davvero** il pacchetto e fare
   un'operazione: pip garantisce i metadati, non il funzionamento.

2. **torchvision non si installa da pip.** Va compilato contro la ruota, e oggi non c'è.
   Chi lo importa solo di passaggio (come la catena `torchmetrics → pytorch_lightning`
   applicativi) usa uno stub.

3. **fp16, non bf16.** gfx906 non ha istruzioni bf16: la matmul bf16 non gira. Usare
   `torch.autocast("cuda", dtype=torch.float16)` con `GradScaler`.

4. **Una rete nuova va confrontata una volta con la CPU** prima di fidarsi della GPU:
   - sul **gradiente dei pesi**, non solo sull'uscita;
   - con **lotto maggiore di 1**, e **cambiando lotto** a metà (l'ultimo lotto corto di
     un'epoca: la conv 1×1 sbagliava proprio lì);
   - su **almeno tre passi all'indietro di fila, non uno**: la LSTM sbagliava solo dal
     secondo, e un collaudo da un passo la lasciava passare;
   - con forme **oltre le soglie** delle librerie (per le RNN: ≥ 32 passi di sequenza).

   MIOpen sceglie l'algoritmo per velocità, non per correttezza. I difetti noti sono
   corretti o esclusi (B2), e su 597 forme di convoluzione nessuna sbaglia; ma una forma
   mai vista resta una forma mai vista. **Dopo il 20 ottobre MIOpen e il percorso delle RNN
   a più strati sono cambiati: i collaudi fatti prima vanno rifatti.**

5. **Più stream funzionano, ma qui non fanno guadagnare tempo.** Su questo runtime il
   lavoro della GPU va sempre in fila: prefetch e copie «in parallelo» al calcolo non si
   sovrappongono. Non costruirci sopra aspettative di velocità.

6. **Durante una ricompilazione non usare la ruota**: il manutentore avvisa prima di
   lanciarne una. A fine build l'installazione sovrascrive le DLL, e se un processo le
   tiene aperte fallisce.
   Chi ne ha bisogno proprio allora usa la ruota di riserva:

   ```
   set PYTHONPATH=C:\LaRuota_workspace\ruota_vecchia
   C:\LaRuota_workspace\venv_build\Scripts\python.exe script.py
   ```

   **È una copia esatta della ruota in uso** (dal 20 ottobre: `riserva_ruota_2026_10_20`,
   con MIOpen nuova e tutte le correzioni), con il numpy dell'ambiente. Verificata il 20 ott
   sulla LSTM con ≥ 32 passi e sulla conv 1×1 al cambio di lotto: giusta. Il manutentore la
   ricopia dopo ogni ricompilazione verificata (B4), così resta sempre uguale a quella in uso.

7. **Non mettere a mano variabili `MIOPEN_*`, `HIP_*`, `HSA_*`**, né file
   `sitecustomize.py` in site-packages: le esclusioni di sicurezza sono già dentro
   `torch/__init__.py` (B2), insieme alla cache MIOpen propria della ruota. Una variabile
   impostata a mano al valore sbagliato riaccende un difetto senza alcun segnale.

## A3. Cosa funziona e cosa no

**Funziona, misurato il 20 ottobre** (configurazione definitiva, `regressione_completa.py`
14 su 14):

| area | |
|---|---|
| operazioni GPU contro CPU (riduzioni, elementwise, indicizzazione, ordinamenti, FFT, complessi, interi, immagini, perdite) | 98 su 98, più le 105 del censimento di Rocm |
| algebra lineare GPU: `solve`, `inv`, `det`, `qr`, `svd`, `eigh`, `eig`, `lu`, **`cholesky`**, **`lstsq`**, `pinv`, anche a lotti | 20 su 20 contro numpy; **13 su 13 a tutte le dimensioni da 16 a 512**, fp32/fp64, lotti (dal 20 ott: prima `eigh` sbagliava da n=64). `svd` ed `eigh` ripetibili bit a bit |
| algebra lineare CPU (MKL) | tutta, scarti ≤ 3e-12 contro numpy |
| convoluzioni 1D/2D/3D, stride, gruppi, depthwise, dilatazione, trasposte, fp16 | 597 forme su 597 con la MIOpen nuova, **senza esclusioni**; la conv 1×1 con stride al cambio di lotto è giusta (prima: scarto 3,1) |
| LSTM / GRU / RNN, 1–3 strati, bidirezionali, sequenze impacchettate | giuste, su tre passi all'indietro di fila, fino a 128 passi di sequenza e alle soglie di agosto (hidden 256, lotto 32). **Dal 20 ott quelle a più strati passano da MIOpen: 2,86x più veloci** (LSTM 2×256: 26 → 9 ms). La LSTM a uno strato con ≥ 32 passi dava gradienti a zero dal secondo indietro: **corretta dal 17 ott** |
| attenzione: `sdpa` (anche con dropout e maschera causale), `MultiheadAttention`, `TransformerEncoder` (anche in eval, percorso veloce acceso) | corrette |
| dropout, `GradScaler`, autocast fp16, AdamW e gli ottimizzatori `_foreach_` | corretti |
| più stream ed eventi, `record_stream`, copie pinned non bloccanti | corretti (ma senza guadagno, A2.5) |
| TorchScript con `torch.cuda` (stream, eventi, `synchronize`) | corretto |
| profiler con tempi GPU (`torch.autograd.profiler.profile(use_device="cuda")`) | funziona |
| `torch.distributed` | solo Gloo su CPU |

**Non funziona, e non si risolve nella ruota:**

| | perché | cosa fare |
|---|---|---|
| matmul **bf16** | gfx906 non ha le istruzioni | fp16 con `GradScaler` |
| flash attention **nel percorso predefinito** | c'è, ma si accende a mano (A6) | `ruota_flash.attiva()`; senza, `sdpa` usa il percorso standard: corretto, più memoria |
| `torch.optim.Adam/AdamW/SGD(fused=True)` | crash del processo (0xC0000005 all'indirizzo base di `torch_hip.dll`). **Causa trovata il 22 ott**: lo stesso difetto delle 20 operazioni del 29 ago. `Fused{Adam,AdamW,Sgd}Kernel.hip` non includono il proprio `ATen/ops/<op>_native.h`, quindi `_fused_*_kernel_cuda_` non sono esportate e `RegisterCUDA` salta a una voce d'import nulla. **VEGA-PATCH 83 installata il 22 ott** (torch_hip md5 13290B46): Adam/AdamW (anche amsgrad) fused ora funzionano, a 2,4e-7 / 4,8e-6 da foreach dopo 20 passi, **ma non rendono** (MLP rete di prova: 2,48 contro 2,31 ms a passo). SGD fused poi si bloccava (ciclo infinito: `auto i_start = threadIdx.x` copia un oggetto coordinata di HIP il cui `+=` non modifica nulla, `amd_hip_runtime.h:284`): **VEGA-PATCH 84** (`int64_t`), torch_hip md5 24EDD6E2. Ora **tutti e sei** passano; SGD fused contro foreach ≤ 9,5e-7 dopo 20 passi | `foreach=True` resta il consigliato (il fuso non rende sulle reti piccole) |
| `lstsq` con `driver` diverso da `gels` | su GPU c'è solo `gels`, come in PyTorch ufficiale | per matrici a rango non pieno: `driver="gelsd"` sulla CPU |
| GPU distribuita, RPC | su Windows non esistono RCCL né TensorPipe | una sola GPU |
| AOTInductor | PyTorch 2.5 non lo supporta su Windows | — |
| torchvision, oneDNN | non compilati | si aggiungono quando servono (B8) |

**Prestazioni orientative** (macchina scarica; a macchina carica il GEMM può scendere a
un terzo, quindi confrontare solo numeri presi nelle stesse condizioni):

| | |
|---|---|
| GEMM fp16 4096 | 9–11 TFLOPS |
| banda elementwise | 496 GB/s (la banda piena della scheda) |
| costo di un lancio | 8,7 µs (ZLUDA: 46) |
| passo di training, transformer 3,67M con AdamW | 69 ms (ZLUDA: 343, cioè 5x) |
| matmul CPU fp32 4096 | 160–235 GFLOPS a macchina carica (numpy, stesso istante: 88–110); **832** a macchina scarica (20 ott) |
| LSTM 2 strati 256, avanti+indietro | 9,1 ms (dal 20 ott in MIOpen; prima 26) |
| copia di un tensore trasposto (`x.t().contiguous()`, ≥ 1 MB) | 280–640 GB/s in fp16 (dal 20 ott; prima 3–45) |
| attenzione B2 H16 S2048 D128 causale, avanti+indietro | 24,9 ms / 146 MB con `ruota_flash` (senza: 48,6 ms / 2.162 MB) |

⚠️ Una `.item()` o una stampa di un tensore GPU dentro il ciclo sincronizza la CPU con la
GPU a ogni passo: in generazione dimezza la velocità. Leggere i valori ogni N passi.

## A4. Quando qualcosa non va

| sintomo | causa probabile | cosa fare |
|---|---|---|
| `torch.cuda.is_available()` è `False` | interprete sbagliato (il `.venv` di un progetto invece della ruota) | lanciare con `C:\LaRuota_workspace\venv_build\Scripts\python.exe` |
| `import torch` fallisce, cita `shm.dll` o `libiomp5md.dll` | manca una DLL in `torch\lib` (installazione rifatta) | al manutentore: B1 |
| `torch.__version__` non è `2.5.0+gita8d6afb` | pip ha sostituito torch | al manutentore; d'ora in poi pip **solo con i vincoli** (A2.1) |
| numeri diversi dalla CPU su una convoluzione nuova | forma che sceglie un algoritmo MIOpen difettoso | confronto di A2.4, poi al manutentore con la forma esatta |
| errore di memoria con molta memoria libera, alla prima conv di una forma | MIOpen chiede spazi di lavoro grandi mentre cerca l'algoritmo | dal 20 ott la ricerca ripiega da sola su uno spazio più piccolo (VEGA-PATCH 73); se capita ancora, al manutentore. Non svuotare la cache di MIOpen |
| un'operazione dà *"Could not run … with arguments from the 'HIP' backend"* | difetto di masquerading rimasto nella build | al manutentore con il nome dell'operazione: si ripara (B6) |
| *"requires compiling PyTorch with MAGMA / cuSOLVER"* | percorso che upstream spegne su ROCm | al manutentore: finora si è sempre potuto reindirizzare su rocSOLVER |
| la prima chiamata a una conv, a una RNN o a un kernel è lenta (secondi, a volte minuti a macchina carica) | compilazione e ricerca dell'algoritmo, una volta per forma. Dal 20 ott la cache MIOpen della ruota è **nuova**: tutte le forme si ricompilano una prima volta | normale; dalla seconda volta, anche in un altro processo, è veloce. Per un tempo di passo vero, misurare dal terzo passo |
| *"Attempting to use hipBLASLt on an unsupported architecture"* | avviso, non errore | ignorarlo: PyTorch passa da solo a hipBLAS |
| `TransformerEncoder` **in eval**, `activation="gelu"`: uscita GPU diversa dalla CPU di ~1e-3 | il percorso veloce usa la GELU **approssimata `tanh`**: è PyTorch (`Blas.cpp`, ramo senza hipBLASLt, imita l'epilogo di cuBLASLt), uguale su NVIDIA. L'addestramento non è toccato | se serve la GELU esatta in inferenza: `torch.backends.mha.set_fastpath_enabled(False)` |
| gradiente del bias della `BatchNorm` da 2 a 9 volte meno preciso della CPU (assoluto ~1e-5) | ordine della somma dentro l'indietro della BatchNorm | niente: non è un errore |
| due corse identiche sulla GPU differiscono di poco (~1e-6 relativo; fino a ~1e-4 dopo passaggi iterativi come `svd_lowrank`) | PyTorch su ROCm accende le **atomiche di hipBLAS** (`CublasHandlePool.cpp`): alcuni GEMM con K grande sommano in ordine variabile. È il comportamento previsto da upstream, non un difetto | se serve la ripetibilità esatta: `torch.use_deterministic_algorithms(True)` all'inizio (le spegne; verificato: scarto 0,0) |
| gradiente dei pesi di una conv 3×3 con stride 2 un po' diverso da un processo all'altro (3–6e-6 relativo invece di 4e-7) | ogni processo rifà la ricerca a tempo di MIOpen (`MIOPEN_FIND_MODE=1`, variabile utente di il responsabile del progetto) e a volte vince una variante **Winograd** a tessera grande (`ConvWinograd3x3MultipassWrW<3-4>`, `<3-5>`, `<3-6>`), meno precisa per costruzione | niente: è l'arrotondamento di Winograd, come su NVIDIA. Banco: `diag_wrw3x3\solutori_passo2.py` |

Nel dubbio: un esempio minimo che riproduce il problema, confrontato con la CPU, e lo si
passa al manutentore. Chi usa la ruota non modifica la ruota.

## A6. Qwen3.5 e LoRA

`transformers 4.51.3` non conosce Qwen3.5. `transformers 5.15.0` sta in un albero
separato, per non toccare l'ambiente che regge Qwen3:

```python
import sys
sys.path.insert(0, r"%USERPROFILE%\Documents\2SAI\Memoria\working\prova_tf_nuovo")
```

L'attenzione lineare (Gated DeltaNet, 24 strati su 32) gira in **PyTorch puro**, senza
Triton né `causal-conv1d`. I processori d'immagine di transformers vogliono torchvision:
per addestrare su **immagini** va prima compilato (B8); sul testo non serve.

### L'assetto LoRA che entra nella scheda

In fp32 il 4B occupa 15,78 GB su 15,98: non resta memoria per i gradienti.

1. carica con `dtype=torch.float16` → **8,04 GB**
2. `requires_grad_(False)` su **tutto**, *poi* aggiungi gli adattatori. Al contrario,
   restano allenabili embedding e norme in fp16 e lo scaler rifiuta i loro gradienti
3. adattatori in **fp32**, calcolati dentro `autocast(enabled=False)`
4. `gradient_checkpointing_enable()`
5. `autocast(fp16)` + `GradScaler(init_scale=128)`

⚠️ **Non `model.half()`**: con tutti i parametri in fp16 l'attenzione lineare dà NaN.
⚠️ Con la scala predefinita (65536) lo scaler salta i primi passi e sembra fermo.

| lotto × token | picco GB | s/passo | token/s |
|---|---|---|---|
| 1 × 512 | 8,74 | 3,68 | 139 |
| **2 × 512** | 9,31 | 5,45 | **188** |
| 1 × 1024 | 9,52 | 6,13 | 167 |
| 1 × 2048 | 11,21 | 23,14 | 88 |
| 1 × 4096 | 15,98 | 42,92 | 95 |

**Allargare il lotto, non la sequenza**: l'attenzione lineare scorre la sequenza passo
per passo, quindi 2048 token costano 13 s a 4×512 e 23 s a 1×2048.

### Il modo più semplice: `ruota_acceleratori` (dal 20 ottobre)

Una riga accende tutto quello che la ruota ha per Qwen3.5, dopo l'import di transformers e
prima di caricare il modello:

```python
sys.path.insert(0, r"C:\LaRuota_workspace\ruota_acceleratori")
import ruota_acceleratori
ruota_acceleratori.attiva()     # stampa cosa ha acceso
```

Accende il kernel **Gated DeltaNet** (attenzione lineare, con la conv causale fusa) e la
**flash attention** (strati ad attenzione piena). Si spengono dall'ambiente:
`RUOTA_ACCELERATORI=0` (tutti), `RUOTA_GDN=0`, `RUOTA_FLASH=0`. Con transformers 4.51,
senza Qwen3.5, il Gated DeltaNet viene saltato da solo. **È già agganciato in
`Memoria\working\qwen35\train_qwen35.py`** (copia di prima: `….bak_pre_acceleratori_20ott`).

Passo LoRA del 4B, 1024 token, GPU libera, 20 ott (`diag_gemm\ab_lora.py`):

| | token/s |
|---|---:|
| 17 ott, percorso puro | 182 |
| Gated DeltaNet con conv fusa + Tensile instradato | 546 |
| **+ flash attention** | **562** |

Perdite uguali entro il fp16, memoria invariata (11,0 GB). Il Gated DeltaNet fuso è giusto
**anche con il padding** (lotti di lunghezze diverse con `attention_mask`, come in
`train_qwen35.py`): uscita e gradienti a 1e-03 dall'originale
(`ruota_acceleratori\prova_gdn_padding.py`).

⚠️ **Con il padding la flash rende poco**: se il lotto ha lunghezze diverse, transformers
passa a `sdpa` una maschera e la chiamata va al percorso originale (giusto, più lento).
`ruota_acceleratori.contatori_flash()` dice quante chiamate sono andate alla flash. Per
averla sempre: lotti di lunghezza uguale, o un esempio per lotto con accumulo dei gradienti.

**Dal 20 ottobre sera `attiva()` accende anche** norme fuse, perdita fusa e GEMM gfx906, e
c'è `aggancia_lora_peft()` per il ramo LoRA di peft. Va chiamato **dopo** aver sistemato
`LoraLinear.forward`. Interruttori: `RUOTA_NORME`, `RUOTA_PERDITA`, `RUOTA_GEMM`,
`RUOTA_LORA` = 0. ⚠️ La perdita fusa restituisce `logits=None` quando si passano le
`labels`: va spenta se servono i logit. Entrambi sono già in `train_qwen35.py` (copia di prima:
`….bak_pre_lora_peft_20ott`).

Misura sul passo vero di `train_qwen35.py` (4B, peft r=32 su 7 moduli, lotto 2 × 768/640 con
padding, checkpointing; `banco_train_qwen35.py`, GPU libera):

| | token/s | picco |
|---|---:|---:|
| Gated DeltaNet + flash (come prima) | 459 | 12,84 GB |
| **+ norme, perdita, GEMM, LoRA fuso** | **468** | **9,34 GB** |

Perdite uguali fino alla terza cifra; tutte le 2.048 chiamate LoRA vanno al kernel fuso.
**Con la maschera di padding la flash non lavora mai** (128 chiamate su 128 al percorso originale).
Il 22 ott: con padding a destra e labels -100, togliere `attention_mask` lascia la perdita uguale
(13,975150 contro 13,975204 sullo stesso lotto) e manda alla flash 128 chiamate su 128: passo
464 → 472 tok/s. **Applicato in `train_qwen35.py`** (se il padding andasse a sinistra la maschera
torna obbligatoria). Lo script arrotonda anche la lunghezza del lotto al multiplo di 128, così le
GEMM usano le 197 forme tarate da rocm-marconi (`gemm_gfx906\tarature.json`).

Il 22 ott, sul passo vero, GEMM gfx906 acceso 473 tok/s contro 471-472 spento: le tarature (−11% sulla
somma delle GEMM) nel passo intero valgono +0,3%, perché il collo non sono le GEMM. Restano accese.

**Qwen3.5 con immagini (22 ott)**: con torchvision installato, `AutoModelForImageTextToText` →
`Qwen3_5ForConditionalGeneration`, immagine 448×448 più testo, peft r=32 sul solo modello di lingua,
checkpointing, acceleratori della ruota: passo 0,94 s, picco 9,41 GB, perdita finita e in discesa,
flash 160/160, LoRA fuso 1024/1024. La torre visiva (congelata) va avanti e indietro sulla GPU.
Banco: `prova_qwen35_immagine.py`.

⚠️ **Senza checkpointing il 4B a 2×768 NON entra**: picco 21,2 GB su 16. Il driver **non dà
errore**: tracima in silenzio nella memoria condivisa e il passo va 5 volte più lento (93 tok/s).
Su Windows un'allocazione oltre la VRAM non fallisce: chi rischia di sforare imposti
`torch.cuda.set_per_process_memory_fraction(0.85)` per avere un `OutOfMemoryError` invece della lentezza.

### Dal 20 ottobre: kernel Gated DeltaNet e GEMM instradate (rocm-marconi)

L'attenzione lineare ha un kernel proprio per gfx906, compilato a runtime (hipRTC), avanti
e indietro, 11 su 11 giusti. **Va agganciato a mano**, dopo aver importato transformers 5:

```python
import sys
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import gdn_gfx906
gdn_gfx906.aggancia()   # sostituisce torch_chunk_gated_delta_rule di modeling_qwen3_5
```

Con quello e le GEMM instradate (B1), passo LoRA del 4B (stesso assetto di sopra; mediane
dal 3° passo, misure di rocm-marconi, `diag_gemm\ab_lora.py --gdn`):

| | 256 token | 512 token | 1024 token |
|---|---:|---:|---:|
| 17 ott, percorso puro | 1,41 s · 182 tok/s | — | — |
| **20 ott, Gated DeltaNet + Tensile** | **0,797 s · 321 tok/s** | **1,141 s · 449 tok/s** | **2,196 s · 466 tok/s** |

- **Almeno 512 token per passo**: a 256 metà del passo sono pause. A 1024 il picco è 11,0 GB.
- Il clock della GPU scende nelle pause (la stessa GEMM costa +13–46% dopo 0,5–10 ms di
  GPU ferma). Bloccarlo da Adrenalin è una scelta del progetto.

### Flash attention (dal 20 ottobre, su richiesta)

Il kernel di rocm-marconi (`flash_gfx906\fa_gfx906.py`) è collegato a
`F.scaled_dot_product_attention` dal modulo `ruota_flash`, **da accendere a mano**:

```python
import sys
sys.path.insert(0, r"C:\LaRuota_workspace\ruota_flash")
import ruota_flash
ruota_flash.attiva()          # ruota_flash.disattiva() per tornare indietro
print(ruota_flash.contatori)  # quante chiamate sono andate alla flash, e perché le altre no
```

Va alla flash: fp16 (o fp32 sotto autocast fp16), head dim 64/128/256, causale o no,
GQA (`enable_gqa=True`), S_q ≠ S_k, dropout. Tutto il resto va al percorso originale,
invariato: `attn_mask`, fp32 senza autocast, altre head dim, e D=256 non causale (lì è più
lenta). Verificato il 20 ott (`ruota_flash\prova_ruota_flash.py`, 11/11, scarti ~5e-04 come
il fp16): forma B2 H16 S2048 D128 causale, avanti+indietro, **1,95x** più veloce e memoria
**da 2.162 a 146 MB**.

⚠️ Il dropout usa una maschera propria (stessa distribuzione, numeri diversi da quelli di
PyTorch). ⚠️ Vale per il codice che chiama `F.scaled_dot_product_attention` (transformers lo
fa); il percorso veloce di `nn.MultiheadAttention` in eval non passa di qui. Non ancora
provata in un addestramento intero di Qwen3.5.

## A7. Cosa non è ancora stato provato

- **addestramenti lunghi** (ore): il massimo misurato sono pochi passi;
- **salvataggio e ripresa dei checkpoint**;
- forme di convoluzione fuori dalle 597 provate (A2.4).

Chi fa per primo una di queste cose controlli i risultati contro la CPU e riferisca
l'esito al manutentore.

---

# PARTE B — PER CHI LA MANTIENE

## B1. Lo stack runtime — cosa deve stare dove

**`torch\lib` tiene copie proprie delle DLL, ed è l'unica che conta.** Da Python 3.8 la
ricerca delle DLL non usa il PATH.

| file in `torch\lib` | perché |
|---|---|
| `uv.dll` | `torch_cpu.dll` la importa (distributed). Senza, `import torch` fallisce lamentando **`shm.dll`**, che manda fuori strada |
| `libiomp5md.dll` | OpenMP di Intel, che MKL usa per i suoi thread; `torch_cpu.dll` la importa. **`setup.py install` non la copia**: dopo un'installazione pulita va rimessa da `C:\LaRuota_workspace\mkl_prefix\Library\bin\` (lo fa `deploy_runtime_dlls.py`) |
| `hiprtc07013.dll` (158 720 byte, sha256 `029b9131…`, dal 10 nov) | shim di miopen-gfx906: carica hipRTC 7.1 da `MIOPEN_SHIM_HIPRTC`, poi dalla propria cartella (dove stanno `hiprtc0701.dll`, `hiprtc-builtins0701.dll` e `amd_comgr0701.dll`), infine da ROCm 7.1; impone `-mcode-object-version=5`. La versione precedente (158 208 byte) caricava solo da `C:\Program Files\AMD\ROCm\7.1\bin`, quindi senza ROCm 7.1 installato MIOpen non compilava i kernel |
| `amd_cmgr3.dll` (160 256 byte) | shim: impone la code object version e riscrive `sramecc+` in `sramecc-` |
| `rocblas\library\` (774 file) | libreria Tensile **piatta** di ROCm 5.7. Dal 20 ott rocm-marconi ha **instradato** 5 file (`TensileLibrary_Type_HH_HPA_…_gfx906.dat` NN/NT/TN e due `SS_…`): voci a chiave esatta verso la soluzione più veloce già presente, per le forme del LoRA di Qwen3.5-4B (256/512/1024 token), e corrette 12 voci di agosto che puntavano alla soluzione sbagliata. Nessun kernel nuovo. Per tornare all'originale: i tre HH_HPA ← `*.bak_pre_instradamento_20ott`, i due SS ← `*.bak_pre_correzione_indici_20ott`. Strumenti per instradare forme nuove: `diag_gemm\` |
| `rocblas.dll` | quella del Marconi, la stessa di ZLUDA |
| `rocsolver.dll` | ROCm 5.7; `torch_hip` la importa direttamente (VEGA-PATCH 64, 67) |
| `MIOpen.dll` (492 240 896 byte, md5 `795DBB2D…`, dal 20 ott) | MIOpen 3.5.2 di TheRock **ricompilata con le tre patch di miopen-gfx906** (WrW3x3, V4R1, sotto-campionamento), con l'import `amd_comgr.dll` rinominato `amd_cmgr3.dll` (lo shim) come nel pack. Quella di prima (la stessa del pack, md5 `22217B4C…`) è in `backup_miopen_pre_patch_rocm_2026_10_20\MIOpen_torch_lib_in_uso.dll`. ⚠️ Tornando a quella vanno riaccese le esclusioni 58, 62 e 72 (B2) |
| `amdhip64_7.dll` (105 984 byte, md5 `2AD85902…`, dal 17 ott) | shim del Marconi che **MIOpen** carica (PyTorch invece va direttamente ad `amdhip64.dll` del driver). Dal 17 ott, opera di rocm-marconi, contiene il **ponte sullo stream nullo** anche per le attese che partono da dentro MIOpen. La copia precedente è in `amdhip64_7.dll.bak_pre_ponte_20261017`. Con questa, la VEGA-PATCH 71 non serve più alla correttezza, ma resta: non costa nulla ed è una seconda difesa |

Cosa **non** deve esserci:

| | perché |
|---|---|
| `amd_comgr.dll` (110 MB, ROCm 7.01) | fa ombra a quella del driver: ogni allocazione GPU va in access violation |
| `amdhip64_6.dll` (il vecchio proxy) | non serve: torch è linkato direttamente ad `amdhip64.dll` del driver |
| `sitecustomize.py` in site-packages | iniettava un finto `torch._C._distributed_c10d` all'avvio: ora fa fallire `import torch` |

Se le convoluzioni tornano a fallire o l'allocazione crolla, **la prima cosa da
controllare sono queste voci**.

### L'ambiente e i vincoli

`C:\LaRuota_workspace\vincoli_ruota.txt` tiene fermi torch (la ruota stessa), numpy
2.2.6, pyarrow < 22 e accelerate 0.33.0, ognuno col motivo accanto.

- **numpy**: `torch_python` è compilato contro gli header di numpy 2.2.6 (VEGA-PATCH 65),
  quindi regge la 1.x e la 2.x. Prima di salire oltre la 2.2.6: `verifica_mkl_numpy2.py`
  e i censimenti.
- **accelerate 0.33.0** dichiara `numpy<2` e `pip check` se ne lamenta: è un vincolo di
  metadati, un passo fp16 sulla GPU funziona. Non aggiornarla senza riprovare Qwen/LoRA.
- **pyarrow**: la 21 è quella verificata (la 22+ vuole numpy 2 all'esecuzione, cosa che
  ora c'è, ma non è stata riprovata).

### ⚠️ Lo stream nullo non sa aspettare (difetto del driver)

Il runtime HIP del driver Adrenalin (`amdhip64.dll`, HIP 5.7.31541, e il Marconi che vi
inoltra) restituisce `hipErrorInvalidValue` da `hipStreamWaitEvent` quando lo stream che
aspetta è lo **stream nullo**, che in PyTorch è quello predefinito. La ruota lo aggira
(VEGA-PATCH 69, `c10/hip/VegaStreamWait.h`) con il **ponte** proposto da rocm-marconi:
verso lo stream nullo l'attesa va su uno stream **bloccante** di servizio, uno per scheda,
che lo stream nullo per specifica HIP aspetta. Se il ponte non si può creare si ricade su
`hipEventSynchronize`.

| | CPU ferma in `wait_stream`/`wait_event` (lavoro di 372 ms) | risultato |
|---|---|---|
| prima versione della 69 (`hipEventSynchronize`) | **341–388 ms**, tutta l'attesa | giusto 5/5 |
| **ponte** (in vigore) | **0,0–0,1 ms**; solo la prima attesa di ogni processo ~190 ms (creazione del ponte) | giusto 5/5 |

Riproduzione senza PyTorch: `riproduci_stream_nullo_hip.py`; costo: `banco_attesa_stream.py`.

Dai banchi di rocm-marconi (`diag_stream_nullo\`, non inclusi):
nei banchi gli stream non si sovrappongono mai (due kernel su stream diversi: 599 ms,
come in fila), e l'ordine c'era anche senza attesa. Il difetto è già corretto nel CLR
attuale, ma nessun runtime più recente vede la Radeon VII.

⚠️ **Smentito per gli stream interni delle librerie.** Il ponte copre solo le attese che
partono da PyTorch. Quelle che partono **da dentro una libreria** chiamano il runtime
direttamente: MIOpen, per le LSTM con ≥ 32 passi, distribuisce l'indietro su stream di
servizio e poi fa aspettare lo stream nullo. L'attesa viene rifiutata, MIOpen ignora
l'errore, e **i gradienti escono sbagliati** (VEGA-PATCH 71, trovato dalun utente).
Lì l'attesa persa ha fatto danni. Regola: **una libreria che usa più stream va fatta
lavorare su uno stream solo**. Fra le librerie della ruota, solo MIOpen usa più stream, e
solo per le RNN (`MultiStreamController` compare solo in `src/rnn` e `src/ocl/rnnocl.cpp`).

## B2. ⚠️ I difetti che danno numeri sbagliati senza dire niente

Sono cinque, tutti in MIOpen. **Dal 20 ottobre tre sono corretti alla radice** in una
MIOpen ricompilata con le patch di miopen-gfx906 (B4, «Ricompilare MIOpen»), e le loro
esclusioni sono spente (VEGA-PATCH 75, righe commentate in `torch/__init__.py`, pronte da
riaccendere se si tornasse alla MIOpen vecchia). Gli altri due sono neutralizzati dalle
patch 71 e 73 e dallo shim. Vanno conosciuti tutti: tornando alla MIOpen vecchia, o
toccando i punti indicati, ricompaiono senza alcun segnale.

| difetto | stato |
|---|---|
| conv **1×1 con stride > 1**: se la stessa forma torna con un **lotto diverso** nello stesso processo (l'ultimo lotto corto di ogni epoca), gradiente dei pesi sbagliato (scarto 3,1 misurato) o memoria vicina sporcata. Causa: `ConvAsmBwdWrW1x1` e `ConvAsm1x1U` sotto-campionano con una cache di kernel senza il lotto nella chiave | **corretto in MIOpen il 20 ott** (lotto nella chiave). Verificato con i solver riaccesi: lotti 2,4 / 4,2 / 8,2,8 giusti. Esclusione (VEGA-PATCH 72) spenta dalla 75. Banco: `diag_battuta\ordine_lotti.py <cache privata> 2,4` |
| LSTM a uno strato con **≥ 32 passi**: dal **secondo** indietro i gradienti dei pesi escono a zero (scarto 1,0), a volte anche quello dell'ingresso. Causa: le soluzioni RNN **a più stream** di MIOpen (`rnn/selector.cpp`, `seqLen >= 32`) fanno aspettare lo stream nullo, e il driver rifiuta l'attesa (B1) | neutralizzato: `MIOPEN_RNNBWDMS_EXP=0`, `MIOPEN_RNNBWMS_EXP=0`, `MIOPEN_RNNFWD_EXP=0` in `torch/__init__.py` (VEGA-PATCH 71) **e** lo shim con il ponte |
| gradiente sui **pesi** della conv 3×3 a 3 canali (primo strato di ogni rete RGB): scarto relativo 91. Causa: `ConvAsmBwdWrW3x3`, ramo `reverse_inout`, passi calcolati con i canali non scambiati in `conv_sizes.inc` | **corretto in MIOpen il 20 ott**. Verificato forzando il solver (log: `Selected: ConvAsmBwdWrW3x3`): C=3/5 → 16/64, scarto 2,5–2,8e-07. Esclusione (VEGA-PATCH 58) spenta dalla 75. Banco: `diag_wrw3x3\caso.py C K N H W` con `CARTELLA_DB` nuova |
| gradiente sui **pesi** su 77 forme su 597, Conv1d **e** Conv2d ordinarie: da relativo 1,2 a NaN. Causa: `ConvAsmImplicitGemmV4R1DynamicWrw`, argomenti del kernel non più trasposti dopo il commit MIOpen `24815807e1` | **corretto in MIOpen il 20 ott**. Verificato forzando il solver: 5 forme (lotto 1 e 4, k1/k3/k5, Conv1d), ≤ 1,6e-06. Esclusione (VEGA-PATCH 62) spenta dalla 75. Banco: `diag_wrw3x3\caso_v4r1.py C K N H W KERNEL [1d]` |
| RNN con **più di uno strato**: uscita completamente sbagliata appena una dimensione cresce | era la stessa causa della riga sopra (il percorso a più stream). Dal 2 ago al 20 ott `use_miopen` rifiutava il multistrato (VEGA-PATCH 59); **tolta il 20 ott (VEGA-PATCH 73)**: con la 71 e lo shim nuovo è giusto, e 2,84x più veloce del percorso nativo |

⚠️ **Con la MIOpen vecchia, le due esclusioni WrW rompevano forme disgiunte: nessuna
sostituiva l'altra.** Chi tornasse alla MIOpen vecchia deve riaccenderle **tutte**
(58, 62, 72), togliendo il commento davanti alle righe della 75.

⚠️ **La cache dei kernel di MIOpen ha per chiave nome, opzioni e versione, non il
sorgente.** Una MIOpen corretta con lo stesso numero di versione riusa i kernel compilati
da quella vecchia. Per questo la ruota ha una cache sua (VEGA-PATCH 74,
oggi `%LOCALAPPDATA%\2S\la-ruota\miopen`, VEGA-PATCH 85), e i banchi vanno lanciati con
cartelle nuove.
⚠️ Fino al 20 ottobre **il db** (scelte dei solver e sintonie) è rimasto comunque quello
condiviso con ZLUDA: il responsabile del progetto ha `MIOPEN_USER_DB_PATH=%LOCALAPPDATA%\miopen\db` fra le
variabili **utente**, e quella batteva il `setdefault` della 74. La VEGA-PATCH 79 lo
corregge, e un percorso privato impostato da uno script continua a vincere. Fra le variabili
utente c'è anche `MIOPEN_FIND_MODE=1` (NORMAL): ogni processo rifà la ricerca a tempo e la
scelta del solver può cambiare da un processo all'altro (A4). **Si tiene così, per scelta**
(il responsabile del progetto, 20 ott): la GPU di macchina di prova è spesso condivisa fra più lavori, e una ricerca fatta a
GPU occupata può scegliere un solver più lento. Con `FIND_MODE=1` quella scelta vale per un
solo processo; col modo predefinito verrebbe salvata e riusata per sempre. Il prezzo è una
variabilità di ~1e-6 relativo fra processi. MIOpen non passa mai alla CPU: tutti i solver
sono kernel GPU.

### ⚠️ Fuori da MIOpen: `eigh` via hipSOLVER (corretto dalla 78)

Su ROCm `USE_LINALG_SOLVER` **è definito** (`BatchLinearAlgebraLib.h`: `|| defined(USE_ROCM)`),
e `linalg_eigh` usava sempre `syevj` via **hipSOLVER**, che sbaglia in silenzio da n=64 in su
(autovalori a 0 o 1e+35; fp32 e fp64, singola e a lotti; giusta fino a 48). La `svd` passava
da `gesvdj` (hipSOLVER): risultati giusti ma non ripetibili (9e-4). rocSOLVER chiamato
direttamente è giusto (`prova_rocsolver_syev.py`, `prova_rocsolver_gesvd.py`): il difetto sta
nello strato hipSOLVER. Dalla VEGA-PATCH 78 eigh va su `rocsolver_?syevd/?heevd` e svd su
`rocsolver_?gesvd`, entrambe a lotti. Il censimento lo aveva mancato perché provava solo
matrici piccole: **ogni operazione di algebra lineare va provata fino a 512**
(`battuta_linalg_dimensioni.py`). (La docstring della patch 67 diceva il contrario su
`USE_LINALG_SOLVER`; corretta.)

### Regole di collaudo che ne discendono

**La ricerca di MIOpen sceglie il solver per velocità, non per correttezza.** Ogni forma
nuova va confrontata con la CPU almeno una volta:

- sul **gradiente dei pesi**, non solo sull'uscita: tutti i 77 casi sbagliati erano lì;
- con **lotto maggiore di 1**: 69 su 77 comparivano solo a lotto 4;
- su **almeno tre passi all'indietro di fila**: la LSTM a più stream era giusta al primo
  e sbagliata dal secondo (`prova_lstm_gradzki.py` faceva un passo solo, e non la vide);
- con forme **oltre le soglie** delle librerie: MIOpen cambia algoritmo RNN a 32 passi;
- con uno scarto **relativo con un pavimento** al denominatore. Il relativo puro esplode
  su riferimenti nulli, l'assoluto dà falsi allarmi su gradienti grandi.

⚠️ **La cache di MIOpen conta solo in diagnosi.** Memorizza il solver scelto per ogni
forma, quindi a cache diversa un difetto sembra intermittente. Ma le variabili di
esclusione hanno la meglio sulla cache: **in produzione non serve svuotarla**.
Svuotarla, anzi, costa: alla ricerca successiva MIOpen chiede spazi di lavoro molto
grandi, ed è capitato un esaurimento di memoria con 15,86 GB liberi.

⚠️ **Per identificare un solver colpevole, non usare la riga `solver` del log**: dà lo
stesso nome con la variabile accesa e spenta. Serve la riga dell'algoritmo, filtrata per
direzione:

```
MIOPEN_ENABLE_LOGGING=1 MIOPEN_LOG_LEVEL=6 python caso.py 2>&1 | grep GetInvoker | grep xWxDefault | sed "s/.*and //"
```

⚠️ **Per riprodurre i difetti, i solver vanno riaccesi a mano**: `torch/__init__.py` li
spegne con `setdefault`, e un banco lanciato normalmente misura zero.

⚠️ Il censimento di Rocm segnala `layer_norm`, `group_norm` e `softmax` all'indietro
come «da dirottare». **Sono falsi allarmi**: il banco usa `f(x).sum()`, il cui gradiente
per una normalizzazione o una softmax è *analiticamente zero*, e il confronto relativo su
zero esplode. Con una perdita pesata lo scarto è ~1e-07.

## B3. Il dettaglio di cosa funziona

| area | esito |
|---|---|
| censimento di Rocm, 105 operazioni | **105 su 105** |
| censimento della ruota, 98 operazioni | **98 su 98** (17 ott) |
| algebra lineare GPU contro numpy | **20 su 20** (17 ott) |
| `cholesky`, `cholesky_ex`, `cholesky_solve`, `cholesky_inverse`, `lstsq` su GPU — 4 precisioni, lotti fino a 512, `upper`, sovra- e sottodeterminati, broadcasting, gradienti | **63 su 63** (VEGA-PATCH 67, via rocSOLVER) |
| algebra lineare CPU | tutta, ≤ 3e-12 contro numpy (MKL, VEGA-PATCH 65–66) |
| interoperabilità numpy 1.26 **e** 2.2.6 | **21 su 21** in `verifica_mkl_numpy2.py` con entrambe |
| più stream, eventi, `record_stream`, copie pinned su stream secondario, 8 stream in catena | **9 su 9** (VEGA-PATCH 69, 70); prima del 17 ott fallivano **tutti** |
| `torch.cuda` dentro TorchScript | 2 su 2 (VEGA-PATCH 68, 69) |
| profiler con tempi GPU, `record_function`, `emit_nvtx` | funziona (VEGA-PATCH 68); i marcatori roctx sono vuoti |
| convoluzioni, 597 forme 1D e 2D | **597 su 597** |
| LSTM / GRU / RNN | **13 su 13** |
| CNN addestrata 5 passi contro CPU | pesi identici a 1,2e-07 |
| dropout nativo, `sdpa` con dropout, `TransformerEncoder` in eval con percorso veloce, MHA con dropout | corretti (riverificati il 17 ott) |

Sulla CPU, matmul torch (MKL) contro numpy (OpenBLAS) nello stesso istante, a macchina
carica (`banco_cpu_mkl.py`):

| | torch | numpy | |
|---|---|---|---|
| 4096 fp32 | **158–235 GFLOPS** | 88–110 | 1,4–2x |
| 4096 fp64 | **101 GFLOPS** | 32–49 | 2–3x |
| 2048 fp32 | 66–87 GFLOPS | 22–37 | ~2,5x |

Prima di MKL la matmul 2048 fp32 faceva **1,4 GFLOPS** (Eigen).

Il GEMM GPU passa dalla **stessa `rocblas.dll` di ZLUDA**: su quel fronte non c'è
vantaggio, il guadagno è negli elementwise e nei lanci.

## B4. Ricompilare

```bat
C:\LaRuota_workspace\build_laruota_canonical.cmd resume
```

Prima di lanciare, **verificare che nessun processo carichi le DLL della ruota**: per
ogni `python.exe`, i moduli caricati non devono stare sotto `C:\LaRuota_workspace`. I job
applicativi girano di solito sul loro `.venv` e non c'entrano, ma va controllato.
Avvisare chi usa la ruota (A2.6). Lo STEP 3 dello script controlla che le patch
persistenti 65–69 siano nei sorgenti.

| regola | perché |
|---|---|
| **la cache CMake è la fonte di verità**, non lo script | in `resume` `setup.py` non ripassa le `USE_*`; `cmake_dependent_option` non sovrascrive una voce già in cache. Modificare `build\CMakeCache.txt` **senza BOM**, poi toccare `CMakeLists.txt` |
| togliendo una voce dalla cache, **togliere anche il commento `//` che la precede** | un commento seguito da una riga vuota è un errore di sintassi per CMake: segnala *Parse error*, prosegue, e a fine configure dichiara *Configuring incomplete* |
| **si compilano i `.hip`, non i `.cu`** | l'albero contiene i `.hip` già generati e hipify non viene rilanciato: una patch sui `.cu` non arriva al compilatore. hipify rinomina anche i **nomi** dei file (`SparseCUDATensorMath.cu` → `SparseHIPTensorMath.hip`) |
| `clang-cl` vuole **`/O2`**, non `-O3` | `-O3` viene scartato in silenzio: build a ottimizzazione zero, 80x più lenta |
| niente `/DNDEBUG` fra i flag HIP | `Macros.h` fa `#undef NDEBUG` apposta; definirlo rompe il link |
| code object **v4 o v5, mai v6**; target `gfx906` liscio | il driver Adrenalin non legge la v6; `sramecc` attivo viene rifiutato |
| **`libuv_ROOT`** obbligatoria | altrimenti `CMakeLists.txt` spegne distributed senza chiedere |
| versione `2.5.0+gita8d6afb` via `PYTORCH_BUILD_VERSION` | `2.5.0a0` è una pre-release per PEP 440 e `transformers 5.x` disattiva torch. Dopo un cambio di versione va rimossa a mano la vecchia `egg-info`, e aggiornato `vincoli_ruota.txt` |
| in `torch_hip`, **`TORCH_API` significa *importa*** | gli oggetti ricevono `TORCH_HIP_BUILD_MAIN_LIB`, non `CAFFE2_BUILD_MAIN_LIB`. La macro che esporta è **`TORCH_HIP_CPP_API`** |
| ogni `.hip` che definisce un'operazione deve includere il proprio `ATen/ops/<op>_native.h` | altrimenti la funzione non viene esportata e la chiamata salta a `0x0` (20 operazioni rotte così fino al 29 agosto) |
| MKL **statico** da pip, in una cartella separata: `pip install --prefix C:\LaRuota_workspace\mkl_prefix mkl-static mkl-include intel-openmp` | FindMKL su MSVC cerca prima la variante `_dll`: se ci fosse anche `mkl-devel`, collegherebbe quella dinamica. `mkl_prefix\Library` è in `CMAKE_PREFIX_PATH` (script e cache) e in `INTEL_MKL_DIR`/`INTEL_OMP_DIR` |
| gli header di numpy 2 stanno in `C:\LaRuota_workspace\numpy2_headers` (numpy 2.2.6, `--target`) | `Dependencies.cmake` punta lì il bersaglio `Python::NumPy` (VEGA-PATCH 65). **Non** cambiare `_Python_NumPy_INCLUDE_DIR` in cache: FindPython lo lega all'interprete con una firma e lo ripristina |
| con il pool di thread nativo (`USE_OPENMP=OFF`) **MKL va su un solo core** se manca la VEGA-PATCH 66 | `ParallelNative.cpp` faceva `mkl_set_num_threads(1)` globale. Controllo: `MKL_VERBOSE=1` deve mostrare `NThr:16`, non `NThr:1` |
| un header in `c10/hip` o `ATen/hip/impl` costa una ricompilazione di ~90 passi | `VegaStreamWait.h`, `HIPGuardImpl.h`, `HIPEvent.h` sono inclusi ovunque in `torch_hip`. Stimare prima con `ninja -n` in `build\` |
| dopo un'installazione, **verificare con un hash** che le DLL siano state sostituite | se un processo tiene aperta una DLL, la copia può fallire; a volte in silenzio |
| dopo una ricompilazione **verificata** (`regressione_completa.py` verde), **ricopiare la riserva**: `robocopy <venv_build>\Lib\site-packages\torch C:\LaRuota_workspace\riserva_ruota_<data>\torch /E`, poi ripuntare `ruota_vecchia\torch` (`rmdir` del collegamento, `New-Item -ItemType Junction`) | fino al 20 ott la riserva era ferma al 16 ott, senza le correzioni del 17–20: LSTM ≥ 32 passi e conv 1×1 al cambio di lotto sbagliavano lì in silenzio. Una riserva diversa da quella in uso è un rischio, non una difesa |

Dopo ogni modifica: la battuta degli export (`diag_dropout\battuta.py`, dopo aver
rigenerato il dump degli export) e i banchi di B7.

### Ricompilare MIOpen

MIOpen non fa parte della build della ruota: è la build di TheRock in
`C:\TheRock_workspace\TheRock\build_gfx906\ml-libs\MIOpen\build` (sorgenti in
`rocm-libraries\projects\miopen`, compilatore clang di TheRock in `core\clr\dist\lib\llvm`,
lo stesso con cui è nata a giugno la MIOpen del pack). Il 20 ott, per le tre patch dell'agente
Rocm (516 passi, ~15 minuti con 8 processi):

1. patch nei sorgenti: `git apply --ignore-whitespace <patch>` dentro `rocm-libraries`
   (i sorgenti sono CRLF). Ora applicate e non committate: `git status` le mostra;
2. `build\miopen_ricompila.cmd compila` di miopen-gfx906 (ambiente di Visual Studio; svuota `HIP_PATH`, che a
   sistema punta a ROCm 6.2 e fa fallire il configure con *"Invalid character escape '\P'"*);
3. `python build\miopen_rinomina_comgr.py <build\bin\MIOpen.dll> <copia>` (miopen-gfx906): l'**unica** differenza
   fra la MIOpen del pack e la build di TheRock sono 4 byte, l'import `amd_comgr.dll` →
   `amd_cmgr3.dll` (verificato byte per byte);
4. con la ruota libera, la copia in `torch\lib\MIOpen.dll`;
5. **cache MIOpen nuova** (B2): la chiave dei kernel non contiene il sorgente;
6. verificare ogni correzione **forzando il suo solver** e controllando `Selected:` nel log
   (`MIOPEN_DEBUG_FIND_ONLY_SOLVER` vale solo con `benchmark=True`), poi la battuta ampia.

La MIOpen del **pack** (usata da ZLUDA) non è stata toccata: segue rocm-marconi.

## B5. Diagnostica, nell'ordine in cui conviene

1. **Registro eventi di Windows** (`Get-WinEvent -ProviderName 'Application Error'`):
   modulo e offset del crash senza debugger. Offset `0x0` = chiamata a un puntatore
   nullo, quasi sempre un export mancante.
2. **`AMD_LOG_LEVEL=4`**: il runtime racconta ogni chiamata, e stampa file e riga del
   proprio sorgente. Se l'ultimo kernel lanciato è quello della riga *precedente*, il
   crash è lato host.
3. **`MIOPEN_ENABLE_LOGGING=1 MIOPEN_LOG_LEVEL=6`** per MIOpen (B2 per leggerlo bene).
4. **Gli export**: `dumpbin /exports torch_hip.dll` o `llvm-objdump -p`; per le funzioni
   di rocSOLVER, gli export di `rocsolver.dll`.
5. **Riprodurre fuori da PyTorch**: un `.hip` di venti righe, o ctypes direttamente su
   `amdhip64.dll` (così si è isolato lo stream nullo). Con una build da ore per
   tentativo, è la differenza fra una giornata e una settimana.
6. **Misurare l'ordine, non solo i codici di ritorno**: un banco d'ordine con un
   controllo *senza* attesa (`diag_stream_nullo\ordine_reale.py`). Il controllo che cade
   è quello che rivela.
7. **Cercare una stringa nota dentro la DLL**: se una diagnostica messa nel sorgente non
   c'è, il linker ha scartato il codice.

## B6. Le famiglie di difetti viste finora

Utile per riconoscere un difetto nuovo:

| famiglia | sintomo | esempi | rimedio tipo |
|---|---|---|---|
| **masquerading** | *"Could not run … 'HIP' backend"*, *"Expected … DeviceType::HIP"* | 21 righe con `kHIP`/`DispatchKey::HIP` (patch 63), `RecordStream.hip` (70), `jit/cuda/cuda.h` (68) | dove arriva un oggetto «CUDA», usare il tipo `…MasqueradingAsCUDA` o `.hip_stream()` |
| **export mancante** | salto a `0x0`, access violation | 20 operazioni (29 ago) | includere `ATen/ops/<op>_native.h` nel `.hip` |
| **percorso spento per ROCm** | *"requires MAGMA / cuSOLVER"* | algebra a lotti (64), cholesky e lstsq (67), `ir.cpp` di TorchScript (69) | reindirizzare su rocSOLVER, o togliere la guardia `USE_ROCM` se il motivo non vale più |
| **solver MIOpen difettoso** | numeri sbagliati, nessun errore | B2 | variabile di esclusione, banco su forme |
| **difetto del driver** | codice d'errore dove su Linux non c'è | stream nullo (69) | aggiramento nella ruota, consegna a rocm-marconi |
| **difetto del driver dentro una libreria** | numeri sbagliati, nessun errore (la libreria ignora il codice d'errore) | LSTM a più stream di MIOpen (71) | far lavorare la libreria su uno stream solo (variabili di MIOpen); `AMD_LOG_LEVEL=3` mostra le chiamate rifiutate |

⚠️ **Una funzione che nessun banco tocca non è verificata**: gli stream secondari erano
tutti rotti dal primo giorno, e lo si è scoperto solo riattivando TorchScript.

## B7. Banchi di prova

In `C:\LaRuota_workspace\`, da lanciare con il python della ruota.

**Tutti in una volta:** `regressione_completa.py` lancia 16 banchi in fila, ciascuno nel suo
processo, e stampa una riga d'esito per banco; i log completi vanno in `regressione_log\`.
Il 20 ott, configurazione definitiva (MIOpen nuova, esclusioni spente): **14 su 14 verdi in
3,9 minuti** (`regressione_completa_2026_10_20.log`), e di nuovo dopo la patch 76
(`…_p76.log`); dopo le patch 78 e 79, con i due banchi nuovi dell'algebra lineare, **16 su 16
in 2,2 minuti** (`…_p79.log`). In `prova_conv_miopen.py` il gradiente dei pesi si confronta
ora in **relativo** (soglia 2e-5): con la soglia assoluta di prima, una variante Winograd
scelta per tempo faceva fallire il banco una volta su ~15 (A4). ⚠️ I **tempi** stampati valgono solo a GPU libera: in quella seconda corsa
un altro processo usava la GPU e GEMM e LSTM risultavano 3 volte più lenti; rimisurati
da soli erano quelli di sempre. La correttezza non ne risente. La battuta delle 597 forme
(`battuta_conv_ampia.py`) va lanciata a parte, perché con la cache vuota impiega molto di più:
il 20 ott **597 su 597**, senza esclusioni.

| banco | cosa verifica | atteso |
|---|---|---|
| `regressione_completa.py` | i 16 banchi qui sotto marcati come principali | 16 su 16 |
| `battuta_linalg_dimensioni.py` | 13 operazioni di algebra lineare GPU contro CPU, n da 16 a 512, fp32/fp64, singole e a lotti | 13 su 13 (prima della 78: eigh/eigvalsh sbagliate da 64) |
| `prova_eigh_svd_78.py` | svd ed eigh via rocSOLVER: rettangolari alte e larghe, `full_matrices`, complessi, `UPLO`, viste trasposte, gradienti contro CPU, ripetibilità, lotti vuoti | 93 su 93 |
| `diag_wrw3x3\solutori_passo2.py [--solo NOME…]` | conv 3×3 stride 2: ogni solutore WrW forzato | Winograd `<3-4..6>` 2–4e-4 assoluto, gli altri ≤ 4e-5 |
| `prova_allocazione_gpu.py` | allocazione, copie, elementwise, matmul, autograd, GEMM fp16 | tutto OK, GEMM 9–11 TFLOPS |
| `verifica_mkl_numpy2.py` | MKL (matmul 4096 > 100 GFLOPS), LAPACK su CPU, `eig` su GPU, interoperabilità numpy | 21 su 21, con numpy 1.26 **e** 2.2.6 |
| `banco_cpu_mkl.py` | matmul CPU torch contro numpy, nello stesso istante | torch davanti alle taglie grandi |
| `censimento_ruota.py` | 98 operazioni GPU contro CPU | 98 su 98 |
| `censimento_linalg_gpu.py` | algebra lineare GPU contro numpy | 20 su 20 |
| `prova_cholesky_lstsq_gpu.py` | cholesky e varianti, lstsq su GPU | 63 su 63 |
| `prova_stream_eventi.py` | più stream, eventi, `record_stream`, TorchScript | 9 su 9 |
| `prova_torchscript_cuda.py` | `torch.cuda` dentro TorchScript | 2 su 2 |
| `banco_attesa_stream.py` | CPU ferma in `wait_stream` verso lo stream predefinito | ~0 ms, risultato 5/5 |
| `riproduci_stream_nullo_hip.py` | il difetto del driver, senza PyTorch | `hipErrorInvalidValue` solo sullo stream nullo |
| `diag_stream_nullo\ordine_reale.py` (rocm-marconi) | ordine reale fra stream, con e senza attesa | sempre `ATTESO`; il ponte con 0 ms di CPU |
| `Memoria\working\manzoni_llm\scripts\censimento_v8.py` | le 105 di Rocm | 102 + i 3 falsi allarmi di B2 |
| `prova_conv_miopen.py` (in miopen-gfx906, `banchi\`) | conv, gradienti su 5 forme, CNN 5 passi, `benchmark` | 9 su 9 |
| `battuta_conv_ampia.py` | 597 forme; con `RIACCENDI=1` cerca solver difettosi | 0 sbagliate |
| `battuta_wrw_v4r1.py` | 14 forme sul solver V4R1 | 0 sbagliate |
| `prova_lstm_gradzki.py` | 13 varianti di ricorrenti (un passo all'indietro) | 13 su 13 |
| `prova_lstm_multistream.py` | il caso minimo delun utente: LSTM 35 passi, 5 indietro di fila (VEGA-PATCH 71) | 5 su 5 giusti; con `MIOPEN_RNNBWDMS_EXP=1` torna sbagliato dal secondo |
| `prova_lstm_passi_ripetuti.py` | LSTM da 16 a 128 passi, bidirezionale, `batch_first=False`, stream secondario, 3 indietro di fila | 7 su 7 |
| `prova_lstm_multistrato_miopen.py` (in miopen-gfx906, `banchi\`) | LSTM a più strati dentro MIOpen, chiamata direttamente | 4 su 4 |
| `prova_rnn_multistrato.py` | RNN a più strati nel percorso normale (dalla 73), soglie di agosto, tempo contro nativo, `_sleep`, ricerca con `benchmark` | 10 su 10, ~2,85x |
| `ruota_flash\prova_ruota_flash.py` | flash attention collegata a `sdpa`: correttezza, ripieghi, tempo e memoria | 11 su 11, ~1,95x |
| `ruota_acceleratori\prova_gdn_padding.py` | strato Gated DeltaNet fuso contro l'originale, lotto con padding, 3 indietro | scarto ~1e-03 |
| `ruota_flash\ab_lora_con_flash.py --gdn --lunghezza 1024` | passo LoRA del 4B con la flash accesa (lancia `diag_gemm\ab_lora.py`) | ~560 token/s |
| `prova_copia_trasposta.py` | `copy_` trasposto (VEGA-PATCH 76): 5 tipi, due versi, forme irregolari, bit a bit, e banda | 25 su 25; fp16 4096×8192 ~640 GB/s |
| `diag_wrw3x3\caso.py C K N H W` (rocm-marconi) | `ConvAsmBwdWrW3x3` forzato; usare `CARTELLA_DB` nuova | scarto ~3e-07 |
| `diag_wrw3x3\caso_v4r1.py C K N H W KERNEL [1d]` | `ConvAsmImplicitGemmV4R1DynamicWrw` forzato | scarto ≤ 2e-06 |
| `diag_battuta\ordine_lotti.py <cache> 2,4` (rocm-marconi) | conv 1×1 stride al cambio di lotto | pesi ~1e-07 |
| `diag_dropout\casi.py <caso>` | le operazioni riparate il 29 agosto | `VIVO` |
| `diag_dropout\battuta.py` | export mancanti | 0 con header mancante |
| `prova_qwen35*.py`, `prova_lora_*.py` | Qwen3.5 e LoRA | A6 |

## B8. Cosa resta da fare

| lacuna | rimedio possibile | costo |
|---|---|---|
| ~~ricompilazione della ruota~~ **fatta il 20 ott (VEGA-PATCH 73)**: (a) togliere la VEGA-PATCH 59 — la sua causa era il passo in avanti a più stream di MIOpen; con la 71 e lo shim nuovo le LSTM a più strati in MIOpen sono giuste (mie 4/4; rocm-marconi 20/20 anche alle soglie di agosto); (b) `Conv_miopen.cpp` 370/443/516: nella ricerca (`benchmark=True`) limitare lo spazio di lavoro e intercettare l'esaurimento di memoria (punto 9 delle risposte Rocm); (c) `Sleep.hip`: rimettere il kernel d'attesa (`__builtin_readcyclecounter`, punto 11) | una ricompilazione unica; dopo: collaudo RNN con tre indietro di fila (`prova_lstm_passi_ripetuti.py`, `prova_lstm_gradzki.py`), misura del guadagno sulle LSTM a più strati | piccola (decine di minuti); **in attesa del via di il responsabile del progetto** |
| ~~ricompilazione di MIOpen~~ **fatta il 20 ott, esclusioni 58/62/72 spente (VEGA-PATCH 75)**; resta da portare la stessa MIOpen nel pack per ZLUDA (rocm-marconi). Era: **ricompilazione di MIOpen** con le tre patch di miopen-gfx906: WrW3x3 (`diag_wrw3x3\VEGA_conv_sizes_reverse_inout.patch`, verificata), V4R1 (`diag_wrw3x3\VEGA_v4r1_wrw_dimensioni_trasposte.patch`, verificata: regressione del commit `24815807e1`), sotto-campionamento (`diag_battuta\VEGA_sottocampiona_lotto_nella_chiave.patch`, da verificare) | dopo: togliere le esclusioni 58, 62 e 72 una alla volta, ciascuna col suo banco (`solver_wrw.py --riaccendi`, `battuta_conv_ampia.py` con `RIACCENDI=1`, `ordine_lotti.py` 2,4 e 4,2) | alta: va ricostruita la build di MIOpen di TheRock. Guadagno: +18% sul primo strato RGB; il resto oggi costa ~0. Sorgenti CRLF: `git apply --ignore-whitespace` |
| ~~collegare la flash attention~~ **fatto il 20 ott, su richiesta (A6)**; resta da provarla in un addestramento intero di Qwen3.5 e poi decidere se accenderla per difetto. Era: collegare la **flash attention** di rocm-marconi (`flash_gfx906\fa_gfx906.py`: fp16, D 64/128/256, GQA, causale, dropout, avanti e indietro, 33/33; memoria O(S); 1,2–2,4× avanti+indietro) a `scaled_dot_product_attention` | prima in Python e su richiesta (ripiego sul percorso attuale per `attn_mask` arbitraria e per D=256 non causale lungo, dove è più lenta); poi, se regge, nel percorso predefinito | medio; nessuna ricompilazione per la versione in Python |
| torchvision (serve per Qwen3.5 su immagini, restauro: basicsr/Real-ESRGAN/GFPGAN, BasicVSR++) | **compilato il 22 ott**: 0.20.0+ruota, operazioni proprie SOLO CPU (PyTorch 2.5 rifiuta le estensioni HIP su Windows, `cpp_extension.py:155`). Con **clang-cl** come la ruota: con MSVC i costruttori ereditati di c10 non si collegano (LNK2001) e `Half.h` usa `__builtin_memcpy`; la regola ninja chiama `cl` alla lettera, quindi un `cl.exe` finto (`vision_src\strumenti`). Script `vision_src\compila_torchvision_cpu.cmd`, wheel in `vision_src\dist`. Per prove senza installare: `PYTHONPATH=C:\LaRuota_workspace\vision_pythonpath` (con Pillow 11.3). `deform_conv2d` su GPU: kernel di rocm-marconi (`restauro_gfx906\vsr_dcn.py`, `registra()` dopo `import torchvision`) | **installato in venv_build il 22 ott** (scelta del progetto: la ruota completa una volta per tutte), con Pillow 11.3.0; `torchvision==0.20.0+ruota` aggiunto a `vincoli_ruota.txt`; stato di prima in `venv_build_freeze_pre_torchvision_2026_10_22.txt`. Lo stub di torchvision del `_gpu_boot` applicativi sta in testa a `sys.meta_path` e continua a vincere sui processi applicativi. Il restauro resta su RealBasicVSR; servirà per i pesi NTIRE 2021, le foto (Real-ESRGAN, GFPGAN, CodeFormer) e Qwen su immagini. Sulla GPU: `ruota_acceleratori.aggancia_torchvision_gpu()`. Con torchvision, il processore d'immagini di Qwen3.5 (`Qwen3VLProcessor`) funziona: verificato il 22 ott su CPU (testo + immagine → `pixel_values`, `image_grid_thw`). Foto: `realesrgan\realesrgan_ruota.py` (Real-ESRGAN x4plus in torch puro, pesi ufficiali con `weights_only=True`, tessere 512 con bordo 48: con il bordo ufficiale di 10 px restano cuciture fino a 18 livelli) |
| `mkldnn` (oneDNN) spento: conv e RNN su **CPU** senza i kernel ottimizzati | `USE_MKLDNN=1` e ricompilazione di `torch_cpu` | ricompilazione ampia; serve solo a chi allena reti su CPU |
| addestramento lungo con checkpoint e ripresa | una prova di qualche ora su Qwen3.5 LoRA | poche ore di macchina |

Non sono lacune della ruota, e non si risolvono: matmul bf16 (gfx906 non ha le
istruzioni), `hipBLASLt` (non supporta gfx906), Gloo su GPU e RPC (su Windows non
esistono RCCL né TensorPipe), AOTInductor (upstream non lo supporta su Windows).

## B9. Cronologia delle correzioni

| patch | data | cosa |
|---|---|---|
| 48 | lug–ago | export di `rocblas`, `hipsparse`, `MIOpen`; 16 routine `*Batched` spente (sostituite dalla 64) |
| 49–53 | 1 ago | link ad `amdhip64.dll` del driver, code object v4, guardie di masquerading, `/O2` |
| 54–57 | 1 ago | guard masquerading in copia e jiterator; distributed (libuv, `flock_`, `gloo_hip`, eccezioni di `c10d_init`) |
| 58 | 2 ago | `WRW3X3=0`: solver MIOpen difettoso sulla conv a 3 canali |
| 59 | 2 ago | RNN multistrato fuori da MIOpen |
| 60 | 3 ago | export delle primitive AMP (`GradScaler` faceva cadere il processo) |
| — | 3 ago | versione `2.5.0+gita8d6afb` per `transformers 5.x` |
| export | 29 ago | 24 include in 14 file: 20 operazioni che saltavano a zero (dropout, sdpa, transformer, sparse) |
| 61 | 29 ago | `TORCH_HIP_CPP_API` su `_assert_async_cuda` |
| 62 | 29 ago | `V4R1_WRW=0`: secondo solver MIOpen difettoso, 77 forme |
| 63 | 16 ott | 21 righe in cui hipify aveva lasciato `HIP` al posto di `CUDA`: `histc`, `bincount`, tensori nulli dell'autograd, eventi, tensori annidati, percorsi di attenzione |
| 64 | 16 ott | le 16 routine `*Batched` reindirizzate su rocSOLVER: algebra lineare a lotti |
| 65 | 17 ott | MKL statico (CPU: BLAS veloce e LAPACK; `eig` su GPU) e `torch_python` contro gli header di numpy 2: torch regge numpy 1.x e 2.x. `patch_mkl_numpy2.py` |
| 66 | 17 ott | `ParallelNative.cpp`: MKL a un thread solo dentro le regioni parallele, non per tutto il processo (matmul CPU da ~45 a ~170 GFLOPS). `patch_mkl_thread.py` |
| 67 | 17 ott | `cholesky`, `cholesky_solve`, `cholesky_inverse`, `lstsq` su GPU via rocSOLVER (`potrf`/`potrs`/`gels` a lotti) dove upstream voleva MAGMA. `patch_cholesky_lstsq_rocsolver.py` |
| 68 | 17 ott | rientrano i tre file esclusi a giugno: `shim_cuda.cpp`, `profiler/stubs/cuda.cpp` (marcatori roctx vuoti: niente roctracer su Windows), `register_cuda_ops.cpp` (con `jit/cuda/cuda.h` corretto: costanti degli eventi e `.hip_stream()`). `patch_tre_file_esclusi.py` |
| 69 | 17 ott | stream nullo che aspetta un evento (difetto del driver): prima un'attesa della CPU, poi il ponte su uno stream bloccante di servizio proposto da rocm-marconi (CPU ferma da ~370 ms a 0,1); in `ir.cpp` le operazioni `cuda::` di TorchScript tornano «con effetti collaterali» (upstream le escludeva su ROCm, e `synchronize`/`set_stream` sparivano dal grafo). `patch_stream_nullo_e_torchscript.py` |
| 70 | 17 ott | `record_stream`: `RecordStream.hip` passava uno stream CUDA a `HIPStream::unpack3`, che vuole HIP; ora passa da `HIPStreamMasqueradingAsCUDA`. `patch_record_stream.py` |
| vincoli | 17 ott | `torch==2.5.0+gita8d6afb` in `vincoli_ruota.txt`: senza, `pip install torchvision` avrebbe installato `torch-2.6.0` sopra la ruota |
| 71 | 17 ott | LSTM di MIOpen con ≥ 32 passi: gradienti dei pesi a zero dal secondo indietro (trovato dal collaudo di un utente). Soluzioni RNN a più stream spente con `MIOPEN_RNNBWDMS_EXP`/`MIOPEN_RNNBWMS_EXP`/`MIOPEN_RNNFWD_EXP=0` in `torch/__init__.py`, senza ricompilare. `patch_rnn_multistream.py` |
| shim, Tensile | 17–20 ott | opera di rocm-marconi, su decisione del progetto: `amdhip64_7.dll` con il ponte sullo stream nullo anche per MIOpen; 5 file Tensile instradati per le forme di Qwen3.5 (B1) |
| 73 | 20 ott | ricompilazione: (a) **via la VEGA-PATCH 59**, le RNN a più strati tornano in MIOpen — giuste alle soglie di agosto (LSTM/GRU/RNN, hidden 256, 64 passi, bidirezionale, impacchettate, tre indietro: 8/8), **2,84x** più veloci (LSTM 2×256: 26,3 → 9,2 ms); (b) `Conv_miopen.cpp`: spazio di lavoro della ricerca con ripiego (dimezza se esaurisce la memoria); (c) `Sleep.hip`: `torch.cuda._sleep` vera. `patch_rnn_ws_sleep.py`, banco `prova_rnn_multistrato.py` 10/10 |
| 72 | 20 ott | conv 1×1 con stride > 1 sbagliata al cambio di lotto (trovato da rocm-marconi): esclusi `ConvAsmBwdWrW1x1` e `ConvAsm1x1U` in `torch/__init__.py`, senza ricompilare. Controllo: con i solver riaccesi scarto 3,1, con la patch ~1e-07. `patch_conv1x1_stride.py` |
| MIOpen | 20 ott | MIOpen ricompilata con le tre patch di miopen-gfx906 (WrW3x3, V4R1, sotto-campionamento) e installata in `torch\lib` (B1, B4). `miopen_ricompila.cmd`, `miopen_rinomina_comgr.py` (in miopen-gfx906, `build\`) |
| 74 | 20 ott | cache MIOpen propria della ruota (`miopen_cache_ruota\cache` e `\db`): la chiave dei kernel non contiene il sorgente, e la cache condivisa con ZLUDA avrebbe riportato i kernel difettosi. `patch_miopen_cache_ruota.py` |
| 75 | 20 ott | spente le esclusioni 58, 62 e 72 (righe commentate): le tre correzioni verificate forzando i solver. `patch_togli_esclusioni_miopen.py` |
| 76 | 20 ott | `copy_` GPU→GPU di un tensore **trasposto** (ultime due dimensioni) con il kernel a tessere 64×64 di rocm-marconi, portato in `Copy.hip`: solo stesso tipo da 2/4 byte, stessa scheda, nessuna sovrapposizione, ≥ 1 MB, uno dei due contiguo e l'altro la trasposta di un contiguo; altrimenti il percorso di sempre. Fp16 4096×8192: 3,3 → 638 GB/s (194x); [1, 8192, 512]: 30 → 280 GB/s. Bit a bit identico, 25/25. `patch_copia_trasposta.py`, banco `prova_copia_trasposta.py` |
| 77 | 20 ott | un pacchetto esterno nell'ambiente, con i suoi vincoli; la variabile che aggiungeva in `torch/__init__.py` è stata tolta con la 85 |
| 78 | 20 ott | `eigh`/`eigvalsh` GPU **sbagliate da n=64** (hipSOLVER `syevj`) → `rocsolver_?syevd/?heevd_strided_batched`; `svd` GPU non ripetibile (hipSOLVER `gesvdj`) → `rocsolver_?gesvd_strided_batched`. Solo su ROCm senza MAGMA, in `hip/linalg/BatchLinearAlgebra.cpp`. 13/13 a tutte le dimensioni, 93/93. `patch_eigh_svd_rocsolver.py` |
| 80, 80b | 20 ott | `softmax`/`log_softmax` fp64, righe dispari 513-1021 (trovato da rocm-marconi, `softmax_fp64\diag_softmax.py`). In `SoftMax.hip` (`cunn_SoftMaxForward`, ramo non-smem, righe non allineate a 16 byte) il primo giro «un elemento per thread» presuppone riga + shift ≥ blocco: (80) mancava `threadIdx.x < size`; (80b) dopo `size -= blockDim.x` la size è negativa e `size % (ILP * blockDim.x)` si calcolava in **unsigned** (`blockDim.x`), così il ciclo di coda leggeva e scriveva **all'indietro**, nella riga precedente. Modulo con segno nei 3 punti. Banco `prova_softmax_righe.py` 13/13. `patch_softmax_fp64_righe_corte.py` |
| 81 | 20 ott | `eigh` e `svd` di tensori GPU calcolate con MKL sulla CPU (copie comprese), salvo la svd di lotti ≥ 32 di matrici con lato ≤ 32 (resta rocSOLVER `gesvd`, lì 2x più veloce). rocSOLVER su gfx906 era 20-114x più lento: svd 1000×96 209 → 3 ms, 2048² 68 → 0,6 s; eigh 1024² 1,66 s → 42 ms. Giuste e ripetibili. `patch_eigh_svd_su_cpu.py`, banco `banco_svd_cpu_gpu.py [--eigh]` |
| Tensile SS | 20 ott | da rocm-marconi: 7 voci fp32 «T N» per le forme fp32 di un'applicazione in `torch\lib\rocblas\library\TensileLibrary_Type_SS_Contraction_l_Alik_Bljk_Cijk_Dijk_gfx906.dat` (md5 EA860306; prima 33DA9FA5, con copia di sicurezza). mm [1256,1024]→512 −42%, addmm [8000,64]→64 −57%. Verificato: SGEMM su 9 forme 1,3e-6 contro fp64, l'applicazione 1,08 → 1,03 s (scarto 5,4e-6, risultati identici), regressione 17/17. Le GEMM fp16 non cambiano |
| 82 | 20 ott | caching allocator (`c10\hip\HIPCachingAllocator.cpp`, `round_size`): con `PYTORCH_RUOTA_ALLINEA_2MB=1` le richieste > 1 MB si arrotondano a multipli di 2 MB, quindi ogni blocco grande parte a 0 mod 2 MB (verificato). Motivo: rocm-marconi ha visto GEMM rocBLAS fp16 fino al 30% più lente con l'attivazione fra ~512 KB e 1,25 MB mod 2 MB. **Spenta di default**: nel banco di rocm-marconi (`diag_gemm\banco_allineamento.sh`) aiuta solo il passo base a 256 token (350 → 417 tok/s), mentre a 512 e 1024 e con i kernel Rocm perde 2-9%. Il riallineamento mirato di Rocm (`GEMM_ALLINEA`) resta la via giusta. `patch_allocatore_2mb.py` |
| 79 | 20 ott | `MIOPEN_USER_DB_PATH`: se è quella dell'epoca ZLUDA (`%LOCALAPPDATA%\miopen\db`, variabile utente), la ruota usa il suo db `miopen_cache_ruota\db`. In `torch/__init__.py`, senza ricompilare |

| 83 | 22 ott | `Fused{Adam,AdamW,Sgd}Kernel.hip` includono il proprio `ATen/ops/<op>_native.h`: gli ottimizzatori `fused=True` non saltano più a una voce d'import nulla (A3) |
| 84 | 22 ott | `FusedSgdKernel.hip`: indice `int64_t` invece di `auto` (in HIP `threadIdx.x` è un oggetto il cui `+=` non modifica nulla: ciclo infinito) |
| 85 | 10 nov | `torch/__init__.py` allineato alla wheel pubblicata: cache e db di MIOpen in `%LOCALAPPDATA%\2S\la-ruota\miopen\{cache,db}` (vincono `MIOPEN_CUSTOM_CACHE_DIR` e `MIOPEN_USER_DB_PATH` se impostate), commenti senza percorsi locali. Senza marcatore nel sorgente |

Lato MIOpen e ZLUDA: [miopen-gfx906](https://github.com/2s-2solution/miopen-gfx906),
`docs/MIOPEN_gfx906.md`.

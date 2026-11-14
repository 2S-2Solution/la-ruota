# La Ruota — PyTorch ROCm nativo su Windows per Radeon VII (gfx906)

**2S · 2Solution** · fork di [pytorch/pytorch](https://github.com/pytorch/pytorch) ·
[English below](#english)

> Il README originale di PyTorch è in [README-PyTorch.md](README-PyTorch.md).
> PyTorch è opera di Meta Platforms e dei suoi contributori (licenza BSD-3, [LICENSE](LICENSE)).

## Novità: La Ruota 2.15 (novembre 2026)

**PyTorch 2.15.0** per la Radeon VII, sul kit **ROCm 10.1** di AMD e con **MIOpen 3.6** corretta per
gfx906. Passa tutta la regressione di La Ruota (17 gruppi di prove contro la CPU) senza variabili
d'ambiente; MKL per la CPU; torchvision 0.30.0a0. Corregge due difetti di PyTorch su ROCm presenti
anche nella wheel di AMD (softmax fp64 a 32 bit sopra i 1024 elementi, lstsq che non segnala il rango
non pieno). Richiede il kit [rocm-marconi](https://github.com/2s-2solution/rocm-marconi) 2026.11.14
o successivo. Sorgenti, patch e istruzioni in [`la-ruota/2.15/`](la-ruota/2.15/LEGGIMI.md); il
pacchetto `la-ruota-gfx906-2.15-*.exe` è nella pagina Releases. La 2.5.1, descritta qui sotto,
resta disponibile e può convivere con la 2.15.

## Cosa fa

**La Ruota** è PyTorch **2.5.1** compilato **in modo nativo per ROCm su Windows** per la
AMD **Radeon VII** (Vega 20, **gfx906**), una scheda che AMD non supporta più su Windows e
per la quale non esistono wheel ufficiali. Niente traduzione CUDA→HIP a runtime (come con
ZLUDA): i kernel sono compilati per gfx906 e PyTorch chiama direttamente HIP, rocBLAS,
rocSOLVER e MIOpen. Sullo stesso carico è circa **5 volte più veloce** del percorso via
[zluda-gfx906](https://github.com/2s-2solution/zluda-gfx906).

A quanto ci risulta, al momento della costruzione (agosto 2026) non esisteva alcuna build
pubblica funzionante di PyTorch ROCm nativo su Windows per gfx906.

Il ramo `la-ruota-gfx906` parte dal tag **`v2.5.1`** (`a8d6afb511a69687bbb2b7e88a3cf67917e1697e`)
e contiene:

1. le modifiche ai sorgenti di PyTorch (CMake, ATen, c10, `torch/csrc`, `torch/__init__.py`),
   ciascuna marcata con un commento `VEGA-PATCH <n>` (fino alla 84; la 85, che allinea
   `torch/__init__.py` alla wheel pubblicata, non ha marcatore: il file è identico a quello
   della wheel);
2. **i file HIP generati da hipify e poi corretti a mano** (`aten/src/ATen/hip`,
   `aten/src/ATen/native/hip`, `c10/hip`, …): la build compila questi `.hip`, non i `.cu`,
   e su Windows hipify ha un difetto con i separatori di percorso che lo fa uscire con
   successo senza scrivere nulla. Sono inclusi così come sono stati compilati;
3. la cartella [`la-ruota/`](la-ruota/): guida, runbook di compilazione, script, banchi di
   regressione e i kernel gfx906 scritti a mano usati da `ruota_flash` e `ruota_acceleratori`.

## Hardware e software di prova

| | |
|---|---|
| GPU | AMD Radeon VII, 16 GB HBM2 (gfx906, wave64); fp32 e **fp16** — gfx906 non ha istruzioni bf16 |
| CPU | AMD Ryzen 9 5950X (per la parte CPU con MKL) |
| sistema | Windows 10/11, driver AMD Adrenalin (runtime HIP 5.7 in `System32\amdhip64.dll`) |
| toolchain (solo per compilare) | HIP SDK **5.7** per Windows + kit [rocm-marconi](https://github.com/2s-2solution/rocm-marconi) (clang 21, shim HIP); build di TheRock per gfx906; Visual Studio Build Tools 2022; CMake 3.31; Ninja; Python 3.12 |
| librerie | rocBLAS/rocSOLVER 5.7; **MIOpen 3.5.2** ricompilata con le patch di [miopen-gfx906](https://github.com/2s-2solution/miopen-gfx906); Intel MKL statico (CPU) |

## Risultati misurati

Banco unico `la-ruota/workspace/regressione_completa.py`, 22 ottobre 2026 (patch 83),
GPU libera; log completo in
[`regressione_completa_2026_10_22_p83.log`](la-ruota/workspace/regressione_completa_2026_10_22_p83.log):

| banco | esito |
|---|---|
| GEMM fp16 | **10,96 TFLOPS** |
| convoluzioni MIOpen (9 prove), CNN 5 passi | tutte corrette; pesi uguali alla CPU entro 1,2·10⁻⁷ |
| reti ricorrenti, 13 varianti; LSTM all'indietro ripetuti | 13 / 13; 7 / 7 |
| RNN multistrato in MIOpen (LSTM 2×256, lotto 32, 64 passi) | 10 / 10, **12,6 ms contro 62,3 ms** del percorso nativo (4,93x) |
| censimento delle operazioni GPU | **98 / 98** |
| algebra lineare su tensori GPU (rocSOLVER; `eigh` e `svd` su MKL CPU, VEGA-PATCH 81) | 20 / 20; cholesky e lstsq 63 / 63; eigh e svd 93 / 93; n da 16 a 512: 13 / 13 |
| softmax / log_softmax, 3 tipi, avanti e indietro | 13 / 13 |
| stream ed eventi multipli; `torch.cuda` in TorchScript | 9 / 9; 2 / 2 |
| CPU con MKL, LAPACK, numpy 2 | 21 / 21; matmul fp32 4096 a 317 GFLOPS |
| flash attention (B2 H16 S2048 D128 causale, avanti+indietro) | 11 / 11; **25,5 ms / 146 MB contro 49,6 ms / 2.162 MB** (1,94x) |
| conv 1×1 con stride al cambio di lotto | corretta (scarto ≤ 1,7·10⁻⁷) |

Altri numeri dal diario di lavoro: LoRA fp16 su Qwen3.5-4B a 1024 token da 182 a **562
token/s** con `ruota_acceleratori` (Gated DeltaNet e flash attention gfx906); `copy_`
trasposto fp16 4096×8192 da 3,3 a **638 GB/s**, identico bit a bit.

## Requisiti a runtime

Per **usare** La Ruota (dal pacchetto della pagina Releases) servono solo:

| | provato |
|---|---|
| GPU | AMD Radeon VII (gfx906): è l'unica provata |
| sistema | Windows 10 Pro 22H2 (build 19045), 64 bit |
| driver | AMD Software 25.Q3 (31.0.21923.11000), che fornisce `System32\amdhip64.dll`. Non è incluso |
| Python | 3.12 a 64 bit (la wheel è solo per 3.12) |
| VC++ | Microsoft Visual C++ Redistributable 2015-2022 x64 |

**Non** servono ZLUDA, il kit rocm-marconi, l'HIP SDK né ROCm 7.1: la wheel porta in
`torch\lib` le librerie ROCm 5.7, MIOpen corretta, hipRTC e COMgr di ROCm 7.1 e gli shim.
I sorgenti degli shim sono pubblici: `hiprtc07013.dll` e `amd_cmgr3.dll` in
[miopen-gfx906/shim](https://github.com/2s-2solution/miopen-gfx906/tree/main/shim),
`amdhip64_7.dll` in [rocm-marconi](https://github.com/2s-2solution/rocm-marconi)
(`runtime/src/shim_main.c`).

### Da dove vengono le DLL di `torch\lib`

La wheel è autosufficiente: come la wheel ufficiale porta cuDNN, questa porta MIOpen e le
librerie ROCm. Questo repository contiene solo PyTorch; le altre DLL vengono da qui:

| DLL in `torch\lib` | origine |
|---|---|
| `torch_*.dll`, `c10*.dll`, `caffe2_nvrtc.dll`, `shm.dll`, `torch.dll` | questo repository (build di PyTorch) |
| `MIOpen.dll`, `hiprtc07013.dll`, `amd_cmgr3.dll` | [miopen-gfx906](https://github.com/2s-2solution/miopen-gfx906): MIOpen 3.5.2 con le patch e i due shim |
| `hiprtc0701.dll`, `hiprtc-builtins0701.dll`, `amd_comgr0701.dll`, `amd_comgr_3.dll` | ROCm 7.1 di AMD, file identici (servono agli shim di miopen-gfx906) |
| `amdhip64_7.dll`, `hipblaslt.dll`, `libhipblaslt.dll`, `hiprtc-builtins07013.dll` | [rocm-marconi](https://github.com/2s-2solution/rocm-marconi): shim HIP con il ponte sullo stream nullo, hipBLASLt |
| `rocblas.dll` e `rocblas\library\`, `rocsolver.dll`, `rocsparse.dll`, `rocfft.dll`, `hipblas.dll`, `hipfft.dll`, `hipsolver.dll`, `libhipsparse.dll`, `hiprtc0507.dll`, `amd_comgr0507.dll` | HIP SDK 5.7 di AMD; alcuni file della libreria Tensile sono instradati per gfx906 (guida, B1) |
| `uv.dll` | libuv (MIT), costruita da `la-ruota/workspace/costruisci_libuv.cmd` |
| `libiomp5md.dll` | non inclusa: la installa pip dal pacchetto `intel-openmp` |

Il runtime HIP (`amdhip64.dll`) è quello del driver e non è incluso.

## Installazione rapida

Per installare senza compilare, scaricare il pacchetto autoestraente dalla pagina
**[Releases](https://github.com/2s-2solution/la-ruota/releases)** e verificarne lo SHA256
pubblicato accanto. I pacchetti binari non sono nel repository git.

## Compilare da sorgente

La build **non è portabile così com'è**: gli script e alcuni file CMake del ramo
(`cmake/public/LoadHIP.cmake`, `cmake/Dependencies.cmake`, `cmake/Modules/Findmiopen.cmake`,
`CMakeLists.txt`, `la-ruota/workspace/build_laruota_canonical.cmd`) contengono i percorsi
della macchina di costruzione. Il modo più semplice è riprodurli identici; altrimenti vanno
cambiati in quei file.

Prerequisiti, tutti da preparare **prima** della build:

| cosa | dove la cercano gli script | come si ottiene |
|---|---|---|
| HIP SDK 5.7 per Windows | `C:\Program Files\AMD\ROCm\5.7` | installatore AMD |
| kit [rocm-marconi](https://github.com/2s-2solution/rocm-marconi) (clang 21, shim HIP) | `C:\rocm_5_7_expansion_pack` | dal suo repository |
| ritocchi manuali al kit | `include\hip\hip_version.h` e `include\miopen\` | **VEGA-PATCH 28**: in `hip_version.h` `HIP_VERSION_MAJOR` 5→6 e `HIP_VERSION_MINOR` 7→4 (altrimenti gli header di hipBLASLt 7.x ridefiniscono i tipi); gli header di MIOpen li copia lo STEP 2 di `build_laruota_canonical.cmd` dall'albero di TheRock |
| build di [TheRock](https://github.com/ROCm/TheRock) per gfx906 | `C:\TheRock_workspace\TheRock\build_gfx906` | serve per `dist\rocm` (hipBLASLt e hipblas-common 7.x, header BLAS) e per `artifacts\miopen_run_generic\ml-libs\MIOpen\stage` (header e import di MIOpen); MIOpen con le patch di [miopen-gfx906](https://github.com/2s-2solution/miopen-gfx906) |
| libuv | `C:\LaRuota_workspace\libuv_install` (`libuv_ROOT`) | `la-ruota\workspace\costruisci_libuv.cmd`, dai sorgenti già nei sottomoduli. Senza, CMake spegne `USE_DISTRIBUTED` senza chiedere |
| MKL statico | `C:\LaRuota_workspace\mkl_prefix` | `pip install --prefix C:\LaRuota_workspace\mkl_prefix mkl-static mkl-include intel-openmp` (VEGA-PATCH 65; solo statico) |
| header di numpy 2 | `C:\LaRuota_workspace\numpy2_headers` | `pip install --target C:\LaRuota_workspace\numpy2_headers numpy==2.2.6` (VEGA-PATCH 65: `torch_python` contro numpy 2 regge 1.x e 2.x) |
| strumenti | | Visual Studio Build Tools 2022 (x64), CMake 3.31, Ninja, Python 3.12 |

Poi:

```bat
mkdir C:\LaRuota_workspace
git clone -b la-ruota-gfx906 https://github.com/2s-2solution/la-ruota C:\LaRuota_workspace\pytorch_src
cd C:\LaRuota_workspace\pytorch_src
git submodule update --init --recursive
cd third_party\kineto && git apply ..\..\la-ruota\patches\kineto-hip-platform-amd.patch && cd ..\..
:: script e banchi nella cartella di lavoro
xcopy /E /I la-ruota\workspace C:\LaRuota_workspace
:: ambiente Python di build e compilazione (ore, non minuti)
py -3.12 -m venv C:\LaRuota_workspace\venv_build
C:\LaRuota_workspace\venv_build\Scripts\pip install -r requirements.txt -c C:\LaRuota_workspace\vincoli_ruota.txt
C:\LaRuota_workspace\build_laruota_canonical.cmd verify
C:\LaRuota_workspace\build_laruota_canonical.cmd build
```

`setup.py` non copia le DLL di runtime che la build non produce. Le copia
`deploy_runtime_dlls.py`, che ne controlla l'impronta: MIOpen e i suoi shim dal pacchetto
di miopen-gfx906, le librerie di ROCm 5.7, `amdhip64_7.dll` e hipBLASLt dal kit,
`uv.dll` e `libiomp5md.dll`:

```bat
C:\LaRuota_workspace\venv_build\Scripts\python.exe C:\LaRuota_workspace\deploy_runtime_dlls.py ^
  --torch-lib C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib ^
  --miopen <cartella bin del pacchetto miopen-gfx906> ^
  --libuv C:\LaRuota_workspace\libuv_install --mkl C:\LaRuota_workspace\mkl_prefix\Library\bin
:: verifica
C:\LaRuota_workspace\venv_build\Scripts\python.exe C:\LaRuota_workspace\regressione_completa.py
```

Cosa deve stare in `torch\lib`, e perché, è nella guida (sezione B1). La guida completa è in
[la-ruota/docs/GUIDA_LA_RUOTA.md](la-ruota/docs/GUIDA_LA_RUOTA.md) (uso, regole, difetti
noti, ricompilazione, banchi, cronologia delle patch). Il runbook in `la-ruota/docs/`
(`BUILD_LARUOTA_RUNBOOK.md`) è **storico** (giugno-luglio 2026): descrive strade poi abbandonate.

Uso:

```python
import torch
print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))
# 2.5.0+gita8d6afb True AMD Radeon VII
```

La ruota si presenta come CUDA («masquerading»): si usa `device="cuda"`, e per riconoscere
la GPU si usa `torch.cuda.is_available()`, non `torch.version.hip`.

## Limiti noti

- **Solo gfx906**, provata su una sola scheda. Niente bf16 in hardware: usare fp16
  (autocast).
- Niente `torch.compile`/Triton, niente aotriton; la flash attention gfx906 è collegata a
  `sdpa` solo su richiesta (`ruota_flash.attiva()`) e copre fp16 con head dim fino a 256.
- `torch.distributed` esiste (Gloo) ma senza RCCL/NCCL; niente Kineto (profiler GPU
  limitato a quanto attivato dalla patch 68), niente MKLDNN, FBGEMM, XNNPACK.
- Lo stream nullo del driver Adrenalin non sa attendere un evento: aggirato con un ponte su
  uno stream bloccante (la CPU attende ~0,1 ms).
- torchvision 0.20 compilato a parte con operazioni proprie solo su CPU (deform_conv2d GPU
  via `ruota_acceleratori`).
- I tempi valgono a GPU libera; con altri processi sulla stessa scheda calano.
- Gli script di build e molti banchi contengono percorsi assoluti della macchina di
  costruzione (`C:\LaRuota_workspace`, `C:\rocm_5_7_expansion_pack`, `C:\TheRock_workspace`):
  vedi «Compilare da sorgente». La wheel installata non ne dipende.

## Licenza

**BSD-3-Clause**, come PyTorch ([LICENSE](LICENSE), [NOTICE](NOTICE)). Le modifiche e i
file della cartella `la-ruota/` sono © 2026 2 Solution e distribuiti alle stesse condizioni:
vedi [la-ruota/NOTICE](la-ruota/NOTICE).

---

<a name="english"></a>
# English

**New: La Ruota 2.15 (November 2026)** — **PyTorch 2.15.0** for the Radeon VII on AMD's **ROCm 10.1**
kit with **MIOpen 3.6** fixed for gfx906. It passes La Ruota's whole regression (17 test groups
against the CPU) with no environment variables; MKL on the CPU; torchvision 0.30.0a0. It fixes two
PyTorch-on-ROCm bugs also present in AMD's wheel (fp64 softmax computed with a 32-bit exp above 1024
elements; lstsq not reporting rank deficiency). Requires the
[rocm-marconi](https://github.com/2s-2solution/rocm-marconi) kit 2026.11.14 or later. Sources,
patches and instructions in [`la-ruota/2.15/`](la-ruota/2.15/LEGGIMI.md); the
`la-ruota-gfx906-2.15-*.exe` package is on the Releases page. The 2.5.1 build described below is
still available and can coexist with 2.15.

**La Ruota** ("the wheel") is **PyTorch 2.5.1 built natively for ROCm on Windows** for the
AMD **Radeon VII (gfx906)**, a card AMD no longer supports on Windows and for which no
official wheels exist. No CUDA→HIP translation at runtime: kernels are compiled for gfx906
and PyTorch calls HIP, rocBLAS, rocSOLVER and MIOpen directly — about **5× faster** than the
ZLUDA route ([zluda-gfx906](https://github.com/2s-2solution/zluda-gfx906)). To our knowledge
no working public native ROCm-on-Windows build for gfx906 existed when it was made
(August 2026).

Branch `la-ruota-gfx906` starts at tag **`v2.5.1`** (`a8d6afb`) and contains the source
changes (marked `VEGA-PATCH <n>`, up to 84; patch 85, which aligns `torch/__init__.py` with the
published wheel, has no marker), the hipified HIP sources as actually compiled
(Windows hipify silently writes nothing because of a path-separator bug, and the build
compiles the `.hip` files, so they are committed with their hand fixes), and the
[`la-ruota/`](la-ruota/) folder with the guide (Italian), build runbook, scripts, regression
benches and hand-written gfx906 kernels (flash attention, Gated DeltaNet, fused norms, LoRA,
loss, GEMM routing, tiled transpose).

**Measured (22 Oct 2026, single Radeon VII, idle GPU):** fp16 GEMM 10.96 TFLOPS; all MIOpen
convolution tests pass, 5-step CNN within 1.2e-7 of CPU; RNN 13/13, multilayer LSTM in MIOpen
4.93× faster than the native path; GPU op census 98/98; GPU linear algebra 20/20,
cholesky/lstsq 63/63, eigh/svd 93/93 (computed with MKL on the CPU since patch 81); softmax 13/13; streams/events 9/9; TorchScript 2/2;
MKL/LAPACK/numpy 2 21/21 (CPU matmul 317 GFLOPS); flash attention 1.94× faster with
146 MB instead of 2,162 MB; LoRA fp16 on Qwen3.5-4B 182 → 562 tokens/s.

**Runtime requirements:** Radeon VII (gfx906, the only card tested), Windows 10 22H2 64-bit,
AMD Software 25.Q3 driver (`System32\amdhip64.dll`), Python 3.12 64-bit, VC++ 2015-2022 x64
redistributable. ZLUDA, rocm-marconi, the HIP SDK and ROCm 7.1 are **not** needed: the wheel
ships the ROCm 5.7 libraries, the fixed MIOpen, ROCm 7.1 hipRTC/COMgr and the shims in
`torch\lib`. Shim sources: `hiprtc07013.dll` and `amd_cmgr3.dll` in miopen-gfx906 (`shim/`),
`amdhip64_7.dll` in rocm-marconi (`runtime/src/shim_main.c`).

**Where the `torch\lib` DLLs come from:** PyTorch from this repository; `MIOpen.dll`,
`hiprtc07013.dll` and `amd_cmgr3.dll` from miopen-gfx906 (with ROCm 7.1's hipRTC and COMgr DLLs,
unchanged); `amdhip64_7.dll` and hipBLASLt from rocm-marconi; rocBLAS, rocSOLVER, rocSPARSE,
rocFFT and the hip* wrappers from the HIP SDK 5.7; `uv.dll` from libuv; `libiomp5md.dll` from the
`intel-openmp` pip package. The HIP runtime is the driver's and is not included.

**Quick install:** download the self-extracting package from the
**[Releases](https://github.com/2s-2solution/la-ruota/releases)** page and check its published
SHA256. Binary packages are not stored in git.

**Build (not portable as is):** the build scripts and some CMake files of this branch hard-code
the build machine's paths. Prerequisites: HIP SDK 5.7; rocm-marconi in
`C:\rocm_5_7_expansion_pack`, with `include\hip\hip_version.h` bumped to 6.4 by hand (patch 28);
a TheRock build for gfx906 in `C:\TheRock_workspace\TheRock\build_gfx906` (hipBLASLt 7.x and
MIOpen headers); libuv built with `costruisci_libuv.cmd`; static MKL via
`pip install --prefix C:\LaRuota_workspace\mkl_prefix mkl-static mkl-include intel-openmp`;
numpy 2.2.6 headers via `pip install --target C:\LaRuota_workspace\numpy2_headers numpy==2.2.6`;
VS Build Tools 2022, CMake 3.31, Ninja, Python 3.12. Then clone this branch to
`C:\LaRuota_workspace\pytorch_src`, apply `la-ruota/patches/kineto-hip-platform-amd.patch`, copy
`la-ruota/workspace` to `C:\LaRuota_workspace`, run `build_laruota_canonical.cmd build`, copy the
runtime DLLs with `deploy_runtime_dlls.py` and check with `regressione_completa.py` (commands
above). The runbook in `la-ruota/docs/` is historical.

**Known limits:** gfx906 only, tested on one card; no bf16 hardware (use fp16); no
`torch.compile`/Triton/aotriton; Gloo-only distributed, no Kineto/MKLDNN/FBGEMM/XNNPACK;
the Adrenalin null stream cannot wait on events (worked around); scripts use absolute paths
of the build machine.

**License:** BSD-3-Clause, same as PyTorch. Changes © 2026 2 Solution, same terms; see
[la-ruota/NOTICE](la-ruota/NOTICE).

# La Ruota 2.15 — PyTorch 2.15.0 ROCm nativo per Radeon VII (gfx906) su Windows

**2S · 2Solution** · novembre 2026

La Ruota 2.15 è PyTorch **2.15.0** compilato per la **AMD Radeon VII (gfx906)** su Windows con il
kit **ROCm 10.1** di AMD (TheRock), con **MIOpen 3.6** corretta per gfx906. Il pacchetto di
installazione è nella pagina **Releases** (`la-ruota-gfx906-2.15-AAAA.MM.GG.exe`): questa cartella
contiene i sorgenti di quello che il pacchetto porta.

## Come è fatta

A differenza della 2.5, qui PyTorch non ha bisogno di quasi nessuna modifica: dalla 2.15 il supporto
ROCm su Windows è a monte (`USE_ROCM` su WIN32, LoadHIP con i rami Windows, hipify funzionante), e il
kit di sviluppo ROCm 10.1 si installa con pip (`rocm-sdk-devel`). Restano:

| pezzo | da dove | cosa fa La Ruota |
|---|---|---|
| PyTorch | tag `v2.15.0` (commit `31a77fc`) | 2 patch ([patches/](patches/)), build con MKL e code object V5 |
| librerie ROCm 10.1 | wheel nightly di AMD `10.1.0a20260822` (`rocm.nightlies.amd.com/whl-multi-arch`) | nessuna modifica; si scaricano all'installazione |
| runtime HIP | driver Adrenalin (runtime 5.7) | lo shim `amdhip64_7.dll` del kit [rocm-marconi](https://github.com/2s-2solution/rocm-marconi) offre le API di HIP 7 sopra il driver |
| MIOpen | 3.6.0, rocm-libraries `416eae89` (lo stesso commit della nightly) | 5 patch, nel repository [miopen-gfx906](https://github.com/2s-2solution/miopen-gfx906) |
| torchvision | ramo principale (0.30.0a0, commit `4260301`) | compilata contro questa torch |

## Le due patch di PyTorch

- **[0001](patches/0001-ROCm-softmax-exp-a-64-bit-per-fp64-dim-1024.patch) — softmax fp64.** In
  `aten/src/ATen/native/cuda/SoftMax.cu`, nel ramo `USE_ROCM`, per righe di più di 1024 elementi
  `SumExpfFloat` e `SoftMaxForwardWithMulEpilogue` usano `__expf`, l'esponenziale a 32 bit, anche
  quando l'accumulatore è `double`. Il softmax fp64 sbaglia di ~2e-6 relativo per elemento e la somma
  resta 1, quindi nessun controllo se ne accorge. Con accumulatore `double` ora si usa `std::exp`.
  Il difetto c'è anche nella wheel di AMD.
- **[0002](patches/0002-lstsq-gels-su-GPU-rango-non-pieno-segnalato-in-infos.patch) — lstsq.**
  `linalg_lstsq_gels` (QR più triangolare, il ramo della matrice singola) non scrive mai `infos`: con
  una matrice a rango non pieno la GPU restituisce inf/nan senza errore, mentre la CPU e il ramo in
  lotto sollevano `LinAlgError`. Ora `infos` riceve l'indice del primo zero sulla diagonale di R, come
  fa LAPACK `?trtrs`, e l'errore sale come sulla CPU, senza sincronizzazioni in più.

Le patch toccano i sorgenti `cuda/`; dopo hipify vanno applicate anche alle copie `hip/` generate
(oppure si lancia hipify dopo averle applicate).

## Compilare

Servono Visual Studio 2022 Build Tools, Python 3.12, Git, e circa 3 ore con 8 compilazioni in
parallelo su 32 GB di RAM.

1. Sorgenti: `git clone --branch v2.15.0 --recurse-submodules https://github.com/pytorch/pytorch`,
   poi `python tools/amd_build/build_amd.py` (hipify) e le due patch.
2. Venv di build con Python 3.12: le wheel ROCm `10.1.0a20260822` dall'indice AMD (`rocm`,
   `rocm-sdk-core`, `rocm-sdk-libraries`, `rocm-sdk-device-gfx906`, `rocm-sdk-devel`), poi
   `python -m rocm_sdk path --root` per srotolare il kit; da PyPI `mkl-static==2026.2.0`,
   `mkl-include==2026.2.0`, `intel-openmp==2026.2.0`, `cmake<4.3`, `ninja==1.13.0`,
   `scikit-build-core`, `numpy==2.2.6` e i requisiti di `requirements-build.txt`.
3. `set LARUOTA_PT=<sorgenti>` e `build\esegui_msvc.cmd <python del venv> build\costruisci_215.py`.
   Lo script svuota `HIP_PATH` e `ROCM_PATH` (un ROCm installato porterebbe header sbagliati), usa il
   clang del kit, `HIPFLAGS=-mcode-object-version=5`, `BLAS=MKL` e, con CMake 4, spegne la scansione
   dei moduli C++ e il modulo di fmt (`CMAKE_CXX_SCAN_FOR_MODULES=OFF`, `FMT_MODULE=OFF`).
4. `build\ripulisci_wheel.py <wheel> <wheel ripulita>` toglie Intel OpenMP dalla wheel (non si
   ridistribuisce: arriva da PyPI con `intel-openmp`) e il percorso della cartella temporanea di
   build dai file CMake.
5. torchvision: installare la torch nel venv di build, `set LARUOTA_VISION_SRC=<sorgenti>`,
   `build\esegui_msvc.cmd <python> build\costruisci_vision.py`. Con ninja nel PATH: senza,
   `cpp_extension` passa a hipcc i percorsi di Visual Studio non quotati.

## Installatore

[installatore/](installatore/) contiene gli script del pacchetto. `installa.ps1` crea un venv,
scarica le librerie ROCm da AMD, installa le wheel di La Ruota, mette lo shim di Marconi e la MIOpen
3.6 al posto dei file corrispondenti delle wheel AMD e scrive i percorsi di MIOpen in un `.pth` del
solo ambiente di La Ruota. `verifica.py` confronta GPU e CPU (matmul, conv RGB, LSTM a 2 strati,
softmax fp64, lstsq, MKL, compilazione MIOpen).

## Risultati misurati

Radeon VII, Windows 10 22H2, driver Adrenalin 25.Q3, 14 novembre 2026:

| | La Ruota 2.15 | wheel AMD 2.15 (stesse librerie ROCm, stesso shim) |
|---|---|---|
| regressione di La Ruota, 17 gruppi di prove contro la CPU | **17/17**, senza variabili d'ambiente | 15/17 senza correzioni; 17/17 solo con 7 variabili MIOpen e correzioni esterne |
| GEMM fp16 sulla GPU | 11,0 TFLOPS | 10,7 TFLOPS |
| matmul fp32 sulla CPU (4096) | 800-900 GFLOPS (MKL) | 14 GFLOPS (OpenBLAS a un thread) |
| code object | V5, caricati dal driver così come sono | V6 in kpack, convertiti dallo shim |

`prova_torchvision.py`: nms, roi_align, deform_conv2d e ResNet-18 sulla GPU uguali alla CPU.

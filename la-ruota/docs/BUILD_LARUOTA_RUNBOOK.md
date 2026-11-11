# BUILD LA RUOTA — Runbook canonico Vega gfx906 Windows

> **Documento storico (giugno-luglio 2026).** Descrive una fase della costruzione poi superata (strade,
> versioni e percorsi non più validi). Lo stato attuale è nel [README](../../README.md) e nella
> [guida](GUIDA_LA_RUOTA.md).

**Scopo**: documentazione esaustiva di TUTTI i fix necessari per buildare PyTorch ROCm nativo Windows su Vega 20 (gfx906) usando Marconi Expansion Pack 5.7. Aggiornato 22 giu 2026 T16:45.

**Regola d'oro**: tutti i fix in 5 categorie distinte. Categoria A+B sono persistenti in `pytorch_src/`. Categoria C+D+E vanno ricostruiti ogni volta tramite `build_laruota_canonical.cmd` (idempotente).

---

## Categoria A — CMake source patches (PERMANENTI in pytorch_src/)

| # | File | Linea | Cosa fa | Data |
|---|---|---|---|---|
| 1 | `CMakeLists.txt` | 896 | Disable aotriton FlashAttention/MemEff per gfx906 | 18 giu |
| 2 v3 | `CMakeLists.txt` | 248 | `set(... FORCE)` override option() cache | 20 giu |
| 4 | `cmake/public/LoadHIP.cmake` | 62 | HIP_FOUND fix quando hip-config esiste ma find_package fail | 18 giu |
| 4b | `cmake/public/LoadHIP.cmake` | 70-72 | Marconi pack detection via include/hip path | 20 giu |
| 5 | `cmake/public/LoadHIP.cmake` | 144-158 | ROCM_VERSION/HIP_VERSION fallback 6.4.1 | 18 giu |
| 5b | `cmake/public/LoadHIP.cmake` | 129 | Skip REGEX se RAW vuoto (try_run Windows fail) | 18 giu |
| 6 | `cmake/Modules/Findhsa-runtime64.cmake` | tutto | Stub Windows ROCm | 18 giu |
| 7 | `cmake/Modules/Findamd_comgr.cmake` | tutto | Stub Windows ROCm | 18 giu |
| **8** | `cmake/Modules/Findmiopen.cmake` | 6 | Stub Windows; **path corretto `dev_generic` → `run_generic` 22 giu T16:38** | 18→22 giu |
| 9 | `cmake/public/LoadHIP.cmake` | 43 | Macro legacy FindHIP non disponibile ROCm 6.x | 18 giu |
| 10 | `cmake/public/LoadHIP.cmake` | 245-248 | ROCM_ROCTX_LIB empty (roctx64 non distribuito Windows 6.4) | 18 giu |
| 11 | `cmake/Dependencies.cmake` | 1054 | Strip flag GCC-style non riconosciuti da MSVC cl.exe | 18 giu |
| 12 | `c10/hip/CMakeLists.txt` | 40 | Force include shim MSVC builtins | 18 giu |
| 12b | `c10/hip/CMakeLists.txt` | 43 | Escludo clang-cl (ha già builtin GCC) | 20 giu |
| **23** | `aten/src/ATen/hip/EmptyTensor.h` | 43-66 | **22 giu T16:12**: 6 aliases empty_cuda → empty_hip (codegen RegisterCUDA.cpp non-hipified) | 22 giu |

## Categoria B — C++ source patches (PERMANENTI in pytorch_src/)

| File | Linea | Cosa fa |
|---|---|---|
| `aten/src/ATen/hip/HIPContextLight.h` | 2 | `TORCH_HIP_CPP_API` alias di `TORCH_CUDA_CPP_API` |
| `aten/src/ATen/hip/impl/HIPStreamMasqueradingAsCUDA.h` | 94 | Clang-cl 21 strict warning fix |
| `torch/csrc/jit/runtime/static/native_ops.cpp` | 1057 | ForkedSubgraphSRLauncher senza TORCH_API (anonymous namespace) |
| `aten/src/ATen/hip/impl/HIPGraphsC10Utils.h` | hipify | Patch `at::cuda` → `at::hip` (build #22) |
| `caffe2/operators/...` | various | next_pot constexpr clang-cl21 fix (Marconi pack) |
| `torch/csrc/jit/...` | wmkstemps/exec | Static linkage fix |
| `setup.py distutils` | various | `/MANIFEST:NO` linker flag |

## Categoria C — Build environment (FRAGILI: ricreare ogni configure)

Setup.py legge USE_* da env vars `USE_<NAME>=0`. **Lista esaustiva**:

```cmd
:: =========== USE FLAGS (=0 disable, =1 enable) ===========
set "USE_ROCM=1"
set "USE_CUDA=0"
set "USE_DISTRIBUTED=0"
set "USE_FLASH_ATTENTION=0"
set "USE_MEM_EFF_ATTENTION=0"
set "USE_KINETO=0"
set "USE_TENSORPIPE=0"
set "USE_XNNPACK=0"
set "USE_GFLAGS=0"
set "USE_GLOG=0"
set "USE_MKLDNN=0"
set "USE_NNPACK=0"
set "USE_QNNPACK=0"
set "USE_FBGEMM=0"
set "BUILD_TEST=0"

:: =========== PATH ENV VARS ===========
set "HIP_PATH=C:\Program Files\AMD\ROCm\6.4"
set "ROCM_PATH=C:\rocm_5_7_expansion_pack"
set "ROCM_SOURCE_DIR=C:\rocm_5_7_expansion_pack"
set "ROCM_HOME=C:\rocm_5_7_expansion_pack"

:: =========== INCLUDE PATHS ===========
set "CXXFLAGS=-IC:\rocm_5_7_expansion_pack\include -IC:/TheRock_workspace/TheRock/build_gfx906/artifacts/miopen_run_generic/ml-libs/MIOpen/stage/include"

:: =========== PYTORCH BUILD VARS ===========
set "MAX_JOBS=4"
set "PYTORCH_ROCM_ARCH=gfx906"

:: =========== TOOL PATHS (PATH override) ===========
set "PATH=C:\rocm_5_7_expansion_pack\compiler\bin;C:\rocm_5_7_expansion_pack\bin;%PATH%"
```

## Categoria D — Filesystem artifacts (FRAGILI: ricreare se rm build/)

1. **Junction** `build/aten/src/ATen/hip` → `aten/src/ATen/hip`
   - Comando: `New-Item -ItemType Junction -Path 'build\aten\src\ATen\hip' -Target 'aten\src\ATen\hip'`
   - Necessaria per HIPDevice.h not found (build #22-#23 fix T15:11)

2. **MIOpen header copy** in 2 path:
   - `C:\rocm_5_7_expansion_pack\include\miopen\*.h` (5 files: miopen.h, config.h, export.h, export_internals.h, version.h)
   - Source: `C:\TheRock_workspace\TheRock\build_gfx906\artifacts\miopen_run_generic\ml-libs\MIOpen\stage\include\miopen\*`

3. **Cleanup CMakeCache stale** SOLO se richiesto fresh configure:
   - `del build\CMakeCache.txt`
   - ⚠️ Se cancellato, **devi rilanciare con TUTTE le env vars Categoria C** altrimenti perdi configurazione

## Categoria E — Setup.py args (PASSATI come argomenti CLI)

```cmd
python setup.py install --cmake-only ::: per generare solo CMake files
python setup.py install              ::: per build completa
python setup.py bdist_wheel          ::: per produrre wheel solo
```

---

## Bug noti emersi & fixati (cronologia 18-22 giu)

| Data | Bug | Fix | Stato |
|---|---|---|---|
| 18 giu | HIP_FOUND non settato Windows | VEGA-PATCH 4+4b | ✅ Permanente |
| 18 giu | ROCM_VERSION parsing fail | VEGA-PATCH 5+5b | ✅ Permanente |
| 18 giu | hsa-runtime64/amd_comgr/miopen findpackage fail | VEGA-PATCH 6+7+8 | ✅ Permanente |
| 18 giu | FindHIP legacy ROCm 6.x | VEGA-PATCH 9 | ✅ Permanente |
| 18 giu | roctx64 not distributed | VEGA-PATCH 10 | ✅ Permanente |
| 18 giu | MSVC cl.exe rifiuta flag GCC | VEGA-PATCH 11+12 | ✅ Permanente |
| 18 giu | aotriton non supporta gfx906 | VEGA-PATCH 1+2 | ✅ Permanente |
| 19 giu | ForkedSubgraphSRLauncher TORCH_API+anonymous ns | VEGA-FIX native_ops.cpp | ✅ Permanente |
| 20 giu | HIPStreamMasqueradingAsCUDA clang-cl21 strict | VEGA-FIX | ✅ Permanente |
| 20 giu | next_pot constexpr clang-cl21 (Marconi) | Patch caffe2 | ✅ Permanente |
| 20 giu | wmkstemps/exec/activate static linkage | Patch | ✅ Permanente |
| 20 giu | `/MANIFEST:NO` linker flag | Patch distutils | ✅ Permanente |
| 22 giu T15:11 | HIPDevice.h not found build/ tree | Junction | ⚠️ Categoria D, ricreare |
| **22 giu T16:12** | `at::detail::empty_cuda` codegen mismatch | **VEGA-PATCH 23** EmptyTensor.h | ✅ Permanente |
| **22 giu T16:38** | Findmiopen.cmake path `dev_generic` errato | Corretto in `run_generic` | ✅ Permanente (sotto VEGA-PATCH 8) |
| **22 giu T16:38** | `ROCM_SOURCE_DIR` env mancante → `\opt\rocm` su Windows | env var | ⚠️ Categoria C |
| **22 giu T16:38** | MIOpen header non in path include compile | Copy + CXXFLAGS | ⚠️ Categoria C+D |
| **22 giu T17:05** | `c10/hip/HIPAllocatorConfig.cpp` C3615 + C2146 — MSVC cl.exe non ha `__builtin_clz` constexpr + non capisce `__attribute__((vector_size))` | VEGA-PATCH 12c (constexpr loop shim) + **VEGA-PATCH 24 (force clang-cl global)** | ✅ Permanente (12c) + ⚠️ Categoria C (24) |
| **22 giu T17:30** | `c10/hip/HIPMallocAsyncAllocator.cpp:185,805` clang-cl error — `hipStreamWaitEvent(stream, event)` 2-arg, ROCm 6.4 richiede 3-arg `(stream, event, flags)` | **VEGA-PATCH 26**: aggiunto `, 0` come flags. Altre 2 occorrenze in `HIPGuardImpl.h` + `HIPGuardImplMasqueradingAsCUDA.h` GIA' 3-arg, OK | ✅ Permanente |
| **22 giu T19:00** | `hipblaslt.h:63` typedef redefinition `hipblasComputeType_t` — conflict hipblaslt vs hipblas-common ROCm 6.4 | **VEGA-PATCH 27**: rimosso `-IC:\rocm_5_7_expansion_pack\include` da CXXFLAGS (NON sufficiente — clang-cl Marconi pack include implicit). | ⚠️ Categoria C |
| **22 giu T21:30** | Stesso typedef redefinition persiste anche post-PATCH 27 | **VEGA-PATCH 28**: modifica diretta `C:\rocm_5_7_expansion_pack\include\hip\hip_version.h`: `HIP_VERSION_MAJOR 5→6`, `MINOR 7→4`. Marconi pack è 5.7 nativo ma layer-mix simula 6.4 (rocBLAS 7.14 + amdhip64 6.4) → bump version skip legacy hipblaslt typedef branch | ⚠️ Categoria D (filesystem patch) |
| **22 giu T21:32** | `EmptyTensor.h:38` `unknown type name 'TORCH_HIP_CPP_API'` + `'TensorBase' must use 'class' tag` — header non self-sufficient | **VEGA-PATCH 29**: aggiunto `#include <c10/macros/Export.h>` + `#ifndef TORCH_HIP_CPP_API #define TORCH_HIP_CPP_API TORCH_CUDA_CPP_API #endif` in EmptyTensor.h. Macro era definita solo in HIPContextLight.h ma `Conv_miopen.cpp` include EmptyTensor.h senza HIPContextLight | ✅ Permanente |
| **22 giu T21:40** | `EmptyTensor.h file not found` — auto-inflict by `rm -f build/aten/src/ATen/hip/EmptyTensor.h` | **REGOLA CRITICA**: `build/aten/src/ATen/hip` è **junction** → `aten/src/ATen/hip` SOURCE. Cancellare file nel build/ cancella anche source! File restaurato via Write. Per forzare rebuild .obj usare `rm -f build/caffe2/CMakeFiles/torch_hip.dir/*.obj` NON file in junction-mirrored hip/ | ⚠️ REGOLA OPERATIVA |
| **22 giu T21:50** | `Handle.cpp:31,49` namespace errors — `at::cuda::DeviceThreadHandlePool` (non hipify-d) + `at::hip::getCurrentHIPStream` (sbagliato namespace) | **VEGA-PATCH 30**: `at::cuda` → `at::hip` linea 31; `at::hip` → `c10::hip` linea 49 (`getCurrentHIPStream` è in c10::hip, non at::hip) | ✅ Permanente |
| **22 giu T22:00** | `cuda_cmake_macros.h file not found` (CudaIPCTypes.cpp) | **VEGA-PATCH 31**: stub `build/c10/cuda/impl/cuda_cmake_macros.h` redirect a `<c10/hip/impl/hip_cmake_macros.h>` | ⚠️ Categoria D (filesystem) |
| **22 giu T22:01** | `cuda_runtime_api.h file not found` (CUDAContextLight.h:6) | **VEGA-PATCH 32**: `#ifdef USE_ROCM` in CUDAContextLight.h redirect hip headers + define cudaStream_t/cusparseHandle_t/cublasHandle_t come hip equivalenti | ✅ Permanente |
| **22 giu T22:25** | `cublasLt.h file not found` (CUDAContextLight.h:22) | **VEGA-PATCH 32b**: wrap `#include <cublasLt.h>` in `#ifndef USE_ROCM` (ROCm usa hipblaslt) | ✅ Permanente |
| **22 giu T22:25** | `cuda.h file not found` (CUDAException.h:9) | **VEGA-PATCH 33**: `#ifdef USE_ROCM` redirect `<cuda.h>` → `<hip/hip_runtime.h>` | ✅ Permanente |
| **22 giu T23:53** | `cuda_runtime_api.h not found` (CUDAFunctions.h:14) | **VEGA-PATCH 34**: stesso pattern PATCH 32 in CUDAFunctions.h | ✅ Permanente |
| **23 giu T00:21** | Decine errori `cudaError_t/Stream_t/MemcpyKind/StreamCaptureMode` ecc — `torch/csrc/cuda/*.cpp` NON hipify-d ma includono c10/cuda/*.h con symbol CUDA-only | **VEGA-PATCH 35**: nuovo header `c10/cuda/_cuda_to_hip_compat.h` con 20+ `#define cuda*_t hip*_t` + 20+ function aliases. Force-include via `/FI` in CMakeLists torch_hip target. | ✅ Permanente (strutturale) |
| **22 giu T22:00 - VERITÀ F.1 BETATEST** | F.1 wave64 shfl 5→6bit patch NON RISOLVE reduction bug — 10/10 FAIL (mean 14382%, argmax 2000%) | safety_v7.py monkey-patch RESTA NECESSARIO. LA RUOTA wheel = unica strada definitiva (bypass ZLUDA wrapper completo) | 🚨 KNOWN |

## Bug NON ancora visti (latenti potenziali)

- rccl missing su Windows (warning configure — NON blocca, USE_DISTRIBUTED=0 mitiga)
- ROCm-distributed missing (stesso)
- **`at::native::empty_cuda` linker error potenziale**: 386 chiamate `at::native::*_cuda` in `RegisterCUDA.cpp` (generated codegen) con declarations in `build/aten/src/ATen/ops/*_native.h`, ma definizioni post-HIPify sono `*_hip` (in `aten/src/ATen/native/hip/*.hip`). Compile OK ma **link time potrebbe fallire** quando arriva a torch_hip.dll. Build #30 da verificare. Se emerge: VEGA-PATCH 25 (wrapper extern in `TensorFactories.hip` o linker .def aliases).
- Possibili problemi link MIOpen.lib se non in lib path

## Pattern ricorrente: header HIP AMD ROCm 6.x richiedono compilatore GCC-builtin compatible

**Tutti i file che includono `<hip/hip_runtime.h>` includono indirettamente `amd_hip_vector_types.h`**:
- 9 file `c10/hip/*.cpp` (HIPAllocatorConfig, HIPCachingAllocator, HIPDeviceAssertionHost, HIPException, HIPFunctions, HIPMallocAsyncAllocator, HIPMiscFunctions, HIPStream, driver_api)
- File `caffe2/hip/*.cpp` quando enabled
- File `aten/src/ATen/hip/*.cpp` quando enabled

`amd_hip_vector_types.h` usa:
- `__builtin_clz` in `constexpr next_pot()` (linea 139-141) → richiede compilatore con builtin constexpr GCC
- `__attribute__((vector_size(N)))` per `Native_vec_` / `Vec3_cmp` (linea 358) → richiede attribute GCC

**MSVC cl.exe fallisce su entrambi**. **clang-cl gestisce entrambi nativamente**.

**Decisione architetturale**: usare clang-cl 21 (Marconi pack ROCm 7.1) come compilatore GLOBALE per LA RUOTA, NON cl.exe MSVC. Patch 12+12b sono kept-as-fallback ma non più necessarie con VEGA-PATCH 24.

---

## Procedura idempotente CANONICA

1. **Verifica state**: `build_laruota_canonical.cmd verify` (controlla junction, header MIOpen, VEGA-PATCH presenti)
2. **Build clean**: `build_laruota_canonical.cmd build` (applica TUTTO + lancia setup.py install)
3. **Build resume**: `build_laruota_canonical.cmd resume` (no clean cache, riprende ninja)

Vedi `build_laruota_canonical.cmd` per implementazione.

---

⭐ **2 Solution, 22 giu 2026 T16:45** — runbook chiuso post-incidente ciclo build #24-#28.

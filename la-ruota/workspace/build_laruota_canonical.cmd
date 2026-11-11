@echo off
:: ============================================================================
:: BUILD LA RUOTA ? Script canonico idempotente Vega gfx906 Windows
:: Versione: 1.0  Data: 22 giu 2026 T16:45
:: Vedi BUILD_LARUOTA_RUNBOOK.md per documentazione completa
:: ============================================================================
:: Uso:
::   build_laruota_canonical.cmd verify   - verifica stato senza buildare
::   build_laruota_canonical.cmd build    - clean cache + configure + build full
::   build_laruota_canonical.cmd resume   - ninja resume (no reconfigure)
::   build_laruota_canonical.cmd          - default = resume
:: ============================================================================

setlocal enabledelayedexpansion

set "MODE=%~1"
if "%MODE%"=="" set "MODE=resume"

echo ============================================================
echo BUILD LA RUOTA canonico ? modalita: %MODE%
echo Timestamp: %DATE% %TIME%
echo ============================================================

:: ============================================================
:: STEP 0 ? VS environment setup
:: ============================================================
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64 >nul

:: ============================================================
:: STEP 1 ? Categoria C: env vars USE_* + paths
:: ============================================================
echo [STEP 1] Setting USE_* + path env vars...

:: USE flags (1=enable, 0=disable)
set "USE_ROCM=1"
set "USE_CUDA=0"
:: [1 ago 2026] USE_DISTRIBUTED=1: serve a transformers >= 4.51 (Qwen3), che importa
:: torch.distributed in modo incondizionato per il supporto tensor-parallel. NON serve
:: un backend funzionante: basta che il modulo esista e i simboli ci siano.
:: Su Windows il backend e' Gloo (sottomodulo gia' presente); RCCL e TensorPipe restano
:: spenti perche' su Windows non esistono -> niente RPC, ma c10d c'e'.
:: [3 ago 2026] Versione del pacchetto senza marcatore alpha.
:: Di default la build produce "2.5.0a0+gita8d6afb": secondo PEP 440 quell'"a0" la
:: rende una PRE-RELEASE, quindi MINORE di 2.5.0, e transformers 5.x disattiva torch
:: ("Disabling PyTorch because PyTorch >= 2.5 is required but found 2.5.0a0+..."),
:: lasciando solo tokenizer e configurazioni.
:: Il controllo legge i METADATI della distribuzione via importlib.metadata, NON
:: torch/version.py: riscrivere quel file a mano non basterebbe.
:: Lo sha resta come segmento locale, che PEP 440 ordina SOPRA la versione base.
set "PYTORCH_BUILD_VERSION=2.5.0+gita8d6afb"
set "PYTORCH_BUILD_NUMBER=1"

:: libuv_ROOT e' OBBLIGATORIA su Windows: senza, CMakeLists.txt riga 448 spegne
:: USE_DISTRIBUTED senza chiedere ("Libuv is not installed in current conda env").
:: libuv costruita dai sorgenti gia' nell'albero: costruisci_libuv.cmd
set "libuv_ROOT=C:\LaRuota_workspace\libuv_install"
set "USE_DISTRIBUTED=1"
set "USE_GLOO=1"
set "USE_NCCL=0"
set "USE_RCCL=0"
set "USE_MPI=0"
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
set "BUILD_CAFFE2=1"
set "BUILD_CAFFE2_OPS=0"

:: [VEGA-PATCH 41 T15:35 23 giu ? FIX HIP TOOLCHAIN]
:: HIP_PATH ora punta a Marconi pack (era ROCm 6.4 ? conflitto)
:: + CMAKE_HIP_COMPILER/ARCHITECTURES/PLATFORM forzati per enable_language(HIP) in LoadHIP.cmake
set "HIP_PATH=C:\rocm_5_7_expansion_pack"
set "ROCM_PATH=C:\rocm_5_7_expansion_pack"
set "ROCM_SOURCE_DIR=C:\rocm_5_7_expansion_pack"
set "ROCM_HOME=C:\rocm_5_7_expansion_pack"
:: [VEGA-PATCH 42 T07:50 24 giu] HIP compiler MUST be clang-cl per coerenza MSVC_RUNTIME_LIBRARY.
:: clang.exe (GCC frontend) rifiuta 'MultiThreadedDLL' propagato da caffe2/CMakeLists.txt.
:: Build #56 fail T07:47 con: "MSVC_RUNTIME_LIBRARY value 'MultiThreadedDLL' not known for this HIP compiler"
set "CMAKE_HIP_COMPILER=C:\rocm_5_7_expansion_pack\compiler\bin\clang-cl.exe"
set "CMAKE_HIP_ARCHITECTURES=gfx906"
set "CMAKE_HIP_PLATFORM=amd"
set "HIP_PLATFORM=amd"

:: [VEGA-PATCH 24 T17:10 22 giu] FORCE CLANG-CL global compiler (Marconi pack)
:: cl.exe MSVC NON ha __builtin_clz constexpr ne capisce __attribute__((vector_size))
:: usati da amd_hip_vector_types.h. Tutti 9 c10/hip/*.cpp falliranno con MSVC.
:: clang-cl ha entrambi builtin + GCC attributes nativi.
set "CC=C:\rocm_5_7_expansion_pack\compiler\bin\clang-cl.exe"
set "CXX=C:\rocm_5_7_expansion_pack\compiler\bin\clang-cl.exe"
set "CMAKE_C_COMPILER=C:\rocm_5_7_expansion_pack\compiler\bin\clang-cl.exe"
set "CMAKE_CXX_COMPILER=C:\rocm_5_7_expansion_pack\compiler\bin\clang-cl.exe"

:: CMAKE_PREFIX_PATH
:: [VEGA-PATCH 46 T11:20 5 lug - REGOLA 4-bis: SOLO ROCm 5.7 + Marconi, mai 6.x/7.x]
:: Rimosso ROCm 6.4 (violazione). I 12 pacchetti find_package (hip/rocblas/hipblas/hiprand/
:: hipsparse/hipsolver/rocprim/hipcub/rocthrust/hipfft/hiprtc/rocrand) risolti da ROCm 5.7 base
:: (permessa, config+import-lib+prefix coerenti). hipblaslt+hipblas-common dai NOSTRI artifact
:: TheRock 7.14 (binari sovrani, NON da 7.1). Runtime carica DLL TheRock da Marconi via PATH.
:: [VEGA-PATCH 65 - 16 ott 2026] MKL statico (pip, in mkl_prefix): FindMKL lo trova
:: in <prefix>/lib e <prefix>/include. Vedi patch_mkl_numpy2.py
set "CMAKE_PREFIX_PATH=C:\LaRuota_workspace\mkl_prefix\Library;C:\LaRuota_workspace\venv_build\Lib\site-packages;C:\rocm_5_7_expansion_pack;C:/Program Files/AMD/ROCm/5.7;C:/TheRock_workspace/TheRock/build_gfx906/dist/rocm;C:/TheRock_workspace/TheRock/build_gfx906/artifacts/miopen_run_generic/ml-libs/MIOpen/stage"
:: Include paths
:: [VEGA-PATCH 27 T19:05 + RIATTIVATO VEGA-PATCH 40 T02:46 23 giu]
:: Marconi pack include riattivato per pickare cuda.h/cuda_runtime_api.h stub (redirect a hip).
:: hip_version.h Marconi pack ora ha HIP_VERSION_MAJOR=6 (VEGA-PATCH 28) - no piu' typedef conflict.
:: [VEGA-PATCH 46d T11:45 5 lug] dist/rocm/include PRIMO -I: forza risoluzione header BLAS a
:: TheRock 7.14 (hipblas.h + hipblas-common.h coerenti) PRIMA che clang veda hipblas.h 5.7
:: (modello vecchio, definisce HIPBLAS_OP_N inline -> redefinition con hipblas-common 7.x).
set "CXXFLAGS=-IC:/TheRock_workspace/TheRock/build_gfx906/dist/rocm/include -IC:\rocm_5_7_expansion_pack\include -IC:/TheRock_workspace/TheRock/build_gfx906/artifacts/miopen_run_generic/ml-libs/MIOpen/stage/include"

:: Build vars
set "MAX_JOBS=4"
set "PYTORCH_ROCM_ARCH=gfx906"

:: PATH (compiler clang-cl21 primo)
set "PATH=C:\rocm_5_7_expansion_pack\compiler\bin;C:\rocm_5_7_expansion_pack\bin;%PATH%"

echo   OK env settings (16 vars USE_*, 4 path, CXXFLAGS, MAX_JOBS)

:: ============================================================
:: STEP 2 ? Categoria D: filesystem artifacts (junction + MIOpen headers)
:: ============================================================
echo [STEP 2] Setup filesystem artifacts...

:: 2a. Junction build/aten/src/ATen/hip -> aten/src/ATen/hip
if not exist "C:\LaRuota_workspace\pytorch_src\build\aten\src\ATen\hip" (
    if exist "C:\LaRuota_workspace\pytorch_src\build\aten\src\ATen" (
        echo   Creando junction build/aten/src/ATen/hip...
        powershell -NoProfile -Command "New-Item -ItemType Junction -Path 'C:\LaRuota_workspace\pytorch_src\build\aten\src\ATen\hip' -Target 'C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip'" >nul 2>&1
        if exist "C:\LaRuota_workspace\pytorch_src\build\aten\src\ATen\hip" (
            echo   OK junction creata
        ) else (
            echo   [WARN] junction NON creata, build/ non ancora pronto
        )
    ) else (
        echo   [SKIP] build/aten/src/ATen/ non esiste ancora, junction sara' creata dopo configure
    )
) else (
    echo   OK junction gia' presente
)

:: 2b. MIOpen headers in Marconi pack
if not exist "C:\rocm_5_7_expansion_pack\include\miopen\miopen.h" (
    echo   Copia MIOpen headers in Marconi pack...
    if not exist "C:\rocm_5_7_expansion_pack\include\miopen" mkdir "C:\rocm_5_7_expansion_pack\include\miopen"
    xcopy /Y /Q "C:\TheRock_workspace\TheRock\build_gfx906\artifacts\miopen_run_generic\ml-libs\MIOpen\stage\include\miopen\*.h" "C:\rocm_5_7_expansion_pack\include\miopen\" >nul
    echo   OK MIOpen headers copiati
) else (
    echo   OK MIOpen headers gia' in Marconi pack
)

:: ============================================================
:: STEP 3 ? Verifica VEGA-PATCH source persistenti (categoria A+B)
:: ============================================================
echo [STEP 3] Verifica VEGA-PATCH source persistenti...
findstr /C:"VEGA-PATCH 23" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip\EmptyTensor.h" >nul && (
    echo   OK VEGA-PATCH 23 ^(empty_cuda alias^) presente
) || (
    echo   [FAIL] VEGA-PATCH 23 MANCANTE in EmptyTensor.h
    if /I "%MODE%"=="verify" exit /b 1
)

findstr /C:"miopen_run_generic" "C:\LaRuota_workspace\pytorch_src\cmake\Modules\Findmiopen.cmake" >nul && (
    echo   OK Findmiopen.cmake punta a miopen_run_generic
) || (
    echo   [FAIL] Findmiopen.cmake punta ancora a dev_generic ^(percorso errato^)
    if /I "%MODE%"=="verify" exit /b 1
)

findstr /C:"VEGA-PATCH 4b" "C:\LaRuota_workspace\pytorch_src\cmake\public\LoadHIP.cmake" >nul && (
    echo   OK VEGA-PATCH 4b ^(Marconi pack detection^) presente
)

findstr /C:"VEGA-PATCH 8" "C:\LaRuota_workspace\pytorch_src\cmake\Modules\Findmiopen.cmake" >nul && (
    echo   OK VEGA-PATCH 8 ^(Findmiopen stub^) presente
)

findstr /C:"VEGA-PATCH 65" "C:\LaRuota_workspace\pytorch_src\cmake\Dependencies.cmake" >nul && (
    echo   OK VEGA-PATCH 65 ^(torch_python contro numpy 2^) presente
) || (
    echo   [FAIL] VEGA-PATCH 65 MANCANTE in Dependencies.cmake: torch tornerebbe a rompersi con numpy 2
)

findstr /C:"VEGA-PATCH 66" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\ParallelNative.cpp" >nul && (
    echo   OK VEGA-PATCH 66 ^(MKL su tutti i core^) presente
) || (
    echo   [FAIL] VEGA-PATCH 66 MANCANTE in ParallelNative.cpp: MKL tornerebbe a un solo core
)

findstr /C:"VEGA-PATCH 67" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\linalg\BatchLinearAlgebra.cpp" >nul && (
    echo   OK VEGA-PATCH 67 ^(cholesky e lstsq su GPU via rocSOLVER^) presente
) || (
    echo   [FAIL] VEGA-PATCH 67 MANCANTE in BatchLinearAlgebra.cpp: cholesky e lstsq tornerebbero a chiedere MAGMA
)

findstr /C:"VEGA-PATCH 68" "C:\LaRuota_workspace\pytorch_src\torch\csrc\profiler\stubs\cuda.cpp" >nul && (
    echo   OK VEGA-PATCH 68 ^(profiler GPU senza roctx^) presente
) || (
    echo   [FAIL] VEGA-PATCH 68 MANCANTE in profiler\stubs\cuda.cpp: senza roctracer non compila
)

findstr /C:"VEGA-PATCH 69" "C:\LaRuota_workspace\pytorch_src\c10\hip\impl\HIPGuardImpl.h" >nul && (
    echo   OK VEGA-PATCH 69 ^(stream nullo che aspetta un evento^) presente
) || (
    echo   [FAIL] VEGA-PATCH 69 MANCANTE in HIPGuardImpl.h: wait_stream/wait_event tornerebbero a fallire
)

findstr /C:"VEGA-PATCH 71" "C:\LaRuota_workspace\pytorch_src\torch\__init__.py" >nul && (
    echo   OK VEGA-PATCH 71 ^(RNN di MIOpen a uno stream^) presente
) || (
    echo   [FAIL] VEGA-PATCH 71 MANCANTE in torch\__init__.py: l'installazione la cancellerebbe
)

findstr /C:"VEGA-PATCH 72" "C:\LaRuota_workspace\pytorch_src\torch\__init__.py" >nul && (
    echo   OK VEGA-PATCH 72 ^(conv 1x1 stride al cambio di lotto^) presente
) || (
    echo   [FAIL] VEGA-PATCH 72 MANCANTE in torch\__init__.py: l'installazione la cancellerebbe
)

findstr /C:"VEGA-PATCH 74" "C:\LaRuota_workspace\pytorch_src\torch\__init__.py" >nul && (
    echo   OK VEGA-PATCH 74 ^(cache MIOpen propria della ruota^) presente
) || (
    echo   [FAIL] VEGA-PATCH 74 MANCANTE in torch\__init__.py: la cache condivisa riporterebbe kernel MIOpen vecchi
)

findstr /C:"VEGA-PATCH 79" "C:\LaRuota_workspace\pytorch_src\torch\__init__.py" >nul && (
    echo   OK VEGA-PATCH 79 ^(db MIOpen della ruota anche con la variabile utente di ZLUDA^) presente
) || (
    echo   [FAIL] VEGA-PATCH 79 MANCANTE in torch\__init__.py: il db MIOpen resterebbe condiviso con ZLUDA
)

findstr /C:"VEGA-PATCH 75" "C:\LaRuota_workspace\pytorch_src\torch\__init__.py" >nul && (
    echo   OK VEGA-PATCH 75 ^(esclusioni 58/62/72 spente: MIOpen corretta^) presente
) || (
    echo   [FAIL] VEGA-PATCH 75 MANCANTE in torch\__init__.py
)

findstr /C:"VEGA-PATCH 76" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\Copy.hip" >nul && (
    echo   OK VEGA-PATCH 76 ^(copy_ trasposto con il kernel a tessere^) presente
) || (
    echo   [FAIL] VEGA-PATCH 76 MANCANTE in Copy.hip: le copie trasposte tornerebbero a 3-45 GB/s
)

findstr /C:"VEGA-PATCH 73" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\miopen\Conv_miopen.cpp" >nul && (
    echo   OK VEGA-PATCH 73 ^(spazio di lavoro nella ricerca, RNN multistrato, sleep^) presente
) || (
    echo   [FAIL] VEGA-PATCH 73 MANCANTE in Conv_miopen.cpp
)

findstr /C:"VEGA-PATCH 78" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\linalg\BatchLinearAlgebra.cpp" >nul && (
    echo   OK VEGA-PATCH 78 ^(eigh e svd via rocSOLVER^) presente
) || (
    echo   [FAIL] VEGA-PATCH 78 MANCANTE: eigh tornerebbe sbagliata da n=64, svd non ripetibile
)

findstr /C:"VEGA-PATCH 80b" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\SoftMax.hip" >nul && (
    echo   OK VEGA-PATCH 80/80b ^(softmax fp64 righe non allineate^) presente
) || (
    echo   [FAIL] VEGA-PATCH 80b MANCANTE: softmax e log_softmax fp64 tornerebbero sbagliate
)

findstr /C:"VEGA-PATCH 81" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\linalg\BatchLinearAlgebra.cpp" >nul && (
    echo   OK VEGA-PATCH 81 ^(eigh e svd su MKL^) presente
) || (
    echo   [FAIL] VEGA-PATCH 81 MANCANTE: eigh e svd GPU tornerebbero 20-114x piu' lente
)

findstr /C:"VEGA-PATCH 83" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\FusedSgdKernel.hip" >nul && (
    echo   OK VEGA-PATCH 83 ^(ottimizzatori fused esportati^) presente
) || (
    echo   [FAIL] VEGA-PATCH 83 MANCANTE: Adam/AdamW/SGD fused=True farebbero crollare il processo
)

findstr /C:"VEGA-PATCH 84" "C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\FusedSgdKernel.hip" >nul && (
    echo   OK VEGA-PATCH 84 ^(SGD fused senza ciclo infinito^) presente
) || (
    echo   [FAIL] VEGA-PATCH 84 MANCANTE: SGD fused=True bloccherebbe la GPU
)

findstr /C:"VEGA-PATCH 82" "C:\LaRuota_workspace\pytorch_src\c10\hip\HIPCachingAllocator.cpp" >nul && (
    echo   OK VEGA-PATCH 82 ^(allocatore: PYTORCH_RUOTA_ALLINEA_2MB^) presente
) || (
    echo   [FAIL] VEGA-PATCH 82 MANCANTE in HIPCachingAllocator.cpp: niente allineamento a 2 MB
)

:: ============================================================
:: STEP 4 ? Mode-specific actions
:: ============================================================
echo [STEP 4] Esecuzione modalita: %MODE%
cd /D C:\LaRuota_workspace\pytorch_src

if /I "%MODE%"=="verify" (
    echo.
    echo === VERIFY MODE: state check completato, no build lanciata ===
    echo.
    exit /b 0
)

if /I "%MODE%"=="build" (
    echo   Modalita BUILD: clean CMakeCache + fresh configure + build
    if exist "build\CMakeCache.txt" (
        echo   Backup CMakeCache.txt.bak prima del clean...
        copy /Y "build\CMakeCache.txt" "build\CMakeCache.txt.bak_%RANDOM%" >nul
        del /Q "build\CMakeCache.txt"
    )
)

if /I "%MODE%"=="resume" (
    echo   Modalita RESUME: ninja prosegue senza reconfigure
)

:: ============================================================
:: STEP 5 ? Lancio setup.py install
:: ============================================================
echo [STEP 5] Lancio python setup.py install T%TIME%...
echo.
C:\LaRuota_workspace\venv_build\Scripts\python.exe setup.py install 2>&1
set RC=%ERRORLEVEL%
echo.

:: ============================================================
:: STEP 6 ? Post-build: ricreate junction se ora c'e' build/
:: ============================================================
if not exist "C:\LaRuota_workspace\pytorch_src\build\aten\src\ATen\hip" (
    if exist "C:\LaRuota_workspace\pytorch_src\build\aten\src\ATen" (
        echo [STEP 6] Post-configure: creo junction mancante...
        powershell -NoProfile -Command "New-Item -ItemType Junction -Path 'C:\LaRuota_workspace\pytorch_src\build\aten\src\ATen\hip' -Target 'C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip'" >nul 2>&1
    )
)

echo.
echo ============================================================
echo BUILD finished RC=%RC% T%TIME%
echo ============================================================
exit /b %RC%

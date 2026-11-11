@echo off
REM ============================================================================
REM build_pytorch_rocm_gfx906.cmd
REM LA RUOTA — Build PyTorch ROCm Windows nativo gfx906 (Radeon VII / MI50)
REM 2 Solution, 17 giu 2026 T23:30 — pioneer build
REM
REM Prereq:
REM   - VS2022 BuildTools 14.44.35207+ (MSVC 19.44+)
REM   - CMake 3.31.0+
REM   - Ninja 1.12+, ccache 4.10+
REM   - Python 3.12+ + symlink python3.exe
REM   - TheRock build_gfx906 artifacts (rocblas.dll + MIOpen.dll + cmake config)
REM   - HIPSDK 7.1 installato
REM   - 32+ GB RAM (riservare 16+ GB durante build)
REM ============================================================================

REM --- Setup MSVC environment ---
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
if errorlevel 1 (
    echo *** MSVC env setup FAIL ***
    exit /b 1
)

REM [VEGA-FIX T10:43 19 giu] rc.exe path PRIORITARIO per LNK1158 fix torch._C extension
REM Copiati rc.exe + rcdll.dll in venv_build/bin/ (no MSVC bin Program Files admin)
set "PATH=C:\LaRuota_workspace\venv_build\bin;%PATH%"

REM --- PATH setup ---
REM [VEGA-PIVOT T08:10 19 giu] Marconi 5.7 Expansion Pack come HIP_PATH:
REM   - clang 21 ROCm 7.1 (vs 20 ROCm 6.4)
REM   - Headers HIP 5.7 base SENZA bug next_pot constexpr clang-cl strict (testabile)
REM   - Linka rocBLAS TheRock 7.14 con 17.84 TFLOPS asset embedded
REM   - amdhip64_7_shim.dll forwarder reale a System32 v5.7 (validato 21/21 betatest)
set "MARCONI_PACK=C:\rocm_5_7_expansion_pack"
REM [VEGA-PATCH 18 v2 T03:38 20 giu] HIP_PATH → Marconi pack per include headers permissivi clang 21
REM ROCm 6.4 include/hip/amd_detail/amd_hip_vector_types.h ha bug next_pot constexpr clang strict.
REM Marconi pack ha include compat-headers permissivi. find_package(hip) usa CMAKE_PREFIX_PATH = ROCm 6.4.
set "HIP_PATH=%MARCONI_PACK%\"
REM [VEGA-FIX T07:08 18 giu] aggiunto Windows SDK bin per rc.exe (LNK1158 fix)
set "PATH=%MARCONI_PACK%\compiler\bin;%MARCONI_PACK%\runtime;%MARCONI_PACK%\lib;C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64;%PATH%"
REM [VEGA-FIX T07:55] path forward slash per evitare CMake escape error '\T'
REM [VEGA-PATCH 19 T03:30 20 giu] Aggiungo ROCm 6.4 al CMAKE_PREFIX_PATH per find_package(hipblas-common, hipBLAS, hipBLASLt, ...) Config search.
REM Marconi pack non ha lib/cmake/<pkg>/ structure. ROCm 6.4 sì. Lascio TheRock paths per asset rocBLAS+hipBLASLt 7.14 binari.
set "CMAKE_PREFIX_PATH=C:/Program Files/AMD/ROCm/6.4;%MARCONI_PACK%;C:/TheRock_workspace/TheRock/build_gfx906/artifacts/blas_dev_generic/math-libs/BLAS/hipBLAS/stage;C:/TheRock_workspace/TheRock/build_gfx906/artifacts/blas_dev_generic/math-libs/BLAS/hipBLASLt/stage;%CMAKE_PREFIX_PATH%"
set "HIP_DEVICE_LIB_PATH=%MARCONI_PACK%\device_libs"

REM --- PyTorch build config ---
set "USE_ROCM=1"
set "USE_CUDA=0"
set "PYTORCH_ROCM_ARCH=gfx906"
set "HSA_OVERRIDE_GFX_VERSION=9.0.6"
REM [VEGA-FIX T08:30] hip-config.cmake invoca hipconfig.pl che richiede Perl. Bypassa settando HIP_PLATFORM=amd
set "HIP_PLATFORM=amd"

REM --- Patch flags (vedi sediment PYTORCH.md Patch 1) ---
set "USE_FLASH_ATTENTION=0"
set "USE_MEM_EFF_ATTENTION=0"
set "USE_KINETO=0"
set "USE_DISTRIBUTED=0"
set "USE_TENSORPIPE=0"
set "BUILD_TEST=0"
set "USE_GLOG=0"
set "USE_GFLAGS=0"
REM [VEGA-PATCH 14 T10:53 18 giu] fbgemm template strict bug con clang-cl: disabilito
set "USE_FBGEMM=0"
REM Anche XNNPACK potrebbe avere issue analoghi con clang-cl
set "USE_XNNPACK=0"
REM [VEGA-PATCH 15 T19:35 18 giu] mkl-dnn batch_normalization.cpp strict clang-cl C++17 fail
REM (sediment T10:58). Disabilito MKL-DNN backend: PyTorch usa direttamente ROCm/MIOpen su gfx906.
set "USE_MKLDNN=0"
REM [VEGA-PATCH 16 T19:35 18 giu] Disabilito altri backend CPU non utili a ROCm gfx906
set "USE_NNPACK=0"
set "USE_QNNPACK=0"
REM [VEGA-PATCH 17 T08:30 19 giu] clang-cl 21 strict -Werror -Wmissing-prototypes blocca jit/codegen/fuser/cpu
REM (functions wmkstemps, exec, activate in temp_file.h + fused_kernel.cpp non hanno prototype prima della definizione)
REM Soluzione: aggiungi -Wno-missing-prototypes + -Wno-error=missing-prototypes ai CXX flags PyTorch
set "CXXFLAGS=-Wno-missing-prototypes -Wno-error=missing-prototypes -Wno-ignored-attributes"
set "CFLAGS=-Wno-missing-prototypes -Wno-error=missing-prototypes"

REM --- ROCm paths separati: HIP install vs TheRock kernels artifacts ---
REM [VEGA-PATCH 18 v2 T03:38 20 giu] ROCM_PATH → Marconi pack (PATCH 4b detection via include/hip)
REM find_package config via CMAKE_PREFIX_PATH = ROCm 6.4 + Marconi + TheRock.
set "ROCM_PATH=C:/rocm_5_7_expansion_pack"
REM THEROCK_PATH = artifacts TheRock con rocblas.dll + MIOpen.dll + kernels gfx906 custom
set "THEROCK_PATH=C:/TheRock_workspace/TheRock/build_gfx906/artifacts"
set "ROCBLAS_PATH=%THEROCK_PATH%/blas_lib_generic/math-libs/BLAS/rocBLAS/stage"
set "MIOPEN_PATH=%THEROCK_PATH%/miopen_lib_generic/ml-libs/MIOpen/stage"
set "HIPBLAS_PATH=%THEROCK_PATH%/blas_dev_generic/math-libs/BLAS/hipBLAS/stage"
set "HIPBLASLT_PATH=%THEROCK_PATH%/blas_dev_generic/math-libs/BLAS/hipBLASLt/stage"

REM --- ccache wrapper ---
REM [VEGA-PATCH 13 T10:47 18 giu] Switch compilatore globale a clang-cl
REM Header HIP ROCm 6.1 (amd_hip_vector_types.h) usano builtin GCC e attribute clang
REM (ext_vector_type, ext_vector_type) che cl.exe MSVC non supporta.
REM clang-cl = Windows clang in MSVC-compatible mode, supporta tutti i builtin GCC.
REM [VEGA-PIVOT T08:10 19 giu] clang-cl 21 Marconi pack (vs 20 ROCm 6.4)
set "CLANG_CL=C:\rocm_5_7_expansion_pack\compiler\bin\clang-cl.exe"
set "CC=%CLANG_CL%"
set "CXX=%CLANG_CL%"
set "CCACHE_DIR=C:\LaRuota_workspace\ccache"

REM --- Memory + parallelism ---
REM [VEGA-FIX T19:35 18 giu] MAX_JOBS=4 invece di 8 — Manzoni LIVE consuma 2.5 GB RAM + 100% GPU.
REM 4 thread build (8 logical core CPU) lasciano headroom per training senza swap.
set "MAX_JOBS=4"
set "CMAKE_BUILD_PARALLEL_LEVEL=4"

REM --- Activate venv build isolato ---
call "C:\LaRuota_workspace\venv_build\Scripts\activate.bat"
if errorlevel 1 (
    echo *** venv_build activate FAIL ***
    exit /b 1
)

REM --- Build cwd ---
cd /d "C:\LaRuota_workspace\pytorch_src"

REM --- Verify Python ---
echo === Python env ===
python --version
python -c "import sys; print('exe:', sys.executable)"
echo.

REM --- Build deps GIA INSTALLATE in venv_build (vedi setup T23:40) ---
REM Se serve refresh: pip install -r requirements.txt

REM --- Verify TheRock artifacts ---
echo.
echo === Verify TheRock artifacts ===
if not exist "%ROCBLAS_PATH%\bin\rocblas.dll" (
    echo *** rocblas.dll NOT FOUND in %ROCBLAS_PATH% ***
    exit /b 1
)
if not exist "%MIOPEN_PATH%\bin\MIOpen.dll" (
    echo *** MIOpen.dll NOT FOUND in %MIOPEN_PATH% ***
    exit /b 1
)
echo TheRock artifacts found OK

REM --- Pre-build cleanup ---
echo.
echo === Pre-build cleanup ===
python setup.py clean

REM --- Launch build (LONG: 4-6 hours) ---
echo.
echo === Launching PyTorch ROCm build T%TIME% ===
echo Output: C:\LaRuota_workspace\build_log_%DATE:/=-%_%TIME::=.%.txt
python setup.py bdist_wheel 2>&1
set BUILD_RC=%ERRORLEVEL%

echo.
echo === Build finished RC=%BUILD_RC% T%TIME% ===
if %BUILD_RC% EQU 0 (
    dir dist\*.whl
    echo.
    echo *** SUCCESS — PyTorch ROCm gfx906 wheel built ***
) else (
    echo *** BUILD FAIL — check log ***
)
exit /b %BUILD_RC%

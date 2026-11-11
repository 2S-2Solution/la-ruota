@echo off
REM preflight_check.cmd — verifica TUTTO pronto per LA RUOTA build
REM Vega 17 giu T23:42

echo ============================================================
echo LA RUOTA — Preflight check
echo ============================================================
echo.

REM 1. MSVC
echo --- 1. MSVC ---
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" (
    echo [OK] vcvarsall.bat trovato
) else (
    echo [FAIL] vcvarsall.bat NON trovato
    exit /b 1
)

REM 2. CMake, Ninja, ccache
echo.
echo --- 2. Build tools ---
cmake --version | findstr /R "version" | head -1
ninja --version
ccache --version | findstr /R "ccache"

REM 3. Python venv build
echo.
echo --- 3. Python venv ---
if exist "C:\LaRuota_workspace\venv_build\Scripts\python.exe" (
    echo [OK] venv_build presente
    "C:\LaRuota_workspace\venv_build\Scripts\python.exe" --version
) else (
    echo [FAIL] venv_build mancante
    exit /b 1
)

REM 4. PyTorch source + Patch 1
echo.
echo --- 4. PyTorch source ---
if exist "C:\LaRuota_workspace\pytorch_src\CMakeLists.txt" (
    echo [OK] CMakeLists.txt
    findstr /C:"VEGA-PATCH" "C:\LaRuota_workspace\pytorch_src\CMakeLists.txt" > nul
    if errorlevel 1 (
        echo [FAIL] Patch 1 NON applicata
        exit /b 1
    )
    echo [OK] Patch 1 applicata (VEGA-PATCH marker presente)
) else (
    echo [FAIL] PyTorch source mancante
    exit /b 1
)

REM 5. TheRock artifacts gfx906
echo.
echo --- 5. TheRock artifacts ---
if exist "C:\TheRock_workspace\TheRock\build_gfx906\artifacts\blas_lib_generic\math-libs\BLAS\rocBLAS\stage\bin\rocblas.dll" (
    echo [OK] rocblas.dll prodotta
) else (
    echo [FAIL] rocblas.dll mancante
    exit /b 1
)
if exist "C:\TheRock_workspace\TheRock\build_gfx906\artifacts\miopen_lib_generic\ml-libs\MIOpen\stage\bin\MIOpen.dll" (
    echo [OK] MIOpen.dll prodotta
) else (
    echo [FAIL] MIOpen.dll mancante
    exit /b 1
)

REM 6. HIPSDK 6.4 (primary build target)
echo.
echo --- 6. HIPSDK ---
if exist "C:\Program Files\AMD\ROCm\6.4\bin\hipcc.bin.exe" (
    echo [OK] HIPSDK 6.4 presente
) else if exist "C:\Program Files\AMD\ROCm\6.1\bin\hipcc.bin.exe" (
    echo [OK] HIPSDK 6.1 fallback presente
) else (
    echo [FAIL] HIPSDK mancante
    exit /b 1
)

REM 7. RAM check
echo.
echo --- 7. RAM check ---
wmic OS get FreePhysicalMemory /value | findstr /R "[0-9]"

REM 8. Disco
echo.
echo --- 8. Disco C: ---
wmic LogicalDisk where "DeviceID='C:'" get FreeSpace /value | findstr /R "[0-9]"

echo.
echo ============================================================
echo [OK] PREFLIGHT PASS - PRONTO per build_pytorch_rocm_gfx906.cmd
echo ============================================================

@echo off
set "AMD_LOG_LEVEL=1"
if not "%~1"=="" set "HIP_DEVICE_LIB_PATH=%~1"
if not "%~2"=="" set "ROCM_PATH=%~2"
if not "%~2"=="" set "HIP_PATH=%~2"
cd /d "C:\LaRuota_workspace"
"C:\LaRuota_workspace\venv_build\Scripts\python.exe" -u prova_allocazione.py 2>&1

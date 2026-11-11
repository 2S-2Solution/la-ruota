@echo off
set "HIP_PATH=C:\rocm_5_7_expansion_pack\"
set "PATH=C:\rocm_5_7_expansion_pack\bin;C:\rocm_5_7_expansion_pack\runtime;C:\Program Files\AMD\ROCm\5.7\bin;%PATH%"
set "AMD_LOG_LEVEL=0"
cd /d "C:\LaRuota_workspace"
"C:\LaRuota_workspace\venv_build\Scripts\python.exe" -u quali_moduli.py 2>&1

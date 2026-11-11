@echo off
set "AMD_LOG_LEVEL=4"
set "AMD_LOG_MASK=0xFFFFFFFF"
set "OUT=C:\LaRuota_workspace\prova_alloc_log.log"
cd /d "C:\LaRuota_workspace"
"C:\LaRuota_workspace\venv_build\Scripts\python.exe" -u prova_allocazione.py > "%OUT%" 2>&1
echo FINE-LOG >> "%OUT%"

@echo off
set "OUT=C:\LaRuota_workspace\prova_allocazione.log"
cd /d "C:\LaRuota_workspace"
"C:\LaRuota_workspace\venv_build\Scripts\python.exe" -u prova_allocazione.py > "%OUT%" 2>&1
echo FINE-RUOTA >> "%OUT%"
type "%OUT%"

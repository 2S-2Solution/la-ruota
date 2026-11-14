@echo off
rem La Ruota 2.15 - verifica breve (GPU contro CPU). Da lanciare nella cartella d installazione.
"%~dp0venv\Scripts\python.exe" -I "%~dp0verifica.py"
set RC=%ERRORLEVEL%
if "%~1"=="" pause
exit /b %RC%

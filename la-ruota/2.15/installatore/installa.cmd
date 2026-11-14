@echo off
rem La Ruota 2.15 - installazione. Le opzioni vanno a installa.ps1 (vedi LEGGIMI.md).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installa.ps1" %*
set RC=%ERRORLEVEL%
if "%~1"=="" pause
exit /b %RC%

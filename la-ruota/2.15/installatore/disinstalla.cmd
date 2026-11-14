@echo off
rem La Ruota 2.15 - disinstallazione. Il file viene cancellato mentre gira: (goto) chiude il batch
rem e il resto della riga, gia letto, prosegue senza rileggerlo.
(goto) 2>nul & powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0disinstalla.ps1" %* & if "%~1"=="" pause

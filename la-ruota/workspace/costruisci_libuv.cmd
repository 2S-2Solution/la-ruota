@echo off
:: Costruisce libuv dai sorgenti gia' presenti nell'albero di PyTorch.
:: Serve perche' su Windows CMakeLists.txt (riga 448) spegne USE_DISTRIBUTED
:: quando non trova libuv e la variabile libuv_ROOT non e' definita:
::   "Libuv is not installed in current conda env. Set USE_DISTRIBUTED to OFF."
:: Su Windows libuv e' il trasporto di Gloo e il backend di TCPStore.
setlocal

set "SRC=C:\LaRuota_workspace\pytorch_src\third_party\tensorpipe\third_party\libuv"
set "BUILD=C:\LaRuota_workspace\libuv_build"
set "PREFIX=C:\LaRuota_workspace\libuv_install"
:: CMAKE: cmake.exe da usare (predefinito: quello nel PATH)
if not defined CMAKE set "CMAKE=cmake"

echo [1/3] configurazione
"%CMAKE%" -S "%SRC%" -B "%BUILD%" -G "Visual Studio 17 2022" -A x64 ^
  -DCMAKE_INSTALL_PREFIX="%PREFIX%" ^
  -DBUILD_TESTING=OFF ^
  -DLIBUV_BUILD_TESTS=OFF
if errorlevel 1 goto :errore

echo [2/3] compilazione
"%CMAKE%" --build "%BUILD%" --config Release --parallel 8
if errorlevel 1 goto :errore

echo [3/3] installazione
"%CMAKE%" --install "%BUILD%" --config Release
if errorlevel 1 goto :errore

echo.
echo OK: libuv installata in %PREFIX%
dir /b "%PREFIX%\lib"
exit /b 0

:errore
echo.
echo FALLITO (errorlevel %errorlevel%)
exit /b 1

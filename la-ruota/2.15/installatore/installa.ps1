# La Ruota 2.15 - installazione (PyTorch 2.15 ROCm nativo per AMD Radeon VII, gfx906)
# Solo ASCII: PowerShell 5.1 legge l'UTF-8 senza BOM come ANSI.
# Uso: installa.cmd [-Destinazione <cartella>] [-Python <python.exe 3.12>] [-Marconi <cartella del kit>]
#                   [-SenzaVerifica] [-Sovrascrivi]
param(
    [string]$Destinazione = (Join-Path $env:LOCALAPPDATA '2S\la-ruota-2.15'),
    [string]$Python = '',
    [string]$Marconi = '',
    [switch]$SenzaVerifica,
    [switch]$Sovrascrivi
)
$ErrorActionPreference = 'Stop'
$qui = Split-Path -Parent $MyInvocation.MyCommand.Path
$marca = 'la-ruota.installazione'
$indiceAmd = 'https://rocm.nightlies.amd.com/whl-multi-arch/'
$versioneRocm = '10.1.0a20260822'

function Esci([string]$motivo) {
    Write-Host "ESITO: FALLITO - $motivo" -ForegroundColor Red
    exit 1
}

Write-Host "La Ruota 2.15 - installazione in $Destinazione"
$Destinazione = [IO.Path]::GetFullPath($Destinazione)
$cacheMiopen = Join-Path $Destinazione 'miopen-cache'

# 1. Requisiti
if (-not [Environment]::Is64BitOperatingSystem) { Esci 'serve Windows a 64 bit' }
$build = [Environment]::OSVersion.Version.Build
Write-Host "  Windows build $build"
if ($build -lt 19041) { Write-Host '  ATTENZIONE: provato solo su Windows 10 22H2 (build 19045)' -ForegroundColor Yellow }

$hip = Join-Path $env:SystemRoot 'System32\amdhip64.dll'
if (-not (Test-Path $hip)) { Esci 'manca System32\amdhip64.dll: installare prima il driver AMD Adrenalin' }
Write-Host '  runtime HIP del driver: trovato'

$vc = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64' -ErrorAction SilentlyContinue
if (-not $vc -or $vc.Installed -ne 1) {
    Write-Host '  ATTENZIONE: Microsoft Visual C++ Redistributable 2015-2022 x64 non trovato.' -ForegroundColor Yellow
    Write-Host '  Si scarica da https://aka.ms/vs/17/release/vc_redist.x64.exe' -ForegroundColor Yellow
} else { Write-Host "  VC++ Redistributable $($vc.Version)" }

# Kit Marconi (rocm-marconi): da li' viene lo shim amdhip64_7.dll (API HIP 7 sopra il runtime 5.7 del driver)
if (-not $Marconi) {
    $Marconi = [Environment]::GetEnvironmentVariable('MARCONI_ROOT', 'User')
    if (-not $Marconi) { $Marconi = $env:MARCONI_ROOT }
    if (-not $Marconi) { $Marconi = Join-Path $env:LOCALAPPDATA '2S\marconi' }
}
$shim = Join-Path $Marconi 'bin\amdhip64_7.dll'
if (-not (Test-Path $shim)) {
    Esci "manca lo shim $shim : installare prima il kit rocm-marconi (https://github.com/2s-2solution/rocm-marconi) oppure indicarlo con -Marconi <cartella>"
}
Write-Host "  shim HIP 7 del kit Marconi: $shim"

# Python 3.12 a 64 bit
$candidati = @()
if ($Python) { $candidati += $Python }
else {
    try { $p = & py -3.12 -c "import sys; print(sys.executable)" 2>$null; if ($LASTEXITCODE -eq 0 -and $p) { $candidati += $p.Trim() } } catch {}
    foreach ($radice in @('HKCU:\Software\Python\PythonCore\3.12\InstallPath', 'HKLM:\Software\Python\PythonCore\3.12\InstallPath')) {
        $ip = Get-ItemProperty $radice -ErrorAction SilentlyContinue
        if ($ip) {
            if ($ip.ExecutablePath) { $candidati += $ip.ExecutablePath }
            elseif ($ip.'(default)') { $candidati += (Join-Path $ip.'(default)' 'python.exe') }
        }
    }
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($cmd) { $candidati += $cmd.Source }
}
$py = $null
foreach ($c in $candidati) {
    try {
        $v = & $c -c "import sys, struct; print('%d.%d %d' % (sys.version_info[0], sys.version_info[1], struct.calcsize('P') * 8))" 2>$null
        if ($v -and $v.Trim() -eq '3.12 64') { $py = $c; break }
    } catch {}
}
if (-not $py) { Esci 'serve Python 3.12 a 64 bit (python.org); indicarlo con -Python <percorso di python.exe>' }
Write-Host "  Python: $py"

# 2. Cartella di destinazione
if (Test-Path (Join-Path $Destinazione 'venv')) {
    if (-not $Sovrascrivi) { Esci "esiste gia' un'installazione in $Destinazione (usare disinstalla.cmd oppure -Sovrascrivi)" }
    if (-not (Test-Path (Join-Path $Destinazione $marca))) { Esci "$Destinazione non e' un'installazione di La Ruota: non la tocco" }
    Remove-Item -LiteralPath (Join-Path $Destinazione 'venv') -Recurse -Force
}
New-Item -ItemType Directory -Force $Destinazione | Out-Null

# 3. Ambiente Python e pacchetti
Write-Host '  creo l''ambiente Python...'
& $py -m venv (Join-Path $Destinazione 'venv')
if ($LASTEXITCODE -ne 0) { Esci 'creazione del venv non riuscita' }
$vpy = Join-Path $Destinazione 'venv\Scripts\python.exe'
$sp = Join-Path $Destinazione 'venv\Lib\site-packages'

Write-Host "  scarico da AMD le librerie ROCm $versioneRocm (circa 1,5 GB, serve Internet)..."
& $vpy -m pip install --disable-pip-version-check --no-cache-dir --no-deps --index-url $indiceAmd `
    "rocm==$versioneRocm" "rocm-sdk-core==$versioneRocm" "rocm-sdk-libraries==$versioneRocm" `
    "rocm-sdk-device-gfx906==$versioneRocm" 'rocm-bootstrap==0.1.0'
if ($LASTEXITCODE -ne 0) { Esci "pip non ha scaricato le librerie ROCm da $indiceAmd (vedere i messaggi sopra)" }

$ruote = Get-ChildItem (Join-Path $qui 'wheel') -Filter '*.whl' | ForEach-Object { $_.FullName }
Write-Host '  installo torch, torchvision e le dipendenze da PyPI...'
& $vpy -m pip install --disable-pip-version-check --no-cache-dir --no-deps @ruote
if ($LASTEXITCODE -ne 0) { Esci 'installazione delle wheel di La Ruota non riuscita' }
& $vpy -m pip install --disable-pip-version-check --no-cache-dir -c (Join-Path $qui 'vincoli.txt') `
    numpy pillow filelock fsspec jinja2 networkx sympy typing_extensions setuptools intel-openmp
if ($LASTEXITCODE -ne 0) { Esci 'pip install delle dipendenze non riuscito (vedere i messaggi sopra)' }
& $vpy -m pip check
if ($LASTEXITCODE -ne 0) { Esci 'pip check segnala dipendenze mancanti' }

# 4. Shim HIP 7 e MIOpen 3.6 di La Ruota al posto dei file della wheel AMD (gli originali restano *.amd)
$binCore = Join-Path $sp '_rocm_sdk_core\bin'
$binLib = Join-Path $sp '_rocm_sdk_libraries\bin'
foreach ($c in @(@($binCore, 'amdhip64_7.dll', $shim), @($binLib, 'MIOpen.dll', (Join-Path $qui 'miopen\MIOpen.dll')))) {
    $dest = Join-Path $c[0] $c[1]
    if (-not (Test-Path $dest)) { Esci "manca $dest nella wheel AMD" }
    Move-Item -LiteralPath $dest -Destination ($dest + '.amd') -Force
    Copy-Item -LiteralPath $c[2] -Destination $dest -Force
}
$db = Join-Path $sp '_rocm_sdk_libraries\miopen_gfx906_db'
New-Item -ItemType Directory -Force $db | Out-Null
Copy-Item (Join-Path $qui 'miopen\db\*') $db -Force
Write-Host '  shim HIP 7 di Marconi e MIOpen 3.6 di La Ruota al loro posto'

# 5. Cache di MIOpen propria (vuota) e percorsi impostati per il solo Python di La Ruota
if (Test-Path $cacheMiopen) { Remove-Item -LiteralPath $cacheMiopen -Recurse -Force }
New-Item -ItemType Directory -Force $cacheMiopen | Out-Null
$pth = "import os; os.environ['MIOPEN_SYSTEM_DB_PATH'] = r'$db'; os.environ['MIOPEN_USER_DB_PATH'] = r'$cacheMiopen'; os.environ['MIOPEN_CUSTOM_CACHE_DIR'] = r'$cacheMiopen'"
Set-Content -LiteralPath (Join-Path $sp 'laruota_miopen.pth') -Encoding ASCII -Value $pth
Write-Host "  cache MIOpen: $cacheMiopen (nessuna variabile d'ambiente impostata)"

# 6. Lanciatori e file di servizio
Copy-Item (Join-Path $qui 'verifica.py'), (Join-Path $qui 'verifica.cmd'), (Join-Path $qui 'disinstalla.cmd'), (Join-Path $qui 'disinstalla.ps1'), (Join-Path $qui 'LEGGIMI.md') $Destinazione -Force
Set-Content -LiteralPath (Join-Path $Destinazione 'python.cmd') -Encoding ASCII -Value '@"%~dp0venv\Scripts\python.exe" %*'
Set-Content -LiteralPath (Join-Path $Destinazione 'attiva.cmd') -Encoding ASCII -Value '@call "%~dp0venv\Scripts\activate.bat"'
Set-Content -LiteralPath (Join-Path $Destinazione $marca) -Encoding ASCII -Value @(
    "La Ruota 2.15.0 gfx906 (ROCm $versioneRocm) - installata il $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
    "cartella=$Destinazione",
    "shim=$shim",
    "cache_miopen=$cacheMiopen",
    'variabili_utente=nessuna'
)

# 7. Verifica
if ($SenzaVerifica) { Write-Host 'ESITO: OK - installata, verifica saltata'; exit 0 }
Write-Host ''
& $vpy -I (Join-Path $Destinazione 'verifica.py')
exit $LASTEXITCODE

# La Ruota 2.15 - disinstallazione. Solo ASCII.
# Uso: disinstalla.cmd [-Destinazione <cartella>]
# Toglie la cartella d'installazione (venv compreso) e la cache di MIOpen della ruota.
# Non tocca variabili d'ambiente (l'installazione non ne imposta) ne' altro.
param([string]$Destinazione = '')
$ErrorActionPreference = 'Stop'
$qui = Split-Path -Parent $MyInvocation.MyCommand.Path
$marca = 'la-ruota.installazione'
if (-not $Destinazione) {
    if (Test-Path (Join-Path $qui $marca)) { $Destinazione = $qui } else { $Destinazione = Join-Path $env:LOCALAPPDATA '2S\la-ruota-2.15' }
}
$Destinazione = [IO.Path]::GetFullPath($Destinazione)
if (-not (Test-Path (Join-Path $Destinazione $marca))) {
    Write-Host "ESITO: FALLITO - $Destinazione non contiene un'installazione di La Ruota ($marca)" -ForegroundColor Red
    exit 1
}
$cacheMiopen = Join-Path $Destinazione 'miopen-cache'
Write-Host "La Ruota 2.15 - disinstallo $Destinazione"
# Se lo script gira dalla cartella da togliere, si lavora da una copia temporanea.
if ($qui -eq $Destinazione) {
    $tmp = Join-Path $env:TEMP ('la-ruota-disinstalla-' + [guid]::NewGuid().ToString('N') + '.ps1')
    Copy-Item -LiteralPath $MyInvocation.MyCommand.Path $tmp
    Set-Location $env:TEMP
    & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp -Destinazione $Destinazione
    $rc = $LASTEXITCODE
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    exit $rc
}
Remove-Item -LiteralPath $Destinazione -Recurse -Force
if (Test-Path $cacheMiopen) { Remove-Item -LiteralPath $cacheMiopen -Recurse -Force }
foreach ($d in @((Join-Path $env:LOCALAPPDATA '2S\la-ruota-2.15'), (Join-Path $env:LOCALAPPDATA '2S'))) {
    if ((Test-Path $d) -and -not (Get-ChildItem -LiteralPath $d -Force)) { Remove-Item -LiteralPath $d -Force }
}
$resti = @($Destinazione, $cacheMiopen) | Where-Object { Test-Path $_ }
if ($resti) { Write-Host "ESITO: FALLITO - restano: $($resti -join ', ')" -ForegroundColor Red; exit 1 }
Write-Host 'ESITO: OK - La Ruota 2.15 disinstallata, nessun file rimasto'
exit 0

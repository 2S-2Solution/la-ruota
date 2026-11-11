# Verifica che il runtime Adrenalin (amdhip64.dll) esporti tutti i simboli
# che i binari di torch importano oggi dal proxy amdhip64_6.dll.
$dumpbin = (Get-Content 'C:\LaRuota_workspace\dumpbin_path.txt' -Raw).Trim()
$lib = 'C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib'

$need = @()
foreach ($n in @('c10_hip.dll', 'torch_hip.dll')) {
    $out = & $dumpbin /IMPORTS "$lib\$n" 2>$null
    $inBlock = $false
    foreach ($line in $out) {
        if ($line -match 'amdhip64_6\.dll') { $inBlock = $true; continue }
        if ($inBlock -and $line -match '^\s{4}\S+\.dll') { $inBlock = $false }
        # righe import: "<hint hex>  <nome>"  oppure  "<ordinal>  Ordinal   N"
        if ($inBlock -and $line -match '^\s+[0-9A-F]+\s+([A-Za-z_?][\w:?@$]*)\s*$') { $need += $Matches[1] }
    }
}
$need = $need | Sort-Object -Unique
Write-Output "simboli richiesti ad amdhip64_6.dll: $($need.Count)"

$adr = 'C:\Windows\System32\amdhip64.dll'
Write-Output "runtime esaminato: $adr (esiste: $(Test-Path $adr))"
$have = & $dumpbin /EXPORTS $adr 2>$null | ForEach-Object {
    if ($_ -match '^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]{8}\s+(\S+)') { $Matches[1] }
}
Write-Output "export del runtime: $($have.Count)"

$missing = $need | Where-Object { $have -notcontains $_ }
Write-Output "MANCANTI nel runtime Adrenalin: $($missing.Count)"
$missing | Select-Object -First 60

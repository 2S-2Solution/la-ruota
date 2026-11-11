# 1) Trova l'export di amdhip64.dll piu' vicino (da sotto) all'RVA del crash.
# 2) Verifica se il runtime espone le varianti versionate ROCm 6.x (R0600),
#    che indicherebbero un cambio di layout di hipDeviceProp_t rispetto ai
#    header 5.7 con cui torch e' stato compilato.
$dumpbin = (Get-Content 'C:\LaRuota_workspace\dumpbin_path.txt' -Raw).Trim()
$adr = 'C:\Windows\System32\amdhip64.dll'
$crashRva = 0x42c630

$exp = @()
& $dumpbin /EXPORTS $adr 2>$null | ForEach-Object {
    if ($_ -match '^\s+\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)') {
        $exp += [pscustomobject]@{ Rva = [Convert]::ToInt64($Matches[1], 16); Name = $Matches[2] }
    }
}
Write-Output "export totali: $($exp.Count)"
$sotto = $exp | Where-Object { $_.Rva -le $crashRva } | Sort-Object Rva -Descending | Select-Object -First 3
Write-Output "`nexport piu' vicini sotto RVA 0x$($crashRva.ToString('x')):"
$sotto | ForEach-Object { "  0x{0:x}  (+0x{1:x})  {2}" -f $_.Rva, ($crashRva - $_.Rva), $_.Name }

Write-Output "`nvarianti versionate presenti nel runtime:"
$exp | Where-Object { $_.Name -match 'R0[0-9]{3}$' } | ForEach-Object { "  $($_.Name)" }

Write-Output "`nsimboli hipGetDeviceProperties* nel runtime:"
$exp | Where-Object { $_.Name -match 'GetDeviceProp' } | ForEach-Object { "  $($_.Name)" }

Write-Output "`nsimboli hipGetDeviceProperties* IMPORTATI da torch:"
$lib = 'C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib'
foreach ($n in @('c10_hip.dll', 'torch_hip.dll')) {
    $out = @(& $dumpbin /IMPORTS "$lib\$n" 2>$null)
    $inBlock = $false
    foreach ($line in $out) {
        if ($line -match '^\s{4}(\S+\.dll)') { $inBlock = ($Matches[1] -ieq 'amdhip64.dll'); continue }
        if ($inBlock -and $line -match '^\s+[0-9A-F]+\s+(\S*GetDeviceProp\S*)\s*$') { "  $n -> $($Matches[1])" }
    }
}

# Cerca duplicazione di stato del caching allocator HIP fra c10_hip.dll e torch_hip.dll.
# Se torch_hip ESPORTA simboli dell'allocator invece di IMPORTARLI da c10_hip,
# nel processo esistono due singleton distinti -> puntatori nulli -> access violation.
$dumpbin = (Get-Content 'C:\LaRuota_workspace\dumpbin_path.txt' -Raw).Trim()
$lib = 'C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib'

function Get-Exports($path) {
    & $dumpbin /EXPORTS $path 2>$null | ForEach-Object {
        if ($_ -match '^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]{8}\s+(\S+)') { $Matches[1] }
    }
}

function Get-ImportsFrom($path, $dll) {
    $out = @(& $dumpbin /IMPORTS $path 2>$null)
    $res = @(); $inBlock = $false
    for ($j = 0; $j -lt $out.Count; $j++) {
        $line = $out[$j]
        if ($line -match '^\s{4}(\S+\.dll)') {
            $inBlock = ($Matches[1] -ieq $dll); continue
        }
        if ($inBlock -and $line -match '^\s+[0-9A-F]+\s+([A-Za-z_?][\w:?@$]*)\s*$') { $res += $Matches[1] }
    }
    $res
}

$pat = 'HIPCachingAllocator|CUDACachingAllocator'

$c10Exp = @(Get-Exports "$lib\c10_hip.dll" | Where-Object { $_ -match $pat })
$thExp = @(Get-Exports "$lib\torch_hip.dll" | Where-Object { $_ -match $pat })
$thImp = @(Get-ImportsFrom "$lib\torch_hip.dll" 'c10_hip.dll' | Where-Object { $_ -match $pat })

Write-Output "c10_hip  ESPORTA allocator : $($c10Exp.Count)"
Write-Output "torch_hip IMPORTA da c10_hip: $($thImp.Count)"
Write-Output "torch_hip ESPORTA allocator : $($thExp.Count)   <-- se > 0 c'e' duplicazione"

$dup = $thExp | Where-Object { $c10Exp -contains $_ }
Write-Output ""
Write-Output "SIMBOLI DEFINITI IN ENTRAMBE LE DLL: $($dup.Count)"
$dup | Select-Object -First 25

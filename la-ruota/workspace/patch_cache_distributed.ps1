# Attiva distributed nella cache CMake.
# Serve perche':
#  1. in modalita' "resume" setup.py NON ripassa le variabili USE_* a CMake: vince la cache;
#  2. cmake_dependent_option usa option(), che NON sovrascrive una voce di cache gia'
#     esistente: USE_C10D_GLOO resta a OFF anche quando le dipendenze sono soddisfatte.
# ATTENZIONE 1: scrivere SENZA BOM, o setup.py fallisce con ValueError.
# ATTENZIONE 2: niente caratteri non-ASCII (PowerShell 5.1 legge gli script in ANSI).
$cache = 'C:\LaRuota_workspace\pytorch_src\build\CMakeCache.txt'

$attesi = @{
    'USE_DISTRIBUTED' = '1'
    'USE_GLOO'        = 'ON'
    'USE_C10D_GLOO'   = 'ON'
}

$righe = [System.IO.File]::ReadAllLines($cache)
$n = 0
for ($i = 0; $i -lt $righe.Count; $i++) {
    foreach ($k in $attesi.Keys) {
        if ($righe[$i] -match "^$k(:[A-Z]+)=(.*)$") {
            $tipo = $Matches[1]
            $val = $Matches[2]
            if ($val -ne $attesi[$k]) {
                $righe[$i] = "$k$tipo=$($attesi[$k])"
                $n++
                Write-Output "corretto: $($righe[$i])   (era $val)"
            }
        }
    }
}
if ($n -gt 0) {
    [System.IO.File]::WriteAllLines($cache, $righe, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output "cache aggiornata (senza BOM)"
    $ora = Get-Date
    foreach ($f in @('C:\LaRuota_workspace\pytorch_src\CMakeLists.txt',
            'C:\LaRuota_workspace\pytorch_src\caffe2\CMakeLists.txt')) {
        (Get-Item $f).LastWriteTime = $ora
    }
    Write-Output "CMakeLists toccati per forzare la riconfigurazione"
}
else {
    Write-Output "nessuna modifica necessaria"
}

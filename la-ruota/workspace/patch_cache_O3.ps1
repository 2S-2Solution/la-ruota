# Imposta CMAKE_HIP_FLAGS_RELEASE nella cache (era vuoto -> device code a -O0).
# Come per il flag COv4, _INIT/FORCE nel CMakeLists non basta: la voce e' gia' in cache.
# ATTENZIONE: scrivere SENZA BOM, altrimenti setup.py fallisce con ValueError.
$cache = 'C:\LaRuota_workspace\pytorch_src\build\CMakeCache.txt'
$righe = [System.IO.File]::ReadAllLines($cache)
$modificato = $false
for ($i = 0; $i -lt $righe.Count; $i++) {
    if ($righe[$i] -match '^CMAKE_HIP_FLAGS_RELEASE:STRING=') {
        $righe[$i] = 'CMAKE_HIP_FLAGS_RELEASE:STRING=-O3 -DNDEBUG'
        $modificato = $true
        Write-Output "riga: $($righe[$i])"
    }
    elseif ($righe[$i] -match '^CMAKE_HIP_FLAGS_RELWITHDEBINFO:STRING=') {
        $righe[$i] = 'CMAKE_HIP_FLAGS_RELWITHDEBINFO:STRING=-O2 -DNDEBUG'
        Write-Output "riga: $($righe[$i])"
    }
}
if ($modificato) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($cache, $righe, $enc)
    Write-Output "cache aggiornata (senza BOM)"
}
else {
    Write-Output "ATTENZIONE: voce CMAKE_HIP_FLAGS_RELEASE non trovata"
}

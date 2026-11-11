# Aggiunge -mcode-object-version=4 a CMAKE_HIP_FLAGS gia' in cache.
# CMAKE_HIP_FLAGS_INIT agisce solo alla prima configurazione del linguaggio HIP,
# quindi senza questo la cache continuerebbe a imporre i flag vecchi.
# ATTENZIONE: scrivere SENZA BOM, altrimenti setup.py fallisce con ValueError.
$cache = 'C:\LaRuota_workspace\pytorch_src\build\CMakeCache.txt'
$righe = [System.IO.File]::ReadAllLines($cache)
$fatto = $false
for ($i = 0; $i -lt $righe.Count; $i++) {
    if ($righe[$i] -match '^CMAKE_HIP_FLAGS:STRING=') {
        if ($righe[$i] -notmatch 'code-object-version') {
            $righe[$i] = $righe[$i] + ' -mcode-object-version=4'
            $fatto = $true
        }
        Write-Output "riga: $($righe[$i])"
    }
}
if ($fatto) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($cache, $righe, $enc)
    Write-Output "cache aggiornata (senza BOM)"
}
else {
    Write-Output "nessuna modifica necessaria"
}

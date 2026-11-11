# Corregge il percorso degli header numpy nella cache CMake.
# La cache conservava .../numpy/_core/include (layout di un'altra versione di numpy),
# che su questa venv NON esiste: gli header stanno in .../numpy/core/include.
# Difetto latente: emerge solo quando torch_python deve essere ricompilato.
# ATTENZIONE 1: scrivere SENZA BOM, altrimenti setup.py fallisce con ValueError.
# ATTENZIONE 2: niente caratteri non-ASCII in questo file. PowerShell 5.1 legge gli
# script in ANSI e un trattino lungo basta a far fallire il parsing.
$cache = 'C:\LaRuota_workspace\pytorch_src\build\CMakeCache.txt'
$py = 'C:\LaRuota_workspace\venv_build\Scripts\python.exe'

$vero = (& $py -c "import numpy; print(numpy.get_include())").Trim().Replace('\', '/')
if (-not (Test-Path (Join-Path $vero 'numpy/arrayobject.h'))) {
    Write-Output "ATTENZIONE: arrayobject.h non trovato in $vero - non tocco nulla"
    exit 1
}
Write-Output "percorso reale: $vero"

$righe = [System.IO.File]::ReadAllLines($cache)
$n = 0
for ($i = 0; $i -lt $righe.Count; $i++) {
    if ($righe[$i] -match '^(_Python_NumPy_INCLUDE_DIR:INTERNAL=)(.*)$') {
        if ($Matches[2] -ne $vero) {
            $righe[$i] = $Matches[1] + $vero
            $n++
            Write-Output "corretto: $($righe[$i])"
        }
    }
}
if ($n -gt 0) {
    [System.IO.File]::WriteAllLines($cache, $righe, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output "cache aggiornata (senza BOM)"
}
else {
    Write-Output "nessuna modifica necessaria"
}

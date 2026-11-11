# Verifica quali code object version il compilatore del Marconi pack sa emettere.
$cc = 'C:\rocm_5_7_expansion_pack\compiler\bin\clang-cl.exe'
$src = "$env:TEMP\cov_test.hip"
@'
#include <hip/hip_runtime.h>
__global__ void k(float* p) { p[threadIdx.x] = 1.0f; }
'@ | Set-Content -Path $src -Encoding ascii

$py = 'C:\LaRuota_workspace\venv_build\Scripts\python.exe'
$scan = "$env:TEMP\scan_cov.py"
@'
import sys
from collections import Counter
NOMI = {0:"COv2",1:"COv3",2:"COv4",3:"COv5",4:"COv6"}
data = open(sys.argv[1],"rb").read()
c = Counter()
i = 0
while True:
    i = data.find(b"\x7fELF", i)
    if i < 0 or i+16 > len(data): break
    if data[i+7] == 64: c[data[i+8]] += 1
    i += 4
print("  -> " + (", ".join(f"{NOMI.get(v,v)}x{n}" for v,n in sorted(c.items())) if c else "nessun ELF AMDGPU"))
'@ | Set-Content -Path $scan -Encoding ascii

foreach ($v in @('4', '5', '6')) {
    $obj = "$env:TEMP\cov_$v.obj"
    if (Test-Path $obj) { Remove-Item $obj -Force }
    $out = & $cc -x hip "--rocm-path=C:\rocm_5_7_expansion_pack" `
        "--rocm-device-lib-path=C:\rocm_5_7_expansion_pack/device_libs" `
        --offload-arch=gfx906 "-mcode-object-version=$v" -c $src -o $obj 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and (Test-Path $obj)) {
        Write-Output "-mcode-object-version=$v : COMPILA"
        & $py $scan $obj
    }
    else {
        Write-Output "-mcode-object-version=$v : RIFIUTATO"
        ($out -split "`n" | Where-Object { $_ -match 'error|invalid|unsupported' } | Select-Object -First 2) | ForEach-Object { "    $($_.Trim())" }
    }
}

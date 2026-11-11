"""[VEGA-PATCH 48 1 ago] Stub delle chiamate hipblas*Batched non presenti in ROCm 5.7.

Diagnosi: torch_hip.dll importa 12 DLL; 11 combaciano perfettamente con lo stack 5.7
(rocblas, MIOpen, hipsparse, hipsolver, hipblaslt: zero simboli mancanti). L'unica
eccezione e' hipblas, con 16 routine *Batched (getrf/getrs/geqrf/gels) introdotte dopo
la 5.7.

Invece di escludere interi file (che toglie anche simboli usati altrove), sostituiamo
SOLO il corpo dei wrapper in HIPBlas.cpp con un TORCH_CHECK(false, ...): i simboli
restano definiti, l'import verso hipblas sparisce, e chi chiama quelle op riceve un
errore chiaro invece di un comportamento errato.
"""
import re

PATH = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\hip\HIPBlas.cpp"

with open(PATH, encoding="utf-8", errors="surrogateescape") as f:
    src = f.read()

# ogni chiamata TORCH_HIPBLAS_CHECK(hipblas?<op>Batched( ... ));  -> TORCH_CHECK(false, ...)
pattern = re.compile(
    r"TORCH_HIPBLAS_CHECK\(\s*(hipblas[SDCZ](?:getrf|getrs|geqrf|gels)Batched)\s*\((?:[^;]*?)\)\s*\);",
    re.DOTALL,
)

MSG = ('TORCH_CHECK(false, "\\1 non disponibile: hipBLAS di ROCm 5.7 non espone le '
       'routine *Batched (introdotte dopo). [VEGA-PATCH 48]");')

new, n = pattern.subn(MSG, src)
print("chiamate stubbate:", n)

if n:
    with open(PATH, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(new)

resid = re.findall(r"hipblas[SDCZ](?:getrf|getrs|geqrf|gels)Batched\s*\(", new)
print("residui non stubbati:", len(resid))
for r in set(resid):
    print("   ", r)

"""VEGA-PATCH 81 - eigh e svd di tensori GPU calcolate con MKL sulla CPU (copie comprese).

Misurato il 20 ott (banco_svd_cpu_gpu.py [--eigh], GPU in parte occupata da un altro processo):
rocSOLVER su gfx906 e' da 20 a 114 volte piu' lento di MKL, copie comprese:

    svd  1000x96 209 ms contro 15 | 512^2 1,28 s contro 22 ms | 1024^2 9,1 s contro 0,12 | 2048^2 68 s contro 0,6
    eigh 64^2 8,8 ms contro 0,4   | 512^2 305 ms contro 10    | 1024^2 1,66 s contro 41 ms | 2048^2 16 s contro 0,2

La GPU vince solo per la svd di tante matrici minuscole (100x32x32: 7,8 contro 15 ms). La
VEGA-PATCH 78 aveva reso eigh giusta e svd ripetibile, ma lente. Qui: eigh sempre su MKL;
svd su MKL salvo lotti >= 32 con lato <= 32 (resta rocSOLVER gesvd). Stesso schema di MAGMA,
che per eigh lavora in memoria della CPU. Risultati giusti e ripetibili (LAPACK di MKL).

    python patch_eigh_svd_su_cpu.py --prova | --applica
"""
import io
import os
import shutil
import sys

F = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\linalg\BatchLinearAlgebra.cpp"
MARCA = "[VEGA-PATCH 81"
SOSTITUZIONI = [
    ("#include <ATen/ops/linalg_eigh.h>\n",
     "#include <ATen/ops/linalg_eigh.h>\n#include <ATen/ops/_linalg_eigh.h>  // [VEGA-PATCH 81]\n"
     "#include <ATen/ops/_linalg_svd.h>   // [VEGA-PATCH 81]\n"),
    ("""                         bool upper, bool compute_eigenvectors) {
  if (eigenvectors.numel() == 0) {
    return;
  }
""",
     """                         bool upper, bool compute_eigenvectors) {
  if (eigenvectors.numel() == 0) {
    return;
  }
  {
    // [VEGA-PATCH 81 - 20 ott 2026] su gfx906 syevd di rocSOLVER e' 20-77x piu' lento di MKL
    // (copie comprese): si calcola sulla CPU. Spiegazione: patch_eigh_svd_su_cpu.py
    auto [valori, vettori] = at::_linalg_eigh(eigenvectors.cpu(), upper ? "U" : "L", compute_eigenvectors);
    eigenvalues.copy_(valori);
    if (compute_eigenvectors) {
      eigenvectors.copy_(vettori);
    }
    infos.zero_();
    return;
  }
"""),
    ("""  const int64_t m = A.size(-2), n = A.size(-1), k = std::min(m, n);
  const int mi = vega67_int(m, "svd: m"), ni = vega67_int(n, "svd: n");
""",
     """  const int64_t m = A.size(-2), n = A.size(-1), k = std::min(m, n);
  if (!(batchCount(A) >= 32 && std::max(m, n) <= 32)) {
    // [VEGA-PATCH 81 - 20 ott 2026] su gfx906 gesvd di rocSOLVER e' fino a 114x piu' lento di
    // MKL (copie comprese); la GPU vince solo con lotti di matrici minuscole. Spiegazione:
    // patch_eigh_svd_su_cpu.py
    auto [u_c, s_c, vh_c] = at::_linalg_svd(A.cpu(), full_matrices, compute_uv, std::nullopt);
    S.copy_(s_c);
    if (compute_uv) {
      U.copy_(u_c);
      Vh.copy_(vh_c);
    }
    info.zero_();
    return;
  }
  const int mi = vega67_int(m, "svd: m"), ni = vega67_int(n, "svd: n");
"""),
]
t = io.open(F, encoding="utf-8", newline="").read()
if MARCA in t:
    print("gia' applicata")
    sys.exit(0)
crlf = "\r\n" in t
errori = 0
for vecchio, nuovo in SOSTITUZIONI:
    if crlf:
        vecchio, nuovo = vecchio.replace("\n", "\r\n"), nuovo.replace("\n", "\r\n")
    n = t.count(vecchio)
    if n != 1:
        print(f"  ERRORE: trovato {n} volte: {vecchio.strip().splitlines()[0][:70]}")
        errori += 1
        continue
    t = t.replace(vecchio, nuovo)
    print(f"  ok: {vecchio.strip().splitlines()[0][:70]}")
if errori:
    sys.exit(1)
if "--applica" in sys.argv:
    if not os.path.exists(F + ".bak_pre_vega81"):
        shutil.copy2(F, F + ".bak_pre_vega81")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

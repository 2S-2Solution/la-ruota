"""VEGA-PATCH 78 - eigh e svd sulla GPU via rocSOLVER, saltando hipSOLVER.

Trovato il 20 ott verificando un modello che usa svd_lowrank.

1. eigh / eigvalsh: SBAGLIATA in silenzio da n=64 in su (autovalori a zero o 1e+35),
   fp32 e fp64, singola e a lotti; giusta fino a 48. Su ROCm USE_LINALG_SOLVER e' definito
   (BatchLinearAlgebraLib.h: `|| defined(USE_ROCM)`) e linalg_eigh_cusolver usa SEMPRE
   syevj via hipSOLVER. rocSOLVER chiamato direttamente (syevj e syevd) e' giusto a tutte le
   dimensioni (prova_rocsolver_syev.py): il difetto e' nello strato hipSOLVER. Il censimento
   provava solo matrici piccole.
2. svd: giusta ma NON ripetibile (hipSOLVER gesvdj: 9e-04 fra due corse identiche). Un modello
   che la usa nella pre-elaborazione (svd_lowrank) dava in due addestramenti uguali sulla GPU davano
   uguali probabilita' diverse fino a 1,6e-02. rocSOLVER gesvd e' giusto (9e-06) e ripetibile
   (0,0), ~40% piu' lento su 2000x64 (prova_rocsolver_gesvd.py).

Rimedio, solo su ROCm senza MAGMA: linalg_eigh_kernel -> rocsolver_?syevd/?heevd
_strided_batched; svd_kernel -> rocsolver_?gesvd_strided_batched. Stesso schema della
VEGA-PATCH 67 (handle, controlli, prototipi). Battuta: battuta_linalg_dimensioni.py.

    python patch_eigh_svd_rocsolver.py --prova
    python patch_eigh_svd_rocsolver.py --applica
"""
import io
import os
import shutil
import sys

F = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\linalg\BatchLinearAlgebra.cpp"
applica = "--applica" in sys.argv
MARCA = "[VEGA-PATCH 78"

ANCORA_DECL = "int rocsolver_zgels_strided_batched(void*, int, int, int, int, void*, int, int64_t, void*, int, int64_t, int*, int);\n"
NUOVE_DECL = ANCORA_DECL + """// [VEGA-PATCH 78] syevd/heevd e gesvd a lotti con passo
int rocsolver_ssyevd_strided_batched(void*, int, int, int, float*, int, int64_t, float*, int64_t, float*, int64_t, int*, int);
int rocsolver_dsyevd_strided_batched(void*, int, int, int, double*, int, int64_t, double*, int64_t, double*, int64_t, int*, int);
int rocsolver_cheevd_strided_batched(void*, int, int, int, void*, int, int64_t, float*, int64_t, float*, int64_t, int*, int);
int rocsolver_zheevd_strided_batched(void*, int, int, int, void*, int, int64_t, double*, int64_t, double*, int64_t, int*, int);
int rocsolver_sgesvd_strided_batched(void*, int, int, int, int, float*, int, int64_t, float*, int64_t, float*, int, int64_t, float*, int, int64_t, float*, int64_t, int, int*, int);
int rocsolver_dgesvd_strided_batched(void*, int, int, int, int, double*, int, int64_t, double*, int64_t, double*, int, int64_t, double*, int, int64_t, double*, int64_t, int, int*, int);
int rocsolver_cgesvd_strided_batched(void*, int, int, int, int, void*, int, int64_t, float*, int64_t, void*, int, int64_t, void*, int, int64_t, float*, int64_t, int, int*, int);
int rocsolver_zgesvd_strided_batched(void*, int, int, int, int, void*, int, int64_t, double*, int64_t, void*, int, int64_t, void*, int, int64_t, double*, int64_t, int, int*, int);
"""

ANCORA_FINE = "}  // namespace (anonymous)\n#endif  // !AT_MAGMA_ENABLED()\n"
AIUTI = r'''// [VEGA-PATCH 78 - 20 ott 2026] eigh e svd via rocSOLVER (hipSOLVER: eigh sbagliata da n=64,
// svd non ripetibile). Spiegazione: C:\LaRuota_workspace\patch_eigh_svd_rocsolver.py
constexpr int kVegaEvectOriginal = 211, kVegaEvectNone = 213;
constexpr int kVegaSvectAll = 191, kVegaSvectSingular = 192, kVegaSvectNone = 194;
constexpr int kVegaOutOfPlace = 201;

template <typename T> int vega78_syevd(void* h, int ev, int up, int n, T* A, int lda, int64_t sA,
    typename c10::scalar_value_type<T>::type* D, int64_t sD, typename c10::scalar_value_type<T>::type* E,
    int64_t sE, int* info, int b);
template <> int vega78_syevd<float>(void* h, int ev, int up, int n, float* A, int lda, int64_t sA, float* D, int64_t sD, float* E, int64_t sE, int* info, int b) {
  return rocsolver_ssyevd_strided_batched(h, ev, up, n, A, lda, sA, D, sD, E, sE, info, b); }
template <> int vega78_syevd<double>(void* h, int ev, int up, int n, double* A, int lda, int64_t sA, double* D, int64_t sD, double* E, int64_t sE, int* info, int b) {
  return rocsolver_dsyevd_strided_batched(h, ev, up, n, A, lda, sA, D, sD, E, sE, info, b); }
template <> int vega78_syevd<c10::complex<float>>(void* h, int ev, int up, int n, c10::complex<float>* A, int lda, int64_t sA, float* D, int64_t sD, float* E, int64_t sE, int* info, int b) {
  return rocsolver_cheevd_strided_batched(h, ev, up, n, A, lda, sA, D, sD, E, sE, info, b); }
template <> int vega78_syevd<c10::complex<double>>(void* h, int ev, int up, int n, c10::complex<double>* A, int lda, int64_t sA, double* D, int64_t sD, double* E, int64_t sE, int* info, int b) {
  return rocsolver_zheevd_strided_batched(h, ev, up, n, A, lda, sA, D, sD, E, sE, info, b); }

template <typename T> int vega78_gesvd(void* h, int sl, int sr, int m, int n, T* A, int lda, int64_t sA,
    typename c10::scalar_value_type<T>::type* S, int64_t sS, T* U, int ldu, int64_t sU, T* V, int ldv, int64_t sV,
    typename c10::scalar_value_type<T>::type* E, int64_t sE, int* info, int b);
template <> int vega78_gesvd<float>(void* h, int sl, int sr, int m, int n, float* A, int lda, int64_t sA, float* S, int64_t sS, float* U, int ldu, int64_t sU, float* V, int ldv, int64_t sV, float* E, int64_t sE, int* info, int b) {
  return rocsolver_sgesvd_strided_batched(h, sl, sr, m, n, A, lda, sA, S, sS, U, ldu, sU, V, ldv, sV, E, sE, kVegaOutOfPlace, info, b); }
template <> int vega78_gesvd<double>(void* h, int sl, int sr, int m, int n, double* A, int lda, int64_t sA, double* S, int64_t sS, double* U, int ldu, int64_t sU, double* V, int ldv, int64_t sV, double* E, int64_t sE, int* info, int b) {
  return rocsolver_dgesvd_strided_batched(h, sl, sr, m, n, A, lda, sA, S, sS, U, ldu, sU, V, ldv, sV, E, sE, kVegaOutOfPlace, info, b); }
template <> int vega78_gesvd<c10::complex<float>>(void* h, int sl, int sr, int m, int n, c10::complex<float>* A, int lda, int64_t sA, float* S, int64_t sS, c10::complex<float>* U, int ldu, int64_t sU, c10::complex<float>* V, int ldv, int64_t sV, float* E, int64_t sE, int* info, int b) {
  return rocsolver_cgesvd_strided_batched(h, sl, sr, m, n, A, lda, sA, S, sS, U, ldu, sU, V, ldv, sV, E, sE, kVegaOutOfPlace, info, b); }
template <> int vega78_gesvd<c10::complex<double>>(void* h, int sl, int sr, int m, int n, c10::complex<double>* A, int lda, int64_t sA, double* S, int64_t sS, c10::complex<double>* U, int ldu, int64_t sU, c10::complex<double>* V, int ldv, int64_t sV, double* E, int64_t sE, int* info, int b) {
  return rocsolver_zgesvd_strided_batched(h, sl, sr, m, n, A, lda, sA, S, sS, U, ldu, sU, V, ldv, sV, E, sE, kVegaOutOfPlace, info, b); }

// autovalori (e autovettori, sul posto in eigenvectors) con syevd/heevd
void vega_eigh_rocsolver(const Tensor& eigenvalues, const Tensor& eigenvectors, const Tensor& infos,
                         bool upper, bool compute_eigenvectors) {
  if (eigenvectors.numel() == 0) {
    return;
  }
  Tensor work = vega67_colonne(eigenvectors);
  const int n = vega67_int(eigenvectors.size(-1), "eigh: n");
  const int batch = vega67_int(batchCount(eigenvectors), "eigh: lotto");
  Tensor valori = eigenvalues.is_contiguous() ? eigenvalues : at::empty_like(eigenvalues, at::MemoryFormat::Contiguous);
  Tensor info_dev = (infos.is_cuda() && infos.is_contiguous() && infos.scalar_type() == at::kInt)
      ? infos : at::empty({batch}, eigenvectors.options().dtype(at::kInt));
  Tensor e = at::empty({batch, n}, valori.options());
  AT_DISPATCH_FLOATING_AND_COMPLEX_TYPES(eigenvectors.scalar_type(), "eigh_rocsolver", [&] {
    using value_t = typename c10::scalar_value_type<scalar_t>::type;
    VEGA67_CHECK(vega78_syevd<scalar_t>(vega67_handle(), compute_eigenvectors ? kVegaEvectOriginal : kVegaEvectNone,
                                        upper ? kVegaFillUpper : kVegaFillLower, n, work.data_ptr<scalar_t>(),
                                        std::max(1, n), matrixStride(work), valori.data_ptr<value_t>(), n,
                                        e.data_ptr<value_t>(), n, info_dev.data_ptr<int>(), batch),
                 "eigh");
  });
  if (compute_eigenvectors && !work.is_same(eigenvectors)) {
    eigenvectors.copy_(work);
  }
  if (!valori.is_same(eigenvalues)) {
    eigenvalues.copy_(valori);
  }
  if (!info_dev.is_same(infos)) {
    infos.copy_(info_dev.view(infos.sizes()));
  }
}

// SVD con gesvd. U e Vh hanno la forma che PyTorch ha preparato (qualunque disposizione)
void vega_svd_rocsolver(const Tensor& A, bool full_matrices, bool compute_uv,
                        const Tensor& U, const Tensor& S, const Tensor& Vh, const Tensor& info) {
  const int64_t m = A.size(-2), n = A.size(-1), k = std::min(m, n);
  const int mi = vega67_int(m, "svd: m"), ni = vega67_int(n, "svd: n");
  const int batch = vega67_int(batchCount(A), "svd: lotto");
  Tensor a = cloneBatchedColumnMajor(A);
  const int sv = compute_uv ? (full_matrices ? kVegaSvectAll : kVegaSvectSingular) : kVegaSvectNone;
  const int64_t ucol = full_matrices ? m : k, vrig = full_matrices ? n : k;
  Tensor u, vh;
  if (compute_uv) {
    u = vega67_colonne(U);
    vh = at::empty_like(Vh.mT(), at::MemoryFormat::Contiguous).mT();   // [.., vrig, n] a colonne
  } else {
    u = at::empty({1}, A.options());
    vh = at::empty({1}, A.options());
  }
  Tensor s = S.is_contiguous() ? S : at::empty_like(S, at::MemoryFormat::Contiguous);
  Tensor e = at::empty({batch, std::max<int64_t>(k, 1)}, s.options());
  Tensor info_dev = (info.is_cuda() && info.is_contiguous() && info.scalar_type() == at::kInt)
      ? info : at::empty({batch}, A.options().dtype(at::kInt));
  AT_DISPATCH_FLOATING_AND_COMPLEX_TYPES(A.scalar_type(), "svd_rocsolver", [&] {
    using value_t = typename c10::scalar_value_type<scalar_t>::type;
    VEGA67_CHECK(vega78_gesvd<scalar_t>(
                     vega67_handle(), sv, sv, mi, ni, a.data_ptr<scalar_t>(), std::max(1, mi), matrixStride(a),
                     s.data_ptr<value_t>(), k, u.data_ptr<scalar_t>(), compute_uv ? std::max(1, mi) : 1,
                     compute_uv ? m * ucol : 0, vh.data_ptr<scalar_t>(),
                     compute_uv ? vega67_int(std::max<int64_t>(1, vrig), "svd: ldv") : 1,
                     compute_uv ? vrig * n : 0, e.data_ptr<value_t>(), std::max<int64_t>(k, 1),
                     info_dev.data_ptr<int>(), batch),
                 "svd");
  });
  if (compute_uv) {
    if (!u.is_same(U)) {
      U.copy_(u);
    }
    Vh.copy_(vh);
  }
  if (!s.is_same(S)) {
    S.copy_(s);
  }
  if (!info_dev.is_same(info)) {
    info.copy_(info_dev.view(info.sizes()));
  }
}

'''

VECCHIO_EIGH = "void linalg_eigh_kernel(const Tensor& eigenvalues, const Tensor& eigenvectors, const Tensor& infos, bool upper, bool compute_eigenvectors) {\n#if defined(USE_LINALG_SOLVER)\n"
NUOVO_EIGH = ("void linalg_eigh_kernel(const Tensor& eigenvalues, const Tensor& eigenvectors, const Tensor& infos, bool upper, bool compute_eigenvectors) {\n"
              "#if defined(USE_ROCM) && !AT_MAGMA_ENABLED()\n"
              "  // [VEGA-PATCH 78] su ROCm syevj via hipSOLVER sbaglia da n=64: rocSOLVER syevd\n"
              "  vega_eigh_rocsolver(eigenvalues, eigenvectors, infos, upper, compute_eigenvectors);\n"
              "  return;\n"
              "#endif\n"
              "#if defined(USE_LINALG_SOLVER)\n")
VECCHIO_SVD = """                const Tensor& info) {
#ifdef USE_LINALG_SOLVER
  // We always use cuSOLVER unless the user has specified they want to use MAGMA"""
NUOVO_SVD = """                const Tensor& info) {
#if defined(USE_ROCM) && !AT_MAGMA_ENABLED()
  // [VEGA-PATCH 78] su ROCm gesvdj via hipSOLVER non e' ripetibile: rocSOLVER gesvd
  (void)driver;
  vega_svd_rocsolver(A, full_matrices, compute_uv, U, S, Vh, info);
  return;
#endif
#ifdef USE_LINALG_SOLVER
  // We always use cuSOLVER unless the user has specified they want to use MAGMA"""

t = io.open(F, encoding="utf-8", newline="").read()
if MARCA in t:
    print("gia' applicata")
    sys.exit(0)
crlf = "\r\n" in t
errori = 0
for vecchio, nuovo in ((ANCORA_DECL, NUOVE_DECL), (ANCORA_FINE, AIUTI + ANCORA_FINE),
                       (VECCHIO_EIGH, NUOVO_EIGH), (VECCHIO_SVD, NUOVO_SVD)):
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
if applica:
    if not os.path.exists(F + ".bak_pre_vega78"):
        shutil.copy2(F, F + ".bak_pre_vega78")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

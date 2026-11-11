"""VEGA-PATCH 67 - cholesky, cholesky_solve, cholesky_inverse e lstsq su GPU via rocSOLVER.

Sulla GPU queste quattro operazioni avevano un solo percorso: MAGMA, che la ruota non
compila. Il percorso cuSOLVER/hipSOLVER per queste quattro e' escluso da upstream per ROCm
(`defined(USE_LINALG_SOLVER) && !defined(USE_ROCM)`). Risultato: "requires compiling
PyTorch with MAGMA". [Corretto il 20 ott: qui si diceva anche che USE_LINALG_SOLVER non
fosse definito. E' falso: BatchLinearAlgebraLib.h lo definisce con `|| defined(USE_ROCM)`,
ed e' cosi' che eigh e svd finivano su hipSOLVER - vedi VEGA-PATCH 78.]

Non e' un limite di ROCm: rocSOLVER 5.7 (gia' importata da torch_hip, VEGA-PATCH 64)
esporta potrf/potrs/gels *_strided_batched* in tutte e quattro le precisioni. Qui, solo
quando MAGMA manca (`!AT_MAGMA_ENABLED()`), le quattro operazioni vanno su rocSOLVER:

  cholesky / cholesky_ex  -> rocsolver_?potrf_strided_batched
  cholesky_solve          -> rocsolver_?potrs_strided_batched
  cholesky_inverse        -> potrs contro l'identita' (lo stesso metodo del ramo MAGMA)
  lstsq                   -> rocsolver_?gels_strided_batched; copre anche m < n, che
                             il ramo MAGMA rifiutava

Con MAGMA compilata il comportamento torna quello originale.

    python patch_cholesky_lstsq_rocsolver.py --prova
    python patch_cholesky_lstsq_rocsolver.py --applica
"""
import io
import os
import shutil
import sys

F = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\linalg\BatchLinearAlgebra.cpp"
MARCA = "[VEGA-PATCH 67]"
applica = "--applica" in sys.argv

# ---------------------------------------------------------------- 1. dichiarazioni C
DICHIARAZIONI = r'''
#if !AT_MAGMA_ENABLED()
// [VEGA-PATCH 67] prototipi di rocSOLVER 5.7, con handle e dati complessi come void*
// (rocblas_int = int, rocblas_stride = int64_t, enum come int). rocsolver.lib e' gia'
// collegata a torch_hip dalla VEGA-PATCH 64. Spiegazione:
// C:\LaRuota_workspace\patch_cholesky_lstsq_rocsolver.py
extern "C" {
int rocsolver_spotrf_strided_batched(void*, int, int, float*, int, int64_t, int*, int);
int rocsolver_dpotrf_strided_batched(void*, int, int, double*, int, int64_t, int*, int);
int rocsolver_cpotrf_strided_batched(void*, int, int, void*, int, int64_t, int*, int);
int rocsolver_zpotrf_strided_batched(void*, int, int, void*, int, int64_t, int*, int);
int rocsolver_spotrs_strided_batched(void*, int, int, int, float*, int, int64_t, float*, int, int64_t, int);
int rocsolver_dpotrs_strided_batched(void*, int, int, int, double*, int, int64_t, double*, int, int64_t, int);
int rocsolver_cpotrs_strided_batched(void*, int, int, int, void*, int, int64_t, void*, int, int64_t, int);
int rocsolver_zpotrs_strided_batched(void*, int, int, int, void*, int, int64_t, void*, int, int64_t, int);
int rocsolver_sgels_strided_batched(void*, int, int, int, int, float*, int, int64_t, float*, int, int64_t, int*, int);
int rocsolver_dgels_strided_batched(void*, int, int, int, int, double*, int, int64_t, double*, int, int64_t, int*, int);
int rocsolver_cgels_strided_batched(void*, int, int, int, int, void*, int, int64_t, void*, int, int64_t, int*, int);
int rocsolver_zgels_strided_batched(void*, int, int, int, int, void*, int, int64_t, void*, int, int64_t, int*, int);
}
#endif

namespace at::native {
'''

# ---------------------------------------------------------------- 2. funzioni d'appoggio
APPOGGIO = r'''namespace lazy_linalg {
#endif

#if !AT_MAGMA_ENABLED()
// [VEGA-PATCH 67] cholesky, cholesky_solve, cholesky_inverse e lstsq via rocSOLVER
namespace {

constexpr int kVegaFillUpper = 121;   // rocblas_fill_upper
constexpr int kVegaFillLower = 122;   // rocblas_fill_lower
constexpr int kVegaOpNone = 111;      // rocblas_operation_none

#define VEGA67_CHECK(EXPR, NOME)                                                    \
  do {                                                                              \
    const int vega_stato_ = (EXPR);                                                 \
    TORCH_CHECK(vega_stato_ == 0, NOME, ": rocSOLVER ha restituito lo stato ",      \
                vega_stato_, " [VEGA-PATCH 67]");                                   \
  } while (0)

inline void* vega67_handle() {
  // l'handle hipBLAS su AMD e' un rocblas_handle, gia' legato al flusso corrente
  return reinterpret_cast<void*>(at::hip::getCurrentHIPBlasHandle());
}

inline int vega67_int(int64_t v, const char* nome) {
  TORCH_CHECK(v >= 0 && v <= std::numeric_limits<int>::max(), nome,
              " fuori dall'intervallo di rocSOLVER [VEGA-PATCH 67]");
  return static_cast<int>(v);
}

template <typename T> int vega67_potrf(void* h, int uplo, int n, T* A, int lda, int64_t sA, int* info, int b);
template <> int vega67_potrf<float>(void* h, int uplo, int n, float* A, int lda, int64_t sA, int* info, int b) {
  return rocsolver_spotrf_strided_batched(h, uplo, n, A, lda, sA, info, b); }
template <> int vega67_potrf<double>(void* h, int uplo, int n, double* A, int lda, int64_t sA, int* info, int b) {
  return rocsolver_dpotrf_strided_batched(h, uplo, n, A, lda, sA, info, b); }
template <> int vega67_potrf<c10::complex<float>>(void* h, int uplo, int n, c10::complex<float>* A, int lda, int64_t sA, int* info, int b) {
  return rocsolver_cpotrf_strided_batched(h, uplo, n, A, lda, sA, info, b); }
template <> int vega67_potrf<c10::complex<double>>(void* h, int uplo, int n, c10::complex<double>* A, int lda, int64_t sA, int* info, int b) {
  return rocsolver_zpotrf_strided_batched(h, uplo, n, A, lda, sA, info, b); }

template <typename T> int vega67_potrs(void* h, int uplo, int n, int nrhs, T* A, int lda, int64_t sA, T* B, int ldb, int64_t sB, int b);
template <> int vega67_potrs<float>(void* h, int uplo, int n, int nrhs, float* A, int lda, int64_t sA, float* B, int ldb, int64_t sB, int b) {
  return rocsolver_spotrs_strided_batched(h, uplo, n, nrhs, A, lda, sA, B, ldb, sB, b); }
template <> int vega67_potrs<double>(void* h, int uplo, int n, int nrhs, double* A, int lda, int64_t sA, double* B, int ldb, int64_t sB, int b) {
  return rocsolver_dpotrs_strided_batched(h, uplo, n, nrhs, A, lda, sA, B, ldb, sB, b); }
template <> int vega67_potrs<c10::complex<float>>(void* h, int uplo, int n, int nrhs, c10::complex<float>* A, int lda, int64_t sA, c10::complex<float>* B, int ldb, int64_t sB, int b) {
  return rocsolver_cpotrs_strided_batched(h, uplo, n, nrhs, A, lda, sA, B, ldb, sB, b); }
template <> int vega67_potrs<c10::complex<double>>(void* h, int uplo, int n, int nrhs, c10::complex<double>* A, int lda, int64_t sA, c10::complex<double>* B, int ldb, int64_t sB, int b) {
  return rocsolver_zpotrs_strided_batched(h, uplo, n, nrhs, A, lda, sA, B, ldb, sB, b); }

template <typename T> int vega67_gels(void* h, int m, int n, int nrhs, T* A, int lda, int64_t sA, T* B, int ldb, int64_t sB, int* info, int b);
template <> int vega67_gels<float>(void* h, int m, int n, int nrhs, float* A, int lda, int64_t sA, float* B, int ldb, int64_t sB, int* info, int b) {
  return rocsolver_sgels_strided_batched(h, kVegaOpNone, m, n, nrhs, A, lda, sA, B, ldb, sB, info, b); }
template <> int vega67_gels<double>(void* h, int m, int n, int nrhs, double* A, int lda, int64_t sA, double* B, int ldb, int64_t sB, int* info, int b) {
  return rocsolver_dgels_strided_batched(h, kVegaOpNone, m, n, nrhs, A, lda, sA, B, ldb, sB, info, b); }
template <> int vega67_gels<c10::complex<float>>(void* h, int m, int n, int nrhs, c10::complex<float>* A, int lda, int64_t sA, c10::complex<float>* B, int ldb, int64_t sB, int* info, int b) {
  return rocsolver_cgels_strided_batched(h, kVegaOpNone, m, n, nrhs, A, lda, sA, B, ldb, sB, info, b); }
template <> int vega67_gels<c10::complex<double>>(void* h, int m, int n, int nrhs, c10::complex<double>* A, int lda, int64_t sA, c10::complex<double>* B, int ldb, int64_t sB, int* info, int b) {
  return rocsolver_zgels_strided_batched(h, kVegaOpNone, m, n, nrhs, A, lda, sA, B, ldb, sB, info, b); }

// una copia a colonne e a lotti contigui, se la matrice non lo e' gia'
inline Tensor vega67_colonne(const Tensor& t) {
  return t.mT().is_contiguous() ? t : cloneBatchedColumnMajor(t);
}

// fattorizzazione di Cholesky sul posto; info (int, sulla GPU) per ogni matrice
void cholesky_helper_rocsolver(const Tensor& input, bool upper, const Tensor& info) {
  if (input.numel() == 0) {
    info.zero_();
    return;
  }
  Tensor work = vega67_colonne(input);
  const int n = vega67_int(input.size(-1), "cholesky: n");
  const int batch = vega67_int(batchCount(input), "cholesky: lotto");
  Tensor info_dev = (info.is_cuda() && info.is_contiguous() && info.scalar_type() == at::kInt)
      ? info : at::empty({batch}, input.options().dtype(at::kInt));
  AT_DISPATCH_FLOATING_AND_COMPLEX_TYPES(input.scalar_type(), "cholesky_rocsolver", [&] {
    VEGA67_CHECK(vega67_potrf<scalar_t>(vega67_handle(), upper ? kVegaFillUpper : kVegaFillLower,
                                        n, work.data_ptr<scalar_t>(), std::max(1, n),
                                        matrixStride(work), info_dev.data_ptr<int>(), batch),
                 "cholesky");
  });
  if (!work.is_same(input)) {
    input.copy_(work);
  }
  if (!info_dev.is_same(info)) {
    info.copy_(info_dev.view(info.sizes()));
  }
}

// risolve A X = B con A gia' fattorizzata (fattore in A); restituisce X
Tensor cholesky_solve_rocsolver(const Tensor& self, const Tensor& A, bool upper) {
  Tensor b = cloneBatchedColumnMajor(self);
  if (b.numel() == 0 || A.numel() == 0) {
    return b;
  }
  Tensor a = vega67_colonne(A);
  TORCH_CHECK(batchCount(a) == batchCount(b),
              "cholesky_solve: lotti diversi fra A e B [VEGA-PATCH 67]");
  const int n = vega67_int(a.size(-1), "cholesky_solve: n");
  const int nrhs = vega67_int(b.size(-1), "cholesky_solve: nrhs");
  const int batch = vega67_int(batchCount(b), "cholesky_solve: lotto");
  AT_DISPATCH_FLOATING_AND_COMPLEX_TYPES(self.scalar_type(), "cholesky_solve_rocsolver", [&] {
    VEGA67_CHECK(vega67_potrs<scalar_t>(vega67_handle(), upper ? kVegaFillUpper : kVegaFillLower,
                                        n, nrhs, a.data_ptr<scalar_t>(), std::max(1, n), matrixStride(a),
                                        b.data_ptr<scalar_t>(), std::max(1, n), matrixStride(b), batch),
                 "cholesky_solve");
  });
  return b;
}

// inversa da fattore di Cholesky: potrs contro l'identita', come il ramo MAGMA
Tensor& cholesky_inverse_rocsolver(Tensor& result, Tensor& infos, bool upper) {
  infos.zero_();
  if (result.numel() == 0) {
    return result;
  }
  Tensor fattore = cloneBatchedColumnMajor(result);
  Tensor identita = at::zeros(fattore.sizes(), fattore.options());
  identita.diagonal(/*offset=*/0, /*dim1=*/-2, /*dim2=*/-1).fill_(1);
  result.copy_(cholesky_solve_rocsolver(identita, fattore, upper));
  return result;
}

// minimi quadrati con gels; la soluzione va nelle prime n righe di b
void lstsq_rocsolver(const Tensor& a, Tensor& b, Tensor& infos) {
  const int64_t m = a.size(-2), n = a.size(-1);
  if (a.numel() == 0 || b.numel() == 0) {
    return;
  }
  // il lotto di A si allarga a quello di B, come batch_iterator_with_broadcasting
  std::vector<int64_t> forma(b.sizes().begin(), b.sizes().end() - 2);
  forma.push_back(m);
  forma.push_back(n);
  Tensor a_work = cloneBatchedColumnMajor(a.expand(forma));
  Tensor b_work = vega67_colonne(b);
  TORCH_CHECK(b_work.size(-2) == std::max(m, n),
              "lstsq: B deve avere max(m, n) righe [VEGA-PATCH 67]");
  const int mi = vega67_int(m, "lstsq: m");
  const int ni = vega67_int(n, "lstsq: n");
  const int nrhs = vega67_int(b_work.size(-1), "lstsq: nrhs");
  const int ldb = vega67_int(b_work.size(-2), "lstsq: ldb");
  const int batch = vega67_int(batchCount(b_work), "lstsq: lotto");
  Tensor info_dev = at::zeros({std::max(batch, 1)}, b.options().dtype(at::kInt));
  AT_DISPATCH_FLOATING_AND_COMPLEX_TYPES(a.scalar_type(), "lstsq_rocsolver", [&] {
    VEGA67_CHECK(vega67_gels<scalar_t>(vega67_handle(), mi, ni, nrhs,
                                       a_work.data_ptr<scalar_t>(), std::max(1, mi), matrixStride(a_work),
                                       b_work.data_ptr<scalar_t>(), std::max(1, ldb), matrixStride(b_work),
                                       info_dev.data_ptr<int>(), batch),
                 "lstsq");
  });
  if (!b_work.is_same(b)) {
    b.copy_(b_work);
  }
  // info > 0: rango non pieno. Lo si riporta, cosi' PyTorch segnala l'errore invece di
  // restituire una soluzione senza senso
  if (infos.numel() == info_dev.numel()) {
    infos.copy_(info_dev.view(infos.sizes()));
  } else {
    // infos ha il lotto di A, piu' piccolo di quello di B se A e' stata allargata:
    // si riporta il caso peggiore, cosi' l'errore non si perde
    infos.copy_(info_dev.max().expand(infos.sizes()));
  }
}

}  // namespace (anonymous)
#endif  // !AT_MAGMA_ENABLED()
'''

sostituzioni = [
    ("\nnamespace at::native {\n", DICHIARAZIONI),
    ("namespace lazy_linalg {\n#endif\n", APPOGGIO),
    # cholesky_solve
    ("""#else
  return _cholesky_solve_helper_cuda_magma(self, A, upper);
#endif
}""",
     """#elif !AT_MAGMA_ENABLED()
  return cholesky_solve_rocsolver(self, A, upper);  // [VEGA-PATCH 67]
#else
  return _cholesky_solve_helper_cuda_magma(self, A, upper);
#endif
}"""),
    # cholesky
    ("""#else
  cholesky_helper_magma(input, upper, info);
#endif // USE_LINALG_SOLVER""",
     """#elif !AT_MAGMA_ENABLED()
  cholesky_helper_rocsolver(input, upper, info);  // [VEGA-PATCH 67]
#else
  cholesky_helper_magma(input, upper, info);
#endif // USE_LINALG_SOLVER"""),
    # cholesky_inverse
    ("""#else
  return cholesky_inverse_kernel_impl_magma(result, infos, upper);
#endif
""",
     """#elif !AT_MAGMA_ENABLED()
  return cholesky_inverse_rocsolver(result, infos, upper);  // [VEGA-PATCH 67]
#else
  return cholesky_inverse_kernel_impl_magma(result, infos, upper);
#endif
"""),
    # lstsq, caso sottodeterminato
    ("""#if defined(USE_LINALG_SOLVER) && !defined(USE_ROCM)
    linalg_lstsq_gels(a, b, infos);
#else
    TORCH_CHECK(""",
     """#if defined(USE_LINALG_SOLVER) && !defined(USE_ROCM)
    linalg_lstsq_gels(a, b, infos);
#elif !AT_MAGMA_ENABLED()
    lstsq_rocsolver(a, b, infos);  // [VEGA-PATCH 67] gels copre anche m < n
#else
    TORCH_CHECK("""),
    # lstsq, caso sovradeterminato su ROCm
    ("""    // On ROCm platform we can only use MAGMA here
    // If MAGMA is not available, an error will be thrown
    gels_magma(a, b, infos);""",
     """    // On ROCm platform we can only use MAGMA here
    // If MAGMA is not available, an error will be thrown
#if !AT_MAGMA_ENABLED()
    lstsq_rocsolver(a, b, infos);  // [VEGA-PATCH 67]
#else
    gels_magma(a, b, infos);
#endif"""),
]

testo = io.open(F, encoding="utf-8", newline="").read()
if MARCA in testo:
    print("gia' applicata")
    sys.exit(0)
crlf = "\r\n" in testo
errori = 0
for vecchio, nuovo in sostituzioni:
    if crlf:
        vecchio, nuovo = vecchio.replace("\n", "\r\n"), nuovo.replace("\n", "\r\n")
    n = testo.count(vecchio)
    if n != 1:
        print(f"  ERRORE: blocco trovato {n} volte, atteso 1: {vecchio.strip().splitlines()[0][:70]}")
        errori += 1
        continue
    testo = testo.replace(vecchio, nuovo)
    print(f"  ok: {vecchio.strip().splitlines()[0][:70]}")
if "#include <limits>" not in testo:
    testo = testo.replace("#include <utility>", "#include <utility>\n#include <limits>  // [VEGA-PATCH 67]", 1)
if errori:
    print(f"{errori} errori: nulla scritto")
    sys.exit(1)
if applica:
    if not os.path.exists(F + ".bak_pre_vega67"):
        shutil.copy2(F, F + ".bak_pre_vega67")
    io.open(F, "w", encoding="utf-8", newline="").write(testo)
    print("applicata")
else:
    print("prova a vuoto riuscita")

"""VEGA-PATCH 64 - le 16 routine *Batched di hipBLAS, reindirizzate su rocSOLVER.

Ad agosto (VEGA-PATCH 48) erano state sostituite da TORCH_CHECK(false): hipBLAS di
ROCm 5.7 non le espone. Costo misurato il 16 ott 2026: falliscono solve, inv, det,
slogdet, lu_factor e qr quando l'ingresso e' a LOTTI, mentre sulla matrice singola
funzionano (passano da hipSOLVER).

rocSOLVER - gia' in torch\\lib, ROCm 5.7 - ha le sue versioni a lotti di tutte e
quattro le famiglie, ed e' cio' che hipBLAS stesso chiama su AMD dalle versioni
successive: questo e' il rimedio fedele, non un ripiego.

Differenze di semantica gestite (cuBLAS/hipBLAS -> rocSOLVER):
  getrf  pivot contigui (passo n); se il puntatore ai pivot e' nullo -> variante npvt
  getrs  'info' e' un intero LATO HOST che segnala solo errori di argomento; rocSOLVER
         non lo ha -> si mette a 0 dopo una chiamata riuscita
  geqrf  tau come ARRAY DI PUNTATORI in hipBLAS, CONTIGUO con passo in rocSOLVER ->
         si legge l'array di puntatori, si verifica che il passo sia costante (PyTorch
         lo costruisce sempre cosi', da tau.unsqueeze(-1)) e si passa base + passo
  gels   'info' host + 'devInfoArray' device: il secondo va a rocSOLVER

Le funzioni rocSOLVER si DICHIARANO qui con le firme di rocsolver-functions.h 5.7,
invece di includere l'header: nel percorso di inclusione TheRock 7.x precede ROCm 5.7
(VEGA-PATCH 46d), e mescolare header e DLL di versioni diverse e' cio' che questo
progetto ha imparato a evitare. Handle e dati complessi passano come void*: stesso ABI.

Collegamento: rocsolver.lib di ROCm 5.7 - la stessa versione della rocsolver.dll che
sta in torch\\lib - aggiunta in cmake/Dependencies.cmake accanto alla VEGA-PATCH 48.

    python patch_batched_rocsolver.py --prova
    python patch_batched_rocsolver.py --applica
"""
import io
import os
import shutil
import sys

RADICE = r"C:\LaRuota_workspace\pytorch_src"
BLAS = os.path.join(RADICE, r"aten\src\ATen\hip\HIPBlas.cpp")
DEPS = os.path.join(RADICE, r"cmake\Dependencies.cmake")

INIZIO = "template <>\nvoid getrsBatched<float>(HIPBLAS_GETRS_ARGTYPES(float)) {"
FINE = "} // namespace at::hip::blas"

NUOVO = r'''// =====================================================================================
// [VEGA-PATCH 64 - 16 ott 2026] Le 16 routine *Batched, reindirizzate su rocSOLVER.
// Ad agosto (VEGA-PATCH 48) erano TORCH_CHECK(false) perche' hipBLAS 5.7 non le espone.
// Spiegazione completa in C:\LaRuota_workspace\patch_batched_rocsolver.py
// =====================================================================================
} // namespace at::hip::blas

extern "C" {
// Firme di rocsolver-functions.h (ROCm 5.7). rocblas_int = int32, rocblas_stride = int64,
// rocblas_status e rocblas_operation sono enum (int). Handle e dati complessi come void*.
int rocsolver_sgetrf_batched(void*, int, int, float* const[], int, int*, int64_t, int*, int);
int rocsolver_dgetrf_batched(void*, int, int, double* const[], int, int*, int64_t, int*, int);
int rocsolver_cgetrf_batched(void*, int, int, void* const[], int, int*, int64_t, int*, int);
int rocsolver_zgetrf_batched(void*, int, int, void* const[], int, int*, int64_t, int*, int);
int rocsolver_sgetrf_npvt_batched(void*, int, int, float* const[], int, int*, int);
int rocsolver_dgetrf_npvt_batched(void*, int, int, double* const[], int, int*, int);
int rocsolver_cgetrf_npvt_batched(void*, int, int, void* const[], int, int*, int);
int rocsolver_zgetrf_npvt_batched(void*, int, int, void* const[], int, int*, int);
int rocsolver_sgetrs_batched(void*, int, int, int, float* const[], int, const int*, int64_t, float* const[], int, int);
int rocsolver_dgetrs_batched(void*, int, int, int, double* const[], int, const int*, int64_t, double* const[], int, int);
int rocsolver_cgetrs_batched(void*, int, int, int, void* const[], int, const int*, int64_t, void* const[], int, int);
int rocsolver_zgetrs_batched(void*, int, int, int, void* const[], int, const int*, int64_t, void* const[], int, int);
int rocsolver_sgeqrf_batched(void*, int, int, float* const[], int, float*, int64_t, int);
int rocsolver_dgeqrf_batched(void*, int, int, double* const[], int, double*, int64_t, int);
int rocsolver_cgeqrf_batched(void*, int, int, void* const[], int, void*, int64_t, int);
int rocsolver_zgeqrf_batched(void*, int, int, void* const[], int, void*, int64_t, int);
int rocsolver_sgels_batched(void*, int, int, int, int, float* const[], int, float* const[], int, int*, int);
int rocsolver_dgels_batched(void*, int, int, int, int, double* const[], int, double* const[], int, int*, int);
int rocsolver_cgels_batched(void*, int, int, int, int, void* const[], int, void* const[], int, int*, int);
int rocsolver_zgels_batched(void*, int, int, int, int, void* const[], int, void* const[], int, int*, int);
} // extern "C"

namespace at::hip::blas {

namespace {

#define VEGA_ROCSOLVER_CHECK(EXPR, NOME)                                              \
  do {                                                                                \
    const int vega_stato_ = (EXPR);                                                   \
    TORCH_CHECK(vega_stato_ == 0, NOME, ": rocSOLVER ha restituito lo stato ",        \
                vega_stato_, " [VEGA-PATCH 64]");                                     \
  } while (0)

// Su AMD l'handle hipBLAS E' un rocblas_handle (hipblasCreate chiama rocblas_create_handle),
// e porta gia' lo stream corrente: rocSOLVER lavora sullo stesso stream.
inline void* vega_handle(hipblasHandle_t h) { return reinterpret_cast<void*>(h); }

// hipBLAS vuole tau come array di puntatori, rocSOLVER come blocco contiguo con passo.
// Si legge l'array (sono 'batch' puntatori, pochi byte) e si verifica che il passo sia
// costante: PyTorch lo costruisce sempre da un tensore contiguo, ma se un giorno non lo
// fosse si deve fallire in modo esplicito, non scrivere in memoria altrui.
template <typename T>
std::pair<T*, int64_t> vega_tau_contiguo(T** tau_array, int m, int n, int batch) {
  std::vector<T*> h(batch);
  // stessa forma delle altre chiamate di questo file: stream "travestito" da CUDA
  hipStream_t stream = c10::hip::getCurrentHIPStreamMasqueradingAsCUDA().stream();
  TORCH_CHECK(hipMemcpyAsync(h.data(), tau_array, sizeof(T*) * batch,
                             hipMemcpyDeviceToHost, stream) == hipSuccess,
              "geqrfBatched: copia dei puntatori tau fallita [VEGA-PATCH 64]");
  TORCH_CHECK(hipStreamSynchronize(stream) == hipSuccess,
              "geqrfBatched: sincronizzazione fallita [VEGA-PATCH 64]");
  int64_t passo = std::max<int64_t>(1, std::min(m, n));
  if (batch > 1) {
    passo = h[1] - h[0];
  }
  for (int i = 1; i < batch; ++i) {
    TORCH_CHECK(h[i] - h[i - 1] == passo,
                "geqrfBatched: i tau non hanno passo costante [VEGA-PATCH 64]");
  }
  return {h[0], passo};
}

} // anonymous namespace

// ---- getrsBatched: risolve A X = B con la fattorizzazione LU gia' calcolata
#define VEGA_GETRS(T, FN, CAST)                                                       \
  template <>                                                                         \
  void getrsBatched<T>(HIPBLAS_GETRS_ARGTYPES(T)) {                                   \
    VEGA_ROCSOLVER_CHECK(FN(vega_handle(handle), static_cast<int>(trans), n, nrhs,    \
                            CAST(dA_array), lda, ipiv_array, static_cast<int64_t>(n), \
                            CAST(dB_array), ldb, batchsize), #FN);                    \
    *info_array = 0; /* in cuBLAS e' un intero host che segnala errori di argomento */ \
  }
#define VEGA_REALE(p) (p)
#define VEGA_COMPLESSO(p) reinterpret_cast<void* const*>(p)
VEGA_GETRS(float, rocsolver_sgetrs_batched, VEGA_REALE)
VEGA_GETRS(double, rocsolver_dgetrs_batched, VEGA_REALE)
VEGA_GETRS(c10::complex<float>, rocsolver_cgetrs_batched, VEGA_COMPLESSO)
VEGA_GETRS(c10::complex<double>, rocsolver_zgetrs_batched, VEGA_COMPLESSO)

// ---- geqrfBatched: fattorizzazione QR
#define VEGA_GEQRF(T, FN, CAST, TAU)                                                  \
  template <>                                                                         \
  void geqrfBatched<T>(HIPBLAS_GEQRF_BATCHED_ARGTYPES(T)) {                           \
    auto tau = vega_tau_contiguo<T>(tau_array, m, n, batchsize);                      \
    VEGA_ROCSOLVER_CHECK(FN(vega_handle(handle), m, n, CAST(A_array), lda,            \
                            TAU(tau.first), tau.second, batchsize), #FN);             \
    *info = 0;                                                                        \
  }
#define VEGA_TAU_REALE(p) (p)
#define VEGA_TAU_COMPLESSO(p) reinterpret_cast<void*>(p)
VEGA_GEQRF(float, rocsolver_sgeqrf_batched, VEGA_REALE, VEGA_TAU_REALE)
VEGA_GEQRF(double, rocsolver_dgeqrf_batched, VEGA_REALE, VEGA_TAU_REALE)
VEGA_GEQRF(c10::complex<float>, rocsolver_cgeqrf_batched, VEGA_COMPLESSO, VEGA_TAU_COMPLESSO)
VEGA_GEQRF(c10::complex<double>, rocsolver_zgeqrf_batched, VEGA_COMPLESSO, VEGA_TAU_COMPLESSO)

// ---- getrfBatched: fattorizzazione LU. Pivot nulli = senza pivoting -> variante npvt
#define VEGA_GETRF(T, FN, FN_NPVT, CAST)                                              \
  template <>                                                                         \
  void getrfBatched<T>(HIPBLAS_GETRF_ARGTYPES(T)) {                                   \
    auto handle = at::hip::getCurrentHIPBlasHandle();                                 \
    if (ipiv_array != nullptr) {                                                      \
      VEGA_ROCSOLVER_CHECK(FN(vega_handle(handle), n, n, CAST(dA_array), ldda,        \
                              ipiv_array, static_cast<int64_t>(n), info_array,        \
                              batchsize), #FN);                                       \
    } else {                                                                          \
      VEGA_ROCSOLVER_CHECK(FN_NPVT(vega_handle(handle), n, n, CAST(dA_array), ldda,   \
                                   info_array, batchsize), #FN_NPVT);                 \
    }                                                                                 \
  }
VEGA_GETRF(double, rocsolver_dgetrf_batched, rocsolver_dgetrf_npvt_batched, VEGA_REALE)
VEGA_GETRF(float, rocsolver_sgetrf_batched, rocsolver_sgetrf_npvt_batched, VEGA_REALE)
VEGA_GETRF(c10::complex<double>, rocsolver_zgetrf_batched, rocsolver_zgetrf_npvt_batched, VEGA_COMPLESSO)
VEGA_GETRF(c10::complex<float>, rocsolver_cgetrf_batched, rocsolver_cgetrf_npvt_batched, VEGA_COMPLESSO)

// ---- gelsBatched: minimi quadrati. 'info' host, 'devInfoArray' device -> a rocSOLVER
#define VEGA_GELS(T, FN, CAST)                                                        \
  template <>                                                                         \
  void gelsBatched<T>(HIPBLAS_GELS_BATCHED_ARGTYPES(T)) {                             \
    VEGA_ROCSOLVER_CHECK(FN(vega_handle(handle), static_cast<int>(trans), m, n, nrhs, \
                            CAST(dA_array), ldda, CAST(dC_array), lddc, devInfoArray, \
                            batchSize), #FN);                                         \
    *info = 0;                                                                        \
  }
VEGA_GELS(double, rocsolver_dgels_batched, VEGA_REALE)
VEGA_GELS(float, rocsolver_sgels_batched, VEGA_REALE)
VEGA_GELS(c10::complex<double>, rocsolver_zgels_batched, VEGA_COMPLESSO)
VEGA_GELS(c10::complex<float>, rocsolver_cgels_batched, VEGA_COMPLESSO)

#undef VEGA_GETRS
#undef VEGA_GEQRF
#undef VEGA_GETRF
#undef VEGA_GELS
#undef VEGA_REALE
#undef VEGA_COMPLESSO
#undef VEGA_TAU_REALE
#undef VEGA_TAU_COMPLESSO
#undef VEGA_ROCSOLVER_CHECK

'''

DEPS_ANCORA = "foreach(_vega_lib rocblas hipsparse MIOpen)"
DEPS_NUOVO = '''    # [VEGA-PATCH 64 - 16 ott 2026] rocsolver.lib di ROCm 5.7: la stessa versione della
    # rocsolver.dll in torch\\lib. Serve alle 16 routine *Batched reindirizzate su rocSOLVER
    # in ATen/hip/HIPBlas.cpp (prima erano TORCH_CHECK(false), VEGA-PATCH 48).
    set(_vega_rocsolver "C:/Program Files/AMD/ROCm/5.7/lib/rocsolver.lib")
    if(EXISTS "${_vega_rocsolver}")
      list(APPEND Caffe2_PUBLIC_HIP_DEPENDENCY_LIBS "${_vega_rocsolver}")
      message(STATUS "[VEGA-PATCH 64] rocsolver collegata: ${_vega_rocsolver}")
    else()
      message(FATAL_ERROR "[VEGA-PATCH 64] rocsolver.lib non trovata: ${_vega_rocsolver}")
    endif()
'''

applica = "--applica" in sys.argv
errori = 0

# ---- HIPBlas.cpp
testo = io.open(BLAS, encoding="utf-8").read().replace("\r\n", "\n")
if "VEGA-PATCH 64" in testo:
    print("  HIPBlas.cpp: gia' applicata")
else:
    a = testo.find(INIZIO)
    b = testo.find(FINE, a)
    if a < 0 or b < 0:
        print("  ERRORE HIPBlas.cpp: marcatori non trovati")
        errori += 1
    else:
        blocco = testo[a:b]
        stub = blocco.count("[VEGA-PATCH 48]")
        print(f"  HIPBlas.cpp: blocco di {blocco.count(chr(10))} righe, stub VEGA-PATCH 48 trovati: {stub}")
        if stub != 16:
            print("  ERRORE: attesi 16 stub, non tocco nulla")
            errori += 1
        else:
            # il blocco nuovo chiude e riapre il namespace: la FINE originale resta
            nuovo_testo = testo[:a] + NUOVO + testo[b:]
            print(f"  HIPBlas.cpp: {'sostituito' if applica else 'da sostituire'} con le 16 routine rocSOLVER")
            if applica:
                shutil.copy2(BLAS, BLAS + ".bak_pre_vega64")
                io.open(BLAS, "w", encoding="utf-8", newline="\n").write(nuovo_testo)

# ---- Dependencies.cmake
dep = io.open(DEPS, encoding="utf-8").read()
if "VEGA-PATCH 64" in dep:
    print("  Dependencies.cmake: gia' applicata")
elif DEPS_ANCORA not in dep:
    print("  ERRORE Dependencies.cmake: ancora della VEGA-PATCH 48 non trovata")
    errori += 1
else:
    i = dep.find(DEPS_ANCORA)
    riga_inizio = dep.rfind("\n", 0, i) + 1
    nuovo_dep = dep[:riga_inizio] + DEPS_NUOVO + dep[riga_inizio:]
    print(f"  Dependencies.cmake: rocsolver.lib {'aggiunta' if applica else 'da aggiungere'}")
    if applica and errori == 0:
        shutil.copy2(DEPS, DEPS + ".bak_pre_vega64")
        io.open(DEPS, "w", encoding="utf-8", newline="").write(nuovo_dep)

if errori:
    print(f"\n{errori} errori: niente scritto dove c'erano errori")
    sys.exit(1)
print("\nprova a vuoto riuscita" if not applica else "\napplicata")

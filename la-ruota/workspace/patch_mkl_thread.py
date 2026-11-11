"""VEGA-PATCH 66 - MKL usa tutti i core anche col pool di thread nativo.

La ruota e' compilata con USE_OPENMP=OFF, quindi ATen usa il pool nativo
(ParallelNative.cpp). Li' init_num_threads() fa mkl_set_num_threads(1): globale, per
tutto il processo. Serve a evitare che MKL apra 16 thread dentro ciascuno dei 32
thread del pool, ma in pratica blocca OGNI chiamata MKL a un solo core: la matmul su
CPU fa ~45 GFLOPS invece di oltre 150 (MKL_VERBOSE mostra NThr:1). Le build ufficiali
non hanno il problema perche' usano OpenMP, dove torch e MKL condividono i thread.

Rimedio, solo in ParallelNative.cpp:
  - init_num_threads() non tocca piu' MKL: resta il suo valore (core fisici, o
    MKL_NUM_THREADS);
  - ParallelRegionGuard, che avvolge ogni compito eseguito dentro parallel_for, mette
    MKL a 1 thread SOLO per il thread corrente (mkl_set_num_threads_local) e ripristina
    all'uscita: niente sovraffollamento dentro le regioni parallele;
  - set_num_threads(n) imposta anche MKL a n, come fa il ramo OpenMP.

    python patch_mkl_thread.py --prova
    python patch_mkl_thread.py --applica
"""
import io
import os
import shutil
import sys

F = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\ParallelNative.cpp"
applica = "--applica" in sys.argv
MARCA = "[VEGA-PATCH 66]"

sostituzioni = [
    (
        """struct ParallelRegionGuard {
  ParallelRegionGuard(int task_id) {
    internal::set_thread_num(task_id);
    _set_in_parallel_region(true);
  }

  ~ParallelRegionGuard() {
    _set_in_parallel_region(false);
    _unset_thread_num();
  }
};""",
        """struct ParallelRegionGuard {
  ParallelRegionGuard(int task_id) {
    internal::set_thread_num(task_id);
    _set_in_parallel_region(true);
#if AT_MKL_ENABLED()
    // [VEGA-PATCH 66] dentro una regione parallela MKL usa un solo thread, ma solo
    // per questo thread: fuori dalle regioni MKL tiene tutti i core
    mkl_prev_threads_ = mkl_set_num_threads_local(1);
#endif
  }

  ~ParallelRegionGuard() {
#if AT_MKL_ENABLED()
    mkl_set_num_threads_local(mkl_prev_threads_);
#endif
    _set_in_parallel_region(false);
    _unset_thread_num();
  }

#if AT_MKL_ENABLED()
  int mkl_prev_threads_ = 0;
#endif
};""",
    ),
    (
        """#if AT_MKL_ENABLED()
  mkl_set_num_threads(1);
#endif

#ifdef C10_MOBILE
  caffe2::pthreadpool();
#endif
}""",
        """  // [VEGA-PATCH 66] qui c'era mkl_set_num_threads(1): globale, bloccava ogni
  // chiamata MKL a un core. Il limite a 1 ora vale solo dentro ParallelRegionGuard.

#ifdef C10_MOBILE
  caffe2::pthreadpool();
#endif
}""",
    ),
    (
        """void set_num_threads(int nthreads) {
#ifndef C10_MOBILE
  TORCH_CHECK(nthreads > 0, "Expected positive number of threads");
""",
        """void set_num_threads(int nthreads) {
#ifndef C10_MOBILE
  TORCH_CHECK(nthreads > 0, "Expected positive number of threads");
#if AT_MKL_ENABLED()
  mkl_set_num_threads(nthreads);  // [VEGA-PATCH 66] come nel ramo OpenMP
#endif
""",
    ),
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
        print(f"  ERRORE: blocco trovato {n} volte, atteso 1:\n{vecchio[:80]}")
        errori += 1
        continue
    testo = testo.replace(vecchio, nuovo)
    print(f"  ok: {vecchio.splitlines()[0][:70]}")
if errori:
    print(f"{errori} errori: nulla scritto")
    sys.exit(1)
if applica:
    if not os.path.exists(F + ".bak_pre_vega66"):
        shutil.copy2(F, F + ".bak_pre_vega66")
    io.open(F, "w", encoding="utf-8", newline="").write(testo)
    print("applicata")
else:
    print("prova a vuoto riuscita")

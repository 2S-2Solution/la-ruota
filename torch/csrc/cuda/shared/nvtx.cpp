#ifdef _WIN32
#include <wchar.h> // _wgetenv for nvtx
#endif

// [VEGA-PATCH 48 1 ago] roctracer/roctx.h non e' presente in ROCm 5.7 + Marconi su
// Windows: NVTX/ROCTX sono solo marker di profiling. Quando l'header manca esponiamo
// lo stesso sottomodulo Python con funzioni no-op: l'API resta identica, semplicemente
// i marker non vengono emessi.
#if defined(__has_include)
#if __has_include(<roctracer/roctx.h>)
#define VEGA_HAS_ROCTX 1
#include <roctracer/roctx.h>
#endif
#endif

#include <torch/csrc/utils/pybind.h>

namespace torch::cuda::shared {

#ifndef VEGA_HAS_ROCTX
namespace {
int roctxRangePushA(const char* /*message*/) {
  return -1;
}
int roctxRangePop() {
  return -1;
}
int roctxRangeStartA(const char* /*message*/) {
  return -1;
}
void roctxRangeStop(int /*id*/) {}
void roctxMarkA(const char* /*message*/) {}
} // namespace
#endif

void initNvtxBindings(PyObject* module) {
  auto m = py::handle(module).cast<py::module>();

#ifdef VEGA_HAS_ROCTX
  auto nvtx = m.def_submodule("_nvtx", "roctx bindings");
#else
  auto nvtx = m.def_submodule("_nvtx", "roctx bindings (no-op: roctracer assente)");
#endif
  nvtx.def("rangePushA", roctxRangePushA);
  nvtx.def("rangePop", roctxRangePop);
  nvtx.def("rangeStartA", roctxRangeStartA);
  nvtx.def("rangeEnd", roctxRangeStop);
  nvtx.def("markA", roctxMarkA);
}

} // namespace torch::cuda::shared

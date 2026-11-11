#include <ATen/hip\HIPEvent.h>
#include <c10/core/Device.h>
#include <ATen/hip/impl/HIPStreamMasqueradingAsCUDA.h>
#include <torch/custom_class.h>

// VEGA-PATCH 47 T (LA RUOTA #62 cleanup post-#63): hipify enum/typedef CUDA â†’ HIP
// cuda.h JIT eredita ATen/cuda/CUDAEvent.h che porta hip/hip_runtime_api.h via guard ROCm,
// ma gli identificatori semantici (cudaEvent*, hipIpcEventHandle_t) non sono mappati.
// Aliasing tassativo per gfx906 Vega 20 nativo.
// [VEGA-PATCH 68] le #define della 47 (ogni nome definito come se stesso) non
// dichiaravano nulla: serve l'header HIP che porta le costanti degli eventi.
#include <hip/hip_runtime_api.h>

namespace torch::jit {

class CUDAEvent;
// This class is a wrapper around c10::hip::HIPStreamMasqueradingAsCUDA.
// It is needed because TorchBind does not support all of the argument types
// for c10::hip::HIPStreamMasqueradingAsCUDA. For more details, please refer to
// ATen/hip/impl/HIPStreamMasqueradingAsCUDA.h.
class HIPStreamMasqueradingAsCUDA final : public CustomClassHolder {
 public:
  HIPStreamMasqueradingAsCUDA(
      std::optional<c10::Device> device = std::nullopt,
      int64_t priority = 0) {
    c10::DeviceIndex device_index =
        device.has_value() ? device->index() : c10::hip::current_device();
    stream_ = std::make_unique<c10::hip::HIPStreamMasqueradingAsCUDA>(
        c10::hip::getStreamFromPoolMasqueradingAsCUDA(static_cast<int>(priority), device_index));
  }

  HIPStreamMasqueradingAsCUDA(c10::hip::HIPStreamMasqueradingAsCUDA s) {
    stream_ = std::make_unique<c10::hip::HIPStreamMasqueradingAsCUDA>(s);
  }

  bool query() {
    return stream_->query();
  }

  c10::intrusive_ptr<CUDAEvent> recordEvent(
      c10::intrusive_ptr<CUDAEvent> event);

  void synchronize() {
    stream_->synchronize();
  }

  void waitEvent(const c10::intrusive_ptr<CUDAEvent>& event);

  void waitStream(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream);

  /// Get the CUDA device index that this stream is associated with.
  int64_t device_index() const {
    return stream_->device_index();
  }

  /// Get the full Device that this stream is associated with.  The Device
  /// is guaranteed to be a CUDA device.
  c10::Device device() const {
    return stream_->device();
  }

  /// Return the stream ID corresponding to this particular stream.
  int64_t id() const {
    return stream_->id();
  }

 private:
  std::unique_ptr<c10::hip::HIPStreamMasqueradingAsCUDA> stream_;
  friend class CUDAEvent;
};

// This class is a wrapper around c10::hip::HIPStreamMasqueradingAsCUDA.
// It is needed because TorchBind does not support all of the argument types
// for at::hip::HIPEvent. For more details, please refer to
// aten/src/ATen/cuda/CUDAEvent.h.
class CUDAEvent final : public CustomClassHolder {
 public:
  CUDAEvent(
      bool enable_timing = false,
      bool blocking = false,
      bool interprocess = false) {
    int flags = hipEventDisableTiming;
    if (enable_timing) {
      flags = hipEventDefault;
    }
    if (blocking) {
      flags |= hipEventBlockingSync;
    }
    if (interprocess) {
      TORCH_CHECK(!enable_timing);
      flags |= hipEventInterprocess;
    }

    event_ = std::make_unique<at::hip::HIPEvent>(flags);
  }

  double elapsedTime(const c10::intrusive_ptr<CUDAEvent>& end) {
    return event_->elapsed_time(*end->event_);
  }

  std::string ipcHandle() {
    hipIpcEventHandle_t handle{};
    event_->ipc_handle(&handle);
    std::string str_handle((const char*)&handle, sizeof(handle));
    return str_handle;
  }

  bool query() {
    return event_->query();
  }

  void record(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream);

  void synchronize() {
    event_->synchronize();
  }
  void wait(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream);

 private:
  void recordInternal(HIPStreamMasqueradingAsCUDA* stream);
  std::unique_ptr<at::hip::HIPEvent> event_;

  friend class HIPStreamMasqueradingAsCUDA;
};

inline c10::intrusive_ptr<CUDAEvent> HIPStreamMasqueradingAsCUDA::recordEvent(
    c10::intrusive_ptr<CUDAEvent> event) {
  if (!event) {
    event = c10::make_intrusive<CUDAEvent>();
  }

  event->recordInternal(this);
  return event;
}

inline void HIPStreamMasqueradingAsCUDA::waitEvent(const c10::intrusive_ptr<CUDAEvent>& event) {
  event->event_->block(stream_->hip_stream());  // [VEGA-PATCH 68]
}

inline void HIPStreamMasqueradingAsCUDA::waitStream(
    const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream) {
  auto ev = c10::make_intrusive<CUDAEvent>();
  stream->recordEvent(ev);
  waitEvent(ev);
}

inline void CUDAEvent::record(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream) {
  event_->record(stream->stream_->hip_stream());  // [VEGA-PATCH 68]
}

inline void CUDAEvent::recordInternal(HIPStreamMasqueradingAsCUDA* stream) {
  event_->record(stream->stream_->hip_stream());  // [VEGA-PATCH 68]
}

inline void CUDAEvent::wait(const c10::intrusive_ptr<HIPStreamMasqueradingAsCUDA>& stream) {
  event_->block(stream->stream_->hip_stream());  // [VEGA-PATCH 68]
}

TORCH_LIBRARY(cuda, m) {
  auto stream_class = m.class_<torch::jit::HIPStreamMasqueradingAsCUDA>("Stream").def(
      torch::init<std::optional<c10::Device>, int64_t>(),
      "",
      {torch::arg("device") = std::nullopt, torch::arg("priority") = 0});
  auto event_class = m.class_<torch::jit::CUDAEvent>("Event").def(
      torch::init<bool, bool, bool>(),
      "",
      {torch::arg("enable_timing") = false,
       torch::arg("blocking") = false,
       torch::arg("interprocess") = false});

  stream_class.def("query", &HIPStreamMasqueradingAsCUDA::query)
      .def("record_event", &HIPStreamMasqueradingAsCUDA::recordEvent)
      .def("synchronize", &HIPStreamMasqueradingAsCUDA::synchronize)
      .def("wait_event", &HIPStreamMasqueradingAsCUDA::waitEvent)
      .def("wait_stream", &HIPStreamMasqueradingAsCUDA::waitStream)
      .def("device_index", &HIPStreamMasqueradingAsCUDA::device_index)
      .def_property("device", &HIPStreamMasqueradingAsCUDA::device)
      .def("id", &HIPStreamMasqueradingAsCUDA::id);

  event_class.def("elapsed_time", &CUDAEvent::elapsedTime)
      .def("query", &CUDAEvent::query)
      .def("record", &CUDAEvent::record)
      .def("synchronize", &CUDAEvent::synchronize)
      .def("wait", &CUDAEvent::wait);
};

} // namespace torch::jit

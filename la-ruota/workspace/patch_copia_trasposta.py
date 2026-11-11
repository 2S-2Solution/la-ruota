"""VEGA-PATCH 76 - copy_ da GPU a GPU su un tensore trasposto: kernel a tessere di rocm-marconi.

Il copy_ generico di PyTorch, quando una delle due parti e' la trasposta (ultime due
dimensioni scambiate) di un tensore contiguo, legge o scrive con passo: su gfx906 va a
3-70 GB/s (una matrice 4096x8192 fp16: 3 GB/s) contro ~820 di una copia contigua. Nel
passo LoRA di Qwen3.5 a 512 token le trasposizioni sono il ~7% del tempo GPU (misure
del 20 ott).

Il kernel di rocm-marconi (trasposta_gfx906\\trasposta_gfx906.py) carica una tessera
64x64 in LDS con letture contigue e la riscrive trasposta con scritture contigue (fp16 a
coppie da 32 bit, ordine diagonale dei blocchi contro il partition camping): 488-649 GB/s.
Qui e' portato in C++ dentro Copy.hip, e usato SOLO quando:
  - stesso tipo, nessun coniugato/negato, stessa scheda, elementi da 2 o 4 byte;
  - nessuna sovrapposizione fra sorgente e destinazione;
  - almeno 1 MB (sotto, rocm-marconi ha misurato torch preferibile);
  - (a) destinazione contigua e sorgente = trasposta delle ultime due dimensioni di un
    tensore contiguo, oppure (b) il contrario;
  - indirizzi allineati a 4 byte e griglia entro i limiti.
Altrimenti resta il percorso di sempre.

    python patch_copia_trasposta.py --prova
    python patch_copia_trasposta.py --applica
"""
import io
import os
import shutil
import sys

F = r"C:\LaRuota_workspace\pytorch_src\aten\src\ATen\native\hip\Copy.hip"
applica = "--applica" in sys.argv

ANCORA_FUNZ = "// device-to-device copy, does type conversion\nvoid copy_device_to_device(TensorIterator& iter,\n"
KERNEL = r'''// [VEGA-PATCH 76 - 20 ott 2026] copia veloce di un tensore TRASPOSTO (ultime due dimensioni
// scambiate) da GPU a GPU. Kernel a tessere 64x64 in LDS di rocm-marconi
// (trasposta_gfx906\trasposta_gfx906.py): 488-649 GB/s contro i 3-70 del copy_ generico.
// Spiegazione: C:\LaRuota_workspace\patch_copia_trasposta.py
namespace {

constexpr int kVegaTessera = 64;

// 2 byte: letture e scritture a 32 bit, cioe' coppie di elementi. y[..., c, r] = x[..., r, c]
__global__ __launch_bounds__(256) void vega_trasposta16(
    const uint16_t* __restrict__ x, uint16_t* __restrict__ y, int R, int C, int64_t passo_lotto) {
  __shared__ uint16_t tessera[kVegaTessera][kVegaTessera + 2];
  const int tx = threadIdx.x & 31, ty = threadIdx.x >> 5;
  const int by = (blockIdx.y + blockIdx.x) % gridDim.y;  // ordine diagonale dei blocchi
  const int c0 = blockIdx.x * kVegaTessera, r0 = by * kVegaTessera;
  const uint16_t* xb = x + (int64_t)blockIdx.z * passo_lotto;
  uint16_t* yb = y + (int64_t)blockIdx.z * passo_lotto;
  const bool pari_c = (C & 1) == 0, pari_r = (R & 1) == 0;
#pragma unroll
  for (int i = ty; i < kVegaTessera; i += 8) {
    const int r = r0 + i, c = c0 + 2 * tx;
    if (r < R) {
      if (pari_c && c + 1 < C) {
        const uint32_t v = *(const uint32_t*)(xb + (int64_t)r * C + c);
        tessera[i][2 * tx] = (uint16_t)(v & 0xFFFF);
        tessera[i][2 * tx + 1] = (uint16_t)(v >> 16);
      } else {
        if (c < C) tessera[i][2 * tx] = xb[(int64_t)r * C + c];
        if (c + 1 < C) tessera[i][2 * tx + 1] = xb[(int64_t)r * C + c + 1];
      }
    }
  }
  __syncthreads();
#pragma unroll
  for (int i = ty; i < kVegaTessera; i += 8) {
    const int c = c0 + i, r = r0 + 2 * tx;
    if (c < C) {
      if (pari_r && r + 1 < R) {
        const uint32_t v = (uint32_t)tessera[2 * tx][i] | ((uint32_t)tessera[2 * tx + 1][i] << 16);
        *(uint32_t*)(yb + (int64_t)c * R + r) = v;
      } else {
        if (r < R) yb[(int64_t)c * R + r] = tessera[2 * tx][i];
        if (r + 1 < R) yb[(int64_t)c * R + r + 1] = tessera[2 * tx + 1][i];
      }
    }
  }
}

// 4 byte: un elemento per thread e passata
__global__ __launch_bounds__(256) void vega_trasposta32(
    const uint32_t* __restrict__ x, uint32_t* __restrict__ y, int R, int C, int64_t passo_lotto) {
  __shared__ uint32_t tessera[kVegaTessera][kVegaTessera + 1];
  const int tx = threadIdx.x & (kVegaTessera - 1), ty = threadIdx.x >> 6;
  const int by = (blockIdx.y + blockIdx.x) % gridDim.y;
  const int c0 = blockIdx.x * kVegaTessera, r0 = by * kVegaTessera;
  const uint32_t* xb = x + (int64_t)blockIdx.z * passo_lotto;
  uint32_t* yb = y + (int64_t)blockIdx.z * passo_lotto;
#pragma unroll
  for (int i = ty; i < kVegaTessera; i += 4) {
    const int r = r0 + i, c = c0 + tx;
    if (r < R && c < C) tessera[i][tx] = xb[(int64_t)r * C + c];
  }
  __syncthreads();
#pragma unroll
  for (int i = ty; i < kVegaTessera; i += 4) {
    const int c = c0 + i, r = r0 + tx;
    if (r < R && c < C) yb[(int64_t)c * R + r] = tessera[tx][i];
  }
}

// x [..., R, C] contiguo -> y [..., C, R] contiguo. false = caso non coperto: ci pensa il chiamante
bool vega_lancia_trasposta(const void* x, void* y, int64_t R, int64_t C, int64_t lotti,
                           int64_t dim_elem, hipStream_t stream) {
  const int64_t bx = (C + kVegaTessera - 1) / kVegaTessera;
  const int64_t byy = (R + kVegaTessera - 1) / kVegaTessera;
  if (R > INT32_MAX || C > INT32_MAX || bx > INT32_MAX || byy > 65535 || lotti > 65535) {
    return false;
  }
  if (reinterpret_cast<uintptr_t>(x) % 4 || reinterpret_cast<uintptr_t>(y) % 4) {
    return false;
  }
  const dim3 griglia((unsigned)bx, (unsigned)byy, (unsigned)lotti);
  if (dim_elem == 2) {
    vega_trasposta16<<<griglia, 256, 0, stream>>>(
        static_cast<const uint16_t*>(x), static_cast<uint16_t*>(y), (int)R, (int)C, R * C);
  } else {
    vega_trasposta32<<<griglia, 256, 0, stream>>>(
        static_cast<const uint32_t*>(x), static_cast<uint32_t*>(y), (int)R, (int)C, R * C);
  }
  C10_HIP_KERNEL_LAUNCH_CHECK();
  return true;
}

// Prova la via veloce. true = copia fatta.
bool vega_copia_trasposta(const Tensor& dst, const Tensor& src, hipStream_t stream) {
  const int64_t dim_elem = dst.element_size();
  if (dst.scalar_type() != src.scalar_type() || (dim_elem != 2 && dim_elem != 4)) return false;
  if (dst.dim() < 2 || !dst.sizes().equals(src.sizes())) return false;
  if (dst.device() != src.device()) return false;
  if (dst.numel() * dim_elem < (int64_t(1) << 20)) return false;
  if (at::get_overlap_status(dst, src) != MemOverlapStatus::No) return false;
  if (dst.is_contiguous() && src.transpose(-1, -2).is_contiguous()) {
    // (a) src e' la trasposta di x contiguo [..., R, C]; dst = [..., C, R]
    const Tensor x = src.transpose(-1, -2);
    const int64_t R = x.size(-2), C = x.size(-1);
    return vega_lancia_trasposta(x.const_data_ptr(), dst.data_ptr(), R, C, x.numel() / (R * C),
                                 dim_elem, stream);
  }
  if (src.is_contiguous() && dst.transpose(-1, -2).is_contiguous()) {
    // (b) src contiguo [..., R, C]; la memoria di dst e' la sua trasposta [..., C, R]
    const int64_t R = src.size(-2), C = src.size(-1);
    return vega_lancia_trasposta(src.const_data_ptr(), dst.data_ptr(), R, C, src.numel() / (R * C),
                                 dim_elem, stream);
  }
  return false;
}

}  // anonymous namespace

'''

VECCHIO_RAMO = """  } else {
    if (same_neg) {
      if (!same_conj) {
        conj_kernel_cuda(iter);
      } else {
        direct_copy_kernel_cuda(iter);
      }"""
NUOVO_RAMO = """  } else if (same_type && same_conj && same_neg && src_device == dst_device &&
             vega_copia_trasposta(iter.tensor(0), iter.tensor(1), copy_stream)) {
    // [VEGA-PATCH 76] copia trasposta fatta dal kernel a tessere
  } else {
    if (same_neg) {
      if (!same_conj) {
        conj_kernel_cuda(iter);
      } else {
        direct_copy_kernel_cuda(iter);
      }"""
ANCORA_INC = "#include <ATen/native/TensorIterator.h>\n"
NUOVO_INC = ANCORA_INC + "#include <ATen/MemoryOverlap.h>  // [VEGA-PATCH 76]\n#include <c10/hip/HIPException.h>  // [VEGA-PATCH 76]\n"

t = io.open(F, encoding="utf-8", newline="").read()
if "[VEGA-PATCH 76" in t:
    print("gia' applicata")
    sys.exit(0)
crlf = "\r\n" in t
errori = 0
for vecchio, nuovo in ((ANCORA_INC, NUOVO_INC), (ANCORA_FUNZ, KERNEL + ANCORA_FUNZ), (VECCHIO_RAMO, NUOVO_RAMO)):
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
    if not os.path.exists(F + ".bak_pre_vega76"):
        shutil.copy2(F, F + ".bak_pre_vega76")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

"""Perdita fusa sul vocabolario (lm_head + cross-entropy) per gfx906, a blocchi di token.

2S, 20 ott 2026. Nel passo LoRA di Qwen3.5 (vocabolario 248.320) transformers calcola i logit
fp16 [N, V], ne fa una copia fp32 (ForCausalLMLoss: logits.float()), poi log_softmax e nll; all'indietro
altri due tensori [N, V] (fp32 e fp16). A 512 token sono ~1,3 GB in piu', a 1024 ~2,6 GB, e i logit
restano vivi nell'uscita del modello fino alla fine del passo.

Qui, per ogni blocco di C token:
  1. logit = h_c @ W^T            (GEMM rocBLAS, tipo dei pesi, come lm_head)
  2. un kernel per riga: max e somma degli esponenziali in fp32 (online), perdita = lse - logit[etichetta],
     e SOVRASCRIVE i logit col gradiente softmax - onehot (non scalato: niente sottoflusso fp16 da 1/n)
  3. dh_c = gradiente @ W          (GEMM rocBLAS)
Il gradiente si calcola gia' nell'avanti (la perdita e' l'ultimo nodo); l'indietro scala dh per
grad_out / denominatore. Il peso di lm_head e' congelato nel LoRA: dW non si calcola (se servisse,
ricade sul percorso originale).

Stesse convenzioni di transformers (ForCausalLMLoss + fixed_cross_entropy): etichette spostate di uno,
ignore_index -100, media sui token validi oppure somma / num_items_in_batch.

    import perdita_gfx906; perdita_gfx906.aggancia()   # Qwen3_5ForCausalLM / ForConditionalGeneration
    perdita = perdita_gfx906.perdita_vocabolario(h, W, etichette_spostate)   # uso diretto
"""
import ctypes
import os
import sys
import threading

import torch

vp = ctypes.c_void_p

SORGENTE = r"""
#define INFINITY __builtin_inff()
#if TIPO == 16
typedef _Float16 T;
#else
typedef float T;
#endif

__device__ inline void unisci(float& m, float& s, float m2, float s2) {
    const float mm = fmaxf(m, m2);
    s = (m == -INFINITY ? 0.0f : s * expf(m - mm)) + (m2 == -INFINITY ? 0.0f : s2 * expf(m2 - mm));
    m = mm;
}

/* un blocco da 256 thread per riga; logit [righe, V] contigui, sovrascritti col gradiente */
extern "C" __global__ __launch_bounds__(256)
void entropia_incrociata(T* __restrict__ logit, const long long* __restrict__ etichette,
                         float* __restrict__ perdita, int V, long long riga0, int ignora)
{
    __shared__ float rm[4], rs[4];
    const long long r = blockIdx.x;
    T* x = logit + r * (long long)V;
    const long long et = etichette[riga0 + r];
    const int tid = threadIdx.x;
    if (et == ignora) {
        for (int c = tid; c < V; c += 256) x[c] = (T)0.0f;
        if (tid == 0) perdita[riga0 + r] = 0.0f;
        return;
    }
    float m = -INFINITY, s = 0.0f;
    for (int c = tid; c < V; c += 256) {
        const float v = (float)x[c];
        if (v > m) { s = s * expf(m - v) + 1.0f; m = v; }
        else s += expf(v - m);
    }
    #pragma unroll
    for (int k = 32; k >= 1; k >>= 1) {
        const float m2 = __shfl_xor(m, k, 64), s2 = __shfl_xor(s, k, 64);
        unisci(m, s, m2, s2);
    }
    if ((tid & 63) == 0) { rm[tid >> 6] = m; rs[tid >> 6] = s; }
    __syncthreads();
    m = rm[0]; s = rs[0];
    #pragma unroll
    for (int w = 1; w < 4; ++w) unisci(m, s, rm[w], rs[w]);
    const float lse = m + logf(s);
    const float xe = (float)x[et];
    __syncthreads();                          /* tutti hanno letto x[et] prima di sovrascriverlo */
    if (tid == 0) perdita[riga0 + r] = lse - xe;
    for (int c = tid; c < V; c += 256) {
        const float p = expf((float)x[c] - lse);
        x[c] = (T)(c == et ? p - 1.0f : p);
    }
}
"""

_lock = threading.Lock()
_funzioni = {}
_hip = None
_rtc = None


def _carica_rtc():
    global _rtc
    if _rtc is None:
        lib = os.path.join(os.path.dirname(torch.__file__), "lib")
        for p in (os.path.join(lib, "hiprtc07013.dll"), r"C:\rocm_5_7_expansion_pack\bin\hiprtc07013.dll"):
            if os.path.exists(p):
                k32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
                k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, vp, ctypes.c_ulong]
                k32.LoadLibraryExW.restype = vp
                _rtc = ctypes.CDLL(p, handle=k32.LoadLibraryExW(p, None, 0x8))
                break
        else:
            raise RuntimeError("nessuna hipRTC")
    return _rtc


def _funzione(nome, tipo):
    global _hip
    chiave = (nome, tipo)
    with _lock:
        if chiave not in _funzioni:
            if _hip is None:
                _hip = ctypes.CDLL("amdhip64.dll")
                _hip.hipModuleLaunchKernel.argtypes = [vp] + [ctypes.c_uint] * 7 + [vp, vp, vp]
            rtc = _carica_rtc()
            prog = vp()
            assert rtc.hiprtcCreateProgram(ctypes.byref(prog), SORGENTE.encode(), b"perdita.hip", 0, None, None) == 0
            opz = [b"--offload-arch=gfx906", b"-O3", f"-DTIPO={tipo}".encode()]
            if rtc.hiprtcCompileProgram(prog, len(opz), (ctypes.c_char_p * len(opz))(*opz)) != 0:
                n = ctypes.c_size_t(); rtc.hiprtcGetProgramLogSize(prog, ctypes.byref(n))
                b = ctypes.create_string_buffer(n.value); rtc.hiprtcGetProgramLog(prog, b)
                raise RuntimeError(b.value.decode(errors="replace"))
            n = ctypes.c_size_t(); rtc.hiprtcGetCodeSize(prog, ctypes.byref(n))
            codice = ctypes.create_string_buffer(n.value); rtc.hiprtcGetCode(prog, codice)
            mod, f = vp(), vp()
            assert _hip.hipModuleLoadData(ctypes.byref(mod), codice) == 0
            assert _hip.hipModuleGetFunction(ctypes.byref(f), mod, nome.encode()) == 0
            _funzioni[chiave] = (f, codice, mod)
        return _funzioni[chiave][0]


sys.path.insert(0, r"C:\LaRuota_workspace\lancio_gfx906")
from lancio_gfx906 import Kernel, ptr  # noqa: E402
_KERNEL = {}


def _entropia(logit, etichette, perdita, riga0, ignora):
    C, V = logit.shape
    tipo = 16 if logit.dtype == torch.float16 else 32
    k = _KERNEL.get(tipo)
    if k is None:
        k = _KERNEL[tipo] = Kernel(_funzione("entropia_incrociata", tipo), "pppiqi")
    k(C, (logit.data_ptr(), etichette.data_ptr(), perdita.data_ptr(), V, riga0, ignora))


_BUFFER = {}


def _buffer(n, tipo, dispositivo):
    """Buffer dei logit tenuto fra un passo e l'altro: con ~254 MB allocati e liberati a ogni passo
    l'allocatore su Windows costava ~80 ms a passo (hipMalloc/hipFree). Stesso flusso: riuso sicuro."""
    chiave = (tipo, dispositivo)
    b = _BUFFER.get(chiave)
    if b is None or b.numel() < n:
        _BUFFER.pop(chiave, None)
        b = torch.empty(n, dtype=tipo, device=dispositivo)
        _BUFFER[chiave] = b
    return b


def libera_buffer():
    _BUFFER.clear()


# righe per blocco: i logit di un blocco stanno in ~256 MB (V = 248.320 fp16 -> 540 righe)
MEGA_BLOCCO = int(os.environ.get("PERDITA_MB_BLOCCO", "256"))


class _PerditaVocabolario(torch.autograd.Function):
    @staticmethod
    def forward(ctx, h, W, etichette, denominatore, ignora):
        N, D = h.shape
        V = W.shape[0]
        hc = h.to(W.dtype).contiguous()
        righe = max(1, (MEGA_BLOCCO << 20) // (V * W.element_size()))
        perdite = torch.empty(N, device=h.device, dtype=torch.float32)
        dh = torch.empty(N, D, device=h.device, dtype=W.dtype) if h.requires_grad else None
        buf = _buffer(min(righe, N) * V, W.dtype, h.device)
        with torch.autocast("cuda", enabled=False):          # tipi espliciti: quelli dei pesi
            for r0 in range(0, N, righe):
                r1 = min(N, r0 + righe)
                logit = buf[:(r1 - r0) * V].view(r1 - r0, V)
                torch.mm(hc[r0:r1], W.t(), out=logit)
                _entropia(logit, etichette, perdite, r0, ignora)
                if dh is not None:
                    torch.mm(logit, W, out=dh[r0:r1])
        ctx.save_for_backward(dh, denominatore)
        ctx.tipo_h = h.dtype
        return perdite.sum() / denominatore

    @staticmethod
    def backward(ctx, g):
        dh, denominatore = ctx.saved_tensors
        if dh is None:
            return None, None, None, None, None
        scala = (g / denominatore).to(torch.float32)
        return (dh.float() * scala).to(ctx.tipo_h), None, None, None, None


def perdita_vocabolario(h, W, etichette, num_items_in_batch=None, ignore_index=-100):
    """h [N, D], W [V, D] (congelato), etichette [N] gia' spostate. Come fixed_cross_entropy di transformers."""
    etichette = etichette.reshape(-1).to(device=h.device, dtype=torch.long).contiguous()
    if num_items_in_batch is None:
        den = (etichette != ignore_index).sum().to(torch.float32)
    else:
        den = torch.as_tensor(num_items_in_batch, device=h.device).to(torch.float32)
    return _PerditaVocabolario.apply(h.reshape(-1, h.shape[-1]), W, etichette, den, int(ignore_index))


class _Identita(torch.nn.Module):
    def forward(self, x):
        return x


def _avvolgi(cls, usa_num_items):
    orig = cls.forward

    def forward(self, *args, labels=None, **kwargs):
        lm = getattr(self, "lm_head", None)
        if (labels is None or lm is None or lm.weight.requires_grad or not lm.weight.is_cuda
                or getattr(lm, "bias", None) is not None or kwargs.get("logits_to_keep", 0) != 0
                or "shift_labels" in kwargs or lm.weight.dtype not in (torch.float16, torch.float32)):
            return orig(self, *args, labels=labels, **kwargs)
        self.lm_head = _Identita()                  # l'originale restituisce gli stati nascosti al posto dei logit
        try:
            out = orig(self, *args, labels=None, **kwargs)
        finally:
            self.lm_head = lm
        h = out.logits
        spostate = torch.nn.functional.pad(labels, (0, 1), value=-100)[..., 1:]
        out.loss = perdita_vocabolario(h, lm.weight, spostate,
                                       kwargs.get("num_items_in_batch") if usa_num_items else None)
        out.logits = None
        return out

    forward.__wrapped__ = orig
    return orig, forward


_ORIG = {}


def aggancia(modulo=None):
    """Sostituisce il forward di Qwen3_5ForCausalLM e Qwen3_5ForConditionalGeneration (solo con labels e
    lm_head congelato; altrimenti originale). L'uscita ha logits = None."""
    if modulo is None:
        from transformers.models.qwen3_5 import modeling_qwen3_5 as modulo
    fatto = []
    for nome, usa in (("Qwen3_5ForCausalLM", True), ("Qwen3_5ForConditionalGeneration", False)):
        cls = getattr(modulo, nome, None)
        if cls is not None and cls not in _ORIG:
            _ORIG[cls], cls.forward = _avvolgi(cls, usa)
            fatto.append(nome)
    return fatto


def sgancia():
    for cls, orig in _ORIG.items():
        cls.forward = orig
    _ORIG.clear()

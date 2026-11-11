"""Trasposizione veloce per gfx906: [..., R, C] -> [..., C, R] contigua, con tessere in LDS.

2S, 20 ott 2026. Il copy_ generico di PyTorch su un tensore trasposto va a ~30 GB/s su
gfx906 (fp16), contro 510-580 GB/s di una copia contigua: legge o scrive con passo, e ogni onda
tocca 64 linee di cache diverse. Qui ogni workgroup carica una tessera 64x64 con letture contigue
nella LDS (riga con un elemento di padding, niente conflitti di banco) e la riscrive trasposta con
scritture contigue. Prototipo per la correzione del copy_ di PyTorch (agente Ruota).

    y = trasposta(x)            # x [..., R, C] qualunque dtype da 2 o 4 byte, contiguo
"""
import ctypes
import os
import threading

import torch

vp = ctypes.c_void_p

SORGENTE16 = r"""
/* fp16/bf16 (2 byte): letture e scritture a 32 bit, cioe' coppie di elementi. Tessera 64 x 64. */
#define T 64
extern "C" __global__ __launch_bounds__(256)
void trasposta16(const unsigned short* __restrict__ x, unsigned short* __restrict__ y, int R, int C, long long passo_lotto)
{
    __shared__ unsigned short tessera[T][T + 2];
    const int tx = threadIdx.x & 31, ty = threadIdx.x >> 5;           /* 32 coppie x 8 righe */
    /* ordine diagonale dei blocchi: con righe lunghe potenze di 2 le scritture di blocchi vicini
       finirebbero tutte sullo stesso canale di memoria (partition camping) */
    const int by = (blockIdx.y + blockIdx.x) % gridDim.y;   /* blocchi vicini: righe e colonne diverse */
    const int c0 = blockIdx.x * T, r0 = by * T;
    const unsigned short* xb = x + (long long)blockIdx.z * passo_lotto;
    unsigned short* yb = y + (long long)blockIdx.z * passo_lotto;
    const bool pari_c = (C & 1) == 0, pari_r = (R & 1) == 0;
    #pragma unroll
    for (int i = ty; i < T; i += 8) {
        const int r = r0 + i, c = c0 + 2 * tx;
        if (r < R) {
            if (pari_c && c + 1 < C) {
                const unsigned int v = *(const unsigned int*)(xb + (long long)r * C + c);
                tessera[i][2 * tx] = (unsigned short)(v & 0xFFFF);
                tessera[i][2 * tx + 1] = (unsigned short)(v >> 16);
            } else {
                if (c < C) tessera[i][2 * tx] = xb[(long long)r * C + c];
                if (c + 1 < C) tessera[i][2 * tx + 1] = xb[(long long)r * C + c + 1];
            }
        }
    }
    __syncthreads();
    #pragma unroll
    for (int i = ty; i < T; i += 8) {
        const int c = c0 + i, r = r0 + 2 * tx;
        if (c < C) {
            if (pari_r && r + 1 < R) {
                const unsigned int v = (unsigned int)tessera[2 * tx][i] | ((unsigned int)tessera[2 * tx + 1][i] << 16);
                *(unsigned int*)(yb + (long long)c * R + r) = v;
            } else {
                if (r < R) yb[(long long)c * R + r] = tessera[2 * tx][i];
                if (r + 1 < R) yb[(long long)c * R + r + 1] = tessera[2 * tx + 1][i];
            }
        }
    }
}
"""

SORGENTE = r"""
#define T 64
#define RIGHE 4          /* 256 thread = 64 x 4: ogni thread sposta T/RIGHE = 16 elementi */
extern "C" __global__ __launch_bounds__(256)
void trasposta(const ELEM* __restrict__ x, ELEM* __restrict__ y, int R, int C, long long passo_lotto)
{
    __shared__ ELEM tessera[T][T + 1];
    const int tx = threadIdx.x & (T - 1), ty = threadIdx.x >> 6;
    /* ordine diagonale dei blocchi: con righe lunghe potenze di 2 le scritture di blocchi vicini
       finirebbero tutte sullo stesso canale di memoria (partition camping) */
    const int by = (blockIdx.y + blockIdx.x) % gridDim.y;   /* blocchi vicini: righe e colonne diverse */
    const int c0 = blockIdx.x * T, r0 = by * T;
    const ELEM* xb = x + (long long)blockIdx.z * passo_lotto;
    ELEM* yb = y + (long long)blockIdx.z * passo_lotto;
    #pragma unroll
    for (int i = ty; i < T; i += RIGHE) {
        const int r = r0 + i, c = c0 + tx;
        if (r < R && c < C) tessera[i][tx] = xb[(long long)r * C + c];
    }
    __syncthreads();
    #pragma unroll
    for (int i = ty; i < T; i += RIGHE) {
        const int c = c0 + i, r = r0 + tx;
        if (r < R && c < C) yb[(long long)c * R + r] = tessera[tx][i];
    }
}
"""

_lock = threading.Lock()
_funzioni = {}
_hip = None


def _hiprtc():
    lib = os.path.join(os.path.dirname(torch.__file__), "lib")
    for p in (os.path.join(lib, "hiprtc07013.dll"), r"C:\rocm_5_7_expansion_pack\bin\hiprtc07013.dll"):
        if os.path.exists(p):
            k32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
            k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, vp, ctypes.c_ulong]
            k32.LoadLibraryExW.restype = vp
            return ctypes.CDLL(p, handle=k32.LoadLibraryExW(p, None, 0x8))
    raise RuntimeError("nessuna hipRTC")


def _funzione(nbyte):
    global _hip
    with _lock:
        if nbyte in _funzioni:
            return _funzioni[nbyte][0]
        if _hip is None:
            _hip = ctypes.CDLL("amdhip64.dll")
            _hip.hipModuleLaunchKernel.argtypes = [vp] + [ctypes.c_uint] * 7 + [vp, vp, vp]
        rtc = _hiprtc()
        tipo = {2: "unsigned short", 4: "unsigned int", 8: "unsigned long long"}[nbyte]
        prog = vp()
        src, nome = (SORGENTE16, b"trasposta16") if nbyte == 2 else (SORGENTE, b"trasposta")
        assert rtc.hiprtcCreateProgram(ctypes.byref(prog), src.encode(), b"t.hip", 0, None, None) == 0
        opz = [b"--offload-arch=gfx906", b"-O3", f"-DELEM={tipo}".encode()]
        if rtc.hiprtcCompileProgram(prog, len(opz), (ctypes.c_char_p * len(opz))(*opz)) != 0:
            n = ctypes.c_size_t(); rtc.hiprtcGetProgramLogSize(prog, ctypes.byref(n))
            b = ctypes.create_string_buffer(n.value); rtc.hiprtcGetProgramLog(prog, b)
            raise RuntimeError(b.value.decode(errors="replace"))
        n = ctypes.c_size_t(); rtc.hiprtcGetCodeSize(prog, ctypes.byref(n))
        codice = ctypes.create_string_buffer(n.value); rtc.hiprtcGetCode(prog, codice)
        mod, f = vp(), vp()
        assert _hip.hipModuleLoadData(ctypes.byref(mod), codice) == 0
        assert _hip.hipModuleGetFunction(ctypes.byref(f), mod, nome) == 0
        _funzioni[nbyte] = (f, codice, mod)
        return f


def trasposta(x):
    """[..., R, C] contiguo -> [..., C, R] contiguo (scambio delle ultime due dimensioni)."""
    assert x.is_cuda and x.is_contiguous() and x.dim() >= 2
    R, C = x.shape[-2], x.shape[-1]
    lotti = x.numel() // (R * C) if R * C else 0
    y = torch.empty(*x.shape[:-2], C, R, device=x.device, dtype=x.dtype)
    if x.numel() == 0:
        return y
    f = _funzione(x.element_size())
    a = [vp(x.data_ptr()), vp(y.data_ptr()), ctypes.c_int(R), ctypes.c_int(C), ctypes.c_longlong(R * C)]
    args = (vp * len(a))(*[ctypes.cast(ctypes.byref(v), vp) for v in a])
    rc = _hip.hipModuleLaunchKernel(f, (C + 63) // 64, (R + 63) // 64, lotti, 256, 1, 1, 0,
                                    vp(torch.cuda.current_stream().cuda_stream), args, None)
    if rc != 0:
        raise RuntimeError(f"hipModuleLaunchKernel rc={rc}")
    return y

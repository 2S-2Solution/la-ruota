"""Banda HBM davvero raggiungibile su questa Radeon VII, senza librerie di mezzo.

Serve a decidere una cosa sola: i 24 token/s in generazione di llama.cpp sono
un difetto dei kernel o un limite della scheda com'e' adesso?

La generazione di un token legge tutti i pesi una volta: 4,86 GiB a 24 t/s fa
~117 GB/s. La Radeon VII ha 1.024 GB/s di picco su carta. Se il banco qui sotto
misura ~800 GB/s, il collo e' nei kernel; se misura ~120, e' la scheda o il
driver.

Il kernel e' una lettura-somma (stream: read) su float4, che e' il caso migliore.
"""

import ctypes
import os
import time

LOAD_WITH_ALTERED_SEARCH_PATH = 0x8

SORGENTE = rb"""
typedef float f4 __attribute__((ext_vector_type(4)));

extern "C" __global__ void leggi(const f4* __restrict__ a, float* __restrict__ out, int n)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    int passo = gridDim.x * blockDim.x;
    f4 acc = {0.f, 0.f, 0.f, 0.f};
    for (; i < n; i += passo) acc += a[i];
    float s = acc.x + acc.y + acc.z + acc.w;
    if (s == 1234.5678f) out[0] = s;   // non ottimizzabile via, ma non scrive mai
}

extern "C" __global__ void copia(const f4* __restrict__ a, f4* __restrict__ b, int n)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    int passo = gridDim.x * blockDim.x;
    for (; i < n; i += passo) b[i] = a[i];
}
"""


def carica_hiprtc():
    for p in (r"C:\rocm_5_7_expansion_pack\bin\hiprtc07013.dll",
              r"C:\Program Files\AMD\ROCm\7.1\bin\hiprtc0701.dll",
              r"C:\Program Files\AMD\ROCm\5.7\bin\hiprtc0507.dll"):
        if os.path.exists(p):
            k32 = ctypes.WinDLL("kernel32.dll")
            k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p,
                                           ctypes.c_ulong]
            k32.LoadLibraryExW.restype = ctypes.c_void_p
            h = k32.LoadLibraryExW(p, None, LOAD_WITH_ALTERED_SEARCH_PATH)
            if h:
                return ctypes.CDLL(p, handle=h)
    raise RuntimeError("hipRTC non caricabile")


def compila(rtc):
    prog = ctypes.c_void_p()
    if rtc.hiprtcCreateProgram(ctypes.byref(prog), SORGENTE, b"banda.hip",
                               0, None, None) != 0:
        raise RuntimeError("hiprtcCreateProgram")
    opz = [b"--offload-arch=gfx906", b"-mcode-object-version=5", b"-O3"]
    arr = (ctypes.c_char_p * len(opz))(*opz)
    if rtc.hiprtcCompileProgram(prog, len(opz), arr) != 0:
        n = ctypes.c_size_t()
        rtc.hiprtcGetProgramLogSize(prog, ctypes.byref(n))
        b = ctypes.create_string_buffer(n.value)
        rtc.hiprtcGetProgramLog(prog, b)
        raise RuntimeError(b.value.decode(errors="replace"))
    n = ctypes.c_size_t()
    rtc.hiprtcGetCodeSize(prog, ctypes.byref(n))
    b = ctypes.create_string_buffer(n.value)
    rtc.hiprtcGetCode(prog, b)
    return b


def main():
    codice = compila(carica_hiprtc())
    hip = ctypes.CDLL("amdhip64.dll")
    cvp = ctypes.c_void_p

    mod = cvp()
    if hip.hipModuleLoadData(ctypes.byref(mod), codice) != 0:
        raise RuntimeError("hipModuleLoadData")

    hip.hipModuleLaunchKernel.argtypes = [
        cvp, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
        ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
        ctypes.c_uint, cvp, cvp, cvp]

    BYTE = 2 * 1024 * 1024 * 1024      # 2 GiB per buffer
    n4 = BYTE // 16                     # elementi float4

    a, b = cvp(), cvp()
    for p, quanti in ((a, BYTE), (b, BYTE)):
        rc = hip.hipMalloc(ctypes.byref(p), ctypes.c_size_t(quanti))
        if rc != 0:
            raise RuntimeError(f"hipMalloc rc={rc}")
    hip.hipMemset(a, 0, ctypes.c_size_t(BYTE))

    blocchi, fili = 3840, 256           # 60 CU * 64 blocchi

    def esegui(nome, byte_toccati, argomenti):
        f = cvp()
        if hip.hipModuleGetFunction(ctypes.byref(f), mod, nome) != 0:
            raise RuntimeError(f"hipModuleGetFunction {nome}")
        for _ in range(3):
            hip.hipModuleLaunchKernel(f, blocchi, 1, 1, fili, 1, 1, 0, None,
                                      argomenti, None)
        hip.hipDeviceSynchronize()
        giri = 20
        t0 = time.perf_counter()
        for _ in range(giri):
            hip.hipModuleLaunchKernel(f, blocchi, 1, 1, fili, 1, 1, 0, None,
                                      argomenti, None)
        hip.hipDeviceSynchronize()
        dt = (time.perf_counter() - t0) / giri
        return byte_toccati / dt / 1e9

    n = ctypes.c_int(n4)
    arg_a, arg_b, arg_n = cvp(a.value), cvp(b.value), n
    args_leggi = (cvp * 3)(ctypes.cast(ctypes.byref(arg_a), cvp),
                           ctypes.cast(ctypes.byref(arg_b), cvp),
                           ctypes.cast(ctypes.byref(arg_n), cvp))

    print("banda HBM misurata, Radeon VII (picco di targa: 1024 GB/s)")
    print("-" * 58)
    gbs = esegui(b"leggi", BYTE, args_leggi)
    print(f"  sola lettura  (2 GiB)   : {gbs:7.1f} GB/s   ({gbs/1024*100:4.1f}% del picco)")
    gbs = esegui(b"copia", 2 * BYTE, args_leggi)
    print(f"  copia   (2+2 GiB)       : {gbs:7.1f} GB/s   ({gbs/1024*100:4.1f}% del picco)")

    hip.hipFree(a)
    hip.hipFree(b)


if __name__ == "__main__":
    main()

"""Quanto costa lanciare un kernel su gfx906, misurato senza PyTorch di mezzo.

Serve a rispondere a LA RUOTA sull'attenzione lineare in PyTorch puro: se un
lancio costa X microsecondi e uno strato ne fa N, il pavimento del tempo di
passo e' 24 * N * X, qualunque cosa facciano i kernel.

Si misurano tre cose diverse, che spesso vengono confuse:
  1. lancio ASINCRONO in coda (il costo che si paga davvero quando la GPU e'
     satura di lavoro): si accodano M lanci e si sincronizza una volta sola;
  2. lancio con SINCRONIZZAZIONE per ogni lancio (il caso peggiore, quello di
     chi legge un valore sul host dentro il ciclo);
  3. il tempo del kernel vuoto sulla GPU (per sottrazione, quanto e' overhead).

Il kernel e' vuoto per costruzione: quello che resta e' solo il dispatch.
"""

import ctypes
import os
import time

LOAD_WITH_ALTERED_SEARCH_PATH = 0x8

SORGENTE = rb"""
extern "C" __global__ void vuoto(float* p) { if (p) { } }
"""


def carica_hiprtc():
    percorsi = [
        r"C:\rocm_5_7_expansion_pack\bin\hiprtc07013.dll",
        r"C:\Program Files\AMD\ROCm\7.1\bin\hiprtc0701.dll",
        r"C:\Program Files\AMD\ROCm\5.7\bin\hiprtc0507.dll",
    ]
    k32 = ctypes.WinDLL("kernel32.dll")
    k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_ulong]
    k32.LoadLibraryExW.restype = ctypes.c_void_p
    for p in percorsi:
        if os.path.exists(p):
            h = k32.LoadLibraryExW(p, None, LOAD_WITH_ALTERED_SEARCH_PATH)
            if h:
                print(f"hipRTC: {p}")
                return ctypes.CDLL(p, handle=h), p
    raise RuntimeError("nessuna hipRTC caricabile")


def compila(rtc):
    cvp, ccp, ci, cst = ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_size_t
    prog = cvp()
    rc = rtc.hiprtcCreateProgram(ctypes.byref(prog), SORGENTE, b"vuoto.hip",
                                 0, None, None)
    if rc != 0:
        raise RuntimeError(f"hiprtcCreateProgram rc={rc}")
    opzioni = [b"--offload-arch=gfx906", b"-mcode-object-version=5", b"-O3"]
    arr = (ccp * len(opzioni))(*opzioni)
    rc = rtc.hiprtcCompileProgram(prog, len(opzioni), arr)
    if rc != 0:
        n = cst()
        rtc.hiprtcGetProgramLogSize(prog, ctypes.byref(n))
        buf = ctypes.create_string_buffer(n.value)
        rtc.hiprtcGetProgramLog(prog, buf)
        raise RuntimeError(f"compilazione rc={rc}\n{buf.value.decode(errors='replace')}")
    n = cst()
    rtc.hiprtcGetCodeSize(prog, ctypes.byref(n))
    buf = ctypes.create_string_buffer(n.value)
    rtc.hiprtcGetCode(prog, buf)
    return buf


def main():
    rtc, _ = carica_hiprtc()
    codice = compila(rtc)

    hip = ctypes.CDLL("amdhip64.dll")
    cvp = ctypes.c_void_p

    modulo = cvp()
    rc = hip.hipModuleLoadData(ctypes.byref(modulo), codice)
    if rc != 0:
        raise RuntimeError(f"hipModuleLoadData rc={rc}")
    funz = cvp()
    rc = hip.hipModuleGetFunction(ctypes.byref(funz), modulo, b"vuoto")
    if rc != 0:
        raise RuntimeError(f"hipModuleGetFunction rc={rc}")

    mem = cvp()
    hip.hipMalloc(ctypes.byref(mem), ctypes.c_size_t(4096))

    arg0 = cvp(mem.value)
    args = (cvp * 1)(ctypes.cast(ctypes.byref(arg0), cvp))

    hip.hipModuleLaunchKernel.argtypes = [
        cvp, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
        ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
        ctypes.c_uint, cvp, cvp, cvp]

    def lancia():
        return hip.hipModuleLaunchKernel(funz, 1, 1, 1, 64, 1, 1, 0, None,
                                         args, None)

    # riscaldamento
    for _ in range(200):
        lancia()
    hip.hipDeviceSynchronize()

    def misura(m, sincronizza_ogni_volta):
        t0 = time.perf_counter()
        for _ in range(m):
            rc = lancia()
            if rc != 0:
                raise RuntimeError(f"lancio rc={rc}")
            if sincronizza_ogni_volta:
                hip.hipDeviceSynchronize()
        hip.hipDeviceSynchronize()
        return (time.perf_counter() - t0) / m * 1e6

    print()
    print("costo per lancio, kernel vuoto, gfx906")
    print("-" * 46)
    for m in (2000, 10000, 40000, 100000):
        us = misura(m, False)
        print(f"  accodato ({m:>5} lanci)      : {us:6.2f} us")
    for m in (500, 2000):
        us = misura(m, True)
        print(f"  sincronizzato ({m:>5} lanci) : {us:6.2f} us")

    hip.hipFree(mem)


if __name__ == "__main__":
    main()

"""Chiama il runtime HIP direttamente via ctypes, senza PyTorch.

Serve a stabilire se l'access violation su torch.empty nasce nel runtime
(amdhip64.dll) o nello strato PyTorch (caching allocator / guard / stream).
"""
import ctypes
import os

DLL = r"C:\Windows\System32\amdhip64.dll"
hip = ctypes.CDLL(DLL)
print(f"caricata {DLL}")


def chk(nome, rc):
    print(f"  {nome}: rc={rc}" + ("  OK" if rc == 0 else "  ERRORE"))
    return rc == 0


rc = hip.hipInit(0)
chk("hipInit", rc)

n = ctypes.c_int(0)
chk("hipGetDeviceCount", hip.hipGetDeviceCount(ctypes.byref(n)))
print(f"  device count = {n.value}")

chk("hipSetDevice(0)", hip.hipSetDevice(0))

free_b = ctypes.c_size_t(0)
tot_b = ctypes.c_size_t(0)
if chk("hipMemGetInfo", hip.hipMemGetInfo(ctypes.byref(free_b), ctypes.byref(tot_b))):
    print(f"  free {free_b.value / 2**30:.2f} GB / tot {tot_b.value / 2**30:.2f} GB")

print("\n[hipMalloc]")
ptr = ctypes.c_void_p(0)
hip.hipMalloc.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t]
hip.hipMalloc.restype = ctypes.c_int
if chk("hipMalloc(64)", hip.hipMalloc(ctypes.byref(ptr), ctypes.c_size_t(64))):
    print(f"  ptr = 0x{ptr.value:x}")

    print("\n[hipMemcpy H2D/D2H]")
    src = (ctypes.c_float * 16)(*[float(i) for i in range(16)])
    dst = (ctypes.c_float * 16)()
    hip.hipMemcpy.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
    hip.hipMemcpy.restype = ctypes.c_int
    chk("H2D", hip.hipMemcpy(ptr, src, ctypes.c_size_t(64), 1))   # hipMemcpyHostToDevice
    chk("D2H", hip.hipMemcpy(dst, ptr, ctypes.c_size_t(64), 2))   # hipMemcpyDeviceToHost
    ok = list(dst) == [float(i) for i in range(16)]
    print(f"  dati integri: {ok}")

    hip.hipFree.argtypes = [ctypes.c_void_p]
    chk("hipFree", hip.hipFree(ptr))

print("\n[stream]")
st = ctypes.c_void_p(0)
hip.hipStreamCreate.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
if chk("hipStreamCreate", hip.hipStreamCreate(ctypes.byref(st))):
    hip.hipStreamSynchronize.argtypes = [ctypes.c_void_p]
    chk("hipStreamSynchronize", hip.hipStreamSynchronize(st))
    hip.hipStreamDestroy.argtypes = [ctypes.c_void_p]
    chk("hipStreamDestroy", hip.hipStreamDestroy(st))

print("\nfine")

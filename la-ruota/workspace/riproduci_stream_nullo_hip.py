"""hipStreamWaitEvent: chi aspetta, su quale stream e' registrato l'evento, con quali flag."""
import ctypes

hip = ctypes.WinDLL(r"C:\Windows\System32\amdhip64.dll")
for n in ("hipSetDevice", "hipStreamCreateWithFlags", "hipEventCreateWithFlags", "hipEventRecord",
          "hipStreamWaitEvent", "hipDeviceSynchronize", "hipRuntimeGetVersion", "hipDriverGetVersion"):
    getattr(hip, n).restype = ctypes.c_int
hip.hipGetErrorName.restype = ctypes.c_char_p
hip.hipStreamWaitEvent.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
hip.hipEventRecord.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


def nome(rc):
    return hip.hipGetErrorName(rc).decode()


hip.hipSetDevice(0)
v = ctypes.c_int()
hip.hipRuntimeGetVersion(ctypes.byref(v))
print("runtime HIP", v.value)


def stream(flag):
    s = ctypes.c_void_p()
    assert hip.hipStreamCreateWithFlags(ctypes.byref(s), flag) == 0
    return s


A, B = stream(1), stream(1)
C_blocking = stream(0)
NULLO = ctypes.c_void_p(None)
PER_THREAD = ctypes.c_void_p(2)   # hipStreamPerThread
# flag evento: 0 default (con tempi), 2 DisableTiming
for flag_ev in (0, 2):
    for chi_registra, s_rec in (("nullo", NULLO), ("A", A)):
        for chi_aspetta, s_wait in (("nullo", NULLO), ("B", B), ("C bloccante", C_blocking), ("per-thread", PER_THREAD)):
            e = ctypes.c_void_p()
            hip.hipEventCreateWithFlags(ctypes.byref(e), flag_ev)
            r1 = hip.hipEventRecord(e, s_rec)
            r2 = hip.hipStreamWaitEvent(s_wait, e, 0)
            print(f"evento flag {flag_ev}  registrato su {chi_registra:5s}  atteso da {chi_aspetta:12s}: "
                  f"record {nome(r1)}, wait {nome(r2)}")
print("sync finale:", nome(hip.hipDeviceSynchronize()))

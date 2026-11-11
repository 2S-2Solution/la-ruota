import ctypes, os, sys
from ctypes import wintypes
import torch
try:
    torch.zeros(4, device="cuda")
except Exception:
    pass
psapi = ctypes.WinDLL("psapi")
k32 = ctypes.WinDLL("kernel32")
h = k32.GetCurrentProcess()
arr = (ctypes.c_void_p * 2048)()
needed = wintypes.DWORD()
psapi.EnumProcessModules(h, arr, ctypes.sizeof(arr), ctypes.byref(needed))
n = needed.value // ctypes.sizeof(ctypes.c_void_p)
buf = ctypes.create_unicode_buffer(1024)
visti = []
for i in range(n):
    psapi.GetModuleFileNameExW(h, arr[i], buf, 1024)
    p = buf.value
    b = os.path.basename(p).lower()
    if any(k in b for k in ("hip", "comgr", "cmgr", "amdhip", "rocblas", "miopen")):
        visti.append(p)
for p in sorted(visti):
    try:
        d = os.path.getsize(p) / 1048576
    except OSError:
        d = 0
    print(f"  {d:8.2f} MB  {p}")

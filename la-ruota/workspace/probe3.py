import os, ctypes
p = r"C:\TheRock_workspace\TheRock\build_gfx906\dist\rocm\bin\MIOpen.dll"
try:
    ctypes.CDLL(p); print("MIOpen TheRock dalla sua dir: OK")
except OSError as e:
    print("MIOpen TheRock dalla sua dir: FAIL", str(e)[:110])

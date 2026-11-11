import os, ctypes
lib = r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib"
os.add_dll_directory(lib)
os.add_dll_directory(r"C:\rocm_5_7_expansion_pack\bin")
for n in ["amd_cmgr3.dll","hiprtc07013.dll","amdhip64_7.dll","rocblas.dll"]:
    try:
        ctypes.CDLL(os.path.join(lib,n)); print(f"{n:22s} OK")
    except OSError as e:
        print(f"{n:22s} FAIL {str(e)[:80]}")
print("--- MIOpen dalla sua sede originale ---")
try:
    ctypes.CDLL(r"C:\rocm_5_7_expansion_pack\bin\MIOpen.dll"); print("MIOpen (Marconi bin) OK")
except OSError as e:
    print("MIOpen (Marconi bin) FAIL", str(e)[:120])

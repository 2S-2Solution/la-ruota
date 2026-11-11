import os, ctypes
lib = r"C:\LaRuota_workspace\venv_build\Lib\site-packages\torch\lib"
os.add_dll_directory(lib)
order = ["amdhip64_6.dll","amdhip64_7.dll","amd_comgr.dll","hiprtc0507.dll","hiprtc07013.dll",
         "rocblas.dll","MIOpen.dll","hipblas.dll","libhipsparse.dll","hipsolver.dll",
         "libhipblaslt.dll","rocsolver.dll","rocsparse.dll","rocfft.dll","hipfft.dll"]
for name in order:
    p = os.path.join(lib, name)
    if not os.path.exists(p):
        print(f"{name:24s} ASSENTE"); continue
    try:
        ctypes.CDLL(p)
        print(f"{name:24s} OK")
    except OSError as e:
        print(f"{name:24s} FAIL {e}")

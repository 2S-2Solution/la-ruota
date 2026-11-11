"""Lancio veloce dei kernel hipRTC da Python (gfx906, Windows). 2S, 20 ott 2026.

Con ctypes "classico" (un oggetto c_int/c_void_p per argomento + array di puntatori con cast/byref) un
lancio costava ~35-50 us di CPU: per gli MLP e i LoRA piccoli il passo era legato alla CPU per questo.
Qui gli argomenti si impacchettano con struct in un buffer unico (allineamento come in C: ogni campo
allineato alla sua dimensione) e si passano con HIP_LAUNCH_PARAM_BUFFER_POINTER nell'`extra` di
hipModuleLaunchKernel, che copia gli argomenti nel pacchetto di comando prima di tornare: il buffer si
puo' riusare subito.

    from lancio_gfx906 import Kernel
    k = Kernel(funzione_hip, "ppiif")          # p puntatore, i int32, q int64, f float32
    # ATTENZIONE: su Windows (LLP64) `long` e' a 32 bit anche nel kernel: a 'q' deve corrispondere long long / int64_t
    # (con `long` il kernel legge 4 byte fuori posto quando c'e' riempimento: valore 0, nessun errore).
    k(griglia, valori, blocco=256)             # valori: int (data_ptr o 0), float; tensori -> data_ptr()
"""
import ctypes
import hashlib
import os
import struct
import threading

import torch

vp = ctypes.c_void_p
_hip = None
_DIM = {"p": (8, "Q"), "q": (8, "q"), "i": (4, "i"), "f": (4, "f")}


def hip():
    global _hip
    if _hip is None:
        _hip = ctypes.CDLL("amdhip64.dll")
        _hip.hipModuleLaunchKernel.argtypes = [vp] + [ctypes.c_uint] * 7 + [vp, vp, vp]
        _hip.hipModuleLaunchKernel.restype = ctypes.c_int
    return _hip


class Kernel:
    __slots__ = ("f", "s", "buf", "dim", "extra", "lancia", "tipi")

    def __init__(self, funzione, firma):
        formato, off = "<", 0
        for c in firma:
            n, cod = _DIM[c]
            pad = (-off) % n
            formato += "x" * pad + cod
            off += pad + n
        pad = (-off) % 8
        formato += "x" * pad
        self.s = struct.Struct(formato)
        self.tipi = firma
        self.f = vp(funzione.value if isinstance(funzione, vp) else funzione)
        self.buf = ctypes.create_string_buffer(max(8, self.s.size))
        self.dim = ctypes.c_size_t(self.s.size)
        self.extra = (vp * 5)(1, ctypes.addressof(self.buf), 2, ctypes.addressof(self.dim), 3)
        self.lancia = hip().hipModuleLaunchKernel

    def __call__(self, griglia, valori, blocco=256):
        self.s.pack_into(self.buf, 0, *valori)
        gx, gy, gz = griglia if isinstance(griglia, tuple) else (griglia, 1, 1)
        rc = self.lancia(self.f, gx, gy, gz, blocco, 1, 1, 0, torch.cuda.current_stream().cuda_stream,
                         None, self.extra)
        if rc != 0:
            raise RuntimeError(f"hipModuleLaunchKernel rc={rc}")


def ptr(t):
    """data_ptr di un tensore o 0 per None."""
    return 0 if t is None else t.data_ptr()


# ---- Compilazione hipRTC con cache su disco (22 ott 2026) ----
# Ogni processo ricompilava da capo: mlp_gfx906 ~1,8 s per nome di kernel, ~7 s a processo per programma.
# Qui il codice oggetto si salva in CACHE_RTC con chiave sha256(sorgente, opzioni, impronta di hiprtc/comgr/builtins:
# nome, dimensione, data); in memoria un modulo per chiave, cosi' piu' kernel dello stesso sorgente si compilano una
# volta. Scrittura atomica (file temporaneo + os.replace); un file illeggibile o rifiutato da hipModuleLoadData si
# ricompila. GFX906_CACHE_RTC=0 la spegne.
#     f = funzione(SORGENTE, [b"--offload-arch=gfx906", b"-O3"], "nome_kernel", "mlp.hip")
CACHE_RTC = os.environ.get("GFX906_CACHE_RTC", r"C:\LaRuota_workspace\cache_hiprtc")
_rtc = None
_rtc_impronta = b""
_moduli = {}
_blocco = threading.Lock()


def rtc():
    """hipRTC come la caricano i moduli (torch/lib, poi expansion pack), con l'impronta delle DLL del compilatore."""
    global _rtc, _rtc_impronta
    if _rtc is None:
        lib = os.path.join(os.path.dirname(torch.__file__), "lib")
        for p in (os.path.join(lib, "hiprtc07013.dll"), r"C:\rocm_5_7_expansion_pack\bin\hiprtc07013.dll"):
            if os.path.exists(p):
                k32 = ctypes.WinDLL("kernel32.dll", use_last_error=True)
                k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, vp, ctypes.c_ulong]
                k32.LoadLibraryExW.restype = vp
                _rtc = ctypes.CDLL(p, handle=k32.LoadLibraryExW(p, None, 0x8))
                d = os.path.dirname(p)
                parti = []
                for n in sorted(os.listdir(d)):
                    nl = n.lower()
                    if nl.endswith(".dll") and (nl.startswith("hiprtc") or nl.startswith("amd_comgr")):
                        st = os.stat(os.path.join(d, n))
                        parti.append(f"{nl}:{st.st_size}:{st.st_mtime_ns}")
                _rtc_impronta = (p.lower() + "|" + "|".join(parti)).encode()
                break
        else:
            raise RuntimeError("nessuna hipRTC")
    return _rtc


def _b(o):
    return o if isinstance(o, bytes) else str(o).encode()


def _compila(sorgente, opzioni, nome_file):
    r = rtc()
    prog = vp()
    assert r.hiprtcCreateProgram(ctypes.byref(prog), sorgente.encode(), nome_file.encode(), 0, None, None) == 0
    try:
        if r.hiprtcCompileProgram(prog, len(opzioni), (ctypes.c_char_p * len(opzioni))(*opzioni)) != 0:
            n = ctypes.c_size_t(); r.hiprtcGetProgramLogSize(prog, ctypes.byref(n))
            b = ctypes.create_string_buffer(n.value); r.hiprtcGetProgramLog(prog, b)
            raise RuntimeError(b.value.decode(errors="replace"))
        n = ctypes.c_size_t(); r.hiprtcGetCodeSize(prog, ctypes.byref(n))
        codice = ctypes.create_string_buffer(n.value); r.hiprtcGetCode(prog, codice)
        return codice.raw
    finally:
        r.hiprtcDestroyProgram(ctypes.byref(prog))


def codice(sorgente, opzioni, nome_file="kernel.hip", rileggi=True):
    """Codice oggetto (bytes) e percorso in cache (None se spenta). Compila solo se non e' gia' su disco."""
    opzioni = [_b(o) for o in opzioni]
    rtc()
    h = hashlib.sha256()
    for parte in (_rtc_impronta, sorgente.encode(), b"\0".join(opzioni), nome_file.encode()):
        h.update(parte); h.update(b"\x01")
    percorso = None if CACHE_RTC == "0" else os.path.join(CACHE_RTC, h.hexdigest() + ".co")
    if percorso and rileggi:
        try:
            with open(percorso, "rb") as fh:
                dati = fh.read()
            if dati:
                return dati, percorso
        except OSError:
            pass
    dati = _compila(sorgente, opzioni, nome_file)
    if percorso:
        try:
            os.makedirs(CACHE_RTC, exist_ok=True)
            tmp = f"{percorso}.{os.getpid()}.{threading.get_ident()}.tmp"
            with open(tmp, "wb") as fh:
                fh.write(dati)
            try:
                os.replace(tmp, percorso)
            except OSError:          # un altro processo l'ha appena scritto (o lo sta leggendo): va bene il suo
                os.remove(tmp)
        except OSError:
            pass
    return dati, percorso


def modulo(sorgente, opzioni, nome_file="kernel.hip"):
    """hipModule caricato (uno per sorgente + opzioni nel processo)."""
    opzioni = [_b(o) for o in opzioni]
    chiave = (sorgente, tuple(opzioni), nome_file)
    with _blocco:
        if chiave not in _moduli:
            h = hip()
            dati, percorso = codice(sorgente, opzioni, nome_file)
            buf = ctypes.create_string_buffer(dati, len(dati))
            mod = vp()
            if h.hipModuleLoadData(ctypes.byref(mod), buf) != 0:
                if not percorso:
                    raise RuntimeError("hipModuleLoadData rifiuta il codice appena compilato")
                dati, _ = codice(sorgente, opzioni, nome_file, rileggi=False)   # file guasto: ricompila e riscrive
                buf = ctypes.create_string_buffer(dati, len(dati))
                assert h.hipModuleLoadData(ctypes.byref(mod), buf) == 0
            _moduli[chiave] = (mod, buf)
        return _moduli[chiave][0]


def funzione(sorgente, opzioni, nome_kernel, nome_file="kernel.hip"):
    """Puntatore alla funzione `nome_kernel` del modulo compilato (o letto dalla cache)."""
    mod = modulo(sorgente, opzioni, nome_file)
    f = vp()
    rc = hip().hipModuleGetFunction(ctypes.byref(f), mod, nome_kernel.encode())
    if rc != 0:
        raise RuntimeError(f"hipModuleGetFunction({nome_kernel}) rc={rc}")
    return f

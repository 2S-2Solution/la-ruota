"""Verifica di La Ruota 2.15 (PyTorch 2.15 ROCm nativo per Radeon VII, gfx906).

Controlla sistema, driver, GPU, shim e code object, poi fa prove brevi sulla GPU contro la CPU.
Ultima riga: "ESITO: OK" oppure "ESITO: FALLITO - <motivo>". Codice d'uscita 0 o 1.
"""
import ctypes
import glob
import os
import platform
import struct
import subprocess
import sys
import tempfile
import time

problemi = []


def riga(chiave, valore):
    print(f"  {chiave:<26} {valore}")


def fallito(motivo):
    print(f"ESITO: FALLITO - {motivo}")
    sys.exit(1)


print("La Ruota 2.15 - verifica")
print("1. Sistema e driver")
riga("Windows", f"{platform.release()} {platform.version()} ({platform.machine()})")
riga("Python", sys.version.split()[0])
try:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name + '|' + $_.DriverVersion }"],
        capture_output=True, text=True, timeout=60).stdout.strip().splitlines()
    for r in out:
        nome, _, ver = r.partition("|")
        riga("scheda video (Windows)", f"{nome.strip()}  driver {ver.strip()}")
except Exception as e:  # noqa: BLE001
    riga("scheda video (Windows)", f"non letta ({e})")
hip = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "amdhip64.dll")
if not os.path.exists(hip):
    fallito("manca System32\\amdhip64.dll: installare il driver AMD Adrenalin (runtime HIP)")
riga("runtime HIP del driver", hip)

print("2. GPU")
t0 = time.time()
try:
    import torch
except Exception as e:  # noqa: BLE001
    fallito(f"import torch non riuscito: {e}")
sito = os.path.dirname(os.path.dirname(torch.__file__))
bin_core = os.path.join(sito, "_rocm_sdk_core", "bin")
riga("torch", f"{torch.__version__}, HIP {torch.version.hip}")
if not torch.cuda.is_available():
    if os.path.exists(os.path.join(bin_core, "amdhip64_7.dll.amd")):
        fallito("torch non vede nessuna GPU (driver Adrenalin assente, scheda non riconosciuta o shim di Marconi non adatto)")
    fallito("torch non vede nessuna GPU: manca lo shim amdhip64_7.dll del kit rocm-marconi (rifare installa.cmd)")
prop = torch.cuda.get_device_properties(0)
arch = getattr(prop, "gcnArchName", "?")
riga("dispositivo 0", f"{prop.name}, {prop.total_memory / 2**30:.1f} GB, {arch}")
if not arch.startswith("gfx906"):
    fallito(f"GPU {arch}: questo pacchetto e' provato solo su gfx906 (Radeon VII)")
riga("MIOpen", torch.backends.cudnn.version())

print("3. Code object (il driver carica V4 e V5, non V6)")
try:
    rtc_dll = sorted(f for f in glob.glob(os.path.join(bin_core, "hiprtc*.dll")) if "builtins" not in f.lower())
    if not rtc_dll:
        fallito(f"manca hipRTC in {bin_core}")
    rtc = ctypes.CDLL(rtc_dll[0])
    src = b'extern "C" __global__ void somma(float* a, float b) { a[threadIdx.x] += b; }'
    prog = ctypes.c_void_p()
    rc = rtc.hiprtcCreateProgram(ctypes.byref(prog), src, b"prova.hip", 0, None, None)
    opz = [b"--offload-arch=gfx906", b"-mcode-object-version=5"]
    rc2 = rtc.hiprtcCompileProgram(prog, len(opz), (ctypes.c_char_p * len(opz))(*opz))
    n = ctypes.c_size_t()
    rtc.hiprtcGetCodeSize(prog, ctypes.byref(n))
    img = ctypes.create_string_buffer(n.value)
    rtc.hiprtcGetCode(prog, img)
    if rc or rc2 or n.value < 64 or img.raw[:4] != b"\x7fELF":
        fallito(f"compilazione hipRTC non riuscita (create={rc}, compile={rc2})")
    abi = img.raw[8]
    flags = struct.unpack_from("<I", img.raw, 0x30)[0]
    versione = {2: "V4", 3: "V5", 4: "V6"}.get(abi, f"ABI {abi}")
    riga("compilato", f"code object {versione}, e_flags 0x{flags:x} con {os.path.basename(rtc_dll[0])}")
    torch.zeros(1, device="cuda")
    amdhip = ctypes.CDLL(os.path.join(bin_core, "amdhip64_7.dll"))
    mod = ctypes.c_void_p()
    rcl = amdhip.hipModuleLoadData(ctypes.byref(mod), img)
    if rcl != 0:
        fallito(f"il runtime rifiuta il code object {versione} (rc={rcl})")
    amdhip.hipModuleUnload(mod)
    riga("caricato dal runtime", "si'")
except SystemExit:
    raise
except Exception as e:  # noqa: BLE001
    fallito(f"prova del code object non riuscita: {e}")

print("4. Prove GPU contro CPU")
torch.manual_seed(0)


def scarto(a, b):
    return ((a.detach().cpu().double() - b.detach().double()).abs().max() / (b.detach().double().abs().max() + 1e-12)).item()


def prova(nome, fn, soglia):
    t = time.time()
    try:
        e = fn()
    except Exception as ex:  # noqa: BLE001
        problemi.append(f"{nome}: {type(ex).__name__}: {ex}")
        riga(nome, f"ERRORE {type(ex).__name__}: {str(ex)[:120]}")
        return
    torch.cuda.synchronize()
    stato = "ok" if e < soglia else "SBAGLIATO"
    if e >= soglia:
        problemi.append(f"{nome}: scarto {e:.1e} oltre {soglia:.0e}")
    riga(nome, f"{stato}  scarto relativo {e:.1e}  ({time.time() - t:.1f} s)")


def p_matmul():
    a, b = torch.randn(1024, 1024), torch.randn(1024, 1024)
    return scarto(a.cuda() @ b.cuda(), a @ b)


def p_conv():
    x = torch.randn(8, 3, 64, 64)
    conv = torch.nn.Conv2d(3, 16, 3, padding=1)
    cc = torch.nn.Conv2d(3, 16, 3, padding=1)
    cc.load_state_dict(conv.state_dict())
    cc = cc.cuda()
    conv(x).square().sum().backward()
    cc(x.cuda()).square().sum().backward()
    return max(scarto(cc.weight.grad, conv.weight.grad), scarto(cc.bias.grad, conv.bias.grad))


def p_lstm():
    x = torch.randn(4, 40, 32)
    m = torch.nn.LSTM(32, 64, num_layers=2, batch_first=True)
    mg = torch.nn.LSTM(32, 64, num_layers=2, batch_first=True)
    mg.load_state_dict(m.state_dict())
    mg = mg.cuda()
    peggiore = 0.0
    for _ in range(3):
        m.zero_grad(); mg.zero_grad()
        y, yg = m(x)[0], mg(x.cuda())[0]
        y.sum().backward()
        yg.sum().backward()
        peggiore = max(peggiore, scarto(yg, y), *(scarto(pg.grad, pc.grad) for pg, pc in zip(mg.parameters(), m.parameters())))
    return peggiore


def p_softmax64():
    x = torch.randn(64, 3000, dtype=torch.float64)
    return scarto(torch.softmax(x.cuda(), -1), torch.softmax(x, -1))


def p_lstsq():
    a = torch.randn(6, 4)
    a[:, 3] = 0.0  # rango non pieno: la CPU solleva, la GPU deve fare lo stesso
    try:
        torch.linalg.lstsq(a.cuda(), torch.randn(6, 2).cuda())
    except torch.linalg.LinAlgError:
        return 0.0
    raise RuntimeError("lstsq con rango non pieno non ha sollevato LinAlgError")


def p_cpu_mkl():
    a = torch.randn(2048, 2048)
    a @ a
    t = time.perf_counter()
    for _ in range(3):
        a @ a
    gflops = 3 * 2 * 2048 ** 3 / (time.perf_counter() - t) / 1e9
    riga("matmul CPU fp32 2048", f"{gflops:.0f} GFLOPS (MKL)")
    return 0.0 if gflops > 100 else 1.0


FIGLIO_MIOPEN = r'''
import torch
torch.backends.cudnn.benchmark = True
x = torch.randn(2, 7, 23, 19); w = torch.randn(5, 7, 3, 5)
y = torch.nn.functional.conv2d(x.cuda(), w.cuda(), padding=(1, 2), dilation=(1, 2))
r = torch.nn.functional.conv2d(x, w, padding=(1, 2), dilation=(1, 2))
print(((y.cpu().double() - r.double()).abs().max() / r.double().abs().max()).item())
'''


def p_miopen_compila():
    """Conv con il solver HIP ConvDirectNaiveConvFwd imposto e cache vuota: MIOpen deve compilare
    il kernel con hipRTC e scriverlo nella cache."""
    with tempfile.TemporaryDirectory() as d:
        cache = os.path.join(d, "cache")
        env = dict(os.environ, MIOPEN_DEBUG_FIND_ONLY_SOLVER="ConvDirectNaiveConvFwd", MIOPEN_FIND_MODE="1")
        codice = ("import os; os.environ['MIOPEN_CUSTOM_CACHE_DIR'] = os.environ['MIOPEN_USER_DB_PATH'] = "
                  f"r'{cache}'\n" + FIGLIO_MIOPEN)
        r = subprocess.run([sys.executable, "-I", "-c", codice], env=env, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1][:200])
        scritti = [f for f in glob.glob(os.path.join(cache, "**", "*"), recursive=True) if os.path.isfile(f)]
        if not scritti:
            raise RuntimeError("MIOpen non ha compilato nulla (cache vuota)")
        return float(r.stdout.strip().splitlines()[-1])


prova("matmul fp32 1024", p_matmul, 1e-4)
prova("conv 3x3 RGB, gradiente", p_conv, 1e-4)
prova("LSTM 2 strati, 40 passi", p_lstm, 1e-4)
prova("softmax fp64, righe 3000", p_softmax64, 1e-12)
prova("lstsq, rango non pieno", p_lstsq, 0.5)
prova("matmul CPU (MKL)", p_cpu_mkl, 0.5)
prova("MIOpen compila con hipRTC", p_miopen_compila, 1e-4)
print(f"  durata totale              {time.time() - t0:.1f} s (la prima volta MIOpen compila i kernel)")

if problemi:
    fallito("; ".join(problemi))
print("ESITO: OK")

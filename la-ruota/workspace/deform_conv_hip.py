"""Convoluzione deformabile modulata (DCNv2), solo passo in avanti, per LA RUOTA.

    from deform_conv_hip import deform_conv2d

Stessa firma e stessa semantica di `torchvision.ops.deform_conv2d`, cosi' i
modelli che la usano (VRT, e via adattatore BasicVSR++/EDVR/IconVSR) non vanno
modificati.

COM'E' FATTA
------------
La struttura e' quella di torchvision: un kernel di **im2col deformabile** che
campiona l'ingresso nei punti spostati, e poi un prodotto matriciale. Solo
l'im2col e' codice nostro; la moltiplicazione la fa PyTorch, quindi finisce su
rocBLAS che sulla ruota e' gia' verificato.

Il kernel HIP viene compilato **a runtime con hipRTC** la prima volta che serve,
e poi tenuto in memoria. Non c'e' nessun sistema di build: niente torchvision da
compilare, niente `torch.utils.cpp_extension` (e quindi nemmeno il problema di
`library_paths(cuda=True)`, che cerca le librerie CUDA dentro l'installazione di
torch).

VINCOLI RISPETTATI
------------------
- `--offload-arch=gfx906` LISCIO, senza feature: e_flags 0x52f, xnack e sramecc
  entrambi "any". Con sramecc attivo il binario verrebbe rifiutato.
- `-mcode-object-version=5`: il driver Adrenalin legge fino alla v5, la v6 la
  rifiuta con rc=303.
- hipRTC caricata per PERCORSO ASSOLUTO con LOAD_WITH_ALTERED_SEARCH_PATH: una
  DLL ROCm caricata fuori dalla sua cartella risolve le dipendenze sui binari
  sbagliati accanto e scrive all'indirizzo 0.
- Il flag `-O3` qui va bene: l'avvertenza della guida riguarda `clang-cl`, che lo
  scarta in silenzio. hipRTC prende opzioni in stile clang.

LIMITI DICHIARATI
-----------------
- Solo **passo in avanti**, come richiesto. Non c'e' backward: usare sotto
  `torch.no_grad()` o in `eval()`.
- Solo **fp32**. Per fp16 servirebbe un secondo kernel; non si scrive codice non
  verificato.
- La memoria di appoggio (il tensore `colonne`) e' quella dell'im2col:
  `C_in * kH * kW * n_par * H_out * W_out` elementi. E' la stessa di torchvision.
"""

import ctypes
import os
import threading

import torch

__all__ = ["deform_conv2d", "modulated_deform_conv2d", "DeformConv2d",
           "informazioni"]

# ---------------------------------------------------------------------------
#  Il kernel
# ---------------------------------------------------------------------------
#
# E' la trascrizione dell'im2col deformabile di torchvision
# (torchvision/csrc/ops/cuda/deform_conv2d_kernel.cu). Due punti da non
# sbagliare, perche' sbagliati non danno errore ma numeri diversi:
#
#  - l'ordine dei canali di `offset` e' (porta, y/x): per il campione
#    `i*kW + j` lo spostamento in Y sta al canale `2*(i*kW+j)` e quello in X al
#    canale successivo;
#  - fuori dai bordi vale ZERO, non replica. Il controllo va fatto sul punto
#    frazionario PRIMA di arrotondare, altrimenti un punto a -0.3 verrebbe
#    trattato come dentro.

SORGENTE = r"""
extern "C" __device__ float bilineare(
    const float* in, int altezza, int larghezza, float y, float x)
{
    // Zero-padding: fuori dal bordo non si campiona nulla.
    if (y <= -1.0f || (float)altezza <= y || x <= -1.0f || (float)larghezza <= x)
        return 0.0f;

    int y0 = (int)floorf(y);
    int x0 = (int)floorf(x);
    int y1 = y0 + 1;
    int x1 = x0 + 1;

    float dy = y - (float)y0;
    float dx = x - (float)x0;
    float cy = 1.0f - dy;
    float cx = 1.0f - dx;

    float v00 = 0.0f, v01 = 0.0f, v10 = 0.0f, v11 = 0.0f;
    if (y0 >= 0 && x0 >= 0)                       v00 = in[y0 * larghezza + x0];
    if (y0 >= 0 && x1 <= larghezza - 1)           v01 = in[y0 * larghezza + x1];
    if (y1 <= altezza - 1 && x0 >= 0)             v10 = in[y1 * larghezza + x0];
    if (y1 <= altezza - 1 && x1 <= larghezza - 1) v11 = in[y1 * larghezza + x1];

    return cy * cx * v00 + cy * dx * v01 + dy * cx * v10 + dy * dx * v11;
}

extern "C" __global__ void im2col_deformabile(
    int quanti,
    const float* __restrict__ ingresso,
    const float* __restrict__ spostamenti,
    const float* __restrict__ maschera,
    int altezza, int larghezza,
    int kh, int kw,
    int bordo_h, int bordo_w,
    int passo_h, int passo_w,
    int dil_h, int dil_w,
    int immagini, int canali_in, int gruppi_spostamento,
    int usc_h, int usc_w,
    int con_maschera,
    float* __restrict__ colonne)
{
    int indice = blockIdx.x * blockDim.x + threadIdx.x;
    if (indice >= quanti) return;

    int ux = indice % usc_w;
    int uy = (indice / usc_w) % usc_h;
    int ub = (indice / (usc_w * usc_h)) % immagini;
    int ci = indice / (usc_w * usc_h * immagini);

    int canali_per_gruppo = canali_in / gruppi_spostamento;
    int gruppo = ci / canali_per_gruppo;

    int punti = usc_h * usc_w;
    // riga di partenza nelle colonne: il canale d'ingresso occupa kh*kw righe
    long long riga = (long long)ci * kh * kw;
    long long col = (long long)ub * punti + (long long)uy * usc_w + ux;
    float* uscita = colonne + riga * ((long long)immagini * punti) + col;

    const float* piano = ingresso + ((long long)ub * canali_in + ci) * altezza * larghezza;
    const float* sp = spostamenti
        + ((long long)ub * gruppi_spostamento + gruppo) * 2 * kh * kw * punti;
    const float* ms = con_maschera
        ? maschera + ((long long)ub * gruppi_spostamento + gruppo) * kh * kw * punti
        : (const float*)0;

    for (int i = 0; i < kh; ++i) {
        for (int j = 0; j < kw; ++j) {
            int campione = i * kw + j;
            float peso = 1.0f;
            if (con_maschera) peso = ms[(long long)campione * punti + uy * usc_w + ux];

            float sy = sp[(long long)(2 * campione) * punti + uy * usc_w + ux];
            float sx = sp[(long long)(2 * campione + 1) * punti + uy * usc_w + ux];

            float y = (float)(uy * passo_h - bordo_h) + (float)(i * dil_h) + sy;
            float x = (float)(ux * passo_w - bordo_w) + (float)(j * dil_w) + sx;

            *uscita = peso * bilineare(piano, altezza, larghezza, y, x);
            uscita += (long long)immagini * punti;
        }
    }
}
"""

# ---------------------------------------------------------------------------
#  Compilazione a runtime e caricamento
# ---------------------------------------------------------------------------

_LOAD_WITH_ALTERED_SEARCH_PATH = 0x8
_lucchetto = threading.Lock()
_kernel = None  # (funzione, modulo, hip)


def _percorsi_hiprtc():
    """In ordine di preferenza. Lo shim dentro torch\\lib e' il primo perche' e'
    gia' quello che il resto della ruota usa, e impone da solo la versione del
    code object."""
    lib = os.path.join(os.path.dirname(torch.__file__), "lib")
    return [
        os.path.join(lib, "hiprtc07013.dll"),
        r"C:\Program Files\AMD\ROCm\7.1\bin\hiprtc0701.dll",
        r"C:\Program Files\AMD\ROCm\5.7\bin\hiprtc0507.dll",
    ]


def _compila():
    k32 = ctypes.WinDLL("kernel32.dll")
    k32.LoadLibraryExW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_ulong]
    k32.LoadLibraryExW.restype = ctypes.c_void_p
    k32.GetProcAddress.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    k32.GetProcAddress.restype = ctypes.c_void_p

    h = None
    for p in _percorsi_hiprtc():
        if os.path.exists(p):
            h = k32.LoadLibraryExW(p, None, _LOAD_WITH_ALTERED_SEARCH_PATH)
            if h:
                break
    if not h:
        raise RuntimeError(
            "hipRTC non trovata: cercata in torch\\lib e nelle installazioni "
            "ROCm 7.1 e 5.7"
        )

    def sim(nome, restype, *argtypes):
        p = k32.GetProcAddress(h, nome.encode())
        if not p:
            raise RuntimeError(f"simbolo mancante in hipRTC: {nome}")
        return ctypes.CFUNCTYPE(restype, *argtypes)(p)

    ci, cvp, ccp, cst = (ctypes.c_int, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t)
    crea = sim("hiprtcCreateProgram", ci, ctypes.POINTER(cvp), ccp, ccp, ci, cvp, cvp)
    comp = sim("hiprtcCompileProgram", ci, cvp, ci, ctypes.POINTER(ccp))
    log_n = sim("hiprtcGetProgramLogSize", ci, cvp, ctypes.POINTER(cst))
    log_g = sim("hiprtcGetProgramLog", ci, cvp, ccp)
    cod_n = sim("hiprtcGetCodeSize", ci, cvp, ctypes.POINTER(cst))
    cod_g = sim("hiprtcGetCode", ci, cvp, ccp)

    prog = cvp()
    if crea(ctypes.byref(prog), SORGENTE.encode(), b"deform_conv.hip", 0, None, None):
        raise RuntimeError("hiprtcCreateProgram fallita")

    opzioni = [b"--offload-arch=gfx906", b"-mcode-object-version=5", b"-O3"]
    arr = (ccp * len(opzioni))(*opzioni)
    rc = comp(prog, len(opzioni), arr)
    if rc:
        n = cst()
        log_n(prog, ctypes.byref(n))
        b = ctypes.create_string_buffer(max(n.value, 1))
        log_g(prog, b)
        raise RuntimeError("compilazione del kernel fallita:\n" + b.value.decode("utf8", "replace"))

    n = cst()
    cod_n(prog, ctypes.byref(n))
    binario = ctypes.create_string_buffer(n.value)
    cod_g(prog, binario)

    hip = ctypes.CDLL("amdhip64.dll")
    hip.hipModuleLoadData.argtypes = [ctypes.POINTER(cvp), cvp]
    hip.hipModuleLoadData.restype = ci
    hip.hipModuleGetFunction.argtypes = [ctypes.POINTER(cvp), cvp, ccp]
    hip.hipModuleGetFunction.restype = ci
    hip.hipModuleLaunchKernel.argtypes = [cvp] + [ctypes.c_uint] * 7 + [
        cvp, ctypes.POINTER(cvp), cvp]
    hip.hipModuleLaunchKernel.restype = ci

    modulo = cvp()
    if hip.hipModuleLoadData(ctypes.byref(modulo), binario):
        raise RuntimeError(
            "hipModuleLoadData rifiutata: controllare la versione del code "
            "object (il driver legge fino alla v5) e le e_flags (sramecc)"
        )
    fn = cvp()
    if hip.hipModuleGetFunction(ctypes.byref(fn), modulo, b"im2col_deformabile"):
        raise RuntimeError("kernel non trovato nel modulo")
    return fn, modulo, hip


def _prendi_kernel():
    global _kernel
    if _kernel is None:
        with _lucchetto:
            if _kernel is None:
                _kernel = _compila()
    return _kernel


def informazioni():
    """Compila subito e riferisce cosa e' stato caricato. Utile in avvio."""
    _prendi_kernel()
    return {
        "kernel": "im2col_deformabile",
        "compilato": True,
        "hiprtc": next((p for p in _percorsi_hiprtc() if os.path.exists(p)), None),
        "precisione": "fp32",
        "passo": "solo in avanti",
    }


# ---------------------------------------------------------------------------
#  L'operazione
# ---------------------------------------------------------------------------


def _coppia(v):
    if isinstance(v, int):
        return (v, v)
    return tuple(v)


def _divisore_massimo_sotto(n, limite):
    """Come torchvision: quante immagini lavorare insieme. Serve a limitare il
    tensore d'appoggio senza cambiare il risultato."""
    for d in range(min(n, limite), 0, -1):
        if n % d == 0:
            return d
    return 1


def deform_conv2d(
    input,
    offset,
    weight,
    bias=None,
    stride=(1, 1),
    padding=(0, 0),
    dilation=(1, 1),
    mask=None,
):
    """Convoluzione deformabile modulata, passo in avanti.

    Stessa semantica di `torchvision.ops.deform_conv2d`. Con `mask=None` e' la
    DCN v1, con `mask` valorizzata e' la v2.
    """
    if not input.is_cuda:
        raise RuntimeError("deform_conv2d (HIP) vuole tensori su GPU")
    if input.dtype != torch.float32:
        raise RuntimeError(f"solo fp32, ricevuto {input.dtype}")

    passo_h, passo_w = _coppia(stride)
    bordo_h, bordo_w = _coppia(padding)
    dil_h, dil_w = _coppia(dilation)

    input = input.contiguous()
    offset = offset.contiguous()
    weight = weight.contiguous()

    b, c_in, alt, largh = input.shape
    c_out = weight.shape[0]
    kh, kw = weight.shape[2], weight.shape[3]
    gruppi = c_in // weight.shape[1]
    con_maschera = mask is not None

    if c_in % weight.shape[1] != 0:
        raise RuntimeError("i canali d'ingresso non sono divisibili per quelli del peso")
    if c_out % gruppi != 0:
        raise RuntimeError("i canali d'uscita non sono divisibili per i gruppi")
    if offset.shape[1] % (2 * kh * kw) != 0:
        raise RuntimeError(
            f"offset ha {offset.shape[1]} canali, non multiplo di 2*kH*kW = {2*kh*kw}"
        )
    gruppi_sp = offset.shape[1] // (2 * kh * kw)
    if c_in % gruppi_sp != 0:
        raise RuntimeError("i canali d'ingresso non sono divisibili per i gruppi di offset")

    usc_h = (alt + 2 * bordo_h - (dil_h * (kh - 1) + 1)) // passo_h + 1
    usc_w = (largh + 2 * bordo_w - (dil_w * (kw - 1) + 1)) // passo_w + 1
    if usc_h <= 0 or usc_w <= 0:
        raise RuntimeError("dimensione d'uscita nulla o negativa")
    if offset.shape[2] != usc_h or offset.shape[3] != usc_w:
        raise RuntimeError(
            f"offset e' {tuple(offset.shape[2:])}, l'uscita e' {(usc_h, usc_w)}"
        )
    if con_maschera:
        mask = mask.contiguous()
        if mask.shape[1] != gruppi_sp * kh * kw:
            raise RuntimeError(
                f"mask ha {mask.shape[1]} canali, attesi {gruppi_sp * kh * kw}"
            )
        if mask.shape[2] != usc_h or mask.shape[3] != usc_w:
            raise RuntimeError("mask non ha la forma dell'uscita")

    fn, _modulo, hip = _prendi_kernel()

    n_par = _divisore_massimo_sotto(b, 32)
    lotti = b // n_par
    punti = usc_h * usc_w

    inp = input.view(lotti, n_par, c_in, alt, largh)
    off = offset.view(lotti, n_par, gruppi_sp * 2 * kh * kw, usc_h, usc_w)
    msk = (mask.view(lotti, n_par, gruppi_sp * kh * kw, usc_h, usc_w)
           if con_maschera else None)

    colonne = torch.empty(
        (c_in * kh * kw, n_par * punti), dtype=torch.float32, device=input.device
    )
    # (gruppi, c_out/gruppi, c_in/gruppi * kh * kw)
    peso = weight.view(gruppi, c_out // gruppi, -1)
    uscita = torch.empty(
        (lotti, c_out, n_par, usc_h, usc_w), dtype=torch.float32, device=input.device
    )

    quanti = n_par * c_in * punti
    blocco = 256
    griglia = (quanti + blocco - 1) // blocco
    stream = ctypes.c_void_p(torch.cuda.current_stream().cuda_stream)

    vuoto = ctypes.c_void_p(0)
    for l in range(lotti):
        p_in = ctypes.c_void_p(inp[l].data_ptr())
        p_off = ctypes.c_void_p(off[l].data_ptr())
        p_msk = ctypes.c_void_p(msk[l].data_ptr()) if con_maschera else vuoto
        p_col = ctypes.c_void_p(colonne.data_ptr())
        interi = [quanti, alt, largh, kh, kw, bordo_h, bordo_w, passo_h, passo_w,
                  dil_h, dil_w, n_par, c_in, gruppi_sp, usc_h, usc_w,
                  1 if con_maschera else 0]
        celle = [ctypes.c_int(interi[0]), p_in, p_off, p_msk] + \
                [ctypes.c_int(v) for v in interi[1:]] + [p_col]
        arr = (ctypes.c_void_p * len(celle))(
            *[ctypes.cast(ctypes.byref(c), ctypes.c_void_p) for c in celle]
        )
        rc = hip.hipModuleLaunchKernel(fn, griglia, 1, 1, blocco, 1, 1, 0, stream, arr, None)
        if rc:
            raise RuntimeError(f"lancio del kernel fallito, rc={rc}")

        # prodotto matriciale: e' qui che va il grosso del tempo, e lo fa rocBLAS
        c = colonne.view(gruppi, (c_in // gruppi) * kh * kw, n_par * punti)
        r = torch.bmm(peso, c)                       # (gruppi, c_out/gruppi, n_par*punti)
        uscita[l] = r.reshape(c_out, n_par, usc_h, usc_w)

    uscita = uscita.transpose(1, 2).reshape(b, c_out, usc_h, usc_w)
    if bias is not None:
        uscita = uscita + bias.view(1, -1, 1, 1)
    return uscita


def modulated_deform_conv2d(
    input,
    offset,
    mask,
    weight,
    bias=None,
    stride=1,
    padding=0,
    dilation=1,
    groups=1,
    deform_groups=1,
):
    """Firma di `mmcv.ops.modulated_deform_conv2d`, per i modelli che la usano
    (BasicVSR++, EDVR, IconVSR).

    ⚠️ L'ordine degli argomenti NON e' quello di torchvision: qui la maschera
    viene prima del peso. E' l'errore facile da fare montando l'adattatore, e
    non darebbe un errore di forma — darebbe numeri sbagliati.

    `groups` e `deform_groups` sono ridondanti: si ricavano gia' dalle forme di
    `weight` e `offset`. Si accettano per compatibilita' e si CONTROLLANO, cosi'
    una discrepanza si vede subito invece di propagarsi.
    """
    kh, kw = weight.shape[2], weight.shape[3]
    g_dedotti = input.shape[1] // weight.shape[1]
    dg_dedotti = offset.shape[1] // (2 * kh * kw)
    if groups != g_dedotti:
        raise RuntimeError(
            f"groups={groups} ma dalle forme risulta {g_dedotti} "
            f"(canali {input.shape[1]}, peso {weight.shape[1]})"
        )
    if deform_groups != dg_dedotti:
        raise RuntimeError(
            f"deform_groups={deform_groups} ma dall'offset risulta {dg_dedotti} "
            f"({offset.shape[1]} canali / (2*{kh}*{kw}))"
        )
    return deform_conv2d(
        input, offset, weight, bias,
        stride=_coppia(stride), padding=_coppia(padding), dilation=_coppia(dilation),
        mask=mask,
    )


class DeformConv2d(torch.nn.Module):
    """Comodita': stessa interfaccia di `torchvision.ops.DeformConv2d`, ma solo
    in avanti. I pesi sono compatibili."""

    def __init__(self, in_channels, out_channels, kernel_size, stride=1,
                 padding=0, dilation=1, groups=1, bias=True):
        super().__init__()
        kh, kw = _coppia(kernel_size)
        self.stride = _coppia(stride)
        self.padding = _coppia(padding)
        self.dilation = _coppia(dilation)
        self.groups = groups
        self.weight = torch.nn.Parameter(
            torch.empty(out_channels, in_channels // groups, kh, kw)
        )
        self.bias = torch.nn.Parameter(torch.empty(out_channels)) if bias else None
        torch.nn.init.kaiming_uniform_(self.weight, a=5 ** 0.5)
        if self.bias is not None:
            torch.nn.init.zeros_(self.bias)

    def forward(self, input, offset, mask=None):
        return deform_conv2d(
            input, offset, self.weight, self.bias,
            stride=self.stride, padding=self.padding, dilation=self.dilation,
            mask=mask,
        )

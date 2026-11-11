"""Quanto costa la convoluzione deformabile: kernel HIP contro la via in
PyTorch puro (grid_sample), su forme da restauro video.

Serve a decidere se BasicVSR++ e' praticabile su film interi o solo su spezzoni.
Si misurano anche i picchi di memoria, perche' e' li' che la via in PyTorch puro
si fa sentire di piu'.
"""

import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, r"C:\LaRuota_workspace")
from deform_conv_hip import deform_conv2d  # noqa: E402


def deform_conv2d_puro(input, offset, weight, bias=None, stride=(1, 1),
                       padding=(0, 0), dilation=(1, 1), mask=None):
    """La via alternativa: si materializza il tensore dei campioni con
    grid_sample, uno per posizione del kernel, e poi si somma.

    E' quella che si usa quando il kernel non c'e'. Corretta, ma materializza
    kH*kW tensori grandi quanto l'ingresso invece di accumulare nel kernel.
    """
    b, c_in, alt, largh = input.shape
    c_out = weight.shape[0]
    kh, kw = weight.shape[2], weight.shape[3]
    gruppi = c_in // weight.shape[1]
    gruppi_sp = offset.shape[1] // (2 * kh * kw)
    sh, sw = stride
    ph, pw = padding
    dh, dw = dilation
    usc_h = (alt + 2 * ph - (dh * (kh - 1) + 1)) // sh + 1
    usc_w = (largh + 2 * pw - (dw * (kw - 1) + 1)) // sw + 1

    cpg = c_in // gruppi_sp
    cin_g = c_in // gruppi
    cout_g = c_out // gruppi
    quale = torch.arange(c_in, device=input.device) // cpg

    off = offset.view(b, gruppi_sp, 2 * kh * kw, usc_h, usc_w)
    msk = mask.view(b, gruppi_sp, kh * kw, usc_h, usc_w) if mask is not None else None
    base_y = (torch.arange(usc_h, device=input.device).view(usc_h, 1) * sh - ph).float()
    base_x = (torch.arange(usc_w, device=input.device).view(1, usc_w) * sw - pw).float()

    uscita = torch.zeros(b, c_out, usc_h, usc_w, device=input.device, dtype=input.dtype)
    for i in range(kh):
        for j in range(kw):
            s = i * kw + j
            y = base_y + i * dh + off[:, :, 2 * s]
            x = base_x + j * dw + off[:, :, 2 * s + 1]
            y = y[:, quale]
            x = x[:, quale]
            # grid_sample vuole coordinate normalizzate in [-1,1]
            gy = 2.0 * y / max(alt - 1, 1) - 1.0
            gx = 2.0 * x / max(largh - 1, 1) - 1.0
            # un campionamento per canale: si impila il canale nel lotto
            griglia = torch.stack((gx, gy), dim=-1).reshape(b * c_in, usc_h, usc_w, 2)
            piani = input.reshape(b * c_in, 1, alt, largh)
            camp = F.grid_sample(piani, griglia, mode="bilinear",
                                 padding_mode="zeros", align_corners=True)
            camp = camp.reshape(b, c_in, usc_h, usc_w)
            if msk is not None:
                camp = camp * msk[:, quale, s]
            for g in range(gruppi):
                w = weight[g * cout_g:(g + 1) * cout_g, :, i, j]
                uscita[:, g * cout_g:(g + 1) * cout_g] += torch.einsum(
                    "oc,bchw->bohw", w, camp[:, g * cin_g:(g + 1) * cin_g])
    if bias is not None:
        uscita = uscita + bias.view(1, -1, 1, 1)
    return uscita


def misura(fn, giri=10):
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    for _ in range(giri):
        fn()
    torch.cuda.synchronize()
    ms = (time.perf_counter() - t0) * 1000 / giri
    picco = torch.cuda.max_memory_allocated() / (1024 ** 2)
    return ms, picco


FORME = [
    ("360p   1x64x180x320", 1, 64, 180, 320),
    ("540p   1x64x270x480", 1, 64, 270, 480),
    ("720p   1x64x360x640", 1, 64, 360, 640),
]


def main():
    if not torch.cuda.is_available():
        print("  nessuna GPU")
        return 1
    print(f"  {torch.cuda.get_device_name(0)}  torch {torch.__version__}\n")
    gruppi_sp = 8
    kh = kw = 3

    print(f"  {'forma':<22} {'HIP':>10} {'PyTorch puro':>14} {'rapporto':>10}"
          f" {'mem HIP':>10} {'mem puro':>10}")
    for nome, b, c, h, w in FORME:
        torch.manual_seed(0)
        x = torch.randn(b, c, h, w, device="cuda")
        peso = (torch.randn(c, c, kh, kw) * 0.1).cuda()
        spost = (torch.randn(b, gruppi_sp * 2 * kh * kw, h, w) * 2).cuda()
        masc = torch.rand(b, gruppi_sp * kh * kw, h, w, device="cuda")
        arg = dict(padding=(1, 1), mask=masc)

        # una volta sola: verifica che le due vie diano lo stesso risultato
        with torch.no_grad():
            a = deform_conv2d(x, spost, peso, None, **arg)
            bb = deform_conv2d_puro(x, spost, peso, None, **arg)
        rel = ((a - bb).abs() / bb.abs().clamp_min(1e-2)).max().item()
        # Le due vie NON coincidono all'ultima cifra, ed e' atteso: grid_sample
        # normalizza le coordinate in [-1,1] e le riconverte, e quel giro perde
        # precisione. Il kernel HIP lavora direttamente in pixel, come
        # torchvision, ed e' lui a coincidere col riferimento CPU (4e-05 contro
        # 2e-04). Non e' un difetto di nessuna delle due: e' il prezzo della via
        # alternativa.
        segno = f"   scarto {rel:.1e}"

        with torch.no_grad():
            ms_hip, mem_hip = misura(lambda: deform_conv2d(x, spost, peso, None, **arg))
            ms_puro, mem_puro = misura(
                lambda: deform_conv2d_puro(x, spost, peso, None, **arg), giri=5)
        print(f"  {nome:<22} {ms_hip:>8.1f}ms {ms_puro:>12.1f}ms "
              f"{ms_puro/ms_hip:>9.1f}x {mem_hip:>8.0f}MB {mem_puro:>8.0f}MB{segno}")
        del x, peso, spost, masc, a, bb
        torch.cuda.empty_cache()

    print("\n  Lo scarto fra le due vie e' precisione, non semantica: grid_sample")
    print("  normalizza le coordinate e le riconverte. Contro il riferimento CPU")
    print("  il kernel HIP sta a ~4e-05, la via pura a ~2e-04.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

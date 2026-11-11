"""Banco per la convoluzione deformabile modulata su LA RUOTA.

Confronta `deform_conv_hip.deform_conv2d` (kernel HIP) con un riferimento
scritto in PyTorch puro su CPU, **indipendente** dal kernel: se sbagliano
entrambi allo stesso modo non e' un caso fortunato, e' un errore di
comprensione della semantica, e si vedrebbe altrove.

Vale la regola della guida: i kernel scelgono per velocita', non per
correttezza. Ogni forma nuova va confrontata con la CPU almeno una volta.
"""

import sys
import time

import torch

sys.path.insert(0, r"C:\LaRuota_workspace")
from deform_conv_hip import deform_conv2d, informazioni  # noqa: E402


# ---------------------------------------------------------------------------
#  Riferimento in PyTorch puro. Lento e ovvio: e' il suo mestiere.
# ---------------------------------------------------------------------------
def riferimento(input, offset, weight, bias=None, stride=(1, 1), padding=(0, 0),
                dilation=(1, 1), mask=None):
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

    cpg = c_in // gruppi_sp          # canali per gruppo di spostamento
    cin_g = c_in // gruppi           # canali per gruppo di convoluzione
    cout_g = c_out // gruppi
    di_quale_gruppo = torch.arange(c_in) // cpg   # (c_in,)

    off = offset.view(b, gruppi_sp, 2 * kh * kw, usc_h, usc_w)
    msk = mask.view(b, gruppi_sp, kh * kw, usc_h, usc_w) if mask is not None else None

    base_y = (torch.arange(usc_h).view(usc_h, 1) * sh - ph).float()
    base_x = (torch.arange(usc_w).view(1, usc_w) * sw - pw).float()

    uscita = torch.zeros(b, c_out, usc_h, usc_w, dtype=input.dtype)

    for i in range(kh):
        for j in range(kw):
            s = i * kw + j
            # posizione di campionamento per ogni gruppo: (b, gruppi_sp, h, w)
            y = base_y + i * dh + off[:, :, 2 * s]
            x = base_x + j * dw + off[:, :, 2 * s + 1]
            # e per ogni canale, secondo il suo gruppo: (b, c_in, h, w)
            y = y[:, di_quale_gruppo]
            x = x[:, di_quale_gruppo]

            y0 = torch.floor(y)
            x0 = torch.floor(x)
            dy = y - y0
            dx = x - x0
            y0 = y0.long()
            x0 = x0.long()

            def prendi(yy, xx):
                """Un angolo dell'interpolazione. Fuori dal bordo vale ZERO —
                non replica: e' la convenzione di torchvision."""
                dentro = (yy >= 0) & (yy < alt) & (xx >= 0) & (xx < largh)
                yc = yy.clamp(0, alt - 1)
                xc = xx.clamp(0, largh - 1)
                piatto = (yc * largh + xc).reshape(b, c_in, -1)
                v = torch.gather(input.reshape(b, c_in, -1), 2, piatto)
                v = v.reshape(b, c_in, usc_h, usc_w)
                return torch.where(dentro, v, torch.zeros_like(v))

            campione = (
                (1 - dy) * (1 - dx) * prendi(y0, x0)
                + (1 - dy) * dx * prendi(y0, x0 + 1)
                + dy * (1 - dx) * prendi(y0 + 1, x0)
                + dy * dx * prendi(y0 + 1, x0 + 1)
            )
            if msk is not None:
                campione = campione * msk[:, di_quale_gruppo, s]

            for g in range(gruppi):
                w = weight[g * cout_g:(g + 1) * cout_g, :, i, j]      # (cout_g, cin_g)
                c = campione[:, g * cin_g:(g + 1) * cin_g]            # (b, cin_g, h, w)
                uscita[:, g * cout_g:(g + 1) * cout_g] += torch.einsum("oc,bchw->bohw", w, c)

    if bias is not None:
        uscita = uscita + bias.view(1, -1, 1, 1)
    return uscita


# ---------------------------------------------------------------------------
#  I casi
# ---------------------------------------------------------------------------
esiti = []


def caso(nome, b, c_in, c_out, alt, largh, kh, kw, *, stride=(1, 1), padding=(1, 1),
         dilation=(1, 1), gruppi=1, gruppi_sp=1, con_maschera=True,
         scala_spostamenti=2.0, seme=0):
    torch.manual_seed(seme)
    sh, sw = stride
    ph, pw = padding
    dh, dw = dilation
    usc_h = (alt + 2 * ph - (dh * (kh - 1) + 1)) // sh + 1
    usc_w = (largh + 2 * pw - (dw * (kw - 1) + 1)) // sw + 1

    x = torch.randn(b, c_in, alt, largh)
    peso = torch.randn(c_out, c_in // gruppi, kh, kw) * 0.1
    polar = torch.randn(c_out) * 0.1
    spost = torch.randn(b, gruppi_sp * 2 * kh * kw, usc_h, usc_w) * scala_spostamenti
    masc = torch.rand(b, gruppi_sp * kh * kw, usc_h, usc_w) if con_maschera else None

    args = dict(stride=stride, padding=padding, dilation=dilation)
    atteso = riferimento(x, spost, peso, polar, mask=masc, **args)
    try:
        ott = deform_conv2d(
            x.cuda(), spost.cuda(), peso.cuda(), polar.cuda(),
            mask=masc.cuda() if masc is not None else None, **args
        ).cpu()
    except Exception as e:
        print(f"  *** {nome:<44} {type(e).__name__}: {str(e)[:70]}")
        esiti.append((nome, False))
        return

    if ott.shape != atteso.shape:
        print(f"  *** {nome:<44} forma {tuple(ott.shape)}, attesa {tuple(atteso.shape)}")
        esiti.append((nome, False))
        return

    # pavimento al denominatore: dove il riferimento e' quasi zero un rapporto
    # esploderebbe senza che ci sia niente di sbagliato
    rel = ((ott - atteso).abs() / atteso.abs().clamp_min(1e-2)).max().item()
    ok = rel < 1e-4
    esiti.append((nome, ok))
    print(f"  {'OK  ' if ok else '*** '}{nome:<44} relativo {rel:.2e}")


def main():
    if not torch.cuda.is_available():
        print("  nessuna GPU visibile")
        return 1
    print(f"  {torch.cuda.get_device_name(0)}  torch {torch.__version__}")
    try:
        info = informazioni()
    except Exception as e:
        print(f"  *** compilazione del kernel fallita: {e}")
        return 1
    print(f"  kernel compilato da: {info['hiprtc']}\n")

    print("--- i sei casi richiesti")
    caso("base, spostamenti frazionari", 2, 16, 32, 64, 64, 3, 3)
    caso("spostamenti fuori dai bordi", 2, 8, 8, 16, 16, 3, 3, scala_spostamenti=12.0)
    caso("senza maschera (v1)", 2, 8, 16, 32, 32, 3, 3, con_maschera=False)
    caso("passo 2", 2, 8, 16, 32, 32, 3, 3, stride=(2, 2))
    caso("dilatazione 2", 2, 8, 16, 32, 32, 3, 3, dilation=(2, 2), padding=(2, 2))
    caso("16 gruppi di spostamento", 1, 16, 16, 32, 32, 3, 3, gruppi_sp=16)
    caso("gruppi 4 + spostamenti 4", 2, 16, 32, 24, 24, 3, 3, gruppi=4, gruppi_sp=4)
    caso("dimensioni non multiple di 16", 1, 6, 10, 23, 17, 3, 3)

    print("\n--- casi di contorno")
    caso("kernel 1x1, senza bordo", 2, 8, 8, 16, 16, 1, 1, padding=(0, 0))
    caso("kernel 5x5, bordo 2", 1, 4, 8, 20, 20, 5, 5, padding=(2, 2))
    caso("kernel rettangolare 3x5", 1, 4, 8, 20, 20, 3, 5, padding=(1, 2))
    caso("passo 2 e dilatazione 2", 1, 8, 8, 32, 32, 3, 3,
         stride=(2, 2), dilation=(2, 2), padding=(2, 2))
    caso("un solo canale", 1, 1, 1, 12, 12, 3, 3)
    caso("spostamenti nulli = conv normale", 2, 8, 16, 24, 24, 3, 3,
         scala_spostamenti=0.0, con_maschera=False)

    passati = sum(1 for _, ok in esiti if ok)
    print(f"\n  ESITO: {passati}/{len(esiti)} prove superate")
    if passati != len(esiti):
        print("  fallite:", ", ".join(n for n, ok in esiti if not ok))
        return 1

    # --- controllo incrociato: spostamenti nulli devono dare conv2d normale
    print("\n--- controprova indipendente: spostamenti nulli contro conv2d")
    torch.manual_seed(1)
    x = torch.randn(2, 8, 24, 24)
    peso = torch.randn(16, 8, 3, 3) * 0.1
    polar = torch.randn(16) * 0.1
    spost = torch.zeros(2, 2 * 9, 24, 24)
    a = torch.nn.functional.conv2d(x, peso, polar, padding=1)
    b = deform_conv2d(x.cuda(), spost.cuda(), peso.cuda(), polar.cuda(),
                      padding=(1, 1)).cpu()
    rel = ((b - a).abs() / a.abs().clamp_min(1e-2)).max().item()
    print(f"  {'OK  ' if rel < 1e-4 else '*** '}contro torch.conv2d"
          f"{'':<26} relativo {rel:.2e}")
    if rel >= 1e-4:
        return 1

    # --- quanto costa
    print("\n--- tempi, forma tipica di un allineamento video")
    torch.manual_seed(2)
    b_, c_, h_, w_ = 1, 64, 180, 320
    x = torch.randn(b_, c_, h_, w_, device="cuda")
    peso = (torch.randn(64, 64 // 8, 3, 3) * 0.1).cuda()
    spost = (torch.randn(b_, 8 * 2 * 9, h_, w_) * 2).cuda()
    masc = torch.rand(b_, 8 * 9, h_, w_, device="cuda")
    for _ in range(3):
        deform_conv2d(x, spost, peso, None, padding=(1, 1), mask=masc)
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    giri = 10
    for _ in range(giri):
        deform_conv2d(x, spost, peso, None, padding=(1, 1), mask=masc)
    torch.cuda.synchronize()
    ms = (time.perf_counter() - t0) * 1000 / giri
    print(f"  {b_}x{c_}x{h_}x{w_}, 8 gruppi, kernel 3x3: {ms:.1f} ms per chiamata")

    # --- l'adattatore mmcv deve dare lo STESSO risultato di quello torchvision
    print("\n--- adattatore mmcv (l'ordine degli argomenti e' diverso)")
    from deform_conv_hip import modulated_deform_conv2d
    torch.manual_seed(3)
    x = torch.randn(1, 16, 24, 24).cuda()
    peso = (torch.randn(16, 16 // 2, 3, 3) * 0.1).cuda()
    polar = (torch.randn(16) * 0.1).cuda()
    spost = (torch.randn(1, 4 * 2 * 9, 24, 24) * 2).cuda()
    masc = torch.rand(1, 4 * 9, 24, 24, device="cuda")
    a = deform_conv2d(x, spost, peso, polar, padding=(1, 1), mask=masc)
    b = modulated_deform_conv2d(x, spost, masc, peso, polar, stride=1, padding=1,
                                dilation=1, groups=2, deform_groups=4)
    diff = (a - b).abs().max().item()
    print(f"  {'OK  ' if diff == 0 else '*** '}mmcv contro torchvision"
          f"{'':<21} scarto {diff:.2e}")
    if diff != 0:
        return 1
    # e i controlli di coerenza devono scattare, non passare in silenzio
    try:
        modulated_deform_conv2d(x, spost, masc, peso, polar, groups=1, deform_groups=4)
        print("  *** il controllo su groups NON e' scattato")
        return 1
    except RuntimeError:
        print("  OK  il controllo su un groups sbagliato scatta")

    print("\n  ESITO COMPLESSIVO: TUTTO CORRETTO")
    return 0


if __name__ == "__main__":
    sys.exit(main())

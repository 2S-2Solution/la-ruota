"""Perche' la via con grid_sample non coincide con la convenzione di torchvision.

Sospetto: il trattamento del bordo. Si isola confrontando le due vie con
spostamenti che restano DENTRO e con spostamenti che escono.
"""
import sys

import torch

sys.path.insert(0, r"C:\LaRuota_workspace")
from deform_conv_hip import deform_conv2d  # noqa: E402
from confronto_deform_conv import deform_conv2d_puro  # noqa: E402
from prova_deform_conv import riferimento  # noqa: E402


def prova(nome, scala, bordo=1):
    torch.manual_seed(0)
    b, c, h, w = 1, 4, 16, 16
    x = torch.randn(b, c, h, w)
    peso = torch.randn(8, c, 3, 3) * 0.1
    spost = torch.randn(b, 2 * 9, h, w) * scala
    arg = dict(padding=(bordo, bordo))

    rif = riferimento(x, spost, peso, None, **arg)
    hip = deform_conv2d(x.cuda(), spost.cuda(), peso.cuda(), None, **arg).cpu()
    puro = deform_conv2d_puro(x.cuda(), spost.cuda(), peso.cuda(), None, **arg).cpu()

    def rel(a, b):
        return ((a - b).abs() / b.abs().clamp_min(1e-2)).max().item()

    print(f"  {nome:<34} HIP-rif {rel(hip, rif):.2e}   "
          f"puro-rif {rel(puro, rif):.2e}   puro-HIP {rel(puro, hip):.2e}")


def main():
    print("  Le tre vie a confronto. 'rif' e' il riferimento CPU che segue la\n"
          "  convenzione di torchvision (zero fuori dal bordo).\n")
    prova("spostamenti nulli", 0.0)
    prova("spostamenti piccoli (dentro)", 0.3)
    prova("spostamenti medi", 2.0)
    prova("spostamenti grandi (escono)", 12.0)
    print("\n  Se HIP coincide col riferimento e 'puro' no, la differenza sta")
    print("  nella convenzione di bordo di grid_sample, non nel kernel.")

    # dov'e' esattamente
    print("\n  --- dove differiscono, sulla mappa")
    torch.manual_seed(0)
    b, c, h, w = 1, 1, 8, 8
    x = torch.randn(b, c, h, w)
    peso = torch.ones(1, c, 3, 3)
    spost = torch.randn(b, 2 * 9, h, w) * 3.0
    hip = deform_conv2d(x.cuda(), spost.cuda(), peso.cuda(), None, padding=(1, 1)).cpu()
    puro = deform_conv2d_puro(x.cuda(), spost.cuda(), peso.cuda(), None, padding=(1, 1)).cpu()
    d = (hip - puro).abs()[0, 0]
    print(f"  scarto massimo {d.max().item():.3e}")
    ry, rx = torch.where(d > d.max() * 0.5)
    print(f"  posizioni con lo scarto piu' grande: {list(zip(ry.tolist(), rx.tolist()))[:8]}")
    print(f"  (l'uscita e' {h}x{w}: i bordi sono 0 e {h-1})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""eigh sulla GPU passa dalla CPU (MKL, deterministica). Perche' non si ripete uguale?

    python -u prova_eigh_ordine.py
"""
import torch

M = torch.randn(2000, 64, generator=torch.Generator().manual_seed(0)).cuda()


def una(sincronizza):
    S = M.t() @ M
    if sincronizza:
        torch.cuda.synchronize()
    w, v = torch.linalg.eigh(S)
    w_c, v_c = torch.linalg.eigh(S.cpu())          # la stessa cosa, fatta a mano sulla CPU
    return w.cpu(), v.cpu(), w_c, v_c, S.cpu()


for sincronizza in (False, True):
    r = [una(sincronizza) for _ in range(5)]
    d_ingresso = max((x[4] - r[0][4]).abs().max().item() for x in r)
    d_gpu = max((x[1] - r[0][1]).abs().max().item() for x in r)
    d_cpu = max((x[3] - r[0][3]).abs().max().item() for x in r)
    d_gpu_cpu = max((x[1] - x[3]).abs().max().item() for x in r)
    d_val = max((x[0] - x[2]).abs().max().item() for x in r)
    print(f"sincronizzazione prima di eigh: {sincronizza}")
    print(f"  ingresso S fra le corse             {d_ingresso:.1e}")
    print(f"  autovettori GPU fra le corse        {d_gpu:.1e}")
    print(f"  autovettori CPU fra le corse        {d_cpu:.1e}")
    print(f"  autovettori GPU contro CPU, stessa corsa {d_gpu_cpu:.1e}   autovalori {d_val:.1e}")

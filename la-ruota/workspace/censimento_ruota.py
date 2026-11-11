"""Secondo censimento della ruota: le aree che il censimento_v8 di Rocm non copre.

Ogni operazione gira su CPU e su GPU partendo dagli STESSI tensori (creati su CPU
e copiati). Dove conta, si confrontano anche i gradienti, con una perdita PESATA
(somma di f(x)*W con W casuale): con f(x).sum() il gradiente di una normalizzazione
o di una softmax e' analiticamente zero e il confronto relativo esplode.

Criterio: scarto relativo con pavimento al denominatore. Per le decomposizioni
(QR, SVD, autovettori) i fattori sono definiti a meno di segni e rotazioni, quindi
si confronta la RICOSTRUZIONE, non i fattori.

Il nome dell'operazione viene stampato PRIMA di eseguirla: se il processo muore
(un salto a zero, come i 20 export mancanti di agosto) l'ultima riga dice quale.
Uso:  python censimento_ruota.py            tutte
      python censimento_ruota.py --salta a,b   salta quelle che fanno cadere il processo
"""
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F

SOGLIA = 1e-3
SALTA = set()
if "--salta" in sys.argv:
    SALTA = set(sys.argv[sys.argv.index("--salta") + 1].split(","))

torch.manual_seed(0)
ESITI = {}


def rel(a, b):
    a = a.detach().cpu().double()
    b = b.detach().cpu().double()
    if a.is_complex() or b.is_complex():
        a, b = torch.view_as_real(a), torch.view_as_real(b)
    if a.shape != b.shape:
        return float("inf")
    if not torch.isfinite(b).all() and torch.isfinite(a).all():
        return float("nan")
    return float((a - b).abs().max() / max(float(a.abs().max()), 1e-6)) if a.numel() else 0.0


def come_lista(o):
    if torch.is_tensor(o):
        return [o]
    if isinstance(o, (tuple, list)):
        return [t for t in o if torch.is_tensor(t)]
    if hasattr(o, "_fields"):  # namedtuple di torch.linalg
        return [getattr(o, f) for f in o._fields if torch.is_tensor(getattr(o, f))]
    return []


def prova(area, nome, fn, ingressi, grad=False, soglia=SOGLIA, confronta=None):
    chiave = f"{area}/{nome}"
    if nome in SALTA:
        ESITI[chiave] = ("saltata", "fa cadere il processo")
        return
    print(f"  .. {chiave}", end="", flush=True)
    try:
        uscite, gradi = [], []
        for dev in ("cpu", "cuda"):
            xs = [x.clone().to(dev) for x in ingressi]
            if grad:
                for x in xs:
                    if x.is_floating_point():
                        x.requires_grad_(True)
            out = fn(*xs)
            outs = come_lista(out)
            uscite.append(outs)
            if grad:
                torch.manual_seed(1)
                perdita = 0
                for o in outs:
                    if o.is_floating_point() and o.requires_grad:
                        W = torch.randn(o.shape, dtype=o.dtype).to(dev)
                        perdita = perdita + (o * W).sum()
                perdita.backward()
                gradi.append([x.grad for x in xs if x.is_floating_point() and x.grad is not None])
        if confronta is not None:
            e = confronta(*uscite[0], *uscite[1])
        else:
            e = max((rel(a, b) for a, b in zip(uscite[0], uscite[1])), default=0.0)
        eg = max((rel(a, b) for a, b in zip(*gradi)), default=0.0) if grad else 0.0
        peggiore = max(e, eg)
        if peggiore != peggiore or peggiore >= soglia:
            stato = "SBAGLIATA"
        else:
            stato = "ok"
        nota = f"avanti {e:.1e}" + (f"  grad {eg:.1e}" if grad else "")
        ESITI[chiave] = (stato, nota)
        print(f"\r  {stato:9s} {chiave:42s} {nota}", flush=True)
    except Exception as exc:
        msg = f"{type(exc).__name__}: {str(exc).splitlines()[0][:70]}"
        ESITI[chiave] = ("ECCEZIONE", msg)
        print(f"\r  ECCEZIONE {chiave:42s} {msg}", flush=True)


def ricostruzione(f_ricostruisci):
    """Confronta A ricostruita da GPU con A ricostruita da CPU."""
    def c(*tutte):
        n = len(tutte) // 2
        return rel(f_ricostruisci(*tutte[:n]), f_ricostruisci(*tutte[n:]))
    return c


R = torch.randn
spd = lambda b, n: (lambda a: a @ a.mT + n * torch.eye(n))(R(b, n, n))  # simmetrica definita positiva

print(f"{torch.cuda.get_device_name(0)}  torch {torch.__version__}\n")

print("=== algebra lineare")
A1, Ab = R(32, 32), R(8, 32, 32)
B1, Bb = R(32, 4), R(8, 32, 4)
prova("linalg", "solve", torch.linalg.solve, [A1, B1], grad=True)
prova("linalg", "solve batch", torch.linalg.solve, [Ab, Bb], grad=True)
prova("linalg", "inv", torch.linalg.inv, [A1], grad=True)
prova("linalg", "inv batch", torch.linalg.inv, [Ab], grad=True)
prova("linalg", "det batch", torch.linalg.det, [Ab], grad=True)
prova("linalg", "slogdet batch", lambda a: torch.linalg.slogdet(a)[1], [Ab], grad=True)
prova("linalg", "cholesky batch", torch.linalg.cholesky, [spd(8, 32)], grad=True)
prova("linalg", "qr", torch.linalg.qr, [A1],
      confronta=ricostruzione(lambda q, r: q @ r))
prova("linalg", "qr batch", torch.linalg.qr, [Ab],
      confronta=ricostruzione(lambda q, r: q @ r))
prova("linalg", "lu_factor", lambda a: torch.linalg.lu_factor(a)[0], [A1])
prova("linalg", "lu_factor batch", lambda a: torch.linalg.lu_factor(a)[0], [Ab])
prova("linalg", "svd", lambda a: torch.linalg.svd(a, full_matrices=False), [A1],
      confronta=ricostruzione(lambda u, s, vh: u @ torch.diag_embed(s) @ vh))
prova("linalg", "svd batch", lambda a: torch.linalg.svd(a, full_matrices=False), [Ab],
      confronta=ricostruzione(lambda u, s, vh: u @ torch.diag_embed(s) @ vh))
prova("linalg", "svdvals", torch.linalg.svdvals, [Ab])
prova("linalg", "eigh batch", torch.linalg.eigh, [spd(8, 32)],
      confronta=ricostruzione(lambda w, v: v @ torch.diag_embed(w) @ v.mT))
prova("linalg", "eigvalsh", torch.linalg.eigvalsh, [spd(8, 32)])
prova("linalg", "lstsq", lambda a, b: torch.linalg.lstsq(a, b).solution, [R(64, 32), R(64, 4)])
prova("linalg", "pinv", torch.linalg.pinv, [R(32, 16)])
prova("linalg", "matrix_norm nuc", lambda a: torch.linalg.matrix_norm(a, "nuc"), [Ab])
prova("linalg", "bmm", torch.bmm, [Ab, Bb], grad=True)
prova("linalg", "baddbmm", lambda c, a, b: torch.baddbmm(c, a, b), [R(8, 32, 4), Ab, Bb], grad=True)
prova("linalg", "einsum", lambda a, b: torch.einsum("bij,bjk->bik", a, b), [Ab, Bb], grad=True)
prova("linalg", "cdist", torch.cdist, [R(64, 16), R(48, 16)], grad=True)
prova("linalg", "matmul fp16", lambda a, b: (a.half() @ b.half()).float(), [R(256, 256), R(256, 256)],
      soglia=5e-3)

print("\n=== FFT")
S = R(4, 256)
prova("fft", "fft", torch.fft.fft, [S])
prova("fft", "ifft", lambda x: torch.fft.ifft(torch.fft.fft(x)).real, [S])
prova("fft", "rfft", torch.fft.rfft, [S], grad=False)
prova("fft", "irfft", lambda x: torch.fft.irfft(torch.fft.rfft(x)), [S])
prova("fft", "fft2", torch.fft.fft2, [R(4, 32, 32)])
prova("fft", "rfftn", torch.fft.rfftn, [R(2, 16, 16, 16)])
prova("fft", "stft", lambda x: torch.stft(x, 64, return_complex=True, window=torch.hann_window(64, device=x.device)), [R(2, 1024)])

print("\n=== indicizzazione")
X = R(64, 32)
idx = torch.randint(0, 64, (128,))
prova("indici", "index_select", lambda x, i: x.index_select(0, i), [X, idx], grad=True)
prova("indici", "gather", lambda x, i: x.gather(1, i), [X, torch.randint(0, 32, (64, 8))], grad=True)
prova("indici", "scatter_add", lambda s, i: torch.zeros(64, 32, device=s.device).scatter_add(0, i, s),
      [R(16, 32), torch.randint(0, 64, (16, 32))], grad=True)
prova("indici", "scatter_reduce amax", lambda s, i: torch.zeros(64, device=s.device).scatter_reduce(0, i, s, "amax"),
      [R(256), torch.randint(0, 64, (256,))])
prova("indici", "index_add", lambda x, s, i: x.index_add(0, i, s), [X, R(128, 32), idx], grad=True)
prova("indici", "index_put accumula", lambda x, s, i: x.index_put((i,), s, accumulate=True), [X, R(128, 32), idx], grad=True)
prova("indici", "masked_select", lambda x: x.masked_select(x > 0), [X])
prova("indici", "nonzero", lambda x: torch.nonzero(x > 0.5).float(), [X])
prova("indici", "take_along_dim", lambda x, i: torch.take_along_dim(x, i, 1), [X, torch.randint(0, 32, (64, 8))], grad=True)
prova("indici", "embedding", lambda w, i: F.embedding(i, w), [R(100, 16), torch.randint(0, 100, (32, 8))], grad=True)
for modo in ("sum", "mean", "max"):
    prova("indici", f"embedding_bag {modo}",
          lambda w, i, o, m=modo: F.embedding_bag(i, w, o, mode=m),
          [R(100, 16), torch.randint(0, 100, (64,)), torch.tensor([0, 10, 25, 40])], grad=True)
prova("indici", "one_hot", lambda i: F.one_hot(i, 10).float(), [torch.randint(0, 10, (64,))])

print("\n=== ordinamenti e cumulate")
V = R(8, 512)
prova("ordina", "sort", lambda x: torch.sort(x, -1)[0], [V], grad=True)
prova("ordina", "argsort", lambda x: torch.argsort(x, -1).float(), [V])
prova("ordina", "topk", lambda x: torch.topk(x, 16, -1)[0], [V], grad=True)
prova("ordina", "kthvalue", lambda x: torch.kthvalue(x, 100, -1)[0], [V])
prova("ordina", "median", lambda x: torch.median(x, -1)[0], [V])
prova("ordina", "mode", lambda x: torch.mode(x, -1)[0], [torch.randint(0, 10, (8, 512)).float()])
prova("ordina", "unique counts", lambda x: torch.unique(x, return_counts=True)[1].float(), [torch.randint(0, 50, (4096,))])
prova("ordina", "searchsorted", lambda s, v: torch.searchsorted(s, v).float(), [torch.sort(R(256))[0], R(512)])
prova("ordina", "bucketize", lambda v, b: torch.bucketize(v, b).float(), [R(512), torch.sort(R(32))[0]])
prova("ordina", "cumsum", lambda x: torch.cumsum(x, -1), [V], grad=True)
prova("ordina", "cumprod", lambda x: torch.cumprod(x * 0.01 + 1, -1), [V], grad=True)
prova("ordina", "cummax", lambda x: torch.cummax(x, -1)[0], [V], grad=True)
prova("ordina", "logcumsumexp", lambda x: torch.logcumsumexp(x, -1), [V], grad=True)
prova("ordina", "histc", lambda x: torch.histc(x, 20, -3, 3), [R(4096)])
prova("ordina", "bincount", lambda i: torch.bincount(i).float(), [torch.randint(0, 100, (4096,))])

print("\n=== complessi e interi")
C = torch.randn(256, dtype=torch.complex64)
prova("tipi", "complex mul", lambda a, b: a * b, [C, torch.randn(256, dtype=torch.complex64)])
prova("tipi", "complex abs/angle", lambda a: torch.stack([a.abs(), a.angle()]), [C])
prova("tipi", "int64 div floor", lambda a, b: torch.div(a, b, rounding_mode="floor").float(),
      [torch.randint(-1000, 1000, (512,)), torch.randint(1, 50, (512,))])
prova("tipi", "int64 remainder", lambda a, b: torch.remainder(a, b).float(),
      [torch.randint(-1000, 1000, (512,)), torch.randint(1, 50, (512,))])
prova("tipi", "bitwise", lambda a, b: ((a & b) ^ (a | b)).float(),
      [torch.randint(0, 2 ** 30, (512,)), torch.randint(0, 2 ** 30, (512,))])
prova("tipi", "half somma", lambda x: x.half().sum(-1).float(), [R(8, 4096)], soglia=5e-3)
prova("tipi", "bfloat16 elementwise", lambda x: (x.bfloat16() * 2 + 1).float(), [R(4096)], soglia=1e-2)

print("\n=== convoluzioni: le varianti che la battuta di agosto non copriva")
prova("conv", "conv2d stride 2", lambda x, w: F.conv2d(x, w, stride=2, padding=1), [R(4, 16, 32, 32), R(32, 16, 3, 3)], grad=True)
prova("conv", "conv2d depthwise", lambda x, w: F.conv2d(x, w, padding=1, groups=32), [R(4, 32, 32, 32), R(32, 1, 3, 3)], grad=True)
prova("conv", "conv2d groups 4", lambda x, w: F.conv2d(x, w, padding=1, groups=4), [R(4, 32, 16, 16), R(64, 8, 3, 3)], grad=True)
prova("conv", "conv2d dilation 2", lambda x, w: F.conv2d(x, w, padding=2, dilation=2), [R(4, 16, 32, 32), R(32, 16, 3, 3)], grad=True)
prova("conv", "conv_transpose2d", lambda x, w: F.conv_transpose2d(x, w, stride=2, padding=1), [R(4, 32, 16, 16), R(32, 16, 4, 4)], grad=True)
prova("conv", "conv1d stride 2", lambda x, w: F.conv1d(x, w, stride=2, padding=1), [R(4, 32, 256), R(64, 32, 3)], grad=True)
prova("conv", "conv1d dilation 4", lambda x, w: F.conv1d(x, w, padding=4, dilation=4), [R(4, 32, 256), R(32, 32, 3)], grad=True)
prova("conv", "conv3d", lambda x, w: F.conv3d(x, w, padding=1), [R(2, 8, 8, 16, 16), R(16, 8, 3, 3, 3)], grad=True)
prova("conv", "conv2d fp16", lambda x, w: F.conv2d(x.half(), w.half(), padding=1).float(),
      [R(4, 16, 32, 32), R(32, 16, 3, 3)], soglia=5e-3)

print("\n=== immagini e campionamento")
I = R(2, 8, 32, 32)
for modo in ("nearest", "bilinear", "bicubic"):
    prova("immagini", f"interpolate {modo}",
          lambda x, m=modo: F.interpolate(x, scale_factor=2, mode=m, **({} if m == "nearest" else {"align_corners": False})),
          [I], grad=True)
prova("immagini", "adaptive_avg_pool2d", lambda x: F.adaptive_avg_pool2d(x, 7), [I], grad=True)
prova("immagini", "adaptive_max_pool2d", lambda x: F.adaptive_max_pool2d(x, 7), [I], grad=True)
prova("immagini", "max_pool2d + unpool", lambda x: F.max_unpool2d(*F.max_pool2d(x, 2, return_indices=True), 2), [I], grad=True)
for modo in ("reflect", "replicate", "circular"):
    prova("immagini", f"pad {modo}", lambda x, m=modo: F.pad(x, (2, 2, 2, 2), mode=m), [I], grad=True)
prova("immagini", "pixel_shuffle", lambda x: F.pixel_shuffle(x, 2), [I], grad=True)
prova("immagini", "grid_sample bicubic",
      lambda x, g: F.grid_sample(x, g, mode="bicubic", align_corners=False),
      [I, torch.rand(2, 16, 16, 2) * 2 - 1], grad=True)
prova("immagini", "unfold (im2col)", lambda x: F.unfold(x, 3, padding=1), [I], grad=True)

print("\n=== attenzione e perdite")
q = R(2, 4, 64, 32)
prova("attenzione", "sdpa", lambda q, k, v: F.scaled_dot_product_attention(q, k, v), [q, R(2, 4, 64, 32), R(2, 4, 64, 32)], grad=True)
prova("attenzione", "sdpa causale", lambda q, k, v: F.scaled_dot_product_attention(q, k, v, is_causal=True), [q, R(2, 4, 64, 32), R(2, 4, 64, 32)], grad=True)
prova("attenzione", "sdpa maschera",
      lambda q, k, v, m: F.scaled_dot_product_attention(q, k, v, attn_mask=m),
      [q, R(2, 4, 64, 32), R(2, 4, 64, 32), torch.rand(64, 64) > 0.2], grad=True)


def mha(x):
    torch.manual_seed(3)
    m = nn.MultiheadAttention(32, 4, batch_first=True).to(x.device).eval()
    return m(x, x, x, need_weights=False)[0]


prova("attenzione", "MultiheadAttention", mha, [R(4, 16, 32)], grad=True)
prova("perdite", "cross_entropy smoothing",
      lambda x, t: F.cross_entropy(x, t, label_smoothing=0.1), [R(64, 10), torch.randint(0, 10, (64,))], grad=True)
prova("perdite", "cross_entropy ignore",
      lambda x, t: F.cross_entropy(x, t, ignore_index=0), [R(64, 10), torch.randint(0, 10, (64,))], grad=True)
prova("perdite", "nll_loss 2d", lambda x, t: F.nll_loss(F.log_softmax(x, 1), t),
      [R(4, 5, 16, 16), torch.randint(0, 5, (4, 16, 16))], grad=True)
prova("perdite", "kl_div", lambda a, b: F.kl_div(F.log_softmax(a, -1), F.softmax(b, -1), reduction="batchmean"),
      [R(64, 10), R(64, 10)], grad=True)
prova("perdite", "huber", lambda a, b: F.huber_loss(a, b), [R(256), R(256)], grad=True)
prova("perdite", "cosine_similarity", lambda a, b: F.cosine_similarity(a, b), [R(64, 32), R(64, 32)], grad=True)

print("\n" + "=" * 78)
per_stato = {}
for k, (s, n) in ESITI.items():
    per_stato.setdefault(s, []).append((k, n))
print(f"  operazioni provate: {len(ESITI)}")
for s in ("ok", "SBAGLIATA", "ECCEZIONE", "saltata"):
    print(f"  {s:10s} {len(per_stato.get(s, []))}")
for s in ("SBAGLIATA", "ECCEZIONE", "saltata"):
    for k, n in per_stato.get(s, []):
        print(f"    {s:9s} {k:42s} {n}")

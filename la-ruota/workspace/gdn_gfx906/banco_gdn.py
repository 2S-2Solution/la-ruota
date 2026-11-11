"""Banco del kernel Gated DeltaNet: correttezza e tempi contro torch_chunk_gated_delta_rule.

    python banco_gdn.py correttezza
    python banco_gdn.py prestazioni

Riferimenti: la funzione di transformers così com'è (fp32 al suo interno) e una sua copia con
float64 al posto di float32 ("verità"). Il kernel passa se il suo errore contro la verità non supera
il doppio di quello del riferimento fp32 (con un pavimento di 1e-5 relativo al massimo).
"""
import inspect
import statistics
import sys
import time

TF5 = r"%USERPROFILE%\Documents\2SAI\Memoria\working\prova_tf_nuovo"
sys.path.insert(0, TF5)
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")

import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from transformers.models.qwen3_5 import modeling_qwen3_5 as mq  # noqa: E402

import gdn_gfx906 as gdn  # noqa: E402

rif32 = mq.torch_chunk_gated_delta_rule


def _rif64():
    src = inspect.getsource(mq.torch_chunk_gated_delta_rule.__wrapped__)
    src = src[src.index("def "):].replace("torch.float32", "torch.float64")
    g = dict(mq.__dict__)
    exec(src, g)
    return g["torch_chunk_gated_delta_rule"]


rif64 = _rif64()


def dati_modello(B, S, H, D, forza, dtipo, seme):
    """Come li passa Qwen3_5GatedDeltaNet: q, k, v viste di mixed_qkv (v non contigua), q e k
    ripetute da H/2 a H teste con repeat_interleave, beta = sigmoid in fp16, g in fp32."""
    gen = torch.Generator(device="cuda").manual_seed(seme)
    r = lambda *f: torch.randn(*f, device="cuda", generator=gen)
    hk = H // 2
    mixed = r(B, S, 2 * hk * D + H * D).to(dtipo)
    q, k, v = torch.split(mixed, [hk * D, hk * D, H * D], dim=-1)
    q = q.reshape(B, S, hk, D).repeat_interleave(2, dim=2)
    k = k.reshape(B, S, hk, D).repeat_interleave(2, dim=2)
    v = v.reshape(B, S, H, D)
    A = torch.rand(H, device="cuda", generator=gen) * forza
    g = -(A * F.softplus(r(B, S, H) - 2.0)).float()
    beta = torch.sigmoid(r(B, S, H).to(dtipo))
    return q, k, v, g, beta


def dati(B, S, H, D, forza, dtipo, seme):
    gen = torch.Generator(device="cuda").manual_seed(seme)
    r = lambda *f: torch.randn(*f, device="cuda", generator=gen)
    q = r(B, S, H, D).to(dtipo)
    k = r(B, S, H, D).to(dtipo)
    v = r(B, S, H, D).to(dtipo)
    # g come nel modello: -exp(A_log) * softplus(a + dt_bias), A in (0, 16)
    A = torch.rand(H, device="cuda", generator=gen) * forza
    g = -(A * F.softplus(r(B, S, H) - 2.0)).float()
    beta = torch.sigmoid(r(B, S, H)).to(dtipo)
    return q, k, v, g, beta


def errore(x, verita):
    return ((x.double() - verita).abs().max() / verita.abs().max().clamp_min(1e-30)).item()


def un_caso(nome, B, S, H, D, forza, dtipo=torch.float32, stato=False, seme=0, n_indietro=3, modello=False):
    q, k, v, g, beta = (dati_modello if modello else dati)(B, S, H, D, forza, dtipo, seme)
    s0 = torch.randn(B, H, D, D, device="cuda") * 0.1 if stato else None
    esito = True
    righe = []
    for giro in range(n_indietro):
        do = torch.randn(B, S, H, D, device="cuda", generator=torch.Generator(device="cuda").manual_seed(100 + giro))
        dsf = torch.randn(B, H, D, D, device="cuda") * 0.1 if stato else None
        uscite = {}
        for etich, fn, conv in (("kernel", gdn.chunk_gated_delta_rule, lambda x: x),
                                ("rif32", rif32, lambda x: x),
                                ("verita", rif64, lambda x: x.double())):
            xs = [conv(x.detach()).requires_grad_(True) if etich != "verita" else
                  conv(x.detach().clone()).requires_grad_(True) for x in (q, k, v, g, beta)]
            s0x = None if s0 is None else conv(s0.clone()).requires_grad_(True)
            o, sf = fn(*xs, chunk_size=64, initial_state=s0x, output_final_state=stato,
                       use_qk_l2norm_in_kernel=True)
            perdita = (o.double() * do.double()).sum()
            if stato:
                perdita = perdita + (sf.double() * dsf.double()).sum()
            perdita.backward()
            uscite[etich] = [o.detach(), sf.detach() if stato else None] + [x.grad for x in xs] + \
                            ([s0x.grad] if stato else [])
        nomi = ["o", "stato_fin", "dq", "dk", "dv", "dg", "dbeta"] + (["ds0"] if stato else [])
        for i, n in enumerate(nomi):
            if uscite["verita"][i] is None:
                continue
            ek = errore(uscite["kernel"][i], uscite["verita"][i])
            er = errore(uscite["rif32"][i], uscite["verita"][i])
            ok = ek <= max(2 * er, 1e-5) if dtipo == torch.float32 else ek <= max(2 * er, 2e-3)
            esito &= ok
            righe.append(f"    giro {giro} {n:9s} kernel {ek:.2e}  rif32 {er:.2e}  {'ok' if ok else 'NO'}")
    print(f"[{'OK' if esito else 'NO'}] {nome}", flush=True)
    print("\n".join(righe[:len(righe) // n_indietro] + [r for r in righe[len(righe) // n_indietro:] if r.endswith("NO")]))
    return esito


def stessa_storia_tre_volte():
    """Tre indietro sullo STESSO grafo (retain_graph): i buffer salvati non devono sporcarsi."""
    q, k, v, g, beta = dati(1, 256, 32, 128, 16.0, torch.float16, 7)
    xs = [x.detach().clone().requires_grad_(True) for x in (q, k, v, g, beta)]
    o, _ = gdn.chunk_gated_delta_rule(*xs, use_qk_l2norm_in_kernel=True)
    do = torch.randn_like(o)
    grad = []
    for _ in range(3):
        for x in xs:
            x.grad = None
        o.backward(do, retain_graph=True)
        grad.append([x.grad.clone() for x in xs])
    uguali = all(torch.equal(a, b) for gr in grad[1:] for a, b in zip(grad[0], gr))
    print(f"[{'OK' if uguali else 'NO'}] tre indietro sullo stesso grafo: gradienti identici bit a bit")
    return uguali


def correttezza():
    casi = [
        ("Qwen3.5-4B B1 S256 H32 D128, decadimento forte", 1, 256, 32, 128, 16.0),
        ("S200 (non multiplo di 64)", 1, 200, 32, 128, 16.0),
        ("B2 S130 H4, decadimento debole", 2, 130, 4, 128, 0.5),
        ("S64 un blocco", 1, 64, 8, 128, 4.0),
        ("S1000 H4", 1, 1000, 4, 128, 16.0),
        ("D64", 1, 192, 8, 64, 8.0),
    ]
    tutti = True
    for c in casi:
        tutti &= un_caso(*c)
    tutti &= un_caso("stato iniziale e finale, B2 S150 H4", 2, 150, 4, 128, 8.0, stato=True)
    tutti &= un_caso("ingressi fp16, S256 H32", 1, 256, 32, 128, 16.0, dtipo=torch.float16)
    tutti &= un_caso("layout del modello (v vista non contigua, q/k ripetute), fp16, S256 H32", 1, 256, 32, 128,
                     16.0, dtipo=torch.float16, modello=True)
    tutti &= un_caso("layout del modello, fp32, B2 S100 H8", 2, 100, 8, 128, 16.0, modello=True)
    tutti &= stessa_storia_tre_volte()
    print("\nTUTTI OK" if tutti else "\nQUALCOSA NON VA")


def cronometra(fn, n=20):
    for _ in range(3):
        fn()
    torch.cuda.synchronize()
    t = []
    for _ in range(n):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        fn()
        torch.cuda.synchronize()
        t.append(time.perf_counter() - t0)
    return 1000 * statistics.median(t)


def prestazioni():
    for B, S, H in ((1, 256, 32), (1, 1024, 32), (1, 4096, 32)):
        q, k, v, g, beta = dati(B, S, H, 128, 16.0, torch.float16, 0)
        xs = [x.detach().clone().requires_grad_(True) for x in (q, k, v, g, beta)]
        do = torch.randn(B, S, H, 128, device="cuda", dtype=torch.float16)
        riga = f"B{B} S{S} H{H}:"
        for etich, fn in (("torch", rif32), ("kernel", gdn.chunk_gated_delta_rule)):
            if etich == "torch" and S > 1024:
                riga += "  torch -"
                continue
            def avanti():
                with torch.no_grad():
                    fn(*xs, use_qk_l2norm_in_kernel=True)
            def ai():
                o, _ = fn(*xs, use_qk_l2norm_in_kernel=True)
                o.backward(do)
            ta, tai = cronometra(avanti), cronometra(ai, n=10)
            riga += f"  {etich} avanti {ta:8.2f} ms  a+i {tai:8.2f} ms"
        print(riga, flush=True)


if __name__ == "__main__":
    {"correttezza": correttezza, "prestazioni": prestazioni}[sys.argv[1] if len(sys.argv) > 1 else "correttezza"]()

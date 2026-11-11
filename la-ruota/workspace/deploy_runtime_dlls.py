"""Copia in torch\\lib le DLL di runtime che la build di PyTorch non produce.

Da Python 3.8 la ricerca delle DLL non usa il PATH: torch/__init__.py aggiunge torch\\lib
con os.add_dll_directory, quindi le dipendenze devono stare li'. Elenco e origini sono
quelli dell'installazione provata (10 nov 2026), verificati per impronta; il perche' di
ogni file e' nella guida, sezione B1.

    python deploy_runtime_dlls.py --torch-lib <venv>\\Lib\\site-packages\\torch\\lib
        --miopen <cartella bin del pacchetto miopen-gfx906>
        [--rocm57 "C:\\Program Files\\AMD\\ROCm\\5.7\\bin"]
        [--marconi C:\\rocm_5_7_expansion_pack\\bin]
        [--libuv <prefisso di installazione di libuv>]
        [--mkl <mkl_prefix>\\Library\\bin] [--prova]

Ogni copia e' controllata con lo SHA256. Un file gia' presente e identico non si
ricopia; uno presente e diverso si sostituisce (una DLL in uso fa fallire la copia, e lo
script lo dice). Con --prova mostra cosa farebbe senza copiare.

Non copia (e segnala se ci sono) i file che in torch\\lib NON devono esserci:
amd_comgr.dll (fa ombra a quella del driver) e amdhip64_6.dll (vecchio proxy).
I file Tensile instradati per gfx906 (guida, B1) non si rigenerano qui: la libreria
copiata e' quella piatta di ROCm 5.7; le versioni instradate sono nella wheel pubblicata.
"""
import argparse
import hashlib
import os
import shutil
import sys

# (nome, origine): l'origine e' la chiave di una delle cartelle passate da riga di comando
DLL = [
    # MIOpen corretta, i due shim e le DLL di ROCm 7.1 che usano (pacchetto miopen-gfx906)
    ("MIOpen.dll", "miopen"),
    ("hiprtc07013.dll", "miopen"),
    ("amd_cmgr3.dll", "miopen"),
    ("amd_comgr_3.dll", "miopen"),
    ("hiprtc0701.dll", "miopen"),
    ("hiprtc-builtins0701.dll", "miopen"),
    ("amd_comgr0701.dll", "miopen"),
    # shim HIP che MIOpen carica (con il ponte sullo stream nullo) e hipBLASLt: kit Marconi
    ("amdhip64_7.dll", "marconi"),
    ("hipblaslt.dll", "marconi"),
    ("libhipblaslt.dll", "marconi"),
    ("hiprtc-builtins07013.dll", "marconi"),
    # librerie di ROCm 5.7 (HIP SDK)
    ("rocblas.dll", "rocm57"),
    ("rocsolver.dll", "rocm57"),
    ("rocsparse.dll", "rocm57"),
    ("rocfft.dll", "rocm57"),
    ("hipblas.dll", "rocm57"),
    ("hipfft.dll", "rocm57"),
    ("hipsolver.dll", "rocm57"),
    ("libhipsparse.dll", "rocm57"),
    ("hiprtc0507.dll", "rocm57"),
    ("amd_comgr0507.dll", "rocm57"),
    # libuv (costruisci_libuv.cmd) e OpenMP di Intel (dal pacchetto pip intel-openmp)
    ("uv.dll", "libuv"),
    ("libiomp5md.dll", "mkl"),
]
NON_DEVONO_ESSERCI = ["amd_comgr.dll", "amdhip64_6.dll"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


def main():
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--torch-lib", required=True)
    a.add_argument("--miopen", required=True, help="cartella bin del pacchetto miopen-gfx906")
    a.add_argument("--rocm57", default=r"C:\Program Files\AMD\ROCm\5.7\bin")
    a.add_argument("--marconi", default=r"C:\rocm_5_7_expansion_pack\bin")
    a.add_argument("--libuv", default=None, help="prefisso di libuv: si cerca uv.dll in lib\\ e bin\\")
    a.add_argument("--mkl", default=None, help="cartella con libiomp5md.dll (mkl_prefix\\Library\\bin)")
    a.add_argument("--prova", action="store_true")
    arg = a.parse_args()

    dest = arg.torch_lib
    if not os.path.isfile(os.path.join(dest, "torch_hip.dll")):
        sys.exit(f"{dest} non sembra torch\\lib di La Ruota (manca torch_hip.dll)")

    cartelle = {"miopen": [arg.miopen], "rocm57": [arg.rocm57], "marconi": [arg.marconi],
                "libuv": [os.path.join(arg.libuv, "lib"), os.path.join(arg.libuv, "bin")] if arg.libuv else [],
                "mkl": [arg.mkl] if arg.mkl else []}

    errori = 0
    for nome, chiave in DLL:
        src = next((os.path.join(d, nome) for d in cartelle[chiave]
                    if os.path.isfile(os.path.join(d, nome))), None)
        dst = os.path.join(dest, nome)
        if src is None:
            if os.path.isfile(dst):
                print(f"  tenuta   {nome} (nessuna origine indicata per '{chiave}')")
            else:
                print(f"  MANCA    {nome}: non trovata in {cartelle[chiave] or '(passare --' + chiave + ')'}")
                errori += 1
            continue
        hs = sha(src)
        if os.path.isfile(dst) and sha(dst) == hs:
            print(f"  uguale   {nome}")
            continue
        if arg.prova:
            print(f"  copierei {nome} <- {os.path.dirname(src)}")
            continue
        try:
            shutil.copy2(src, dst)
        except OSError as e:
            print(f"  ERRORE   {nome}: {e} (DLL in uso?)")
            errori += 1
            continue
        if sha(dst) != hs:
            print(f"  ERRORE   {nome}: impronta diversa dopo la copia")
            errori += 1
        else:
            print(f"  copiata  {nome} <- {os.path.dirname(src)}")

    # libreria Tensile piatta di ROCm 5.7, solo se manca
    lib = os.path.join(dest, "rocblas", "library")
    src_lib = os.path.join(arg.rocm57, "rocblas", "library")
    if os.path.isdir(lib):
        print(f"  tenuta   rocblas\\library ({len(os.listdir(lib))} file)")
    elif os.path.isdir(src_lib):
        if arg.prova:
            print(f"  copierei rocblas\\library <- {src_lib}")
        else:
            shutil.copytree(src_lib, lib)
            print(f"  copiata  rocblas\\library ({len(os.listdir(lib))} file) <- {src_lib}")
    else:
        print(f"  MANCA    rocblas\\library: non trovata in {src_lib}")
        errori += 1

    for nome in NON_DEVONO_ESSERCI:
        if os.path.exists(os.path.join(dest, nome)):
            print(f"  ATTENZIONE: {nome} in torch\\lib non deve esserci (guida, B1): toglierlo")
            errori += 1

    print("ESITO: OK" if errori == 0 else f"ESITO: FALLITO - {errori} problemi")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())

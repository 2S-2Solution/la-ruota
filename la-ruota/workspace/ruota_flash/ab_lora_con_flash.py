"""Lancia diag_gemm\\ab_lora.py (rocm-marconi) con la flash attention della ruota accesa.

    python ab_lora_con_flash.py --gdn --lunghezza 1024

Stessi argomenti di ab_lora.py. Alla fine stampa quante chiamate a sdpa sono andate alla
flash e quante al percorso originale.
"""
import runpy
import sys

sys.path.insert(0, r"C:\LaRuota_workspace\ruota_flash")
import ruota_flash  # noqa: E402

ruota_flash.attiva()
print("flash attention della ruota: accesa", flush=True)
sys.argv = [r"C:\LaRuota_workspace\diag_gemm\ab_lora.py"] + sys.argv[1:]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
finally:
    print("contatori sdpa:", dict(ruota_flash.contatori), flush=True)

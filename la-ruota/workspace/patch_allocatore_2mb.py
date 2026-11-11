"""VEGA-PATCH 82 - caching allocator: blocchi del pool grande allineati a 2 MB (interruttore).

Scoperta di rocm-marconi (20 ott, diag_gemm\\indirizzi3.py): le GEMM rocBLAS fp16 su gfx906
dipendono dall'indirizzo dell'operando ATTIVAZIONE modulo 2 MB. 512x2560 @ 2560x4096 fa 14,6
TFLOPS a 0 mod 2 MB e 10,2 fra ~512 KB e 1,25 MB (-30%); peso e uscita non contano. Nel passo
LoRA l'allocatore mette le attivazioni nella zona lenta: aten::mm +109 ms a passo.

Perche' succede: i segmenti di hipMalloc partono allineati a 2 MB (verificato), ma le richieste
fra 1 e 10 MB si tagliano da segmenti da 20 MB a passi di 512 byte, e un blocco a valle parte a
un offset qualunque. Rimedio: con PYTORCH_RUOTA_ALLINEA_2MB=1, round_size porta ogni richiesta
del pool grande (> 1 MB) al multiplo di 2 MB. Segmenti (20 MB o multipli di 2 MB), tagli e
fusioni restano multipli di 2 MB, quindi OGNI blocco grande parte a 0 mod 2 MB. Costo: in media
1 MB in piu' per tensore grande (frammentazione interna). Il pool piccolo (<= 1 MB) non cambia.

    python patch_allocatore_2mb.py --prova | --applica
"""
import io
import os
import shutil
import sys

F = r"C:\LaRuota_workspace\pytorch_src\c10\hip\HIPCachingAllocator.cpp"
MARCA = "[VEGA-PATCH 82"
VECCHIO = """  static size_t round_size(size_t size) {
    if (size < kMinBlockSize) {
      return kMinBlockSize;
    } else {
      auto divisions = HIPAllocatorConfig::roundup_power2_divisions(size);
      if (divisions > 1 && size > (kMinBlockSize * divisions)) {
        return roundup_power2_next_division(size, divisions);
      } else {
        return kMinBlockSize * ((size + kMinBlockSize - 1) / kMinBlockSize);
      }
    }
  }
"""
NUOVO = """  // [VEGA-PATCH 82 - 20 ott 2026] con PYTORCH_RUOTA_ALLINEA_2MB=1 i blocchi del pool grande
  // (> 1 MB) sono multipli di 2 MB, quindi partono tutti a 0 mod 2 MB: le GEMM rocBLAS fp16 su
  // gfx906 perdono fino al 30% con l'attivazione fra ~512 KB e 1,25 MB mod 2 MB (rocm-marconi).
  // Spiegazione: C:\\LaRuota_workspace\\patch_allocatore_2mb.py
  static bool vega_allinea_2mb() {
    static const bool attivo = [] {
      const char* v = std::getenv("PYTORCH_RUOTA_ALLINEA_2MB");
      return v != nullptr && v[0] == '1';
    }();
    return attivo;
  }

  static size_t round_size(size_t size) {
    size_t r;
    if (size < kMinBlockSize) {
      return kMinBlockSize;
    } else {
      auto divisions = HIPAllocatorConfig::roundup_power2_divisions(size);
      if (divisions > 1 && size > (kMinBlockSize * divisions)) {
        r = roundup_power2_next_division(size, divisions);
      } else {
        r = kMinBlockSize * ((size + kMinBlockSize - 1) / kMinBlockSize);
      }
    }
    if (r > kSmallSize && vega_allinea_2mb()) {
      r = kRoundLarge * ((r + kRoundLarge - 1) / kRoundLarge);
    }
    return r;
  }
"""
t = io.open(F, encoding="utf-8", newline="").read()
if MARCA in t:
    print("gia' applicata")
    sys.exit(0)
crlf = "\r\n" in t
v, n = (VECCHIO.replace("\n", "\r\n"), NUOVO.replace("\n", "\r\n")) if crlf else (VECCHIO, NUOVO)
if t.count(v) != 1:
    print(f"ERRORE: round_size trovata {t.count(v)} volte")
    sys.exit(1)
t = t.replace(v, n)
if "--applica" in sys.argv:
    if not os.path.exists(F + ".bak_pre_vega82"):
        shutil.copy2(F, F + ".bak_pre_vega82")
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("applicata")
else:
    print("prova a vuoto riuscita")

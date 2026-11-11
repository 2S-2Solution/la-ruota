import sys; sys.path.insert(0, r"C:\LaRuota_workspace\flash_gfx906")
import fa_avanti
for hd in (64, 128):
    c = fa_avanti._compila(hd)
    open(f"fa_{hd}.co", "wb").write(c.raw)
print("scritti")

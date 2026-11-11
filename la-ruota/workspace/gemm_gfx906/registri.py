"""VGPR, SGPR, sversamenti, LDS e istruzioni chiave del kernel gemm (dal code object, senza GPU).
    python registri.py [A_KCONT B_KCONT]   -> scrive asm\gemm_<a><b>.s"""
import re, subprocess, sys
sys.path.insert(0, r"C:\LaRuota_workspace\gemm_gfx906")
import gemm_gfx906 as gg
OBJDUMP = r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-objdump.exe"
READELF = r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-readobj.exe"
akc, bkc = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 1)
gg.OPZIONI[:] = sys.argv[3:]
gg._funzione("gemm", akc, bkc)
codice = gg._funzioni[("gemm", akc, bkc, tuple(gg.OPZIONI))][1]
p = rf"C:\LaRuota_workspace\gemm_gfx906\asm\gemm_{akc}{bkc}.co"
open(p, "wb").write(codice.raw)
s = subprocess.run([OBJDUMP, "-d", "--mcpu=gfx906", p], capture_output=True, text=True).stdout
open(p[:-3] + ".s", "w").write(s)
note = subprocess.run([READELF, "--notes", p], capture_output=True, text=True).stdout
for k in ("vgpr_count", "sgpr_count", "private_segment_fixed_size", "group_segment_fixed_size", "vgpr_spill_count", "sgpr_spill_count"):
    print(k, re.findall(rf"\.{k}:\s*(\d+)", note))
for ist in ("v_dot2_f32_f16", "ds_read_b128", "ds_read_b32", "ds_write_b32", "ds_write_b128", "global_load_dwordx4",
            "buffer_store_dword", "buffer_load_dword", "scratch_", "s_waitcnt", "s_barrier", "v_movreld", "v_movrels"):
    print(f"{ist:22s} {len(re.findall(ist, s))}")

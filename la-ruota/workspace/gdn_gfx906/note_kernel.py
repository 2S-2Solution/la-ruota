"""VGPR / LDS / scratch per kernel, con opzioni di compilazione facoltative."""
import sys, subprocess, re, time
sys.path.insert(0, r"C:\LaRuota_workspace\gdn_gfx906")
import gdn_gfx906 as g
o = sys.argv[1:]
t = time.time(); open("t.co", "wb").write(g.compila(128, 128, o).raw); dt = time.time() - t
n = subprocess.run([r"C:\Program Files\AMD\ROCm\5.7\bin\llvm-readobj.exe", "--notes", "t.co"], capture_output=True, text=True).stdout
for b in n.split("  - .args:")[1:]:          # una voce per kernel
    nome = re.findall(r"\.name:\s*(\S+)", b)[0]
    if nome.startswith("gdn") and not nome.endswith(".kd"):
        f = lambda k: (re.findall(rf"\.{k}:\s*(\d+)", b) or ["?"])[0]
        print(f"{nome:12s} VGPR {f('vgpr_count'):>4s}  LDS {f('group_segment_fixed_size'):>6s}  scratch {f('private_segment_fixed_size')}")
print(o, f"compilazione {dt:.1f} s")

"""Porta i kernel dell'indietro di fa_gfx906.py a 256 thread (4 onde) con 64 righe ferme."""
p = r"C:\LaRuota_workspace\flash_gfx906\fa_gfx906.py"
s = open(p, encoding="utf-8").read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:80])
    s = s.replace(a, b)


# ---- dkdv
rep("#define NT 128\n#define BK 32\n#define BQ 64\n#define PST (BQ / 2 + 4)",
    "#define NT 256\n#define BK 64                                   /* chiavi ferme: tr + 16a */\n"
    "#define BQ (HEAD_DIM == 128 ? 32 : 64)          /* query che scorrono: tc + 16b, b < NB */\n"
    "#define NB (BQ / 16)\n#define PST (BQ / 2 + 4)")
rep("/* chiavi tr + 8a, query tc + 16b */", "/* chiavi tr + 16a, query tc + 16b */")
rep("        float st[4][4], dpt[4][4];", "        float st[4][NB], dpt[4][NB];")
rep("            for (int bb = 0; bb < 4; ++bb) { st[a][bb] = 0.0f; dpt[a][bb] = 0.0f; }",
    "            for (int bb = 0; bb < NB; ++bb) { st[a][bb] = 0.0f; dpt[a][bb] = 0.0f; }")
rep("            u4 ka[4], va[4], qa[4], oa[4];", "            u4 ka[4], va[4], qa[NB], oa[NB];")
rep("                ka[a] = *(const u4*)(Ks + (tr + 8 * a) * QSTR + c);\n"
    "                va[a] = *(const u4*)(Vs + (tr + 8 * a) * QSTR + c);",
    "                ka[a] = *(const u4*)(Ks + (tr + 16 * a) * QSTR + c);\n"
    "                va[a] = *(const u4*)(Vs + (tr + 16 * a) * QSTR + c);")
rep("            for (int bb = 0; bb < 4; ++bb) {\n                qa[bb]",
    "            for (int bb = 0; bb < NB; ++bb) {\n                qa[bb]")
rep("                for (int bb = 0; bb < 4; ++bb)\n                    #pragma unroll\n"
    "                    for (int e = 0; e < 4; ++e) {\n                        st[a][bb]",
    "                for (int bb = 0; bb < NB; ++bb)\n                    #pragma unroll\n"
    "                    for (int e = 0; e < 4; ++e) {\n                        st[a][bb]")
rep("        for (int bb = 0; bb < 4; ++bb) {\n            const int ql = tc + 16 * bb, q = q0 + ql;",
    "        for (int bb = 0; bb < NB; ++bb) {\n            const int ql = tc + 16 * bb, q = q0 + ql;")
rep("                const int key = k0 + tr + 8 * a;", "                const int key = k0 + tr + 16 * a;")
rep("                PTh[(tr + 8 * a) * (2 * PST) + ql] = (f16)pd;\n"
    "                dSTh[(tr + 8 * a) * (2 * PST) + ql]",
    "                PTh[(tr + 16 * a) * (2 * PST) + ql] = (f16)pd;\n"
    "                dSTh[(tr + 16 * a) * (2 * PST) + ql]")
rep("                pa[a] = *(const u4*)(PT + (tr + 8 * a) * PST + qp4);\n"
    "                sa[a] = *(const u4*)(dST + (tr + 8 * a) * PST + qp4);",
    "                pa[a] = *(const u4*)(PT + (tr + 16 * a) * PST + qp4);\n"
    "                sa[a] = *(const u4*)(dST + (tr + 16 * a) * PST + qp4);")
rep("        const int key = k0 + tr + 8 * a;\n        if (key < Sk) {",
    "        const int key = k0 + tr + 16 * a;\n        if (key < Sk) {")

# ---- dq
rep("#define NT 128\n#define BQ 32\n#define BK 64\n#define SST (BK / 2 + 4)",
    "#define NT 256\n#define BQ 64                                   /* query ferme: tr + 16i */\n"
    "#define BK (HEAD_DIM == 128 ? 32 : 64)          /* chiavi che scorrono: tc + 16j, j < NJ */\n"
    "#define NJ (BK / 16)\n#define SST (BK / 2 + 4)")
rep("/* query tr + 8i, chiavi tc + 16j */", "/* query tr + 16i, chiavi tc + 16j */")
rep("        sr[i] = seme_riga(s0, s1, bh, q0 + tr + 8 * i);", "        sr[i] = seme_riga(s0, s1, bh, q0 + tr + 16 * i);")
rep("        float s[4][4], dp[4][4];", "        float s[4][NJ], dp[4][NJ];")
rep("            for (int j = 0; j < 4; ++j) { s[i][j] = 0.0f; dp[i][j] = 0.0f; }",
    "            for (int j = 0; j < NJ; ++j) { s[i][j] = 0.0f; dp[i][j] = 0.0f; }")
rep("            u4 qa[4], oa[4], ka[4], va[4];", "            u4 qa[4], oa[4], ka[NJ], va[NJ];")
rep("                qa[i] = *(const u4*)(Qs + (tr + 8 * i) * QSTR + c);\n"
    "                oa[i] = *(const u4*)(dOs + (tr + 8 * i) * QSTR + c);",
    "                qa[i] = *(const u4*)(Qs + (tr + 16 * i) * QSTR + c);\n"
    "                oa[i] = *(const u4*)(dOs + (tr + 16 * i) * QSTR + c);")
rep("            for (int j = 0; j < 4; ++j) {\n                ka[j]", "            for (int j = 0; j < NJ; ++j) {\n                ka[j]")
rep("                for (int j = 0; j < 4; ++j)\n                    #pragma unroll\n"
    "                    for (int e = 0; e < 4; ++e) {\n                        s[i][j]  = DOT2",
    "                for (int j = 0; j < NJ; ++j)\n                    #pragma unroll\n"
    "                    for (int e = 0; e < 4; ++e) {\n                        s[i][j]  = DOT2")
rep("            const int ql = tr + 8 * i, q = q0 + ql;\n            #pragma unroll\n"
    "            for (int j = 0; j < 4; ++j) {",
    "            const int ql = tr + 16 * i, q = q0 + ql;\n            #pragma unroll\n"
    "            for (int j = 0; j < NJ; ++j) {")
rep("sa[i] = *(const u4*)(dSs + (tr + 8 * i) * SST + kp4);", "sa[i] = *(const u4*)(dSs + (tr + 16 * i) * SST + kp4);")
rep("        const int q = q0 + tr + 8 * i;\n        if (q < Sq) {", "        const int q = q0 + tr + 16 * i;\n        if (q < Sq) {")

rep('"fa_dkdv": (SORGENTE_DKDV, 128, 32),', '"fa_dkdv": (SORGENTE_DKDV, 256, 64),')
rep('"fa_dq": (SORGENTE_DQ, 128, 32)}', '"fa_dq": (SORGENTE_DQ, 256, 64)}')
assert "tr + 8 *" not in s, "resta un indice a 8"
open(p, "w", encoding="utf-8").write(s)
print("patch applicata")

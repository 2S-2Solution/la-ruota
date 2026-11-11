
C:/LaRuota_workspace/flash_gfx906/fa_64.co:	file format elf64-amdgpu

Disassembly of section .text:

0000000000001700 <fa_avanti>:
	s_mov_b64 s[26:27], s[2:3]                                 // 000000001700: BE9A0102
	s_mov_b64 s[24:25], s[0:1]                                 // 000000001704: BE980100
	s_add_u32 s24, s24, s8                                     // 000000001708: 80180818
	s_load_dwordx4 s[8:11], s[4:5], 0x20                       // 00000000170C: C00A0202 00000020
	s_load_dwordx2 s[2:3], s[4:5], 0x0                         // 000000001714: C0060082 00000000
	s_addc_u32 s25, s25, 0                                     // 00000000171C: 82198019
	s_lshl_b32 s14, s6, 6                                      // 000000001720: 8E0E8606
	v_or_b32_e32 v110, s14, v0                                 // 000000001724: 28DC000E
	s_waitcnt lgkmcnt(0)                                       // 000000001728: BF8CC07F
	s_mul_hi_i32 s13, s8, s7                                   // 00000000172C: 968D0708
	s_mul_i32 s11, s8, s7                                      // 000000001730: 920B0708
	v_ashrrev_i32_e32 v2, 31, v110                             // 000000001734: 2204DC9F
	v_mov_b32_e32 v3, s13                                      // 000000001738: 7E06020D
	v_add_co_u32_e32 v1, vcc, s11, v110                        // 00000000173C: 3202DC0B
	v_addc_co_u32_e32 v2, vcc, v3, v2, vcc                     // 000000001740: 38040503
	v_lshlrev_b64 v[6:7], 7, v[1:2]                            // 000000001744: D28F0006 00020287
	v_mov_b32_e32 v2, s3                                       // 00000000174C: 7E040203
	v_add_co_u32_e32 v1, vcc, s2, v6                           // 000000001750: 32020C02
	v_cmp_gt_i32_e64 s[0:1], s8, v110                          // 000000001754: D0C40000 0002DC08
	v_addc_co_u32_e32 v2, vcc, v2, v7, vcc                     // 00000000175C: 38040F02
	v_mov_b32_e32 v111, 0                                      // 000000001760: 7EDE0280
	v_mov_b32_e32 v121, 0                                      // 000000001764: 7EF20280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001768: BE822000
	s_cbranch_execz 2                                          // 00000000176C: BF880002 <fa_avanti+0x78>
	global_load_dword v121, v[1:2], off                        // 000000001770: DC508000 797F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001778: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 00000000177C: BE822000
	s_cbranch_execz 2                                          // 000000001780: BF880002 <fa_avanti+0x8c>
	global_load_dword v111, v[1:2], off offset:4               // 000000001784: DC508004 6F7F0001
	s_or_b64 exec, exec, s[2:3]                                // 00000000178C: 87FE027E
	v_mov_b32_e32 v126, 0                                      // 000000001790: 7EFC0280
	v_mov_b32_e32 v127, 0                                      // 000000001794: 7EFE0280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001798: BE822000
	s_cbranch_execz 2                                          // 00000000179C: BF880002 <fa_avanti+0xa8>
	global_load_dword v127, v[1:2], off offset:8               // 0000000017A0: DC508008 7F7F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000017A8: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000017AC: BE822000
	s_cbranch_execz 2                                          // 0000000017B0: BF880002 <fa_avanti+0xbc>
	global_load_dword v126, v[1:2], off offset:12              // 0000000017B4: DC50800C 7E7F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000017BC: 87FE027E
	v_mov_b32_e32 v141, 0                                      // 0000000017C0: 7F1A0280
	v_mov_b32_e32 v120, 0                                      // 0000000017C4: 7EF00280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000017C8: BE822000
	s_cbranch_execz 2                                          // 0000000017CC: BF880002 <fa_avanti+0xd8>
	global_load_dword v120, v[1:2], off offset:16              // 0000000017D0: DC508010 787F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000017D8: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000017DC: BE822000
	s_cbranch_execz 2                                          // 0000000017E0: BF880002 <fa_avanti+0xec>
	global_load_dword v141, v[1:2], off offset:20              // 0000000017E4: DC508014 8D7F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000017EC: 87FE027E
	v_mov_b32_e32 v142, 0                                      // 0000000017F0: 7F1C0280
	v_mov_b32_e32 v143, 0                                      // 0000000017F4: 7F1E0280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000017F8: BE822000
	s_cbranch_execz 2                                          // 0000000017FC: BF880002 <fa_avanti+0x108>
	global_load_dword v143, v[1:2], off offset:24              // 000000001800: DC508018 8F7F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001808: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 00000000180C: BE822000
	s_cbranch_execz 2                                          // 000000001810: BF880002 <fa_avanti+0x11c>
	global_load_dword v142, v[1:2], off offset:28              // 000000001814: DC50801C 8E7F0001
	s_or_b64 exec, exec, s[2:3]                                // 00000000181C: 87FE027E
	v_mov_b32_e32 v147, 0                                      // 000000001820: 7F260280
	v_mov_b32_e32 v140, 0                                      // 000000001824: 7F180280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001828: BE822000
	s_cbranch_execz 2                                          // 00000000182C: BF880002 <fa_avanti+0x138>
	global_load_dword v140, v[1:2], off offset:32              // 000000001830: DC508020 8C7F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001838: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 00000000183C: BE822000
	s_cbranch_execz 2                                          // 000000001840: BF880002 <fa_avanti+0x14c>
	global_load_dword v147, v[1:2], off offset:36              // 000000001844: DC508024 937F0001
	s_or_b64 exec, exec, s[2:3]                                // 00000000184C: 87FE027E
	v_mov_b32_e32 v169, 0                                      // 000000001850: 7F520280
	v_mov_b32_e32 v170, 0                                      // 000000001854: 7F540280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001858: BE822000
	s_cbranch_execz 2                                          // 00000000185C: BF880002 <fa_avanti+0x168>
	global_load_dword v170, v[1:2], off offset:40              // 000000001860: DC508028 AA7F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001868: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 00000000186C: BE822000
	s_cbranch_execz 2                                          // 000000001870: BF880002 <fa_avanti+0x17c>
	global_load_dword v169, v[1:2], off offset:44              // 000000001874: DC50802C A97F0001
	s_or_b64 exec, exec, s[2:3]                                // 00000000187C: 87FE027E
	v_mov_b32_e32 v171, 0                                      // 000000001880: 7F560280
	v_mov_b32_e32 v172, 0                                      // 000000001884: 7F580280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001888: BE822000
	s_cbranch_execz 2                                          // 00000000188C: BF880002 <fa_avanti+0x198>
	global_load_dword v172, v[1:2], off offset:48              // 000000001890: DC508030 AC7F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001898: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 00000000189C: BE822000
	s_cbranch_execz 2                                          // 0000000018A0: BF880002 <fa_avanti+0x1ac>
	global_load_dword v171, v[1:2], off offset:52              // 0000000018A4: DC508034 AB7F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000018AC: 87FE027E
	v_mov_b32_e32 v173, 0                                      // 0000000018B0: 7F5A0280
	v_mov_b32_e32 v174, 0                                      // 0000000018B4: 7F5C0280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000018B8: BE822000
	s_cbranch_execz 2                                          // 0000000018BC: BF880002 <fa_avanti+0x1c8>
	global_load_dword v174, v[1:2], off offset:56              // 0000000018C0: DC508038 AE7F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000018C8: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000018CC: BE822000
	s_cbranch_execz 2                                          // 0000000018D0: BF880002 <fa_avanti+0x1dc>
	global_load_dword v173, v[1:2], off offset:60              // 0000000018D4: DC50803C AD7F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000018DC: 87FE027E
	v_mov_b32_e32 v175, 0                                      // 0000000018E0: 7F5E0280
	v_mov_b32_e32 v176, 0                                      // 0000000018E4: 7F600280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000018E8: BE822000
	s_cbranch_execz 2                                          // 0000000018EC: BF880002 <fa_avanti+0x1f8>
	global_load_dword v176, v[1:2], off offset:64              // 0000000018F0: DC508040 B07F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000018F8: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000018FC: BE822000
	s_cbranch_execz 2                                          // 000000001900: BF880002 <fa_avanti+0x20c>
	global_load_dword v175, v[1:2], off offset:68              // 000000001904: DC508044 AF7F0001
	s_or_b64 exec, exec, s[2:3]                                // 00000000190C: 87FE027E
	v_mov_b32_e32 v177, 0                                      // 000000001910: 7F620280
	v_mov_b32_e32 v178, 0                                      // 000000001914: 7F640280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001918: BE822000
	s_cbranch_execz 2                                          // 00000000191C: BF880002 <fa_avanti+0x228>
	global_load_dword v178, v[1:2], off offset:72              // 000000001920: DC508048 B27F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001928: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 00000000192C: BE822000
	s_cbranch_execz 2                                          // 000000001930: BF880002 <fa_avanti+0x23c>
	global_load_dword v177, v[1:2], off offset:76              // 000000001934: DC50804C B17F0001
	s_or_b64 exec, exec, s[2:3]                                // 00000000193C: 87FE027E
	v_mov_b32_e32 v179, 0                                      // 000000001940: 7F660280
	v_mov_b32_e32 v180, 0                                      // 000000001944: 7F680280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001948: BE822000
	s_cbranch_execz 2                                          // 00000000194C: BF880002 <fa_avanti+0x258>
	global_load_dword v180, v[1:2], off offset:80              // 000000001950: DC508050 B47F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001958: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 00000000195C: BE822000
	s_cbranch_execz 2                                          // 000000001960: BF880002 <fa_avanti+0x26c>
	global_load_dword v179, v[1:2], off offset:84              // 000000001964: DC508054 B37F0001
	s_or_b64 exec, exec, s[2:3]                                // 00000000196C: 87FE027E
	v_mov_b32_e32 v181, 0                                      // 000000001970: 7F6A0280
	v_mov_b32_e32 v182, 0                                      // 000000001974: 7F6C0280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001978: BE822000
	s_cbranch_execz 2                                          // 00000000197C: BF880002 <fa_avanti+0x288>
	global_load_dword v182, v[1:2], off offset:88              // 000000001980: DC508058 B67F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001988: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 00000000198C: BE822000
	s_cbranch_execz 2                                          // 000000001990: BF880002 <fa_avanti+0x29c>
	global_load_dword v181, v[1:2], off offset:92              // 000000001994: DC50805C B57F0001
	s_or_b64 exec, exec, s[2:3]                                // 00000000199C: 87FE027E
	v_mov_b32_e32 v183, 0                                      // 0000000019A0: 7F6E0280
	v_mov_b32_e32 v184, 0                                      // 0000000019A4: 7F700280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000019A8: BE822000
	s_cbranch_execz 2                                          // 0000000019AC: BF880002 <fa_avanti+0x2b8>
	global_load_dword v184, v[1:2], off offset:96              // 0000000019B0: DC508060 B87F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000019B8: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000019BC: BE822000
	s_cbranch_execz 2                                          // 0000000019C0: BF880002 <fa_avanti+0x2cc>
	global_load_dword v183, v[1:2], off offset:100             // 0000000019C4: DC508064 B77F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000019CC: 87FE027E
	v_mov_b32_e32 v185, 0                                      // 0000000019D0: 7F720280
	v_mov_b32_e32 v186, 0                                      // 0000000019D4: 7F740280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000019D8: BE822000
	s_cbranch_execz 2                                          // 0000000019DC: BF880002 <fa_avanti+0x2e8>
	global_load_dword v186, v[1:2], off offset:104             // 0000000019E0: DC508068 BA7F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000019E8: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 0000000019EC: BE822000
	s_cbranch_execz 2                                          // 0000000019F0: BF880002 <fa_avanti+0x2fc>
	global_load_dword v185, v[1:2], off offset:108             // 0000000019F4: DC50806C B97F0001
	s_or_b64 exec, exec, s[2:3]                                // 0000000019FC: 87FE027E
	v_mov_b32_e32 v187, 0                                      // 000000001A00: 7F760280
	v_mov_b32_e32 v188, 0                                      // 000000001A04: 7F780280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001A08: BE822000
	s_cbranch_execz 2                                          // 000000001A0C: BF880002 <fa_avanti+0x318>
	global_load_dword v188, v[1:2], off offset:112             // 000000001A10: DC508070 BC7F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001A18: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001A1C: BE822000
	s_cbranch_execz 2                                          // 000000001A20: BF880002 <fa_avanti+0x32c>
	global_load_dword v187, v[1:2], off offset:116             // 000000001A24: DC508074 BB7F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001A2C: 87FE027E
	v_mov_b32_e32 v189, 0                                      // 000000001A30: 7F7A0280
	v_mov_b32_e32 v190, 0                                      // 000000001A34: 7F7C0280
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001A38: BE822000
	s_cbranch_execz 2                                          // 000000001A3C: BF880002 <fa_avanti+0x348>
	global_load_dword v190, v[1:2], off offset:120             // 000000001A40: DC508078 BE7F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001A48: 87FE027E
	s_and_saveexec_b64 s[2:3], s[0:1]                          // 000000001A4C: BE822000
	s_cbranch_execz 2                                          // 000000001A50: BF880002 <fa_avanti+0x35c>
	global_load_dword v189, v[1:2], off offset:124             // 000000001A54: DC50807C BD7F0001
	s_or_b64 exec, exec, s[2:3]                                // 000000001A5C: 87FE027E
	s_add_i32 s2, s8, 63                                       // 000000001A60: 8102BF08
	s_ashr_i32 s3, s2, 31                                      // 000000001A64: 90039F02
	s_lshr_b32 s3, s3, 26                                      // 000000001A68: 8F039A03
	s_add_i32 s2, s2, s3                                       // 000000001A6C: 81020302
	s_ashr_i32 s12, s2, 6                                      // 000000001A70: 900C8602
	s_cmp_eq_u32 s10, 0                                        // 000000001A74: BF06800A
	s_cselect_b64 s[6:7], -1, 0                                // 000000001A78: 858680C1
	s_and_b64 vcc, exec, s[6:7]                                // 000000001A7C: 86EA067E
	s_cbranch_vccnz 7                                          // 000000001A80: BF870007 <fa_avanti+0x3a0>
	s_ashr_i32 s2, s14, 31                                     // 000000001A84: 90029F0E
	s_lshr_b32 s2, s2, 26                                      // 000000001A88: 8F029A02
	s_add_i32 s2, s2, s14                                      // 000000001A8C: 81020E02
	s_add_i32 s2, s2, 63                                       // 000000001A90: 8102BF02
	s_ashr_i32 s2, s2, 6                                       // 000000001A94: 90028602
	s_add_i32 s2, s2, 1                                        // 000000001A98: 81028102
	s_min_i32 s12, s12, s2                                     // 000000001A9C: 830C020C
	s_load_dwordx2 s[2:3], s[4:5], 0x18                        // 000000001AA0: C0060082 00000018
	s_cmp_lt_i32 s12, 1                                        // 000000001AA8: BF04810C
	s_cbranch_scc1 4681                                        // 000000001AAC: BF851249 <fa_avanti+0x4cd4>
	v_and_b32_e32 v1, 31, v0                                   // 000000001AB0: 2602009F
	v_or_b32_e32 v2, 0xffffffc0, v0                            // 000000001AB4: 280400FF FFFFFFC0
	v_lshrrev_b32_e32 v3, 5, v0                                // 000000001ABC: 20060085
	buffer_store_dword v6, off, s[24:27], 0 offset:204         // 000000001AC0: E07000CC 80060600
	s_nop 0                                                    // 000000001AC8: BF800000
	buffer_store_dword v7, off, s[24:27], 0 offset:208         // 000000001ACC: E07000D0 80060700
	s_load_dwordx4 s[16:19], s[4:5], 0x8                       // 000000001AD4: C00A0402 00000008
	buffer_store_dword v2, off, s[24:27], 0 offset:196         // 000000001ADC: E07000C4 80060200
	v_lshlrev_b32_e32 v2, 2, v1                                // 000000001AE4: 24040282
	v_mov_b32_e32 v1, s13                                      // 000000001AE8: 7E02020D
	v_add_co_u32_e32 v0, vcc, s11, v3                          // 000000001AEC: 3200060B
	v_addc_co_u32_e32 v1, vcc, 0, v1, vcc                      // 000000001AF0: 38020280
	v_lshlrev_b64 v[0:1], 7, v[0:1]                            // 000000001AF4: D28F0000 00020087
	v_lshl_or_b32 v4, v3, 7, v2                                // 000000001AFC: D2000004 04090F03
	v_or_b32_e32 v0, v0, v2                                    // 000000001B04: 28000500
	buffer_store_dword v4, off, s[24:27], 0 offset:200         // 000000001B08: E07000C8 80060400
	s_waitcnt lgkmcnt(0)                                       // 000000001B10: BF8CC07F
	v_mov_b32_e32 v2, s19                                      // 000000001B14: 7E040213
	v_add_co_u32_e32 v7, vcc, s18, v0                          // 000000001B18: 320E0012
	v_mov_b32_e32 v4, 0                                        // 000000001B1C: 7E080280
	v_addc_co_u32_e32 v8, vcc, v2, v1, vcc                     // 000000001B20: 38100302
	v_mov_b32_e32 v5, v4                                       // 000000001B24: 7E0A0304
	v_mov_b32_e32 v2, s17                                      // 000000001B28: 7E040211
	v_add_co_u32_e32 v11, vcc, s16, v0                         // 000000001B2C: 32160010
	v_mov_b32_e32 v237, v5                                     // 000000001B30: 7FDA0305
	v_mov_b32_e32 v249, v5                                     // 000000001B34: 7FF20305
	v_mov_b32_e32 v247, v5                                     // 000000001B38: 7FEE0305
	v_mov_b32_e32 v255, v5                                     // 000000001B3C: 7FFE0305
	v_mov_b32_e32 v97, v5                                      // 000000001B40: 7EC20305
	v_mov_b32_e32 v99, v5                                      // 000000001B44: 7EC60305
	v_mov_b32_e32 v101, v5                                     // 000000001B48: 7ECA0305
	v_mov_b32_e32 v103, v5                                     // 000000001B4C: 7ECE0305
	v_mov_b32_e32 v145, v5                                     // 000000001B50: 7F220305
	v_mov_b32_e32 v107, v5                                     // 000000001B54: 7ED60305
	v_mov_b32_e32 v149, v5                                     // 000000001B58: 7F2A0305
	v_mov_b32_e32 v153, v5                                     // 000000001B5C: 7F320305
	v_mov_b32_e32 v151, v5                                     // 000000001B60: 7F2E0305
	v_mov_b32_e32 v155, v5                                     // 000000001B64: 7F360305
	v_mov_b32_e32 v157, v5                                     // 000000001B68: 7F3A0305
	v_mov_b32_e32 v129, v5                                     // 000000001B6C: 7F020305
	v_mov_b32_e32 v109, v5                                     // 000000001B70: 7EDA0305
	v_mov_b32_e32 v117, v5                                     // 000000001B74: 7EEA0305
	v_mov_b32_e32 v135, v5                                     // 000000001B78: 7F0E0305
	v_mov_b32_e32 v133, v5                                     // 000000001B7C: 7F0A0305
	v_mov_b32_e32 v139, v5                                     // 000000001B80: 7F160305
	v_mov_b32_e32 v137, v5                                     // 000000001B84: 7F120305
	v_mov_b32_e32 v165, v5                                     // 000000001B88: 7F4A0305
	v_mov_b32_e32 v119, v5                                     // 000000001B8C: 7EEE0305
	v_mov_b32_e32 v63, v5                                      // 000000001B90: 7E7E0305
	v_mov_b32_e32 v131, v5                                     // 000000001B94: 7F060305
	v_mov_b32_e32 v123, v5                                     // 000000001B98: 7EF60305
	v_mov_b32_e32 v125, v5                                     // 000000001B9C: 7EFA0305
	v_mov_b32_e32 v161, v5                                     // 000000001BA0: 7F420305
	v_mov_b32_e32 v163, v5                                     // 000000001BA4: 7F460305
	v_mov_b32_e32 v26, v5                                      // 000000001BA8: 7E340305
	v_mov_b32_e32 v24, v5                                      // 000000001BAC: 7E300305
	v_addc_co_u32_e32 v12, vcc, v2, v1, vcc                    // 000000001BB0: 38180302
	s_mov_b32 s13, 0                                           // 000000001BB4: BE8D0080
	v_mov_b32_e32 v6, 0xff800000                               // 000000001BB8: 7E0C02FF FF800000
	s_movk_i32 s14, 0x7bf                                      // 000000001BC0: B00E07BF
	s_mov_b32 s15, 0xff800000                                  // 000000001BC4: BE8F00FF FF800000
	v_mov_b32_e32 v226, 0xff800000                             // 000000001BCC: 7FC402FF FF800000
	v_mov_b32_e32 v236, v4                                     // 000000001BD4: 7FD80304
	v_mov_b32_e32 v248, v4                                     // 000000001BD8: 7FF00304
	v_mov_b32_e32 v246, v4                                     // 000000001BDC: 7FEC0304
	v_mov_b32_e32 v254, v4                                     // 000000001BE0: 7FFC0304
	v_mov_b32_e32 v96, v4                                      // 000000001BE4: 7EC00304
	v_mov_b32_e32 v98, v4                                      // 000000001BE8: 7EC40304
	v_mov_b32_e32 v100, v4                                     // 000000001BEC: 7EC80304
	v_mov_b32_e32 v102, v4                                     // 000000001BF0: 7ECC0304
	v_mov_b32_e32 v144, v4                                     // 000000001BF4: 7F200304
	v_mov_b32_e32 v106, v4                                     // 000000001BF8: 7ED40304
	v_mov_b32_e32 v148, v4                                     // 000000001BFC: 7F280304
	v_mov_b32_e32 v152, v4                                     // 000000001C00: 7F300304
	v_mov_b32_e32 v150, v4                                     // 000000001C04: 7F2C0304
	v_mov_b32_e32 v154, v4                                     // 000000001C08: 7F340304
	v_mov_b32_e32 v156, v4                                     // 000000001C0C: 7F380304
	v_mov_b32_e32 v128, v4                                     // 000000001C10: 7F000304
	v_mov_b32_e32 v108, v4                                     // 000000001C14: 7ED80304
	v_mov_b32_e32 v116, v4                                     // 000000001C18: 7EE80304
	v_mov_b32_e32 v134, v4                                     // 000000001C1C: 7F0C0304
	v_mov_b32_e32 v132, v4                                     // 000000001C20: 7F080304
	v_mov_b32_e32 v138, v4                                     // 000000001C24: 7F140304
	v_mov_b32_e32 v136, v4                                     // 000000001C28: 7F100304
	v_mov_b32_e32 v164, v4                                     // 000000001C2C: 7F480304
	v_mov_b32_e32 v118, v4                                     // 000000001C30: 7EEC0304
	v_mov_b32_e32 v62, v4                                      // 000000001C34: 7E7C0304
	v_mov_b32_e32 v130, v4                                     // 000000001C38: 7F040304
	v_mov_b32_e32 v122, v4                                     // 000000001C3C: 7EF40304
	v_mov_b32_e32 v124, v4                                     // 000000001C40: 7EF80304
	v_mov_b32_e32 v160, v4                                     // 000000001C44: 7F400304
	v_mov_b32_e32 v162, v4                                     // 000000001C48: 7F440304
	v_mov_b32_e32 v25, v4                                      // 000000001C4C: 7E320304
	v_mov_b32_e32 v23, v4                                      // 000000001C50: 7E2E0304
	s_branch 26                                                // 000000001C54: BF82001A <fa_avanti+0x5c0>
	s_waitcnt lgkmcnt(0)                                       // 000000001C58: BF8CC07F
	buffer_load_dword v7, off, s[24:27], 0 offset:180          // 000000001C5C: E05000B4 80060700
	buffer_load_dword v8, off, s[24:27], 0 offset:184          // 000000001C64: E05000B8 80060800
	buffer_load_dword v11, off, s[24:27], 0 offset:188         // 000000001C6C: E05000BC 80060B00
	buffer_load_dword v12, off, s[24:27], 0 offset:192         // 000000001C74: E05000C0 80060C00
	buffer_load_dword v3, off, s[24:27], 0 offset:176          // 000000001C7C: E05000B0 80060300
	s_add_i32 s13, s13, 1                                      // 000000001C84: 810D810D
	s_cmp_eq_u32 s13, s12                                      // 000000001C88: BF060C0D
	s_waitcnt vmcnt(4)                                         // 000000001C8C: BF8C0F74
	v_add_co_u32_e32 v7, vcc, 0x2000, v7                       // 000000001C90: 320E0EFF 00002000
	s_waitcnt vmcnt(3)                                         // 000000001C98: BF8C0F73
	v_addc_co_u32_e32 v8, vcc, 0, v8, vcc                      // 000000001C9C: 38101080
	s_waitcnt vmcnt(2)                                         // 000000001CA0: BF8C0F72
	v_add_co_u32_e32 v11, vcc, 0x2000, v11                     // 000000001CA4: 321616FF 00002000
	s_waitcnt vmcnt(1)                                         // 000000001CAC: BF8C0F71
	v_addc_co_u32_e32 v12, vcc, 0, v12, vcc                    // 000000001CB0: 38181880
	s_waitcnt vmcnt(0)                                         // 000000001CB4: BF8C0F70
	v_add_u32_e32 v3, 64, v3                                   // 000000001CB8: 680606C0
	s_cbranch_scc1 4368                                        // 000000001CBC: BF851110 <fa_avanti+0x4a00>
	buffer_store_dword v3, off, s[24:27], 0 offset:176         // 000000001CC0: E07000B0 80060300
	buffer_store_dword v7, off, s[24:27], 0 offset:180         // 000000001CC8: E07000B4 80060700
	s_nop 0                                                    // 000000001CD0: BF800000
	buffer_store_dword v8, off, s[24:27], 0 offset:184         // 000000001CD4: E07000B8 80060800
	v_mov_b32_e32 v5, v3                                       // 000000001CDC: 7E0A0303
	v_mov_b32_e32 v0, v11                                      // 000000001CE0: 7E00030B
	s_mov_b64 s[4:5], 0                                        // 000000001CE4: BE840180
	v_mov_b32_e32 v1, v12                                      // 000000001CE8: 7E02030C
	v_mov_b32_e32 v2, v7                                       // 000000001CEC: 7E040307
	v_mov_b32_e32 v3, v8                                       // 000000001CF0: 7E060308
	buffer_load_dword v7, off, s[24:27], 0 offset:200          // 000000001CF4: E05000C8 80060700
	buffer_load_dword v8, off, s[24:27], 0 offset:196          // 000000001CFC: E05000C4 80060800
	s_branch 18                                                // 000000001D04: BF820012 <fa_avanti+0x650>
	s_or_b64 exec, exec, s[10:11]                              // 000000001D08: 87FE0A7E
	v_add_co_u32_e32 v2, vcc, 0x100, v2                        // 000000001D0C: 320404FF 00000100
	v_addc_co_u32_e32 v3, vcc, 0, v3, vcc                      // 000000001D14: 38060680
	v_add_co_u32_e32 v0, vcc, 0x100, v0                        // 000000001D18: 320000FF 00000100
	s_waitcnt vmcnt(0)                                         // 000000001D20: BF8C0F70
	v_add_u32_e32 v8, 64, v8                                   // 000000001D24: 681010C0
	v_addc_co_u32_e32 v1, vcc, 0, v1, vcc                      // 000000001D28: 38020280
	v_cmp_lt_u32_e32 vcc, s14, v8                              // 000000001D2C: 7D92100E
	ds_write2st64_b32 v7, v9, v10 offset1:32                   // 000000001D30: D81E2000 000A0907
	v_add_u32_e32 v7, 0x100, v7                                // 000000001D38: 680E0EFF 00000100
	s_or_b64 s[4:5], vcc, s[4:5]                               // 000000001D40: 8784046A
	v_add_u32_e32 v5, 2, v5                                    // 000000001D44: 680A0A82
	s_andn2_b64 exec, exec, s[4:5]                             // 000000001D48: 89FE047E
	s_cbranch_execz 10                                         // 000000001D4C: BF88000A <fa_avanti+0x678>
	v_cmp_gt_i32_e32 vcc, s8, v5                               // 000000001D50: 7D880A08
	v_mov_b32_e32 v9, 0                                        // 000000001D54: 7E120280
	v_mov_b32_e32 v10, 0                                       // 000000001D58: 7E140280
	s_and_saveexec_b64 s[10:11], vcc                           // 000000001D5C: BE8A206A
	s_cbranch_execz 65513                                      // 000000001D60: BF88FFE9 <fa_avanti+0x608>
	global_load_dword v9, v[0:1], off                          // 000000001D64: DC508000 097F0000
	global_load_dword v10, v[2:3], off                         // 000000001D6C: DC508000 0A7F0002
	s_branch 65508                                             // 000000001D74: BF82FFE4 <fa_avanti+0x608>
	s_or_b64 exec, exec, s[4:5]                                // 000000001D78: 87FE047E
	s_lshl_b32 s10, s13, 6                                     // 000000001D7C: 8E0A860D
	s_mov_b32 s11, 0                                           // 000000001D80: BE8B0080
	buffer_store_dword v11, off, s[24:27], 0 offset:188        // 000000001D84: E07000BC 80060B00
	s_nop 0                                                    // 000000001D8C: BF800000
	buffer_store_dword v12, off, s[24:27], 0 offset:192        // 000000001D90: E07000C0 80060C00
	s_waitcnt lgkmcnt(0)                                       // 000000001D98: BF8CC07F
	s_waitcnt lgkmcnt(0)                                       // 000000001D9C: BF8CC07F
	s_lshl_b32 s16, s11, 7                                     // 000000001DA0: 8E10870B
	v_mov_b32_e32 v1, s16                                      // 000000001DA4: 7E020210
	ds_read_b128 v[7:10], v1                                   // 000000001DA8: D9FE0000 07000001
	ds_read_b128 v[11:14], v1 offset:16                        // 000000001DB0: D9FE0010 0B000001
	ds_read_b128 v[15:18], v1 offset:32                        // 000000001DB8: D9FE0020 0F000001
	ds_read_b128 v[19:22], v1 offset:48                        // 000000001DC0: D9FE0030 13000001
	s_or_b32 s4, s11, s10                                      // 000000001DC8: 87040A0B
	s_cmp_lt_i32 s4, s8                                        // 000000001DCC: BF040804
	v_cmp_le_i32_e32 vcc, s4, v110                             // 000000001DD0: 7D86DC04
	s_waitcnt lgkmcnt(3)                                       // 000000001DD4: BF8CC37F
	v_dot2_f32_f16 v0, v121, v7, 0                             // 000000001DD8: D3A34000 1A020F79
	v_dot2_f32_f16 v0, v111, v8, v0                            // 000000001DE0: D3A34000 1C02116F
	v_dot2_f32_f16 v0, v127, v9, v0                            // 000000001DE8: D3A34000 1C02137F
	v_dot2_f32_f16 v0, v126, v10, v0                           // 000000001DF0: D3A34000 1C02157E
	s_waitcnt lgkmcnt(2)                                       // 000000001DF8: BF8CC27F
	v_dot2_f32_f16 v0, v120, v11, v0                           // 000000001DFC: D3A34000 1C021778
	v_dot2_f32_f16 v0, v141, v12, v0                           // 000000001E04: D3A34000 1C02198D
	v_dot2_f32_f16 v0, v143, v13, v0                           // 000000001E0C: D3A34000 1C021B8F
	v_dot2_f32_f16 v0, v142, v14, v0                           // 000000001E14: D3A34000 1C021D8E
	s_waitcnt lgkmcnt(1)                                       // 000000001E1C: BF8CC17F
	v_dot2_f32_f16 v0, v140, v15, v0                           // 000000001E20: D3A34000 1C021F8C
	v_dot2_f32_f16 v0, v147, v16, v0                           // 000000001E28: D3A34000 1C022193
	v_dot2_f32_f16 v0, v170, v17, v0                           // 000000001E30: D3A34000 1C0223AA
	v_dot2_f32_f16 v0, v169, v18, v0                           // 000000001E38: D3A34000 1C0225A9
	ds_read_b128 v[7:10], v1 offset:64                         // 000000001E40: D9FE0040 07000001
	ds_read_b128 v[11:14], v1 offset:80                        // 000000001E48: D9FE0050 0B000001
	s_waitcnt lgkmcnt(2)                                       // 000000001E50: BF8CC27F
	v_dot2_f32_f16 v0, v172, v19, v0                           // 000000001E54: D3A34000 1C0227AC
	v_dot2_f32_f16 v0, v171, v20, v0                           // 000000001E5C: D3A34000 1C0229AB
	v_dot2_f32_f16 v0, v174, v21, v0                           // 000000001E64: D3A34000 1C022BAE
	v_dot2_f32_f16 v0, v173, v22, v0                           // 000000001E6C: D3A34000 1C022DAD
	s_waitcnt lgkmcnt(1)                                       // 000000001E74: BF8CC17F
	v_dot2_f32_f16 v0, v176, v7, v0                            // 000000001E78: D3A34000 1C020FB0
	v_dot2_f32_f16 v0, v175, v8, v0                            // 000000001E80: D3A34000 1C0211AF
	v_dot2_f32_f16 v0, v178, v9, v0                            // 000000001E88: D3A34000 1C0213B2
	v_dot2_f32_f16 v0, v177, v10, v0                           // 000000001E90: D3A34000 1C0215B1
	ds_read_b128 v[7:10], v1 offset:96                         // 000000001E98: D9FE0060 07000001
	s_waitcnt lgkmcnt(1)                                       // 000000001EA0: BF8CC17F
	v_dot2_f32_f16 v0, v180, v11, v0                           // 000000001EA4: D3A34000 1C0217B4
	v_dot2_f32_f16 v0, v179, v12, v0                           // 000000001EAC: D3A34000 1C0219B3
	v_dot2_f32_f16 v0, v182, v13, v0                           // 000000001EB4: D3A34000 1C021BB6
	v_dot2_f32_f16 v0, v181, v14, v0                           // 000000001EBC: D3A34000 1C021DB5
	ds_read_b128 v[11:14], v1 offset:112                       // 000000001EC4: D9FE0070 0B000001
	s_waitcnt lgkmcnt(1)                                       // 000000001ECC: BF8CC17F
	v_dot2_f32_f16 v0, v184, v7, v0                            // 000000001ED0: D3A34000 1C020FB8
	v_dot2_f32_f16 v0, v183, v8, v0                            // 000000001ED8: D3A34000 1C0211B7
	v_dot2_f32_f16 v0, v186, v9, v0                            // 000000001EE0: D3A34000 1C0213BA
	v_dot2_f32_f16 v0, v185, v10, v0                           // 000000001EE8: D3A34000 1C0215B9
	ds_read_b128 v[7:10], v1 offset:128                        // 000000001EF0: D9FE0080 07000001
	s_waitcnt lgkmcnt(1)                                       // 000000001EF8: BF8CC17F
	v_dot2_f32_f16 v0, v188, v11, v0                           // 000000001EFC: D3A34000 1C0217BC
	v_dot2_f32_f16 v0, v187, v12, v0                           // 000000001F04: D3A34000 1C0219BB
	v_dot2_f32_f16 v0, v190, v13, v0                           // 000000001F0C: D3A34000 1C021BBE
	v_dot2_f32_f16 v0, v189, v14, v0                           // 000000001F14: D3A34000 1C021DBD
	ds_read_b128 v[11:14], v1 offset:144                       // 000000001F1C: D9FE0090 0B000001
	s_waitcnt lgkmcnt(1)                                       // 000000001F24: BF8CC17F
	v_dot2_f32_f16 v2, v121, v7, 0                             // 000000001F28: D3A34002 1A020F79
	v_dot2_f32_f16 v2, v111, v8, v2                            // 000000001F30: D3A34002 1C0A116F
	v_dot2_f32_f16 v2, v127, v9, v2                            // 000000001F38: D3A34002 1C0A137F
	v_dot2_f32_f16 v2, v126, v10, v2                           // 000000001F40: D3A34002 1C0A157E
	ds_read_b128 v[7:10], v1 offset:160                        // 000000001F48: D9FE00A0 07000001
	s_waitcnt lgkmcnt(1)                                       // 000000001F50: BF8CC17F
	v_dot2_f32_f16 v2, v120, v11, v2                           // 000000001F54: D3A34002 1C0A1778
	v_dot2_f32_f16 v2, v141, v12, v2                           // 000000001F5C: D3A34002 1C0A198D
	v_dot2_f32_f16 v2, v143, v13, v2                           // 000000001F64: D3A34002 1C0A1B8F
	v_dot2_f32_f16 v2, v142, v14, v2                           // 000000001F6C: D3A34002 1C0A1D8E
	ds_read_b128 v[11:14], v1 offset:176                       // 000000001F74: D9FE00B0 0B000001
	s_waitcnt lgkmcnt(1)                                       // 000000001F7C: BF8CC17F
	v_dot2_f32_f16 v2, v140, v7, v2                            // 000000001F80: D3A34002 1C0A0F8C
	v_dot2_f32_f16 v2, v147, v8, v2                            // 000000001F88: D3A34002 1C0A1193
	v_dot2_f32_f16 v2, v170, v9, v2                            // 000000001F90: D3A34002 1C0A13AA
	v_dot2_f32_f16 v2, v169, v10, v2                           // 000000001F98: D3A34002 1C0A15A9
	ds_read_b128 v[7:10], v1 offset:192                        // 000000001FA0: D9FE00C0 07000001
	s_waitcnt lgkmcnt(1)                                       // 000000001FA8: BF8CC17F
	v_dot2_f32_f16 v2, v172, v11, v2                           // 000000001FAC: D3A34002 1C0A17AC
	v_dot2_f32_f16 v2, v171, v12, v2                           // 000000001FB4: D3A34002 1C0A19AB
	v_dot2_f32_f16 v2, v174, v13, v2                           // 000000001FBC: D3A34002 1C0A1BAE
	v_dot2_f32_f16 v2, v173, v14, v2                           // 000000001FC4: D3A34002 1C0A1DAD
	ds_read_b128 v[11:14], v1 offset:208                       // 000000001FCC: D9FE00D0 0B000001
	s_waitcnt lgkmcnt(1)                                       // 000000001FD4: BF8CC17F
	v_dot2_f32_f16 v2, v176, v7, v2                            // 000000001FD8: D3A34002 1C0A0FB0
	v_dot2_f32_f16 v2, v175, v8, v2                            // 000000001FE0: D3A34002 1C0A11AF
	v_dot2_f32_f16 v2, v178, v9, v2                            // 000000001FE8: D3A34002 1C0A13B2
	v_dot2_f32_f16 v2, v177, v10, v2                           // 000000001FF0: D3A34002 1C0A15B1
	ds_read_b128 v[7:10], v1 offset:224                        // 000000001FF8: D9FE00E0 07000001
	s_waitcnt lgkmcnt(1)                                       // 000000002000: BF8CC17F
	v_dot2_f32_f16 v2, v180, v11, v2                           // 000000002004: D3A34002 1C0A17B4
	v_dot2_f32_f16 v2, v179, v12, v2                           // 00000000200C: D3A34002 1C0A19B3
	v_dot2_f32_f16 v2, v182, v13, v2                           // 000000002014: D3A34002 1C0A1BB6
	v_dot2_f32_f16 v2, v181, v14, v2                           // 00000000201C: D3A34002 1C0A1DB5
	ds_read_b128 v[11:14], v1 offset:240                       // 000000002024: D9FE00F0 0B000001
	s_waitcnt lgkmcnt(1)                                       // 00000000202C: BF8CC17F
	v_dot2_f32_f16 v2, v184, v7, v2                            // 000000002030: D3A34002 1C0A0FB8
	v_dot2_f32_f16 v2, v183, v8, v2                            // 000000002038: D3A34002 1C0A11B7
	v_dot2_f32_f16 v2, v186, v9, v2                            // 000000002040: D3A34002 1C0A13BA
	v_dot2_f32_f16 v2, v185, v10, v2                           // 000000002048: D3A34002 1C0A15B9
	ds_read_b128 v[7:10], v1 offset:256                        // 000000002050: D9FE0100 07000001
	s_waitcnt lgkmcnt(1)                                       // 000000002058: BF8CC17F
	v_dot2_f32_f16 v2, v188, v11, v2                           // 00000000205C: D3A34002 1C0A17BC
	v_dot2_f32_f16 v2, v187, v12, v2                           // 000000002064: D3A34002 1C0A19BB
	v_dot2_f32_f16 v2, v190, v13, v2                           // 00000000206C: D3A34002 1C0A1BBE
	v_dot2_f32_f16 v2, v189, v14, v2                           // 000000002074: D3A34002 1C0A1DBD
	ds_read_b128 v[11:14], v1 offset:272                       // 00000000207C: D9FE0110 0B000001
	s_waitcnt lgkmcnt(1)                                       // 000000002084: BF8CC17F
	v_dot2_f32_f16 v5, v121, v7, 0                             // 000000002088: D3A34005 1A020F79
	v_dot2_f32_f16 v5, v111, v8, v5                            // 000000002090: D3A34005 1C16116F
	v_dot2_f32_f16 v5, v127, v9, v5                            // 000000002098: D3A34005 1C16137F
	v_dot2_f32_f16 v5, v126, v10, v5                           // 0000000020A0: D3A34005 1C16157E
	ds_read_b128 v[7:10], v1 offset:288                        // 0000000020A8: D9FE0120 07000001
	s_waitcnt lgkmcnt(1)                                       // 0000000020B0: BF8CC17F
	v_dot2_f32_f16 v5, v120, v11, v5                           // 0000000020B4: D3A34005 1C161778
	v_dot2_f32_f16 v5, v141, v12, v5                           // 0000000020BC: D3A34005 1C16198D
	v_dot2_f32_f16 v5, v143, v13, v5                           // 0000000020C4: D3A34005 1C161B8F
	v_dot2_f32_f16 v5, v142, v14, v5                           // 0000000020CC: D3A34005 1C161D8E
	ds_read_b128 v[11:14], v1 offset:304                       // 0000000020D4: D9FE0130 0B000001
	s_waitcnt lgkmcnt(1)                                       // 0000000020DC: BF8CC17F
	v_dot2_f32_f16 v5, v140, v7, v5                            // 0000000020E0: D3A34005 1C160F8C
	v_dot2_f32_f16 v5, v147, v8, v5                            // 0000000020E8: D3A34005 1C161193
	v_dot2_f32_f16 v5, v170, v9, v5                            // 0000000020F0: D3A34005 1C1613AA
	v_dot2_f32_f16 v5, v169, v10, v5                           // 0000000020F8: D3A34005 1C1615A9
	ds_read_b128 v[7:10], v1 offset:320                        // 000000002100: D9FE0140 07000001
	s_waitcnt lgkmcnt(1)                                       // 000000002108: BF8CC17F
	v_dot2_f32_f16 v5, v172, v11, v5                           // 00000000210C: D3A34005 1C1617AC
	v_dot2_f32_f16 v5, v171, v12, v5                           // 000000002114: D3A34005 1C1619AB
	v_dot2_f32_f16 v5, v174, v13, v5                           // 00000000211C: D3A34005 1C161BAE
	v_dot2_f32_f16 v5, v173, v14, v5                           // 000000002124: D3A34005 1C161DAD
	ds_read_b128 v[11:14], v1 offset:336                       // 00000000212C: D9FE0150 0B000001
	s_waitcnt lgkmcnt(1)                                       // 000000002134: BF8CC17F
	v_dot2_f32_f16 v5, v176, v7, v5                            // 000000002138: D3A34005 1C160FB0
	v_dot2_f32_f16 v5, v175, v8, v5                            // 000000002140: D3A34005 1C1611AF
	v_dot2_f32_f16 v5, v178, v9, v5                            // 000000002148: D3A34005 1C1613B2
	v_dot2_f32_f16 v5, v177, v10, v5                           // 000000002150: D3A34005 1C1615B1
	ds_read_b128 v[7:10], v1 offset:352                        // 000000002158: D9FE0160 07000001
	s_waitcnt lgkmcnt(1)                                       // 000000002160: BF8CC17F
	v_dot2_f32_f16 v5, v180, v11, v5                           // 000000002164: D3A34005 1C1617B4
	v_dot2_f32_f16 v5, v179, v12, v5                           // 00000000216C: D3A34005 1C1619B3
	v_dot2_f32_f16 v5, v182, v13, v5                           // 000000002174: D3A34005 1C161BB6
	v_dot2_f32_f16 v5, v181, v14, v5                           // 00000000217C: D3A34005 1C161DB5
	ds_read_b128 v[11:14], v1 offset:368                       // 000000002184: D9FE0170 0B000001
	s_waitcnt lgkmcnt(1)                                       // 00000000218C: BF8CC17F
	v_dot2_f32_f16 v5, v184, v7, v5                            // 000000002190: D3A34005 1C160FB8
	v_dot2_f32_f16 v5, v183, v8, v5                            // 000000002198: D3A34005 1C1611B7
	v_dot2_f32_f16 v5, v186, v9, v5                            // 0000000021A0: D3A34005 1C1613BA
	v_dot2_f32_f16 v5, v185, v10, v5                           // 0000000021A8: D3A34005 1C1615B9
	ds_read_b128 v[7:10], v1 offset:384                        // 0000000021B0: D9FE0180 07000001
	s_waitcnt lgkmcnt(1)                                       // 0000000021B8: BF8CC17F
	v_dot2_f32_f16 v5, v188, v11, v5                           // 0000000021BC: D3A34005 1C1617BC
	v_dot2_f32_f16 v5, v187, v12, v5                           // 0000000021C4: D3A34005 1C1619BB
	v_dot2_f32_f16 v5, v190, v13, v5                           // 0000000021CC: D3A34005 1C161BBE
	v_dot2_f32_f16 v5, v189, v14, v5                           // 0000000021D4: D3A34005 1C161DBD
	ds_read_b128 v[11:14], v1 offset:400                       // 0000000021DC: D9FE0190 0B000001
	s_waitcnt lgkmcnt(1)                                       // 0000000021E4: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 0000000021E8: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 0000000021F0: D3A34007 1C1E116F
	v_dot2_f32_f16 v7, v127, v9, v7                            // 0000000021F8: D3A34007 1C1E137F
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000002200: D3A34007 1C1E157E
	s_waitcnt lgkmcnt(0)                                       // 000000002208: BF8CC07F
	v_dot2_f32_f16 v11, v120, v11, v7                          // 00000000220C: D3A3400B 1C1E1778
	ds_read_b128 v[7:10], v1 offset:416                        // 000000002214: D9FE01A0 07000001
	v_dot2_f32_f16 v11, v141, v12, v11                         // 00000000221C: D3A3400B 1C2E198D
	v_dot2_f32_f16 v11, v143, v13, v11                         // 000000002224: D3A3400B 1C2E1B8F
	v_dot2_f32_f16 v15, v142, v14, v11                         // 00000000222C: D3A3400F 1C2E1D8E
	ds_read_b128 v[11:14], v1 offset:432                       // 000000002234: D9FE01B0 0B000001
	s_waitcnt lgkmcnt(1)                                       // 00000000223C: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v15                           // 000000002240: D3A34007 1C3E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 000000002248: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000002250: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 000000002258: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000002260: BF8CC07F
	v_dot2_f32_f16 v11, v172, v11, v7                          // 000000002264: D3A3400B 1C1E17AC
	ds_read_b128 v[7:10], v1 offset:448                        // 00000000226C: D9FE01C0 07000001
	v_dot2_f32_f16 v11, v171, v12, v11                         // 000000002274: D3A3400B 1C2E19AB
	v_dot2_f32_f16 v11, v174, v13, v11                         // 00000000227C: D3A3400B 1C2E1BAE
	v_dot2_f32_f16 v15, v173, v14, v11                         // 000000002284: D3A3400F 1C2E1DAD
	ds_read_b128 v[11:14], v1 offset:464                       // 00000000228C: D9FE01D0 0B000001
	s_waitcnt lgkmcnt(1)                                       // 000000002294: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v15                           // 000000002298: D3A34007 1C3E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 0000000022A0: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 0000000022A8: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 0000000022B0: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 0000000022B8: BF8CC07F
	v_dot2_f32_f16 v11, v180, v11, v7                          // 0000000022BC: D3A3400B 1C1E17B4
	ds_read_b128 v[7:10], v1 offset:480                        // 0000000022C4: D9FE01E0 07000001
	v_dot2_f32_f16 v11, v179, v12, v11                         // 0000000022CC: D3A3400B 1C2E19B3
	v_dot2_f32_f16 v11, v182, v13, v11                         // 0000000022D4: D3A3400B 1C2E1BB6
	v_dot2_f32_f16 v15, v181, v14, v11                         // 0000000022DC: D3A3400F 1C2E1DB5
	ds_read_b128 v[11:14], v1 offset:496                       // 0000000022E4: D9FE01F0 0B000001
	s_waitcnt lgkmcnt(1)                                       // 0000000022EC: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v15                           // 0000000022F0: D3A34007 1C3E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 0000000022F8: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 000000002300: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 000000002308: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 000000002310: BF8CC07F
	v_dot2_f32_f16 v7, v188, v11, v7                           // 000000002314: D3A34007 1C1E17BC
	v_dot2_f32_f16 v7, v187, v12, v7                           // 00000000231C: D3A34007 1C1E19BB
	s_cselect_b64 s[18:19], -1, 0                              // 000000002324: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 000000002328: 87946A06
	v_dot2_f32_f16 v7, v190, v13, v7                           // 00000000232C: D3A34007 1C1E1BBE
	v_mul_f32_e32 v0, s9, v0                                   // 000000002334: 0A000009
	s_and_b64 vcc, s[18:19], s[20:21]                          // 000000002338: 86EA1412
	s_or_b32 s5, s4, 1                                         // 00000000233C: 87058104
	v_dot2_f32_f16 v7, v189, v14, v7                           // 000000002340: D3A34007 1C1E1DBD
	v_cndmask_b32_e32 v0, v226, v0, vcc                        // 000000002348: 000001E2
	s_cmp_lt_i32 s5, s8                                        // 00000000234C: BF040805
	v_cmp_lt_i32_e32 vcc, s4, v110                             // 000000002350: 7D82DC04
	v_mul_f32_e32 v11, s9, v7                                  // 000000002354: 0A160E09
	ds_read_b128 v[7:10], v1 offset:512                        // 000000002358: D9FE0200 07000001
	ds_read_b128 v[13:16], v1 offset:528                       // 000000002360: D9FE0210 0D000001
	s_cselect_b64 s[18:19], -1, 0                              // 000000002368: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 00000000236C: 87946A06
	v_mul_f32_e32 v2, s9, v2                                   // 000000002370: 0A040409
	s_and_b64 vcc, s[18:19], s[20:21]                          // 000000002374: 86EA1412
	s_or_b32 s5, s4, 2                                         // 000000002378: 87058204
	v_cndmask_b32_e32 v2, v226, v2, vcc                        // 00000000237C: 000405E2
	s_cmp_lt_i32 s5, s8                                        // 000000002380: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000002384: 7D86DC05
	s_cselect_b64 s[18:19], -1, 0                              // 000000002388: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 00000000238C: 87946A06
	v_mul_f32_e32 v5, s9, v5                                   // 000000002390: 0A0A0A09
	s_and_b64 vcc, s[18:19], s[20:21]                          // 000000002394: 86EA1412
	s_or_b32 s5, s4, 3                                         // 000000002398: 87058304
	s_waitcnt lgkmcnt(1)                                       // 00000000239C: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 0000000023A0: D3A34007 1A020F79
	v_cndmask_b32_e32 v5, v226, v5, vcc                        // 0000000023A8: 000A0BE2
	s_cmp_lt_i32 s5, s8                                        // 0000000023AC: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 0000000023B0: 7D86DC05
	v_dot2_f32_f16 v7, v111, v8, v7                            // 0000000023B4: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 0000000023BC: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 0000000023C0: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 0000000023C4: D3A34007 1C1E137F
	s_and_b64 vcc, s[18:19], s[20:21]                          // 0000000023CC: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 0000000023D0: D3A34007 1C1E157E
	v_cndmask_b32_e32 v12, v226, v11, vcc                      // 0000000023D8: 001817E2
	s_waitcnt lgkmcnt(0)                                       // 0000000023DC: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 0000000023E0: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:544                        // 0000000023E8: D9FE0220 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 0000000023F0: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 0000000023F8: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000002400: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:560                       // 000000002408: D9FE0230 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002410: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000002414: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 00000000241C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000002424: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 00000000242C: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000002434: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 000000002438: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:576                        // 000000002440: D9FE0240 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 000000002448: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 000000002450: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 000000002458: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:592                       // 000000002460: D9FE0250 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002468: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 00000000246C: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 000000002474: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 00000000247C: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000002484: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 00000000248C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000002490: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:608                        // 000000002498: D9FE0260 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 0000000024A0: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 0000000024A8: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 0000000024B0: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:624                       // 0000000024B8: D9FE0270 0D000001
	s_waitcnt lgkmcnt(1)                                       // 0000000024C0: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 0000000024C4: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 0000000024CC: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 0000000024D4: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 0000000024DC: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 0000000024E4: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 0000000024E8: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 0000000024F0: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 0000000024F8: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v11, v189, v16, v7                          // 000000002500: D3A3400B 1C1E21BD
	ds_read_b128 v[7:10], v1 offset:640                        // 000000002508: D9FE0280 07000001
	ds_read_b128 v[13:16], v1 offset:656                       // 000000002510: D9FE0290 0D000001
	s_or_b32 s5, s4, 4                                         // 000000002518: 87058404
	s_cmp_lt_i32 s5, s8                                        // 00000000251C: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000002520: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 000000002524: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 000000002528: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 000000002530: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 000000002538: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 00000000253C: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 000000002540: D3A34007 1C1E137F
	v_mul_f32_e32 v11, s9, v11                                 // 000000002548: 0A161609
	s_and_b64 vcc, s[18:19], s[20:21]                          // 00000000254C: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000002550: D3A34007 1C1E157E
	v_cndmask_b32_e32 v20, v226, v11, vcc                      // 000000002558: 002817E2
	s_waitcnt lgkmcnt(0)                                       // 00000000255C: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 000000002560: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:672                        // 000000002568: D9FE02A0 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 000000002570: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 000000002578: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000002580: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:688                       // 000000002588: D9FE02B0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002590: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000002594: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 00000000259C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 0000000025A4: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 0000000025AC: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 0000000025B4: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 0000000025B8: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:704                        // 0000000025C0: D9FE02C0 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 0000000025C8: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 0000000025D0: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 0000000025D8: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:720                       // 0000000025E0: D9FE02D0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 0000000025E8: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 0000000025EC: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 0000000025F4: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 0000000025FC: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000002604: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 00000000260C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000002610: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:736                        // 000000002618: D9FE02E0 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 000000002620: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 000000002628: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 000000002630: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:752                       // 000000002638: D9FE02F0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002640: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 000000002644: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 00000000264C: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 000000002654: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 00000000265C: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 000000002664: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 000000002668: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 000000002670: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 000000002678: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v7, v189, v16, v7                           // 000000002680: D3A34007 1C1E21BD
	v_mul_f32_e32 v11, s9, v7                                  // 000000002688: 0A160E09
	ds_read_b128 v[7:10], v1 offset:768                        // 00000000268C: D9FE0300 07000001
	ds_read_b128 v[13:16], v1 offset:784                       // 000000002694: D9FE0310 0D000001
	s_or_b32 s5, s4, 5                                         // 00000000269C: 87058504
	s_cmp_lt_i32 s5, s8                                        // 0000000026A0: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 0000000026A4: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 0000000026A8: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 0000000026AC: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 0000000026B4: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 0000000026BC: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 0000000026C0: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 0000000026C4: D3A34007 1C1E137F
	s_and_b64 vcc, s[18:19], s[20:21]                          // 0000000026CC: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 0000000026D0: D3A34007 1C1E157E
	v_cndmask_b32_e32 v28, v226, v11, vcc                      // 0000000026D8: 003817E2
	s_waitcnt lgkmcnt(0)                                       // 0000000026DC: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 0000000026E0: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:800                        // 0000000026E8: D9FE0320 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 0000000026F0: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 0000000026F8: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000002700: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:816                       // 000000002708: D9FE0330 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002710: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000002714: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 00000000271C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000002724: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 00000000272C: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000002734: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 000000002738: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:832                        // 000000002740: D9FE0340 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 000000002748: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 000000002750: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 000000002758: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:848                       // 000000002760: D9FE0350 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002768: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 00000000276C: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 000000002774: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 00000000277C: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000002784: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 00000000278C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000002790: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:864                        // 000000002798: D9FE0360 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 0000000027A0: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 0000000027A8: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 0000000027B0: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:880                       // 0000000027B8: D9FE0370 0D000001
	s_waitcnt lgkmcnt(1)                                       // 0000000027C0: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 0000000027C4: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 0000000027CC: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 0000000027D4: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 0000000027DC: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 0000000027E4: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 0000000027E8: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 0000000027F0: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 0000000027F8: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v11, v189, v16, v7                          // 000000002800: D3A3400B 1C1E21BD
	ds_read_b128 v[7:10], v1 offset:896                        // 000000002808: D9FE0380 07000001
	ds_read_b128 v[13:16], v1 offset:912                       // 000000002810: D9FE0390 0D000001
	s_or_b32 s5, s4, 6                                         // 000000002818: 87058604
	s_cmp_lt_i32 s5, s8                                        // 00000000281C: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000002820: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 000000002824: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 000000002828: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 000000002830: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 000000002838: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 00000000283C: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 000000002840: D3A34007 1C1E137F
	v_mul_f32_e32 v11, s9, v11                                 // 000000002848: 0A161609
	s_and_b64 vcc, s[18:19], s[20:21]                          // 00000000284C: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000002850: D3A34007 1C1E157E
	v_cndmask_b32_e32 v40, v226, v11, vcc                      // 000000002858: 005017E2
	s_waitcnt lgkmcnt(0)                                       // 00000000285C: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 000000002860: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:928                        // 000000002868: D9FE03A0 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 000000002870: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 000000002878: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000002880: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:944                       // 000000002888: D9FE03B0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002890: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000002894: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 00000000289C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 0000000028A4: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 0000000028AC: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 0000000028B4: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 0000000028B8: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:960                        // 0000000028C0: D9FE03C0 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 0000000028C8: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 0000000028D0: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 0000000028D8: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:976                       // 0000000028E0: D9FE03D0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 0000000028E8: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 0000000028EC: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 0000000028F4: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 0000000028FC: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000002904: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 00000000290C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000002910: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:992                        // 000000002918: D9FE03E0 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 000000002920: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 000000002928: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 000000002930: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:1008                      // 000000002938: D9FE03F0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002940: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 000000002944: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 00000000294C: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 000000002954: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 00000000295C: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 000000002964: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 000000002968: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 000000002970: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 000000002978: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v7, v189, v16, v7                           // 000000002980: D3A34007 1C1E21BD
	v_mul_f32_e32 v11, s9, v7                                  // 000000002988: 0A160E09
	ds_read_b128 v[7:10], v1 offset:1024                       // 00000000298C: D9FE0400 07000001
	ds_read_b128 v[13:16], v1 offset:1040                      // 000000002994: D9FE0410 0D000001
	s_or_b32 s5, s4, 7                                         // 00000000299C: 87058704
	s_cmp_lt_i32 s5, s8                                        // 0000000029A0: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 0000000029A4: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 0000000029A8: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 0000000029AC: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 0000000029B4: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 0000000029BC: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 0000000029C0: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 0000000029C4: D3A34007 1C1E137F
	s_and_b64 vcc, s[18:19], s[20:21]                          // 0000000029CC: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 0000000029D0: D3A34007 1C1E157E
	v_cndmask_b32_e32 v52, v226, v11, vcc                      // 0000000029D8: 006817E2
	s_waitcnt lgkmcnt(0)                                       // 0000000029DC: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 0000000029E0: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:1056                       // 0000000029E8: D9FE0420 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 0000000029F0: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 0000000029F8: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000002A00: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:1072                      // 000000002A08: D9FE0430 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002A10: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000002A14: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 000000002A1C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000002A24: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 000000002A2C: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000002A34: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 000000002A38: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:1088                       // 000000002A40: D9FE0440 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 000000002A48: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 000000002A50: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 000000002A58: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:1104                      // 000000002A60: D9FE0450 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002A68: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 000000002A6C: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 000000002A74: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 000000002A7C: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000002A84: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 000000002A8C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000002A90: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:1120                       // 000000002A98: D9FE0460 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 000000002AA0: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 000000002AA8: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 000000002AB0: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:1136                      // 000000002AB8: D9FE0470 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002AC0: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 000000002AC4: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 000000002ACC: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 000000002AD4: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 000000002ADC: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 000000002AE4: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 000000002AE8: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 000000002AF0: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 000000002AF8: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v11, v189, v16, v7                          // 000000002B00: D3A3400B 1C1E21BD
	ds_read_b128 v[7:10], v1 offset:1152                       // 000000002B08: D9FE0480 07000001
	ds_read_b128 v[13:16], v1 offset:1168                      // 000000002B10: D9FE0490 0D000001
	s_or_b32 s5, s4, 8                                         // 000000002B18: 87058804
	s_cmp_lt_i32 s5, s8                                        // 000000002B1C: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000002B20: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 000000002B24: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 000000002B28: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 000000002B30: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 000000002B38: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 000000002B3C: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 000000002B40: D3A34007 1C1E137F
	v_mul_f32_e32 v11, s9, v11                                 // 000000002B48: 0A161609
	s_and_b64 vcc, s[18:19], s[20:21]                          // 000000002B4C: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000002B50: D3A34007 1C1E157E
	v_cndmask_b32_e32 v85, v226, v11, vcc                      // 000000002B58: 00AA17E2
	s_waitcnt lgkmcnt(0)                                       // 000000002B5C: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 000000002B60: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:1184                       // 000000002B68: D9FE04A0 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 000000002B70: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 000000002B78: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000002B80: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:1200                      // 000000002B88: D9FE04B0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002B90: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000002B94: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 000000002B9C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000002BA4: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 000000002BAC: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000002BB4: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 000000002BB8: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:1216                       // 000000002BC0: D9FE04C0 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 000000002BC8: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 000000002BD0: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 000000002BD8: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:1232                      // 000000002BE0: D9FE04D0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002BE8: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 000000002BEC: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 000000002BF4: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 000000002BFC: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000002C04: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 000000002C0C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000002C10: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:1248                       // 000000002C18: D9FE04E0 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 000000002C20: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 000000002C28: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 000000002C30: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:1264                      // 000000002C38: D9FE04F0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002C40: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 000000002C44: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 000000002C4C: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 000000002C54: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 000000002C5C: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 000000002C64: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 000000002C68: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 000000002C70: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 000000002C78: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v7, v189, v16, v7                           // 000000002C80: D3A34007 1C1E21BD
	v_mul_f32_e32 v11, s9, v7                                  // 000000002C88: 0A160E09
	ds_read_b128 v[7:10], v1 offset:1280                       // 000000002C8C: D9FE0500 07000001
	ds_read_b128 v[13:16], v1 offset:1296                      // 000000002C94: D9FE0510 0D000001
	s_or_b32 s5, s4, 9                                         // 000000002C9C: 87058904
	s_cmp_lt_i32 s5, s8                                        // 000000002CA0: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000002CA4: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 000000002CA8: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 000000002CAC: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 000000002CB4: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 000000002CBC: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 000000002CC0: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 000000002CC4: D3A34007 1C1E137F
	s_and_b64 vcc, s[18:19], s[20:21]                          // 000000002CCC: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000002CD0: D3A34007 1C1E157E
	v_cndmask_b32_e32 v17, v226, v11, vcc                      // 000000002CD8: 002217E2
	s_waitcnt lgkmcnt(0)                                       // 000000002CDC: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 000000002CE0: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:1312                       // 000000002CE8: D9FE0520 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 000000002CF0: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 000000002CF8: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000002D00: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:1328                      // 000000002D08: D9FE0530 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002D10: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000002D14: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 000000002D1C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000002D24: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 000000002D2C: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000002D34: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 000000002D38: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:1344                       // 000000002D40: D9FE0540 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 000000002D48: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 000000002D50: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 000000002D58: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:1360                      // 000000002D60: D9FE0550 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002D68: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 000000002D6C: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 000000002D74: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 000000002D7C: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000002D84: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 000000002D8C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000002D90: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:1376                       // 000000002D98: D9FE0560 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 000000002DA0: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 000000002DA8: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 000000002DB0: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:1392                      // 000000002DB8: D9FE0570 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002DC0: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 000000002DC4: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 000000002DCC: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 000000002DD4: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 000000002DDC: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 000000002DE4: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 000000002DE8: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 000000002DF0: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 000000002DF8: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v11, v189, v16, v7                          // 000000002E00: D3A3400B 1C1E21BD
	ds_read_b128 v[7:10], v1 offset:1408                       // 000000002E08: D9FE0580 07000001
	ds_read_b128 v[13:16], v1 offset:1424                      // 000000002E10: D9FE0590 0D000001
	s_or_b32 s5, s4, 10                                        // 000000002E18: 87058A04
	s_cmp_lt_i32 s5, s8                                        // 000000002E1C: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000002E20: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 000000002E24: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 000000002E28: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 000000002E30: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 000000002E38: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 000000002E3C: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 000000002E40: D3A34007 1C1E137F
	v_mul_f32_e32 v11, s9, v11                                 // 000000002E48: 0A161609
	s_and_b64 vcc, s[18:19], s[20:21]                          // 000000002E4C: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000002E50: D3A34007 1C1E157E
	v_cndmask_b32_e32 v18, v226, v11, vcc                      // 000000002E58: 002417E2
	s_waitcnt lgkmcnt(0)                                       // 000000002E5C: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 000000002E60: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:1440                       // 000000002E68: D9FE05A0 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 000000002E70: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 000000002E78: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000002E80: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:1456                      // 000000002E88: D9FE05B0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002E90: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000002E94: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 000000002E9C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000002EA4: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 000000002EAC: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000002EB4: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 000000002EB8: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:1472                       // 000000002EC0: D9FE05C0 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 000000002EC8: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 000000002ED0: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 000000002ED8: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:1488                      // 000000002EE0: D9FE05D0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002EE8: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 000000002EEC: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 000000002EF4: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 000000002EFC: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000002F04: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 000000002F0C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000002F10: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:1504                       // 000000002F18: D9FE05E0 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 000000002F20: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 000000002F28: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 000000002F30: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:1520                      // 000000002F38: D9FE05F0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000002F40: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 000000002F44: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 000000002F4C: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 000000002F54: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 000000002F5C: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 000000002F64: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 000000002F68: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 000000002F70: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 000000002F78: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v7, v189, v16, v7                           // 000000002F80: D3A34007 1C1E21BD
	v_mul_f32_e32 v11, s9, v7                                  // 000000002F88: 0A160E09
	ds_read_b128 v[7:10], v1 offset:1536                       // 000000002F8C: D9FE0600 07000001
	ds_read_b128 v[13:16], v1 offset:1552                      // 000000002F94: D9FE0610 0D000001
	s_or_b32 s5, s4, 11                                        // 000000002F9C: 87058B04
	s_cmp_lt_i32 s5, s8                                        // 000000002FA0: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000002FA4: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 000000002FA8: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 000000002FAC: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 000000002FB4: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 000000002FBC: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 000000002FC0: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 000000002FC4: D3A34007 1C1E137F
	s_and_b64 vcc, s[18:19], s[20:21]                          // 000000002FCC: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000002FD0: D3A34007 1C1E157E
	v_cndmask_b32_e32 v19, v226, v11, vcc                      // 000000002FD8: 002617E2
	s_waitcnt lgkmcnt(0)                                       // 000000002FDC: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 000000002FE0: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:1568                       // 000000002FE8: D9FE0620 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 000000002FF0: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 000000002FF8: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000003000: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:1584                      // 000000003008: D9FE0630 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000003010: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000003014: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 00000000301C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000003024: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 00000000302C: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000003034: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 000000003038: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:1600                       // 000000003040: D9FE0640 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 000000003048: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 000000003050: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 000000003058: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:1616                      // 000000003060: D9FE0650 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000003068: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 00000000306C: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 000000003074: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 00000000307C: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000003084: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 00000000308C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000003090: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:1632                       // 000000003098: D9FE0660 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 0000000030A0: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 0000000030A8: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 0000000030B0: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:1648                      // 0000000030B8: D9FE0670 0D000001
	s_waitcnt lgkmcnt(1)                                       // 0000000030C0: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 0000000030C4: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 0000000030CC: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 0000000030D4: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 0000000030DC: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 0000000030E4: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 0000000030E8: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 0000000030F0: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 0000000030F8: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v11, v189, v16, v7                          // 000000003100: D3A3400B 1C1E21BD
	ds_read_b128 v[7:10], v1 offset:1664                       // 000000003108: D9FE0680 07000001
	ds_read_b128 v[13:16], v1 offset:1680                      // 000000003110: D9FE0690 0D000001
	s_or_b32 s5, s4, 12                                        // 000000003118: 87058C04
	s_cmp_lt_i32 s5, s8                                        // 00000000311C: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000003120: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 000000003124: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 000000003128: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 000000003130: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 000000003138: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 00000000313C: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 000000003140: D3A34007 1C1E137F
	v_mul_f32_e32 v11, s9, v11                                 // 000000003148: 0A161609
	s_and_b64 vcc, s[18:19], s[20:21]                          // 00000000314C: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000003150: D3A34007 1C1E157E
	v_cndmask_b32_e32 v21, v226, v11, vcc                      // 000000003158: 002A17E2
	s_waitcnt lgkmcnt(0)                                       // 00000000315C: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 000000003160: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:1696                       // 000000003168: D9FE06A0 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 000000003170: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 000000003178: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000003180: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:1712                      // 000000003188: D9FE06B0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000003190: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000003194: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 00000000319C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 0000000031A4: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 0000000031AC: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 0000000031B4: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 0000000031B8: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:1728                       // 0000000031C0: D9FE06C0 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 0000000031C8: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 0000000031D0: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 0000000031D8: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:1744                      // 0000000031E0: D9FE06D0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 0000000031E8: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 0000000031EC: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 0000000031F4: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 0000000031FC: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000003204: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 00000000320C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000003210: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:1760                       // 000000003218: D9FE06E0 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 000000003220: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 000000003228: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 000000003230: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:1776                      // 000000003238: D9FE06F0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000003240: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 000000003244: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 00000000324C: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 000000003254: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 00000000325C: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 000000003264: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 000000003268: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 000000003270: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 000000003278: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v7, v189, v16, v7                           // 000000003280: D3A34007 1C1E21BD
	v_mul_f32_e32 v11, s9, v7                                  // 000000003288: 0A160E09
	ds_read_b128 v[7:10], v1 offset:1792                       // 00000000328C: D9FE0700 07000001
	ds_read_b128 v[13:16], v1 offset:1808                      // 000000003294: D9FE0710 0D000001
	s_or_b32 s5, s4, 13                                        // 00000000329C: 87058D04
	s_cmp_lt_i32 s5, s8                                        // 0000000032A0: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 0000000032A4: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 0000000032A8: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 0000000032AC: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 0000000032B4: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 0000000032BC: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 0000000032C0: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 0000000032C4: D3A34007 1C1E137F
	s_and_b64 vcc, s[18:19], s[20:21]                          // 0000000032CC: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 0000000032D0: D3A34007 1C1E157E
	v_cndmask_b32_e32 v22, v226, v11, vcc                      // 0000000032D8: 002C17E2
	s_waitcnt lgkmcnt(0)                                       // 0000000032DC: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 0000000032E0: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:1824                       // 0000000032E8: D9FE0720 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 0000000032F0: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 0000000032F8: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000003300: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:1840                      // 000000003308: D9FE0730 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000003310: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000003314: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 00000000331C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 000000003324: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 00000000332C: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 000000003334: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 000000003338: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:1856                       // 000000003340: D9FE0740 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 000000003348: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 000000003350: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 000000003358: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:1872                      // 000000003360: D9FE0750 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000003368: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 00000000336C: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 000000003374: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 00000000337C: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000003384: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 00000000338C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000003390: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:1888                       // 000000003398: D9FE0760 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 0000000033A0: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 0000000033A8: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 0000000033B0: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:1904                      // 0000000033B8: D9FE0770 0D000001
	s_waitcnt lgkmcnt(1)                                       // 0000000033C0: BF8CC17F
	v_dot2_f32_f16 v7, v184, v7, v11                           // 0000000033C4: D3A34007 1C2E0FB8
	v_dot2_f32_f16 v7, v183, v8, v7                            // 0000000033CC: D3A34007 1C1E11B7
	v_dot2_f32_f16 v7, v186, v9, v7                            // 0000000033D4: D3A34007 1C1E13BA
	v_dot2_f32_f16 v7, v185, v10, v7                           // 0000000033DC: D3A34007 1C1E15B9
	s_waitcnt lgkmcnt(0)                                       // 0000000033E4: BF8CC07F
	v_dot2_f32_f16 v7, v188, v13, v7                           // 0000000033E8: D3A34007 1C1E1BBC
	v_dot2_f32_f16 v7, v187, v14, v7                           // 0000000033F0: D3A34007 1C1E1DBB
	v_dot2_f32_f16 v7, v190, v15, v7                           // 0000000033F8: D3A34007 1C1E1FBE
	v_dot2_f32_f16 v11, v189, v16, v7                          // 000000003400: D3A3400B 1C1E21BD
	ds_read_b128 v[7:10], v1 offset:1920                       // 000000003408: D9FE0780 07000001
	ds_read_b128 v[13:16], v1 offset:1936                      // 000000003410: D9FE0790 0D000001
	s_or_b32 s5, s4, 14                                        // 000000003418: 87058E04
	s_cmp_lt_i32 s5, s8                                        // 00000000341C: BF040805
	v_cmp_le_i32_e32 vcc, s5, v110                             // 000000003420: 7D86DC05
	s_waitcnt lgkmcnt(1)                                       // 000000003424: BF8CC17F
	v_dot2_f32_f16 v7, v121, v7, 0                             // 000000003428: D3A34007 1A020F79
	v_dot2_f32_f16 v7, v111, v8, v7                            // 000000003430: D3A34007 1C1E116F
	s_cselect_b64 s[18:19], -1, 0                              // 000000003438: 859280C1
	s_or_b64 s[20:21], s[6:7], vcc                             // 00000000343C: 87946A06
	v_dot2_f32_f16 v7, v127, v9, v7                            // 000000003440: D3A34007 1C1E137F
	v_mul_f32_e32 v11, s9, v11                                 // 000000003448: 0A161609
	s_and_b64 vcc, s[18:19], s[20:21]                          // 00000000344C: 86EA1412
	v_dot2_f32_f16 v7, v126, v10, v7                           // 000000003450: D3A34007 1C1E157E
	v_cndmask_b32_e32 v27, v226, v11, vcc                      // 000000003458: 003617E2
	s_waitcnt lgkmcnt(0)                                       // 00000000345C: BF8CC07F
	v_dot2_f32_f16 v11, v120, v13, v7                          // 000000003460: D3A3400B 1C1E1B78
	ds_read_b128 v[7:10], v1 offset:1952                       // 000000003468: D9FE07A0 07000001
	v_dot2_f32_f16 v11, v141, v14, v11                         // 000000003470: D3A3400B 1C2E1D8D
	v_dot2_f32_f16 v11, v143, v15, v11                         // 000000003478: D3A3400B 1C2E1F8F
	v_dot2_f32_f16 v11, v142, v16, v11                         // 000000003480: D3A3400B 1C2E218E
	ds_read_b128 v[13:16], v1 offset:1968                      // 000000003488: D9FE07B0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000003490: BF8CC17F
	v_dot2_f32_f16 v7, v140, v7, v11                           // 000000003494: D3A34007 1C2E0F8C
	v_dot2_f32_f16 v7, v147, v8, v7                            // 00000000349C: D3A34007 1C1E1193
	v_dot2_f32_f16 v7, v170, v9, v7                            // 0000000034A4: D3A34007 1C1E13AA
	v_dot2_f32_f16 v7, v169, v10, v7                           // 0000000034AC: D3A34007 1C1E15A9
	s_waitcnt lgkmcnt(0)                                       // 0000000034B4: BF8CC07F
	v_dot2_f32_f16 v11, v172, v13, v7                          // 0000000034B8: D3A3400B 1C1E1BAC
	ds_read_b128 v[7:10], v1 offset:1984                       // 0000000034C0: D9FE07C0 07000001
	v_dot2_f32_f16 v11, v171, v14, v11                         // 0000000034C8: D3A3400B 1C2E1DAB
	v_dot2_f32_f16 v11, v174, v15, v11                         // 0000000034D0: D3A3400B 1C2E1FAE
	v_dot2_f32_f16 v11, v173, v16, v11                         // 0000000034D8: D3A3400B 1C2E21AD
	ds_read_b128 v[13:16], v1 offset:2000                      // 0000000034E0: D9FE07D0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 0000000034E8: BF8CC17F
	v_dot2_f32_f16 v7, v176, v7, v11                           // 0000000034EC: D3A34007 1C2E0FB0
	v_dot2_f32_f16 v7, v175, v8, v7                            // 0000000034F4: D3A34007 1C1E11AF
	v_dot2_f32_f16 v7, v178, v9, v7                            // 0000000034FC: D3A34007 1C1E13B2
	v_dot2_f32_f16 v7, v177, v10, v7                           // 000000003504: D3A34007 1C1E15B1
	s_waitcnt lgkmcnt(0)                                       // 00000000350C: BF8CC07F
	v_dot2_f32_f16 v11, v180, v13, v7                          // 000000003510: D3A3400B 1C1E1BB4
	ds_read_b128 v[7:10], v1 offset:2016                       // 000000003518: D9FE07E0 07000001
	v_dot2_f32_f16 v11, v179, v14, v11                         // 000000003520: D3A3400B 1C2E1DB3
	v_dot2_f32_f16 v11, v182, v15, v11                         // 000000003528: D3A3400B 1C2E1FB6
	v_dot2_f32_f16 v11, v181, v16, v11                         // 000000003530: D3A3400B 1C2E21B5
	ds_read_b128 v[13:16], v1 offset:2032                      // 000000003538: D9FE07F0 0D000001
	s_waitcnt lgkmcnt(1)                                       // 000000003540: BF8CC17F
	v_dot2_f32_f16 v1, v184, v7, v11                           // 000000003544: D3A34001 1C2E0FB8
	v_dot2_f32_f16 v1, v183, v8, v1                            // 00000000354C: D3A34001 1C0611B7
	v_dot2_f32_f16 v1, v186, v9, v1                            // 000000003554: D3A34001 1C0613BA
	v_max3_f32 v3, v6, v0, v2                                  // 00000000355C: D1D30003 040A0106
	v_dot2_f32_f16 v1, v185, v10, v1                           // 000000003564: D3A34001 1C0615B9
	v_max3_f32 v3, v3, v5, v12                                 // 00000000356C: D1D30003 04320B03
	s_waitcnt lgkmcnt(0)                                       // 000000003574: BF8CC07F
	v_dot2_f32_f16 v1, v188, v13, v1                           // 000000003578: D3A34001 1C061BBC
	v_max3_f32 v3, v3, v20, v28                                // 000000003580: D1D30003 04722903
	v_dot2_f32_f16 v1, v187, v14, v1                           // 000000003588: D3A34001 1C061DBB
	s_or_b32 s17, s4, 15                                       // 000000003590: 87118F04
	v_max3_f32 v3, v3, v40, v52                                // 000000003594: D1D30003 04D25103
	v_dot2_f32_f16 v1, v190, v15, v1                           // 00000000359C: D3A34001 1C061FBE
	s_cmp_lt_i32 s17, s8                                       // 0000000035A4: BF040811
	v_cmp_le_i32_e32 vcc, s17, v110                            // 0000000035A8: 7D86DC11
	v_max3_f32 v3, v3, v85, v17                                // 0000000035AC: D1D30003 0446AB03
	v_dot2_f32_f16 v1, v189, v16, v1                           // 0000000035B4: D3A34001 1C0621BD
	s_cselect_b64 s[4:5], -1, 0                                // 0000000035BC: 858480C1
	s_or_b64 s[18:19], s[6:7], vcc                             // 0000000035C0: 87926A06
	v_max3_f32 v3, v3, v18, v19                                // 0000000035C4: D1D30003 044E2503
	v_mul_f32_e32 v1, s9, v1                                   // 0000000035CC: 0A020209
	s_and_b64 vcc, s[4:5], s[18:19]                            // 0000000035D0: 86EA1204
	v_max3_f32 v3, v3, v21, v22                                // 0000000035D4: D1D30003 045A2B03
	v_cndmask_b32_e32 v1, v226, v1, vcc                        // 0000000035DC: 000203E2
	v_max3_f32 v195, v3, v27, v1                               // 0000000035E0: D1D300C3 04063703
	v_cmp_neq_f32_e32 vcc, s15, v195                           // 0000000035E8: 7C9B860F
	s_and_saveexec_b64 s[4:5], vcc                             // 0000000035EC: BE84206A
	s_cbranch_execz 2749                                       // 0000000035F0: BF880ABD <fa_avanti+0x49e8>
	buffer_store_dword v1, off, s[24:27], 0                    // 0000000035F4: E0700000 80060100
	v_sub_f32_e32 v1, v6, v195                                 // 0000000035FC: 04038706
	v_mul_f32_e32 v1, 0x3fb8aa3b, v1                           // 000000003600: 0A0202FF 3FB8AA3B
	v_exp_f32_e32 v204, v1                                     // 000000003608: 7F984101
	buffer_store_dword v17, off, s[24:27], 0 offset:24         // 00000000360C: E0700018 80061100
	buffer_store_dword v18, off, s[24:27], 0 offset:16         // 000000003614: E0700010 80061200
	buffer_store_dword v19, off, s[24:27], 0 offset:8          // 00000000361C: E0700008 80061300
	buffer_store_dword v25, off, s[24:27], 0 offset:28         // 000000003624: E070001C 80061900
	s_nop 0                                                    // 00000000362C: BF800000
	buffer_store_dword v26, off, s[24:27], 0 offset:32         // 000000003630: E0700020 80061A00
	v_sub_f32_e32 v0, v0, v195                                 // 000000003638: 04018700
	v_mov_b32_e32 v196, s16                                    // 00000000363C: 7F880210
	buffer_store_dword v27, off, s[24:27], 0 offset:4          // 000000003640: E0700004 80061B00
	v_mul_f32_e32 v0, 0x3fb8aa3b, v0                           // 000000003648: 0A0000FF 3FB8AA3B
	ds_read_b128 v[6:9], v196 offset:8192                      // 000000003650: D9FE2000 060000C4
	ds_read_b128 v[13:16], v196 offset:8208                    // 000000003658: D9FE2010 0D0000C4
	buffer_store_dword v23, off, s[24:27], 0 offset:36         // 000000003660: E0700024 80061700
	s_nop 0                                                    // 000000003668: BF800000
	buffer_store_dword v24, off, s[24:27], 0 offset:40         // 00000000366C: E0700028 80061800
	buffer_store_dword v21, off, s[24:27], 0 offset:20         // 000000003674: E0700014 80061500
	buffer_store_dword v22, off, s[24:27], 0 offset:12         // 00000000367C: E070000C 80061600
	v_mul_f32_e32 v35, v204, v144                              // 000000003684: 0A4721CC
	v_exp_f32_e32 v144, v0                                     // 000000003688: 7F204100
	ds_read_b128 v[21:24], v196 offset:8224                    // 00000000368C: D9FE2020 150000C4
	ds_read_b128 v[81:84], v196 offset:8240                    // 000000003694: D9FE2030 510000C4
	v_sub_f32_e32 v0, v2, v195                                 // 00000000369C: 04018702
	v_mul_f32_e32 v0, 0x3fb8aa3b, v0                           // 0000000036A0: 0A0000FF 3FB8AA3B
	v_mul_f32_e32 v1, v204, v236                               // 0000000036A8: 0A03D9CC
	v_mul_f32_e32 v3, v204, v237                               // 0000000036AC: 0A07DBCC
	v_mul_f32_e32 v10, v204, v248                              // 0000000036B0: 0A15F1CC
	v_mul_f32_e32 v11, v204, v249                              // 0000000036B4: 0A17F3CC
	v_mul_f32_e32 v17, v204, v246                              // 0000000036B8: 0A23EDCC
	v_mul_f32_e32 v18, v204, v247                              // 0000000036BC: 0A25EFCC
	v_mul_f32_e32 v19, v204, v254                              // 0000000036C0: 0A27FDCC
	v_mul_f32_e32 v25, v204, v255                              // 0000000036C4: 0A33FFCC
	v_mul_f32_e32 v26, v204, v96                               // 0000000036C8: 0A34C1CC
	v_mul_f32_e32 v27, v204, v97                               // 0000000036CC: 0A36C3CC
	v_mul_f32_e32 v29, v204, v98                               // 0000000036D0: 0A3AC5CC
	v_mul_f32_e32 v30, v204, v99                               // 0000000036D4: 0A3CC7CC
	v_mul_f32_e32 v31, v204, v100                              // 0000000036D8: 0A3EC9CC
	v_mul_f32_e32 v32, v204, v101                              // 0000000036DC: 0A40CBCC
	v_mul_f32_e32 v33, v204, v102                              // 0000000036E0: 0A42CDCC
	v_mul_f32_e32 v34, v204, v103                              // 0000000036E4: 0A44CFCC
	v_mul_f32_e32 v36, v204, v145                              // 0000000036E8: 0A4923CC
	v_exp_f32_e32 v145, v0                                     // 0000000036EC: 7F224100
	s_waitcnt lgkmcnt(3)                                       // 0000000036F0: BF8CC37F
	v_fma_mix_f32 v50, v144, v6, v1 op_sel_hi:[0,1,0]          // 0000000036F4: D3A00032 14060D90
	v_fma_mix_f32 v6, v144, v6, v3 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000036FC: D3A01006 140E0D90
	v_fma_mix_f32 v51, v144, v7, v10 op_sel_hi:[0,1,0]         // 000000003704: D3A00033 142A0F90
	v_fma_mix_f32 v7, v144, v7, v11 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000370C: D3A01007 142E0F90
	v_fma_mix_f32 v17, v144, v8, v17 op_sel_hi:[0,1,0]         // 000000003714: D3A00011 14461190
	v_fma_mix_f32 v18, v144, v8, v18 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000371C: D3A01012 144A1190
	v_fma_mix_f32 v19, v144, v9, v19 op_sel_hi:[0,1,0]         // 000000003724: D3A00013 144E1390
	v_fma_mix_f32 v25, v144, v9, v25 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000372C: D3A01019 14661390
	s_waitcnt lgkmcnt(2)                                       // 000000003734: BF8CC27F
	v_fma_mix_f32 v26, v144, v13, v26 op_sel_hi:[0,1,0]        // 000000003738: D3A0001A 146A1B90
	v_fma_mix_f32 v27, v144, v13, v27 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003740: D3A0101B 146E1B90
	v_fma_mix_f32 v29, v144, v14, v29 op_sel_hi:[0,1,0]        // 000000003748: D3A0001D 14761D90
	v_fma_mix_f32 v30, v144, v14, v30 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003750: D3A0101E 147A1D90
	v_fma_mix_f32 v31, v144, v15, v31 op_sel_hi:[0,1,0]        // 000000003758: D3A0001F 147E1F90
	v_fma_mix_f32 v53, v144, v15, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003760: D3A01035 14821F90
	v_fma_mix_f32 v54, v144, v16, v33 op_sel_hi:[0,1,0]        // 000000003768: D3A00036 14862190
	v_fma_mix_f32 v55, v144, v16, v34 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003770: D3A01037 148A2190
	s_waitcnt lgkmcnt(1)                                       // 000000003778: BF8CC17F
	v_fma_mix_f32 v60, v144, v21, v35 op_sel_hi:[0,1,0]        // 00000000377C: D3A0003C 148E2B90
	ds_read_b128 v[56:59], v196 offset:8256                    // 000000003784: D9FE2040 380000C4
	ds_read_b128 v[32:35], v196 offset:8272                    // 00000000378C: D9FE2050 200000C4
	ds_read_b128 v[13:16], v196 offset:8320                    // 000000003794: D9FE2080 0D0000C4
	ds_read_b128 v[8:11], v196 offset:8288                     // 00000000379C: D9FE2060 080000C4
	ds_read_b128 v[0:3], v196 offset:8304                      // 0000000037A4: D9FE2070 000000C4
	v_mul_f32_e32 v37, v204, v106                              // 0000000037AC: 0A4AD5CC
	v_mul_f32_e32 v38, v204, v107                              // 0000000037B0: 0A4CD7CC
	v_mul_f32_e32 v39, v204, v148                              // 0000000037B4: 0A4F29CC
	v_mul_f32_e32 v41, v204, v149                              // 0000000037B8: 0A532BCC
	v_mul_f32_e32 v42, v204, v152                              // 0000000037BC: 0A5531CC
	v_mul_f32_e32 v43, v204, v153                              // 0000000037C0: 0A5733CC
	v_mov_b32_e32 v202, v63                                    // 0000000037C4: 7F94033F
	v_fma_mix_f32 v36, v144, v21, v36 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000037C8: D3A01024 14922B90
	v_fma_mix_f32 v37, v144, v22, v37 op_sel_hi:[0,1,0]        // 0000000037D0: D3A00025 14962D90
	v_fma_mix_f32 v38, v144, v22, v38 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000037D8: D3A01026 149A2D90
	v_fma_mix_f32 v39, v144, v23, v39 op_sel_hi:[0,1,0]        // 0000000037E0: D3A00027 149E2F90
	v_fma_mix_f32 v41, v144, v23, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000037E8: D3A01029 14A62F90
	v_fma_mix_f32 v42, v144, v24, v42 op_sel_hi:[0,1,0]        // 0000000037F0: D3A0002A 14AA3190
	v_fma_mix_f32 v43, v144, v24, v43 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000037F8: D3A0102B 14AE3190
	ds_read_b128 v[21:24], v196 offset:8336                    // 000000003800: D9FE2090 150000C4
	v_mov_b32_e32 v201, v62                                    // 000000003808: 7F92033E
	s_waitcnt lgkmcnt(3)                                       // 00000000380C: BF8CC37F
	v_fma_mix_f32 v62, v145, v13, v6 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003810: D3A0103E 141A1B91
	v_fma_mix_f32 v50, v145, v13, v50 op_sel_hi:[0,1,0]        // 000000003818: D3A00032 14CA1B91
	v_fma_mix_f32 v63, v145, v14, v7 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003820: D3A0103F 141E1D91
	v_fma_mix_f32 v51, v145, v14, v51 op_sel_hi:[0,1,0]        // 000000003828: D3A00033 14CE1D91
	v_fma_mix_f32 v64, v145, v15, v18 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003830: D3A01040 144A1F91
	v_fma_mix_f32 v65, v145, v15, v17 op_sel_hi:[0,1,0]        // 000000003838: D3A00041 14461F91
	v_fma_mix_f32 v25, v145, v16, v25 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003840: D3A01019 14662191
	v_fma_mix_f32 v66, v145, v16, v19 op_sel_hi:[0,1,0]        // 000000003848: D3A00042 144E2191
	ds_read_b128 v[13:16], v196 offset:8352                    // 000000003850: D9FE20A0 0D0000C4
	ds_read_b128 v[228:231], v196 offset:8368                  // 000000003858: D9FE20B0 E40000C4
	v_fma_f32 v61, v4, v204, v144                              // 000000003860: D1CB003D 06439904
	v_sub_f32_e32 v4, v5, v195                                 // 000000003868: 04098705
	v_mul_f32_e32 v44, v204, v150                              // 00000000386C: 0A592DCC
	v_mul_f32_e32 v45, v204, v151                              // 000000003870: 0A5B2FCC
	v_mul_f32_e32 v46, v204, v154                              // 000000003874: 0A5D35CC
	v_mul_f32_e32 v47, v204, v155                              // 000000003878: 0A5F37CC
	v_mul_f32_e32 v4, 0x3fb8aa3b, v4                           // 00000000387C: 0A0808FF 3FB8AA3B
	v_fma_mix_f32 v44, v144, v81, v44 op_sel_hi:[0,1,0]        // 000000003884: D3A0002C 14B2A390
	v_fma_mix_f32 v45, v144, v81, v45 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000388C: D3A0102D 14B6A390
	v_fma_mix_f32 v46, v144, v82, v46 op_sel_hi:[0,1,0]        // 000000003894: D3A0002E 14BAA590
	v_fma_mix_f32 v47, v144, v82, v47 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000389C: D3A0102F 14BEA590
	v_exp_f32_e32 v146, v4                                     // 0000000038A4: 7F244104
	s_waitcnt lgkmcnt(2)                                       // 0000000038A8: BF8CC27F
	v_fma_mix_f32 v27, v145, v21, v27 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000038AC: D3A0101B 146E2B91
	v_fma_mix_f32 v26, v145, v21, v26 op_sel_hi:[0,1,0]        // 0000000038B4: D3A0001A 146A2B91
	v_fma_mix_f32 v30, v145, v22, v30 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000038BC: D3A0101E 147A2D91
	v_fma_mix_f32 v29, v145, v22, v29 op_sel_hi:[0,1,0]        // 0000000038C4: D3A0001D 14762D91
	v_fma_mix_f32 v53, v145, v23, v53 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000038CC: D3A01035 14D62F91
	v_fma_mix_f32 v31, v145, v23, v31 op_sel_hi:[0,1,0]        // 0000000038D4: D3A0001F 147E2F91
	v_fma_mix_f32 v55, v145, v24, v55 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000038DC: D3A01037 14DE3191
	v_fma_mix_f32 v54, v145, v24, v54 op_sel_hi:[0,1,0]        // 0000000038E4: D3A00036 14DA3191
	s_waitcnt lgkmcnt(1)                                       // 0000000038EC: BF8CC17F
	v_fma_mix_f32 v43, v145, v16, v43 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000038F0: D3A0102B 14AE2191
	v_fma_mix_f32 v42, v145, v16, v42 op_sel_hi:[0,1,0]        // 0000000038F8: D3A0002A 14AA2191
	s_waitcnt lgkmcnt(0)                                       // 000000003900: BF8CC07F
	v_fma_mix_f32 v72, v145, v228, v45 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003904: D3A01048 14B7C991
	v_fma_mix_f32 v73, v145, v228, v44 op_sel_hi:[0,1,0]       // 00000000390C: D3A00049 14B3C991
	v_fma_mix_f32 v74, v145, v229, v47 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003914: D3A0104A 14BFCB91
	v_fma_mix_f32 v75, v145, v229, v46 op_sel_hi:[0,1,0]       // 00000000391C: D3A0004B 14BBCB91
	ds_read_b128 v[68:71], v196 offset:8384                    // 000000003924: D9FE20C0 440000C4
	ds_read_b128 v[44:47], v196 offset:8400                    // 00000000392C: D9FE20D0 2C0000C4
	ds_read_b128 v[21:24], v196 offset:8448                    // 000000003934: D9FE2100 150000C4
	ds_read_b128 v[16:19], v196 offset:8416                    // 00000000393C: D9FE20E0 100000C4
	ds_read_b128 v[4:7], v196 offset:8432                      // 000000003944: D9FE20F0 040000C4
	v_fma_mix_f32 v67, v145, v13, v36 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000394C: D3A01043 14921B91
	v_fma_mix_f32 v13, v145, v13, v60 op_sel_hi:[0,1,0]        // 000000003954: D3A0000D 14F21B91
	v_fma_mix_f32 v60, v145, v14, v38 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000395C: D3A0103C 149A1D91
	v_fma_mix_f32 v14, v145, v14, v37 op_sel_hi:[0,1,0]        // 000000003964: D3A0000E 14961D91
	v_fma_mix_f32 v41, v145, v15, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000396C: D3A01029 14A61F91
	v_fma_mix_f32 v15, v145, v15, v39 op_sel_hi:[0,1,0]        // 000000003974: D3A0000F 149E1F91
	ds_read_b128 v[36:39], v196 offset:8464                    // 00000000397C: D9FE2110 240000C4
	s_waitcnt lgkmcnt(3)                                       // 000000003984: BF8CC37F
	v_fma_mix_f32 v76, v146, v21, v50 op_sel_hi:[0,1,0]        // 000000003988: D3A0004C 14CA2B92
	v_fma_mix_f32 v77, v146, v21, v62 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003990: D3A0104D 14FA2B92
	v_fma_mix_f32 v78, v146, v22, v51 op_sel_hi:[0,1,0]        // 000000003998: D3A0004E 14CE2D92
	v_fma_mix_f32 v79, v146, v22, v63 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000039A0: D3A0104F 14FE2D92
	v_fma_mix_f32 v65, v146, v23, v65 op_sel_hi:[0,1,0]        // 0000000039A8: D3A00041 15062F92
	v_fma_mix_f32 v64, v146, v23, v64 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000039B0: D3A01040 15022F92
	v_fma_mix_f32 v66, v146, v24, v66 op_sel_hi:[0,1,0]        // 0000000039B8: D3A00042 150A3192
	v_fma_mix_f32 v86, v146, v24, v25 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000039C0: D3A01056 14663192
	ds_read_b128 v[21:24], v196 offset:8480                    // 0000000039C8: D9FE2120 150000C4
	v_sub_f32_e32 v12, v12, v195                               // 0000000039D0: 0419870C
	v_mul_f32_e32 v48, v204, v156                              // 0000000039D4: 0A6139CC
	v_mul_f32_e32 v12, 0x3fb8aa3b, v12                         // 0000000039D8: 0A1818FF 3FB8AA3B
	v_mul_f32_e32 v49, v204, v157                              // 0000000039E0: 0A633BCC
	v_fma_mix_f32 v48, v144, v83, v48 op_sel_hi:[0,1,0]        // 0000000039E4: D3A00030 14C2A790
	v_exp_f32_e32 v157, v12                                    // 0000000039EC: 7F3A410C
	v_fma_mix_f32 v49, v144, v83, v49 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000039F0: D3A01031 14C6A790
	v_fma_mix_f32 v203, v145, v230, v48 op_sel_hi:[0,1,0]      // 0000000039F8: D3A000CB 14C3CD91
	v_add_f32_e32 v48, v61, v145                               // 000000003A00: 0261233D
	s_waitcnt lgkmcnt(1)                                       // 000000003A04: BF8CC17F
	v_fma_mix_f32 v87, v146, v36, v26 op_sel_hi:[0,1,0]        // 000000003A08: D3A00057 146A4992
	v_fma_mix_f32 v88, v146, v36, v27 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003A10: D3A01058 146E4992
	v_fma_mix_f32 v29, v146, v37, v29 op_sel_hi:[0,1,0]        // 000000003A18: D3A0001D 14764B92
	v_fma_mix_f32 v30, v146, v37, v30 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003A20: D3A0101E 147A4B92
	v_fma_mix_f32 v31, v146, v38, v31 op_sel_hi:[0,1,0]        // 000000003A28: D3A0001F 147E4D92
	v_fma_mix_f32 v53, v146, v38, v53 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003A30: D3A01035 14D64D92
	v_fma_mix_f32 v54, v146, v39, v54 op_sel_hi:[0,1,0]        // 000000003A38: D3A00036 14DA4F92
	v_fma_mix_f32 v55, v146, v39, v55 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003A40: D3A01037 14DE4F92
	ds_read_b128 v[232:235], v196 offset:8496                  // 000000003A48: D9FE2130 E80000C4
	s_waitcnt lgkmcnt(1)                                       // 000000003A50: BF8CC17F
	v_fma_mix_f32 v89, v146, v21, v13 op_sel_hi:[0,1,0]        // 000000003A54: D3A00059 14362B92
	v_fma_mix_f32 v21, v146, v21, v67 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003A5C: D3A01015 150E2B92
	v_fma_mix_f32 v67, v146, v22, v14 op_sel_hi:[0,1,0]        // 000000003A64: D3A00043 143A2D92
	v_fma_mix_f32 v22, v146, v22, v60 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003A6C: D3A01016 14F22D92
	v_fma_mix_f32 v90, v146, v23, v15 op_sel_hi:[0,1,0]        // 000000003A74: D3A0005A 143E2F92
	v_fma_mix_f32 v23, v146, v23, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003A7C: D3A01017 14A62F92
	v_fma_mix_f32 v41, v146, v24, v42 op_sel_hi:[0,1,0]        // 000000003A84: D3A00029 14AA3192
	v_fma_mix_f32 v42, v146, v24, v43 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003A8C: D3A0102A 14AE3192
	ds_read_b128 v[80:83], v196 offset:8512                    // 000000003A94: D9FE2140 500000C4
	ds_read_b128 v[60:63], v196 offset:8528                    // 000000003A9C: D9FE2150 3C0000C4
	ds_read_b128 v[36:39], v196 offset:8576                    // 000000003AA4: D9FE2180 240000C4
	ds_read_b128 v[24:27], v196 offset:8544                    // 000000003AAC: D9FE2160 180000C4
	ds_read_b128 v[12:15], v196 offset:8560                    // 000000003AB4: D9FE2170 0C0000C4
	v_fma_mix_f32 v225, v145, v230, v49 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003ABC: D3A010E1 14C7CD91
	v_add_f32_e32 v91, v48, v146                               // 000000003AC4: 02B72530
	ds_read_b128 v[48:51], v196 offset:8592                    // 000000003AC8: D9FE2190 300000C4
	s_waitcnt lgkmcnt(3)                                       // 000000003AD0: BF8CC37F
	v_fma_mix_f32 v77, v157, v36, v77 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003AD4: D3A0104D 1536499D
	v_fma_mix_f32 v76, v157, v36, v76 op_sel_hi:[0,1,0]        // 000000003ADC: D3A0004C 1532499D
	v_fma_mix_f32 v79, v157, v37, v79 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003AE4: D3A0104F 153E4B9D
	v_fma_mix_f32 v78, v157, v37, v78 op_sel_hi:[0,1,0]        // 000000003AEC: D3A0004E 153A4B9D
	v_fma_mix_f32 v96, v157, v38, v64 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003AF4: D3A01060 15024D9D
	v_fma_mix_f32 v97, v157, v38, v65 op_sel_hi:[0,1,0]        // 000000003AFC: D3A00061 15064D9D
	v_fma_mix_f32 v86, v157, v39, v86 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003B04: D3A01056 155A4F9D
	v_fma_mix_f32 v98, v157, v39, v66 op_sel_hi:[0,1,0]        // 000000003B0C: D3A00062 150A4F9D
	ds_read_b128 v[36:39], v196 offset:8608                    // 000000003B14: D9FE21A0 240000C4
	ds_read_b128 v[236:239], v196 offset:8624                  // 000000003B1C: D9FE21B0 EC0000C4
	v_sub_f32_e32 v20, v20, v195                               // 000000003B24: 04298714
	v_mul_f32_e32 v20, 0x3fb8aa3b, v20                         // 000000003B28: 0A2828FF 3FB8AA3B
	v_fma_mix_f32 v43, v146, v232, v73 op_sel_hi:[0,1,0]       // 000000003B30: D3A0002B 1527D192
	v_fma_mix_f32 v72, v146, v232, v72 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003B38: D3A01048 1523D192
	v_fma_mix_f32 v73, v146, v233, v75 op_sel_hi:[0,1,0]       // 000000003B40: D3A00049 152FD392
	v_fma_mix_f32 v74, v146, v233, v74 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003B48: D3A0104A 152BD392
	v_exp_f32_e32 v209, v20                                    // 000000003B50: 7FA24114
	s_waitcnt lgkmcnt(2)                                       // 000000003B54: BF8CC27F
	v_fma_mix_f32 v88, v157, v48, v88 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003B58: D3A01058 1562619D
	v_fma_mix_f32 v87, v157, v48, v87 op_sel_hi:[0,1,0]        // 000000003B60: D3A00057 155E619D
	v_fma_mix_f32 v30, v157, v49, v30 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003B68: D3A0101E 147A639D
	v_fma_mix_f32 v29, v157, v49, v29 op_sel_hi:[0,1,0]        // 000000003B70: D3A0001D 1476639D
	v_fma_mix_f32 v53, v157, v50, v53 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003B78: D3A01035 14D6659D
	v_fma_mix_f32 v31, v157, v50, v31 op_sel_hi:[0,1,0]        // 000000003B80: D3A0001F 147E659D
	v_fma_mix_f32 v55, v157, v51, v55 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003B88: D3A01037 14DE679D
	v_fma_mix_f32 v54, v157, v51, v54 op_sel_hi:[0,1,0]        // 000000003B90: D3A00036 14DA679D
	s_waitcnt lgkmcnt(1)                                       // 000000003B98: BF8CC17F
	v_fma_mix_f32 v99, v157, v36, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003B9C: D3A01063 1456499D
	v_fma_mix_f32 v89, v157, v36, v89 op_sel_hi:[0,1,0]        // 000000003BA4: D3A00059 1566499D
	v_fma_mix_f32 v100, v157, v37, v22 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003BAC: D3A01064 145A4B9D
	v_fma_mix_f32 v101, v157, v37, v67 op_sel_hi:[0,1,0]       // 000000003BB4: D3A00065 150E4B9D
	v_fma_mix_f32 v102, v157, v38, v23 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003BBC: D3A01066 145E4D9D
	v_fma_mix_f32 v90, v157, v38, v90 op_sel_hi:[0,1,0]        // 000000003BC4: D3A0005A 156A4D9D
	v_fma_mix_f32 v42, v157, v39, v42 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003BCC: D3A0102A 14AA4F9D
	v_fma_mix_f32 v41, v157, v39, v41 op_sel_hi:[0,1,0]        // 000000003BD4: D3A00029 14A64F9D
	s_waitcnt lgkmcnt(0)                                       // 000000003BDC: BF8CC07F
	v_fma_mix_f32 v103, v157, v236, v72 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003BE0: D3A01067 1523D99D
	v_fma_mix_f32 v104, v157, v237, v74 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003BE8: D3A01068 152BDB9D
	v_fma_mix_f32 v105, v157, v237, v73 op_sel_hi:[0,1,0]      // 000000003BF0: D3A00069 1527DB9D
	ds_read_b128 v[92:95], v196 offset:8640                    // 000000003BF8: D9FE21C0 5C0000C4
	ds_read_b128 v[72:75], v196 offset:8656                    // 000000003C00: D9FE21D0 480000C4
	ds_read_b128 v[48:51], v196 offset:8704                    // 000000003C08: D9FE2200 300000C4
	ds_read_b128 v[36:39], v196 offset:8672                    // 000000003C10: D9FE21E0 240000C4
	ds_read_b128 v[20:23], v196 offset:8688                    // 000000003C18: D9FE21F0 140000C4
	ds_read_b128 v[64:67], v196 offset:8720                    // 000000003C20: D9FE2210 400000C4
	v_sub_f32_e32 v28, v28, v195                               // 000000003C28: 0439871C
	s_waitcnt lgkmcnt(3)                                       // 000000003C2C: BF8CC37F
	v_fma_mix_f32 v107, v209, v48, v76 op_sel_hi:[0,1,0]       // 000000003C30: D3A0006B 153261D1
	v_fma_mix_f32 v112, v209, v48, v77 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003C38: D3A01070 153661D1
	v_fma_mix_f32 v113, v209, v49, v78 op_sel_hi:[0,1,0]       // 000000003C40: D3A00071 153A63D1
	v_fma_mix_f32 v114, v209, v49, v79 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003C48: D3A01072 153E63D1
	v_fma_mix_f32 v97, v209, v50, v97 op_sel_hi:[0,1,0]        // 000000003C50: D3A00061 158665D1
	v_fma_mix_f32 v96, v209, v50, v96 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003C58: D3A01060 158265D1
	v_fma_mix_f32 v98, v209, v51, v98 op_sel_hi:[0,1,0]        // 000000003C60: D3A00062 158A67D1
	v_fma_mix_f32 v86, v209, v51, v86 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003C68: D3A01056 155A67D1
	ds_read_b128 v[48:51], v196 offset:8736                    // 000000003C70: D9FE2220 300000C4
	v_mul_f32_e32 v28, 0x3fb8aa3b, v28                         // 000000003C78: 0A3838FF 3FB8AA3B
	v_exp_f32_e32 v218, v28                                    // 000000003C80: 7FB4411C
	v_add_f32_e32 v106, v91, v157                              // 000000003C84: 02D53B5B
	s_waitcnt lgkmcnt(1)                                       // 000000003C88: BF8CC17F
	v_fma_mix_f32 v87, v209, v64, v87 op_sel_hi:[0,1,0]        // 000000003C8C: D3A00057 155E81D1
	v_fma_mix_f32 v115, v209, v64, v88 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003C94: D3A01073 156281D1
	v_fma_mix_f32 v148, v209, v65, v29 op_sel_hi:[0,1,0]       // 000000003C9C: D3A00094 147683D1
	v_fma_mix_f32 v149, v209, v65, v30 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003CA4: D3A01095 147A83D1
	v_fma_mix_f32 v150, v209, v66, v31 op_sel_hi:[0,1,0]       // 000000003CAC: D3A00096 147E85D1
	v_fma_mix_f32 v53, v209, v66, v53 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003CB4: D3A01035 14D685D1
	v_fma_mix_f32 v54, v209, v67, v54 op_sel_hi:[0,1,0]        // 000000003CBC: D3A00036 14DA87D1
	v_fma_mix_f32 v55, v209, v67, v55 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003CC4: D3A01037 14DE87D1
	ds_read_b128 v[240:243], v196 offset:8752                  // 000000003CCC: D9FE2230 F00000C4
	s_waitcnt lgkmcnt(1)                                       // 000000003CD4: BF8CC17F
	v_fma_mix_f32 v151, v209, v48, v89 op_sel_hi:[0,1,0]       // 000000003CD8: D3A00097 156661D1
	v_fma_mix_f32 v99, v209, v48, v99 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003CE0: D3A01063 158E61D1
	v_fma_mix_f32 v101, v209, v49, v101 op_sel_hi:[0,1,0]      // 000000003CE8: D3A00065 159663D1
	v_fma_mix_f32 v100, v209, v49, v100 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003CF0: D3A01064 159263D1
	v_fma_mix_f32 v152, v209, v50, v90 op_sel_hi:[0,1,0]       // 000000003CF8: D3A00098 156A65D1
	v_fma_mix_f32 v102, v209, v50, v102 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003D00: D3A01066 159A65D1
	v_fma_mix_f32 v41, v209, v51, v41 op_sel_hi:[0,1,0]        // 000000003D08: D3A00029 14A667D1
	v_fma_mix_f32 v42, v209, v51, v42 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003D10: D3A0102A 14AA67D1
	ds_read_b128 v[244:247], v196 offset:8768                  // 000000003D18: D9FE2240 F40000C4
	ds_read_b128 v[88:91], v196 offset:8784                    // 000000003D20: D9FE2250 580000C4
	ds_read_b128 v[64:67], v196 offset:8832                    // 000000003D28: D9FE2280 400000C4
	ds_read_b128 v[48:51], v196 offset:8800                    // 000000003D30: D9FE2260 300000C4
	ds_read_b128 v[28:31], v196 offset:8816                    // 000000003D38: D9FE2270 1C0000C4
	ds_read_b128 v[76:79], v196 offset:8848                    // 000000003D40: D9FE2290 4C0000C4
	ds_read_b128 v[248:251], v196 offset:8880                  // 000000003D48: D9FE22B0 F80000C4
	s_waitcnt lgkmcnt(4)                                       // 000000003D50: BF8CC47F
	v_fma_mix_f32 v112, v218, v64, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003D54: D3A01070 15C281DA
	v_fma_mix_f32 v107, v218, v64, v107 op_sel_hi:[0,1,0]      // 000000003D5C: D3A0006B 15AE81DA
	v_fma_mix_f32 v114, v218, v65, v114 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003D64: D3A01072 15CA83DA
	v_fma_mix_f32 v113, v218, v65, v113 op_sel_hi:[0,1,0]      // 000000003D6C: D3A00071 15C683DA
	v_fma_mix_f32 v153, v218, v66, v96 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003D74: D3A01099 158285DA
	v_fma_mix_f32 v154, v218, v66, v97 op_sel_hi:[0,1,0]       // 000000003D7C: D3A0009A 158685DA
	v_fma_mix_f32 v86, v218, v67, v86 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003D84: D3A01056 155A87DA
	v_fma_mix_f32 v155, v218, v67, v98 op_sel_hi:[0,1,0]       // 000000003D8C: D3A0009B 158A87DA
	ds_read_b128 v[64:67], v196 offset:8864                    // 000000003D94: D9FE22A0 400000C4
	v_sub_f32_e32 v40, v40, v195                               // 000000003D9C: 04518728
	v_fma_mix_f32 v43, v157, v236, v43 op_sel_hi:[0,1,0]       // 000000003DA0: D3A0002B 14AFD99D
	v_mul_f32_e32 v40, 0x3fb8aa3b, v40                         // 000000003DA8: 0A5050FF 3FB8AA3B
	v_fma_mix_f32 v43, v209, v240, v43 op_sel_hi:[0,1,0]       // 000000003DB0: D3A0002B 14AFE1D1
	v_fma_mix_f32 v103, v209, v240, v103 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003DB8: D3A01067 159FE1D1
	v_exp_f32_e32 v219, v40                                    // 000000003DC0: 7FB64128
	s_waitcnt lgkmcnt(2)                                       // 000000003DC4: BF8CC27F
	v_fma_mix_f32 v115, v218, v76, v115 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003DC8: D3A01073 15CE99DA
	v_fma_mix_f32 v87, v218, v76, v87 op_sel_hi:[0,1,0]        // 000000003DD0: D3A00057 155E99DA
	v_fma_mix_f32 v149, v218, v77, v149 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003DD8: D3A01095 16569BDA
	v_fma_mix_f32 v148, v218, v77, v148 op_sel_hi:[0,1,0]      // 000000003DE0: D3A00094 16529BDA
	v_fma_mix_f32 v53, v218, v78, v53 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003DE8: D3A01035 14D69DDA
	v_fma_mix_f32 v150, v218, v78, v150 op_sel_hi:[0,1,0]      // 000000003DF0: D3A00096 165A9DDA
	v_fma_mix_f32 v55, v218, v79, v55 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003DF8: D3A01037 14DE9FDA
	v_fma_mix_f32 v54, v218, v79, v54 op_sel_hi:[0,1,0]        // 000000003E00: D3A00036 14DA9FDA
	s_waitcnt lgkmcnt(0)                                       // 000000003E08: BF8CC07F
	v_fma_mix_f32 v156, v218, v64, v99 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003E0C: D3A0109C 158E81DA
	v_fma_mix_f32 v151, v218, v64, v151 op_sel_hi:[0,1,0]      // 000000003E14: D3A00097 165E81DA
	v_fma_mix_f32 v166, v218, v65, v100 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003E1C: D3A010A6 159283DA
	v_fma_mix_f32 v167, v218, v65, v101 op_sel_hi:[0,1,0]      // 000000003E24: D3A000A7 159683DA
	v_fma_mix_f32 v168, v218, v66, v102 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003E2C: D3A010A8 159A85DA
	v_fma_mix_f32 v152, v218, v66, v152 op_sel_hi:[0,1,0]      // 000000003E34: D3A00098 166285DA
	v_fma_mix_f32 v197, v218, v67, v42 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003E3C: D3A010C5 14AA87DA
	v_fma_mix_f32 v198, v218, v67, v41 op_sel_hi:[0,1,0]       // 000000003E44: D3A000C6 14A687DA
	v_fma_mix_f32 v199, v218, v248, v103 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003E4C: D3A010C7 159FF1DA
	v_fma_mix_f32 v200, v218, v248, v43 op_sel_hi:[0,1,0]      // 000000003E54: D3A000C8 14AFF1DA
	ds_read_b128 v[252:255], v196 offset:8896                  // 000000003E5C: D9FE22C0 FC0000C4
	ds_read_b128 v[100:103], v196 offset:8912                  // 000000003E64: D9FE22D0 640000C4
	ds_read_b128 v[76:79], v196 offset:8960                    // 000000003E6C: D9FE2300 4C0000C4
	ds_read_b128 v[64:67], v196 offset:8928                    // 000000003E74: D9FE22E0 400000C4
	ds_read_b128 v[40:43], v196 offset:8944                    // 000000003E7C: D9FE22F0 280000C4
	v_fma_mix_f32 v105, v209, v241, v105 op_sel_hi:[0,1,0]     // 000000003E84: D3A00069 15A7E3D1
	v_fma_mix_f32 v104, v209, v241, v104 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003E8C: D3A01068 15A3E3D1
	v_add_f32_e32 v106, v106, v209                             // 000000003E94: 02D5A36A
	v_fma_mix_f32 v205, v218, v249, v104 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003E98: D3A010CD 15A3F3DA
	v_fma_mix_f32 v206, v218, v249, v105 op_sel_hi:[0,1,0]     // 000000003EA0: D3A000CE 15A7F3DA
	v_add_f32_e32 v207, v106, v218                             // 000000003EA8: 039FB56A
	ds_read_b128 v[96:99], v196 offset:8976                    // 000000003EAC: D9FE2310 600000C4
	s_waitcnt lgkmcnt(3)                                       // 000000003EB4: BF8CC37F
	v_fma_mix_f32 v210, v219, v76, v107 op_sel_hi:[0,1,0]      // 000000003EB8: D3A000D2 15AE99DB
	v_fma_mix_f32 v112, v219, v76, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003EC0: D3A01070 15C299DB
	v_fma_mix_f32 v113, v219, v77, v113 op_sel_hi:[0,1,0]      // 000000003EC8: D3A00071 15C69BDB
	v_fma_mix_f32 v114, v219, v77, v114 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003ED0: D3A01072 15CA9BDB
	v_fma_mix_f32 v211, v219, v78, v154 op_sel_hi:[0,1,0]      // 000000003ED8: D3A000D3 166A9DDB
	v_fma_mix_f32 v212, v219, v78, v153 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003EE0: D3A010D4 16669DDB
	v_fma_mix_f32 v213, v219, v79, v155 op_sel_hi:[0,1,0]      // 000000003EE8: D3A000D5 166E9FDB
	v_fma_mix_f32 v86, v219, v79, v86 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003EF0: D3A01056 155A9FDB
	ds_read_b128 v[76:79], v196 offset:8992                    // 000000003EF8: D9FE2320 4C0000C4
	ds_read_b128 v[104:107], v196 offset:9008                  // 000000003F00: D9FE2330 680000C4
	v_sub_f32_e32 v52, v52, v195                               // 000000003F08: 04698734
	v_mul_f32_e32 v52, 0x3fb8aa3b, v52                         // 000000003F0C: 0A6868FF 3FB8AA3B
	s_waitcnt lgkmcnt(2)                                       // 000000003F14: BF8CC27F
	v_fma_mix_f32 v87, v219, v96, v87 op_sel_hi:[0,1,0]        // 000000003F18: D3A00057 155EC1DB
	v_fma_mix_f32 v115, v219, v96, v115 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003F20: D3A01073 15CEC1DB
	v_fma_mix_f32 v214, v219, v97, v148 op_sel_hi:[0,1,0]      // 000000003F28: D3A000D6 1652C3DB
	v_fma_mix_f32 v215, v219, v97, v149 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003F30: D3A010D7 1656C3DB
	v_fma_mix_f32 v216, v219, v98, v150 op_sel_hi:[0,1,0]      // 000000003F38: D3A000D8 165AC5DB
	v_fma_mix_f32 v217, v219, v98, v53 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003F40: D3A010D9 14D6C5DB
	v_fma_mix_f32 v220, v219, v99, v54 op_sel_hi:[0,1,0]       // 000000003F48: D3A000DC 14DAC7DB
	v_fma_mix_f32 v221, v219, v99, v55 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003F50: D3A010DD 14DEC7DB
	s_waitcnt lgkmcnt(1)                                       // 000000003F58: BF8CC17F
	v_fma_mix_f32 v222, v219, v76, v151 op_sel_hi:[0,1,0]      // 000000003F5C: D3A000DE 165E99DB
	v_fma_mix_f32 v156, v219, v76, v156 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003F64: D3A0109C 167299DB
	v_fma_mix_f32 v167, v219, v77, v167 op_sel_hi:[0,1,0]      // 000000003F6C: D3A000A7 169E9BDB
	v_fma_mix_f32 v166, v219, v77, v166 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003F74: D3A010A6 169A9BDB
	v_fma_mix_f32 v223, v219, v78, v152 op_sel_hi:[0,1,0]      // 000000003F7C: D3A000DF 16629DDB
	v_fma_mix_f32 v168, v219, v78, v168 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003F84: D3A010A8 16A29DDB
	v_fma_mix_f32 v198, v219, v79, v198 op_sel_hi:[0,1,0]      // 000000003F8C: D3A000C6 171A9FDB
	v_fma_mix_f32 v197, v219, v79, v197 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003F94: D3A010C5 17169FDB
	s_waitcnt lgkmcnt(0)                                       // 000000003F9C: BF8CC07F
	v_fma_mix_f32 v200, v219, v104, v200 op_sel_hi:[0,1,0]     // 000000003FA0: D3A000C8 1722D1DB
	v_fma_mix_f32 v104, v219, v104, v199 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003FA8: D3A01068 171ED1DB
	v_fma_mix_f32 v199, v219, v105, v206 op_sel_hi:[0,1,0]     // 000000003FB0: D3A000C7 173AD3DB
	v_fma_mix_f32 v105, v219, v105, v205 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003FB8: D3A01069 1736D3DB
	ds_read_b128 v[148:151], v196 offset:9024                  // 000000003FC0: D9FE2340 940000C4
	ds_read_b128 v[152:155], v196 offset:9040                  // 000000003FC8: D9FE2350 980000C4
	v_exp_f32_e32 v227, v52                                    // 000000003FD0: 7FC64134
	ds_read_b128 v[96:99], v196 offset:9088                    // 000000003FD4: D9FE2380 600000C4
	ds_read_b128 v[76:79], v196 offset:9056                    // 000000003FDC: D9FE2360 4C0000C4
	ds_read_b128 v[52:55], v196 offset:9072                    // 000000003FE4: D9FE2370 340000C4
	v_add_f32_e32 v230, v207, v219                             // 000000003FEC: 03CDB7CF
	ds_read_b128 v[205:208], v196 offset:9104                  // 000000003FF0: D9FE2390 CD0000C4
	s_waitcnt lgkmcnt(3)                                       // 000000003FF8: BF8CC37F
	v_fma_mix_f32 v228, v227, v96, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000003FFC: D3A010E4 15C2C1E3
	v_fma_mix_f32 v232, v227, v96, v210 op_sel_hi:[0,1,0]      // 000000004004: D3A000E8 174AC1E3
	v_fma_mix_f32 v233, v227, v97, v114 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000400C: D3A010E9 15CAC3E3
	v_fma_mix_f32 v236, v227, v97, v113 op_sel_hi:[0,1,0]      // 000000004014: D3A000EC 15C6C3E3
	v_fma_mix_f32 v240, v227, v98, v212 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000401C: D3A010F0 1752C5E3
	v_fma_mix_f32 v241, v227, v98, v211 op_sel_hi:[0,1,0]      // 000000004024: D3A000F1 174EC5E3
	v_fma_mix_f32 v86, v227, v99, v86 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000402C: D3A01056 155AC7E3
	v_fma_mix_f32 v248, v227, v99, v213 op_sel_hi:[0,1,0]      // 000000004034: D3A000F8 1756C7E3
	ds_read_b128 v[96:99], v196 offset:9120                    // 00000000403C: D9FE23A0 600000C4
	s_waitcnt lgkmcnt(1)                                       // 000000004044: BF8CC17F
	v_fma_mix_f32 v193, v227, v205, v115 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004048: D3A010C1 15CF9BE3
	v_fma_mix_f32 v87, v227, v205, v87 op_sel_hi:[0,1,0]       // 000000004050: D3A00057 155F9BE3
	v_fma_mix_f32 v215, v227, v206, v215 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004058: D3A010D7 175F9DE3
	v_fma_mix_f32 v214, v227, v206, v214 op_sel_hi:[0,1,0]     // 000000004060: D3A000D6 175B9DE3
	v_fma_mix_f32 v194, v227, v207, v217 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004068: D3A010C2 17679FE3
	v_fma_mix_f32 v216, v227, v207, v216 op_sel_hi:[0,1,0]     // 000000004070: D3A000D8 17639FE3
	v_fma_mix_f32 v221, v227, v208, v221 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004078: D3A010DD 1777A1E3
	v_fma_mix_f32 v220, v227, v208, v220 op_sel_hi:[0,1,0]     // 000000004080: D3A000DC 1773A1E3
	ds_read_b128 v[205:208], v196 offset:9136                  // 000000004088: D9FE23B0 CD0000C4
	v_sub_f32_e32 v85, v85, v195                               // 000000004090: 04AB8755
	s_waitcnt lgkmcnt(1)                                       // 000000004094: BF8CC17F
	v_fma_mix_f32 v191, v227, v96, v156 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004098: D3A010BF 1672C1E3
	v_fma_mix_f32 v192, v227, v96, v222 op_sel_hi:[0,1,0]      // 0000000040A0: D3A000C0 177AC1E3
	v_fma_mix_f32 v166, v227, v97, v166 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000040A8: D3A010A6 169AC3E3
	v_fma_mix_f32 v167, v227, v97, v167 op_sel_hi:[0,1,0]      // 0000000040B0: D3A000A7 169EC3E3
	v_fma_mix_f32 v168, v227, v98, v168 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000040B8: D3A010A8 16A2C5E3
	v_fma_mix_f32 v222, v227, v98, v223 op_sel_hi:[0,1,0]      // 0000000040C0: D3A000DE 177EC5E3
	v_fma_mix_f32 v223, v227, v99, v197 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000040C8: D3A010DF 1716C7E3
	v_fma_mix_f32 v158, v227, v99, v198 op_sel_hi:[0,1,0]      // 0000000040D0: D3A0009E 171AC7E3
	ds_read_b128 v[96:99], v196 offset:9216                    // 0000000040D8: D9FE2400 600000C4
	s_waitcnt lgkmcnt(1)                                       // 0000000040E0: BF8CC17F
	v_fma_mix_f32 v159, v227, v205, v200 op_sel_hi:[0,1,0]     // 0000000040E4: D3A0009F 17239BE3
	v_fma_mix_f32 v224, v227, v206, v199 op_sel_hi:[0,1,0]     // 0000000040EC: D3A000E0 171F9DE3
	v_mul_f32_e32 v85, 0x3fb8aa3b, v85                         // 0000000040F4: 0AAAAAFF 3FB8AA3B
	ds_read_b128 v[197:200], v196 offset:9152                  // 0000000040FC: D9FE23C0 C50000C4
	ds_read_b128 v[210:213], v196 offset:9168                  // 000000004104: D9FE23D0 D20000C4
	ds_read_b128 v[112:115], v196 offset:9232                  // 00000000410C: D9FE2410 700000C4
	v_exp_f32_e32 v229, v85                                    // 000000004114: 7FCA4155
	v_fma_mix_f32 v104, v227, v205, v104 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004118: D3A01068 15A39BE3
	v_fma_mix_f32 v105, v227, v206, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004120: D3A01069 15A79DE3
	v_add_f32_e32 v230, v230, v227                             // 000000004128: 03CDC7E6
	s_waitcnt lgkmcnt(3)                                       // 00000000412C: BF8CC37F
	v_fma_mix_f32 v237, v229, v96, v232 op_sel_hi:[0,1,0]      // 000000004130: D3A000ED 17A2C1E5
	s_waitcnt lgkmcnt(0)                                       // 000000004138: BF8CC07F
	v_fma_mix_f32 v232, v229, v113, v214 op_sel_hi:[0,1,0]     // 00000000413C: D3A000E8 175AE3E5
	v_fma_mix_f32 v156, v229, v113, v215 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004144: D3A0109C 175EE3E5
	v_fma_mix_f32 v85, v229, v114, v216 op_sel_hi:[0,1,0]      // 00000000414C: D3A00055 1762E5E5
	ds_read_b128 v[214:217], v196 offset:9248                  // 000000004154: D9FE2420 D60000C4
	buffer_store_dword v85, off, s[24:27], 0 offset:172        // 00000000415C: E07000AC 80065500
	v_fma_mix_f32 v85, v229, v115, v220 op_sel_hi:[0,1,0]      // 000000004164: D3A00055 1772E7E5
	buffer_store_dword v85, off, s[24:27], 0 offset:164        // 00000000416C: E07000A4 80065500
	v_fma_mix_f32 v85, v229, v115, v221 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004174: D3A01055 1776E7E5
	buffer_store_dword v85, off, s[24:27], 0 offset:168        // 00000000417C: E07000A8 80065500
	s_waitcnt lgkmcnt(0)                                       // 000000004184: BF8CC07F
	v_fma_mix_f32 v85, v229, v214, v192 op_sel_hi:[0,1,0]      // 000000004188: D3A00055 1703ADE5
	buffer_store_dword v85, off, s[24:27], 0 offset:156        // 000000004190: E070009C 80065500
	v_fma_mix_f32 v85, v229, v214, v191 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004198: D3A01055 16FFADE5
	buffer_store_dword v85, off, s[24:27], 0 offset:160        // 0000000041A0: E07000A0 80065500
	v_fma_mix_f32 v85, v229, v215, v167 op_sel_hi:[0,1,0]      // 0000000041A8: D3A00055 169FAFE5
	buffer_store_dword v85, off, s[24:27], 0 offset:88         // 0000000041B0: E0700058 80065500
	v_fma_mix_f32 v85, v229, v215, v166 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000041B8: D3A01055 169BAFE5
	v_fma_mix_f32 v249, v229, v99, v86 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000041C0: D3A010F9 155AC7E5
	buffer_store_dword v85, off, s[24:27], 0 offset:96         // 0000000041C8: E0700060 80065500
	v_fma_mix_f32 v85, v229, v216, v222 op_sel_hi:[0,1,0]      // 0000000041D0: D3A00055 177BB1E5
	v_fma_mix_f32 v86, v229, v217, v223 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000041D8: D3A01056 177FB3E5
	ds_read_b128 v[220:223], v196 offset:9264                  // 0000000041E0: D9FE2430 DC0000C4
	buffer_store_dword v85, off, s[24:27], 0 offset:72         // 0000000041E8: E0700048 80065500
	v_fma_mix_f32 v85, v229, v216, v168 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000041F0: D3A01055 16A3B1E5
	buffer_store_dword v85, off, s[24:27], 0 offset:76         // 0000000041F8: E070004C 80065500
	v_fma_mix_f32 v85, v229, v217, v158 op_sel_hi:[0,1,0]      // 000000004200: D3A00055 167BB3E5
	s_waitcnt lgkmcnt(0)                                       // 000000004208: BF8CC07F
	v_fma_mix_f32 v104, v229, v220, v104 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000420C: D3A01068 15A3B9E5
	buffer_store_dword v104, off, s[24:27], 0 offset:84        // 000000004214: E0700054 80066800
	v_fma_mix_f32 v104, v229, v221, v224 op_sel_hi:[0,1,0]     // 00000000421C: D3A00068 1783BBE5
	buffer_store_dword v104, off, s[24:27], 0 offset:56        // 000000004224: E0700038 80066800
	v_fma_mix_f32 v104, v229, v221, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000422C: D3A01068 15A7BBE5
	buffer_store_dword v104, off, s[24:27], 0 offset:60        // 000000004234: E070003C 80066800
	v_fma_mix_f32 v104, v146, v234, v203 op_sel_hi:[0,1,0]     // 00000000423C: D3A00068 172FD592
	v_fma_mix_f32 v105, v146, v234, v225 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004244: D3A01069 1787D592
	v_fma_mix_f32 v104, v157, v238, v104 op_sel_hi:[0,1,0]     // 00000000424C: D3A00068 15A3DD9D
	buffer_store_dword v85, off, s[24:27], 0 offset:44         // 000000004254: E070002C 80065500
	v_cvt_f32_f16_e32 v85, v84                                 // 00000000425C: 7EAA1754
	v_fma_mix_f32 v105, v157, v238, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004260: D3A01069 15A7DD9D
	v_fma_mix_f32 v104, v209, v242, v104 op_sel_hi:[0,1,0]     // 000000004268: D3A00068 15A3E5D1
	v_fma_mix_f32 v105, v209, v242, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004270: D3A01069 15A7E5D1
	v_fma_mix_f32 v104, v218, v250, v104 op_sel_hi:[0,1,0]     // 000000004278: D3A00068 15A3F5DA
	v_fma_mix_f32 v105, v218, v250, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004280: D3A01069 15A7F5DA
	v_fma_mix_f32 v104, v219, v106, v104 op_sel_hi:[0,1,0]     // 000000004288: D3A00068 15A2D5DB
	v_fma_mix_f32 v105, v219, v106, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004290: D3A01069 15A6D5DB
	v_fma_mix_f32 v104, v227, v207, v104 op_sel_hi:[0,1,0]     // 000000004298: D3A00068 15A39FE3
	v_cvt_f32_f16_sdwa v84, v84 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 0000000042A0: 7EA816F9 00050654
	v_mul_f32_e32 v113, v144, v85                              // 0000000042A8: 0AE2AB90
	v_fma_mix_f32 v105, v227, v207, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000042AC: D3A01069 15A79FE3
	v_fma_mix_f32 v104, v229, v222, v104 op_sel_hi:[0,1,0]     // 0000000042B4: D3A00068 15A3BDE5
	v_fmac_f32_e32 v113, v204, v128                            // 0000000042BC: 76E301CC
	buffer_store_dword v104, off, s[24:27], 0 offset:48        // 0000000042C0: E0700030 80066800
	v_fma_mix_f32 v104, v229, v222, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000042C8: D3A01068 15A7BDE5
	buffer_store_dword v104, off, s[24:27], 0 offset:52        // 0000000042D0: E0700034 80066800
	v_fma_mix_f32 v104, v145, v231, v113 op_sel_hi:[0,1,0]     // 0000000042D8: D3A00068 15C7CF91
	v_fma_mix_f32 v104, v146, v235, v104 op_sel_hi:[0,1,0]     // 0000000042E0: D3A00068 15A3D792
	v_fma_mix_f32 v205, v229, v97, v236 op_sel_hi:[0,1,0]      // 0000000042E8: D3A000CD 17B2C3E5
	v_fma_mix_f32 v236, v229, v98, v241 op_sel_hi:[0,1,0]      // 0000000042F0: D3A000EC 17C6C5E5
	v_fma_mix_f32 v241, v229, v114, v194 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000042F8: D3A010F1 170AE5E5
	v_mul_f32_e32 v114, v144, v84                              // 000000004300: 0AE4A990
	v_fma_mix_f32 v104, v157, v239, v104 op_sel_hi:[0,1,0]     // 000000004304: D3A00068 15A3DF9D
	v_fmac_f32_e32 v114, v204, v129                            // 00000000430C: 76E503CC
	v_fma_mix_f32 v104, v209, v243, v104 op_sel_hi:[0,1,0]     // 000000004310: D3A00068 15A3E7D1
	v_cvt_f32_f16_e32 v106, v56                                // 000000004318: 7ED41738
	v_cvt_f32_f16_sdwa v56, v56 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 00000000431C: 7E7016F9 00050638
	v_fma_mix_f32 v105, v145, v231, v114 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004324: D3A01069 15CBCF91
	v_fma_mix_f32 v104, v218, v251, v104 op_sel_hi:[0,1,0]     // 00000000432C: D3A00068 15A3F7DA
	v_fma_mix_f32 v105, v146, v235, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004334: D3A01069 15A7D792
	v_fma_mix_f32 v104, v219, v107, v104 op_sel_hi:[0,1,0]     // 00000000433C: D3A00068 15A2D7DB
	v_fma_mix_f32 v105, v157, v239, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004344: D3A01069 15A7DF9D
	v_fma_mix_f32 v104, v227, v208, v104 op_sel_hi:[0,1,0]     // 00000000434C: D3A00068 15A3A1E3
	v_fma_mix_f32 v105, v209, v243, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004354: D3A01069 15A7E7D1
	v_fma_mix_f32 v104, v229, v223, v104 op_sel_hi:[0,1,0]     // 00000000435C: D3A00068 15A3BFE5
	v_mul_f32_e32 v56, v144, v56                               // 000000004364: 0A707190
	v_fma_mix_f32 v105, v218, v251, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004368: D3A01069 15A7F7DA
	buffer_store_dword v104, off, s[24:27], 0 offset:68        // 000000004370: E0700044 80066800
	v_mul_f32_e32 v104, v144, v106                             // 000000004378: 0AD0D590
	v_fmac_f32_e32 v56, v204, v109                             // 00000000437C: 7670DBCC
	v_fma_mix_f32 v105, v219, v107, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004380: D3A01069 15A6D7DB
	v_fmac_f32_e32 v104, v204, v108                            // 000000004388: 76D0D9CC
	v_fma_mix_f32 v56, v145, v68, v56 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000438C: D3A01038 14E28991
	v_fma_mix_f32 v105, v227, v208, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004394: D3A01069 15A7A1E3
	v_fma_mix_f32 v104, v145, v68, v104 op_sel_hi:[0,1,0]      // 00000000439C: D3A00068 15A28991
	v_fma_mix_f32 v56, v146, v80, v56 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000043A4: D3A01038 14E2A192
	v_fma_mix_f32 v115, v229, v220, v159 op_sel_hi:[0,1,0]     // 0000000043AC: D3A00073 167FB9E5
	v_fma_mix_f32 v105, v229, v223, v105 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000043B4: D3A01069 15A7BFE5
	v_fma_mix_f32 v68, v146, v80, v104 op_sel_hi:[0,1,0]       // 0000000043BC: D3A00044 15A2A192
	v_fma_mix_f32 v56, v157, v92, v56 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000043C4: D3A01038 14E2B99D
	ds_read_b128 v[220:223], v196 offset:9280                  // 0000000043CC: D9FE2440 DC0000C4
	ds_read_b128 v[106:109], v196 offset:9296                  // 0000000043D4: D9FE2450 6A0000C4
	v_fma_mix_f32 v68, v157, v92, v68 op_sel_hi:[0,1,0]        // 0000000043DC: D3A00044 1512B99D
	v_fma_mix_f32 v56, v209, v244, v56 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000043E4: D3A01038 14E3E9D1
	v_fma_mix_f32 v68, v209, v244, v68 op_sel_hi:[0,1,0]       // 0000000043EC: D3A00044 1513E9D1
	v_fma_mix_f32 v56, v218, v252, v56 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000043F4: D3A01038 14E3F9DA
	v_fma_mix_f32 v68, v218, v252, v68 op_sel_hi:[0,1,0]       // 0000000043FC: D3A00044 1513F9DA
	v_fma_mix_f32 v56, v219, v148, v56 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004404: D3A01038 14E329DB
	v_cvt_f32_f16_sdwa v80, v57 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 00000000440C: 7EA016F9 00050639
	v_cvt_f32_f16_e32 v57, v57                                 // 000000004414: 7E721739
	v_fma_mix_f32 v68, v219, v148, v68 op_sel_hi:[0,1,0]       // 000000004418: D3A00044 151329DB
	v_fma_mix_f32 v56, v227, v197, v56 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004420: D3A01038 14E38BE3
	v_fma_mix_f32 v68, v227, v197, v68 op_sel_hi:[0,1,0]       // 000000004428: D3A00044 15138BE3
	s_waitcnt lgkmcnt(1)                                       // 000000004430: BF8CC17F
	v_fma_mix_f32 v56, v229, v220, v56 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004434: D3A01038 14E3B9E5
	buffer_store_dword v56, off, s[24:27], 0 offset:140        // 00000000443C: E070008C 80063800
	v_fma_mix_f32 v56, v229, v220, v68 op_sel_hi:[0,1,0]       // 000000004444: D3A00038 1513B9E5
	buffer_store_dword v56, off, s[24:27], 0 offset:148        // 00000000444C: E0700094 80063800
	v_mul_f32_e32 v56, v144, v57                               // 000000004454: 0A707390
	v_fmac_f32_e32 v56, v204, v116                             // 000000004458: 7670E9CC
	v_fma_mix_f32 v56, v145, v69, v56 op_sel_hi:[0,1,0]        // 00000000445C: D3A00038 14E28B91
	v_fma_mix_f32 v56, v146, v81, v56 op_sel_hi:[0,1,0]        // 000000004464: D3A00038 14E2A392
	v_fma_mix_f32 v56, v157, v93, v56 op_sel_hi:[0,1,0]        // 00000000446C: D3A00038 14E2BB9D
	v_fma_mix_f32 v56, v209, v245, v56 op_sel_hi:[0,1,0]       // 000000004474: D3A00038 14E3EBD1
	v_mul_f32_e32 v57, v144, v80                               // 00000000447C: 0A72A190
	v_fma_mix_f32 v56, v218, v253, v56 op_sel_hi:[0,1,0]       // 000000004480: D3A00038 14E3FBDA
	v_cvt_f32_f16_e32 v68, v58                                 // 000000004488: 7E88173A
	v_fmac_f32_e32 v57, v204, v117                             // 00000000448C: 7672EBCC
	v_fma_mix_f32 v56, v219, v149, v56 op_sel_hi:[0,1,0]       // 000000004490: D3A00038 14E32BDB
	v_fma_mix_f32 v57, v145, v69, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004498: D3A01039 14E68B91
	v_fma_mix_f32 v56, v227, v198, v56 op_sel_hi:[0,1,0]       // 0000000044A0: D3A00038 14E38DE3
	v_fma_mix_f32 v57, v146, v81, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000044A8: D3A01039 14E6A392
	v_fma_mix_f32 v56, v229, v221, v56 op_sel_hi:[0,1,0]       // 0000000044B0: D3A00038 14E3BBE5
	v_fma_mix_f32 v57, v157, v93, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000044B8: D3A01039 14E6BB9D
	buffer_store_dword v56, off, s[24:27], 0 offset:104        // 0000000044C0: E0700068 80063800
	v_mul_f32_e32 v56, v144, v68                               // 0000000044C8: 0A708990
	v_fma_mix_f32 v57, v209, v245, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000044CC: D3A01039 14E7EBD1
	v_fmac_f32_e32 v56, v204, v134                             // 0000000044D4: 76710DCC
	v_fma_mix_f32 v57, v218, v253, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000044D8: D3A01039 14E7FBDA
	v_cvt_f32_f16_sdwa v58, v58 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 0000000044E0: 7E7416F9 0005063A
	v_fma_mix_f32 v56, v145, v70, v56 op_sel_hi:[0,1,0]        // 0000000044E8: D3A00038 14E28D91
	v_fma_mix_f32 v57, v219, v149, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000044F0: D3A01039 14E72BDB
	v_fma_mix_f32 v56, v146, v82, v56 op_sel_hi:[0,1,0]        // 0000000044F8: D3A00038 14E2A592
	v_fma_mix_f32 v57, v227, v198, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004500: D3A01039 14E78DE3
	v_fma_mix_f32 v56, v157, v94, v56 op_sel_hi:[0,1,0]        // 000000004508: D3A00038 14E2BD9D
	v_fma_mix_f32 v57, v229, v221, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004510: D3A01039 14E7BBE5
	v_fma_mix_f32 v56, v209, v246, v56 op_sel_hi:[0,1,0]       // 000000004518: D3A00038 14E3EDD1
	buffer_store_dword v57, off, s[24:27], 0 offset:100        // 000000004520: E0700064 80063900
	v_mul_f32_e32 v57, v144, v58                               // 000000004528: 0A727590
	v_fma_mix_f32 v56, v218, v254, v56 op_sel_hi:[0,1,0]       // 00000000452C: D3A00038 14E3FDDA
	v_cvt_f32_f16_e32 v58, v59                                 // 000000004534: 7E74173B
	v_fma_mix_f32 v56, v219, v150, v56 op_sel_hi:[0,1,0]       // 000000004538: D3A00038 14E32DDB
	v_fma_mix_f32 v56, v227, v199, v56 op_sel_hi:[0,1,0]       // 000000004540: D3A00038 14E38FE3
	v_fma_mix_f32 v56, v229, v222, v56 op_sel_hi:[0,1,0]       // 000000004548: D3A00038 14E3BDE5
	buffer_store_dword v56, off, s[24:27], 0 offset:112        // 000000004550: E0700070 80063800
	v_mul_f32_e32 v56, v144, v58                               // 000000004558: 0A707590
	v_fmac_f32_e32 v56, v204, v132                             // 00000000455C: 767109CC
	v_fma_mix_f32 v56, v145, v71, v56 op_sel_hi:[0,1,0]        // 000000004560: D3A00038 14E28F91
	v_fma_mix_f32 v56, v146, v83, v56 op_sel_hi:[0,1,0]        // 000000004568: D3A00038 14E2A792
	v_fma_mix_f32 v56, v157, v95, v56 op_sel_hi:[0,1,0]        // 000000004570: D3A00038 14E2BF9D
	v_fma_mix_f32 v56, v209, v247, v56 op_sel_hi:[0,1,0]       // 000000004578: D3A00038 14E3EFD1
	v_cvt_f32_f16_e32 v58, v32                                 // 000000004580: 7E741720
	v_cvt_f32_f16_sdwa v32, v32 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004584: 7E4016F9 00050620
	v_fma_mix_f32 v56, v218, v255, v56 op_sel_hi:[0,1,0]       // 00000000458C: D3A00038 14E3FFDA
	v_fma_mix_f32 v56, v219, v151, v56 op_sel_hi:[0,1,0]       // 000000004594: D3A00038 14E32FDB
	v_fma_mix_f32 v56, v227, v200, v56 op_sel_hi:[0,1,0]       // 00000000459C: D3A00038 14E391E3
	v_fma_mix_f32 v56, v229, v223, v56 op_sel_hi:[0,1,0]       // 0000000045A4: D3A00038 14E3BFE5
	v_mul_f32_e32 v32, v144, v32                               // 0000000045AC: 0A404190
	buffer_store_dword v56, off, s[24:27], 0 offset:120        // 0000000045B0: E0700078 80063800
	v_mul_f32_e32 v56, v144, v58                               // 0000000045B8: 0A707590
	v_fmac_f32_e32 v32, v204, v139                             // 0000000045BC: 764117CC
	v_fmac_f32_e32 v56, v204, v138                             // 0000000045C0: 767115CC
	v_fma_mix_f32 v32, v145, v44, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000045C4: D3A01020 14825991
	v_fma_mix_f32 v56, v145, v44, v56 op_sel_hi:[0,1,0]        // 0000000045CC: D3A00038 14E25991
	v_fma_mix_f32 v32, v146, v60, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000045D4: D3A01020 14827992
	v_fma_mix_f32 v44, v146, v60, v56 op_sel_hi:[0,1,0]        // 0000000045DC: D3A0002C 14E27992
	v_fma_mix_f32 v32, v157, v72, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000045E4: D3A01020 1482919D
	v_fma_mix_f32 v44, v157, v72, v44 op_sel_hi:[0,1,0]        // 0000000045EC: D3A0002C 14B2919D
	v_fma_mix_f32 v32, v209, v88, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000045F4: D3A01020 1482B1D1
	v_fma_mix_f32 v44, v209, v88, v44 op_sel_hi:[0,1,0]        // 0000000045FC: D3A0002C 14B2B1D1
	v_fma_mix_f32 v32, v218, v100, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004604: D3A01020 1482C9DA
	v_fma_mix_f32 v44, v218, v100, v44 op_sel_hi:[0,1,0]       // 00000000460C: D3A0002C 14B2C9DA
	v_fma_mix_f32 v32, v219, v152, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004614: D3A01020 148331DB
	v_cvt_f32_f16_e32 v56, v33                                 // 00000000461C: 7E701721
	v_fma_mix_f32 v44, v219, v152, v44 op_sel_hi:[0,1,0]       // 000000004620: D3A0002C 14B331DB
	v_fma_mix_f32 v32, v227, v210, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004628: D3A01020 1483A5E3
	v_fma_mix_f32 v44, v227, v210, v44 op_sel_hi:[0,1,0]       // 000000004630: D3A0002C 14B3A5E3
	s_waitcnt lgkmcnt(0)                                       // 000000004638: BF8CC07F
	v_fma_mix_f32 v32, v229, v106, v32 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000463C: D3A01020 1482D5E5
	v_cvt_f32_f16_sdwa v33, v33 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004644: 7E4216F9 00050621
	buffer_store_dword v32, off, s[24:27], 0 offset:124        // 00000000464C: E070007C 80062000
	v_fma_mix_f32 v32, v229, v106, v44 op_sel_hi:[0,1,0]       // 000000004654: D3A00020 14B2D5E5
	buffer_store_dword v32, off, s[24:27], 0 offset:128        // 00000000465C: E0700080 80062000
	v_mul_f32_e32 v32, v144, v56                               // 000000004664: 0A407190
	v_fmac_f32_e32 v32, v204, v136                             // 000000004668: 764111CC
	v_fma_mix_f32 v32, v145, v45, v32 op_sel_hi:[0,1,0]        // 00000000466C: D3A00020 14825B91
	v_mul_f32_e32 v33, v144, v33                               // 000000004674: 0A424390
	v_fma_mix_f32 v32, v146, v61, v32 op_sel_hi:[0,1,0]        // 000000004678: D3A00020 14827B92
	v_fmac_f32_e32 v33, v204, v137                             // 000000004680: 764313CC
	v_fma_mix_f32 v32, v157, v73, v32 op_sel_hi:[0,1,0]        // 000000004684: D3A00020 1482939D
	v_fma_mix_f32 v33, v145, v45, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000468C: D3A01021 14865B91
	v_fma_mix_f32 v32, v209, v89, v32 op_sel_hi:[0,1,0]        // 000000004694: D3A00020 1482B3D1
	v_fma_mix_f32 v33, v146, v61, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000469C: D3A01021 14867B92
	v_fma_mix_f32 v32, v218, v101, v32 op_sel_hi:[0,1,0]       // 0000000046A4: D3A00020 1482CBDA
	v_cvt_f32_f16_e32 v44, v34                                 // 0000000046AC: 7E581722
	v_fma_mix_f32 v33, v157, v73, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000046B0: D3A01021 1486939D
	v_fma_mix_f32 v32, v219, v153, v32 op_sel_hi:[0,1,0]       // 0000000046B8: D3A00020 148333DB
	v_fma_mix_f32 v33, v209, v89, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000046C0: D3A01021 1486B3D1
	v_fma_mix_f32 v32, v227, v211, v32 op_sel_hi:[0,1,0]       // 0000000046C8: D3A00020 1483A7E3
	v_fma_mix_f32 v33, v218, v101, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000046D0: D3A01021 1486CBDA
	v_cvt_f32_f16_sdwa v34, v34 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 0000000046D8: 7E4416F9 00050622
	v_fma_mix_f32 v32, v229, v107, v32 op_sel_hi:[0,1,0]       // 0000000046E0: D3A00020 1482D7E5
	v_fma_mix_f32 v33, v219, v153, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000046E8: D3A01021 148733DB
	buffer_store_dword v32, off, s[24:27], 0 offset:136        // 0000000046F0: E0700088 80062000
	v_mul_f32_e32 v32, v144, v44                               // 0000000046F8: 0A405990
	v_fma_mix_f32 v33, v227, v211, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000046FC: D3A01021 1487A7E3
	v_fmac_f32_e32 v32, v204, v164                             // 000000004704: 764149CC
	v_fma_mix_f32 v33, v229, v107, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004708: D3A01021 1486D7E5
	v_fma_mix_f32 v32, v145, v46, v32 op_sel_hi:[0,1,0]        // 000000004710: D3A00020 14825D91
	buffer_store_dword v33, off, s[24:27], 0 offset:132        // 000000004718: E0700084 80062100
	v_mul_f32_e32 v33, v144, v34                               // 000000004720: 0A424590
	v_fma_mix_f32 v32, v146, v62, v32 op_sel_hi:[0,1,0]        // 000000004724: D3A00020 14827D92
	v_fmac_f32_e32 v33, v204, v165                             // 00000000472C: 76434BCC
	v_fma_mix_f32 v32, v157, v74, v32 op_sel_hi:[0,1,0]        // 000000004730: D3A00020 1482959D
	v_fma_mix_f32 v33, v145, v46, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004738: D3A01021 14865D91
	v_fma_mix_f32 v32, v209, v90, v32 op_sel_hi:[0,1,0]        // 000000004740: D3A00020 1482B5D1
	v_fma_mix_f32 v33, v146, v62, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004748: D3A01021 14867D92
	v_fma_mix_f32 v32, v218, v102, v32 op_sel_hi:[0,1,0]       // 000000004750: D3A00020 1482CDDA
	v_cvt_f32_f16_e32 v34, v35                                 // 000000004758: 7E441723
	v_fma_mix_f32 v33, v157, v74, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000475C: D3A01021 1486959D
	v_fma_mix_f32 v32, v219, v154, v32 op_sel_hi:[0,1,0]       // 000000004764: D3A00020 148335DB
	v_fma_mix_f32 v33, v209, v90, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000476C: D3A01021 1486B5D1
	v_fma_mix_f32 v32, v227, v212, v32 op_sel_hi:[0,1,0]       // 000000004774: D3A00020 1483A9E3
	v_fma_mix_f32 v33, v218, v102, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000477C: D3A01021 1486CDDA
	v_cvt_f32_f16_sdwa v35, v35 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004784: 7E4616F9 00050623
	v_fma_mix_f32 v32, v229, v108, v32 op_sel_hi:[0,1,0]       // 00000000478C: D3A00020 1482D9E5
	v_fma_mix_f32 v33, v219, v154, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004794: D3A01021 148735DB
	buffer_store_dword v32, off, s[24:27], 0 offset:152        // 00000000479C: E0700098 80062000
	v_mul_f32_e32 v32, v144, v34                               // 0000000047A4: 0A404590
	v_fma_mix_f32 v33, v227, v212, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000047A8: D3A01021 1487A9E3
	v_fmac_f32_e32 v32, v204, v118                             // 0000000047B0: 7640EDCC
	v_fma_mix_f32 v33, v229, v108, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000047B4: D3A01021 1486D9E5
	v_fma_mix_f32 v32, v145, v47, v32 op_sel_hi:[0,1,0]        // 0000000047BC: D3A00020 14825F91
	buffer_store_dword v33, off, s[24:27], 0 offset:144        // 0000000047C4: E0700090 80062100
	v_mul_f32_e32 v33, v144, v35                               // 0000000047CC: 0A424790
	v_fma_mix_f32 v32, v146, v63, v32 op_sel_hi:[0,1,0]        // 0000000047D0: D3A00020 14827F92
	v_fmac_f32_e32 v33, v204, v119                             // 0000000047D8: 7642EFCC
	v_fma_mix_f32 v32, v157, v75, v32 op_sel_hi:[0,1,0]        // 0000000047DC: D3A00020 1482979D
	v_cvt_f32_f16_e32 v34, v8                                  // 0000000047E4: 7E441708
	v_cvt_f32_f16_sdwa v8, v8 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 0000000047E8: 7E1016F9 00050608
	v_fma_mix_f32 v33, v145, v47, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000047F0: D3A01021 14865F91
	v_fma_mix_f32 v32, v209, v91, v32 op_sel_hi:[0,1,0]        // 0000000047F8: D3A00020 1482B7D1
	v_fma_mix_f32 v33, v146, v63, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004800: D3A01021 14867F92
	v_fma_mix_f32 v32, v218, v103, v32 op_sel_hi:[0,1,0]       // 000000004808: D3A00020 1482CFDA
	v_fma_mix_f32 v33, v157, v75, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004810: D3A01021 1486979D
	v_fma_mix_f32 v32, v219, v155, v32 op_sel_hi:[0,1,0]       // 000000004818: D3A00020 148337DB
	v_fma_mix_f32 v33, v209, v91, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004820: D3A01021 1486B7D1
	v_fma_mix_f32 v32, v227, v213, v32 op_sel_hi:[0,1,0]       // 000000004828: D3A00020 1483ABE3
	v_mul_f32_e32 v8, v144, v8                                 // 000000004830: 0A101190
	v_fma_mix_f32 v33, v218, v103, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004834: D3A01021 1486CFDA
	v_fma_mix_f32 v234, v229, v109, v32 op_sel_hi:[0,1,0]      // 00000000483C: D3A000EA 1482DBE5
	v_mul_f32_e32 v32, v144, v34                               // 000000004844: 0A404590
	v_fmac_f32_e32 v8, v204, v202                              // 000000004848: 761195CC
	v_fma_mix_f32 v33, v219, v155, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000484C: D3A01021 148737DB
	v_fmac_f32_e32 v32, v204, v201                             // 000000004854: 764193CC
	v_fma_mix_f32 v8, v145, v16, v8 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004858: D3A01008 14222191
	v_fma_mix_f32 v228, v229, v96, v228 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004860: D3A010E4 1792C1E5
	v_fma_mix_f32 v233, v229, v97, v233 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004868: D3A010E9 17A6C3E5
	v_fma_mix_f32 v240, v229, v98, v240 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004870: D3A010F0 17C2C5E5
	v_fma_mix_f32 v248, v229, v99, v248 op_sel_hi:[0,1,0]      // 000000004878: D3A000F8 17E2C7E5
	ds_read_b128 v[96:99], v196 offset:9184                    // 000000004880: D9FE23E0 600000C4
	v_fma_mix_f32 v33, v227, v213, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004888: D3A01021 1487ABE3
	v_fma_mix_f32 v32, v145, v16, v32 op_sel_hi:[0,1,0]        // 000000004890: D3A00020 14822191
	v_fma_mix_f32 v8, v146, v24, v8 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004898: D3A01008 14223192
	v_fma_mix_f32 v238, v229, v109, v33 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000048A0: D3A010EE 1486DBE5
	v_fma_mix_f32 v16, v146, v24, v32 op_sel_hi:[0,1,0]        // 0000000048A8: D3A00010 14823192
	v_fma_mix_f32 v8, v157, v36, v8 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000048B0: D3A01008 1422499D
	ds_read_b128 v[32:35], v196 offset:9312                    // 0000000048B8: D9FE2460 200000C4
	ds_read_b128 v[44:47], v196 offset:9328                    // 0000000048C0: D9FE2470 2C0000C4
	v_fma_mix_f32 v8, v209, v48, v8 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000048C8: D3A01008 142261D1
	v_cvt_f32_f16_sdwa v24, v9 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 0000000048D0: 7E3016F9 00050609
	v_cvt_f32_f16_e32 v9, v9                                   // 0000000048D8: 7E121709
	v_fma_mix_f32 v8, v218, v64, v8 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000048DC: D3A01008 142281DA
	v_fma_mix_f32 v8, v219, v76, v8 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000048E4: D3A01008 142299DB
	v_fma_mix_f32 v206, v229, v112, v87 op_sel_hi:[0,1,0]      // 0000000048EC: D3A000CE 155EE1E5
	buffer_store_dword v86, off, s[24:27], 0 offset:92         // 0000000048F4: E070005C 80065600
	ds_read_b128 v[84:87], v196 offset:9200                    // 0000000048FC: D9FE23F0 540000C4
	s_waitcnt lgkmcnt(3)                                       // 000000004904: BF8CC37F
	v_fma_mix_f32 v8, v227, v96, v8 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004908: D3A01008 1422C1E3
	v_fma_mix_f32 v16, v157, v36, v16 op_sel_hi:[0,1,0]        // 000000004910: D3A00010 1442499D
	s_waitcnt lgkmcnt(2)                                       // 000000004918: BF8CC27F
	v_fma_mix_f32 v114, v229, v32, v8 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000491C: D3A01072 142241E5
	v_mul_f32_e32 v8, v144, v9                                 // 000000004924: 0A101390
	v_fma_mix_f32 v16, v209, v48, v16 op_sel_hi:[0,1,0]        // 000000004928: D3A00010 144261D1
	v_fmac_f32_e32 v8, v204, v130                              // 000000004930: 761105CC
	v_fma_mix_f32 v16, v218, v64, v16 op_sel_hi:[0,1,0]        // 000000004934: D3A00010 144281DA
	v_fma_mix_f32 v8, v145, v17, v8 op_sel_hi:[0,1,0]          // 00000000493C: D3A00008 14222391
	v_fma_mix_f32 v16, v219, v76, v16 op_sel_hi:[0,1,0]        // 000000004944: D3A00010 144299DB
	v_fma_mix_f32 v8, v146, v25, v8 op_sel_hi:[0,1,0]          // 00000000494C: D3A00008 14223392
	v_fma_mix_f32 v16, v227, v96, v16 op_sel_hi:[0,1,0]        // 000000004954: D3A00010 1442C1E3
	v_fma_mix_f32 v8, v157, v37, v8 op_sel_hi:[0,1,0]          // 00000000495C: D3A00008 14224B9D
	buffer_store_dword v105, off, s[24:27], 0 offset:64        // 000000004964: E0700040 80066900
	v_fma_mix_f32 v105, v229, v32, v16 op_sel_hi:[0,1,0]       // 00000000496C: D3A00069 144241E5
	v_mul_f32_e32 v9, v144, v24                                // 000000004974: 0A123190
	v_fma_mix_f32 v8, v209, v49, v8 op_sel_hi:[0,1,0]          // 000000004978: D3A00008 142263D1
	v_cvt_f32_f16_e32 v16, v10                                 // 000000004980: 7E20170A
	v_fmac_f32_e32 v9, v204, v131                              // 000000004984: 761307CC
	v_fma_mix_f32 v8, v218, v65, v8 op_sel_hi:[0,1,0]          // 000000004988: D3A00008 142283DA
	v_fma_mix_f32 v9, v145, v17, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004990: D3A01009 14262391
	v_fma_mix_f32 v8, v219, v77, v8 op_sel_hi:[0,1,0]          // 000000004998: D3A00008 14229BDB
	v_fma_mix_f32 v9, v146, v25, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000049A0: D3A01009 14263392
	v_fma_mix_f32 v8, v227, v97, v8 op_sel_hi:[0,1,0]          // 0000000049A8: D3A00008 1422C3E3
	v_fma_mix_f32 v9, v157, v37, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000049B0: D3A01009 14264B9D
	v_fma_mix_f32 v239, v229, v33, v8 op_sel_hi:[0,1,0]        // 0000000049B8: D3A000EF 142243E5
	v_mul_f32_e32 v8, v144, v16                                // 0000000049C0: 0A102190
	v_fma_mix_f32 v9, v209, v49, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000049C4: D3A01009 142663D1
	v_cvt_f32_f16_sdwa v10, v10 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 0000000049CC: 7E1416F9 0005060A
	v_fmac_f32_e32 v8, v204, v122                              // 0000000049D4: 7610F5CC
	v_fma_mix_f32 v9, v218, v65, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000049D8: D3A01009 142683DA
	v_fma_mix_f32 v8, v145, v18, v8 op_sel_hi:[0,1,0]          // 0000000049E0: D3A00008 14222591
	v_fma_mix_f32 v9, v219, v77, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000049E8: D3A01009 14269BDB
	v_fma_mix_f32 v8, v146, v26, v8 op_sel_hi:[0,1,0]          // 0000000049F0: D3A00008 14223592
	v_fma_mix_f32 v9, v227, v97, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000049F8: D3A01009 1426C3E3
	v_fma_mix_f32 v8, v157, v38, v8 op_sel_hi:[0,1,0]          // 000000004A00: D3A00008 14224D9D
	v_fma_mix_f32 v235, v229, v33, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004A08: D3A010EB 142643E5
	v_mul_f32_e32 v9, v144, v10                                // 000000004A10: 0A121590
	v_fma_mix_f32 v8, v209, v50, v8 op_sel_hi:[0,1,0]          // 000000004A14: D3A00008 142265D1
	v_cvt_f32_f16_e32 v10, v11                                 // 000000004A1C: 7E14170B
	v_fma_mix_f32 v8, v218, v66, v8 op_sel_hi:[0,1,0]          // 000000004A20: D3A00008 142285DA
	v_fma_mix_f32 v8, v219, v78, v8 op_sel_hi:[0,1,0]          // 000000004A28: D3A00008 14229DDB
	v_fma_mix_f32 v8, v227, v98, v8 op_sel_hi:[0,1,0]          // 000000004A30: D3A00008 1422C5E3
	v_fma_mix_f32 v216, v229, v34, v8 op_sel_hi:[0,1,0]        // 000000004A38: D3A000D8 142245E5
	v_mul_f32_e32 v8, v144, v10                                // 000000004A40: 0A101590
	v_fmac_f32_e32 v8, v204, v124                              // 000000004A44: 7610F9CC
	v_fma_mix_f32 v8, v145, v19, v8 op_sel_hi:[0,1,0]          // 000000004A48: D3A00008 14222791
	v_fma_mix_f32 v8, v146, v27, v8 op_sel_hi:[0,1,0]          // 000000004A50: D3A00008 14223792
	v_cvt_f32_f16_e32 v10, v0                                  // 000000004A58: 7E141700
	v_cvt_f32_f16_sdwa v0, v0 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004A5C: 7E0016F9 00050600
	v_fma_mix_f32 v8, v157, v39, v8 op_sel_hi:[0,1,0]          // 000000004A64: D3A00008 14224F9D
	v_fmac_f32_e32 v57, v204, v135                             // 000000004A6C: 76730FCC
	v_fma_mix_f32 v8, v209, v51, v8 op_sel_hi:[0,1,0]          // 000000004A70: D3A00008 142267D1
	v_fma_mix_f32 v57, v145, v70, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004A78: D3A01039 14E68D91
	v_fma_mix_f32 v8, v218, v67, v8 op_sel_hi:[0,1,0]          // 000000004A80: D3A00008 142287DA
	v_fma_mix_f32 v57, v146, v82, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004A88: D3A01039 14E6A592
	v_fma_mix_f32 v8, v219, v79, v8 op_sel_hi:[0,1,0]          // 000000004A90: D3A00008 14229FDB
	v_mul_f32_e32 v0, v144, v0                                 // 000000004A98: 0A000190
	v_fma_mix_f32 v57, v157, v94, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004A9C: D3A01039 14E6BD9D
	v_fma_mix_f32 v8, v227, v99, v8 op_sel_hi:[0,1,0]          // 000000004AA4: D3A00008 1422C7E3
	v_fmac_f32_e32 v0, v204, v161                              // 000000004AAC: 760143CC
	v_fma_mix_f32 v57, v209, v246, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004AB0: D3A01039 14E7EDD1
	v_fma_mix_f32 v217, v229, v35, v8 op_sel_hi:[0,1,0]        // 000000004AB8: D3A000D9 142247E5
	v_mul_f32_e32 v8, v144, v10                                // 000000004AC0: 0A101590
	v_fma_mix_f32 v0, v145, v4, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004AC4: D3A01000 14020991
	v_fma_mix_f32 v57, v218, v254, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004ACC: D3A01039 14E7FDDA
	v_cvt_f32_f16_sdwa v59, v59 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004AD4: 7E7616F9 0005063B
	v_fmac_f32_e32 v8, v204, v160                              // 000000004ADC: 761141CC
	v_fma_mix_f32 v0, v146, v12, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004AE0: D3A01000 14021992
	v_fma_mix_f32 v57, v219, v150, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004AE8: D3A01039 14E72DDB
	v_fma_mix_f32 v8, v145, v4, v8 op_sel_hi:[0,1,0]           // 000000004AF0: D3A00008 14220991
	v_fma_mix_f32 v0, v157, v20, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004AF8: D3A01000 1402299D
	v_fma_mix_f32 v57, v227, v199, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B00: D3A01039 14E78FE3
	v_fma_mix_f32 v4, v146, v12, v8 op_sel_hi:[0,1,0]          // 000000004B08: D3A00004 14221992
	v_fma_mix_f32 v0, v209, v28, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B10: D3A01000 140239D1
	v_cvt_f32_f16_e32 v8, v1                                   // 000000004B18: 7E101701
	v_fma_mix_f32 v57, v229, v222, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B1C: D3A01039 14E7BDE5
	v_fma_mix_f32 v0, v218, v40, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B24: D3A01000 140251DA
	buffer_store_dword v57, off, s[24:27], 0 offset:108        // 000000004B2C: E070006C 80063900
	v_mul_f32_e32 v57, v144, v59                               // 000000004B34: 0A727790
	v_fma_mix_f32 v0, v219, v52, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B38: D3A01000 140269DB
	v_fmac_f32_e32 v57, v204, v133                             // 000000004B40: 76730BCC
	s_waitcnt lgkmcnt(0)                                       // 000000004B44: BF8CC07F
	v_fma_mix_f32 v0, v227, v84, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B48: D3A01000 1402A9E3
	v_fma_mix_f32 v57, v145, v71, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B50: D3A01039 14E68F91
	v_fma_mix_f32 v4, v157, v20, v4 op_sel_hi:[0,1,0]          // 000000004B58: D3A00004 1412299D
	v_fma_mix_f32 v213, v229, v44, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B60: D3A010D5 140259E5
	v_mul_f32_e32 v0, v144, v8                                 // 000000004B68: 0A001190
	v_fma_mix_f32 v57, v146, v83, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B6C: D3A01039 14E6A792
	v_fma_mix_f32 v4, v209, v28, v4 op_sel_hi:[0,1,0]          // 000000004B74: D3A00004 141239D1
	v_fmac_f32_e32 v0, v204, v162                              // 000000004B7C: 760145CC
	v_fma_mix_f32 v57, v157, v95, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B80: D3A01039 14E6BF9D
	v_fma_mix_f32 v4, v218, v40, v4 op_sel_hi:[0,1,0]          // 000000004B88: D3A00004 141251DA
	v_fma_mix_f32 v0, v145, v5, v0 op_sel_hi:[0,1,0]           // 000000004B90: D3A00000 14020B91
	v_fma_mix_f32 v57, v209, v247, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004B98: D3A01039 14E7EFD1
	v_fma_mix_f32 v4, v219, v52, v4 op_sel_hi:[0,1,0]          // 000000004BA0: D3A00004 141269DB
	v_cvt_f32_f16_sdwa v1, v1 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004BA8: 7E0216F9 00050601
	v_fma_mix_f32 v0, v146, v13, v0 op_sel_hi:[0,1,0]          // 000000004BB0: D3A00000 14021B92
	v_fma_mix_f32 v57, v218, v255, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004BB8: D3A01039 14E7FFDA
	v_fma_mix_f32 v4, v227, v84, v4 op_sel_hi:[0,1,0]          // 000000004BC0: D3A00004 1412A9E3
	v_fma_mix_f32 v0, v157, v21, v0 op_sel_hi:[0,1,0]          // 000000004BC8: D3A00000 14022B9D
	v_fma_mix_f32 v57, v219, v151, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004BD0: D3A01039 14E72FDB
	v_fma_mix_f32 v214, v229, v44, v4 op_sel_hi:[0,1,0]        // 000000004BD8: D3A000D6 141259E5
	v_fma_mix_f32 v0, v209, v29, v0 op_sel_hi:[0,1,0]          // 000000004BE0: D3A00000 14023BD1
	v_cvt_f32_f16_e32 v4, v2                                   // 000000004BE8: 7E081702
	v_fma_mix_f32 v57, v227, v200, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004BEC: D3A01039 14E791E3
	v_fma_mix_f32 v0, v218, v41, v0 op_sel_hi:[0,1,0]          // 000000004BF4: D3A00000 140253DA
	v_fma_mix_f32 v57, v229, v223, v57 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004BFC: D3A01039 14E7BFE5
	v_mul_f32_e32 v1, v144, v1                                 // 000000004C04: 0A020390
	v_fma_mix_f32 v0, v219, v53, v0 op_sel_hi:[0,1,0]          // 000000004C08: D3A00000 14026BDB
	buffer_store_dword v115, off, s[24:27], 0 offset:80        // 000000004C10: E0700050 80067300
	buffer_store_dword v57, off, s[24:27], 0 offset:116        // 000000004C18: E0700074 80063900
	v_fmac_f32_e32 v1, v204, v163                              // 000000004C20: 760347CC
	v_fma_mix_f32 v0, v227, v85, v0 op_sel_hi:[0,1,0]          // 000000004C24: D3A00000 1402ABE3
	v_fma_mix_f32 v1, v145, v5, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004C2C: D3A01001 14060B91
	v_fma_mix_f32 v115, v229, v45, v0 op_sel_hi:[0,1,0]        // 000000004C34: D3A00073 14025BE5
	v_mul_f32_e32 v0, v144, v4                                 // 000000004C3C: 0A000990
	buffer_load_dword v4, off, s[24:27], 0 offset:28           // 000000004C40: E050001C 80060400
	buffer_load_dword v5, off, s[24:27], 0 offset:32           // 000000004C48: E0500020 80060500
	v_fma_mix_f32 v1, v146, v13, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004C50: D3A01001 14061B92
	v_fma_mix_f32 v1, v157, v21, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004C58: D3A01001 14062B9D
	v_fma_mix_f32 v1, v209, v29, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004C60: D3A01001 14063BD1
	v_cvt_f32_f16_sdwa v2, v2 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004C68: 7E0416F9 00050602
	v_fma_mix_f32 v1, v218, v41, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004C70: D3A01001 140653DA
	v_fma_mix_f32 v1, v219, v53, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004C78: D3A01001 14066BDB
	v_fma_mix_f32 v1, v227, v85, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004C80: D3A01001 1406ABE3
	v_fma_mix_f32 v207, v229, v45, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004C88: D3A010CF 14065BE5
	v_mul_f32_e32 v1, v144, v2                                 // 000000004C90: 0A020590
	v_cvt_f32_f16_e32 v2, v3                                   // 000000004C94: 7E041703
	v_cvt_f32_f16_sdwa v3, v3 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004C98: 7E0616F9 00050603
	v_fmac_f32_e32 v9, v204, v123                              // 000000004CA0: 7612F7CC
	v_fma_mix_f32 v9, v145, v18, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CA4: D3A01009 14262591
	v_fma_mix_f32 v9, v146, v26, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CAC: D3A01009 14263592
	v_fma_mix_f32 v9, v157, v38, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CB4: D3A01009 14264D9D
	v_fma_mix_f32 v9, v209, v50, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CBC: D3A01009 142665D1
	v_cvt_f32_f16_sdwa v11, v11 dst_sel:DWORD dst_unused:UNUSED_PAD src0_sel:WORD_1// 000000004CC4: 7E1616F9 0005060B
	v_fma_mix_f32 v9, v218, v66, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CCC: D3A01009 142685DA
	v_fma_mix_f32 v9, v219, v78, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CD4: D3A01009 14269DDB
	v_fma_mix_f32 v9, v227, v98, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CDC: D3A01009 1426C5E3
	v_fma_mix_f32 v231, v229, v34, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CE4: D3A010E7 142645E5
	v_mul_f32_e32 v9, v144, v11                                // 000000004CEC: 0A121790
	v_fmac_f32_e32 v9, v204, v125                              // 000000004CF0: 7612FBCC
	v_fma_mix_f32 v9, v145, v19, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CF4: D3A01009 14262791
	v_fma_mix_f32 v9, v146, v27, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004CFC: D3A01009 14263792
	v_fma_mix_f32 v9, v157, v39, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D04: D3A01009 14264F9D
	v_fma_mix_f32 v9, v209, v51, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D0C: D3A01009 142667D1
	v_fma_mix_f32 v9, v218, v67, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D14: D3A01009 142687DA
	v_fma_mix_f32 v9, v219, v79, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D1C: D3A01009 14269FDB
	v_fma_mix_f32 v9, v227, v99, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D24: D3A01009 1426C7E3
	v_fma_mix_f32 v215, v229, v35, v9 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D2C: D3A010D7 142647E5
	v_fma_mix_f32 v112, v229, v112, v193 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D34: D3A01070 1706E1E5
	s_waitcnt vmcnt(0)                                         // 000000004D3C: BF8C0F70
	v_fmac_f32_e32 v1, v204, v5                                // 000000004D40: 76020BCC
	v_fmac_f32_e32 v0, v204, v4                                // 000000004D44: 760009CC
	v_fma_mix_f32 v0, v145, v6, v0 op_sel_hi:[0,1,0]           // 000000004D48: D3A00000 14020D91
	v_fma_mix_f32 v1, v145, v6, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D50: D3A01001 14060D91
	v_fma_mix_f32 v1, v146, v14, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D58: D3A01001 14061D92
	v_fma_mix_f32 v0, v146, v14, v0 op_sel_hi:[0,1,0]          // 000000004D60: D3A00000 14021D92
	v_fma_mix_f32 v0, v157, v22, v0 op_sel_hi:[0,1,0]          // 000000004D68: D3A00000 14022D9D
	v_fma_mix_f32 v1, v157, v22, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D70: D3A01001 14062D9D
	v_fma_mix_f32 v1, v209, v30, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D78: D3A01001 14063DD1
	v_fma_mix_f32 v0, v209, v30, v0 op_sel_hi:[0,1,0]          // 000000004D80: D3A00000 14023DD1
	v_fma_mix_f32 v0, v218, v42, v0 op_sel_hi:[0,1,0]          // 000000004D88: D3A00000 140255DA
	v_fma_mix_f32 v1, v218, v42, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D90: D3A01001 140655DA
	v_fma_mix_f32 v1, v219, v54, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004D98: D3A01001 14066DDB
	v_fma_mix_f32 v0, v219, v54, v0 op_sel_hi:[0,1,0]          // 000000004DA0: D3A00000 14026DDB
	v_fma_mix_f32 v0, v227, v86, v0 op_sel_hi:[0,1,0]          // 000000004DA8: D3A00000 1402ADE3
	v_fma_mix_f32 v1, v227, v86, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004DB0: D3A01001 1406ADE3
	v_fma_mix_f32 v208, v229, v46, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004DB8: D3A010D0 14065DE5
	v_fma_mix_f32 v113, v229, v46, v0 op_sel_hi:[0,1,0]        // 000000004DC0: D3A00071 14025DE5
	v_mul_f32_e32 v0, v144, v2                                 // 000000004DC8: 0A000590
	v_mul_f32_e32 v1, v144, v3                                 // 000000004DCC: 0A020790
	buffer_load_dword v2, off, s[24:27], 0 offset:36           // 000000004DD0: E0500024 80060200
	buffer_load_dword v3, off, s[24:27], 0 offset:40           // 000000004DD8: E0500028 80060300
	v_add_f32_e32 v4, v230, v229                               // 000000004DE0: 0209CBE6
	s_waitcnt vmcnt(1)                                         // 000000004DE4: BF8C0F71
	v_fmac_f32_e32 v0, v204, v2                                // 000000004DE8: 760005CC
	v_fma_mix_f32 v0, v145, v7, v0 op_sel_hi:[0,1,0]           // 000000004DEC: D3A00000 14020F91
	v_fma_mix_f32 v0, v146, v15, v0 op_sel_hi:[0,1,0]          // 000000004DF4: D3A00000 14021F92
	v_fma_mix_f32 v0, v157, v23, v0 op_sel_hi:[0,1,0]          // 000000004DFC: D3A00000 14022F9D
	v_fma_mix_f32 v0, v209, v31, v0 op_sel_hi:[0,1,0]          // 000000004E04: D3A00000 14023FD1
	v_fma_mix_f32 v0, v218, v43, v0 op_sel_hi:[0,1,0]          // 000000004E0C: D3A00000 140257DA
	v_fma_mix_f32 v0, v219, v55, v0 op_sel_hi:[0,1,0]          // 000000004E14: D3A00000 14026FDB
	v_fma_mix_f32 v0, v227, v87, v0 op_sel_hi:[0,1,0]          // 000000004E1C: D3A00000 1402AFE3
	v_fma_mix_f32 v104, v229, v47, v0 op_sel_hi:[0,1,0]        // 000000004E24: D3A00068 14025FE5
	buffer_load_dword v0, off, s[24:27], 0 offset:24           // 000000004E2C: E0500018 80060000
	s_waitcnt vmcnt(1)                                         // 000000004E34: BF8C0F71
	v_fmac_f32_e32 v1, v204, v3                                // 000000004E38: 760207CC
	v_fma_mix_f32 v1, v145, v7, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004E3C: D3A01001 14060F91
	v_fma_mix_f32 v1, v146, v15, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004E44: D3A01001 14061F92
	v_fma_mix_f32 v1, v157, v23, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004E4C: D3A01001 14062F9D
	v_fma_mix_f32 v1, v209, v31, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004E54: D3A01001 14063FD1
	v_fma_mix_f32 v1, v218, v43, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004E5C: D3A01001 140657DA
	v_fma_mix_f32 v1, v219, v55, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004E64: D3A01001 14066FDB
	v_fma_mix_f32 v1, v227, v87, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004E6C: D3A01001 1406AFE3
	v_fma_mix_f32 v146, v229, v47, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004E74: D3A01092 14065FE5
	s_waitcnt vmcnt(0)                                         // 000000004E7C: BF8C0F70
	v_sub_f32_e32 v0, v0, v195                                 // 000000004E80: 04018700
	v_mul_f32_e32 v0, 0x3fb8aa3b, v0                           // 000000004E84: 0A0000FF 3FB8AA3B
	v_exp_f32_e32 v197, v0                                     // 000000004E8C: 7F8A4100
	ds_read_b128 v[44:47], v196 offset:9344                    // 000000004E90: D9FE2480 2C0000C4
	ds_read_b128 v[96:99], v196 offset:9360                    // 000000004E98: D9FE2490 600000C4
	ds_read_b128 v[106:109], v196 offset:9376                  // 000000004EA0: D9FE24A0 6A0000C4
	ds_read_b128 v[209:212], v196 offset:9392                  // 000000004EA8: D9FE24B0 D10000C4
	ds_read_b128 v[68:71], v196 offset:9408                    // 000000004EB0: D9FE24C0 440000C4
	ds_read_b128 v[40:43], v196 offset:9424                    // 000000004EB8: D9FE24D0 280000C4
	ds_read_b128 v[20:23], v196 offset:9440                    // 000000004EC0: D9FE24E0 140000C4
	ds_read_b128 v[0:3], v196 offset:9456                      // 000000004EC8: D9FE24F0 000000C4
	v_add_f32_e32 v8, v4, v197                                 // 000000004ED0: 02118B04
	buffer_load_dword v4, off, s[24:27], 0 offset:16           // 000000004ED4: E0500010 80060400
	s_waitcnt lgkmcnt(7)                                       // 000000004EDC: BF8CC77F
	v_fma_mix_f32 v145, v197, v44, v228 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004EE0: D3A01091 179259C5
	v_fma_mix_f32 v44, v197, v44, v237 op_sel_hi:[0,1,0]       // 000000004EE8: D3A0002C 17B659C5
	v_fma_mix_f32 v204, v197, v45, v233 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004EF0: D3A010CC 17A65BC5
	v_fma_mix_f32 v45, v197, v45, v205 op_sel_hi:[0,1,0]       // 000000004EF8: D3A0002D 17365BC5
	v_fma_mix_f32 v205, v197, v46, v240 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004F00: D3A010CD 17C25DC5
	v_fma_mix_f32 v46, v197, v46, v236 op_sel_hi:[0,1,0]       // 000000004F08: D3A0002E 17B25DC5
	v_fma_mix_f32 v227, v197, v47, v249 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004F10: D3A010E3 17E65FC5
	v_fma_mix_f32 v47, v197, v47, v248 op_sel_hi:[0,1,0]       // 000000004F18: D3A0002F 17E25FC5
	s_waitcnt lgkmcnt(6)                                       // 000000004F20: BF8CC67F
	v_fma_mix_f32 v112, v197, v96, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004F24: D3A01070 15C2C1C5
	v_fma_mix_f32 v96, v197, v96, v206 op_sel_hi:[0,1,0]       // 000000004F2C: D3A00060 173AC1C5
	s_waitcnt vmcnt(0)                                         // 000000004F34: BF8C0F70
	v_sub_f32_e32 v4, v4, v195                                 // 000000004F38: 04098704
	v_mul_f32_e32 v4, 0x3fb8aa3b, v4                           // 000000004F3C: 0A0808FF 3FB8AA3B
	v_exp_f32_e32 v198, v4                                     // 000000004F44: 7F8C4104
	ds_read_b128 v[64:67], v196 offset:9472                    // 000000004F48: D9FE2500 400000C4
	ds_read_b128 v[100:103], v196 offset:9488                  // 000000004F50: D9FE2510 640000C4
	ds_read_b128 v[148:151], v196 offset:9504                  // 000000004F58: D9FE2520 940000C4
	ds_read_b128 v[218:221], v196 offset:9520                  // 000000004F60: D9FE2530 DA0000C4
	ds_read_b128 v[72:75], v196 offset:9536                    // 000000004F68: D9FE2540 480000C4
	ds_read_b128 v[48:51], v196 offset:9552                    // 000000004F70: D9FE2550 300000C4
	ds_read_b128 v[24:27], v196 offset:9568                    // 000000004F78: D9FE2560 180000C4
	ds_read_b128 v[4:7], v196 offset:9584                      // 000000004F80: D9FE2570 040000C4
	v_add_f32_e32 v12, v8, v198                                // 000000004F88: 02198D08
	buffer_load_dword v8, off, s[24:27], 0 offset:8            // 000000004F8C: E0500008 80060800
	s_waitcnt lgkmcnt(7)                                       // 000000004F94: BF8CC77F
	v_fma_mix_f32 v44, v198, v64, v44 op_sel_hi:[0,1,0]        // 000000004F98: D3A0002C 14B281C6
	v_fma_mix_f32 v64, v198, v64, v145 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004FA0: D3A01040 164681C6
	v_fma_mix_f32 v45, v198, v65, v45 op_sel_hi:[0,1,0]        // 000000004FA8: D3A0002D 14B683C6
	v_fma_mix_f32 v65, v198, v65, v204 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004FB0: D3A01041 173283C6
	v_fma_mix_f32 v46, v198, v66, v46 op_sel_hi:[0,1,0]        // 000000004FB8: D3A0002E 14BA85C6
	v_fma_mix_f32 v66, v198, v66, v205 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004FC0: D3A01042 173685C6
	v_fma_mix_f32 v47, v198, v67, v47 op_sel_hi:[0,1,0]        // 000000004FC8: D3A0002F 14BE87C6
	v_fma_mix_f32 v67, v198, v67, v227 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000004FD0: D3A01043 178E87C6
	s_waitcnt lgkmcnt(6)                                       // 000000004FD8: BF8CC67F
	v_fma_mix_f32 v96, v198, v100, v96 op_sel_hi:[0,1,0]       // 000000004FDC: D3A00060 1582C9C6
	s_waitcnt vmcnt(0)                                         // 000000004FE4: BF8C0F70
	v_sub_f32_e32 v8, v8, v195                                 // 000000004FE8: 04118708
	v_mul_f32_e32 v8, 0x3fb8aa3b, v8                           // 000000004FEC: 0A1010FF 3FB8AA3B
	v_exp_f32_e32 v199, v8                                     // 000000004FF4: 7F8E4108
	ds_read_b128 v[88:91], v196 offset:9600                    // 000000004FF8: D9FE2580 580000C4
	ds_read_b128 v[152:155], v196 offset:9616                  // 000000005000: D9FE2590 980000C4
	ds_read_b128 v[222:225], v196 offset:9632                  // 000000005008: D9FE25A0 DE0000C4
	ds_read_b128 v[242:245], v196 offset:9648                  // 000000005010: D9FE25B0 F20000C4
	ds_read_b128 v[76:79], v196 offset:9664                    // 000000005018: D9FE25C0 4C0000C4
	ds_read_b128 v[52:55], v196 offset:9680                    // 000000005020: D9FE25D0 340000C4
	ds_read_b128 v[28:31], v196 offset:9696                    // 000000005028: D9FE25E0 1C0000C4
	ds_read_b128 v[8:11], v196 offset:9712                     // 000000005030: D9FE25F0 080000C4
	v_add_f32_e32 v16, v12, v199                               // 000000005038: 02218F0C
	buffer_load_dword v12, off, s[24:27], 0 offset:20          // 00000000503C: E0500014 80060C00
	s_waitcnt lgkmcnt(7)                                       // 000000005044: BF8CC77F
	v_fma_mix_f32 v44, v199, v88, v44 op_sel_hi:[0,1,0]        // 000000005048: D3A0002C 14B2B1C7
	v_fma_mix_f32 v64, v199, v88, v64 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005050: D3A01040 1502B1C7
	v_fma_mix_f32 v65, v199, v89, v65 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005058: D3A01041 1506B3C7
	v_fma_mix_f32 v45, v199, v89, v45 op_sel_hi:[0,1,0]        // 000000005060: D3A0002D 14B6B3C7
	v_fma_mix_f32 v46, v199, v90, v46 op_sel_hi:[0,1,0]        // 000000005068: D3A0002E 14BAB5C7
	v_fma_mix_f32 v66, v199, v90, v66 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005070: D3A01042 150AB5C7
	v_fma_mix_f32 v47, v199, v91, v47 op_sel_hi:[0,1,0]        // 000000005078: D3A0002F 14BEB7C7
	v_fma_mix_f32 v67, v199, v91, v67 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005080: D3A01043 150EB7C7
	s_waitcnt lgkmcnt(6)                                       // 000000005088: BF8CC67F
	v_fma_mix_f32 v96, v199, v152, v96 op_sel_hi:[0,1,0]       // 00000000508C: D3A00060 158331C7
	s_waitcnt vmcnt(0)                                         // 000000005094: BF8C0F70
	v_sub_f32_e32 v12, v12, v195                               // 000000005098: 0419870C
	v_mul_f32_e32 v12, 0x3fb8aa3b, v12                         // 00000000509C: 0A1818FF 3FB8AA3B
	v_exp_f32_e32 v200, v12                                    // 0000000050A4: 7F90410C
	ds_read_b128 v[92:95], v196 offset:9728                    // 0000000050A8: D9FE2600 5C0000C4
	ds_read_b128 v[250:253], v196 offset:9744                  // 0000000050B0: D9FE2610 FA0000C4
	ds_read_b128 v[136:139], v196 offset:9760                  // 0000000050B8: D9FE2620 880000C4
	ds_read_b128 v[128:131], v196 offset:9776                  // 0000000050C0: D9FE2630 800000C4
	ds_read_b128 v[80:83], v196 offset:9792                    // 0000000050C8: D9FE2640 500000C4
	ds_read_b128 v[56:59], v196 offset:9808                    // 0000000050D0: D9FE2650 380000C4
	ds_read_b128 v[32:35], v196 offset:9824                    // 0000000050D8: D9FE2660 200000C4
	ds_read_b128 v[12:15], v196 offset:9840                    // 0000000050E0: D9FE2670 0C0000C4
	v_add_f32_e32 v116, v16, v200                              // 0000000050E8: 02E99110
	buffer_load_dword v16, off, s[24:27], 0 offset:12          // 0000000050EC: E050000C 80061000
	s_waitcnt lgkmcnt(7)                                       // 0000000050F4: BF8CC77F
	v_fma_mix_f32 v44, v200, v92, v44 op_sel_hi:[0,1,0]        // 0000000050F8: D3A0002C 14B2B9C8
	v_fma_mix_f32 v64, v200, v92, v64 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005100: D3A01040 1502B9C8
	v_fma_mix_f32 v45, v200, v93, v45 op_sel_hi:[0,1,0]        // 000000005108: D3A0002D 14B6BBC8
	v_fma_mix_f32 v65, v200, v93, v65 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005110: D3A01041 1506BBC8
	v_fma_mix_f32 v46, v200, v94, v46 op_sel_hi:[0,1,0]        // 000000005118: D3A0002E 14BABDC8
	v_fma_mix_f32 v66, v200, v94, v66 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005120: D3A01042 150ABDC8
	v_fma_mix_f32 v47, v200, v95, v47 op_sel_hi:[0,1,0]        // 000000005128: D3A0002F 14BEBFC8
	v_fma_mix_f32 v67, v200, v95, v67 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005130: D3A01043 150EBFC8
	s_waitcnt lgkmcnt(6)                                       // 000000005138: BF8CC67F
	v_fma_mix_f32 v96, v200, v250, v96 op_sel_hi:[0,1,0]       // 00000000513C: D3A00060 1583F5C8
	s_waitcnt vmcnt(0)                                         // 000000005144: BF8C0F70
	v_sub_f32_e32 v16, v16, v195                               // 000000005148: 04218710
	v_mul_f32_e32 v16, 0x3fb8aa3b, v16                         // 00000000514C: 0A2020FF 3FB8AA3B
	v_exp_f32_e32 v201, v16                                    // 000000005154: 7F924110
	ds_read_b128 v[122:125], v196 offset:9856                  // 000000005158: D9FE2680 7A0000C4
	ds_read_b128 v[191:194], v196 offset:9872                  // 000000005160: D9FE2690 BF0000C4
	ds_read_b128 v[157:160], v196 offset:9888                  // 000000005168: D9FE26A0 9D0000C4
	ds_read_b128 v[161:164], v196 offset:9904                  // 000000005170: D9FE26B0 A10000C4
	ds_read_b128 v[84:87], v196 offset:9920                    // 000000005178: D9FE26C0 540000C4
	ds_read_b128 v[60:63], v196 offset:9936                    // 000000005180: D9FE26D0 3C0000C4
	ds_read_b128 v[36:39], v196 offset:9952                    // 000000005188: D9FE26E0 240000C4
	ds_read_b128 v[16:19], v196 offset:9968                    // 000000005190: D9FE26F0 100000C4
	v_add_f32_e32 v144, v116, v201                             // 000000005198: 03219374
	buffer_load_dword v116, off, s[24:27], 0 offset:4          // 00000000519C: E0500004 80067400
	s_waitcnt lgkmcnt(7)                                       // 0000000051A4: BF8CC77F
	v_fma_mix_f32 v44, v201, v122, v44 op_sel_hi:[0,1,0]       // 0000000051A8: D3A0002C 14B2F5C9
	v_fma_mix_f32 v64, v201, v122, v64 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000051B0: D3A01040 1502F5C9
	v_fma_mix_f32 v45, v201, v123, v45 op_sel_hi:[0,1,0]       // 0000000051B8: D3A0002D 14B6F7C9
	s_waitcnt lgkmcnt(6)                                       // 0000000051C0: BF8CC67F
	v_fma_mix_f32 v96, v201, v191, v96 op_sel_hi:[0,1,0]       // 0000000051C4: D3A00060 15837FC9
	s_waitcnt vmcnt(0)                                         // 0000000051CC: BF8C0F70
	v_sub_f32_e32 v116, v116, v195                             // 0000000051D0: 04E98774
	v_mul_f32_e32 v116, 0x3fb8aa3b, v116                       // 0000000051D4: 0AE8E8FF 3FB8AA3B
	v_exp_f32_e32 v203, v116                                   // 0000000051DC: 7F964174
	ds_read_b128 v[116:119], v196 offset:9984                  // 0000000051E0: D9FE2700 740000C4
	ds_read_b128 v[165:168], v196 offset:10000                 // 0000000051E8: D9FE2710 A50000C4
	buffer_load_dword v145, off, s[24:27], 0                   // 0000000051F0: E0500000 80069100
	ds_read_b128 v[132:135], v196 offset:10016                 // 0000000051F8: D9FE2720 840000C4
	ds_read_b128 v[227:230], v196 offset:10032                 // 000000005200: D9FE2730 E30000C4
	s_waitcnt lgkmcnt(3)                                       // 000000005208: BF8CC37F
	v_fma_mix_f32 v122, v203, v116, v44 op_sel_hi:[0,1,0]      // 00000000520C: D3A0007A 14B2E9CB
	v_fma_mix_f32 v44, v201, v123, v65 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005214: D3A0102C 1506F7C9
	v_fma_mix_f32 v123, v203, v117, v45 op_sel_hi:[0,1,0]      // 00000000521C: D3A0007B 14B6EBCB
	v_fma_mix_f32 v117, v203, v117, v44 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005224: D3A01075 14B2EBCB
	v_fma_mix_f32 v44, v201, v124, v46 op_sel_hi:[0,1,0]       // 00000000522C: D3A0002C 14BAF9C9
	v_fma_mix_f32 v116, v203, v116, v64 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005234: D3A01074 1502E9CB
	v_fma_mix_f32 v64, v201, v124, v66 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000523C: D3A01040 150AF9C9
	v_fma_mix_f32 v124, v203, v118, v44 op_sel_hi:[0,1,0]      // 000000005244: D3A0007C 14B2EDCB
	v_fma_mix_f32 v66, v201, v125, v47 op_sel_hi:[0,1,0]       // 00000000524C: D3A00042 14BEFBC9
	ds_read_b128 v[44:47], v196 offset:10112                   // 000000005254: D9FE2780 2C0000C4
	v_fma_mix_f32 v65, v201, v125, v67 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000525C: D3A01041 150EFBC9
	v_fma_mix_f32 v125, v203, v119, v66 op_sel_hi:[0,1,0]      // 000000005264: D3A0007D 150AEFCB
	v_add_f32_e32 v204, v144, v203                             // 00000000526C: 03999790
	v_fma_mix_f32 v118, v203, v118, v64 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005270: D3A01076 1502EDCB
	v_fma_mix_f32 v119, v203, v119, v65 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005278: D3A01077 1506EFCB
	s_waitcnt lgkmcnt(3)                                       // 000000005280: BF8CC37F
	v_fma_mix_f32 v96, v203, v165, v96 op_sel_hi:[0,1,0]       // 000000005284: D3A00060 15834BCB
	ds_read_b128 v[88:91], v196 offset:10048                   // 00000000528C: D9FE2740 580000C4
	ds_read_b128 v[92:95], v196 offset:10064                   // 000000005294: D9FE2750 5C0000C4
	ds_read_b128 v[64:67], v196 offset:10080                   // 00000000529C: D9FE2760 400000C4
	s_waitcnt vmcnt(0)                                         // 0000000052A4: BF8C0F70
	v_sub_f32_e32 v145, v145, v195                             // 0000000052A8: 05238791
	v_mul_f32_e32 v145, 0x3fb8aa3b, v145                       // 0000000052AC: 0B2322FF 3FB8AA3B
	v_exp_f32_e32 v202, v145                                   // 0000000052B4: 7F944191
	s_waitcnt lgkmcnt(3)                                       // 0000000052B8: BF8CC37F
	v_fma_mix_f32 v236, v202, v44, v122 op_sel_hi:[0,1,0]      // 0000000052BC: D3A000EC 15EA59CA
	v_fma_mix_f32 v248, v202, v45, v123 op_sel_hi:[0,1,0]      // 0000000052C4: D3A000F8 15EE5BCA
	v_fma_mix_f32 v122, v197, v97, v156 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000052CC: D3A0107A 1672C3C5
	v_fma_mix_f32 v123, v197, v97, v232 op_sel_hi:[0,1,0]      // 0000000052D4: D3A0007B 17A2C3C5
	buffer_load_dword v97, off, s[24:27], 0 offset:172         // 0000000052DC: E05000AC 80066100
	v_fma_mix_f32 v254, v202, v47, v125 op_sel_hi:[0,1,0]      // 0000000052E4: D3A000FE 15F65FCA
	v_fma_mix_f32 v237, v202, v44, v116 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000052EC: D3A010ED 15D259CA
	v_fma_mix_f32 v249, v202, v45, v117 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000052F4: D3A010F9 15D65BCA
	v_fma_mix_f32 v247, v202, v46, v118 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000052FC: D3A010F7 15DA5DCA
	v_fma_mix_f32 v255, v202, v47, v119 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005304: D3A010FF 15DE5FCA
	ds_read_b128 v[116:119], v196 offset:10128                 // 00000000530C: D9FE2790 740000C4
	v_fma_mix_f32 v246, v202, v46, v124 op_sel_hi:[0,1,0]      // 000000005314: D3A000F6 15F25DCA
	v_fma_mix_f32 v124, v197, v98, v241 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000531C: D3A0107C 17C6C5C5
	ds_read_b128 v[44:47], v196 offset:10096                   // 000000005324: D9FE2770 2C0000C4
	s_waitcnt vmcnt(0)                                         // 00000000532C: BF8C0F70
	v_fma_mix_f32 v125, v197, v98, v97 op_sel_hi:[0,1,0]       // 000000005330: D3A0007D 1586C5C5
	buffer_load_dword v97, off, s[24:27], 0 offset:168         // 000000005338: E05000A8 80066100
	v_fma_mix_f32 v98, v198, v101, v123 op_sel_hi:[0,1,0]      // 000000005340: D3A00062 15EECBC6
	v_fma_mix_f32 v98, v199, v153, v98 op_sel_hi:[0,1,0]       // 000000005348: D3A00062 158B33C7
	v_fma_mix_f32 v98, v200, v251, v98 op_sel_hi:[0,1,0]       // 000000005350: D3A00062 158BF7C8
	v_fma_mix_f32 v98, v201, v192, v98 op_sel_hi:[0,1,0]       // 000000005358: D3A00062 158B81C9
	v_fma_mix_f32 v98, v203, v166, v98 op_sel_hi:[0,1,0]       // 000000005360: D3A00062 158B4DCB
	s_waitcnt vmcnt(0)                                         // 000000005368: BF8C0F70
	v_fma_mix_f32 v144, v197, v99, v97 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000536C: D3A01090 1586C7C5
	buffer_load_dword v97, off, s[24:27], 0 offset:164         // 000000005374: E05000A4 80066100
	s_waitcnt vmcnt(0)                                         // 00000000537C: BF8C0F70
	v_fma_mix_f32 v145, v197, v99, v97 op_sel_hi:[0,1,0]       // 000000005380: D3A00091 1586C7C5
	v_fma_mix_f32 v97, v198, v100, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005388: D3A01061 15C2C9C6
	v_fma_mix_f32 v97, v199, v152, v97 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005390: D3A01061 158731C7
	v_fma_mix_f32 v97, v200, v250, v97 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005398: D3A01061 1587F5C8
	v_fma_mix_f32 v97, v201, v191, v97 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000053A0: D3A01061 15877FC9
	v_fma_mix_f32 v97, v203, v165, v97 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000053A8: D3A01061 15874BCB
	v_fma_mix_f32 v99, v198, v101, v122 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000053B0: D3A01063 15EACBC6
	v_fma_mix_f32 v100, v198, v102, v125 op_sel_hi:[0,1,0]     // 0000000053B8: D3A00064 15F6CDC6
	v_fma_mix_f32 v101, v198, v102, v124 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000053C0: D3A01065 15F2CDC6
	ds_read_b128 v[122:125], v196 offset:10160                 // 0000000053C8: D9FE27B0 7A0000C4
	s_waitcnt lgkmcnt(2)                                       // 0000000053D0: BF8CC27F
	v_fma_mix_f32 v97, v202, v116, v97 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000053D4: D3A01061 1586E9CA
	v_fma_mix_f32 v96, v202, v116, v96 op_sel_hi:[0,1,0]       // 0000000053DC: D3A00060 1582E9CA
	buffer_load_dword v112, off, s[24:27], 0 offset:160        // 0000000053E4: E05000A0 80067000
	buffer_load_dword v116, off, s[24:27], 0 offset:156        // 0000000053EC: E050009C 80067400
	v_fma_mix_f32 v102, v198, v103, v145 op_sel_hi:[0,1,0]     // 0000000053F4: D3A00066 1646CFC6
	v_fma_mix_f32 v103, v198, v103, v144 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000053FC: D3A01067 1642CFC6
	v_fma_mix_f32 v99, v199, v153, v99 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005404: D3A01063 158F33C7
	v_fma_mix_f32 v101, v199, v154, v101 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000540C: D3A01065 159735C7
	v_fma_mix_f32 v100, v199, v154, v100 op_sel_hi:[0,1,0]     // 000000005414: D3A00064 159335C7
	v_fma_mix_f32 v103, v199, v155, v103 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000541C: D3A01067 159F37C7
	v_fma_mix_f32 v102, v199, v155, v102 op_sel_hi:[0,1,0]     // 000000005424: D3A00066 159B37C7
	v_fma_mix_f32 v99, v200, v251, v99 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000542C: D3A01063 158FF7C8
	v_fma_mix_f32 v100, v200, v252, v100 op_sel_hi:[0,1,0]     // 000000005434: D3A00064 1593F9C8
	v_fma_mix_f32 v101, v200, v252, v101 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000543C: D3A01065 1597F9C8
	v_fma_mix_f32 v102, v200, v253, v102 op_sel_hi:[0,1,0]     // 000000005444: D3A00066 159BFBC8
	v_fma_mix_f32 v103, v200, v253, v103 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000544C: D3A01067 159FFBC8
	v_fma_mix_f32 v99, v201, v192, v99 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005454: D3A01063 158F81C9
	v_fma_mix_f32 v101, v201, v193, v101 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000545C: D3A01065 159783C9
	v_fma_mix_f32 v100, v201, v193, v100 op_sel_hi:[0,1,0]     // 000000005464: D3A00064 159383C9
	v_fma_mix_f32 v103, v201, v194, v103 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000546C: D3A01067 159F85C9
	v_fma_mix_f32 v102, v201, v194, v102 op_sel_hi:[0,1,0]     // 000000005474: D3A00066 159B85C9
	v_fma_mix_f32 v99, v203, v166, v99 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000547C: D3A01063 158F4DCB
	v_fma_mix_f32 v100, v203, v167, v100 op_sel_hi:[0,1,0]     // 000000005484: D3A00064 15934FCB
	v_fma_mix_f32 v101, v203, v167, v101 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000548C: D3A01065 15974FCB
	v_fma_mix_f32 v102, v203, v168, v102 op_sel_hi:[0,1,0]     // 000000005494: D3A00066 159B51CB
	v_fma_mix_f32 v103, v203, v168, v103 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000549C: D3A01067 159F51CB
	v_fma_mix_f32 v99, v202, v117, v99 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000054A4: D3A01063 158EEBCA
	v_fma_mix_f32 v98, v202, v117, v98 op_sel_hi:[0,1,0]       // 0000000054AC: D3A00062 158AEBCA
	v_fma_mix_f32 v101, v202, v118, v101 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000054B4: D3A01065 1596EDCA
	v_fma_mix_f32 v100, v202, v118, v100 op_sel_hi:[0,1,0]     // 0000000054BC: D3A00064 1592EDCA
	v_fma_mix_f32 v103, v202, v119, v103 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000054C4: D3A01067 159EEFCA
	v_fma_mix_f32 v102, v202, v119, v102 op_sel_hi:[0,1,0]     // 0000000054CC: D3A00066 159AEFCA
	s_waitcnt vmcnt(1)                                         // 0000000054D4: BF8C0F71
	v_fma_mix_f32 v112, v197, v106, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000054D8: D3A01070 15C2D5C5
	s_waitcnt vmcnt(0)                                         // 0000000054E0: BF8C0F70
	v_fma_mix_f32 v106, v197, v106, v116 op_sel_hi:[0,1,0]     // 0000000054E4: D3A0006A 15D2D5C5
	v_fma_mix_f32 v106, v198, v148, v106 op_sel_hi:[0,1,0]     // 0000000054EC: D3A0006A 15AB29C6
	v_fma_mix_f32 v112, v198, v148, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000054F4: D3A01070 15C329C6
	ds_read_b128 v[116:119], v196 offset:10144                 // 0000000054FC: D9FE27A0 740000C4
	v_fma_mix_f32 v112, v199, v222, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005504: D3A01070 15C3BDC7
	v_fma_mix_f32 v106, v199, v222, v106 op_sel_hi:[0,1,0]     // 00000000550C: D3A0006A 15ABBDC7
	v_fma_mix_f32 v106, v200, v136, v106 op_sel_hi:[0,1,0]     // 000000005514: D3A0006A 15AB11C8
	v_fma_mix_f32 v112, v200, v136, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000551C: D3A01070 15C311C8
	v_fma_mix_f32 v112, v201, v157, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005524: D3A01070 15C33BC9
	v_fma_mix_f32 v106, v201, v157, v106 op_sel_hi:[0,1,0]     // 00000000552C: D3A0006A 15AB3BC9
	v_fma_mix_f32 v106, v203, v132, v106 op_sel_hi:[0,1,0]     // 000000005534: D3A0006A 15AB09CB
	v_fma_mix_f32 v112, v203, v132, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000553C: D3A01070 15C309CB
	s_waitcnt lgkmcnt(0)                                       // 000000005544: BF8CC07F
	v_fma_mix_f32 v145, v202, v116, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005548: D3A01091 15C2E9CA
	v_fma_mix_f32 v144, v202, v116, v106 op_sel_hi:[0,1,0]     // 000000005550: D3A00090 15AAE9CA
	buffer_load_dword v106, off, s[24:27], 0 offset:96         // 000000005558: E0500060 80066A00
	buffer_load_dword v112, off, s[24:27], 0 offset:88         // 000000005560: E0500058 80067000
	buffer_load_dword v116, off, s[24:27], 0 offset:72         // 000000005568: E0500048 80067400
	s_waitcnt vmcnt(2)                                         // 000000005570: BF8C0F72
	v_fma_mix_f32 v106, v197, v107, v106 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005574: D3A0106A 15AAD7C5
	s_waitcnt vmcnt(1)                                         // 00000000557C: BF8C0F71
	v_fma_mix_f32 v107, v197, v107, v112 op_sel_hi:[0,1,0]     // 000000005580: D3A0006B 15C2D7C5
	v_fma_mix_f32 v107, v198, v149, v107 op_sel_hi:[0,1,0]     // 000000005588: D3A0006B 15AF2BC6
	v_fma_mix_f32 v106, v198, v149, v106 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005590: D3A0106A 15AB2BC6
	v_fma_mix_f32 v106, v199, v223, v106 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005598: D3A0106A 15ABBFC7
	v_fma_mix_f32 v107, v199, v223, v107 op_sel_hi:[0,1,0]     // 0000000055A0: D3A0006B 15AFBFC7
	v_fma_mix_f32 v107, v200, v137, v107 op_sel_hi:[0,1,0]     // 0000000055A8: D3A0006B 15AF13C8
	v_fma_mix_f32 v106, v200, v137, v106 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000055B0: D3A0106A 15AB13C8
	v_fma_mix_f32 v106, v201, v158, v106 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000055B8: D3A0106A 15AB3DC9
	v_fma_mix_f32 v107, v201, v158, v107 op_sel_hi:[0,1,0]     // 0000000055C0: D3A0006B 15AF3DC9
	v_fma_mix_f32 v112, v203, v133, v107 op_sel_hi:[0,1,0]     // 0000000055C8: D3A00070 15AF0BCB
	v_fma_mix_f32 v106, v203, v133, v106 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000055D0: D3A0106A 15AB0BCB
	v_fma_mix_f32 v107, v202, v117, v106 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000055D8: D3A0106B 15AAEBCA
	v_fma_mix_f32 v106, v202, v117, v112 op_sel_hi:[0,1,0]     // 0000000055E0: D3A0006A 15C2EBCA
	buffer_load_dword v112, off, s[24:27], 0 offset:76         // 0000000055E8: E050004C 80067000
	s_waitcnt vmcnt(0)                                         // 0000000055F0: BF8C0F70
	v_fma_mix_f32 v112, v197, v108, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000055F4: D3A01070 15C2D9C5
	v_fma_mix_f32 v112, v198, v150, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000055FC: D3A01070 15C32DC6
	v_fma_mix_f32 v112, v199, v224, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005604: D3A01070 15C3C1C7
	v_fma_mix_f32 v112, v200, v138, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000560C: D3A01070 15C315C8
	v_fma_mix_f32 v112, v201, v159, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005614: D3A01070 15C33FC9
	v_fma_mix_f32 v112, v203, v134, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000561C: D3A01070 15C30DCB
	v_fma_mix_f32 v149, v202, v118, v112 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005624: D3A01095 15C2EDCA
	buffer_load_dword v112, off, s[24:27], 0 offset:44         // 00000000562C: E050002C 80067000
	v_fma_mix_f32 v108, v197, v108, v116 op_sel_hi:[0,1,0]     // 000000005634: D3A0006C 15D2D9C5
	v_fma_mix_f32 v108, v198, v150, v108 op_sel_hi:[0,1,0]     // 00000000563C: D3A0006C 15B32DC6
	v_fma_mix_f32 v108, v199, v224, v108 op_sel_hi:[0,1,0]     // 000000005644: D3A0006C 15B3C1C7
	v_fma_mix_f32 v108, v200, v138, v108 op_sel_hi:[0,1,0]     // 00000000564C: D3A0006C 15B315C8
	v_fma_mix_f32 v108, v201, v159, v108 op_sel_hi:[0,1,0]     // 000000005654: D3A0006C 15B33FC9
	v_fma_mix_f32 v108, v203, v134, v108 op_sel_hi:[0,1,0]     // 00000000565C: D3A0006C 15B30DCB
	v_fma_mix_f32 v148, v202, v118, v108 op_sel_hi:[0,1,0]     // 000000005664: D3A00094 15B2EDCA
	buffer_load_dword v108, off, s[24:27], 0 offset:92         // 00000000566C: E050005C 80066C00
	s_waitcnt vmcnt(0)                                         // 000000005674: BF8C0F70
	v_fma_mix_f32 v108, v197, v109, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005678: D3A0106C 15B2DBC5
	v_fma_mix_f32 v108, v198, v151, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005680: D3A0106C 15B32FC6
	v_fma_mix_f32 v108, v199, v225, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005688: D3A0106C 15B3C3C7
	v_fma_mix_f32 v108, v200, v139, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005690: D3A0106C 15B317C8
	v_fma_mix_f32 v108, v201, v160, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005698: D3A0106C 15B341C9
	v_fma_mix_f32 v108, v203, v135, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000056A0: D3A0106C 15B30FCB
	v_fma_mix_f32 v153, v202, v119, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000056A8: D3A01099 15B2EFCA
	buffer_load_dword v108, off, s[24:27], 0 offset:84         // 0000000056B0: E0500054 80066C00
	v_fma_mix_f32 v109, v197, v109, v112 op_sel_hi:[0,1,0]     // 0000000056B8: D3A0006D 15C2DBC5
	v_fma_mix_f32 v109, v198, v151, v109 op_sel_hi:[0,1,0]     // 0000000056C0: D3A0006D 15B72FC6
	v_fma_mix_f32 v109, v199, v225, v109 op_sel_hi:[0,1,0]     // 0000000056C8: D3A0006D 15B7C3C7
	v_fma_mix_f32 v109, v200, v139, v109 op_sel_hi:[0,1,0]     // 0000000056D0: D3A0006D 15B717C8
	v_fma_mix_f32 v109, v201, v160, v109 op_sel_hi:[0,1,0]     // 0000000056D8: D3A0006D 15B741C9
	v_fma_mix_f32 v109, v203, v135, v109 op_sel_hi:[0,1,0]     // 0000000056E0: D3A0006D 15B70FCB
	v_fma_mix_f32 v152, v202, v119, v109 op_sel_hi:[0,1,0]     // 0000000056E8: D3A00098 15B6EFCA
	buffer_load_dword v109, off, s[24:27], 0 offset:80         // 0000000056F0: E0500050 80066D00
	ds_read_b128 v[116:119], v196 offset:10176                 // 0000000056F8: D9FE27C0 740000C4
	s_waitcnt vmcnt(1)                                         // 000000005700: BF8C0F71
	v_fma_mix_f32 v108, v197, v209, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005704: D3A0106C 15B3A3C5
	v_fma_mix_f32 v108, v198, v218, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000570C: D3A0106C 15B3B5C6
	v_fma_mix_f32 v108, v199, v242, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005714: D3A0106C 15B3E5C7
	v_fma_mix_f32 v108, v200, v128, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000571C: D3A0106C 15B301C8
	v_fma_mix_f32 v108, v201, v161, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005724: D3A0106C 15B343C9
	v_fma_mix_f32 v108, v203, v227, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000572C: D3A0106C 15B3C7CB
	v_fma_mix_f32 v151, v202, v122, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005734: D3A01097 15B2F5CA
	buffer_load_dword v108, off, s[24:27], 0 offset:60         // 00000000573C: E050003C 80066C00
	s_waitcnt vmcnt(1)                                         // 000000005744: BF8C0F71
	v_fma_mix_f32 v109, v197, v209, v109 op_sel_hi:[0,1,0]     // 000000005748: D3A0006D 15B7A3C5
	v_fma_mix_f32 v109, v198, v218, v109 op_sel_hi:[0,1,0]     // 000000005750: D3A0006D 15B7B5C6
	v_fma_mix_f32 v109, v199, v242, v109 op_sel_hi:[0,1,0]     // 000000005758: D3A0006D 15B7E5C7
	v_fma_mix_f32 v109, v200, v128, v109 op_sel_hi:[0,1,0]     // 000000005760: D3A0006D 15B701C8
	v_fma_mix_f32 v109, v201, v161, v109 op_sel_hi:[0,1,0]     // 000000005768: D3A0006D 15B743C9
	v_fma_mix_f32 v109, v203, v227, v109 op_sel_hi:[0,1,0]     // 000000005770: D3A0006D 15B7C7CB
	v_fma_mix_f32 v150, v202, v122, v109 op_sel_hi:[0,1,0]     // 000000005778: D3A00096 15B6F5CA
	buffer_load_dword v109, off, s[24:27], 0 offset:56         // 000000005780: E0500038 80066D00
	s_waitcnt vmcnt(1)                                         // 000000005788: BF8C0F71
	v_fma_mix_f32 v108, v197, v210, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000578C: D3A0106C 15B3A5C5
	v_fma_mix_f32 v108, v198, v219, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005794: D3A0106C 15B3B7C6
	v_fma_mix_f32 v108, v199, v243, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000579C: D3A0106C 15B3E7C7
	v_fma_mix_f32 v108, v200, v129, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000057A4: D3A0106C 15B303C8
	v_fma_mix_f32 v108, v201, v162, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000057AC: D3A0106C 15B345C9
	v_fma_mix_f32 v108, v203, v228, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000057B4: D3A0106C 15B3C9CB
	v_fma_mix_f32 v155, v202, v123, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000057BC: D3A0109B 15B2F7CA
	buffer_load_dword v108, off, s[24:27], 0 offset:52         // 0000000057C4: E0500034 80066C00
	s_waitcnt vmcnt(1)                                         // 0000000057CC: BF8C0F71
	v_fma_mix_f32 v109, v197, v210, v109 op_sel_hi:[0,1,0]     // 0000000057D0: D3A0006D 15B7A5C5
	v_fma_mix_f32 v109, v198, v219, v109 op_sel_hi:[0,1,0]     // 0000000057D8: D3A0006D 15B7B7C6
	v_fma_mix_f32 v109, v199, v243, v109 op_sel_hi:[0,1,0]     // 0000000057E0: D3A0006D 15B7E7C7
	v_fma_mix_f32 v109, v200, v129, v109 op_sel_hi:[0,1,0]     // 0000000057E8: D3A0006D 15B703C8
	v_fma_mix_f32 v109, v201, v162, v109 op_sel_hi:[0,1,0]     // 0000000057F0: D3A0006D 15B745C9
	v_fma_mix_f32 v109, v203, v228, v109 op_sel_hi:[0,1,0]     // 0000000057F8: D3A0006D 15B7C9CB
	v_fma_mix_f32 v154, v202, v123, v109 op_sel_hi:[0,1,0]     // 000000005800: D3A0009A 15B6F7CA
	buffer_load_dword v109, off, s[24:27], 0 offset:48         // 000000005808: E0500030 80066D00
	s_waitcnt vmcnt(1)                                         // 000000005810: BF8C0F71
	v_fma_mix_f32 v108, v197, v211, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005814: D3A0106C 15B3A7C5
	v_fma_mix_f32 v108, v198, v220, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000581C: D3A0106C 15B3B9C6
	v_fma_mix_f32 v108, v199, v244, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005824: D3A0106C 15B3E9C7
	v_fma_mix_f32 v108, v200, v130, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000582C: D3A0106C 15B305C8
	v_fma_mix_f32 v108, v201, v163, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005834: D3A0106C 15B347C9
	v_fma_mix_f32 v108, v203, v229, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000583C: D3A0106C 15B3CBCB
	v_fma_mix_f32 v157, v202, v124, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005844: D3A0109D 15B2F9CA
	buffer_load_dword v108, off, s[24:27], 0 offset:68         // 00000000584C: E0500044 80066C00
	s_waitcnt vmcnt(1)                                         // 000000005854: BF8C0F71
	v_fma_mix_f32 v109, v197, v211, v109 op_sel_hi:[0,1,0]     // 000000005858: D3A0006D 15B7A7C5
	v_fma_mix_f32 v109, v198, v220, v109 op_sel_hi:[0,1,0]     // 000000005860: D3A0006D 15B7B9C6
	v_fma_mix_f32 v109, v199, v244, v109 op_sel_hi:[0,1,0]     // 000000005868: D3A0006D 15B7E9C7
	v_fma_mix_f32 v109, v200, v130, v109 op_sel_hi:[0,1,0]     // 000000005870: D3A0006D 15B705C8
	v_fma_mix_f32 v109, v201, v163, v109 op_sel_hi:[0,1,0]     // 000000005878: D3A0006D 15B747C9
	v_fma_mix_f32 v109, v203, v229, v109 op_sel_hi:[0,1,0]     // 000000005880: D3A0006D 15B7CBCB
	v_fma_mix_f32 v156, v202, v124, v109 op_sel_hi:[0,1,0]     // 000000005888: D3A0009C 15B6F9CA
	buffer_load_dword v109, off, s[24:27], 0 offset:64         // 000000005890: E0500040 80066D00
	s_waitcnt vmcnt(1)                                         // 000000005898: BF8C0F71
	v_fma_mix_f32 v108, v197, v212, v108 op_sel_hi:[0,1,0]     // 00000000589C: D3A0006C 15B3A9C5
	v_fma_mix_f32 v108, v198, v221, v108 op_sel_hi:[0,1,0]     // 0000000058A4: D3A0006C 15B3BBC6
	v_fma_mix_f32 v108, v199, v245, v108 op_sel_hi:[0,1,0]     // 0000000058AC: D3A0006C 15B3EBC7
	v_fma_mix_f32 v108, v200, v131, v108 op_sel_hi:[0,1,0]     // 0000000058B4: D3A0006C 15B307C8
	v_fma_mix_f32 v108, v201, v164, v108 op_sel_hi:[0,1,0]     // 0000000058BC: D3A0006C 15B349C9
	v_fma_mix_f32 v108, v203, v230, v108 op_sel_hi:[0,1,0]     // 0000000058C4: D3A0006C 15B3CDCB
	v_fma_mix_f32 v128, v202, v125, v108 op_sel_hi:[0,1,0]     // 0000000058CC: D3A00080 15B2FBCA
	buffer_load_dword v108, off, s[24:27], 0 offset:148        // 0000000058D4: E0500094 80066C00
	s_waitcnt vmcnt(1)                                         // 0000000058DC: BF8C0F71
	v_fma_mix_f32 v109, v197, v212, v109 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000058E0: D3A0106D 15B7A9C5
	v_fma_mix_f32 v109, v198, v221, v109 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000058E8: D3A0106D 15B7BBC6
	v_fma_mix_f32 v109, v199, v245, v109 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000058F0: D3A0106D 15B7EBC7
	v_fma_mix_f32 v109, v200, v131, v109 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000058F8: D3A0106D 15B707C8
	v_fma_mix_f32 v109, v201, v164, v109 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005900: D3A0106D 15B749C9
	v_fma_mix_f32 v109, v203, v230, v109 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005908: D3A0106D 15B7CDCB
	v_fma_mix_f32 v129, v202, v125, v109 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005910: D3A01081 15B6FBCA
	ds_read_b128 v[122:125], v196 offset:10192                 // 000000005918: D9FE27D0 7A0000C4
	s_waitcnt vmcnt(0)                                         // 000000005920: BF8C0F70
	v_fma_mix_f32 v112, v197, v68, v108 op_sel_hi:[0,1,0]      // 000000005924: D3A00070 15B289C5
	buffer_load_dword v108, off, s[24:27], 0 offset:140        // 00000000592C: E050008C 80066C00
	s_waitcnt vmcnt(0)                                         // 000000005934: BF8C0F70
	v_fma_mix_f32 v68, v197, v68, v108 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005938: D3A01044 15B289C5
	v_fma_mix_f32 v68, v198, v72, v68 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005940: D3A01044 151291C6
	v_fma_mix_f32 v72, v198, v72, v112 op_sel_hi:[0,1,0]       // 000000005948: D3A00048 15C291C6
	v_fma_mix_f32 v72, v199, v76, v72 op_sel_hi:[0,1,0]        // 000000005950: D3A00048 152299C7
	v_fma_mix_f32 v68, v199, v76, v68 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005958: D3A01044 151299C7
	v_fma_mix_f32 v68, v200, v80, v68 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005960: D3A01044 1512A1C8
	v_fma_mix_f32 v72, v200, v80, v72 op_sel_hi:[0,1,0]        // 000000005968: D3A00048 1522A1C8
	v_fma_mix_f32 v72, v201, v84, v72 op_sel_hi:[0,1,0]        // 000000005970: D3A00048 1522A9C9
	v_fma_mix_f32 v68, v201, v84, v68 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005978: D3A01044 1512A9C9
	v_fma_mix_f32 v68, v203, v88, v68 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005980: D3A01044 1512B1CB
	v_fma_mix_f32 v72, v203, v88, v72 op_sel_hi:[0,1,0]        // 000000005988: D3A00048 1522B1CB
	s_waitcnt lgkmcnt(1)                                       // 000000005990: BF8CC17F
	v_fma_mix_f32 v108, v202, v116, v72 op_sel_hi:[0,1,0]      // 000000005994: D3A0006C 1522E9CA
	v_fma_mix_f32 v109, v202, v116, v68 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 00000000599C: D3A0106D 1512E9CA
	buffer_load_dword v68, off, s[24:27], 0 offset:104         // 0000000059A4: E0500068 80064400
	buffer_load_dword v72, off, s[24:27], 0 offset:100         // 0000000059AC: E0500064 80064800
	s_waitcnt vmcnt(1)                                         // 0000000059B4: BF8C0F71
	v_fma_mix_f32 v68, v197, v69, v68 op_sel_hi:[0,1,0]        // 0000000059B8: D3A00044 15128BC5
	s_waitcnt vmcnt(0)                                         // 0000000059C0: BF8C0F70
	v_fma_mix_f32 v69, v197, v69, v72 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000059C4: D3A01045 15228BC5
	v_fma_mix_f32 v69, v198, v73, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000059CC: D3A01045 151693C6
	v_fma_mix_f32 v68, v198, v73, v68 op_sel_hi:[0,1,0]        // 0000000059D4: D3A00044 151293C6
	v_fma_mix_f32 v68, v199, v77, v68 op_sel_hi:[0,1,0]        // 0000000059DC: D3A00044 15129BC7
	v_fma_mix_f32 v69, v199, v77, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000059E4: D3A01045 15169BC7
	v_fma_mix_f32 v69, v200, v81, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000059EC: D3A01045 1516A3C8
	v_fma_mix_f32 v68, v200, v81, v68 op_sel_hi:[0,1,0]        // 0000000059F4: D3A00044 1512A3C8
	v_fma_mix_f32 v68, v201, v85, v68 op_sel_hi:[0,1,0]        // 0000000059FC: D3A00044 1512ABC9
	v_fma_mix_f32 v69, v201, v85, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A04: D3A01045 1516ABC9
	v_fma_mix_f32 v69, v203, v89, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A0C: D3A01045 1516B3CB
	v_fma_mix_f32 v68, v203, v89, v68 op_sel_hi:[0,1,0]        // 000000005A14: D3A00044 1512B3CB
	v_fma_mix_f32 v116, v202, v117, v68 op_sel_hi:[0,1,0]      // 000000005A1C: D3A00074 1512EBCA
	v_fma_mix_f32 v117, v202, v117, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A24: D3A01075 1516EBCA
	buffer_load_dword v68, off, s[24:27], 0 offset:112         // 000000005A2C: E0500070 80064400
	buffer_load_dword v69, off, s[24:27], 0 offset:108         // 000000005A34: E050006C 80064500
	s_waitcnt vmcnt(1)                                         // 000000005A3C: BF8C0F71
	v_fma_mix_f32 v68, v197, v70, v68 op_sel_hi:[0,1,0]        // 000000005A40: D3A00044 15128DC5
	s_waitcnt vmcnt(0)                                         // 000000005A48: BF8C0F70
	v_fma_mix_f32 v69, v197, v70, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A4C: D3A01045 15168DC5
	v_fma_mix_f32 v69, v198, v74, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A54: D3A01045 151695C6
	v_fma_mix_f32 v68, v198, v74, v68 op_sel_hi:[0,1,0]        // 000000005A5C: D3A00044 151295C6
	v_fma_mix_f32 v68, v199, v78, v68 op_sel_hi:[0,1,0]        // 000000005A64: D3A00044 15129DC7
	v_fma_mix_f32 v69, v199, v78, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A6C: D3A01045 15169DC7
	v_fma_mix_f32 v69, v200, v82, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A74: D3A01045 1516A5C8
	v_fma_mix_f32 v68, v200, v82, v68 op_sel_hi:[0,1,0]        // 000000005A7C: D3A00044 1512A5C8
	v_fma_mix_f32 v68, v201, v86, v68 op_sel_hi:[0,1,0]        // 000000005A84: D3A00044 1512ADC9
	v_fma_mix_f32 v69, v201, v86, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A8C: D3A01045 1516ADC9
	v_fma_mix_f32 v69, v203, v90, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005A94: D3A01045 1516B5CB
	v_fma_mix_f32 v68, v203, v90, v68 op_sel_hi:[0,1,0]        // 000000005A9C: D3A00044 1512B5CB
	v_fma_mix_f32 v134, v202, v118, v68 op_sel_hi:[0,1,0]      // 000000005AA4: D3A00086 1512EDCA
	v_fma_mix_f32 v135, v202, v118, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005AAC: D3A01087 1516EDCA
	buffer_load_dword v68, off, s[24:27], 0 offset:120         // 000000005AB4: E0500078 80064400
	buffer_load_dword v69, off, s[24:27], 0 offset:116         // 000000005ABC: E0500074 80064500
	s_waitcnt vmcnt(1)                                         // 000000005AC4: BF8C0F71
	v_fma_mix_f32 v68, v197, v71, v68 op_sel_hi:[0,1,0]        // 000000005AC8: D3A00044 15128FC5
	s_waitcnt vmcnt(0)                                         // 000000005AD0: BF8C0F70
	v_fma_mix_f32 v69, v197, v71, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005AD4: D3A01045 15168FC5
	v_fma_mix_f32 v69, v198, v75, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005ADC: D3A01045 151697C6
	v_fma_mix_f32 v68, v198, v75, v68 op_sel_hi:[0,1,0]        // 000000005AE4: D3A00044 151297C6
	v_fma_mix_f32 v68, v199, v79, v68 op_sel_hi:[0,1,0]        // 000000005AEC: D3A00044 15129FC7
	v_fma_mix_f32 v69, v199, v79, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005AF4: D3A01045 15169FC7
	v_fma_mix_f32 v69, v200, v83, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005AFC: D3A01045 1516A7C8
	v_fma_mix_f32 v68, v200, v83, v68 op_sel_hi:[0,1,0]        // 000000005B04: D3A00044 1512A7C8
	v_fma_mix_f32 v68, v201, v87, v68 op_sel_hi:[0,1,0]        // 000000005B0C: D3A00044 1512AFC9
	v_fma_mix_f32 v69, v201, v87, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005B14: D3A01045 1516AFC9
	v_fma_mix_f32 v69, v203, v91, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005B1C: D3A01045 1516B7CB
	v_fma_mix_f32 v68, v203, v91, v68 op_sel_hi:[0,1,0]        // 000000005B24: D3A00044 1512B7CB
	v_fma_mix_f32 v132, v202, v119, v68 op_sel_hi:[0,1,0]      // 000000005B2C: D3A00084 1512EFCA
	v_fma_mix_f32 v133, v202, v119, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005B34: D3A01085 1516EFCA
	buffer_load_dword v68, off, s[24:27], 0 offset:128         // 000000005B3C: E0500080 80064400
	buffer_load_dword v69, off, s[24:27], 0 offset:124         // 000000005B44: E050007C 80064500
	s_waitcnt vmcnt(1)                                         // 000000005B4C: BF8C0F71
	v_fma_mix_f32 v68, v197, v40, v68 op_sel_hi:[0,1,0]        // 000000005B50: D3A00044 151251C5
	s_waitcnt vmcnt(0)                                         // 000000005B58: BF8C0F70
	v_fma_mix_f32 v40, v197, v40, v69 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005B5C: D3A01028 151651C5
	v_fma_mix_f32 v40, v198, v48, v40 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005B64: D3A01028 14A261C6
	v_fma_mix_f32 v48, v198, v48, v68 op_sel_hi:[0,1,0]        // 000000005B6C: D3A00030 151261C6
	v_fma_mix_f32 v40, v199, v52, v40 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005B74: D3A01028 14A269C7
	v_fma_mix_f32 v48, v199, v52, v48 op_sel_hi:[0,1,0]        // 000000005B7C: D3A00030 14C269C7
	v_fma_mix_f32 v40, v200, v56, v40 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005B84: D3A01028 14A271C8
	v_fma_mix_f32 v48, v200, v56, v48 op_sel_hi:[0,1,0]        // 000000005B8C: D3A00030 14C271C8
	v_fma_mix_f32 v40, v201, v60, v40 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005B94: D3A01028 14A279C9
	v_fma_mix_f32 v48, v201, v60, v48 op_sel_hi:[0,1,0]        // 000000005B9C: D3A00030 14C279C9
	v_fma_mix_f32 v40, v203, v92, v40 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005BA4: D3A01028 14A2B9CB
	v_fma_mix_f32 v48, v203, v92, v48 op_sel_hi:[0,1,0]        // 000000005BAC: D3A00030 14C2B9CB
	s_waitcnt lgkmcnt(0)                                       // 000000005BB4: BF8CC07F
	v_fma_mix_f32 v139, v202, v122, v40 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005BB8: D3A0108B 14A2F5CA
	buffer_load_dword v40, off, s[24:27], 0 offset:136         // 000000005BC0: E0500088 80062800
	v_fma_mix_f32 v138, v202, v122, v48 op_sel_hi:[0,1,0]      // 000000005BC8: D3A0008A 14C2F5CA
	buffer_load_dword v48, off, s[24:27], 0 offset:132         // 000000005BD0: E0500084 80063000
	s_waitcnt vmcnt(1)                                         // 000000005BD8: BF8C0F71
	v_fma_mix_f32 v40, v197, v41, v40 op_sel_hi:[0,1,0]        // 000000005BDC: D3A00028 14A253C5
	v_fma_mix_f32 v40, v198, v49, v40 op_sel_hi:[0,1,0]        // 000000005BE4: D3A00028 14A263C6
	s_waitcnt vmcnt(0)                                         // 000000005BEC: BF8C0F70
	v_fma_mix_f32 v41, v197, v41, v48 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005BF0: D3A01029 14C253C5
	v_fma_mix_f32 v41, v198, v49, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005BF8: D3A01029 14A663C6
	v_fma_mix_f32 v40, v199, v53, v40 op_sel_hi:[0,1,0]        // 000000005C00: D3A00028 14A26BC7
	v_fma_mix_f32 v41, v199, v53, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005C08: D3A01029 14A66BC7
	v_fma_mix_f32 v40, v200, v57, v40 op_sel_hi:[0,1,0]        // 000000005C10: D3A00028 14A273C8
	v_fma_mix_f32 v41, v200, v57, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005C18: D3A01029 14A673C8
	v_fma_mix_f32 v40, v201, v61, v40 op_sel_hi:[0,1,0]        // 000000005C20: D3A00028 14A27BC9
	v_fma_mix_f32 v41, v201, v61, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005C28: D3A01029 14A67BC9
	v_fma_mix_f32 v40, v203, v93, v40 op_sel_hi:[0,1,0]        // 000000005C30: D3A00028 14A2BBCB
	v_fma_mix_f32 v41, v203, v93, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005C38: D3A01029 14A6BBCB
	v_fma_mix_f32 v136, v202, v123, v40 op_sel_hi:[0,1,0]      // 000000005C40: D3A00088 14A2F7CA
	buffer_load_dword v40, off, s[24:27], 0 offset:152         // 000000005C48: E0500098 80062800
	v_fma_mix_f32 v137, v202, v123, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005C50: D3A01089 14A6F7CA
	buffer_load_dword v41, off, s[24:27], 0 offset:144         // 000000005C58: E0500090 80062900
	s_waitcnt vmcnt(1)                                         // 000000005C60: BF8C0F71
	v_fma_mix_f32 v40, v197, v42, v40 op_sel_hi:[0,1,0]        // 000000005C64: D3A00028 14A255C5
	v_fma_mix_f32 v40, v198, v50, v40 op_sel_hi:[0,1,0]        // 000000005C6C: D3A00028 14A265C6
	s_waitcnt vmcnt(0)                                         // 000000005C74: BF8C0F70
	v_fma_mix_f32 v41, v197, v42, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005C78: D3A01029 14A655C5
	v_fma_mix_f32 v41, v198, v50, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005C80: D3A01029 14A665C6
	v_fma_mix_f32 v40, v199, v54, v40 op_sel_hi:[0,1,0]        // 000000005C88: D3A00028 14A26DC7
	v_fma_mix_f32 v41, v199, v54, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005C90: D3A01029 14A66DC7
	v_fma_mix_f32 v40, v200, v58, v40 op_sel_hi:[0,1,0]        // 000000005C98: D3A00028 14A275C8
	v_fma_mix_f32 v41, v200, v58, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005CA0: D3A01029 14A675C8
	v_fma_mix_f32 v40, v201, v62, v40 op_sel_hi:[0,1,0]        // 000000005CA8: D3A00028 14A27DC9
	v_fma_mix_f32 v41, v201, v62, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005CB0: D3A01029 14A67DC9
	v_fma_mix_f32 v40, v203, v94, v40 op_sel_hi:[0,1,0]        // 000000005CB8: D3A00028 14A2BDCB
	v_fma_mix_f32 v41, v203, v94, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005CC0: D3A01029 14A6BDCB
	v_fma_mix_f32 v164, v202, v124, v40 op_sel_hi:[0,1,0]      // 000000005CC8: D3A000A4 14A2F9CA
	v_fma_mix_f32 v40, v197, v43, v234 op_sel_hi:[0,1,0]       // 000000005CD0: D3A00028 17AA57C5
	v_fma_mix_f32 v165, v202, v124, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005CD8: D3A010A5 14A6F9CA
	v_fma_mix_f32 v41, v197, v43, v238 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005CE0: D3A01029 17BA57C5
	v_fma_mix_f32 v40, v198, v51, v40 op_sel_hi:[0,1,0]        // 000000005CE8: D3A00028 14A267C6
	v_fma_mix_f32 v41, v198, v51, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005CF0: D3A01029 14A667C6
	v_fma_mix_f32 v40, v199, v55, v40 op_sel_hi:[0,1,0]        // 000000005CF8: D3A00028 14A26FC7
	v_fma_mix_f32 v41, v199, v55, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D00: D3A01029 14A66FC7
	v_fma_mix_f32 v40, v200, v59, v40 op_sel_hi:[0,1,0]        // 000000005D08: D3A00028 14A277C8
	v_fma_mix_f32 v41, v200, v59, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D10: D3A01029 14A677C8
	v_fma_mix_f32 v40, v201, v63, v40 op_sel_hi:[0,1,0]        // 000000005D18: D3A00028 14A27FC9
	v_fma_mix_f32 v41, v201, v63, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D20: D3A01029 14A67FC9
	v_fma_mix_f32 v40, v203, v95, v40 op_sel_hi:[0,1,0]        // 000000005D28: D3A00028 14A2BFCB
	v_fma_mix_f32 v41, v203, v95, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D30: D3A01029 14A6BFCB
	v_fma_mix_f32 v118, v202, v125, v40 op_sel_hi:[0,1,0]      // 000000005D38: D3A00076 14A2FBCA
	v_fma_mix_f32 v40, v197, v20, v105 op_sel_hi:[0,1,0]       // 000000005D40: D3A00028 15A629C5
	v_fma_mix_f32 v20, v197, v20, v114 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D48: D3A01014 15CA29C5
	v_fma_mix_f32 v119, v202, v125, v41 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D50: D3A01077 14A6FBCA
	v_fma_mix_f32 v20, v198, v24, v20 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D58: D3A01014 145231C6
	v_fma_mix_f32 v24, v198, v24, v40 op_sel_hi:[0,1,0]        // 000000005D60: D3A00018 14A231C6
	ds_read_b128 v[40:43], v196 offset:10208                   // 000000005D68: D9FE27E0 280000C4
	ds_read_b128 v[48:51], v196 offset:10224                   // 000000005D70: D9FE27F0 300000C4
	v_fma_mix_f32 v20, v199, v28, v20 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D78: D3A01014 145239C7
	v_fma_mix_f32 v20, v200, v32, v20 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D80: D3A01014 145241C8
	v_fma_mix_f32 v20, v201, v36, v20 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D88: D3A01014 145249C9
	v_fma_mix_f32 v20, v203, v64, v20 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D90: D3A01014 145281CB
	s_waitcnt lgkmcnt(1)                                       // 000000005D98: BF8CC17F
	v_fma_mix_f32 v63, v202, v40, v20 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005D9C: D3A0103F 145251CA
	v_fma_mix_f32 v20, v197, v21, v239 op_sel_hi:[0,1,0]       // 000000005DA4: D3A00014 17BE2BC5
	v_fma_mix_f32 v20, v198, v25, v20 op_sel_hi:[0,1,0]        // 000000005DAC: D3A00014 145233C6
	v_fma_mix_f32 v20, v199, v29, v20 op_sel_hi:[0,1,0]        // 000000005DB4: D3A00014 14523BC7
	v_fma_mix_f32 v20, v200, v33, v20 op_sel_hi:[0,1,0]        // 000000005DBC: D3A00014 145243C8
	v_fma_mix_f32 v20, v201, v37, v20 op_sel_hi:[0,1,0]        // 000000005DC4: D3A00014 14524BC9
	v_fma_mix_f32 v20, v203, v65, v20 op_sel_hi:[0,1,0]        // 000000005DCC: D3A00014 145283CB
	v_fma_mix_f32 v130, v202, v41, v20 op_sel_hi:[0,1,0]       // 000000005DD4: D3A00082 145253CA
	v_fma_mix_f32 v20, v197, v22, v216 op_sel_hi:[0,1,0]       // 000000005DDC: D3A00014 17622DC5
	v_fma_mix_f32 v20, v198, v26, v20 op_sel_hi:[0,1,0]        // 000000005DE4: D3A00014 145235C6
	v_fma_mix_f32 v20, v199, v30, v20 op_sel_hi:[0,1,0]        // 000000005DEC: D3A00014 14523DC7
	v_fma_mix_f32 v20, v200, v34, v20 op_sel_hi:[0,1,0]        // 000000005DF4: D3A00014 145245C8
	v_fma_mix_f32 v20, v201, v38, v20 op_sel_hi:[0,1,0]        // 000000005DFC: D3A00014 14524DC9
	v_fma_mix_f32 v20, v203, v66, v20 op_sel_hi:[0,1,0]        // 000000005E04: D3A00014 145285CB
	v_fma_mix_f32 v122, v202, v42, v20 op_sel_hi:[0,1,0]       // 000000005E0C: D3A0007A 145255CA
	v_fma_mix_f32 v20, v197, v23, v217 op_sel_hi:[0,1,0]       // 000000005E14: D3A00014 17662FC5
	v_fma_mix_f32 v20, v198, v27, v20 op_sel_hi:[0,1,0]        // 000000005E1C: D3A00014 145237C6
	v_fma_mix_f32 v20, v199, v31, v20 op_sel_hi:[0,1,0]        // 000000005E24: D3A00014 14523FC7
	v_fma_mix_f32 v20, v200, v35, v20 op_sel_hi:[0,1,0]        // 000000005E2C: D3A00014 145247C8
	v_fma_mix_f32 v20, v201, v39, v20 op_sel_hi:[0,1,0]        // 000000005E34: D3A00014 14524FC9
	v_fma_mix_f32 v20, v203, v67, v20 op_sel_hi:[0,1,0]        // 000000005E3C: D3A00014 145287CB
	v_fma_mix_f32 v124, v202, v43, v20 op_sel_hi:[0,1,0]       // 000000005E44: D3A0007C 145257CA
	v_fma_mix_f32 v20, v197, v0, v214 op_sel_hi:[0,1,0]        // 000000005E4C: D3A00014 175A01C5
	v_fma_mix_f32 v0, v197, v0, v213 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005E54: D3A01000 175601C5
	v_fma_mix_f32 v0, v198, v4, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005E5C: D3A01000 140209C6
	v_fma_mix_f32 v0, v199, v8, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005E64: D3A01000 140211C7
	v_fma_mix_f32 v0, v200, v12, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005E6C: D3A01000 140219C8
	v_fma_mix_f32 v0, v201, v16, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005E74: D3A01000 140221C9
	v_fma_mix_f32 v0, v203, v44, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005E7C: D3A01000 140259CB
	v_fma_mix_f32 v21, v197, v21, v235 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005E84: D3A01015 17AE2BC5
	s_waitcnt lgkmcnt(0)                                       // 000000005E8C: BF8CC07F
	v_fma_mix_f32 v161, v202, v48, v0 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005E90: D3A010A1 140261CA
	v_fma_mix_f32 v0, v197, v1, v115 op_sel_hi:[0,1,0]         // 000000005E98: D3A00000 15CE03C5
	v_fma_mix_f32 v1, v197, v1, v207 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005EA0: D3A01001 173E03C5
	v_fma_mix_f32 v21, v198, v25, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005EA8: D3A01015 145633C6
	v_fma_mix_f32 v1, v198, v5, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005EB0: D3A01001 14060BC6
	v_fma_mix_f32 v0, v198, v5, v0 op_sel_hi:[0,1,0]           // 000000005EB8: D3A00000 14020BC6
	v_fma_mix_f32 v21, v199, v29, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005EC0: D3A01015 14563BC7
	v_fma_mix_f32 v0, v199, v9, v0 op_sel_hi:[0,1,0]           // 000000005EC8: D3A00000 140213C7
	v_fma_mix_f32 v1, v199, v9, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005ED0: D3A01001 140613C7
	v_fma_mix_f32 v21, v200, v33, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005ED8: D3A01015 145643C8
	v_fma_mix_f32 v1, v200, v13, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005EE0: D3A01001 14061BC8
	v_fma_mix_f32 v0, v200, v13, v0 op_sel_hi:[0,1,0]          // 000000005EE8: D3A00000 14021BC8
	v_fma_mix_f32 v21, v201, v37, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005EF0: D3A01015 14564BC9
	v_fma_mix_f32 v0, v201, v17, v0 op_sel_hi:[0,1,0]          // 000000005EF8: D3A00000 140223C9
	v_fma_mix_f32 v1, v201, v17, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F00: D3A01001 140623C9
	v_fma_mix_f32 v21, v203, v65, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F08: D3A01015 145683CB
	v_fma_mix_f32 v1, v203, v45, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F10: D3A01001 14065BCB
	v_fma_mix_f32 v0, v203, v45, v0 op_sel_hi:[0,1,0]          // 000000005F18: D3A00000 14025BCB
	v_fma_mix_f32 v131, v202, v41, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F20: D3A01083 145653CA
	v_fma_mix_f32 v21, v197, v22, v231 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F28: D3A01015 179E2DC5
	v_fma_mix_f32 v162, v202, v49, v0 op_sel_hi:[0,1,0]        // 000000005F30: D3A000A2 140263CA
	v_fma_mix_f32 v163, v202, v49, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F38: D3A010A3 140663CA
	v_fma_mix_f32 v0, v197, v2, v113 op_sel_hi:[0,1,0]         // 000000005F40: D3A00000 15C605C5
	v_fma_mix_f32 v1, v197, v2, v208 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F48: D3A01001 174205C5
	v_fma_mix_f32 v21, v198, v26, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F50: D3A01015 145635C6
	v_fma_mix_f32 v1, v198, v6, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F58: D3A01001 14060DC6
	v_fma_mix_f32 v0, v198, v6, v0 op_sel_hi:[0,1,0]           // 000000005F60: D3A00000 14020DC6
	v_fma_mix_f32 v21, v199, v30, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F68: D3A01015 14563DC7
	v_fma_mix_f32 v0, v199, v10, v0 op_sel_hi:[0,1,0]          // 000000005F70: D3A00000 140215C7
	v_fma_mix_f32 v1, v199, v10, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F78: D3A01001 140615C7
	v_fma_mix_f32 v21, v200, v34, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F80: D3A01015 145645C8
	v_fma_mix_f32 v1, v200, v14, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F88: D3A01001 14061DC8
	v_fma_mix_f32 v0, v200, v14, v0 op_sel_hi:[0,1,0]          // 000000005F90: D3A00000 14021DC8
	v_fma_mix_f32 v21, v201, v38, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005F98: D3A01015 14564DC9
	v_fma_mix_f32 v0, v201, v18, v0 op_sel_hi:[0,1,0]          // 000000005FA0: D3A00000 140225C9
	v_fma_mix_f32 v1, v201, v18, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005FA8: D3A01001 140625C9
	v_fma_mix_f32 v21, v203, v66, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005FB0: D3A01015 145685CB
	v_fma_mix_f32 v1, v203, v46, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005FB8: D3A01001 14065DCB
	v_fma_mix_f32 v0, v203, v46, v0 op_sel_hi:[0,1,0]          // 000000005FC0: D3A00000 14025DCB
	v_fma_mix_f32 v123, v202, v42, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005FC8: D3A0107B 145655CA
	v_fma_mix_f32 v21, v197, v23, v215 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005FD0: D3A01015 175E2FC5
	v_fma_mix_f32 v25, v202, v50, v0 op_sel_hi:[0,1,0]         // 000000005FD8: D3A00019 140265CA
	v_fma_mix_f32 v26, v202, v50, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005FE0: D3A0101A 140665CA
	v_fma_mix_f32 v0, v197, v3, v104 op_sel_hi:[0,1,0]         // 000000005FE8: D3A00000 15A207C5
	v_fma_mix_f32 v1, v197, v3, v146 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005FF0: D3A01001 164A07C5
	v_fma_mix_f32 v21, v198, v27, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000005FF8: D3A01015 145637C6
	v_fma_mix_f32 v4, v198, v4, v20 op_sel_hi:[0,1,0]          // 000000006000: D3A00004 145209C6
	v_fma_mix_f32 v1, v198, v7, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000006008: D3A01001 14060FC6
	v_fma_mix_f32 v0, v198, v7, v0 op_sel_hi:[0,1,0]           // 000000006010: D3A00000 14020FC6
	v_fma_mix_f32 v24, v199, v28, v24 op_sel_hi:[0,1,0]        // 000000006018: D3A00018 146239C7
	v_fma_mix_f32 v21, v199, v31, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000006020: D3A01015 14563FC7
	v_fma_mix_f32 v4, v199, v8, v4 op_sel_hi:[0,1,0]           // 000000006028: D3A00004 141211C7
	v_fma_mix_f32 v0, v199, v11, v0 op_sel_hi:[0,1,0]          // 000000006030: D3A00000 140217C7
	v_fma_mix_f32 v1, v199, v11, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000006038: D3A01001 140617C7
	v_fma_mix_f32 v24, v200, v32, v24 op_sel_hi:[0,1,0]        // 000000006040: D3A00018 146241C8
	v_fma_mix_f32 v21, v200, v35, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000006048: D3A01015 145647C8
	v_fma_mix_f32 v4, v200, v12, v4 op_sel_hi:[0,1,0]          // 000000006050: D3A00004 141219C8
	v_fma_mix_f32 v1, v200, v15, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000006058: D3A01001 14061FC8
	v_fma_mix_f32 v0, v200, v15, v0 op_sel_hi:[0,1,0]          // 000000006060: D3A00000 14021FC8
	v_fma_mix_f32 v24, v201, v36, v24 op_sel_hi:[0,1,0]        // 000000006068: D3A00018 146249C9
	v_fma_mix_f32 v21, v201, v39, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000006070: D3A01015 14564FC9
	v_fma_mix_f32 v4, v201, v16, v4 op_sel_hi:[0,1,0]          // 000000006078: D3A00004 141221C9
	v_fma_mix_f32 v0, v201, v19, v0 op_sel_hi:[0,1,0]          // 000000006080: D3A00000 140227C9
	v_fma_mix_f32 v1, v201, v19, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000006088: D3A01001 140627C9
	v_fma_mix_f32 v24, v203, v64, v24 op_sel_hi:[0,1,0]        // 000000006090: D3A00018 146281CB
	v_fma_mix_f32 v21, v203, v67, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 000000006098: D3A01015 145687CB
	v_fma_mix_f32 v4, v203, v44, v4 op_sel_hi:[0,1,0]          // 0000000060A0: D3A00004 141259CB
	v_fma_mix_f32 v1, v203, v47, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000060A8: D3A01001 14065FCB
	v_fma_mix_f32 v0, v203, v47, v0 op_sel_hi:[0,1,0]          // 0000000060B0: D3A00000 14025FCB
	v_fma_mix_f32 v62, v202, v40, v24 op_sel_hi:[0,1,0]        // 0000000060B8: D3A0003E 146251CA
	v_fma_mix_f32 v125, v202, v43, v21 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000060C0: D3A0107D 145657CA
	v_fma_mix_f32 v160, v202, v48, v4 op_sel_hi:[0,1,0]        // 0000000060C8: D3A000A0 141261CA
	v_fma_mix_f32 v23, v202, v51, v0 op_sel_hi:[0,1,0]         // 0000000060D0: D3A00017 140267CA
	v_fma_mix_f32 v24, v202, v51, v1 op_sel:[0,1,0] op_sel_hi:[0,1,0]// 0000000060D8: D3A01018 140667CA
	v_add_f32_e32 v4, v204, v202                               // 0000000060E0: 020995CC
	v_mov_b32_e32 v6, v195                                     // 0000000060E4: 7E0C03C3
	s_or_b64 exec, exec, s[4:5]                                // 0000000060E8: 87FE047E
	s_add_i32 s4, s11, 16                                      // 0000000060EC: 8104900B
	s_cmp_gt_u32 s11, 47                                       // 0000000060F0: BF08AF0B
	s_cbranch_scc1 61144                                       // 0000000060F4: BF85EED8 <fa_avanti+0x558>
	s_mov_b32 s11, s4                                          // 0000000060F8: BE8B0004
	s_branch 61224                                             // 0000000060FC: BF82EF28 <fa_avanti+0x6a0>
	buffer_load_dword v6, off, s[24:27], 0 offset:204          // 000000006100: E05000CC 80060600
	buffer_load_dword v7, off, s[24:27], 0 offset:208          // 000000006108: E05000D0 80060700
	s_and_saveexec_b64 s[4:5], s[0:1]                          // 000000006110: BE842000
	s_cbranch_execz 174                                        // 000000006114: BF8800AE <fa_avanti+0x4cd0>
	v_div_scale_f32 v0, s[0:1], v4, v4, 1.0                    // 000000006118: D1E00000 03CA0904
	v_div_scale_f32 v1, vcc, 1.0, v4, 1.0                      // 000000006120: D1E06A01 03CA08F2
	v_rcp_f32_e32 v2, v0                                       // 000000006128: 7E044500
	v_fma_f32 v3, -v0, v2, 1.0                                 // 00000000612C: D1CB0003 23CA0500
	v_fmac_f32_e32 v2, v3, v2                                  // 000000006134: 76040503
	v_mul_f32_e32 v3, v1, v2                                   // 000000006138: 0A060501
	v_fma_f32 v5, -v0, v3, v1                                  // 00000000613C: D1CB0005 24060700
	v_fmac_f32_e32 v3, v5, v2                                  // 000000006144: 76060505
	v_fma_f32 v0, -v0, v3, v1                                  // 000000006148: D1CB0000 24060700
	v_div_fmas_f32 v0, v0, v2, v3                              // 000000006150: D1E20000 040E0500
	s_waitcnt lgkmcnt(0)                                       // 000000006158: BF8CC07F
	v_mov_b32_e32 v1, s3                                       // 00000000615C: 7E020203
	s_waitcnt vmcnt(1)                                         // 000000006160: BF8C0F71
	v_add_co_u32_e32 v12, vcc, s2, v6                          // 000000006164: 32180C02
	s_waitcnt vmcnt(0)                                         // 000000006168: BF8C0F70
	v_addc_co_u32_e32 v13, vcc, v1, v7, vcc                    // 00000000616C: 381A0F01
	v_cmp_lt_f32_e32 vcc, 0, v4                                // 000000006170: 7C820880
	v_div_fixup_f32 v0, v0, v4, 1.0                            // 000000006174: D1DE0000 03CA0900
	v_cndmask_b32_e32 v14, 0, v0, vcc                          // 00000000617C: 001C0080
	v_fma_mixlo_f16 v0, v14, v236, 0                           // 000000006180: D3A10000 0203D90E
	v_fma_mixlo_f16 v1, v14, v248, 0                           // 000000006188: D3A10001 0203F10E
	v_fma_mixlo_f16 v2, v14, v246, 0                           // 000000006190: D3A10002 0203ED0E
	v_fma_mixlo_f16 v3, v14, v254, 0                           // 000000006198: D3A10003 0203FD0E
	v_fma_mixlo_f16 v4, v14, v96, 0                            // 0000000061A0: D3A10004 0202C10E
	v_fma_mixlo_f16 v5, v14, v98, 0                            // 0000000061A8: D3A10005 0202C50E
	v_fma_mixlo_f16 v6, v14, v100, 0                           // 0000000061B0: D3A10006 0202C90E
	v_fma_mixlo_f16 v7, v14, v102, 0                           // 0000000061B8: D3A10007 0202CD0E
	v_fma_mixlo_f16 v8, v14, v144, 0                           // 0000000061C0: D3A10008 0203210E
	v_fma_mixlo_f16 v9, v14, v106, 0                           // 0000000061C8: D3A10009 0202D50E
	v_fma_mixlo_f16 v10, v14, v148, 0                          // 0000000061D0: D3A1000A 0203290E
	v_fma_mixlo_f16 v11, v14, v152, 0                          // 0000000061D8: D3A1000B 0203310E
	v_fma_mixhi_f16 v3, v14, v255, 0                           // 0000000061E0: D3A20003 0203FF0E
	v_fma_mixhi_f16 v2, v14, v247, 0                           // 0000000061E8: D3A20002 0203EF0E
	v_fma_mixhi_f16 v1, v14, v249, 0                           // 0000000061F0: D3A20001 0203F30E
	v_fma_mixhi_f16 v0, v14, v237, 0                           // 0000000061F8: D3A20000 0203DB0E
	v_fma_mixhi_f16 v7, v14, v103, 0                           // 000000006200: D3A20007 0202CF0E
	v_fma_mixhi_f16 v6, v14, v101, 0                           // 000000006208: D3A20006 0202CB0E
	v_fma_mixhi_f16 v5, v14, v99, 0                            // 000000006210: D3A20005 0202C70E
	v_fma_mixhi_f16 v4, v14, v97, 0                            // 000000006218: D3A20004 0202C30E
	v_fma_mixhi_f16 v11, v14, v153, 0                          // 000000006220: D3A2000B 0203330E
	v_fma_mixhi_f16 v10, v14, v149, 0                          // 000000006228: D3A2000A 02032B0E
	v_fma_mixhi_f16 v9, v14, v107, 0                           // 000000006230: D3A20009 0202D70E
	v_fma_mixhi_f16 v8, v14, v145, 0                           // 000000006238: D3A20008 0203230E
	global_store_dwordx4 v[12:13], v[0:3], off                 // 000000006240: DC7C8000 007F000C
	global_store_dwordx4 v[12:13], v[4:7], off offset:16       // 000000006248: DC7C8010 007F040C
	global_store_dwordx4 v[12:13], v[8:11], off offset:32      // 000000006250: DC7C8020 007F080C
	v_fma_mixlo_f16 v0, v14, v150, 0                           // 000000006258: D3A10000 02032D0E
	v_fma_mixlo_f16 v1, v14, v154, 0                           // 000000006260: D3A10001 0203350E
	v_fma_mixlo_f16 v2, v14, v156, 0                           // 000000006268: D3A10002 0203390E
	v_fma_mixlo_f16 v3, v14, v128, 0                           // 000000006270: D3A10003 0203010E
	v_fma_mixhi_f16 v3, v14, v129, 0                           // 000000006278: D3A20003 0203030E
	v_fma_mixhi_f16 v2, v14, v157, 0                           // 000000006280: D3A20002 02033B0E
	v_fma_mixhi_f16 v1, v14, v155, 0                           // 000000006288: D3A20001 0203370E
	v_fma_mixhi_f16 v0, v14, v151, 0                           // 000000006290: D3A20000 02032F0E
	global_store_dwordx4 v[12:13], v[0:3], off offset:48       // 000000006298: DC7C8030 007F000C
	s_nop 0                                                    // 0000000062A0: BF800000
	v_fma_mixlo_f16 v0, v14, v108, 0                           // 0000000062A4: D3A10000 0202D90E
	v_fma_mixlo_f16 v1, v14, v116, 0                           // 0000000062AC: D3A10001 0202E90E
	v_fma_mixlo_f16 v2, v14, v134, 0                           // 0000000062B4: D3A10002 02030D0E
	v_fma_mixlo_f16 v3, v14, v132, 0                           // 0000000062BC: D3A10003 0203090E
	v_fma_mixhi_f16 v3, v14, v133, 0                           // 0000000062C4: D3A20003 02030B0E
	v_fma_mixhi_f16 v2, v14, v135, 0                           // 0000000062CC: D3A20002 02030F0E
	v_fma_mixhi_f16 v1, v14, v117, 0                           // 0000000062D4: D3A20001 0202EB0E
	v_fma_mixhi_f16 v0, v14, v109, 0                           // 0000000062DC: D3A20000 0202DB0E
	global_store_dwordx4 v[12:13], v[0:3], off offset:64       // 0000000062E4: DC7C8040 007F000C
	s_nop 0                                                    // 0000000062EC: BF800000
	v_fma_mixlo_f16 v0, v14, v138, 0                           // 0000000062F0: D3A10000 0203150E
	v_fma_mixlo_f16 v1, v14, v136, 0                           // 0000000062F8: D3A10001 0203110E
	v_fma_mixlo_f16 v2, v14, v164, 0                           // 000000006300: D3A10002 0203490E
	v_fma_mixlo_f16 v3, v14, v118, 0                           // 000000006308: D3A10003 0202ED0E
	v_fma_mixhi_f16 v3, v14, v119, 0                           // 000000006310: D3A20003 0202EF0E
	v_fma_mixhi_f16 v2, v14, v165, 0                           // 000000006318: D3A20002 02034B0E
	v_fma_mixhi_f16 v1, v14, v137, 0                           // 000000006320: D3A20001 0203130E
	v_fma_mixhi_f16 v0, v14, v139, 0                           // 000000006328: D3A20000 0203170E
	global_store_dwordx4 v[12:13], v[0:3], off offset:80       // 000000006330: DC7C8050 007F000C
	s_nop 0                                                    // 000000006338: BF800000
	v_fma_mixlo_f16 v0, v14, v62, 0                            // 00000000633C: D3A10000 02027D0E
	v_fma_mixlo_f16 v1, v14, v130, 0                           // 000000006344: D3A10001 0203050E
	v_fma_mixlo_f16 v2, v14, v122, 0                           // 00000000634C: D3A10002 0202F50E
	v_fma_mixlo_f16 v3, v14, v124, 0                           // 000000006354: D3A10003 0202F90E
	v_fma_mixhi_f16 v3, v14, v125, 0                           // 00000000635C: D3A20003 0202FB0E
	v_fma_mixhi_f16 v2, v14, v123, 0                           // 000000006364: D3A20002 0202F70E
	v_fma_mixhi_f16 v1, v14, v131, 0                           // 00000000636C: D3A20001 0203070E
	v_fma_mixhi_f16 v0, v14, v63, 0                            // 000000006374: D3A20000 02027F0E
	global_store_dwordx4 v[12:13], v[0:3], off offset:96       // 00000000637C: DC7C8060 007F000C
	s_nop 0                                                    // 000000006384: BF800000
	v_fma_mixlo_f16 v0, v14, v160, 0                           // 000000006388: D3A10000 0203410E
	v_fma_mixlo_f16 v1, v14, v162, 0                           // 000000006390: D3A10001 0203450E
	v_fma_mixlo_f16 v2, v14, v25, 0                            // 000000006398: D3A10002 0202330E
	v_fma_mixlo_f16 v3, v14, v23, 0                            // 0000000063A0: D3A10003 02022F0E
	v_fma_mixhi_f16 v3, v14, v24, 0                            // 0000000063A8: D3A20003 0202310E
	v_fma_mixhi_f16 v2, v14, v26, 0                            // 0000000063B0: D3A20002 0202350E
	v_fma_mixhi_f16 v1, v14, v163, 0                           // 0000000063B8: D3A20001 0203470E
	v_fma_mixhi_f16 v0, v14, v161, 0                           // 0000000063C0: D3A20000 0203430E
	global_store_dwordx4 v[12:13], v[0:3], off offset:112      // 0000000063C8: DC7C8070 007F000C
	s_endpgm                                                   // 0000000063D0: BF810000
	v_mov_b32_e32 v23, 0                                       // 0000000063D4: 7E2E0280
	v_mov_b32_e32 v24, v23                                     // 0000000063D8: 7E300317
	v_mov_b32_e32 v26, v24                                     // 0000000063DC: 7E340318
	v_mov_b32_e32 v163, v24                                    // 0000000063E0: 7F460318
	v_mov_b32_e32 v161, v24                                    // 0000000063E4: 7F420318
	v_mov_b32_e32 v125, v24                                    // 0000000063E8: 7EFA0318
	v_mov_b32_e32 v123, v24                                    // 0000000063EC: 7EF60318
	v_mov_b32_e32 v131, v24                                    // 0000000063F0: 7F060318
	v_mov_b32_e32 v63, v24                                     // 0000000063F4: 7E7E0318
	v_mov_b32_e32 v119, v24                                    // 0000000063F8: 7EEE0318
	v_mov_b32_e32 v165, v24                                    // 0000000063FC: 7F4A0318
	v_mov_b32_e32 v137, v24                                    // 000000006400: 7F120318
	v_mov_b32_e32 v139, v24                                    // 000000006404: 7F160318
	v_mov_b32_e32 v133, v24                                    // 000000006408: 7F0A0318
	v_mov_b32_e32 v135, v24                                    // 00000000640C: 7F0E0318
	v_mov_b32_e32 v117, v24                                    // 000000006410: 7EEA0318
	v_mov_b32_e32 v109, v24                                    // 000000006414: 7EDA0318
	v_mov_b32_e32 v129, v24                                    // 000000006418: 7F020318
	v_mov_b32_e32 v157, v24                                    // 00000000641C: 7F3A0318
	v_mov_b32_e32 v155, v24                                    // 000000006420: 7F360318
	v_mov_b32_e32 v151, v24                                    // 000000006424: 7F2E0318
	v_mov_b32_e32 v153, v24                                    // 000000006428: 7F320318
	v_mov_b32_e32 v149, v24                                    // 00000000642C: 7F2A0318
	v_mov_b32_e32 v107, v24                                    // 000000006430: 7ED60318
	v_mov_b32_e32 v145, v24                                    // 000000006434: 7F220318
	v_mov_b32_e32 v103, v24                                    // 000000006438: 7ECE0318
	v_mov_b32_e32 v101, v24                                    // 00000000643C: 7ECA0318
	v_mov_b32_e32 v99, v24                                     // 000000006440: 7EC60318
	v_mov_b32_e32 v97, v24                                     // 000000006444: 7EC20318
	v_mov_b32_e32 v255, v24                                    // 000000006448: 7FFE0318
	v_mov_b32_e32 v247, v24                                    // 00000000644C: 7FEE0318
	v_mov_b32_e32 v249, v24                                    // 000000006450: 7FF20318
	v_mov_b32_e32 v237, v24                                    // 000000006454: 7FDA0318
	v_mov_b32_e32 v25, v23                                     // 000000006458: 7E320317
	v_mov_b32_e32 v162, v23                                    // 00000000645C: 7F440317
	v_mov_b32_e32 v160, v23                                    // 000000006460: 7F400317
	v_mov_b32_e32 v124, v23                                    // 000000006464: 7EF80317
	v_mov_b32_e32 v122, v23                                    // 000000006468: 7EF40317
	v_mov_b32_e32 v130, v23                                    // 00000000646C: 7F040317
	v_mov_b32_e32 v62, v23                                     // 000000006470: 7E7C0317
	v_mov_b32_e32 v118, v23                                    // 000000006474: 7EEC0317
	v_mov_b32_e32 v164, v23                                    // 000000006478: 7F480317
	v_mov_b32_e32 v136, v23                                    // 00000000647C: 7F100317
	v_mov_b32_e32 v138, v23                                    // 000000006480: 7F140317
	v_mov_b32_e32 v132, v23                                    // 000000006484: 7F080317
	v_mov_b32_e32 v134, v23                                    // 000000006488: 7F0C0317
	v_mov_b32_e32 v116, v23                                    // 00000000648C: 7EE80317
	v_mov_b32_e32 v108, v23                                    // 000000006490: 7ED80317
	v_mov_b32_e32 v128, v23                                    // 000000006494: 7F000317
	v_mov_b32_e32 v156, v23                                    // 000000006498: 7F380317
	v_mov_b32_e32 v154, v23                                    // 00000000649C: 7F340317
	v_mov_b32_e32 v150, v23                                    // 0000000064A0: 7F2C0317
	v_mov_b32_e32 v152, v23                                    // 0000000064A4: 7F300317
	v_mov_b32_e32 v148, v23                                    // 0000000064A8: 7F280317
	v_mov_b32_e32 v106, v23                                    // 0000000064AC: 7ED40317
	v_mov_b32_e32 v144, v23                                    // 0000000064B0: 7F200317
	v_mov_b32_e32 v102, v23                                    // 0000000064B4: 7ECC0317
	v_mov_b32_e32 v100, v23                                    // 0000000064B8: 7EC80317
	v_mov_b32_e32 v98, v23                                     // 0000000064BC: 7EC40317
	v_mov_b32_e32 v96, v23                                     // 0000000064C0: 7EC00317
	v_mov_b32_e32 v254, v23                                    // 0000000064C4: 7FFC0317
	v_mov_b32_e32 v246, v23                                    // 0000000064C8: 7FEC0317
	v_mov_b32_e32 v248, v23                                    // 0000000064CC: 7FF00317
	v_mov_b32_e32 v236, v23                                    // 0000000064D0: 7FD80317
	v_mov_b32_e32 v4, v23                                      // 0000000064D4: 7E080317
	s_and_saveexec_b64 s[4:5], s[0:1]                          // 0000000064D8: BE842000
	s_cbranch_execnz 65294                                     // 0000000064DC: BF89FF0E <fa_avanti+0x4a18>
	s_branch 65467                                             // 0000000064E0: BF82FFBB <fa_avanti+0x4cd0>

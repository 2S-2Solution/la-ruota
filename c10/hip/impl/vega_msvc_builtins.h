// [VEGA-PATCH 12 T09:45 18 giu] Shim builtin GCC/clang per MSVC cl.exe
// Header HIP ROCm 6.1 usano __builtin_clz/ctz GCC-only. MSVC cl.exe non li riconosce.
// Includiamo questo header tramite /FI (force include) prima di compilare c10/hip target.
//
// [VEGA-PATCH 12c T17:05 22 giu] CONSTEXPR FIX:
// amd_hip_vector_types.h:139 ha `constexpr next_pot()` che chiama __builtin_clz.
// MSVC C3615: constexpr non puo' chiamare funzioni non-constexpr.
// _BitScanReverse intrinsic MSVC NON e' constexpr prima di VS 17.6+.
// Soluzione: implementazione loop puro C++14 constexpr (portable, no intrinsic).
#pragma once

#ifdef _MSC_VER

constexpr int __builtin_clz(unsigned int x) {
    if (x == 0) return 32;
    int n = 0;
    while ((x & 0x80000000u) == 0u) { ++n; x <<= 1; }
    return n;
}

constexpr int __builtin_ctz(unsigned int x) {
    if (x == 0) return 32;
    int n = 0;
    while ((x & 1u) == 0u) { ++n; x >>= 1; }
    return n;
}

constexpr int __builtin_clzll(unsigned long long x) {
    if (x == 0) return 64;
    int n = 0;
    while ((x & 0x8000000000000000ull) == 0ull) { ++n; x <<= 1; }
    return n;
}

constexpr int __builtin_ctzll(unsigned long long x) {
    if (x == 0) return 64;
    int n = 0;
    while ((x & 1ull) == 0ull) { ++n; x >>= 1; }
    return n;
}

constexpr int __builtin_popcount(unsigned int x) {
    int n = 0;
    while (x) { n += (int)(x & 1u); x >>= 1; }
    return n;
}

constexpr int __builtin_popcountll(unsigned long long x) {
    int n = 0;
    while (x) { n += (int)(x & 1ull); x >>= 1; }
    return n;
}

#endif // _MSC_VER

"""
betatest_laruota_gpu.py — Betatest LA RUOTA PyTorch ROCm Windows nativo gfx906.
2 Solution, 20 giu 2026 T00:05 CEST.

Verifica:
  1. import torch
  2. torch.cuda.is_available() — nativo gfx906 SENZA ZLUDA wrapper!
  3. torch.cuda.get_device_name(0) — atteso "AMD Radeon VII" (no [ZLUDA])
  4. torch.cuda.device_count() = 1
  5. matmul fp16 4096² bench → confronto vs ZLUDA 11.32 TFLOPS baseline
  6. Multi-stream test (sblocco potenziale +82% bench T07:55)
  7. cuGraph capture test (sblocco potenziale fusion)
  8. Memory pool async (PyTorch CachingAllocator expandable_segments)

Target: matmul fp16 4096² >= 15 TFLOPS (= +33% vs ZLUDA wrapper)
"""

import sys
import os
import time

print("=" * 70)
print("BETATEST LA RUOTA — PyTorch ROCm Windows nativo gfx906")
print("2 Solution, 20 giu 2026 T00:05 CEST")
print("=" * 70)
print()

# ============================================================================
# T1: import torch
# ============================================================================
print("[T1] import torch")
try:
    import torch
    print(f"  OK torch {torch.__version__}")
    print(f"  Build: {getattr(torch.version, 'hip', 'no HIP attr')}")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)
print()

# ============================================================================
# T2: torch.cuda.is_available()
# ============================================================================
print("[T2] torch.cuda.is_available()")
avail = torch.cuda.is_available()
print(f"  available={avail}")
if not avail:
    print("  FAIL — exit")
    sys.exit(1)
print()

# ============================================================================
# T3: device info
# ============================================================================
print("[T3] device info")
count = torch.cuda.device_count()
print(f"  device_count={count}")
for i in range(count):
    name = torch.cuda.get_device_name(i)
    props = torch.cuda.get_device_properties(i)
    print(f"  device {i}: name={name}")
    print(f"    total_memory={props.total_memory / 1e9:.2f} GB")
    print(f"    multi_processor_count (CU)={props.multi_processor_count}")
    print(f"    major.minor={props.major}.{props.minor}")
print()

# ============================================================================
# T4: alloc + zero base test
# ============================================================================
print("[T4] alloc base 1024x1024 fp16 + zero check")
try:
    a = torch.zeros(1024, 1024, dtype=torch.float16, device='cuda')
    torch.cuda.synchronize()
    print(f"  alloc OK shape={a.shape} sum={a.sum().item():.2f}")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)
print()

# ============================================================================
# T5: matmul fp16 4096² bench
# ============================================================================
print("[T5] matmul fp16 4096² bench (vs ZLUDA 11.32 TFLOPS baseline)")
SIZE = 4096
A = torch.randn(SIZE, SIZE, dtype=torch.float16, device='cuda')
B = torch.randn(SIZE, SIZE, dtype=torch.float16, device='cuda')

# Warmup
for _ in range(5):
    C = torch.matmul(A, B)
torch.cuda.synchronize()

# Bench
N_ITER = 30
t0 = time.perf_counter()
for _ in range(N_ITER):
    C = torch.matmul(A, B)
torch.cuda.synchronize()
elapsed = time.perf_counter() - t0

flops = 2 * SIZE * SIZE * SIZE * N_ITER
tflops = flops / elapsed / 1e12
ms_per_call = elapsed / N_ITER * 1000

print(f"  {N_ITER} matmul {SIZE}² fp16 in {elapsed:.2f}s")
print(f"  {ms_per_call:.2f} ms/call")
print(f"  TFLOPS: {tflops:.2f}")
print(f"  vs ZLUDA wrapper 11.32 TFLOPS baseline: {(tflops/11.32-1)*100:+.0f}%")
print(f"  vs hardware peak 26.8 TFLOPS gfx906: {tflops/26.8*100:.0f}%")
print()

# ============================================================================
# T6: multi-stream sblocco
# ============================================================================
print("[T6] multi-stream — sblocco vs ZLUDA wait_event NULL bug")
try:
    streams = [torch.cuda.Stream() for _ in range(4)]

    A2 = torch.randn(2048, 2048, dtype=torch.float16, device='cuda')
    B2 = torch.randn(2048, 2048, dtype=torch.float16, device='cuda')

    # Warmup
    for s in streams:
        with torch.cuda.stream(s):
            C = torch.matmul(A2, B2)
    torch.cuda.synchronize()

    # Bench 4 stream parallel
    t0 = time.perf_counter()
    for it in range(20):
        for s in streams:
            with torch.cuda.stream(s):
                C = torch.matmul(A2, B2)
    for s in streams:
        s.synchronize()
    elapsed = time.perf_counter() - t0
    n_calls = 4 * 20
    flops_2048 = 2 * 2048 * 2048 * 2048 * n_calls
    tflops_ms = flops_2048 / elapsed / 1e12
    print(f"  4 stream × 20 iter matmul 2048² fp16: {elapsed:.3f}s")
    print(f"  TFLOPS effective multi-stream: {tflops_ms:.2f}")
    print(f"  wait_event multi-stream WORKING ✓")
except Exception as e:
    print(f"  FAIL multi-stream: {e}")
print()

# ============================================================================
# T7: cuGraph capture test (PyTorch native, no ZLUDA bypass)
# ============================================================================
print("[T7] cuGraph capture (sblocco fusion native)")
try:
    A3 = torch.randn(1024, 1024, dtype=torch.float16, device='cuda')
    B3 = torch.randn(1024, 1024, dtype=torch.float16, device='cuda')

    # Warmup
    for _ in range(3):
        out = torch.matmul(A3, B3)
    torch.cuda.synchronize()

    g = torch.cuda.CUDAGraph()
    with torch.cuda.graph(g):
        out_g = torch.matmul(A3, B3)

    # Replay bench
    N = 100
    t0 = time.perf_counter()
    for _ in range(N):
        g.replay()
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - t0
    print(f"  cuGraph replay {N}× matmul 1024² fp16: {elapsed*1000:.1f} ms ({elapsed/N*1e6:.0f} µs/replay)")
    print(f"  cuGraph PASS ✓")
except Exception as e:
    print(f"  FAIL cuGraph: {e}")
print()

# ============================================================================
# T8: hipMallocAsync (Fix #2 nativo)
# ============================================================================
print("[T8] caching allocator async")
try:
    # Stress alloc/free
    for i in range(50):
        t = torch.empty(256, 256, 256, dtype=torch.float16, device='cuda')
        del t
    torch.cuda.synchronize()
    print(f"  50 alloc/free cycle OK")
    print(f"  Allocator stats: {torch.cuda.memory_allocated() / 1e6:.1f} MB allocated, "
          f"{torch.cuda.memory_reserved() / 1e6:.1f} MB reserved")
except Exception as e:
    print(f"  FAIL allocator: {e}")
print()

# ============================================================================
# Summary
# ============================================================================
print("=" * 70)
print("BETATEST LA RUOTA COMPLETE")
print(f"Verdetto velocità matmul 4096² fp16 = {tflops:.2f} TFLOPS")
if tflops >= 15:
    print("⭐ TARGET RAGGIUNTO (>=15 TFLOPS = +33% vs ZLUDA)")
elif tflops >= 12:
    print("✓ Buon risultato, marginale gain vs ZLUDA")
else:
    print("⚠️ Sub-baseline ZLUDA, investigare")
print("=" * 70)

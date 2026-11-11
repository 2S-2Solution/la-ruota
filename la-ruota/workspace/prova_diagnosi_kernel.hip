// Perche' un kernel compilato COv4 va a 6 GB/s mentre hipMemcpy fa 494 GB/s?
// Tre misure per separare le cause:
//   A. calcolo puro (nessuna memoria)      -> se lento, il problema e' l'esecuzione
//   B. memoria con grid-stride, poche wave -> occupancy/dispatch
//   C. scalabilita' con la dimensione      -> costo fisso o proporzionale
#include <hip/hip_runtime.h>
#include <cstdio>

__global__ void calcolo(float* out, int iter) {
    float x = threadIdx.x * 1.0f;
    for (int i = 0; i < iter; ++i) x = fmaf(x, 1.000001f, 1.0f);
    if (x == -1.0f) out[0] = x;  // impedisce l'eliminazione
}

__global__ void copia_semplice(const float* __restrict__ s, float* __restrict__ d, size_t n) {
    size_t i = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) d[i] = s[i];
}

__global__ void copia_stride(const float* __restrict__ s, float* __restrict__ d, size_t n) {
    size_t passo = (size_t)gridDim.x * blockDim.x;
    for (size_t i = (size_t)blockIdx.x * blockDim.x + threadIdx.x; i < n; i += passo)
        d[i] = s[i];
}

__global__ void copia_float4(const float4* __restrict__ s, float4* __restrict__ d, size_t n4) {
    size_t i = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n4) d[i] = s[i];
}

#define CHK(x)                                                       \
    do {                                                             \
        hipError_t e = (x);                                          \
        if (e != hipSuccess) {                                       \
            printf("FALLITO %s -> %s\n", #x, hipGetErrorString(e));  \
            return 1;                                                \
        }                                                            \
    } while (0)

static hipEvent_t t0, t1;

template <typename F>
static float cronometra(F f, int iter) {
    for (int i = 0; i < 3; ++i) f();
    hipDeviceSynchronize();
    hipEventRecord(t0);
    for (int i = 0; i < iter; ++i) f();
    hipEventRecord(t1);
    hipEventSynchronize(t1);
    float ms = 0;
    hipEventElapsedTime(&ms, t0, t1);
    return ms / iter;
}

int main() {
    // NB: niente hipGetDeviceProperties — nei header del pack risolve a
    // hipGetDevicePropertiesR0600, che vive solo in amdhip64_6.dll (rimossa).
    struct { int multiProcessorCount; } p;
    CHK(hipDeviceGetAttribute(&p.multiProcessorCount, hipDeviceAttributeMultiprocessorCount, 0));
    int clock = 0, memClock = 0;
    CHK(hipDeviceGetAttribute(&clock, hipDeviceAttributeClockRate, 0));
    CHK(hipDeviceGetAttribute(&memClock, hipDeviceAttributeMemoryClockRate, 0));
    printf("CU=%d  clock=%d kHz  memClock=%d kHz\n\n", p.multiProcessorCount, clock, memClock);

    CHK(hipEventCreate(&t0));
    CHK(hipEventCreate(&t1));

    const size_t n = 64ull << 20;
    const size_t byte = n * sizeof(float);
    float *a, *b;
    CHK(hipMalloc(&a, byte));
    CHK(hipMalloc(&b, byte));
    CHK(hipMemset(a, 1, byte));

    // A. calcolo puro
    {
        const int iterInterne = 100000;
        const int blocchi = p.multiProcessorCount * 8;
        float ms = cronometra([&] {
            hipLaunchKernelGGL(calcolo, dim3(blocchi), dim3(256), 0, 0, b, iterInterne);
        }, 5);
        double flop = (double)blocchi * 256 * iterInterne * 2;
        printf("A. calcolo puro (fma)      : %7.1f GFLOPS  (%.2f ms)\n", flop / (ms / 1000.0) / 1e9, ms);
    }

    // B. varianti di copia
    {
        const int blocchi = (int)((n + 255) / 256);
        float ms = cronometra([&] {
            hipLaunchKernelGGL(copia_semplice, dim3(blocchi), dim3(256), 0, 0, a, b, n);
        }, 10);
        printf("B1. copia 1 elem/thread    : %7.0f GB/s   (%.2f ms)  griglia=%d blocchi\n",
               (2.0 * byte) / (ms / 1000.0) / 1e9, ms, blocchi);

        const int blocchiS = p.multiProcessorCount * 8;
        ms = cronometra([&] {
            hipLaunchKernelGGL(copia_stride, dim3(blocchiS), dim3(256), 0, 0, a, b, n);
        }, 10);
        printf("B2. copia grid-stride      : %7.0f GB/s   (%.2f ms)  griglia=%d blocchi\n",
               (2.0 * byte) / (ms / 1000.0) / 1e9, ms, blocchiS);

        const size_t n4 = n / 4;
        const int blocchi4 = (int)((n4 + 255) / 256);
        ms = cronometra([&] {
            hipLaunchKernelGGL(copia_float4, dim3(blocchi4), dim3(256), 0, 0,
                               (const float4*)a, (float4*)b, n4);
        }, 10);
        printf("B3. copia float4 (128 bit) : %7.0f GB/s   (%.2f ms)  griglia=%d blocchi\n",
               (2.0 * byte) / (ms / 1000.0) / 1e9, ms, blocchi4);
    }

    // C. scalabilita'
    printf("\nC. scalabilita' della copia semplice:\n");
    for (size_t elem = 1ull << 16; elem <= n; elem <<= 3) {
        const int blocchi = (int)((elem + 255) / 256);
        float ms = cronometra([&] {
            hipLaunchKernelGGL(copia_semplice, dim3(blocchi), dim3(256), 0, 0, a, b, elem);
        }, 20);
        printf("   %8zu elementi (%6.1f MB) : %8.3f ms  -> %6.1f GB/s\n",
               elem, elem * 4.0 / 1e6, ms, (2.0 * elem * 4) / (ms / 1000.0) / 1e9);
    }

    CHK(hipFree(a));
    CHK(hipFree(b));
    return 0;
}

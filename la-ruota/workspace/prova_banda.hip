// Misura la banda di memoria e il costo di lancio direttamente sul runtime,
// senza PyTorch. Serve a stabilire se i 4 GB/s misurati da torch dipendono
// dalla build di torch o sono il tetto di questa configurazione driver+COv4.
#include <hip/hip_runtime.h>
#include <cstdio>

__global__ void scala(const float* __restrict__ src, float* __restrict__ dst, size_t n) {
    size_t i = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) dst[i] = src[i] * 2.0f;
}

__global__ void vuoto() {}

#define CHK(x)                                                       \
    do {                                                             \
        hipError_t e = (x);                                          \
        if (e != hipSuccess) {                                       \
            printf("FALLITO %s -> %s\n", #x, hipGetErrorString(e));  \
            return 1;                                                \
        }                                                            \
    } while (0)

int main() {
    const size_t n = 64ull << 20;           // 64M float = 256 MB
    const size_t byte = n * sizeof(float);

    float *a = nullptr, *b = nullptr;
    CHK(hipMalloc(&a, byte));
    CHK(hipMalloc(&b, byte));
    CHK(hipMemset(a, 0, byte));

    hipEvent_t t0, t1;
    CHK(hipEventCreate(&t0));
    CHK(hipEventCreate(&t1));
    float ms = 0.0f;

    // --- kernel elementwise
    const int blocchi = (int)((n + 255) / 256);
    for (int i = 0; i < 3; ++i) hipLaunchKernelGGL(scala, dim3(blocchi), dim3(256), 0, 0, a, b, n);
    CHK(hipDeviceSynchronize());

    const int iter = 20;
    CHK(hipEventRecord(t0));
    for (int i = 0; i < iter; ++i)
        hipLaunchKernelGGL(scala, dim3(blocchi), dim3(256), 0, 0, a, b, n);
    CHK(hipEventRecord(t1));
    CHK(hipEventSynchronize(t1));
    CHK(hipEventElapsedTime(&ms, t0, t1));
    printf("kernel elementwise : %.0f GB/s   (%.2f ms/iter)\n",
           (2.0 * byte * iter) / (ms / 1000.0) / 1e9, ms / iter);

    // --- hipMemcpy device->device
    CHK(hipEventRecord(t0));
    for (int i = 0; i < iter; ++i) CHK(hipMemcpy(b, a, byte, hipMemcpyDeviceToDevice));
    CHK(hipEventRecord(t1));
    CHK(hipEventSynchronize(t1));
    CHK(hipEventElapsedTime(&ms, t0, t1));
    printf("hipMemcpy D2D      : %.0f GB/s   (%.2f ms/iter)\n",
           (2.0 * byte * iter) / (ms / 1000.0) / 1e9, ms / iter);

    // --- costo di lancio (kernel vuoto, in coda)
    for (int i = 0; i < 100; ++i) hipLaunchKernelGGL(vuoto, dim3(1), dim3(1), 0, 0);
    CHK(hipDeviceSynchronize());
    const int iterL = 2000;
    CHK(hipEventRecord(t0));
    for (int i = 0; i < iterL; ++i) hipLaunchKernelGGL(vuoto, dim3(1), dim3(1), 0, 0);
    CHK(hipEventRecord(t1));
    CHK(hipEventSynchronize(t1));
    CHK(hipEventElapsedTime(&ms, t0, t1));
    printf("costo di lancio    : %.1f us\n", (ms * 1000.0) / iterL);

    CHK(hipFree(a));
    CHK(hipFree(b));
    return 0;
}

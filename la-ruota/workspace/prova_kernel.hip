// Prova autonoma: un kernel reale sul runtime Adrenalin, senza PyTorch.
// Serve a stabilire se il downgrade a code object v4 basta a far girare i kernel.
#include <hip/hip_runtime.h>
#include <cstdio>

__global__ void raddoppia(float* p, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) p[i] = p[i] * 2.0f + 1.0f;
}

#define CHK(x)                                                                 \
    do {                                                                       \
        hipError_t e = (x);                                                    \
        if (e != hipSuccess) {                                                 \
            printf("FALLITO %s -> %s\n", #x, hipGetErrorString(e));            \
            return 1;                                                          \
        }                                                                      \
    } while (0)

int main() {
    const int n = 256;
    float host[n];
    for (int i = 0; i < n; ++i) host[i] = (float)i;

    float* dev = nullptr;
    CHK(hipMalloc(&dev, n * sizeof(float)));
    CHK(hipMemcpy(dev, host, n * sizeof(float), hipMemcpyHostToDevice));

    hipLaunchKernelGGL(raddoppia, dim3(1), dim3(n), 0, 0, dev, n);
    CHK(hipGetLastError());
    CHK(hipDeviceSynchronize());

    float out[n];
    CHK(hipMemcpy(out, dev, n * sizeof(float), hipMemcpyDeviceToHost));
    CHK(hipFree(dev));

    int errori = 0;
    for (int i = 0; i < n; ++i)
        if (out[i] != (float)i * 2.0f + 1.0f) ++errori;

    printf(errori == 0 ? "KERNEL ESEGUITO, risultati corretti\n"
                       : "kernel eseguito ma %d valori errati\n",
           errori);
    return errori == 0 ? 0 : 1;
}

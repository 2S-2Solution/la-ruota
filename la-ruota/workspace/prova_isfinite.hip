// L'involucro isfinite di AmpKernels.hip e' scritto per nvcc. Con clang/HIP
// "isfinite" potrebbe risolvere alla versione HOST anche dentro un kernel:
// il codice device salterebbe a un indirizzo host -> memory fault.
// Qui si confrontano tre formulazioni sullo stesso kernel.
#include <hip/hip_runtime.h>
#include <math.h>
#include <cstdio>

// come nel sorgente di PyTorch
static __host__ __device__ __forceinline__ int isfinite_come_pytorch(float v) {
    return isfinite(v);
}
// builtin del compilatore, valido su host e device
static __host__ __device__ __forceinline__ int isfinite_builtin(float v) {
    return __builtin_isfinite(v);
}

__global__ void k_pytorch(const float* in, int* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) out[i] = isfinite_come_pytorch(in[i]);
}
__global__ void k_builtin(const float* in, int* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) out[i] = isfinite_builtin(in[i]);
}

int main() {
    const int n = 256;
    float host[n];
    for (int i = 0; i < n; ++i) host[i] = (float)i;
    host[3] = INFINITY;
    host[7] = NAN;

    float* d_in = nullptr;
    int* d_out = nullptr;
    hipMalloc(&d_in, n * sizeof(float));
    hipMalloc(&d_out, n * sizeof(int));
    hipMemcpy(d_in, host, n * sizeof(float), hipMemcpyHostToDevice);

    struct { const char* nome; void (*k)(const float*, int*, int); } prove[] = {
        {"isfinite come in PyTorch", k_pytorch},
        {"__builtin_isfinite      ", k_builtin},
    };

    for (auto& p : prove) {
        hipMemset(d_out, 0, n * sizeof(int));
        hipLaunchKernelGGL(p.k, dim3(1), dim3(n), 0, 0, d_in, d_out, n);
        hipError_t e = hipDeviceSynchronize();
        if (e != hipSuccess) {
            printf("%s -> FALLITO: %s\n", p.nome, hipGetErrorString(e));
            continue;
        }
        int out[n];
        hipMemcpy(out, d_out, n * sizeof(int), hipMemcpyDeviceToHost);
        // atteso: tutti 1 tranne l'indice 3 (inf) e il 7 (NaN)
        int errori = 0;
        for (int i = 0; i < n; ++i) {
            int atteso = (i == 3 || i == 7) ? 0 : 1;
            if ((out[i] != 0) != (atteso != 0)) ++errori;
        }
        printf("%s -> eseguito, %d risultati errati su %d\n", p.nome, errori, n);
    }

    hipFree(d_in);
    hipFree(d_out);
    return 0;
}

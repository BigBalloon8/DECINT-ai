#include "cuda_runtime.h"
#include "nccl.h"

void ncclInit(int nDev)
{
    ncclComm_t comms[nDev];
    int devs[nDev];
    for (int i = 0; i<nDev; i++){
        devs[i] = i
    }
    ncclCommInitAll(comms, nDev, devs)
}

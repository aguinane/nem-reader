# Pandas vs Nvidia cuDF
This is a demonstration of the performance gain of using Nvidia's cuDF in GPU library instead of the Pandas in Memory library. A server these days has a maximum limit of [192](https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9965.html) processing cores vs Nvidia GPU core counts of 20,000+ for the [H200](https://www.nvidia.com/en-us/data-center/h200/) card. As the business problem of predicting electricity supply demand requires low latency and faster execution times GPU based solutions can offer up to 1000 times the performance of CPU based solutions with specific cores designed for vecctor operatons and complex linear algebra matrix multiplication and addition/subtraction. 

## Demo system
The demo below is based on the A2000 Ampere Card the lowest end Enterprise card available with only 3328 cores with 12GB of GDDR6 VRAM. 

## cuDF
The cuDF library uses identical commands and API's to Pandas so python code is interchangeable. cuDF also offers a high performance c++ API that can also run in [Bluefield 3](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/documents/datasheet-nvidia-bluefield-3-dpu.pdf) DPU (Data Processing Unit) Network cards terminating some functions at the network leaving more capacity for GPU and CPU operations. Using [GPUDirect](https://docs.nvidia.com/gpudirect-storage/index.html)  functions the system can also bypass or accelerate Disk and Memory bottlenecks.

## Demo results
As you can see executing basic operations using Pandas (df) and cuDF(cf) show greater performance using the GPU to manimpulate matrix operations showing 33% of the time for load and 13.45% of the compute time. When using advanced cards like the H200 card expect 1000 fold performance gains

## Installation

Install via [Nvidia Rapids](https://docs.rapids.ai/install/)

or
```
!pip install \
    --extra-index-url=https://pypi.nvidia.com \
    "cudf-cu12==24.12.*"
```

## Usage

Instead of importing pandas include

```import cudf as cf```

And replace df with cf in your code to utilize the GPU
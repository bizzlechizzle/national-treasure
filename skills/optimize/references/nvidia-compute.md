# NVIDIA GPU Optimization for ML/AI Workloads

Maximize compute performance for machine learning, deep learning, and CUDA workloads.

## Driver and CUDA Stack

### Recommended Versions (RTX 40 Series)

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Driver | 525+ | Latest stable |
| CUDA | 11.8 | 12.x |
| cuDNN | 8.9+ | 8.9.6+ |
| PyTorch | 2.0+ | 2.1+ |
| TensorFlow | 2.12+ | 2.15+ |

### Check Installed Versions

```bash
# Driver version
nvidia-smi --query-gpu=driver_version --format=csv,noheader

# CUDA version
nvcc --version
# or
cat /usr/local/cuda/version.txt

# cuDNN version
cat /usr/include/cudnn_version.h | grep CUDNN_MAJOR -A 2
```

---

## nvidia-smi Configuration

### Persistence Mode

Keeps GPU initialized, reduces first-operation latency:

```bash
# Enable
sudo nvidia-smi -pm 1

# Disable
sudo nvidia-smi -pm 0

# Verify
nvidia-smi -q | grep "Persistence Mode"
```

### Compute Mode

| Mode | Description | Use Case |
|------|-------------|----------|
| Default | Multiple processes | Development |
| Exclusive Process | One process per GPU | Production training |
| Prohibited | No compute allowed | Display-only GPU |

```bash
# Set exclusive mode
sudo nvidia-smi -c EXCLUSIVE_PROCESS

# Reset to default
sudo nvidia-smi -c DEFAULT

# Check
nvidia-smi -q | grep "Compute Mode"
```

### Power Management

```bash
# Check limits
nvidia-smi -q -d POWER

# Example output:
# Min Power Limit: 100.00 W
# Max Power Limit: 450.00 W
# Default Power Limit: 350.00 W

# Set to max (for RTX 4090)
sudo nvidia-smi -pl 450

# Or specific value
sudo nvidia-smi -pl 350
```

### Clock Speeds

```bash
# Lock clocks for consistent benchmarking
# RTX 4090 example: GPU 2520MHz, Memory 10501MHz
sudo nvidia-smi -lgc 2520
sudo nvidia-smi -lmc 10501

# Reset to default
sudo nvidia-smi -rgc
sudo nvidia-smi -rmc
```

---

## VRAM Management

### RTX 4090 (24GB VRAM)

| Model Size | Precision | Inference VRAM | Training VRAM |
|------------|-----------|----------------|---------------|
| 7B | FP16 | ~14GB | ~28GB |
| 7B | INT8 | ~7GB | N/A |
| 7B | INT4 | ~4GB | N/A |
| 13B | FP16 | ~26GB (tight) | Requires 48GB+ |
| 70B | INT4 | ~35GB | Requires 80GB+ |

### PyTorch Memory Optimization

```python
import torch

# Clear cache
torch.cuda.empty_cache()

# Enable memory-efficient attention (PyTorch 2.0+)
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)

# Memory fragmentation handling
import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# Gradient checkpointing (trades compute for memory)
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("model_name")
model.gradient_checkpointing_enable()

# Mixed precision
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()
with autocast():
    output = model(input)
    loss = loss_fn(output, target)
scaler.scale(loss).backward()
```

### Batch Size Optimization

```python
# Start with small batch, increase until OOM
# Then back off 10-20%

# Monitor during training
watch -n 1 nvidia-smi

# Or in Python
import pynvml
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
info = pynvml.nvmlDeviceGetMemoryInfo(handle)
print(f"Used: {info.used / 1024**3:.2f} GB")
```

---

## Multi-GPU Configuration

### Environment Variables

```bash
# Limit visible GPUs
export CUDA_VISIBLE_DEVICES=0,1

# Specific GPU order
export CUDA_DEVICE_ORDER=PCI_BUS_ID

# For NVLink systems
export NCCL_P2P_LEVEL=NVL
```

### PyTorch DataParallel vs DistributedDataParallel

```python
# DataParallel (simpler, less efficient)
model = torch.nn.DataParallel(model)

# DistributedDataParallel (recommended for multi-GPU)
import torch.distributed as dist
dist.init_process_group("nccl")
model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[local_rank])
```

### NCCL Tuning

```bash
# Debug NCCL
export NCCL_DEBUG=INFO

# For PCIe-connected GPUs (no NVLink)
export NCCL_P2P_DISABLE=1
export NCCL_SHM_DISABLE=1
```

---

## Monitoring Tools

### nvidia-smi

```bash
# Continuous monitoring
nvidia-smi dmon -d 1  # Every 1 second

# Specific metrics
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw --format=csv -l 1
```

### nvitop (Recommended)

```bash
pip install nvitop
nvitop  # Interactive TUI

# Or one-shot
nvitop -1
```

### PyTorch Profiler

```python
from torch.profiler import profile, record_function, ProfilerActivity

with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
    model(input)

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
```

---

## Benchmarking

### CUDA Bandwidth Test

```bash
# Part of CUDA samples
cd /usr/local/cuda/samples/1_Utilities/bandwidthTest
make
./bandwidthTest
```

### llama.cpp (LLM Inference)

```bash
# Build with CUDA
cmake -B build -DLLAMA_CUDA=ON
cmake --build build --config Release

# Benchmark
./build/bin/llama-bench -m model.gguf -n 128 -ngl 99
```

### PyTorch Benchmark

```python
import torch
import time

# Matrix multiplication benchmark
size = 8192
a = torch.randn(size, size, device='cuda')
b = torch.randn(size, size, device='cuda')

# Warmup
for _ in range(10):
    c = torch.matmul(a, b)
torch.cuda.synchronize()

# Benchmark
start = time.time()
for _ in range(100):
    c = torch.matmul(a, b)
torch.cuda.synchronize()
elapsed = time.time() - start

print(f"Time: {elapsed/100*1000:.2f} ms per iteration")
print(f"TFLOPS: {2*size**3*100/elapsed/1e12:.2f}")
```

---

## Common Issues

### CUDA Out of Memory

```python
# Clear cache
torch.cuda.empty_cache()

# Reduce batch size
# Enable gradient checkpointing
# Use mixed precision (FP16)
# Use 8-bit optimizers (bitsandbytes)
```

### Slow First Operation

- Enable persistence mode: `nvidia-smi -pm 1`
- Warmup iterations in benchmarks

### Driver/CUDA Mismatch

```bash
# Check compatibility
nvidia-smi  # Shows max supported CUDA version
nvcc --version  # Shows installed CUDA toolkit version

# CUDA toolkit must be <= driver's max CUDA version
```

### Thermal Throttling

```bash
# Monitor temperature
nvidia-smi -q -d TEMPERATURE

# Set temperature target (if supported)
nvidia-smi -gtt 83  # 83°C target
```

---

## Production Deployment

### Systemd Service for Persistence

```ini
# /etc/systemd/system/nvidia-persistence.service
[Unit]
Description=NVIDIA Persistence Daemon
Wants=syslog.target

[Service]
Type=forking
ExecStart=/usr/bin/nvidia-persistenced --user nvidia-persistenced
ExecStopPost=/bin/rm -rf /var/run/nvidia-persistenced

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable nvidia-persistence
sudo systemctl start nvidia-persistence
```

### Docker GPU Access

```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit

# Run with GPU
docker run --gpus all -it pytorch/pytorch:latest
```

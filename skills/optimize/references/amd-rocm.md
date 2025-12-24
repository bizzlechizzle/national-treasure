# AMD ROCm GPU Optimization

Setup and tuning for AMD GPUs with ROCm for ML/AI workloads.

## Supported Hardware

### Consumer (RDNA 3)
| GPU | VRAM | ROCm Support |
|-----|------|--------------|
| RX 7900 XTX | 24GB | ROCm 6.x, gfx1100 |
| RX 7900 XT | 20GB | ROCm 6.x, gfx1100 |
| RX 7900 GRE | 16GB | ROCm 6.x, gfx1100 |
| RX 7800 XT | 16GB | ROCm 6.x, gfx1101 |
| RX 7700 XT | 12GB | ROCm 6.x, gfx1101 |

### Professional (CDNA/RDNA Pro)
| GPU | VRAM | Notes |
|-----|------|-------|
| MI300X | 192GB | Data center, full support |
| MI250X | 128GB | HPC, full support |
| Radeon PRO W7900 | 48GB | Workstation |

---

## Installation (Ubuntu)

### Add Repository

```bash
# Ubuntu 22.04
wget https://repo.radeon.com/amdgpu-install/6.0/ubuntu/jammy/amdgpu-install_6.0.60000-1_all.deb
sudo apt install ./amdgpu-install_6.0.60000-1_all.deb

# Install ROCm
sudo amdgpu-install --usecase=rocm
```

### Add User to Groups

```bash
sudo usermod -a -G render,video $USER
# Logout and login
```

### Verify Installation

```bash
# Check GPU detection
rocm-smi

# HIP info
hipconfig --full

# Check compute capability
rocminfo | grep "gfx"
```

---

## Critical Environment Variables

### RX 7900 Series (gfx1100)

**This is mandatory for RDNA 3 consumer GPUs:**

```bash
# Add to ~/.bashrc
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Apply immediately
source ~/.bashrc
```

Without this, many ML frameworks will fail to detect or use the GPU.

### Other Useful Variables

```bash
# Visible devices (multi-GPU)
export HIP_VISIBLE_DEVICES=0,1

# Debug output
export AMD_LOG_LEVEL=3  # 0=off, 4=verbose

# Force specific GPU
export ROCR_VISIBLE_DEVICES=0
```

---

## PyTorch with ROCm

### Installation

```bash
# PyTorch 2.1+ with ROCm 6.0
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

# Verify
python -c "import torch; print(torch.cuda.is_available())"  # Should print True
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### Flash Attention

Flash Attention support requires PyTorch 2.5.0+:

```python
import torch

# Check Flash Attention availability
print(torch.backends.cuda.flash_sdp_enabled())

# Enable if available
torch.backends.cuda.enable_flash_sdp(True)
torch.backends.cuda.enable_mem_efficient_sdp(True)
```

### Example Training Script

```python
import torch

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Model to GPU
model = model.to(device)

# Training loop
for batch in dataloader:
    inputs = batch[0].to(device)
    labels = batch[1].to(device)
    outputs = model(inputs)
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()
```

---

## TensorFlow with ROCm

### Installation

```bash
# TensorFlow-ROCm
pip install tensorflow-rocm

# Verify
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

---

## Performance Tuning

### Power Profile

```bash
# Check current level
rocm-smi --showperflevel

# Set high performance
sudo rocm-smi --setperflevel high

# Or manual control
sudo rocm-smi --setsclk 2  # Set specific clock level
```

### Fan Control

```bash
# Show fan speed
rocm-smi --showfan

# Manual fan control (percentage)
sudo rocm-smi --setfan 80
```

### Power Limit

```bash
# Show current
rocm-smi --showpower

# Set power cap (example: 300W)
sudo rocm-smi --setpoweroverdrive 300
```

---

## llama.cpp with ROCm

### Build

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build with HIP (ROCm)
make LLAMA_HIPBLAS=1

# Or CMake
cmake -B build -DLLAMA_HIPBLAS=ON
cmake --build build --config Release
```

### Run

```bash
# Offload all layers to GPU
./main -m model.gguf -ngl 99 -p "Hello"

# Benchmark
./llama-bench -m model.gguf -n 128 -ngl 99
```

---

## Monitoring

### rocm-smi Commands

```bash
# Full status
rocm-smi

# Continuous monitoring
watch -n 1 rocm-smi

# GPU utilization
rocm-smi --showuse

# Memory info
rocm-smi --showmeminfo vram

# Temperature
rocm-smi --showtemp

# All info
rocm-smi -a
```

### radeontop (Alternative)

```bash
sudo apt install radeontop
radeontop
```

---

## Multi-GPU Setup

### Check Topology

```bash
rocm-smi --showtopo
```

### Environment for Multi-GPU

```bash
# Specify GPUs
export HIP_VISIBLE_DEVICES=0,1

# Or ROCR
export ROCR_VISIBLE_DEVICES=0,1
```

### PyTorch Multi-GPU

```python
import torch

# Check GPU count
print(torch.cuda.device_count())

# DataParallel (simple)
model = torch.nn.DataParallel(model)

# DistributedDataParallel (recommended)
import torch.distributed as dist
dist.init_process_group("nccl")  # RCCL on AMD
```

---

## Known Issues

### Display Issues During ML Workloads

**Problem:** Display may not wake from standby during ROCm workloads.
**Workaround:** Disable display sleep in Ubuntu settings during ML work.

### Multi-GPU PCIe Issues

**Problem:** HIP error when GPU on chipset PCIe slot.
**Workaround:** Use CPU-connected PCIe slots for compute GPUs.

### Performance Gap vs NVIDIA

hipBLAS may lag behind cuBLAS in some workloads. This is improving with each ROCm release.

---

## Troubleshooting

### GPU Not Detected

```bash
# Check kernel module
lsmod | grep amdgpu

# Check dmesg
dmesg | grep -i amdgpu

# Reinstall driver
sudo amdgpu-install --uninstall
sudo amdgpu-install --usecase=rocm
```

### HIP Runtime Error

```bash
# Ensure environment variable is set
echo $HSA_OVERRIDE_GFX_VERSION
# Should output: 11.0.0

# Check HIP
hipconfig
```

### Memory Errors

```bash
# Check VRAM health
rocm-smi --showmeminfo vram

# Reset GPU
sudo rocm-smi --gpureset
```

---

## Benchmarking

### HIP Bandwidth Test

```bash
cd /opt/rocm/bin
./hipBusBandwidth
```

### rocBLAS Benchmark

```bash
rocblas-bench -f gemm -r f32_r --transposeA N --transposeB N -m 4096 -n 4096 -k 4096
```

### PyTorch Matrix Multiplication

```python
import torch
import time

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

print(f"Time: {elapsed/100*1000:.2f} ms")
print(f"TFLOPS: {2*size**3*100/elapsed/1e12:.2f}")
```

---

## Resources

- [ROCm Documentation](https://rocm.docs.amd.com/)
- [ROCm Installation Guide](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/)
- [PyTorch ROCm](https://pytorch.org/get-started/locally/)
- [ROCm GitHub Issues](https://github.com/ROCm/ROCm/issues)

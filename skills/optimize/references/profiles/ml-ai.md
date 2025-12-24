# ML/AI Workload Optimization Profile

Maximize GPU compute throughput for machine learning training and inference.

## Goals

- Maximum GPU utilization
- Efficient VRAM usage
- Fast data loading
- Consistent training performance

---

## Hardware Tier Recommendations

| Tier | Training | Inference |
|------|----------|-----------|
| **Pro-sumer** (RTX 4090, 24GB) | 7B-13B models, FP16/INT8 | 70B INT4, multiple concurrent |
| **Enthusiast** (RTX 4070, 12GB) | 7B INT8, LoRA fine-tuning | 13B INT4 |
| **Consumer** (RTX 4060, 8GB) | Small models only | 7B INT4 |

---

## GPU Configuration

### NVIDIA

```bash
# Persistence mode (reduce first-op latency)
sudo nvidia-smi -pm 1

# Maximum power limit (check your card's max first)
nvidia-smi -q -d POWER  # Check limits
sudo nvidia-smi -pl 450  # RTX 4090 example

# Exclusive compute mode (one process per GPU)
sudo nvidia-smi -c EXCLUSIVE_PROCESS

# Verify
nvidia-smi -q | grep -E "Persistence|Compute Mode|Power"
```

### AMD ROCm

```bash
# Critical for RX 7900 series
export HSA_OVERRIDE_GFX_VERSION=11.0.0
echo 'export HSA_OVERRIDE_GFX_VERSION=11.0.0' >> ~/.bashrc

# High performance
sudo rocm-smi --setperflevel high

# Monitor
watch -n 1 rocm-smi --showuse
```

---

## System Configuration

### Linux Memory Settings

```bash
# Low swappiness (keep model in RAM)
echo 'vm.swappiness=1' | sudo tee -a /etc/sysctl.d/99-ml.conf

# Disable THP (causes latency spikes)
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

# Apply
sudo sysctl -p /etc/sysctl.d/99-ml.conf
```

### CPU Governor

```bash
# Performance for data loading, preprocessing
sudo cpupower frequency-set -g performance
```

### Storage (Data Loading)

```bash
# NVMe scheduler for parallel I/O
echo none | sudo tee /sys/block/nvme0n1/queue/scheduler

# Store datasets on NVMe
# Use multiple workers in DataLoader
```

---

## PyTorch Optimization

### Environment Variables

```bash
# CUDA memory
export PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True'

# Disable debug for production
export CUDA_LAUNCH_BLOCKING=0

# Thread settings
export OMP_NUM_THREADS=8  # Adjust for your CPU
export MKL_NUM_THREADS=8
```

### Code Optimizations

```python
import torch

# Use TF32 on Ampere+ (faster, ~same accuracy)
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# Benchmark mode (finds fastest algorithms)
torch.backends.cudnn.benchmark = True

# Compile model (PyTorch 2.0+)
model = torch.compile(model, mode="reduce-overhead")
```

### Mixed Precision Training

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    optimizer.zero_grad()

    with autocast():
        output = model(batch)
        loss = loss_fn(output, target)

    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### Gradient Checkpointing (Save VRAM)

```python
# Hugging Face Transformers
model.gradient_checkpointing_enable()

# Generic PyTorch
from torch.utils.checkpoint import checkpoint

def forward(self, x):
    return checkpoint(self.layer, x)
```

### Efficient DataLoader

```python
from torch.utils.data import DataLoader

dataloader = DataLoader(
    dataset,
    batch_size=32,
    num_workers=8,           # Parallel data loading
    pin_memory=True,         # Faster GPU transfer
    prefetch_factor=2,       # Prefetch batches
    persistent_workers=True, # Keep workers alive
)
```

---

## VRAM Management

### Monitor Usage

```python
import torch

# Current allocation
print(f"Allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
print(f"Cached: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")

# Peak usage
print(f"Peak: {torch.cuda.max_memory_allocated() / 1024**3:.2f} GB")

# Clear cache
torch.cuda.empty_cache()
```

### Batch Size Tuning

```python
# Find optimal batch size
def find_batch_size(model, input_shape, start=1, max_bs=256):
    batch_size = start
    while batch_size <= max_bs:
        try:
            x = torch.randn(batch_size, *input_shape, device='cuda')
            _ = model(x)
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            print(f"Batch size {batch_size}: OK")
            batch_size *= 2
        except RuntimeError as e:
            if "out of memory" in str(e):
                print(f"Max batch size: {batch_size // 2}")
                return batch_size // 2
            raise
    return batch_size // 2
```

### Quantization (Reduce VRAM)

```python
# 8-bit with bitsandbytes
import bitsandbytes as bnb
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "model_name",
    load_in_8bit=True,
    device_map="auto",
)

# 4-bit with bitsandbytes
model = AutoModelForCausalLM.from_pretrained(
    "model_name",
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    device_map="auto",
)
```

---

## Multi-GPU Training

### DistributedDataParallel

```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

# Initialize
dist.init_process_group("nccl")
local_rank = int(os.environ["LOCAL_RANK"])
torch.cuda.set_device(local_rank)

# Wrap model
model = model.to(local_rank)
model = DDP(model, device_ids=[local_rank])

# Launch
# torchrun --nproc_per_node=2 train.py
```

### FSDP (Fully Sharded Data Parallel)

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = FSDP(model)
```

### DeepSpeed

```python
import deepspeed

model, optimizer, _, _ = deepspeed.initialize(
    model=model,
    config="ds_config.json",
)
```

---

## Inference Optimization

### TensorRT (NVIDIA)

```python
import torch_tensorrt

model_trt = torch_tensorrt.compile(
    model,
    inputs=[torch_tensorrt.Input(shape=[1, 3, 224, 224])],
    enabled_precisions={torch.half},
)
```

### ONNX Runtime

```python
import onnxruntime as ort

# Export to ONNX
torch.onnx.export(model, dummy_input, "model.onnx")

# Run with ONNX Runtime
session = ort.InferenceSession("model.onnx", providers=['CUDAExecutionProvider'])
output = session.run(None, {"input": input_data})
```

### vLLM (LLM Serving)

```bash
pip install vllm

# Serve
python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-2-7b-hf

# Request
curl http://localhost:8000/v1/completions -d '{"model": "meta-llama/Llama-2-7b-hf", "prompt": "Hello"}'
```

---

## Monitoring

### During Training

```bash
# GPU utilization
watch -n 1 nvidia-smi

# Beautiful monitoring
pip install nvitop
nvitop

# Log to file
nvidia-smi --query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,temperature.gpu,power.draw --format=csv -l 1 > gpu_log.csv
```

### Weights & Biases

```python
import wandb

wandb.init(project="my-project")
wandb.config.update({"batch_size": 32, "lr": 1e-4})

for step, loss in enumerate(training_loop):
    wandb.log({"loss": loss, "step": step})
```

---

## Common Issues

### OOM During Training
- Reduce batch size
- Enable gradient checkpointing
- Use mixed precision
- Use 8-bit optimizers

### Slow Data Loading
- Increase `num_workers`
- Enable `pin_memory=True`
- Store data on NVMe
- Use `persistent_workers=True`

### GPU Underutilized
- Increase batch size
- Check data loading (CPU bottleneck)
- Profile with `torch.profiler`

### Inconsistent Training Speed
- Set `torch.backends.cudnn.benchmark = True`
- Lock GPU clocks for benchmarking
- Disable THP if not already

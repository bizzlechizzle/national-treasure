# System Optimization Skill - SME Reference Document

> **Generated**: 2025-12-23
> **Sources current as of**: December 2025
> **Scope**: Exhaustive
> **Version**: 1.0
> **Audit-Ready**: Yes

---

## Executive Summary / TLDR

This document provides the foundational knowledge for building a cross-platform system optimization skill targeting pro-sumer hardware (high-end CPUs, GPUs, NVMe storage, 64GB+ RAM). The skill enables users to extract maximum performance from enthusiast-grade hardware across Windows, macOS, and Linux.

**Key Capabilities:**
- **Hardware Detection**: Automated scanning of CPU (Intel/AMD), GPU (NVIDIA/AMD/Intel Arc), RAM, and storage using `psutil`, `GPUtil`, `py-cpuinfo`, and platform-specific APIs
- **Dynamic Scaling**: Optimizations scale based on detected hardware tier (consumer → pro-sumer → workstation)
- **Use Case Profiles**: Gaming, ML/AI, content creation, development, virtualization - each with tailored settings
- **Safety-First**: All optimizations are non-destructive with rollback via BTRFS snapshots (Linux), System Restore (Windows), or Time Machine (macOS)
- **Measurable Results**: Before/after benchmarking with Phoronix Test Suite, Geekbench, and custom metrics

**Target Hardware Tier (Pro-sumer):**
- CPU: AMD Ryzen 9 / Intel Core i9, Threadripper, high core-count desktop processors
- GPU: NVIDIA RTX 4090/4080, AMD RX 7900 XTX/XT, Intel Arc A770
- RAM: 64GB+ DDR5, high-frequency modules
- Storage: NVMe Gen4/Gen5 SSDs

---

## Background & Context

Modern pro-sumer hardware delivers exceptional raw performance, but operating systems ship with conservative defaults designed for broad compatibility rather than maximum throughput. A user with an RTX 4090 and Ryzen 9 7950X may only utilize 60-70% of their system's potential without proper tuning.

This optimization skill bridges that gap by:
1. Detecting available hardware capabilities
2. Matching detected capabilities to appropriate optimization profiles
3. Applying platform-specific tuning while maintaining system stability
4. Providing metrics to quantify performance gains

The philosophy is simple: **if someone has beast hardware, use every ounce of it**.

---

## 1. Hardware Detection & Scanning

### 1.1 Cross-Platform Detection Libraries

| Component | Tool/Library | Platform | Notes |
|-----------|-------------|----------|-------|
| CPU | `psutil`, `py-cpuinfo` | All | Core counts, frequencies, architecture |
| GPU (NVIDIA) | `GPUtil`, `pynvml` | All | VRAM, CUDA cores, driver version |
| GPU (AMD) | `rocm-smi`, custom | Linux | ROCm detection for ML workloads |
| GPU (Intel) | `intel-gpu-tools` | Linux | Arc GPU detection |
| RAM | `psutil.virtual_memory()` | All | Total, available, speed via platform APIs |
| Storage | `psutil.disk_io_counters()` | All | NVMe detection via device paths |
| Platform | `platform` module | All | OS version, architecture |

### 1.2 Python Hardware Detection Implementation

```python
import psutil
import platform
from typing import Dict, Any

def detect_hardware() -> Dict[str, Any]:
    """Comprehensive cross-platform hardware detection."""
    hw = {
        "platform": {
            "os": platform.system(),
            "version": platform.version(),
            "arch": platform.machine(),
        },
        "cpu": {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "freq_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else None,
        },
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        },
        "storage": [],
        "gpu": [],
    }

    # Detect storage devices
    for partition in psutil.disk_partitions():
        usage = psutil.disk_usage(partition.mountpoint)
        hw["storage"].append({
            "device": partition.device,
            "mountpoint": partition.mountpoint,
            "fstype": partition.fstype,
            "total_gb": round(usage.total / (1024**3), 1),
            "is_nvme": "nvme" in partition.device.lower(),
        })

    # GPU detection (NVIDIA)
    try:
        import GPUtil
        for gpu in GPUtil.getGPUs():
            hw["gpu"].append({
                "vendor": "NVIDIA",
                "name": gpu.name,
                "vram_mb": gpu.memoryTotal,
                "driver": gpu.driver,
            })
    except ImportError:
        pass

    return hw

def classify_hardware_tier(hw: Dict[str, Any]) -> str:
    """Classify system into optimization tier."""
    cpu_cores = hw["cpu"]["logical_cores"]
    ram_gb = hw["memory"]["total_gb"]

    # Check for pro-sumer indicators
    has_high_end_gpu = any(
        g["vram_mb"] >= 16000 for g in hw["gpu"]
    )
    has_high_ram = ram_gb >= 64
    has_high_cores = cpu_cores >= 16

    if has_high_end_gpu and has_high_ram and has_high_cores:
        return "prosumer"
    elif cpu_cores >= 8 and ram_gb >= 32:
        return "enthusiast"
    else:
        return "consumer"
```

### 1.3 Platform-Specific Detection Commands

**Windows (PowerShell):**
```powershell
# CPU info
Get-WmiObject Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors

# GPU info
Get-WmiObject Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion

# Storage (NVMe detection)
Get-PhysicalDisk | Select-Object MediaType, BusType, Size, Model
```

**Linux (Bash):**
```bash
# CPU
lscpu | grep -E "Model name|Socket|Core|Thread"

# GPU (NVIDIA)
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

# GPU (AMD)
rocm-smi --showproductname --showmeminfo vram

# NVMe drives
nvme list
```

**macOS (zsh):**
```zsh
# System overview (Apple Silicon)
system_profiler SPHardwareDataType

# GPU
system_profiler SPDisplaysDataType

# Storage
diskutil list
```

---

## 2. CPU Optimization

### 2.1 Windows CPU Tuning

#### Power Plans [HIGH]

Windows 11 has known latency issues with standard power plans. The **Ultimate Performance** plan is recommended for pro-sumer systems [1][2].

```powershell
# Enable Ultimate Performance plan (hidden by default)
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61

# Activate it
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61
```

**AMD Ryzen-Specific:**
- Ryzen 5000+ series: Windows Balanced plan is acceptable; Ultimate Performance for maximum throughput [3]
- Install AMD Chipset drivers for CPPC2 (Collaborative Power Performance Control) [3]

**Intel-Specific:**
- 12th/13th/14th Gen: Use custom power plans optimized for P-core/E-core hybrid architecture [4]
- Disable Core Parking for latency-sensitive workloads

#### Hidden Power Options

```powershell
# Expose CPU boost mode option
powercfg -attributes sub_processor perfboostmode -attrib_hide

# Expose core parking options
powercfg -attributes sub_processor 0cc5b647-c1df-4637-891a-dec35c318583 -attrib_hide
```

#### Core Parking (Registry) [MEDIUM]

Disabling core parking reduces latency in fast-paced applications:

```
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\
  54533251-82be-4824-96c1-47b60b740d00\0cc5b647-c1df-4637-891a-dec35c318583

Set "Attributes" DWORD to 0
```

### 2.2 Linux CPU Tuning

#### CPU Governors [HIGH]

Modern kernels (4.7+) use `schedutil` by default, which integrates with the scheduler for intelligent frequency scaling [5].

```bash
# Check current governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Set performance governor (all cores)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Persistent via systemd service
sudo systemctl enable --now cpupower
sudo cpupower frequency-set -g performance
```

**Governor Comparison:**
| Governor | Use Case | Latency | Power |
|----------|----------|---------|-------|
| `performance` | Gaming, low-latency | Lowest | Highest |
| `schedutil` | General workloads | Low | Balanced |
| `ondemand` | Legacy/older kernels | Medium | Moderate |
| `powersave` | Battery/thermals | Highest | Lowest |

#### Intel P-State / AMD P-State

For modern Intel/AMD CPUs, the kernel uses `intel_pstate` or `amd_pstate` drivers:

```bash
# Check driver in use
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver

# For AMD: enable amd_pstate=active in kernel params for best performance
# GRUB: add "amd_pstate=active" to GRUB_CMDLINE_LINUX
```

### 2.3 macOS CPU Tuning

Apple Silicon Macs use aggressive power management controlled at the firmware level. Available tuning is limited but effective [6][7]:

**High Power Mode (M3 Max only):**
- System Settings → Battery → High Power Mode
- Best for: 8K video editing, complex renders, sustained compute

**Low Power Mode:**
- Reduces clock speeds but maintains efficiency
- M3 chips show significant efficiency gains in Low Power mode compared to M2 [8]

**Game Mode (Sonoma+):**
- Automatically activates for games
- Reduces background task priority
- Prioritizes GPU and game process

---

## 3. GPU Optimization

### 3.1 NVIDIA GPU Tuning [HIGH]

#### Driver Settings (NVIDIA Control Panel)

| Setting | Recommended Value | Why |
|---------|------------------|-----|
| Power Management Mode | **Prefer Maximum Performance** | Prevents GPU clock throttling |
| Low Latency Mode | **On** or **Ultra** | Reduces input lag in games |
| Threaded Optimization | **Auto** | Let driver decide per-application |
| OpenGL Rendering GPU | **Select your GPU** | Ensures correct GPU usage |
| DSR Factors | **Off** | Performance killer unless needed |
| CUDA - GPUs | **All** | Enable all CUDA cores |

#### CUDA/Compute Workloads [HIGH]

For RTX 4090 ML/AI workloads [9][10]:

```bash
# Recommended stack (Linux)
CUDA: 12.x
cuDNN: 8.9.6+
Driver: 525+

# Persistence mode (keeps GPU initialized)
sudo nvidia-smi -pm 1

# Set compute mode (for dedicated ML systems)
sudo nvidia-smi -c EXCLUSIVE_PROCESS
```

**VRAM Management for ML:**
- RTX 4090 (24GB): Can run 7B models at FP16 inference with room to spare [11]
- Use `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` for better memory fragmentation handling
- Batch size directly impacts VRAM - larger batches improve throughput but consume more memory [12]

### 3.2 AMD GPU Tuning

#### ROCm Setup (Linux) [MEDIUM]

AMD RX 7900 XTX with ROCm 6.x [13][14]:

```bash
# Critical environment variable for RDNA 3
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Install ROCm
sudo apt install rocm-hip-runtime rocm-dev

# Verify installation
rocm-smi --showproductname

# PyTorch with ROCm
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0
```

**Known Issues:**
- Flash Attention support requires PyTorch 2.5.0+ [14]
- Multi-GPU setups may segfault on older llama.cpp versions
- Display may not wake from standby during ML workloads

#### Windows AMD Settings

- Use **AMD Software: Adrenalin Edition**
- Enable **Radeon Anti-Lag** for gaming
- Set **Power Tuning** to maximum for sustained loads

### 3.3 Intel Arc GPU Tuning [MEDIUM]

Intel Arc GPUs use oneAPI for compute workloads [15][16]:

```bash
# Install oneAPI Base Toolkit
sudo apt install intel-oneapi-runtime-dpcpp-cpp intel-oneapi-runtime-mkl

# Compile SYCL code
icx /EHsc /fsycl your_code.cpp

# XMX (Xe Matrix Extensions) for ML
# Use joint_matrix extension in SYCL
```

**For LLM Inference:**
- Most runtimes default to NVIDIA CUDA
- Use IPEX (Intel Extension for PyTorch) or llama.cpp with SYCL backend
- Performance competitive with RTX 4070 in some workloads

---

## 4. Memory Optimization

### 4.1 Windows Memory Tuning

#### Page File Configuration [HIGH]

For 64GB+ RAM systems, the traditional 1.5x-3x rule is obsolete [17]:

```
Recommended: Custom page file
- Initial: 1GB - 8GB
- Maximum: 8GB - 16GB

Path: System Properties → Advanced → Performance Settings →
      Advanced → Virtual Memory → Change
```

**Why keep a page file at all?**
- Windows needs commit charge for proper memory management
- Some applications crash without any page file
- Actual paging to disk is rare with 64GB+ RAM

**ZRAM-style compression:**
Windows 10/11 includes memory compression by default. No configuration needed.

### 4.2 Linux Memory Tuning

#### Swappiness [HIGH]

```bash
# Check current value
cat /proc/sys/vm/swappiness

# Recommended for high-RAM desktop (64GB+)
sudo sysctl vm.swappiness=10

# Persistent in /etc/sysctl.conf
vm.swappiness=10
```

| Workload | Recommended Value |
|----------|------------------|
| Database servers | 1-10 |
| High-RAM desktops | 10 |
| General use | 60 (default) |
| Low-RAM systems | 60-80 |
| ZRAM/zswap systems | 100-180 |

#### Transparent Huge Pages [HIGH]

**Disable for database workloads** (PostgreSQL, MySQL, Redis) [18]:

```bash
# Check current status
cat /sys/kernel/mm/transparent_hugepage/enabled

# Disable temporarily
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

# Permanent via GRUB
GRUB_CMDLINE_LINUX="transparent_hugepage=never"
```

**Exception:** Keep enabled for general desktop/gaming workloads.

#### Other Memory Sysctls

```bash
# For high-RAM workstations
vm.dirty_background_ratio=5
vm.dirty_ratio=10
vm.vfs_cache_pressure=50

# NUMA systems (Threadripper)
# Handled automatically by kernel if BIOS is set correctly
```

### 4.3 NUMA Optimization (Threadripper/EPYC) [MEDIUM]

AMD Threadripper presents NUMA topology that can be configured [19][20]:

**BIOS Settings:**
- **UMA (Default)**: Memory appears unified, variable latency
- **NPS1**: Single NUMA domain (default for 7000 series)
- **NPS2**: Two NUMA domains
- **NPS4**: Four NUMA domains (most granular)

**When to use NPS2/NPS4:**
- NUMA-aware software (databases, HPC)
- Virtualization with pinned VMs
- Memory-bandwidth-sensitive workloads

**Linux NUMA Tools:**
```bash
# View NUMA topology
numactl --hardware

# Pin process to NUMA node
numactl --cpunodebind=0 --membind=0 ./your_app

# OpenMPI NUMA binding
export OMPI_MCA_hwloc_base_binding_policy=numa
```

---

## 5. Storage Optimization

### 5.1 NVMe Tuning [HIGH]

NVMe drives support up to 65k queues with 65k depth each, enabling massive parallelism [21].

#### Linux NVMe Optimization

```bash
# I/O Scheduler (usually automatic for NVMe)
# Options: none, mq-deadline, bfq, kyber
echo none | sudo tee /sys/block/nvme0n1/queue/scheduler

# For maximum throughput on fast NVMe
echo 2 | sudo tee /sys/block/nvme0n1/queue/rq_affinity

# Increase queue depth if needed
echo 1024 | sudo tee /sys/block/nvme0n1/queue/nr_requests
```

**Scheduler Recommendations:**
| Scheduler | Use Case |
|-----------|----------|
| `none` | Fastest NVMe, minimal CPU overhead |
| `mq-deadline` | Good for mixed workloads |
| `bfq` | Desktop responsiveness, CFQ replacement |
| `kyber` | Better random read performance |

#### TRIM Configuration [HIGH]

```bash
# Weekly TRIM (recommended over continuous)
sudo systemctl enable fstrim.timer

# Manual TRIM
sudo fstrim -av

# fstab option (not recommended - causes overhead)
# UUID=xxx /mount ext4 defaults,discard 0 2  # Avoid 'discard'
```

#### Windows NVMe

- TRIM enabled by default
- Use manufacturer's NVMe toolbox for firmware updates
- Disable indexing on NVMe drives (Properties → General → uncheck indexing)

### 5.2 Filesystem Tuning

**Linux ext4:**
```bash
# For SSDs, disable access time updates
# In /etc/fstab: noatime or relatime
UUID=xxx / ext4 defaults,noatime 0 1
```

**Linux BTRFS:**
- Excellent for snapshots and rollback
- Use `compress=zstd:1` for transparent compression
- Enable `discard=async` for background TRIM

---

## 6. Network Optimization

### 6.1 Low-Latency Gaming (Windows) [HIGH]

#### Nagle's Algorithm [HIGH]

Disabling reduces latency for real-time games [22][23]:

```
Registry Path: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip\
               Parameters\Interfaces\{interface-guid}

Create DWORDs:
- TcpAckFrequency = 1
- TCPNoDelay = 1
```

#### Network Throttling Index [HIGH]

```
Path: HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\
      Multimedia\SystemProfile

Set DWORD:
- NetworkThrottlingIndex = 0xffffffff (disabled)
```

#### Other Tweaks

```
Path: HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\
      Multimedia\SystemProfile

- SystemResponsiveness = 0 (or 10)
```

**Note:** Most games use UDP, not TCP. These tweaks have limited effect on UDP-based games [24].

### 6.2 Linux Network Tuning

```bash
# sysctl network optimizations
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.ipv4.tcp_congestion_control=bbr  # Modern congestion control
net.core.netdev_max_backlog=16384
```

---

## 7. Use Case Profiles

### 7.1 Gaming Profile

**Windows:**
```powershell
# Registry tweaks
$mmcsPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
Set-ItemProperty -Path $mmcsPath -Name "SystemResponsiveness" -Value 0
Set-ItemProperty -Path $mmcsPath -Name "NetworkThrottlingIndex" -Value 0xffffffff

# Game priority
$gamesPath = "$mmcsPath\Tasks\Games"
Set-ItemProperty -Path $gamesPath -Name "GPU Priority" -Value 8
Set-ItemProperty -Path $gamesPath -Name "Priority" -Value 6
Set-ItemProperty -Path $gamesPath -Name "Scheduling Category" -Value "High"

# Power plan
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61

# Disable full-screen optimizations per-game if needed
```

**Linux:**
```bash
# CPU governor
sudo cpupower frequency-set -g performance

# Nice priority for game
nice -n -10 ./game

# GPU (NVIDIA)
__GL_THREADED_OPTIMIZATIONS=1 ./game
```

### 7.2 ML/AI Workload Profile

**Critical Settings:**
- NVIDIA: Persistence mode, compute mode, disable display
- AMD: Set `HSA_OVERRIDE_GFX_VERSION`
- Memory: Low swappiness, disable THP for some frameworks
- Storage: NVMe with high queue depth for data loading

**VRAM Optimization:**
```python
# PyTorch memory management
import torch
torch.cuda.empty_cache()

# Gradient checkpointing (saves VRAM)
model.gradient_checkpointing_enable()

# Mixed precision training
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()
with autocast():
    output = model(input)
```

**Batch Size Guidelines:**
| Model Size | FP16 Inference | Training (w/ LoRA) |
|------------|----------------|-------------------|
| 7B | ~15GB VRAM | ~20GB VRAM |
| 13B | ~28GB VRAM | ~40GB VRAM |
| 70B | ~140GB VRAM | Requires multi-GPU |

### 7.3 Content Creation Profile

**Focus Areas:**
- GPU: Maximum performance mode, disable power saving
- CPU: Performance governor, disable core parking
- RAM: Sufficient for project files in memory
- Storage: Fast scratch disk for renders

**Adobe Premiere Pro / DaVinci Resolve:**
- Allocate ~75% of RAM to application
- Use GPU-accelerated effects
- NVMe scratch disk separate from source media

### 7.4 Virtualization Profile (KVM/QEMU)

**Prerequisites [25][26]:**
- CPU: VT-d (Intel) or AMD-Vi enabled
- IOMMU groups properly separated
- Secondary GPU for passthrough

```bash
# Enable IOMMU (GRUB)
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt"
# or
GRUB_CMDLINE_LINUX="amd_iommu=on iommu=pt"

# Verify
dmesg | grep -i iommu
```

**GPU Passthrough Tips:**
- Use `host-passthrough` CPU mode for best performance
- NVIDIA: Add `kvm=off` to CPU flags to bypass detection
- Use `virtio-scsi` for storage, `virtio-net` for networking
- Pin vCPUs to physical cores for consistent performance

### 7.5 Development Profile

**Balanced approach:**
- CPU: `schedutil` governor (responsive without constant max clocks)
- Storage: Fast NVMe for project files and Docker volumes
- RAM: Sufficient for IDE, containers, and test runners
- Swap: Minimal but present for safety

---

## 8. Safety & Rollback

### 8.1 Windows System Restore [HIGH]

```powershell
# Create restore point before optimization
Checkpoint-Computer -Description "Pre-Optimization Baseline" -RestorePointType "MODIFY_SETTINGS"

# Bypass 24-hour limit
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore" `
    -Name "SystemRestorePointCreationFrequency" -Value 0

# Enable on all drives
Enable-ComputerRestore -Drive "C:\", "D:\"

# Verify
Get-ComputerRestorePoint
```

### 8.2 Linux BTRFS Snapshots [HIGH]

```bash
# Manual snapshot
sudo btrfs subvolume snapshot / /.snapshots/pre-optimization

# With Snapper (recommended)
sudo snapper create -d "Pre-optimization baseline" -t pre

# Rollback
sudo snapper rollback <snapshot-number>
```

**Automated with Snapper:**
```bash
# Install
sudo apt install snapper

# Configure for root
sudo snapper -c root create-config /

# Automatic snapshots on package changes (APT hook)
sudo apt install apt-btrfs-snapshot
```

### 8.3 macOS Time Machine

- Ensure Time Machine backup before modifications
- Limited system tuning available on macOS
- Most changes are reversible through System Settings

### 8.4 Rollback Checklist

Before applying optimizations:
1. [ ] Create system restore point (Windows) or BTRFS snapshot (Linux)
2. [ ] Document current settings (export registry, save sysctl values)
3. [ ] Run baseline benchmarks
4. [ ] Test each change individually when possible
5. [ ] Reboot and verify stability before next change

---

## 9. Monitoring & Metrics

### 9.1 Real-Time Monitoring Tools

| Tool | Platform | CPU | GPU | RAM | Notes |
|------|----------|-----|-----|-----|-------|
| `htop` | Linux | Yes | No | Yes | Interactive, colorful |
| `btop` | Linux/macOS | Yes | No | Yes | Modern, graphical bars |
| `nvidia-smi` | All (NVIDIA) | No | Yes | No | Official NVIDIA tool |
| `nvtop` | Linux | No | Yes* | No | htop for GPUs, multi-vendor [27] |
| `nvitop` | Linux/Windows | No | Yes | No | Beautiful NVIDIA monitor [28] |
| `rocm-smi` | Linux (AMD) | No | Yes | No | AMD ROCm systems |
| `glances` | All | Yes | Yes* | Yes | Web dashboard capable |

### 9.2 Benchmarking Tools

**Cross-Platform:**
- **Phoronix Test Suite**: Most comprehensive, 500+ tests [29]
- **Geekbench 6**: Quick CPU/GPU scoring, cross-platform comparable
- **Sysbench**: CPU, memory, disk, database benchmarks

**Linux-Specific:**
- **hyperfine**: Command-line benchmarking with statistical analysis [30]
- **fio**: Flexible I/O tester for storage

**GPU-Specific:**
- **Blender Benchmark**: Real-world GPU render test
- **3DMark** (Windows): Gaming GPU benchmark

### 9.3 Before/After Methodology

```bash
# Example: Linux CPU benchmark
phoronix-test-suite benchmark pts/cpu

# Store results
phoronix-test-suite result-file-to-text <result-id> > baseline.txt

# After optimization
phoronix-test-suite benchmark pts/cpu
phoronix-test-suite result-file-to-text <result-id> > optimized.txt

# Compare
diff baseline.txt optimized.txt
```

---

## 10. Dynamic Scaling Algorithm

The skill should automatically scale optimizations based on detected hardware:

```python
def determine_optimization_level(hw_tier: str, use_case: str) -> dict:
    """
    Returns optimization parameters scaled to hardware tier.
    """
    profiles = {
        "prosumer": {
            "gaming": {
                "cpu_governor": "performance",
                "gpu_power_mode": "maximum",
                "disable_core_parking": True,
                "network_tweaks": "aggressive",
                "swap": "minimal",
            },
            "ml_ai": {
                "cpu_governor": "performance",
                "gpu_compute_mode": "exclusive",
                "gpu_persistence": True,
                "swap": "disabled",
                "thp": "madvise",  # Let apps decide
            },
            "content_creation": {
                "cpu_governor": "performance",
                "gpu_power_mode": "maximum",
                "ram_allocation": 0.75,  # 75% to apps
                "swap": "minimal",
            },
        },
        "enthusiast": {
            # Slightly conservative versions
            "gaming": {
                "cpu_governor": "schedutil",
                "gpu_power_mode": "adaptive",
                "disable_core_parking": False,
                "network_tweaks": "moderate",
                "swap": "small",
            },
            # ... etc
        },
        "consumer": {
            # Conservative, prioritize stability
            "gaming": {
                "cpu_governor": "schedutil",
                "gpu_power_mode": "adaptive",
                "disable_core_parking": False,
                "network_tweaks": "none",
                "swap": "default",
            },
        },
    }

    return profiles.get(hw_tier, profiles["consumer"]).get(
        use_case, profiles[hw_tier]["gaming"]
    )
```

---

## Analysis & Implications

### What Works Best

1. **CPU Power Plans**: Switching from Balanced to Ultimate Performance yields 1-5% gains in latency-sensitive workloads with near-zero downside on modern hardware [1][5]

2. **GPU Power Mode**: "Maximum Performance" prevents clock throttling during sustained loads, essential for ML training and gaming

3. **Network Tweaks**: Disabling Nagle's algorithm and TCP ACK delays provides measurable latency reduction in online games [22]

4. **Storage I/O Scheduler**: Using `none` or `kyber` on fast NVMe drives reduces CPU overhead [21]

5. **NUMA Configuration**: Proper NUMA awareness on Threadripper can yield 20%+ performance in NUMA-optimized workloads [19]

### What Has Limited Impact

1. **Registry "magic" tweaks**: Many circulated registry hacks have placebo effect or apply only to ancient Windows versions

2. **Disabling services**: Modern Windows/Linux manage services well; aggressive disabling causes instability

3. **Overclocking**: Beyond scope of this skill; requires hardware-specific knowledge and carries risk

### Platform Comparison

- **Linux**: Most tunable, best for ML/AI workloads, 20% faster than Windows on high-core-count CPUs [20]
- **Windows**: Best for gaming (driver support), good for content creation
- **macOS**: Limited tuning, but Apple Silicon efficiency is excellent out-of-box

---

## Limitations & Uncertainties

### What This Document Does NOT Cover

- Overclocking (CPU, GPU, RAM)
- Hardware modifications
- BIOS/UEFI tuning beyond IOMMU/power settings
- Application-specific optimizations (game config files, etc.)
- Driver installation procedures

### Unverified Claims

- Some registry tweaks have anecdotal support but lack rigorous benchmarking [LOW]
- ROCm performance parity claims with CUDA are workload-dependent [MEDIUM]

### Source Conflicts

- Page file recommendations vary widely; some advocate complete removal with 64GB+ RAM while others insist on keeping a small one [17]
- Resolved: Keep a small page file (1-8GB) for stability while avoiding the overhead of large files

### Knowledge Gaps

- Intel Arc oneAPI performance in production ML workloads has limited real-world data
- macOS Sequoia-specific optimizations not fully documented yet

### Recency Limitations

- Windows 11 24H2 may introduce new power management changes
- Linux 6.x kernel changes may affect scheduler behavior
- GPU driver updates can significantly change optimal settings

---

## Recommendations

1. **Start with Detection**: Always run hardware detection first to classify the system tier

2. **Create Rollback Point**: Never apply optimizations without a restore point or snapshot

3. **Profile-Based Approach**: Apply use-case-specific profiles rather than generic "speed up" tweaks

4. **Measure Everything**: Run benchmarks before and after to validate improvements

5. **Prioritize High-Impact Changes**:
   - Power plan (Windows) / CPU governor (Linux)
   - GPU power mode
   - Network latency tweaks (gaming)
   - Storage I/O scheduler (NVMe)

6. **Avoid Over-Optimization**: Diminishing returns set in quickly; stability matters more than 1% gains

7. **Platform-Appropriate Tuning**: Linux for ML/AI, Windows for gaming, respect each platform's strengths

---

## Source Appendix

| # | Source | Date | Type | Used For |
|---|--------|------|------|----------|
| 1 | [Overclock.net - Ryzen Custom Power Plans](https://www.overclock.net/threads/ryzen-custom-power-plans-for-windows-10-11-snappy-lowpower-highpower.1776353/) | 2024 | Secondary | Windows power plan issues |
| 2 | [AllThings.how - Enable Ultimate Performance](https://allthings.how/how-to-enable-ultimate-performance-plan-in-windows-11/) | 2024 | Secondary | Ultimate Performance activation |
| 3 | [ComputerCity - AMD Ryzen Balanced vs High Performance](https://computercity.com/hardware/processors/amd-ryzen-balanced-vs-high-performance-power-plans) | 2024 | Secondary | AMD-specific recommendations |
| 4 | [Overclock.net - Intel Custom Power Plans](https://www.overclock.net/threads/intel-custom-power-plans-for-windows.1802309/) | 2024 | Secondary | Intel hybrid architecture |
| 5 | [Arch Wiki - CPU Frequency Scaling](https://wiki.archlinux.org/title/CPU_frequency_scaling) | 2024 | Primary | Linux CPU governors |
| 6 | [Apple Support - Power Modes](https://support.apple.com/en-us/101613) | 2024 | Primary | macOS power modes |
| 7 | [MacRumors - High Power Mode](https://www.macrumors.com/how-to/high-power-mode-macbook-pro/) | 2024 | Secondary | M3 Max High Power Mode |
| 8 | [MacRumors Forums - M3 Max Low Power](https://forums.macrumors.com/threads/m3-max-low-power-mode-is-insane.2412621/) | 2024 | Secondary | M3 efficiency gains |
| 9 | [Phoronix - RTX 4090 Compute Benchmarks](https://www.phoronix.com/review/nvidia-rtx4080-rtx4090-compute) | 2024 | Secondary | RTX 4090 Linux compute |
| 10 | [NVIDIA Developer Forums - RTX 4090 CUDA](https://forums.developer.nvidia.com/t/best-practices-for-using-rtx-4090-with-ubuntu-22-04-cuda-and-yolo-ultralytics/327865) | 2024 | Secondary | CUDA best practices |
| 11 | [Hyperstack - VRAM for LLMs](https://www.hyperstack.cloud/blog/case-study/how-much-vram-do-you-need-for-llms) | 2024 | Secondary | VRAM requirements |
| 12 | [Hydra Host - GPU Memory Impact](https://hydrahost.com/post/understanding-impact-gpu-memory-training-large-language-models/) | 2024 | Secondary | Batch size and VRAM |
| 13 | [Phoronix - ROCm PyTorch 7900 XTX](https://www.phoronix.com/news/RX-7900-XTX-ROCm-PyTorch) | 2024 | Secondary | ROCm support announcement |
| 14 | [ROCm Docs - System Requirements](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html) | 2024 | Primary | ROCm installation |
| 15 | [Intel - oneAPI GPU Optimization Guide](https://www.intel.com/content/www/us/en/docs/oneapi/optimization-guide-gpu/2024-2/overview.html) | 2024 | Primary | Intel Arc optimization |
| 16 | [Towards Data Science - Intel XMX](https://towardsdatascience.com/utilizing-intel-arc-xe-matrix-extensions-xmx-using-oneapi-bd39479c9555/) | 2024 | Secondary | XMX programming |
| 17 | [Tom's Hardware Forums - Virtual Memory](https://forums.tomshardware.com/threads/virtual-memory-only-9216mb-with-64gb-ram-installed.3789803/) | 2024 | Secondary | Page file sizing |
| 18 | [Red Hat Docs - THP Tuning](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/6/html/performance_tuning_guide/s-memory-tunables) | 2024 | Primary | THP configuration |
| 19 | [Phoronix - Threadripper NPS/SNC](https://www.phoronix.com/review/threadripper-zen4-nps-snc-numa) | 2024 | Secondary | NUMA configuration |
| 20 | [Tom's Hardware - Linux vs Windows Threadripper](https://www.tomshardware.com/news/ubuntu-runs-20-faster-than-windows-11-on-amd-threadripper-pro-7995wx) | 2024 | Secondary | Platform comparison |
| 21 | [Perlod - NVMe Optimization](https://perlod.com/tutorials/nvme-optimization-for-linux-servers/) | 2024 | Secondary | NVMe tuning |
| 22 | [SpeedGuide - Gaming Tweaks](https://www.speedguide.net/articles/gaming-tweaks-5812) | 2024 | Secondary | Network latency |
| 23 | [TCPOptimizer - Gaming Tweaks](https://tcpoptimizer.org/gaming-tweaks/) | 2024 | Secondary | TCP optimization |
| 24 | [Blur Busters Forums - TCP Optimizer](https://forums.blurbusters.com/viewtopic.php?t=10294) | 2024 | Secondary | UDP vs TCP in games |
| 25 | [Arch Wiki - PCI Passthrough](https://wiki.archlinux.org/title/PCI_passthrough_via_OVMF) | 2024 | Primary | GPU passthrough |
| 26 | [Mathias Hueber - VM Gaming Tweaks](https://mathiashueber.com/performance-tweaks-gaming-on-virtual-machines/) | 2024 | Secondary | VM optimization |
| 27 | [GitHub - nvtop](https://github.com/Syllo/nvtop) | 2024 | Primary | Multi-vendor GPU monitoring |
| 28 | [GitHub - nvitop](https://github.com/XuehaiPan/nvitop) | 2024 | Primary | NVIDIA monitoring |
| 29 | [Phoronix Test Suite](https://www.phoronix-test-suite.com/) | 2024 | Primary | Benchmarking platform |
| 30 | [GitHub - hyperfine](https://github.com/sharkdp/hyperfine) | 2024 | Primary | CLI benchmarking |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-23 | Initial comprehensive version |

---

## Appendix A: Quick Reference Commands

### Windows PowerShell (Run as Admin)

```powershell
# Create restore point
Checkpoint-Computer -Description "Pre-Opt" -RestorePointType "MODIFY_SETTINGS"

# Enable Ultimate Performance
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61

# Disable Nagle's (find interface GUID first)
Get-NetAdapter | Select-Object Name, InterfaceGuid

# GPU info
nvidia-smi
```

### Linux Bash (Run as root/sudo)

```bash
# BTRFS snapshot
btrfs subvolume snapshot / /.snapshots/pre-opt

# CPU performance mode
cpupower frequency-set -g performance

# Check GPU
nvidia-smi  # or rocm-smi

# NVMe scheduler
echo none > /sys/block/nvme0n1/queue/scheduler

# Apply sysctl
sysctl -p /etc/sysctl.d/99-optimization.conf
```

### macOS (Terminal)

```zsh
# System info
system_profiler SPHardwareDataType SPDisplaysDataType

# Power settings (limited)
pmset -g
```

---

## Appendix B: Hardware Tier Classification

| Tier | CPU | GPU | RAM | Storage |
|------|-----|-----|-----|---------|
| **Pro-sumer** | 16+ cores, Ryzen 9/i9/Threadripper | RTX 4080+, RX 7900 XT+ | 64GB+ | NVMe Gen4+ |
| **Enthusiast** | 8-16 cores, Ryzen 7/i7 | RTX 4070, RX 7800 XT | 32-64GB | NVMe Gen3+ |
| **Consumer** | 4-8 cores, Ryzen 5/i5 | RTX 4060, RX 7600 | 16-32GB | NVMe/SATA SSD |

---

*This document serves as the foundational reference for the System Optimization skill. Implementations should programmatically detect hardware, apply appropriate profiles, and always maintain rollback capability.*

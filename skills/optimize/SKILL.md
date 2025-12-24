---
name: optimize
description: System optimization skill for pro-sumer hardware. Detects CPU (Intel/AMD), GPU (NVIDIA/AMD/Intel Arc), RAM, and storage. Applies platform-specific optimizations (Windows/macOS/Linux) scaled to hardware tier. Supports gaming, ML/AI, content creation, virtualization, and development profiles. Safety-first with rollback capability.
---

# System Optimization Skill v0.1.0

Maximize performance from pro-sumer hardware across Windows, macOS, and Linux.

## Philosophy

> **If someone has beast hardware, use every ounce of it.**

This skill detects available hardware, classifies system tier, applies appropriate optimizations, and provides before/after metrics—all with rollback safety.

## Quick Start

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      OPTIMIZATION WORKFLOW                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. DETECT      →  Scan hardware (CPU, GPU, RAM, Storage)                │
│     └─► Run: Hardware Detection Commands (below)                        │
│                                                                          │
│  2. CLASSIFY    →  Determine tier (Consumer/Enthusiast/Pro-sumer)        │
│     └─► See: Hardware Tier Matrix                                        │
│                                                                          │
│  3. PROFILE     →  Select use case                                       │
│     └─► Gaming | ML/AI | Content | Virtualization | Development          │
│                                                                          │
│  4. BACKUP      →  Create rollback point (MANDATORY)                     │
│     └─► See: Safety & Rollback                                           │
│                                                                          │
│  5. BASELINE    →  Run benchmarks                                        │
│     └─► See: Benchmarking Commands                                       │
│                                                                          │
│  6. OPTIMIZE    →  Apply platform-specific tuning                        │
│     └─► See: references/[platform].md                                    │
│                                                                          │
│  7. VERIFY      →  Re-run benchmarks, compare                            │
│     └─► Document gains before declaring success                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Hardware Detection

### Universal Detection (Python)

```python
#!/usr/bin/env python3
"""Hardware detection script - save as detect_hardware.py"""
import psutil
import platform
import json
import subprocess
from typing import Dict, Any

def detect_hardware() -> Dict[str, Any]:
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

    # Storage detection
    for p in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(p.mountpoint)
            hw["storage"].append({
                "device": p.device,
                "fstype": p.fstype,
                "total_gb": round(u.total / (1024**3), 1),
                "is_nvme": "nvme" in p.device.lower(),
            })
        except: pass

    # NVIDIA GPU detection
    try:
        import GPUtil
        for gpu in GPUtil.getGPUs():
            hw["gpu"].append({
                "vendor": "NVIDIA",
                "name": gpu.name,
                "vram_mb": gpu.memoryTotal,
            })
    except: pass

    return hw

def classify_tier(hw: Dict) -> str:
    cores = hw["cpu"]["logical_cores"]
    ram = hw["memory"]["total_gb"]
    high_gpu = any(g.get("vram_mb", 0) >= 16000 for g in hw["gpu"])

    if cores >= 16 and ram >= 64 and high_gpu:
        return "prosumer"
    elif cores >= 8 and ram >= 32:
        return "enthusiast"
    return "consumer"

if __name__ == "__main__":
    hw = detect_hardware()
    tier = classify_tier(hw)
    print(f"Hardware Tier: {tier.upper()}")
    print(json.dumps(hw, indent=2))
```

### Platform-Specific Detection

**Windows (PowerShell - Run as Admin):**
```powershell
# CPU
Get-WmiObject Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed

# GPU
Get-WmiObject Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion

# RAM
Get-WmiObject Win32_PhysicalMemory | Measure-Object Capacity -Sum | Select-Object @{N='TotalGB';E={$_.Sum/1GB}}

# Storage (NVMe detection)
Get-PhysicalDisk | Select-Object MediaType, BusType, Size, Model | Format-Table

# Full system summary
systeminfo | Select-String "Total Physical Memory|Processor|OS Name"
```

**Linux (Bash):**
```bash
# CPU
echo "=== CPU ===" && lscpu | grep -E "Model name|Socket|Core|Thread|MHz"

# GPU (NVIDIA)
echo "=== GPU (NVIDIA) ===" && nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv 2>/dev/null || echo "No NVIDIA GPU"

# GPU (AMD)
echo "=== GPU (AMD) ===" && rocm-smi --showproductname 2>/dev/null || echo "No AMD ROCm GPU"

# RAM
echo "=== RAM ===" && free -h | head -2

# Storage
echo "=== Storage ===" && lsblk -d -o NAME,SIZE,TYPE,TRAN | grep -E "nvme|ssd|disk"
```

**macOS (zsh):**
```zsh
# System overview
system_profiler SPHardwareDataType | grep -E "Chip|Cores|Memory"

# GPU
system_profiler SPDisplaysDataType | grep -E "Chipset|VRAM|Metal"

# Storage
diskutil list | head -20
```

---

## Step 2: Hardware Tier Classification

| Tier | CPU | GPU | RAM | Storage |
|------|-----|-----|-----|---------|
| **Pro-sumer** | 16+ cores (Ryzen 9/i9/Threadripper) | RTX 4080+, RX 7900 XT+, 16GB+ VRAM | 64GB+ | NVMe Gen4+ |
| **Enthusiast** | 8-16 cores (Ryzen 7/i7) | RTX 4070, RX 7800 XT, 8-16GB VRAM | 32-64GB | NVMe Gen3+ |
| **Consumer** | 4-8 cores (Ryzen 5/i5) | RTX 4060, RX 7600, <8GB VRAM | 16-32GB | NVMe/SATA SSD |

### Tier-Based Optimization Intensity

| Setting | Consumer | Enthusiast | Pro-sumer |
|---------|----------|------------|-----------|
| CPU Governor/Plan | Balanced | Performance | Ultimate/Performance |
| GPU Power Mode | Adaptive | High | Maximum |
| Core Parking | Enabled | Disabled | Disabled |
| Network Tweaks | None | Moderate | Aggressive |
| Swap/Page File | Default | Small | Minimal/Disabled |

---

## Step 3: Use Case Profiles

| Profile | Primary Focus | Secondary | Key Optimizations |
|---------|---------------|-----------|-------------------|
| **Gaming** | Low latency, high FPS | GPU utilization | Disable Nagle, core parking, max GPU power |
| **ML/AI** | GPU compute, throughput | VRAM management | Persistence mode, compute priority, disable THP |
| **Content** | Render speed, timeline | RAM for preview | Max CPU/GPU power, NVMe scratch disk |
| **Virtualization** | VM performance | Passthrough | IOMMU, CPU pinning, VirtIO |
| **Development** | Responsiveness | Build speed | Balanced power, fast storage |

See `references/profiles/` for detailed per-profile commands.

---

## Step 4: Safety & Rollback (MANDATORY)

**NEVER apply optimizations without a rollback point.**

### Windows - System Restore

```powershell
# Enable System Restore (if disabled)
Enable-ComputerRestore -Drive "C:\"

# Create restore point
Checkpoint-Computer -Description "Pre-Optimization $(Get-Date -Format 'yyyy-MM-dd')" -RestorePointType "MODIFY_SETTINGS"

# Bypass 24-hour limit (run once)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore" -Name "SystemRestorePointCreationFrequency" -Value 0

# Verify
Get-ComputerRestorePoint | Select-Object -Last 3
```

### Linux - BTRFS Snapshots (Recommended)

```bash
# Check if BTRFS
mount | grep btrfs

# Create snapshot
sudo btrfs subvolume snapshot / /.snapshots/pre-optimization-$(date +%Y%m%d)

# With Snapper (easier)
sudo snapper create -d "Pre-optimization baseline" -t pre

# Rollback if needed
sudo snapper rollback <snapshot-id>
```

### Linux - Non-BTRFS Systems

```bash
# Export current settings
sudo sysctl -a > ~/sysctl-backup-$(date +%Y%m%d).conf
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor > ~/governor-backup.txt

# Package list (for dependency issues)
dpkg --get-selections > ~/packages-backup.txt  # Debian/Ubuntu
rpm -qa > ~/packages-backup.txt                 # RHEL/Fedora
```

### macOS

- Ensure Time Machine backup is current
- Limited tuning available; changes mostly reversible via System Settings

---

## Step 5: Baseline Benchmarks

Run BEFORE and AFTER optimization. Same tests, same conditions.

### Cross-Platform

```bash
# Phoronix Test Suite (recommended)
phoronix-test-suite benchmark pts/cpu
phoronix-test-suite benchmark pts/memory
phoronix-test-suite benchmark pts/disk

# Geekbench 6 (simple score)
# Download from https://www.geekbench.com/
geekbench6
```

### GPU Benchmarks

```bash
# NVIDIA - Compute
nvidia-smi dmon -d 1 -c 10  # Monitor for 10 seconds

# Blender Benchmark
# Download from https://opendata.blender.org/
./blender-benchmark-launcher

# 3DMark (Windows) - Gaming
# Purchase/run via Steam
```

### Storage

```bash
# Linux - fio
fio --name=seqread --rw=read --bs=1M --size=1G --numjobs=1 --time_based --runtime=30
fio --name=randread --rw=randread --bs=4K --size=1G --numjobs=4 --time_based --runtime=30

# Windows - CrystalDiskMark or AS SSD Benchmark
```

### Quick Latency Check (Gaming)

```bash
# Windows - LatencyMon
# Download from https://www.resplendence.com/latencymon

# Linux
sudo cyclictest -p 99 -t 4 -n -i 1000 -l 10000
```

---

## Step 6: Apply Optimizations

### Quick Reference: High-Impact Changes

| Platform | Optimization | Command/Path | Impact |
|----------|--------------|--------------|--------|
| Windows | Ultimate Performance | `powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61` | CPU latency |
| Windows | Disable Nagle | Registry: `TcpAckFrequency=1, TCPNoDelay=1` | Network latency |
| Windows | MMCSS Gaming | Registry: `SystemResponsiveness=0` | Input lag |
| Linux | Performance Governor | `cpupower frequency-set -g performance` | CPU throughput |
| Linux | NVMe Scheduler | `echo none > /sys/block/nvme0n1/queue/scheduler` | Storage latency |
| Linux | Swappiness | `sysctl vm.swappiness=10` | Memory pressure |
| NVIDIA | Max Performance | NVIDIA Control Panel → Power Management | GPU clocks |
| NVIDIA | Persistence Mode | `nvidia-smi -pm 1` | GPU init latency |

### Platform-Specific Guides

| Platform | Reference |
|----------|-----------|
| Windows 10/11 | `references/windows.md` |
| Linux (Ubuntu/Arch/Fedora) | `references/linux.md` |
| macOS (Intel/Apple Silicon) | `references/macos.md` |

### GPU-Specific Guides

| GPU | Reference |
|-----|-----------|
| NVIDIA (Gaming) | `references/nvidia-gaming.md` |
| NVIDIA (ML/AI) | `references/nvidia-compute.md` |
| AMD (ROCm) | `references/amd-rocm.md` |
| Intel Arc | `references/intel-arc.md` |

### Profile-Specific Guides

| Use Case | Reference |
|----------|-----------|
| Gaming | `references/profiles/gaming.md` |
| ML/AI | `references/profiles/ml-ai.md` |
| Content Creation | `references/profiles/content.md` |
| Virtualization | `references/profiles/virtualization.md` |

---

## Step 7: Verify & Document

### Compare Results

```bash
# Phoronix - Compare two result files
phoronix-test-suite compare-results-to-baseline before after

# Manual comparison
echo "Before: $(cat ~/benchmark-before.txt)"
echo "After: $(cat ~/benchmark-after.txt)"
echo "Improvement: calculate percentage"
```

### What to Document

1. Hardware tier classification
2. Profile selected
3. Optimizations applied (with exact commands)
4. Benchmark results (before/after)
5. Any issues encountered
6. Rollback procedure if needed

---

## Optimization Commands Reference

### Windows PowerShell (Run as Admin)

```powershell
# === POWER ===
# Enable Ultimate Performance
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61

# Expose hidden power options
powercfg -attributes sub_processor perfboostmode -attrib_hide
powercfg -attributes sub_processor 0cc5b647-c1df-4637-891a-dec35c318583 -attrib_hide

# === NETWORK (Gaming) ===
# Find network adapter GUID
Get-NetAdapter | Select-Object Name, InterfaceGuid

# Disable Nagle's Algorithm (per-interface)
$guid = "{YOUR-ADAPTER-GUID}"
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\$guid" -Name "TcpAckFrequency" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\$guid" -Name "TCPNoDelay" -Value 1 -Type DWord

# Disable Network Throttling
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" -Name "NetworkThrottlingIndex" -Value 0xffffffff -Type DWord

# === GAMING PRIORITY ===
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" -Name "SystemResponsiveness" -Value 0 -Type DWord
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" -Name "GPU Priority" -Value 8 -Type DWord
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" -Name "Priority" -Value 6 -Type DWord
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" -Name "Scheduling Category" -Value "High" -Type String

# === PAGE FILE (64GB+ RAM) ===
# Set custom: 1GB initial, 8GB max via System Properties → Advanced → Performance → Virtual Memory
```

### Linux Bash (Run as root/sudo)

```bash
# === CPU ===
# Set performance governor
sudo cpupower frequency-set -g performance

# Verify
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Persistent (systemd)
sudo systemctl enable cpupower
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpupower

# === MEMORY ===
# Low swappiness for high-RAM systems
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.d/99-optimization.conf

# Disable THP (databases, some ML)
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

# === STORAGE ===
# NVMe scheduler (none = lowest overhead)
echo none | sudo tee /sys/block/nvme0n1/queue/scheduler

# I/O affinity
echo 2 | sudo tee /sys/block/nvme0n1/queue/rq_affinity

# TRIM (weekly, not continuous)
sudo systemctl enable fstrim.timer

# === NETWORK ===
cat << 'EOF' | sudo tee /etc/sysctl.d/99-network.conf
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.ipv4.tcp_congestion_control=bbr
net.core.netdev_max_backlog=16384
EOF
sudo sysctl -p /etc/sysctl.d/99-network.conf

# === APPLY ALL ===
sudo sysctl -p /etc/sysctl.d/99-optimization.conf
```

### NVIDIA GPU

```bash
# Persistence mode (keeps GPU initialized)
sudo nvidia-smi -pm 1

# Power limit to max (check your card's limit first)
nvidia-smi -q -d POWER  # Check default/max
sudo nvidia-smi -pl <WATTS>  # Set (e.g., 450 for 4090)

# Compute mode for ML/AI (exclusive process)
sudo nvidia-smi -c EXCLUSIVE_PROCESS

# Reset to default
sudo nvidia-smi -c DEFAULT
sudo nvidia-smi -pm 0
```

### AMD GPU (ROCm/Linux)

```bash
# Required for RX 7900 series
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Add to ~/.bashrc or /etc/environment for persistence
echo 'HSA_OVERRIDE_GFX_VERSION=11.0.0' >> ~/.bashrc

# Check GPU status
rocm-smi

# Power profile
rocm-smi --setperflevel high
```

---

## Monitoring Tools

### Real-Time Monitoring

| Tool | Platform | What It Shows | Install |
|------|----------|---------------|---------|
| `htop` | Linux | CPU, RAM, processes | `apt install htop` |
| `btop` | Linux/macOS | Modern dashboard | `apt install btop` |
| `nvidia-smi` | All (NVIDIA) | GPU metrics | Included with driver |
| `nvtop` | Linux | GPU dashboard (multi-vendor) | `apt install nvtop` |
| `nvitop` | All | Beautiful NVIDIA monitor | `pip install nvitop` |
| `rocm-smi` | Linux | AMD GPU metrics | Included with ROCm |
| `glances` | All | System + optional GPU | `pip install glances` |

### Continuous Monitoring Commands

```bash
# Watch GPU every 1 second
watch -n 1 nvidia-smi

# CPU frequency monitoring
watch -n 1 "cat /proc/cpuinfo | grep MHz"

# Combined system view
btop
# or
glances
```

---

## Troubleshooting

### Optimization Didn't Help

1. **Verify changes applied**: Re-check settings after reboot
2. **Bottleneck elsewhere**: Use monitoring to find actual bottleneck
3. **Workload not CPU/GPU bound**: Storage or network may be limiting
4. **Already optimized**: Diminishing returns on modern systems

### System Unstable After Changes

1. **Boot to safe mode/recovery**
2. **Restore from rollback point** (you did create one, right?)
3. **Revert specific changes**: Undo in reverse order applied
4. **Check logs**: `journalctl -xb` (Linux), Event Viewer (Windows)

### GPU Not Detected

```bash
# NVIDIA
lspci | grep -i nvidia
nvidia-smi  # Should work if driver installed

# AMD
lspci | grep -i amd
rocm-smi

# Reinstall drivers if needed
```

### Performance Regression

- Thermal throttling: Check temps with `sensors` (Linux) or HWiNFO (Windows)
- Driver update broke things: Rollback driver
- Windows update reset settings: Re-apply optimizations

---

## Reference Documents

### Platform Guides
| Document | Purpose |
|----------|---------|
| `references/windows.md` | Windows 10/11 comprehensive tuning |
| `references/linux.md` | Linux kernel, sysctl, scheduler tuning |
| `references/macos.md` | macOS power and performance settings |

### GPU Guides
| Document | Purpose |
|----------|---------|
| `references/nvidia-gaming.md` | NVIDIA settings for gaming |
| `references/nvidia-compute.md` | NVIDIA CUDA/ML optimization |
| `references/amd-rocm.md` | AMD ROCm setup and tuning |
| `references/intel-arc.md` | Intel Arc oneAPI optimization |

### Use Case Profiles
| Document | Purpose |
|----------|---------|
| `references/profiles/gaming.md` | Low-latency gaming setup |
| `references/profiles/ml-ai.md` | Machine learning workload optimization |
| `references/profiles/content.md` | Video editing, 3D rendering |
| `references/profiles/virtualization.md` | KVM/QEMU GPU passthrough |

### Hardware Specific
| Document | Purpose |
|----------|---------|
| `references/threadripper-numa.md` | NUMA optimization for high-core CPUs |
| `references/nvme-tuning.md` | NVMe scheduler and queue tuning |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-12-23 | Initial version - full optimization workflow |

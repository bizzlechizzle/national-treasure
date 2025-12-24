# Linux Optimization Guide

Comprehensive kernel, scheduler, and system tuning for Linux desktops and workstations.

## CPU Governor Configuration

### Check Current Governor

```bash
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# or
cpupower frequency-info
```

### Set Performance Governor

```bash
# Temporary (until reboot)
sudo cpupower frequency-set -g performance

# Or via sysfs
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Persistent Governor (systemd)

```bash
# Install cpupower
sudo apt install linux-cpupower  # Debian/Ubuntu
sudo dnf install kernel-tools    # Fedora

# Configure
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpupower

# Enable service
sudo systemctl enable --now cpupower
```

### Governor Comparison

| Governor | Use Case | Description |
|----------|----------|-------------|
| `performance` | Gaming, low-latency | Max frequency always |
| `schedutil` | General use | Scheduler-driven, modern default |
| `ondemand` | Legacy | Timer-based scaling |
| `powersave` | Battery/thermals | Minimum frequency |
| `conservative` | Laptop battery | Gradual scaling |

### Intel P-State / AMD P-State

```bash
# Check driver
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver

# Intel: intel_pstate, AMD: amd_pstate or amd_pstate_epp

# For AMD Ryzen, enable active mode in GRUB:
# GRUB_CMDLINE_LINUX="amd_pstate=active"
sudo update-grub
```

---

## Memory Tuning

### Swappiness

```bash
# Check current
cat /proc/sys/vm/swappiness

# Set temporarily
sudo sysctl vm.swappiness=10

# Persistent
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.d/99-optimization.conf
```

**Recommended Values:**
| Workload | Value |
|----------|-------|
| Database servers | 1-10 |
| High-RAM desktop (64GB+) | 10 |
| General desktop | 60 (default) |
| ZRAM/zswap | 100-180 |

### Transparent Huge Pages (THP)

**Disable for databases, some ML frameworks:**

```bash
# Check current
cat /sys/kernel/mm/transparent_hugepage/enabled

# Disable temporarily
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

# Persistent via GRUB
# Add to GRUB_CMDLINE_LINUX:
# transparent_hugepage=never
sudo update-grub

# Or via tuned profile
sudo tuned-adm profile latency-performance
```

### Other Memory Settings

```bash
# For high-RAM workstations
cat << 'EOF' | sudo tee /etc/sysctl.d/99-memory.conf
# Reduce dirty page writeback frequency
vm.dirty_background_ratio=5
vm.dirty_ratio=10

# Balance inode/dentry cache vs page cache
vm.vfs_cache_pressure=50

# Larger buffer for network
net.core.rmem_max=16777216
net.core.wmem_max=16777216
EOF

sudo sysctl -p /etc/sysctl.d/99-memory.conf
```

---

## I/O Scheduler (Storage)

### NVMe Drives

Modern NVMe drives work best with minimal scheduling overhead:

```bash
# Check current scheduler
cat /sys/block/nvme0n1/queue/scheduler

# Set to 'none' (lowest overhead)
echo none | sudo tee /sys/block/nvme0n1/queue/scheduler

# Or 'kyber' (better for random reads)
echo kyber | sudo tee /sys/block/nvme0n1/queue/scheduler
```

**Scheduler Options:**
| Scheduler | Best For |
|-----------|----------|
| `none` | Fast NVMe, minimal CPU |
| `mq-deadline` | Mixed workloads |
| `bfq` | Desktop responsiveness |
| `kyber` | Random read performance |

### Persistent Scheduler (udev)

```bash
cat << 'EOF' | sudo tee /etc/udev/rules.d/60-ioscheduler.rules
# NVMe: no scheduler
ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="none"

# SATA SSD: mq-deadline
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="mq-deadline"

# HDD: bfq
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"
EOF

sudo udevadm control --reload-rules
```

### NVMe Advanced Tuning

```bash
# I/O completion affinity (process on submitting CPU)
echo 2 | sudo tee /sys/block/nvme0n1/queue/rq_affinity

# Increase queue depth (if needed)
echo 1024 | sudo tee /sys/block/nvme0n1/queue/nr_requests
```

### TRIM

```bash
# Enable weekly TRIM (recommended over continuous)
sudo systemctl enable --now fstrim.timer

# Manual TRIM
sudo fstrim -av
```

**fstab options:**
```
# Use 'noatime' to reduce writes, avoid 'discard' for continuous TRIM
UUID=xxx / ext4 defaults,noatime 0 1
```

---

## Network Tuning

### TCP/UDP Optimization

```bash
cat << 'EOF' | sudo tee /etc/sysctl.d/99-network.conf
# Increase buffer sizes
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216

# Modern congestion control
net.ipv4.tcp_congestion_control=bbr

# Increase backlog for high-traffic
net.core.netdev_max_backlog=16384
net.core.somaxconn=8192

# Faster TIME_WAIT recycling
net.ipv4.tcp_tw_reuse=1

# Reduce keepalive time
net.ipv4.tcp_keepalive_time=600
EOF

sudo sysctl -p /etc/sysctl.d/99-network.conf
```

### BBR Congestion Control

```bash
# Check available algorithms
sysctl net.ipv4.tcp_available_congestion_control

# Enable BBR
echo 'net.ipv4.tcp_congestion_control=bbr' | sudo tee -a /etc/sysctl.d/99-network.conf
sudo sysctl -p
```

---

## Process Priority

### Nice and Renice

```bash
# Run with high priority (lower nice = higher priority)
nice -n -10 ./game

# Adjust running process
renice -n -5 -p <PID>

# Only root can set negative nice values
```

### I/O Priority (ionice)

```bash
# Best-effort, high priority
ionice -c 2 -n 0 -p <PID>

# Real-time (use carefully)
sudo ionice -c 1 -n 0 -p <PID>
```

### Combine for games

```bash
# High CPU and I/O priority
sudo nice -n -10 ionice -c 2 -n 0 ./game
```

---

## NVIDIA GPU

```bash
# Persistence mode
sudo nvidia-smi -pm 1

# Check power limits
nvidia-smi -q -d POWER

# Set max power (e.g., 450W for 4090)
sudo nvidia-smi -pl 450

# Performance level
nvidia-settings -a '[gpu:0]/GpuPowerMizerMode=1'
```

---

## AMD GPU (ROCm)

```bash
# Required for RX 7900 series
export HSA_OVERRIDE_GFX_VERSION=11.0.0

# Add to ~/.bashrc
echo 'export HSA_OVERRIDE_GFX_VERSION=11.0.0' >> ~/.bashrc

# Set performance level
sudo rocm-smi --setperflevel high

# Monitor
rocm-smi --showuse
```

---

## BTRFS Snapshots (Rollback)

```bash
# Create snapshot before changes
sudo btrfs subvolume snapshot / /.snapshots/pre-opt-$(date +%Y%m%d)

# With Snapper
sudo snapper create -d "Pre-optimization" -t pre

# List snapshots
sudo snapper list

# Rollback
sudo snapper rollback <number>
```

---

## Tuned Profiles

```bash
# Install tuned
sudo apt install tuned  # or dnf install tuned

# List profiles
tuned-adm list

# Recommended profiles:
# - latency-performance: Low latency, disables THP, NUMA balancing
# - throughput-performance: Max throughput
# - desktop: Balanced for desktop

# Apply
sudo tuned-adm profile latency-performance

# Check active
tuned-adm active
```

---

## Kernel Boot Parameters

Add to `GRUB_CMDLINE_LINUX` in `/etc/default/grub`:

```bash
# For gaming/low-latency
mitigations=off          # Disable Spectre/Meltdown mitigations (security trade-off!)
intel_pstate=passive     # Let cpufreq governors work
amd_pstate=active        # Best for modern AMD
transparent_hugepage=never
nohz_full=2-15           # Isolate cores 2-15 from scheduler (advanced)
```

**Warning:** `mitigations=off` improves performance but reduces security. Only use on dedicated gaming/workstation systems not exposed to untrusted code.

```bash
# Apply
sudo update-grub  # Debian/Ubuntu
sudo grub2-mkconfig -o /boot/grub2/grub.cfg  # RHEL/Fedora
```

---

## Verification

```bash
# CPU governor
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u

# Swappiness
cat /proc/sys/vm/swappiness

# THP status
cat /sys/kernel/mm/transparent_hugepage/enabled

# I/O scheduler
cat /sys/block/*/queue/scheduler

# Network
sysctl net.ipv4.tcp_congestion_control

# Applied sysctl
sysctl -a | grep -E "swappiness|dirty_ratio|congestion"
```

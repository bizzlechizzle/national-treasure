# macOS Optimization Guide

Performance tuning for macOS on Intel and Apple Silicon Macs.

## Important Limitations

macOS provides limited system tuning compared to Windows/Linux:
- No low-level CPU governor control (managed by firmware)
- No kernel parameter tuning without SIP disabled
- Apple Silicon manages power extremely efficiently out-of-box

**Focus areas:** Power modes, Metal settings, storage, memory pressure management.

---

## Power Modes (Apple Silicon)

### High Power Mode (M3 Max only)

Available on 14" and 16" MacBook Pro with M3 Max chip.

**Enable via:**
1. System Settings → Battery → Power Mode
2. Select "High Power" when connected to power

**Use cases:**
- 8K ProRes video editing
- Complex 3D rendering
- Sustained heavy compute

### Low Power Mode

**Enable via:**
1. System Settings → Battery → Low Power Mode
2. Options: Always, Only on Battery, Only on Power Adapter

**M3 Low Power Benefits:**
- Significant efficiency gains over M2
- Reduced fan noise
- Extended battery life
- Still surprisingly performant

---

## Game Mode (Sonoma+)

Automatically activates when playing games:
- Prioritizes GPU and game process
- Reduces background task priority
- Optimizes Bluetooth for controllers/AirPods

**To verify:** Look for Game Mode icon in menu bar during gameplay.

---

## Memory Pressure Management

### Check Memory Status

```zsh
# Memory pressure
memory_pressure

# Detailed memory stats
vm_stat

# Activity Monitor alternative
top -l 1 | head -10
```

### Reduce Memory Pressure

1. Close unused applications
2. Reduce browser tabs
3. Restart memory-heavy apps periodically
4. macOS handles swap efficiently, but high pressure = slowdown

### Compressed Memory

macOS uses memory compression automatically. No configuration needed.
Check compression in Activity Monitor → Memory tab.

---

## Storage Optimization

### Check Storage Type

```zsh
system_profiler SPNVMeDataType
# or
diskutil info disk0
```

### TRIM (SSD)

TRIM is enabled by default on Apple SSDs. For third-party SSDs:

```zsh
# Check TRIM status
system_profiler SPSerialATADataType | grep TRIM

# Enable for third-party SSD (use with caution)
sudo trimforce enable
```

### Free Space

macOS performs better with free space available:
- Keep 10-15% free for optimal performance
- Clear caches: `~/Library/Caches/`
- Use "Reduce Clutter" in Storage settings

---

## Metal Performance

### Check Metal Version

```zsh
system_profiler SPDisplaysDataType | grep Metal
```

### Application-Specific GPU Selection (Intel Macs with dGPU)

System Settings → Battery → Options → Automatic graphics switching

- **Enabled:** Save battery, use iGPU when possible
- **Disabled:** Always use dGPU (more performance, less battery)

### GPU Monitoring

```zsh
# Built-in
sudo powermetrics --samplers gpu_power -i 1000

# Activity Monitor → Window → GPU History
```

---

## Development Optimization

### Xcode

```zsh
# Increase file descriptor limits for large builds
sudo launchctl limit maxfiles 65536 200000

# Parallelize builds
defaults write com.apple.dt.Xcode IDEBuildOperationMaxNumberOfConcurrentCompileTasks $(sysctl -n hw.ncpu)
```

### Homebrew

```zsh
# Parallel package builds
export HOMEBREW_MAKE_JOBS=$(sysctl -n hw.ncpu)
```

### Docker (Apple Silicon)

```zsh
# Increase resources in Docker Desktop settings
# Recommended: 50% of RAM, 50% of CPU cores

# Use Rosetta for x86 images (Docker Desktop settings)
# Native ARM images preferred for performance
```

---

## Network Optimization

### DNS

```zsh
# Check current DNS
scutil --dns | grep 'nameserver'

# Set faster DNS (Cloudflare)
sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1

# Flush DNS cache
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```

### Wi-Fi vs Ethernet

Ethernet provides:
- Lower latency
- More consistent speeds
- Less interference

Use USB-C to Ethernet adapter for performance-critical work.

---

## Terminal Performance

### Reduce Shell Startup Time

```zsh
# Profile zsh startup
time zsh -i -c exit

# Lazy-load heavy plugins (nvm, rbenv, etc.)
# Use zinit or similar for deferred loading
```

### iTerm2 Optimizations

Preferences → Profiles → Terminal:
- Unlimited scrollback → Set reasonable limit
- Disable "Log terminal output to file"

---

## Disable Unused Features

### Spotlight Indexing (for specific folders)

System Settings → Siri & Spotlight → Spotlight Privacy → Add folders to exclude

### Time Machine (if not using)

```zsh
# Disable
sudo tmutil disable

# Or exclude specific folders in Time Machine preferences
```

### Gatekeeper (for developers)

```zsh
# Temporarily allow unsigned apps
sudo spctl --master-disable

# Re-enable after installation
sudo spctl --master-enable
```

---

## Monitoring Tools

### Built-in

```zsh
# CPU/GPU power
sudo powermetrics --samplers cpu_power,gpu_power -i 1000

# Memory
memory_pressure

# Network
nettop

# Disk
iostat 1
```

### Activity Monitor

- CPU tab: Usage per process and core
- Memory tab: Pressure, compressed, swap
- Energy tab: App impact on battery
- Network/Disk tabs: I/O per process

### Third-Party

- **iStat Menus:** Menu bar monitoring
- **htop:** `brew install htop`
- **btop:** `brew install btop`

---

## Benchmarking

### Geekbench 6

```zsh
# Download from geekbench.com
./geekbench6
```

### Cinebench

Universal app, tests CPU multi-core rendering.

### Blackmagic Disk Speed Test

Available on App Store. Tests read/write speeds.

### Custom

```zsh
# Simple CPU benchmark
time python3 -c "sum(range(10**8))"

# Disk speed
dd if=/dev/zero of=testfile bs=1g count=1 oflag=direct
rm testfile
```

---

## Apple Silicon ML/AI

### Core ML

Optimized for Apple Neural Engine. Use Core ML models when possible.

```zsh
# Convert PyTorch to Core ML
pip install coremltools
```

### MLX (Apple's ML Framework)

```zsh
pip install mlx

# Native Apple Silicon ML framework
# Unified memory (no CPU→GPU transfer overhead)
```

### PyTorch MPS Backend

```python
import torch

# Use Metal Performance Shaders
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model = model.to(device)
```

---

## Time Machine Backup (Before Changes)

Always ensure Time Machine backup is current before any system changes.

```zsh
# Force backup now
tmutil startbackup

# Check last backup
tmutil latestbackup
```

---

## Limitations Summary

| What You Can't Do | Why |
|-------------------|-----|
| CPU governor control | Managed by Apple firmware |
| Kernel parameter tuning | SIP protected |
| GPU driver tweaks | Unified Metal stack |
| Deep thermal management | Firmware controlled |

**Focus on:** Application settings, power modes, storage health, memory management.

# Gaming Optimization Profile

Low-latency, high FPS configuration for competitive and immersive gaming.

## Goals

- Minimize input lag
- Maximize frame rate
- Reduce network latency
- Consistent frame times

---

## Windows Gaming Optimization

### Power Plan

```powershell
# Enable Ultimate Performance
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61
```

### Registry Tweaks

```powershell
# === NETWORK LATENCY ===
# Get adapter GUID first
Get-NetAdapter | Select-Object Name, InterfaceGuid

# Disable Nagle's Algorithm (replace {GUID})
$guid = "{YOUR-ADAPTER-GUID}"
$path = "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\$guid"
Set-ItemProperty -Path $path -Name "TcpAckFrequency" -Value 1 -Type DWord
Set-ItemProperty -Path $path -Name "TCPNoDelay" -Value 1 -Type DWord

# === SYSTEM RESPONSIVENESS ===
$mmcs = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
Set-ItemProperty -Path $mmcs -Name "NetworkThrottlingIndex" -Value 0xffffffff -Type DWord
Set-ItemProperty -Path $mmcs -Name "SystemResponsiveness" -Value 0 -Type DWord

# === GAME PRIORITY ===
$games = "$mmcs\Tasks\Games"
Set-ItemProperty -Path $games -Name "GPU Priority" -Value 8 -Type DWord
Set-ItemProperty -Path $games -Name "Priority" -Value 6 -Type DWord
Set-ItemProperty -Path $games -Name "Scheduling Category" -Value "High" -Type String
```

### Disable Full-Screen Optimizations

```powershell
# Per-game (Properties → Compatibility → Disable full-screen optimizations)

# Or system-wide
Set-ItemProperty -Path "HKCU:\System\GameConfigStore" -Name "GameDVR_FSEBehaviorMode" -Value 2 -Type DWord
```

### Disable Game Bar/DVR

```powershell
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" -Name "AppCaptureEnabled" -Value 0 -Type DWord
```

### Mouse Optimization

```powershell
# Disable mouse acceleration (enhance pointer precision)
Set-ItemProperty -Path "HKCU:\Control Panel\Mouse" -Name "MouseSpeed" -Value "0"
Set-ItemProperty -Path "HKCU:\Control Panel\Mouse" -Name "MouseThreshold1" -Value "0"
Set-ItemProperty -Path "HKCU:\Control Panel\Mouse" -Name "MouseThreshold2" -Value "0"
```

---

## Linux Gaming Optimization

### CPU Governor

```bash
# Set performance
sudo cpupower frequency-set -g performance

# Persistent
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpupower
sudo systemctl enable cpupower
```

### Game Launcher with Priority

```bash
#!/bin/bash
# gaming-launch.sh

# Set CPU governor
sudo cpupower frequency-set -g performance

# Disable compositor (if using X11)
# xfwm4 --replace --compositor=off &

# Launch game with high priority
nice -n -10 ionice -c 2 -n 0 "$@"
```

### Proton/Wine Games

```bash
# Environment variables for Proton
export WINE_FULLSCREEN_FSR=1        # Enable FSR
export DXVK_ASYNC=1                 # Async shader compilation
export VKD3D_CONFIG=dxr11           # DirectX Raytracing
export RADV_PERFTEST=gpl            # AMD: Graphics Pipeline Library

# GameMode (auto-optimizes when game runs)
gamemoded -s  # Check status
# Games launch automatically with GameMode if installed
```

### GameMode Setup

```bash
# Install
sudo apt install gamemode  # Debian/Ubuntu
sudo dnf install gamemode  # Fedora

# Test
gamemoded -t

# Games automatically detected, or force:
gamemoderun ./game
```

### Disable Compositor

**GNOME (Wayland):** Games auto-disable compositor in fullscreen
**KDE Plasma:** Settings → Display → Compositor → Disable for fullscreen

**X11 (manual):**
```bash
# Disable
xfwm4 --replace --compositor=off

# Re-enable
xfwm4 --replace --compositor=on
```

---

## NVIDIA Gaming Settings

### nvidia-settings

```bash
# Set performance mode
nvidia-settings -a '[gpu:0]/GpuPowerMizerMode=1'

# Force full composition pipeline (reduces tearing)
nvidia-settings --assign CurrentMetaMode="nvidia-auto-select +0+0 { ForceFullCompositionPipeline = On }"
```

### Environment Variables

```bash
# Maximum performance
__GL_THREADED_OPTIMIZATIONS=1
__GL_YIELD="NOTHING"
__GL_MaxFramesAllowed=1

# Launch game
__GL_THREADED_OPTIMIZATIONS=1 ./game
```

### NVIDIA Control Panel (Windows)

| Setting | Value |
|---------|-------|
| Power Management Mode | Prefer Maximum Performance |
| Low Latency Mode | Ultra |
| Vertical Sync | Off (use in-game) |
| Threaded Optimization | Auto |
| Max Frame Rate | Slightly below monitor refresh |

---

## AMD Gaming Settings (Linux)

```bash
# Performance mode
echo high | sudo tee /sys/class/drm/card0/device/power_dpm_force_performance_level

# Or via corectrl for GUI management
sudo apt install corectrl
```

### Environment Variables

```bash
# Enable Vulkan async compute
RADV_PERFTEST=aco,gpl

# Launch
RADV_PERFTEST=aco ./game
```

---

## Network Optimization

### Router/Modem
- Use wired Ethernet (not WiFi)
- Enable QoS, prioritize gaming traffic
- Disable WiFi if not needed (reduces interference)

### Windows
- Disable Windows Auto-Tuning for games with issues:
```powershell
netsh interface tcp set global autotuninglevel=disabled
```

### DNS
- Use low-latency DNS: Cloudflare (1.1.1.1), Google (8.8.8.8)

---

## Monitor Settings

- Enable highest refresh rate in Display Settings
- Use native resolution
- Disable VSync in-game (use G-Sync/FreeSync instead)
- Set monitor to Gaming/Low-latency mode

---

## Game-Specific Tips

### Competitive FPS (CS2, Valorant)
- Lock FPS slightly above monitor refresh
- Lowest graphics settings for maximum FPS
- Disable all overlays (Discord, Steam)
- Full-screen exclusive mode

### Open World (Cyberpunk, Starfield)
- GPU-bound: enable FSR/DLSS for FPS
- Frame generation if available
- Higher settings acceptable

### Emulators (Ryujinx, Yuzu, RPCS3)
- CPU-bound: max single-thread performance
- Async shader compilation
- Vulkan backend preferred

---

## Troubleshooting

### Stuttering
- Shader compilation: let game compile in menus
- DXVK: set `DXVK_ASYNC=1`
- Check storage (NVMe should be fine)

### High Input Lag
- Check refresh rate is correct
- Disable VSync, use G-Sync/FreeSync
- Check display mode (fullscreen exclusive)
- Verify Low Latency Mode enabled

### Inconsistent Frame Times
- Set FPS cap slightly below max
- Check thermals (GPU/CPU throttling)
- Disable background apps

### Network Lag
- Check with `ping` to game server
- Wired > WiFi
- Close bandwidth-heavy apps
- Check router QoS

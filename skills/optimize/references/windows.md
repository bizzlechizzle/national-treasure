# Windows 10/11 Optimization Guide

Comprehensive tuning for Windows systems with pro-sumer hardware.

## Power Plan Configuration

### Enable Ultimate Performance

```powershell
# Duplicate and activate Ultimate Performance plan
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61

# Verify active plan
powercfg -getactivescheme
```

### Expose Hidden Power Options

```powershell
# CPU boost mode
powercfg -attributes sub_processor perfboostmode -attrib_hide

# Core parking
powercfg -attributes sub_processor 0cc5b647-c1df-4637-891a-dec35c318583 -attrib_hide

# Processor performance increase threshold
powercfg -attributes sub_processor 06cadf0e-64ed-448a-8927-ce7bf90eb35d -attrib_hide
```

### AMD Ryzen-Specific

- Ryzen 5000+: Windows Balanced is acceptable, Ultimate for maximum performance
- Install AMD Chipset drivers for CPPC2 support
- Ryzen Master for per-CCX tuning (advanced)

### Intel-Specific (12th-14th Gen)

- Standard Windows plans suboptimal for P-core/E-core hybrid
- Use custom power plans or Intel XTU
- Consider disabling E-cores for single-threaded workloads

---

## Registry Optimizations

### Network Latency (Gaming)

```powershell
# Get network adapter GUID
Get-NetAdapter | Select-Object Name, InterfaceGuid

# Replace {GUID} with your adapter's GUID
$guid = "{YOUR-GUID-HERE}"
$path = "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\$guid"

# Disable Nagle's Algorithm
Set-ItemProperty -Path $path -Name "TcpAckFrequency" -Value 1 -Type DWord
Set-ItemProperty -Path $path -Name "TCPNoDelay" -Value 1 -Type DWord
```

### Disable Network Throttling

```powershell
$mmcsPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"

# Remove network throttling
Set-ItemProperty -Path $mmcsPath -Name "NetworkThrottlingIndex" -Value 0xffffffff -Type DWord

# Reduce system responsiveness reserve (0 = no reserve for background)
Set-ItemProperty -Path $mmcsPath -Name "SystemResponsiveness" -Value 0 -Type DWord
```

### Gaming Priority (MMCSS)

```powershell
$gamesPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"

# Elevate game priority
Set-ItemProperty -Path $gamesPath -Name "GPU Priority" -Value 8 -Type DWord
Set-ItemProperty -Path $gamesPath -Name "Priority" -Value 6 -Type DWord
Set-ItemProperty -Path $gamesPath -Name "Scheduling Category" -Value "High" -Type String
```

### Disable Core Parking

```
Registry Path:
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\
  54533251-82be-4824-96c1-47b60b740d00\0cc5b647-c1df-4637-891a-dec35c318583

Set DWORD "Attributes" to 0
Then configure via Power Options → Processor power management
```

### Disable Power Throttling

```powershell
$powerPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling"

# Create key if needed
if (-not (Test-Path $powerPath)) {
    New-Item -Path $powerPath -Force
}

Set-ItemProperty -Path $powerPath -Name "PowerThrottlingOff" -Value 1 -Type DWord
```

---

## Page File (Virtual Memory)

### For 64GB+ RAM Systems

**Recommended Settings:**
- Initial: 1GB - 4GB
- Maximum: 8GB - 16GB

**Why keep a page file:**
- Windows commit charge management
- Some applications crash without it
- Actual disk paging rare with high RAM

**Configuration:**
1. System Properties → Advanced → Performance → Settings
2. Advanced tab → Virtual Memory → Change
3. Uncheck "Automatically manage"
4. Select drive, choose "Custom size"
5. Set initial and maximum values
6. Click Set, then OK

**PowerShell Alternative:**
```powershell
# View current page file
Get-WmiObject Win32_PageFileSetting

# Note: Programmatic page file changes require WMI and reboot
```

---

## Disable Full-Screen Optimizations

For games with input lag issues:

```powershell
# Per-game: Right-click .exe → Properties → Compatibility →
# Check "Disable full-screen optimizations"

# System-wide (registry)
Set-ItemProperty -Path "HKCU:\System\GameConfigStore" -Name "GameDVR_FSEBehaviorMode" -Value 2 -Type DWord
Set-ItemProperty -Path "HKCU:\System\GameConfigStore" -Name "GameDVR_HonorUserFSEBehaviorMode" -Value 1 -Type DWord
```

---

## Game Bar / Game DVR

Disable if not using Xbox features:

```powershell
# Disable Game DVR
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" -Name "AppCaptureEnabled" -Value 0 -Type DWord
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\GameDVR" -Name "AllowGameDVR" -Value 0 -Type DWord

# Via Settings: Gaming → Captures → Background recording → Off
```

---

## NVIDIA Control Panel Settings

| Setting | Gaming | Compute |
|---------|--------|---------|
| Power Management Mode | Prefer Maximum Performance | Prefer Maximum Performance |
| Low Latency Mode | On/Ultra | Off |
| Threaded Optimization | Auto | On |
| Texture Filtering - Quality | Performance/High Performance | Quality |
| Vertical Sync | Off (use in-game) | Off |
| CUDA - GPUs | All | All |

---

## Services to Consider Disabling

**Safe to disable (for most users):**
- SysMain (Superfetch) - Marginal benefit on NVMe
- Windows Search - If not using Windows Search heavily
- Connected User Experiences - Telemetry

**Caution:**
- Disable via `services.msc`, not third-party tools
- Document what you disable
- Some games/apps may require certain services

```powershell
# Example: Stop and disable SysMain
Stop-Service -Name "SysMain" -Force
Set-Service -Name "SysMain" -StartupType Disabled
```

---

## System Restore Point

```powershell
# Create before any optimization
Checkpoint-Computer -Description "Pre-Optimization" -RestorePointType "MODIFY_SETTINGS"

# Bypass 24-hour limit
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore" -Name "SystemRestorePointCreationFrequency" -Value 0

# Verify
Get-ComputerRestorePoint | Select-Object -Last 5
```

---

## Verification Commands

```powershell
# Check power plan
powercfg -getactivescheme

# Check registry values
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"

# Check network adapter settings
Get-NetAdapterAdvancedProperty -Name "Ethernet" | Where-Object {$_.DisplayName -like "*offload*" -or $_.DisplayName -like "*checksum*"}

# Check page file
Get-WmiObject Win32_PageFileSetting | Select-Object Name, InitialSize, MaximumSize
```

---

## Rollback

```powershell
# Restore from System Restore point
rstrui.exe

# Or via PowerShell
Get-ComputerRestorePoint
Restore-Computer -RestorePoint <SequenceNumber>
```

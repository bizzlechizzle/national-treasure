# Virtualization Optimization Profile

GPU passthrough and VM performance for KVM/QEMU workstations.

## Goals

- Near-native GPU performance in VMs
- Efficient CPU/memory allocation
- Stable PCIe passthrough
- Host/guest resource isolation

---

## Prerequisites

### Hardware Requirements

| Component | Requirement |
|-----------|-------------|
| CPU | Intel VT-d or AMD-Vi support |
| Motherboard | IOMMU support in BIOS |
| GPUs | Separate GPU for host and guest |
| RAM | 16GB+ (recommended 32GB+) |
| Storage | NVMe for VM storage |

### Check Virtualization Support

```bash
# Intel VT-x / AMD-V
grep -E "vmx|svm" /proc/cpuinfo

# IOMMU support
dmesg | grep -i iommu
```

---

## IOMMU Setup

### Enable in BIOS

- Intel: Enable VT-d
- AMD: Enable AMD-Vi / IOMMU

### Kernel Parameters

```bash
# Edit /etc/default/grub
# Intel:
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt"

# AMD:
GRUB_CMDLINE_LINUX="amd_iommu=on iommu=pt"

# Apply
sudo update-grub  # Debian/Ubuntu
sudo grub2-mkconfig -o /boot/grub2/grub.cfg  # RHEL/Fedora

# Reboot and verify
dmesg | grep -i iommu
```

### Check IOMMU Groups

```bash
#!/bin/bash
# List IOMMU groups
for d in /sys/kernel/iommu_groups/*/devices/*; do
    n=$(basename $(dirname $(dirname $d)))
    echo "IOMMU Group $n: $(lspci -nns ${d##*/})"
done
```

**Ideal:** GPU in its own IOMMU group. If grouped with other devices, may need ACS override patch.

---

## Required Packages

### Debian/Ubuntu

```bash
sudo apt install qemu-system-x86 libvirt-daemon-system \
    virt-manager ovmf bridge-utils
```

### Fedora/RHEL

```bash
sudo dnf install @virtualization
sudo systemctl enable --now libvirtd
```

---

## GPU Passthrough Setup

### Identify GPU

```bash
lspci -nn | grep -E "VGA|Audio"
# Example output:
# 01:00.0 VGA compatible controller [0300]: NVIDIA Corporation [10de:2684]
# 01:00.1 Audio device [0403]: NVIDIA Corporation [10de:22ba]
```

### Bind GPU to VFIO

```bash
# /etc/modprobe.d/vfio.conf
options vfio-pci ids=10de:2684,10de:22ba  # Replace with your GPU IDs

# /etc/modules-load.d/vfio.conf
vfio-pci
vfio
vfio_iommu_type1
vfio_virqfd

# Blacklist nvidia driver (if passing NVIDIA GPU)
# /etc/modprobe.d/blacklist.conf
blacklist nouveau
blacklist nvidia

# Regenerate initramfs
sudo update-initramfs -u  # Debian/Ubuntu
sudo dracut -f            # Fedora/RHEL

# Reboot
```

### Verify VFIO Binding

```bash
lspci -nnk -s 01:00
# Should show: Kernel driver in use: vfio-pci
```

---

## VM Configuration (virt-manager)

### CPU

1. Copy host CPU configuration:
   - CPU → Configuration → Copy host CPU configuration
   - Or manually select "host-passthrough"

2. Topology (for NUMA-aware):
   ```xml
   <cpu mode='host-passthrough'>
     <topology sockets='1' dies='1' cores='8' threads='2'/>
   </cpu>
   ```

### Memory

```xml
<memory unit='GiB'>16</memory>
<currentMemory unit='GiB'>16</currentMemory>
<memoryBacking>
  <hugepages/>
</memoryBacking>
```

### GPU Passthrough

1. Add Hardware → PCI Host Device
2. Select GPU (both VGA and Audio devices)
3. Enable ROM BAR if available

### NVIDIA-Specific Fixes

```xml
<!-- Hide KVM from NVIDIA driver -->
<features>
  <kvm>
    <hidden state='on'/>
  </kvm>
</features>

<!-- Or in CPU section -->
<cpu mode='host-passthrough'>
  <feature policy='disable' name='hypervisor'/>
</cpu>
```

### Machine Type

Use Q35 chipset with OVMF (UEFI):

```xml
<os>
  <type arch='x86_64' machine='pc-q35-8.0'>hvm</type>
  <loader readonly='yes' type='pflash'>/usr/share/OVMF/OVMF_CODE.fd</loader>
  <nvram>/var/lib/libvirt/qemu/nvram/win11_VARS.fd</nvram>
</os>
```

---

## CPU Pinning

### Why Pin?

- Prevents vCPU migration between physical cores
- Reduces latency
- Better cache utilization

### Pin Configuration

```xml
<vcpu placement='static'>16</vcpu>
<cputune>
  <vcpupin vcpu='0' cpuset='8'/>
  <vcpupin vcpu='1' cpuset='9'/>
  <vcpupin vcpu='2' cpuset='10'/>
  <vcpupin vcpu='3' cpuset='11'/>
  <!-- ... continue for all vCPUs -->
  <emulatorpin cpuset='0-1'/>
</cputune>
```

### NUMA-Aware Pinning

For Threadripper/EPYC, pin to same NUMA node:

```bash
# Check NUMA topology
numactl --hardware

# Pin VM to NUMA node 0
<numatune>
  <memory mode='strict' nodeset='0'/>
</numatune>
```

---

## Storage Optimization

### VirtIO (Recommended)

```xml
<disk type='file' device='disk'>
  <driver name='qemu' type='qcow2' cache='none' io='native' discard='unmap'/>
  <source file='/var/lib/libvirt/images/vm.qcow2'/>
  <target dev='vda' bus='virtio'/>
</disk>
```

### Passthrough Physical Disk

```xml
<disk type='block' device='disk'>
  <driver name='qemu' type='raw' cache='none' io='native'/>
  <source dev='/dev/nvme1n1'/>
  <target dev='vdb' bus='virtio'/>
</disk>
```

### Windows VirtIO Drivers

Download from: https://fedorapeople.org/groups/virt/virtio-win/

---

## Network Optimization

### VirtIO Network

```xml
<interface type='network'>
  <source network='default'/>
  <model type='virtio'/>
</interface>
```

### Macvtap (Direct Host Network)

```xml
<interface type='direct'>
  <source dev='enp4s0' mode='bridge'/>
  <model type='virtio'/>
</interface>
```

---

## Looking Glass (Display Without Monitor)

For GPU passthrough without second monitor:

```bash
# Host: Install Looking Glass
git clone https://github.com/gnif/LookingGlass
cd LookingGlass
mkdir build && cd build
cmake ../client
make

# Create shared memory
sudo touch /dev/shm/looking-glass
sudo chown $USER:kvm /dev/shm/looking-glass
chmod 660 /dev/shm/looking-glass
```

VM XML:

```xml
<shmem name='looking-glass'>
  <model type='ivshmem-plain'/>
  <size unit='M'>32</size>
</shmem>
```

Guest: Install Looking Glass Host application.

---

## Performance Checklist

- [ ] IOMMU enabled and verified
- [ ] GPU bound to VFIO
- [ ] CPU pinning configured
- [ ] Hugepages enabled
- [ ] VirtIO drivers installed
- [ ] `host-passthrough` CPU mode
- [ ] KVM hidden from NVIDIA (if applicable)
- [ ] Storage cache=none, io=native

---

## Troubleshooting

### GPU Not Available for Passthrough

```bash
# Check IOMMU groups
# Ensure GPU not in same group as other devices

# Check VFIO binding
lspci -nnk -s 01:00
```

### NVIDIA Code 43

- Enable KVM hidden state
- Use Q35 machine type
- Update NVIDIA drivers in guest

### Poor Performance

- Verify CPU pinning
- Check memory is not shared
- Ensure storage uses VirtIO + io=native
- Verify hugepages enabled

### Audio Crackling

- Use pulseaudio/pipewire passthrough
- Or pass USB audio device directly

---

## Resources

- [Arch Wiki: PCI Passthrough](https://wiki.archlinux.org/title/PCI_passthrough_via_OVMF)
- [GPU Passthrough Tutorial](https://github.com/bryansteiner/gpu-passthrough-tutorial)
- [Looking Glass](https://looking-glass.io/)

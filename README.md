# Run any VM anywhere [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)

anyvm is a single-file helper for bootstrapping BSD and Illumos guests with QEMU on Linux, macOS, and Windows. It downloads cloud images, sets up firmware, and starts the VM with sane defaults so you can focus on the guest.

## Quick launch

- [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/anyvm-org/anyvm)
  
  Enable KVM in Codespaces before running:

  ```bash
  sudo chmod o+rw /dev/kvm
  ```

- Google Cloud Shell:

<a href="https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2Fanyvm-org%2Fanyvm&cloudshell_tutorial=.cloudshell%2Ftutorial.md&show=terminal&ephemeral=true&cloudshell_print=.cloudshell%2Fconsole.md" target="_blank" rel="noopener noreferrer">
  <img src="https://gstatic.com/cloudssh/images/open-btn.svg" alt="Try it Now in Cloud Shell">
</a>


## Quick start (local)

```bash
python anyvm.py --os freebsd
python anyvm.py --os freebsd --release 14.3
python anyvm.py --os freebsd --release 14.3 --arch aarch64
python anyvm.py --os openbsd --release 7.5 --arch aarch64
python anyvm.py --os solaris

python anyvm.py --os freebsd --release 14.3 --arch riscv64


```

## Guest build matrix (CI)

| Guest | Workflow | x86_64 | aarch64 (arm64) | riscv64 |
|-------|----------|--------|-----------------|---------|
| FreeBSD | [![Test FreeBSD](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml) | Yes | Yes | Yes |
| OpenBSD | [![Test OpenBSD](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml) | Yes | Yes | Yes |
| NetBSD | [![Test NetBSD](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml) | Yes | Yes | No |
| DragonFlyBSD | [![Test DragonflyBSD](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml) | Yes | No | No |
| Solaris | [![Test Solaris](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml) | Yes | No | No |
| OmniOS | [![Test OmniOS](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml) | Yes | No | No |
| OpenIndiana | [![Test OpenIndiana](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml) | Yes | No | No |

## Host support

| Host | x86_64 guests | aarch64 guests | riscv64 guests |
|------|---------------|----------------|----------------|
| x86_64 Linux | Yes | Yes | Yes |
| aarch64 (arm64) Linux | No | Yes | No |
| Apple silicon macOS | Yes | Yes | No |
| Windows x86_64 | Yes | No | No |

## Install dependencies

### Linux (apt-based)

```bash
sudo apt-get --no-install-recommends -y install \
  zstd ovmf xz-utils qemu-utils ca-certificates \
  qemu-system-x86 qemu-system-arm qemu-efi-aarch64 \
  qemu-efi-riscv64 qemu-system-riscv64 u-boot-qemu \
  ssh-client
```

### macOS

```bash
brew install qemu
```

### Windows

- Download QEMU for Windows: https://www.qemu.org/download/#windows or https://qemu.weilnetz.de/w64/
- Or install with MSYS2 pacman:

```bash
pacman.exe -S --noconfirm mingw-w64-ucrt-x86_64-qemu
```

- Or install with Chocolatey:

```bash
choco install qemu
```

## Notes

- Hardware virtualization (KVM, HVF, or Hyper-V) is applied automatically when available for best performance.
- Click the quick launch buttons above to start in a ready-to-use cloud environment.



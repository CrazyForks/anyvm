# Run any VM anywhere [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)

anyvm is a single-file tool for bootstrapping BSD and Illumos guests with QEMU on Linux, macOS, and Windows. It downloads cloud images, sets up firmware, and starts the VM with sane defaults so you can focus on the guest.

## 1. Quick launch

- Github CodeSpace:
  
  [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/anyvm-org/anyvm)
  
  Enable KVM in Codespaces before running:

  ```bash
  sudo chmod o+rw /dev/kvm
  ```

- Google Cloud Shell:

  <a href="https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2Fanyvm-org%2Fanyvm&cloudshell_tutorial=.cloudshell%2Ftutorial.md&show=terminal&ephemeral=true&cloudshell_print=.cloudshell%2Fconsole.md" target="_blank" rel="noopener noreferrer">
  <img src="https://gstatic.com/cloudssh/images/open-btn.svg" alt="Try it Now in Cloud Shell">
</a>


## 2. Quick start (local)

```bash
python anyvm.py --os freebsd
python anyvm.py --os freebsd --release 14.3
python anyvm.py --os freebsd --release 14.3 --arch aarch64
python anyvm.py --os openbsd --release 7.5 --arch aarch64
python anyvm.py --os solaris

python anyvm.py --os freebsd --release 14.3 --arch riscv64

# Run a command inside the VM (everything after `--` is sent to the VM via ssh):
python anyvm.py --os freebsd -- uname -a


```

## 3. Run in a Docker container

Prefer containers? Use the Dockerized wrapper.

```bash
docker run --rm -it ghcr.io/anyvm-org/anyvm:latest --os freebsd
```

More examples and tags: https://github.com/anyvm-org/docker

## 4. Guest build matrix (CI)

| Guest | Workflow | x86_64 | aarch64 (arm64) | riscv64 |
|-------|----------|--------|-----------------|---------|
| FreeBSD | [![Test FreeBSD](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml) | ✅ | ✅ | ✅ |
| OpenBSD | [![Test OpenBSD](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml) | ✅ | ✅ | ✅ |
| NetBSD | [![Test NetBSD](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml) | ✅ | ✅ | ❌ |
| DragonFlyBSD | [![Test DragonflyBSD](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml) | ✅ | ❌ | ❌ |
| Solaris | [![Test Solaris](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml) | ✅ | ❌ | ❌ |
| OmniOS | [![Test OmniOS](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml) | ✅ | ❌ | ❌ |
| OpenIndiana | [![Test OpenIndiana](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml) | ✅ | ❌ | ❌ |

## 5. Host support

| Host | x86_64 guests | aarch64 guests | riscv64 guests |
|------|---------------|----------------|----------------|
| x86_64 Linux | ✅ | ✅ | ✅ |
| aarch64 (arm64) Linux | ❌ | ✅ | ❌ |
| Apple silicon macOS | ✅ | ✅ | ❌ |
| Windows x86_64 | ✅ | ❌ | ❌ |

## 6. Install dependencies

### 6.1 Linux (apt-based) [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)

```bash
sudo apt-get --no-install-recommends -y install \
  zstd ovmf xz-utils qemu-utils ca-certificates \
  qemu-system-x86 qemu-system-arm qemu-efi-aarch64 \
  qemu-efi-riscv64 qemu-system-riscv64 u-boot-qemu \
  ssh-client
```

### 6.2 macOS [![MacOS](https://github.com/anyvm-org/anyvm/actions/workflows/testmacos.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/testmacos.yml)

```bash
brew install qemu
```

### 6.3 Windows [![Windows](https://github.com/anyvm-org/anyvm/actions/workflows/testwindows.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/testwindows.yml)

- Download QEMU for Windows: https://www.qemu.org/download/#windows or https://qemu.weilnetz.de/w64/
- Or install with MSYS2 pacman:

```bash
pacman.exe -S --noconfirm mingw-w64-ucrt-x86_64-qemu
```

- Or install with Chocolatey:

```bash
choco install qemu
```

## 7. Notes

- Hardware virtualization (KVM, HVF, or Hyper-V) is applied automatically when available for best performance.
- Click the quick launch buttons above to start in a ready-to-use cloud environment.








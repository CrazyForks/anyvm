# Run any VM anywhere [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)

anyvm is a single-file tool for bootstrapping BSD and Illumos guests with QEMU on Linux, macOS, and Windows. It downloads cloud images, sets up firmware, and starts the VM with sane defaults so you can focus on the guest.

## 1. Quick launch

- Github CodeSpace:
  
  [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/anyvm-org/anyvm)
  
  Enable KVM in Codespaces before running:

  ```bash
  sudo chmod o+rw /dev/kvm
  
  sudo apt-get --no-install-recommends -y install \
  zstd ovmf xz-utils qemu-utils ca-certificates \
  qemu-system-x86 qemu-system-arm qemu-efi-aarch64 \
  qemu-efi-riscv64 qemu-system-riscv64 qemu-system-misc u-boot-qemu \
  openssh-client
  
  ```

- Google Cloud Shell:

  <a href="https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2Fanyvm-org%2Fanyvm&cloudshell_tutorial=.cloudshell%2Ftutorial.md&show=terminal&ephemeral=true&cloudshell_print=.cloudshell%2Fconsole.md" target="_blank" rel="noopener noreferrer">
  <img src="https://gstatic.com/cloudssh/images/open-btn.svg" alt="Try it Now in Cloud Shell">
</a>


## 2. Quick start (local)

```bash
python3 anyvm.py --os freebsd
python3 anyvm.py --os freebsd --release 14.3
python3 anyvm.py --os freebsd --release 14.3 --arch aarch64
python3 anyvm.py --os openbsd --release 7.5 --arch aarch64
python3 anyvm.py --os solaris

python3 anyvm.py --os freebsd --release 14.3 --arch riscv64

# Run a command inside the VM (everything after `--` is sent to the VM via ssh):
python3 anyvm.py --os freebsd -- uname -a
```

## 3. Run in a Docker container

Prefer containers? Use the Dockerized wrapper.

```bash
docker run --rm -it ghcr.io/anyvm-org/anyvm:latest --os freebsd
```

More examples and tags: https://github.com/anyvm-org/docker

## 4. Guest build matrix (CI)

| Guest | Workflow | x86_64 | aarch64 (arm64) | riscv64 | Builder |
|-------|----------|--------|-----------------|---------|---------|
| FreeBSD | [![Test FreeBSD](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml) | ✅ | ✅ | ✅ | [Builder](https://github.com/anyvm-org/freebsd-builder) |
| OpenBSD | [![Test OpenBSD](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml) | ✅ | ✅ | ✅ | [Builder](https://github.com/anyvm-org/openbsd-builder) |
| NetBSD | [![Test NetBSD](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml) | ✅ | ✅ | ❌ | [Builder](https://github.com/anyvm-org/netbsd-builder) |
| DragonFlyBSD | [![Test DragonflyBSD](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml) | ✅ | ❌ | ❌ | [Builder](https://github.com/anyvm-org/dragonflybsd-builder) |
| Solaris | [![Test Solaris](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml) | ✅ | ❌ | ❌ | [Builder](https://github.com/anyvm-org/solaris-builder) |
| OmniOS | [![Test OmniOS](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml) | ✅ | ❌ | ❌ | [Builder](https://github.com/anyvm-org/omnios-builder) |
| OpenIndiana | [![Test OpenIndiana](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml) | ✅ | ❌ | ❌ | [Builder](https://github.com/anyvm-org/openindiana-builder) |
| Haiku | [![Test Haiku](https://github.com/anyvm-org/anyvm/actions/workflows/haiku.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/haiku.yml) | ✅ | ❌ | ❌ | [Builder](https://github.com/anyvm-org/haiku-builder) |

## 5. Host support

| Host | x86_64 guests | aarch64 guests | riscv64 guests |
|------|---------------|----------------|----------------|
| Linux x86_64 | ✅ | ✅ | ✅ |
| Linux aarch64 (arm64)  | ❌ | ✅ | ❌ |
| MacOS Apple silicon  | ✅ | ✅ | ❌ |
| Windows x86_64 Native | ✅ | ❌ | ❌ |
| Windows x86_64 WSL | ✅ | ✅ | ✅ |

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

## 8. VNC Web UI (Display)

AnyVM includes a built-in, premium VNC Web UI that allows you to access the VM's graphical console directly from your browser.

<img width="1362" height="879" alt="xfce" src="https://github.com/user-attachments/assets/793e9341-4602-4ca0-b098-d5e29fab59f9" />


<img width="2348" height="1660" alt="image" src="https://github.com/user-attachments/assets/7f334153-5c89-4323-b6e8-86a1467c80df" />


- **Automatic Launch**: Enabled by default (unless `--vnc off` is specified). AnyVM automatically starts a VNC-to-Web proxy.
- **Modern Interface**: Features a sleek dark mode, glassmorphism aesthetics, and smooth animations.
  - **Clipboard Support**: Use the "Paste Text" button or `Ctrl+V` to send your local clipboard to the VM.
  - **Special Keys**: Dedicated "Ctrl+Alt+Del" button.
  - **Fullscreen**: Toggle fullscreen mode for an immersive experience.
  - **Stats**: Real-time FPS and latency monitoring.
- **Accessibility**: Available at `http://localhost:6080` by default. If the port is occupied, AnyVM will automatically try the next available port (e.g., 6081, 6082).

## 9. CLI options (with examples)

All examples below use `python3 anyvm.py ...`. You can also run `python3 anyvm.py --help` to see the built-in help.

### Required

- `--os <name>`: Target guest OS (required).
  - Supported: `freebsd` / `openbsd` / `netbsd` / `dragonflybsd` / `solaris` / `omnios` / `openindiana` / `haiku`
  - Example:
    - `python3 anyvm.py --os freebsd`

### Release / arch / resources

- `--release <ver>`: Guest release version. If omitted, anyvm auto-selects an available release.
  - Example: `python3 anyvm.py --os freebsd --release 14.3`

- `--arch <arch>`: Guest architecture.
  - Common values: `x86_64` / `aarch64` / `riscv64`
  - Example: `python3 anyvm.py --os openbsd --release 7.5 --arch aarch64`

- `--mem <MB>`: Memory size in MB (default: 2048).
  - Example: `python3 anyvm.py --os freebsd --mem 4096`

- `--cpu <num>`: vCPU count (default: all host cores).
  - Example: `python3 anyvm.py --os freebsd --cpu 4`

- `--cpu-type <type>`: QEMU CPU model (e.g. `host`, `cortex-a72`).
  - Example: `python3 anyvm.py --os openbsd --arch aarch64 --cpu-type cortex-a72`

### Images / builders

- `--builder <ver>`: Pin a specific builder version (used to download matching cloud images).
  - Example: `python3 anyvm.py --os netbsd --builder 2.0.1`

- `--qcow2 <path>`: Use a local qcow2 image (skip downloading).
  - Example: `python3 anyvm.py --os freebsd --qcow2 .\\output\\freebsd\\freebsd-14.3.qcow2`

- `--snapshot`: Enable QEMU snapshot mode. Changes made to the disk are not saved. 
  - Works with `--cache-dir` to run directly from the cache without copying to the data directory.
  - Example: `python3 anyvm.py --os freebsd --snapshot`

### Networking (user-mode networking / slirp)

- `--ssh-port <port>` / `--sshport <port>`: Host port forwarded to guest SSH (`:22`). If omitted, anyvm auto-picks a free port.
  - Example: `python3 anyvm.py --os freebsd --ssh-port 10022`

- `--ssh-name <name>`: Add an extra SSH alias name for convenience (so you can `ssh <name>`).
  - Example: `python3 anyvm.py --os freebsd --ssh-name myvm`

- `--host-ssh-port <port>`: The host SSH port as reachable from the guest (default: 22). Used for generating a `Host host` entry inside the guest.
  - Example: `python3 anyvm.py --os freebsd --host-ssh-port 2222`

- `-p <mapping>`: Additional port forwards (repeatable).
  - Form 1: `host:guest` (TCP by default)
    - Example: `python3 anyvm.py --os freebsd -p 8080:80`
  - Form 2: `tcp:host:guest`
    - Example: `python3 anyvm.py --os freebsd -p tcp:8443:443`
  - Form 3: `udp:host:guest`
    - Example: `python3 anyvm.py --os freebsd -p udp:5353:5353`

- `--public`: Listen on `0.0.0.0` for forwarded ports instead of `127.0.0.1`.
  - Example: `python3 anyvm.py --os freebsd --public -p 8080:80`

- `--enable-ipv6`: Enable IPv6 in QEMU user networking (slirp).
  - Default: IPv6 is disabled (anyvm adds `ipv6=off` to `-netdev user,...`).
  - Example: `python3 anyvm.py --os freebsd --enable-ipv6`


### Shared folders (-v) and sync mode (--sync)

- `-v <host:guest>`: Add a shared/synced folder mapping (repeatable).
  - Linux/macOS example: `python3 anyvm.py --os freebsd -v $(pwd):/data`
  - Windows example: `python3 anyvm.py --os freebsd -v D:\\data:/data`

- `--sync <mode>`: Sync mechanism used for `-v`. Strictly validated.
  - Supported: `rsync` (default), `sshfs`, `nfs`, `scp`. Empty string also defaults to `rsync`. Any other value will cause an error.
  - Examples:
    - `python3 anyvm.py --os freebsd --sync rsync -v $(pwd):/data`
    - `python3 anyvm.py --os solaris --sync scp -v D:\\data:/data`

### Console / display / debugging

- `--console` / `-c`: Run in the foreground (console mode).
  - Example: `python3 anyvm.py --os freebsd --console`

- `--detach` / `-d`: Run in the background (do not auto-enter SSH).
  - Example: `python3 anyvm.py --os freebsd --detach`

- `--serial <port>`: Expose the guest serial console via a host TCP port (if omitted, auto-select starting at 7000).
  - Example: `python3 anyvm.py --os freebsd --serial 7000`

- `--vnc <display>`: Enable VNC (e.g. `0` means `:0` / port 5900). 
  - **VNC Web UI**: Enabled by default starting at port `6080` (auto-increments if busy). Use `--vnc off` to disable.
  - Example: `python3 anyvm.py --os freebsd --vnc 0`

- `--mon <port>`: Expose the QEMU monitor via telnet on localhost.
  - Example: `python3 anyvm.py --os freebsd --mon 4444`

- `--debug`: Enable verbose debug logging.
  - Example: `python3 anyvm.py --os freebsd --debug`

### Boot / platform

- `--uefi`: Enable UEFI boot (FreeBSD enables this implicitly).
  - Example: `python3 anyvm.py --os freebsd --uefi`

- `--disktype <type>`: Disk interface type (e.g. `virtio`, `ide`).
  - Example: `python3 anyvm.py --os dragonflybsd --disktype ide`

- `--whpx`: (Windows) Attempt to use WHPX acceleration.
  - Example: `python3 anyvm.py --os freebsd --whpx`

### Data directory

- `--data-dir <dir>` / `--workingdir <dir>`: Directory used to store images and caches (default: `./output`).
  - Example: `python3 anyvm.py --os freebsd --data-dir .\\output`

### Run a command inside the VM

- `-- <cmd...>`: Everything after `--` is passed through to the final `ssh` invocation and executed inside the VM.
  - Examples:
    - `python3 anyvm.py --os freebsd -- uname -a`
    - `python3 anyvm.py --os freebsd -- sh -lc "id; uname -a"`










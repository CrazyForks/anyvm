# Run any VM anywhere 

[![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)


anyvm is a single-file tool for bootstrapping BSD, Illumos, and Linux guests with QEMU on Linux, macOS, and Windows. It downloads cloud images, sets up firmware, and starts the VM with sane defaults so you can focus on the guest.

## 1. Quick launch

- Github CodeSpace:
  
  [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/anyvm-org/anyvm)
  
  Enable KVM in Codespaces before running:

  ```bash
  sudo chmod o+rw /dev/kvm
  
  sudo apt-get update

  sudo apt-get --no-install-recommends -y install \
  zstd ovmf xz-utils qemu-utils ca-certificates \
  qemu-system-x86 qemu-system-arm qemu-efi-aarch64 \
  qemu-efi-riscv64 qemu-system-riscv64 qemu-system-misc u-boot-qemu \
  qemu-system-ppc qemu-system-s390x \
  openssh-client
  
  ```

- Google Cloud Shell:

  <a href="https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2Fanyvm-org%2Fanyvm&cloudshell_tutorial=.cloudshell%2Ftutorial.md&show=terminal&ephemeral=true&cloudshell_print=.cloudshell%2Fconsole.md" target="_blank" rel="noopener noreferrer">
  <img src="https://gstatic.com/cloudssh/images/open-btn.svg" alt="Try it Now in Cloud Shell">
</a>


## 2. Quick start (local)

```bash


#command line release
python3 anyvm.py --os freebsd
python3 anyvm.py --os freebsd --release 14.3
python3 anyvm.py --os freebsd --release 14.3 --arch aarch64
python3 anyvm.py --os openbsd --release 7.5 --arch aarch64
python3 anyvm.py --os solaris
python3 anyvm.py --os tribblix
python3 anyvm.py --os ubuntu
python3 anyvm.py --os ubuntu --release 24.04
python3 anyvm.py --os ghostbsd
python3 anyvm.py --os blissos

python3 anyvm.py --os freebsd --release 14.3 --arch riscv64
python3 anyvm.py --os freebsd --release 15.0 --arch powerpc64

python3 anyvm.py --os ubuntu --release 24.04 --arch aarch64
python3 anyvm.py --os ubuntu --release 24.04 --arch riscv64
python3 anyvm.py --os ubuntu --release 24.04 --arch s390x
python3 anyvm.py --os ubuntu --release 24.04 --arch ppc64le



#desktop release

python3 anyvm.py --os freebsd  --release 15.0-xfce
python3 anyvm.py --os freebsd  --release 15.0-gnome
python3 anyvm.py --os freebsd  --release 15.0-kde6

python3 anyvm.py --os openbsd  --release 7.9-xfce
python3 anyvm.py --os openbsd  --release 7.9-gnome
python3 anyvm.py --os openbsd  --release 7.9-kde6
python3 anyvm.py --os openbsd  --release 7.9-mate
python3 anyvm.py --os openbsd  --release 7.9-lxqt
python3 anyvm.py --os openbsd  --release 7.9-lumina
python3 anyvm.py --os openbsd  --release 7.9-enlightenment

python3 anyvm.py --os ghostbsd                       # MATE (default)
python3 anyvm.py --os ghostbsd --release 26.1-xfce
python3 anyvm.py --os ghostbsd --release 26.1-gershwin

# BlissOS (Android-x86): root ssh + the Android desktop on the VNC console
# -v folder sync uses scp (the only backend the Android guest supports).
python3 anyvm.py --os blissos                        # latest (16, Android 13)
python3 anyvm.py --os blissos --release 15           # Android 12L
python3 anyvm.py --os blissos --release 14           # Android 11



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

| Guest | Workflow | x86_64 | aarch64 (arm64) | riscv64 | s390x | powerpc64 | Builder |
|-------|----------|--------|-----------------|---------|-------|-----------|---------|
| FreeBSD | [![Test FreeBSD](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml) | ✅ | ✅ | ✅ | — | ✅ | [![Build FreeBSD](https://github.com/anyvm-org/freebsd-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/freebsd-builder) |
| OpenBSD | [![Test OpenBSD](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml) | ✅ | ✅ | ✅ | — | — | [![Build OpenBSD](https://github.com/anyvm-org/openbsd-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/openbsd-builder) |
| NetBSD | [![Test NetBSD](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml) | ✅ | ✅ | — | — | — | — | [![Build NetBSD](https://github.com/anyvm-org/netbsd-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/netbsd-builder) |
| DragonFlyBSD | [![Test DragonflyBSD](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml) | ✅ | — | — | — | — | [![Build DragonflyBSD](https://github.com/anyvm-org/dragonflybsd-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/dragonflybsd-builder) |
| MidnightBSD | [![Test MidnightBSD](https://github.com/anyvm-org/anyvm/actions/workflows/midnightbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/midnightbsd.yml) | ✅ | — | — | — | — | [![Build MidnightBSD](https://github.com/anyvm-org/midnightbsd-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/midnightbsd-builder) |
| GhostBSD | [![Test GhostBSD](https://github.com/anyvm-org/anyvm/actions/workflows/ghostbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/ghostbsd.yml) | ✅ | — | — | — | — | [![Build GhostBSD](https://github.com/anyvm-org/ghostbsd-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/ghostbsd-builder) |
| Solaris | [![Test Solaris](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml) | ✅ | — | — | — | — | [![Build Solaris](https://github.com/anyvm-org/solaris-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/solaris-builder) |
| OmniOS | [![Test OmniOS](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml) | ✅ | — | — | — | — | [![Build OmniOS](https://github.com/anyvm-org/omnios-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/omnios-builder) |
| OpenIndiana | [![Test OpenIndiana](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml) | ✅ | — | — | — | — | [![Build OpenIndiana](https://github.com/anyvm-org/openindiana-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/openindiana-builder) |
| Tribblix | [![Test Tribblix](https://github.com/anyvm-org/anyvm/actions/workflows/tribblix.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/tribblix.yml) | ✅ | — | — | — | — | [![Build Tribblix](https://github.com/anyvm-org/tribblix-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/tribblix-builder) |
| Haiku | [![Test Haiku](https://github.com/anyvm-org/anyvm/actions/workflows/haiku.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/haiku.yml) | ✅ | — | — | — | — | [![Build Haiku](https://github.com/anyvm-org/haiku-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/haiku-builder) |
| Ubuntu | [![Test Ubuntu](https://github.com/anyvm-org/anyvm/actions/workflows/ubuntu.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/ubuntu.yml) | ✅ | ✅ | ✅ | ✅ | ✅ | [![Build Ubuntu](https://github.com/anyvm-org/ubuntu-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/ubuntu-builder) |
| BlissOS (Android) | [![Test BlissOS](https://github.com/anyvm-org/anyvm/actions/workflows/blissos.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/blissos.yml) | ✅ | — | — | — | — | [![Build BlissOS](https://github.com/anyvm-org/blissos-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/blissos-builder) |

## 5. Host support

| Host | x86_64 guests | aarch64 guests | riscv64 guests | s390x guests | powerpc64 guests |
|------|---------------|----------------|----------------|--------------|------------------|
| Linux x86_64 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Linux aarch64 (arm64)  | — | ✅ | — | — | — |
| Linux s390x (IBM Z)  | — | — | — | ✅ (KVM) | — |
| MacOS Apple silicon  | ✅ | ✅ | — | — | — |
| Windows x86_64 Native | ✅ | — | — | — | — |
| Windows x86_64 WSL | ✅ | ✅ | ✅ | ✅ | ✅ |

## 6. Install dependencies

### 6.1 Linux (apt-based) [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)

```bash
sudo apt-get --no-install-recommends -y install \
  zstd ovmf xz-utils qemu-utils ca-certificates \
  qemu-system-x86 qemu-system-arm qemu-efi-aarch64 \
  qemu-efi-riscv64 qemu-system-riscv64 u-boot-qemu \
  qemu-system-ppc \
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
- **Security**: Protect your VNC session with `--vnc-password <pwd>`. When set, the browser will prompt for credentials when accessing the Web UI. (Note: The **username can be anything**, but the **password must be correct**).
- **Remote Access**: Use `--remote-vnc` to automatically create a public, secure tunnel (via Cloudflare, Localhost.run, Pinggy, or Serveo) to access your VM's display from anywhere in the world. (In Google Cloud Shell, this is enabled by default; use `--remote-vnc no` to disable).

## 9. CLI options (with examples)

All examples below use `python3 anyvm.py ...`. You can also run `python3 anyvm.py --help` to see the built-in help.

### Required

- `--os <name>`: Target guest OS (required).
  - Supported: `freebsd` / `ghostbsd` / `openbsd` / `netbsd` / `dragonflybsd` / `midnightbsd` / `solaris` / `omnios` / `openindiana` / `tribblix` / `haiku` / `ubuntu` / `blissos`
  - Example:
    - `python3 anyvm.py --os freebsd`

### Release / arch / resources

- `--release <ver>`: Guest release version. If omitted, anyvm auto-selects an available release.
  - Example: `python3 anyvm.py --os freebsd --release 14.3`

- `--arch <arch>`: Guest architecture.
  - Common values: `x86_64` / `aarch64` / `riscv64` / `s390x` / `powerpc64` /
    `ppc64le` / `sparc64`
  - Example: `python3 anyvm.py --os openbsd --release 7.5 --arch aarch64`
  - Notes for ubuntu guests on emulated arches (always TCG, slow):
    - `aarch64` defaults to `-cpu cortex-a72` (distro QEMU 8.2 aborts with a
      `regime_is_user` assertion when the 26.04 kernel uses VHE under
      `-cpu max`).
    - `riscv64` 26.04 requires QEMU >= 9.1 (`-cpu rva23s64` is selected
      automatically; the RVA23 userspace baseline and the 7.0 kernel do not
      run on QEMU 8.2). 22.04 / 24.04 work on stock QEMU.
    - `s390x` works best with QEMU >= 10; the distro 8.2 intermittently
      freezes guest systemd at startup (a TCG-only bug). On a real IBM Z
      host with `/dev/kvm`, KVM is used automatically (`-cpu host`) and
      stock QEMU is fine.
    - `ppc64le` 22.04 requires QEMU >= 10; under the distro 8.2 pseries TCG
      the jammy python3.10 segfaults (every cloud-init / apt run crashes).
      24.04 / 26.04 work on stock QEMU.
    - For the riscv64 26.04, s390x and ppc64le 22.04 cases, on Linux x86_64
      hosts anyvm.py automatically downloads and uses pinned QEMU 10.2.3
      whenever the system QEMU is too old -- no manual setup needed.
      [ubuntu-builder](https://github.com/anyvm-org/ubuntu-builder) compiles
      these from source in its release-files job (they are no longer
      committed to git) and publishes them as release assets; see its
      `files/README.md`.
  - `openbsd --arch sparc64`: anyvm.py automatically downloads the patched
    OpenBIOS firmware the image needs (QEMU's bundled OpenBIOS crashes every
    OpenBSD >= 7.3 sparc64 kernel on cold boot) and passes it via `-bios`.
    [openbsd-builder](https://github.com/anyvm-org/openbsd-builder) rebuilds
    it from source in its release-files job and publishes it as a release
    asset; see its `bios/README.md`.

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

- `--vnc-password <pwd>`: Set a password for the VNC Web UI. Empty or omitted means no password. (Note: On the login page, the **username can be anything**, but the **password must be correct**).
  - Example: `python3 anyvm.py --os freebsd --vnc-password mysecret`

- `--remote-vnc`: Create a public tunnel for the VNC Web UI using Cloudflare, Localhost.run, Pinggy, or Serveo.
  - Example: `python3 anyvm.py --os freebsd --remote-vnc`
  - Advanced: Use `cf`, `lhr`, `pinggy`, or `serveo` to specify a service: `python3 anyvm.py --os freebsd --remote-vnc cf`
  - Disable: Use `no` to disable (e.g., in Google Cloud Shell where it's default): `python3 anyvm.py --os freebsd --remote-vnc no`

- `--mon <port>`: Expose the QEMU monitor via telnet on localhost.
  - Example: `python3 anyvm.py --os freebsd --mon 4444`

- `--debug`: Enable verbose debug logging.
  - Example: `python3 anyvm.py --os freebsd --debug`

### Boot / platform

- `--uefi`: Enable UEFI boot (FreeBSD enables this implicitly).
  - Example: `python3 anyvm.py --os freebsd --uefi`

- `--disktype <type>`: Disk interface type (e.g. `virtio`, `ide`).
  - Example: `python3 anyvm.py --os dragonflybsd --disktype ide`

- `--boot-timeout-sec <n>`: Boot timeout in seconds before QEMU is killed and retried once. Default: `600` (10 minutes).
  - Exception: OpenBSD on `aarch64` defaults to `1200` (20 minutes) because it boots much slower under emulation.
  - Exception: when running under TCG (no hardware acceleration -- e.g. Windows runners with chocolatey QEMU, or any host without `/dev/kvm` / HVF / WHPX), the default is bumped to `1800` (30 minutes). TCG is 10-50x slower than KVM, and heavy guests like Solaris or DragonFlyBSD often need more time to boot.
  - Both exceptions only apply when `--boot-timeout-sec` is not explicitly passed; an explicit value always wins.
  - Useful for slow hosts (emulated arches, low-resource CI runners) or for failing fast in tests.
  - Example: `python3 anyvm.py --os openbsd --boot-timeout-sec 1200`

- `--enable-pmu`: Expose the host PMU (performance monitoring unit / hardware performance counters) to the guest.
  - **Disabled by default.** Exposing the host PMU via `-cpu host` can trigger intermittent `#GP`-in-`wrmsr` crashes during early guest boot when the host CPU generation exposes PMU MSRs that KVM refuses writes to. DragonFlyBSD is the most affected guest; this manifested as random boot failures across CI runners with different Intel CPU generations.
  - Only applies to x86_64 with hardware acceleration (`kvm` / `whpx` / `hvf`). TCG and non-x86 arches are unaffected.
  - Pass `--enable-pmu` if you need `perf` / `pmcstat` / VTune or similar profilers to work inside the guest.
  - Example: `python3 anyvm.py --os ubuntu --enable-pmu -- perf stat ls`

- `--tcg`: Force pure software emulation (no KVM / HVF / WHPX). Slow; useful when hardware acceleration is unavailable or misbehaving. Generic -- works for any guest.
  - Example: `python3 anyvm.py --os tribblix --tcg`
  - Historical note: older `tribblix` releases froze a CPU-vendor-specific `libc_hwcap` variant into `/lib/libc.so.1` at build time, which crash-looped (`init` killed by `SIGKILL`) when run under KVM on the other vendor's CPU; anyvm used to auto-fall-back to TCG on Intel hosts to dodge it. Since `v2.0.3` (tribblix-builder's `finalizeImage` hook) the release ships the generic, capability-neutral libc that boots under KVM on both Intel and AMD and re-optimizes per-CPU at first boot, so no fallback is needed. Use `--tcg` only if you must run a pre-`v2.0.3` image on a mismatched CPU.



### Data directory

- `--data-dir <dir>`: Directory used to store images and caches (default: `./output`).
  - Example: `python3 anyvm.py --os freebsd --data-dir output`

### Run a command inside the VM

- `-- <cmd...>`: Everything after `--` is passed through to the final `ssh` invocation and executed inside the VM.
  - Examples:
    - `python3 anyvm.py --os freebsd -- uname -a`
    - `python3 anyvm.py --os freebsd -- sh -lc "id; uname -a"`










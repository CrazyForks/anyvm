# Welcome to AnyVM on Google Cloud Shell!

## Introduction

AnyVM allows you to run virtual machines of various BSD and Unix-like operating systems directly in your Cloud Shell environment.

## Prerequisites

First, install the required dependencies:

```bash
sudo apt-get update && sudo apt-get --no-install-recommends -y install \
    zstd \
    ovmf \
    xz-utils \
    qemu-utils \
    ca-certificates \
    qemu-system-x86 \
    qemu-system-arm \
    qemu-efi-aarch64 \
    nfs-kernel-server \
    rsync
```

This will take a minute or two to complete.

## Quick Start

Once the dependencies are installed, you can start using AnyVM immediately!

### Run FreeBSD

```bash
python anyvm.py --os freebsd
```

### Run OpenBSD

```bash
python anyvm.py --os openbsd
```

### Run NetBSD

```bash
python anyvm.py --os netbsd
```

### Run Solaris

```bash
python anyvm.py --os solaris
```

## Advanced Options

### Specify a Release Version

```bash
python anyvm.py --os freebsd --release 14.3
```

### Run ARM64 Architecture

```bash
python anyvm.py --os freebsd --arch aarch64
```

### Mount Local Directory

```bash
python anyvm.py --os freebsd -v /home/user/data:/mnt/data
```

### Custom Port Mapping

```bash
python anyvm.py --os freebsd -p 8080:80
```

## What Happens Next?

1. AnyVM will download the VM image (first time only)
2. The VM will boot automatically
3. SSH connection will be configured
4. You'll be connected to the VM shell

## Connecting to Your VM

After the VM starts, you can connect using:

```bash
ssh <vm-name>
```

For example, if you started FreeBSD:

```bash
ssh freebsd-15.0
```

## Getting Help

View all available options:

```bash
python anyvm.py --help
```

## More Information

Visit the project repository: https://github.com/anyvm-org/anyvm

Happy VM-ing! 🚀

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
    rsync qemu-efi-riscv64 qemu-system-riscv64 u-boot-qemu
    
    
```


Then, try:

```bash

python anyvm.py --os freebsd

```

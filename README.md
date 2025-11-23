# Run any vm anywhere [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)



[![Test FreeBSD](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml)

[![Test NetBSD](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml)

[![Test OpenBSD](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml)

[![Test DragonflyBSD](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml)

[![Test Solaris](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml)

[![Test OmniOS](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml)

[![Test OpenIndiana](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml)



# On Google Cloud Shell:

[![Try it Now in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://console.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/anyvm-org/anyvm.git)

Click the "Try it Now in Cloud Shell" button above to instantly launch this project in Google Cloud Shell.

The environment is already configured with QEMU and all necessary dependencies. Simply run:

```bash
python anyvm.py --os freebsd
```

Or try other operating systems:

```bash
python anyvm.py --os openbsd
python anyvm.py --os netbsd
python anyvm.py --os solaris
```

Note: Google Cloud Shell provides a free Linux environment with nested virtualization support.


# On Linux Host:


| Host    | x86_64 VM | aarch64(arm64) VM | riscv64 VM |
|---------|---------|---------|-----------------|
| x86_64 Linux    |  ✅     |  ✅    |           ✅    |
| aarch64(arm64) Linux    |  ❌     |  ✅    |           ❌    |



```bash

sudo apt-get --no-install-recommends -y install \
        zstd \
        ovmf \
        xz-utils \
        qemu-utils \
        ca-certificates \
        qemu-system-x86 \
        qemu-system-arm qemu-efi-aarch64
        
        
python anyvm.py  --os freebsd

python anyvm.py  --os freebsd --release 14.3

python anyvm.py  --os freebsd --release 14.3  --arch aarch64

```


# On MacOS Host:

Apple silicon:

| Host    | x86_64 VM | aarch64(arm64) VM | riscv64 VM |
|---------|---------|---------|-----------------|
| aarch64(arm64) Apple silicon    |  ✅     |  ✅    |           ✅    |



```bash

brew install qemu


python anyvm.py  --os freebsd

python anyvm.py  --os freebsd --release 14.3

python anyvm.py  --os freebsd --release 14.3  --arch aarch64

```


# On Windows Host:

Install qemu For Windows:

https://www.qemu.org/download/#windows

https://qemu.weilnetz.de/w64/

```bash

python anyvm.py  --os freebsd

```



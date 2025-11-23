# Run any vm anywhere [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)



[![Test FreeBSD](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/freebsd.yml)

[![Test NetBSD](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/netbsd.yml)

[![Test OpenBSD](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openbsd.yml)

[![Test DragonflyBSD](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/dragonflybsd.yml)

[![Test Solaris](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/solaris.yml)

[![Test OmniOS](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/omnios.yml)

[![Test OpenIndiana](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/openindiana.yml)



# Try it Now in Google Cloud Shell:

<a href="https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https%3A%2F%2Fgithub.com%2Fanyvm-org%2Fanyvm&cloudshell_tutorial=.cloudshell%2Ftutorial.md&show=terminal&ephemeral=true&cloudshell_print=.cloudshell%2Fconsole.md" target="_blank" rel="noopener noreferrer">
  <img src="https://gstatic.com/cloudssh/images/open-btn.svg" alt="Try it Now in Cloud Shell">
</a>


Click the "Try it Now in Cloud Shell" button above to instantly launch this project in Google Cloud Shell.


```bash
python anyvm.py --os freebsd
```

Or try other operating systems:

```bash
python anyvm.py --os openbsd
python anyvm.py --os netbsd
python anyvm.py --os solaris
```


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



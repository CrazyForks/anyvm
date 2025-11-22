# Run any vm anywhere [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)





# On Linux Host:

```
sudo apt-get --no-install-recommends -y install \
        zstd \
        ovmf \
        xz-utils \
        qemu-utils \
        ca-certificates \
        qemu-system-x86 \
        qemu-system-arm qemu-efi-aarch64
        
        


python anyvm.py  --os freebsd

```


# On MacOS Host:

```
brew install qemu


python anyvm.py  --os freebsd

```


# On Windows Host:

Install qemu For Windows:

https://www.qemu.org/download/#windows
https://qemu.weilnetz.de/w64/

```

python anyvm.py  --os freebsd

```



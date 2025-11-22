# Run any vm anywhere [![Test](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml/badge.svg)](https://github.com/anyvm-org/anyvm/actions/workflows/test.yml)





#Linux:

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


#MacOS:

```
brew install qemu


python anyvm.py  --os freebsd

```


#Windows:

Install qemu For Windows:

https://www.qemu.org/download/#windows
https://qemu.weilnetz.de/w64/

```

python anyvm.py  --os freebsd

```



#!/usr/bin/env python3
"""Build dist/tolino-koreader-boot.zip, laid out like the reader's USB drive.

    .kobo/Kobo.tgz                  boot hook + start script, unpacked into /usr/local/Kobo
    .adds/koreader-boot/README.txt  the switches that live in this folder
"""
import io
import os
import tarfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, 'dist')
FILES = ('memorylogger', 'koreader-boot')

README = b"""tolino-koreader-boot: switches (create or delete these files over USB)

boot-stock        exists: boot the stock reader instead of KOReader
uninstall         exists: put the stock reader back for good at the next boot
authorized_keys   SSH public keys allowed to log in as root on port 2222
ssh_host_key      created automatically, keeps the SSH host key the same across boots

More: https://github.com/winterwurzel/tolino-koreader-boot
"""


def kobo_tgz():
    """Kobo.tgz the way /etc/init.d/ota expects it: plain names, extracted into /usr/local/Kobo."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz', format=tarfile.GNU_FORMAT) as tar:
        for name in FILES:
            with open(os.path.join(HERE, 'src', name), 'rb') as f:
                data = f.read()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def main():
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, 'tolino-koreader-boot.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('.kobo/Kobo.tgz', kobo_tgz())
        z.writestr('.adds/koreader-boot/README.txt', README)
    print('built', out)


if __name__ == '__main__':
    main()

"""A csomagolt windowsos PicasaPy belépési pontja (#3021).

## Miért kell külön fájl

A PyInstaller a megadott fájlt **szkriptként** futtatja, nem modulként. A
`src/picasapy/app/__main__.py` viszont RELATÍV importot használ
(`from .application import run`), ami szkriptként hibára fut:

```
ImportError: attempted relative import with no known parent package
```

Mérve a windowsos CI-n: a csomag felépült, az indítás viszont ezzel
elhasalt — és mivel ablakos (`console=False`) csomag, a PyInstaller
hibajelző ablakot nyitott, ami **kattintásra várt**, tehát a füstpróba
állt, amíg az időkorlát le nem vágta.

Ez a fájl ezért a CSOMAG belépője: nincs benne relatív import, csak a
rendes modul-hívás.
"""

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--picasapy-video-decode":
        if len(sys.argv) != 4:
            sys.exit(2)
        from picasapy.thumbs.video_decode_worker import main as worker_main

        sys.exit(worker_main(sys.argv[2], sys.argv[3]))

    if len(sys.argv) > 1 and sys.argv[1] == "--picasapy-poster":
        from picasapy.printing.poster_worker import main as worker_main

        sys.exit(worker_main(sys.argv[2:]))

    from picasapy.app.__main__ import main

    sys.exit(main())

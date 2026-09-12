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

from picasapy.app.__main__ import main

if __name__ == "__main__":
    sys.exit(main())

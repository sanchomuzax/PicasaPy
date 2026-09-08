"""A Picasa LASSÚ származás-kulcsa (`originslow`) — #1482, #2733.

A gyors kulcs (`fastkey.picasa_fast_key`, #1481) csak a fájl két végét
nézi, ezért két azonos méretű, csak a közepén eltérő kép ütközik. Az
eredeti Picasa erre egy **második** kulcsot tart, amely a TELJES fájlt
hasheli, és a gyors kulcs ütközéseit oldja fel (mérve: 28,5× dúsulás):

```
originslow = MD5( a teljes fájl )[0..8]   ; 64 bites számként, kis-endián
```

Bináris bizonyíték (`docs/specs/picasa-tartalomkulcs.md`): a termelő a
`FUN_00a4ce40` (`.\\yt\\ytIO.cpp:417`), amely `0x10000` bájtos darabokban
olvas (`ReadFile` + MD5-`Update` ciklus, `0x00a4cf49` / `0x00a4cf75`), majd
MD5-`Final`-t hív (`0x00a4cfa8`). Egyetlen hívója a kulcspár-burkoló
(`FUN_00a4cd00`), amelynek a lassú fele opcionális.

A mérés 18/18 valódi fényképen bitre pontos volt (#1482); a kulcs az ini
`originhash` MÁSODIK fele (`originhash.py`, #2733).
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

#: A bináris ekkora darabokban olvas (`0x10000`) — az eredmény ettől
#: független, de a memóriaigény nem: nagy fájlt sem olvasunk be egészben.
DARAB_MERET = 0x10000

_KULCS = struct.Struct("<Q")


def picasa_slow_key(path: Path) -> int | None:
    """A fájl teljes tartalmának Picasa-kompatibilis lassú kulcsa.

    `None`, ha a fájl üres (ott a gyors kulcs sem ad értéket), vagy ha nem
    olvasható (törölt/elérhetetlen NAS-forrás, könyvtár) — ez nem kivétel,
    a hívó egyszerűen kihagyja a fájlt.

    A teljes fájlt beolvassa, de csak `DARAB_MERET` bájtot tart egyszerre a
    memóriában."""
    md5 = hashlib.md5(usedforsecurity=False)
    olvasott = 0
    try:
        with open(path, "rb") as handle:
            while True:
                darab = handle.read(DARAB_MERET)
                if not darab:
                    break
                olvasott += len(darab)
                md5.update(darab)
    except OSError:
        return None
    if olvasott <= 0:
        return None
    return int(_KULCS.unpack(md5.digest()[:8])[0])

"""A Picasa fej+farok tartalom-kulcsa (`originfast`) — #1481.

Az eredeti Picasa a másodpéldány-kereséshez NEM olvassa végig a fájlt: a
méretből, az első és az utolsó 16834 bájtból képez egy 64 bites kulcsot, és
azt tárolja az `imagedata_originfast.pmp` oszlopban (PMP-típus `0x04`, u64).

```
FEJ   = min(méret, 16834)                       ; 0x41C2
FAROK = (méret > 33668) ? 16834 : méret − FEJ    ; 0x8384
kulcs = MD5( uint32_le(méret) ‖ első FEJ bájt ‖ utolsó FAROK bájt )
        első 8 bájtja, kis-endián uint64-ként
```

A visszafejtés teljes bizonyítéklánca (címekkel, MD5-kezdőállandókkal, a
kizárt téves jelöltekkel) a `docs/specs/picasa-tartalomkulcs.md`-ben van, és
a felhasználó valódi `db3` adatbázisával szemben tizenkét igazi fényképen
bitre pontosan reprodukáltuk.

⚠️ **A kulcs gyengébb, mint egy teljes tartalom-hash.** 64 bites, és csak a
fájl két végét nézi: két azonos méretű kép, amely csak a KÖZEPÉN tér el,
ugyanazt a kulcsot kapja. Az eredeti Picasa ezt elfogadta; mi nem — nálunk a
kulcs kizárólag **előszűrő** (ld. `dedup/exact.py`), a másodpéldányságot
továbbra is a teljes SHA-256 mondja ki. Ez a modul ezért soha nem ad
"azonos"/"különböző" ítéletet, csak kulcsot.
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

#: A fej (és a csonkolt farok) hossza bájtban — a binárisban `0x41C2`.
FEJ_MERET = 16834

#: E fölött a méret fölött csonkol a farok `FEJ_MERET`-re — `0x8384`.
#: Alatta (és rajta) a fej + farok együtt a TELJES fájl, átfedés nélkül.
FAROK_KUSZOB = 33668

_MERET_ELOTAG = struct.Struct("<I")
_KULCS = struct.Struct("<Q")


def farok_meret(meret: int) -> int:
    """A farokból beolvasandó bájtok száma az adott fájlmérethez.

    A `meret <= FAROK_KUSZOB` esetben a fej és a farok együtt pontosan a
    teljes fájlt fedi le (a farok a fej UTÁNI maradék), e fölött mindkét
    vég `FEJ_MERET` bájt, és a közepe kimarad."""
    fej = min(meret, FEJ_MERET)
    return FEJ_MERET if meret > FAROK_KUSZOB else meret - fej


def olvasott_bajtok(meret: int) -> int:
    """Hány bájtot olvas a kulcs egy adott méretű fájlnál (mérésekhez)."""
    if meret <= 0:
        return 0
    return min(meret, FEJ_MERET) + farok_meret(meret)


def picasa_fast_key(path: Path) -> int | None:
    """A fájl Picasa-kompatibilis gyors tartalom-kulcsa 64 bites egészként.

    `None`, ha a fájl üres (az eredeti ilyenkor `-1`-gyel tér vissza), vagy
    ha nem olvasható (törölt/elérhetetlen NAS-forrás, könyvtár) — ez nem
    kivétel, a hívó egyszerűen kihagyja a fájlt az összevetésből.

    Legfeljebb 4 + 2 × 16834 = 33 672 bájtot olvas be, a fájl méretétől
    függetlenül."""
    try:
        meret = path.stat().st_size
        if meret <= 0:
            return None
        fej = min(meret, FEJ_MERET)
        farok = farok_meret(meret)
        with open(path, "rb") as handle:
            eleje = handle.read(fej)
            if farok:
                handle.seek(meret - farok)
                vege = handle.read(farok)
            else:
                vege = b""
    except OSError:
        return None
    if len(eleje) != fej or len(vege) != farok:
        return None  # a fájl olvasás közben rövidült — nem adunk hamis kulcsot
    digest = hashlib.md5(
        _MERET_ELOTAG.pack(meret & 0xFFFFFFFF) + eleje + vege,
        usedforsecurity=False,
    ).digest()
    return int(_KULCS.unpack(digest[:8])[0])

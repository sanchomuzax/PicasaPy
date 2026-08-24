"""A `.cxf` azonosítói: az album `albumUID`-ja és a csomópontok `<uid>`-ja (#1092).

## Mit mért ki a golden készlet

A 12 valódi Picasa-mintán (`referencia/kollazs-golden/`) mindkét azonosító
ott van, és az alakjuk egyértelmű:

| mező | alak | példa |
|---|---|---|
| `albumUID` | 32 kisbetűs hexa | `a4ef8e0fd2dbb152d25d79eb2bd2a28b` |
| `<uid>` | 16 hexa + **16 nulla** | `c91b4354e61f4a5a0000000000000000` |

A mérés két **invariánst** is ad, és ezek fontosabbak a konkrét
értékeknél:

1. Az `AI` mappából készült **11 kollázs `albumUID`-ja azonos** — az
   azonosító tehát a FORRÁSALBUMÉ, nem az egyes kollázsé.
2. Ugyanaz a kép **ugyanazt a `<uid>`-ot kapja** két külön kollázsban is
   (az `AI1.cxf` és az `AI7.cxf` közös képei egyeznek).

Mindkettő azt mondja: az azonosító **determinisztikus**, nem véletlen.
Egy `uuid4()`-alapú megoldás mindkét invariánst megsértené.

## SAJÁT FUNKCIÓ (#1092): a származtatás a miénk

Az eredeti értékek a Picasa BELSŐ adatbázisából jönnek (az `imagedata`
rekord `uid64` mezője, ld. `docs/specs/picasa-imagedata-rekord.md`), és
**nem vezethetők le** sem az útvonalból, sem a `.picasa.ini`-ből:

- lemértük a szokásos útvonal-hasheket (md5 / sha1 / sha256 / FNV-1 /
  FNV-1a / djb2 / crc32, három kódolással, mindkét bájtsorrenddel, a
  puszta fájlnévtől a teljes `$My Pictures\…` alakig) — **egy sem adja
  vissza** a golden uid-okat;
- a `.picasa.ini`-k `IIDLIST_<fiók>_lh` értékei MÁS azonosító-család: a
  korpusz mind a 6045 értéke `4…` prefixű (a felső 32 bit feltöltési
  időbélyeg), míg a `.cxf` uid-jai egyenletesen szórtak.

Ezért a PicasaPy **saját, determinisztikus** azonosítót képez. A cél nem
az eredeti érték eltalálása (az lehetetlen), hanem hogy a fájlunk
ALAKRA és INVARIÁNSRA az eredetihez hasonló legyen, és a mezők ne
hiányozzanak.

⚠️ Amit a PicasaPy már megnyitott fájlból olvasott, azt **nem írjuk
felül** a származtatott értékkel — a körbejárás elve (#1274) előbbre való:
a `project_from_nodes` a `node_uids` leképezésen keresztül visszaadja az
eredeti értékeket.

⚠️ **Nyitott kérdés:** hogy az eredeti Picasának SZÜKSÉGE van-e ezekre a
mezőkre a megnyitáshoz, nincs kimérve. Annyit tudunk a bináris-indexből,
hogy a `.cxf`-olvasó (`0x00832830`) az `albumUID`-ot és az `albumID`-t
**beolvassa** (a `0x008347b0` író az `albumUID`-ot, az `albumTitle`-t és
az `albumDate`-et írja) — de hogy egy általa nem ismert albumazonosítóval
mit kezd, ahhoz dekompiláció kellene. A jegy (#1092) ezt nyitva hagyja.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

#: Az `albumUID` hossza hexa karakterben (mérve: 32).
ALBUM_UID_HEX_LENGTH = 32

#: A csomópont-azonosító NEM NULLA előtagjának hossza (mérve: 16), és a
#: mögötte álló nullák száma. A 64 bites képazonosító 128 bitre töltve.
NODE_UID_PREFIX_HEX_LENGTH = 16
NODE_UID_PADDING = "0" * 16

#: Névtér-előtagok, hogy a kétféle azonosító ugyanabból a szövegből se
#: eshessen egybe. A `blake2b` azért esett a választás, mert a kimeneti
#: hossz szabadon állítható — nem kell egy hosszabb hasht csonkolni.
_ALBUM_NAMESPACE = b"picasapy/collage/album\x00"
_NODE_NAMESPACE = b"picasapy/collage/node\x00"


def album_uid_for(folder: Path | str) -> str:
    """A forrásalbum `albumUID`-ja a mappa útvonalából — 32 kisbetűs hexa.

    Üres bemenetre üres szöveg: azonosítót kitalálni olyan albumhoz, ami
    nincs, rosszabb volna a hiánynál (a `dumps` az üres mezőt egyszerűen
    nem írja ki).

    A mappa TELJES útvonalát vesszük, nem csak a nevét: két különböző
    helyen álló „Nyaralás" mappa két külön album."""
    key = str(folder).strip()
    if not key:
        return ""
    return hashlib.blake2b(
        _ALBUM_NAMESPACE + key.encode("utf-8"), digest_size=16
    ).hexdigest()


def node_uid_for(src: str) -> str:
    """Egy kép `<uid>`-ja a `.cxf`-be írt `<src>` alakjából.

    A kulcs szándékosan a FÁJLBA KERÜLŐ `src` szöveg (a #1096 óta a
    Picasa változós alakja, pl. `$My Pictures\\AI\\kep.png`), nem a
    feloldott abszolút útvonal. Így a `.cxf` **önmagában ellenőrizhető**:
    a benne álló `<src>`-ből újraszámolható a `<uid>`, és két gépen
    ugyanabból a fájlból ugyanaz az azonosító lesz.

    Üres forrásra üres szöveg — kép nélküli csomópontnak nincs mit
    azonosítani."""
    key = str(src).strip()
    if not key:
        return ""
    prefix = hashlib.blake2b(
        _NODE_NAMESPACE + key.encode("utf-8"), digest_size=8
    ).hexdigest()
    return prefix + NODE_UID_PADDING


__all__ = [
    "ALBUM_UID_HEX_LENGTH",
    "NODE_UID_PADDING",
    "NODE_UID_PREFIX_HEX_LENGTH",
    "album_uid_for",
    "node_uid_for",
]

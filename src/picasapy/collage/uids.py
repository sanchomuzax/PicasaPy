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

## Az `albumUID` eredete — NYITOTT KÉRDÉS, nem eldöntött

⚠️ **Van egy ellenőrizetlen hipotézis, és a mai anyagból nem dönthető el.**

A saját specünk (`docs/specs/picasa-create-features.md`, 1.6 táblázat) azt
állítja: az `albumUID` *„ugyanaz az album-token, mint a `[.album:<token>]`
szekcióké"*. Ezt megpróbáltam ellenőrizni, és **nem sikerült**:

- a `.picasa.ini`-korpusz (859 fájl) tartalmaz valódi
  `[.album:<32 hexa>]` szekciókat `token=` / `name=` / `date=` kulcsokkal,
  tehát az **alak stimmel**;
- a golden `albumUID` (`a4ef8e0f…`) **nincs** a korpuszban — **de a golden
  kollázsok forrásmappája (`AI`) sincs benne**, tehát a hiánya SEMMIT nem
  bizonyít, egyik irányba sem.

Amit viszont kimértem: az `IIDLIST_<fiók>_lh` **nem** ez a kulcscsalád (a
korpusz mind a 6045 értéke `4…` prefixű, a felső 32 bit feltöltési
időbélyeg), tehát a jegy eredeti feltevése — „a `.picasa.ini`-ből
kiolvasható" — ebben a formában nem áll.

A kérdés eldöntéséhez a golden kollázsok forrásmappájának `.picasa.ini`-je
kellene. Amíg nincs meg, a lenti származtatás **IDEIGLENES**.

## SAJÁT FUNKCIÓ (#1092): ideiglenes, determinisztikus származtatás

A csomópont-`<uid>`-ra az eredeti érték a Picasa BELSŐ adatbázisából jön
(az `imagedata` rekord `uid64` mezője, ld.
`docs/specs/picasa-imagedata-rekord.md`), és lemértem a szokásos
útvonal-hasheket (md5 / sha1 / sha256 / FNV-1 / FNV-1a / djb2 / crc32,
három kódolással, mindkét bájtsorrenddel, a puszta fájlnévtől a teljes
`$My Pictures\…` alakig) — **egy sem** adja vissza a golden uid-okat.

Ezért a PicasaPy **saját, determinisztikus** azonosítót képez mindkét
mezőre. A cél nem az eredeti érték eltalálása, hanem hogy a fájlunk
ALAKRA és INVARIÁNSRA az eredetihez hasonló legyen, és a mezők ne
hiányozzanak. **Ha a token-hipotézis beigazolódik, az `album_uid_for`
helyére a forrásmappa `.picasa.ini`-jéből olvasott token lép** — a
származtatás akkor is kell marad, tokent nem tartalmazó mappákra.

⚠️ Amit a PicasaPy már megnyitott fájlból olvasott, azt **nem írjuk
felül** a származtatott értékkel — a körbejárás elve (#1274) előbbre való:
a `project_from_nodes` a `node_uids` leképezésen keresztül visszaadja az
eredeti értékeket.

⚠️ **Nyitott kérdés:** hogy az eredeti Picasának SZÜKSÉGE van-e ezekre a
mezőkre a megnyitáshoz, és hogy egy általa nem ismert albumazonosítóval
mit kezd, nincs kimérve — a tulajdonos windowsos próbájára vár (#1390).
Annyit tudunk a bináris-indexből, hogy a `.cxf`-olvasó (`0x00832830`) az
`albumUID`-ot és az `albumID`-t **beolvassa** (a `0x008347b0` író az
`albumUID`-ot, az `albumTitle`-t és az `albumDate`-et írja).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

#: Az `albumUID` hossza hexa karakterben (mérve: 32).
ALBUM_UID_HEX_LENGTH = 32

#: A csomópont-azonosító NEM NULLA előtagjának hossza (mérve: 16), és a
#: mögötte álló nullák száma. A 64 bites képazonosító 128 bitre töltve.
NODE_UID_PREFIX_HEX_LENGTH = 16
NODE_UID_PADDING = "0" * 16

#: Névtér-előtagok, hogy a kétféle azonosító ugyanabból a szövegből se
#: eshessen egybe. A `blake2b`-re azért esett a választás, mert a kimeneti
#: hossz szabadon állítható — nem kell egy hosszabb hasht csonkolni.
_ALBUM_NAMESPACE = b"picasapy/collage/album\x00"
_NODE_NAMESPACE = b"picasapy/collage/node\x00"


def album_uid_for(folder: Path | str) -> str:
    """A forrásalbum `albumUID`-ja a mappa útvonalából — 32 kisbetűs hexa.

    Üres bemenetre üres szöveg: azonosítót kitalálni olyan albumhoz, ami
    nincs, rosszabb volna a hiánynál (a `dumps` az üres mezőt egyszerűen
    nem írja ki).

    A mappa TELJES útvonalát vesszük, nem csak a nevét: két különböző
    helyen álló „Nyaralás" mappa két külön album.

    ⚠️ Az útvonalat a platform szabályai szerint normalizáljuk
    (`normpath` + `normcase`), mert nyers szövegként Windowson a
    `C:\\Kepek\\AI` és a `C:\\kepek\\ai` **két különböző azonosítót**
    adna ugyanarra az albumra — a mért invariáns (egy forrásalbum → egy
    `albumUID`) pont ezen bukna el. Ugyanez a normalizálás védi a
    záró perjelet és a `..` szakaszokat is. Linuxon a `normcase`
    azonosság, tehát a kis-nagybetű ott továbbra is számít — helyesen,
    mert ott két külön mappáról van szó."""
    text = str(folder).strip()
    if not text:
        return ""
    key = os.path.normcase(os.path.normpath(text))
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

    ⚠️ Itt SZÁNDÉKOSAN nincs `normcase`/`normpath`: a `src` nem
    útvonalként, hanem a fájlba írt SZÖVEGKÉNT azonosít. Aki a `.cxf`-ből
    újraszámolja, pontosan azt a szöveget látja, ami ott áll — egy
    normalizálás ezt az ellenőrizhetőséget vinné el.

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

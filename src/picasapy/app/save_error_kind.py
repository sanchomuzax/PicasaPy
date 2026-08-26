"""#1527: a mentés hibáinak besorolása a HÁROM hivatalos üzenet-ágra.

Az eredeti Picasa a mentés-hibát nem egyetlen szöveggel intézi el: három
külön üzenete van, és a legsúlyosabb (a lemezhiba) **kiírja a fájlnevet és
a hibakódot** is (`stringres-en-hu.tsv`, megerősített):

| kulcs | ág | magyar |
|---|---|---|
| `CFileSaveThread:filesaveerr2` | `COLLISION` | „A fájl mentése nem lehetséges. Már van ilyen nevű fájl." |
| `CFileSaveThread:filesaveerr3` | `FORMAT` | „Fájlformázási hiba miatt a fájl nem menthető." |
| `CFileSaveThread::filesaveerr-win` | `DISK` | „Lemezhiba miatt nem lehetséges az összes fájl mentése. …\n\n%1$s\nhiba(%2$d)" |

Plusz egy negyedik, a MÁSOLAT-ág saját azonosság-ellenőrzése:
`IDS_CANT_SAVE_TO_SAME` → „A képet nem lehet kicserélni. Próbálja újra
másik fájlnévvel." (`SAME`).

**Miért külön modul.** A besorolás tiszta függvény: kivétel be, ág ki. Így
tesztelhető QML és Qt nélkül, és a controller nem hízik tovább. A
felhasználónak látszó SZÖVEG nem itt él, hanem a QML-ben (`SaveDialogs`) —
ez a modul csak azt mondja meg, MELYIK ágról van szó.
"""

from __future__ import annotations

import errno as _errno

from picasapy.edit.save import SaveError
from picasapy.edit.save_copy import FileNameCollisionError
from picasapy.ini import IniConflictError, IniSaveError

#: névütközés — a cél már létezik (`filesaveerr2`)
KIND_COLLISION = "collision"
#: a cél AZONOS a forrással (`IDS_CANT_SAVE_TO_SAME`)
KIND_SAME = "same"
#: a kép nem kódolható a cél formátumába (`filesaveerr3`)
KIND_FORMAT = "format"
#: lemezhiba: tele lemez, írásvédettség, zárolás (`filesaveerr-win`)
KIND_DISK = "disk"

#: A `FileNameCollisionError` üzenetébe a `save_copy` ezt írja, ha a cél a
#: forrás — a két ág üzenete más, a kivétel-osztály viszont közös
#: (adatbiztonsági szempontból mindkettő ugyanaz: NEM írunk felül).
_SAME_MARKER = "azonos a forrással"


def save_error_kind(error: BaseException) -> str:
    """A kivételhez tartozó hivatalos hibaág azonosítója.

    A sorrend számít: a névütközés a `SaveError` leszármazottja, tehát
    előbb kell megvizsgálni, mint az általános formátum-hibát.
    """
    if isinstance(error, FileNameCollisionError):
        return KIND_SAME if _SAME_MARKER in str(error) else KIND_COLLISION
    if isinstance(error, FileExistsError):
        return KIND_COLLISION
    if isinstance(error, (OSError, IniSaveError, IniConflictError)):
        return KIND_DISK
    if isinstance(error, (SaveError, ValueError)):
        return KIND_FORMAT
    return KIND_DISK


def save_error_code(error: BaseException) -> int:
    """A `filesaveerr-win` `%2$d` helyére kerülő hibakód.

    `OSError`-nál a rendszer `errno`-ja; minden más ágon 0 — a hivatalos
    üzenet ezt a mezőt csak a lemezhiba-ágon jeleníti meg, tehát ott is
    csak akkor ír számot, ha a rendszer adott egyet.
    """
    kod = getattr(error, "errno", None)
    if isinstance(kod, int):
        return kod
    # Az ini-réteg saját hibái nem hoznak errno-t; a lemez tele/írásvédett
    # eset a leggyakoribb ok, de TALÁLGATNI nem szabad — 0 = „nincs kód".
    if isinstance(error, (IniSaveError, IniConflictError)):
        return 0
    return getattr(_errno, "EIO", 5) if isinstance(error, OSError) else 0

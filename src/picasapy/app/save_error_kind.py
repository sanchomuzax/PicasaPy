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
#: lemezhiba másolat mentésekor (`FileSaveCopy:err`) - #6977
KIND_COPY_DISK = "copy_disk"

#: A `FileNameCollisionError` üzenetébe a `save_copy` ezt írja, ha a cél a
#: forrás — a két ág üzenete más, a kivétel-osztály viszont közös
#: (adatbiztonsági szempontból mindkettő ugyanaz: NEM írunk felül).
_SAME_MARKER = "azonos a forrással"


def save_error_kind(error: BaseException, *, is_copy: bool = False) -> str:
    """A kivételhez tartozó hivatalos hibaág azonosítója.

    A sorrend számít: a névütközés a `SaveError` leszármazottja, tehát
    előbb kell megvizsgálni, mint az általános formátum-hibát.
    """
    if isinstance(error, FileNameCollisionError):
        return KIND_SAME if _SAME_MARKER in str(error) else KIND_COLLISION
    if isinstance(error, FileExistsError):
        return KIND_COLLISION
    if isinstance(error, (OSError, IniSaveError, IniConflictError)):
        return KIND_COPY_DISK if is_copy else KIND_DISK
    if isinstance(error, (SaveError, ValueError)):
        return KIND_FORMAT
    return KIND_COPY_DISK if is_copy else KIND_DISK


#: Az eredeti Picasa belső státuszai a lemezhiba-ablak `hiba(%d)` mezőjében
#: (#7449). A `0x0099cd30` a Windows-hibakódot képezi le erre; mérve: az
#: írásvédett cél mentési hibája `error(11)` (`job-957`).
STATUS_ACCESS_DENIED = 11
STATUS_NOT_FOUND = 10
#: minden le nem képezett hibakód (az eredeti alapága)
STATUS_OTHER = 2

#: a hozzáférés-hibák rendszerszintű kódjai (`PermissionError` is ide tartozik)
_ACCESS_ERRNOS = frozenset({_errno.EACCES, _errno.EPERM, _errno.EROFS})
#: ERROR_ACCESS_DENIED, ERROR_SHARING_VIOLATION
_ACCESS_WINERRORS = frozenset({5, 32})
#: ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND
_NOT_FOUND_WINERRORS = frozenset({2, 3})
#: ERROR_DISK_FULL
_DISK_FULL_WINERROR = 112


def _is_disk_full(error: OSError) -> bool:
    return (
        getattr(error, "errno", None) == _errno.ENOSPC
        or getattr(error, "winerror", None) == _DISK_FULL_WINERROR
    )


def _is_access_denied(error: OSError) -> bool:
    return (
        isinstance(error, PermissionError)
        or getattr(error, "errno", None) in _ACCESS_ERRNOS
        or getattr(error, "winerror", None) in _ACCESS_WINERRORS
    )


def _is_not_found(error: OSError) -> bool:
    return (
        isinstance(error, FileNotFoundError)
        or getattr(error, "errno", None) == _errno.ENOENT
        or getattr(error, "winerror", None) in _NOT_FOUND_WINERRORS
    )


def save_error_code(error: BaseException) -> int:
    """A `filesaveerr-win` `%2$d` helyére kerülő hibakód (#7449).

    Az eredeti Picasa itt NEM a rendszer `errno`-ját írja ki, hanem a saját
    belső státuszát: hozzáférés-hiba (`PermissionError`, `EACCES`, `EPERM`,
    `EROFS`, Windowson `winerror` 5 vagy 32) -> 11; hiányzó fájl vagy út
    (`FileNotFoundError`, `ENOENT`, `winerror` 2 vagy 3) -> 10; minden más
    le nem képezett `OSError` -> 2.

    A tele lemez (`ENOSPC`, `winerror` 112) belső státusza NINCS MEG (#7428:
    12 vagy 2, attól függ, melyik úton fogy el a hely), ezért az továbbra is
    az `errno` marad, amíg a mérés el nem dönti.

    Nem `OSError`-nál (ini-hibák, formátumhiba) 0 - a hivatalos üzenet ezt
    a mezőt csak a lemezhiba-ágon jeleníti meg, és ott sem TALÁLGATUNK
    kódot: 0 = „nincs kód".
    """
    if not isinstance(error, OSError):
        return 0
    if _is_disk_full(error):
        return _errno.ENOSPC
    if _is_access_denied(error):
        return STATUS_ACCESS_DENIED
    if _is_not_found(error):
        return STATUS_NOT_FOUND
    return STATUS_OTHER

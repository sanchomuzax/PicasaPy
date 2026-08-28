"""Új mappa létrehozása a kijelölt képek áthelyezéséhez (#1614).

A Fájl ▸ „Áthelyezés új mappába…" (`eMenuFile::ID_FILE_NEWFOLDER`) az
eredetiben — a hivatalos magyar felirat szerint — a kijelölt képeket egy
ÚJ mappába helyezi át. A tényleges mozgatás a MEGLÉVŐ kötegelt úton megy
(`picasapy.fileops.batch.move_photos`) — ez a modul csak azt a lépést adja
hozzá, ami ott hiányzik: a felhasználó által megadott NÉVBŐL a célmappa
létrehozását, a névvel szemben szükséges ellenőrzéssel.

A névellenőrzés PLATFORMFÜGGETLEN: a projekt kétirányú Windows-kompat célt
követ (ld. CLAUDE.md, `.picasa.ini` round-trip), ezért a Windows-tiltott
fájlnév-karaktereket (`<>:"/\\|?*`) Linuxon futva IS tiltjuk, nem csak a
ténylegesen futó rendszeren — egy Linuxon létrehozott mappa, aminek a neve
Windowson érvénytelen, a NAS-on át futó eredeti Picasa (vagy egy Windowsra
átvitt könyvtár) számára használhatatlan volna (#1700 ugyanezt a
hibaosztályt fogta meg egy tesztnél).
"""

from __future__ import annotations

import re
from pathlib import Path

#: Windows tiltott fájl-/mappanév-karakterei. A `/` és a `\\` a
#: elérésiút-elválasztók is — ezek tiltása egyúttal azt is kizárja, hogy a
#: mappanév véletlenül (vagy szándékosan) egy MÁSIK könyvtárba mutasson.
_TILTOTT_KARAKTEREK = '<>:"/\\|?*'
_TILTOTT_MINTA = re.compile("[" + re.escape(_TILTOTT_KARAKTEREK) + "]")


class InvalidFolderNameError(ValueError):
    """A megadott mappanév nem használható — emberi nyelvű üzenettel."""


def validate_folder_name(name: str) -> str:
    """A `name` mappanév ellenőrzése; a levágott (trimmelt) alak a
    visszatérési érték, ha érvényes.

    Args:
        name: a felhasználó által beírt mappanév (a dialógus mezőjének
            nyers szövege — a szélén álló szóközökkel).

    Returns:
        A `name.strip()` — ez a tényleges mappanév, amivel a hívó
        `create_folder_for_move`-ot hívhatja.

    Raises:
        InvalidFolderNameError: ha a levágott név üres (a mező üres volt,
            vagy csak szóközt tartalmazott), vagy Windows-tiltott
            karaktert tartalmaz (`<>:"/\\|?*`).
    """
    trimmed = name.strip()
    if not trimmed:
        raise InvalidFolderNameError("A mappanév nem lehet üres.")
    talalat = _TILTOTT_MINTA.search(trimmed)
    if talalat is not None:
        raise InvalidFolderNameError(
            f"A mappanév nem tartalmazhatja ezt a karaktert: „{talalat.group()}”."
        )
    return trimmed


def create_folder_for_move(parent: Path, name: str) -> Path:
    """Új, üres mappa létrehozása a `parent` alatt, `name` névvel (#1614).

    A hívó felelőssége, hogy `name`-et előtte `validate_folder_name`-mel
    ellenőrizze — ez a függvény a NEVET nem vizsgálja, csak a lemezi
    állapotot.

    Args:
        parent: a szülőmappa — a kijelölt képek (első elemének) jelenlegi
            mappája; oda kerül az új almappa.
        name: az érvényesített mappanév.

    Returns:
        Az új mappa elérési útja.

    Raises:
        FileExistsError: ha a célmappa (vagy egy azonos nevű fájl) már
            létezik — nem írjuk felül csendben.
        OSError: egyéb fájlrendszeri hiba (pl. jogosultság).
    """
    parent = Path(parent)
    target = parent / name
    if target.exists():
        raise FileExistsError(f"Már létezik ilyen nevű mappa: {target}")
    target.mkdir()
    return target


__all__ = [
    "InvalidFolderNameError",
    "create_folder_for_move",
    "validate_folder_name",
]

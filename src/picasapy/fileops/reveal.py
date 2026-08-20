r"""A fájlt tartalmazó mappa megnyitása a rendszer fájlkezelőjében (#15, #112).

## Platformonként MÁS parancs (#1104)

A modul korábban platform-ág nélkül `xdg-open`-t hívott. A program viszont
**fut Windowson is**, és ott ez nem hiba-ág volt, hanem
**működésképtelenség** — a tulajdonos hibaüzenete (v0.8.23, Windows 11):

```
A fájlkezelő megnyitása sikertelen (xdg-open hiányzik?):
C:\Users\…\Képek\Picasa\Kollázsok
```

| platform | mappa | fájl kijelölve |
|---|---|---|
| Windows | `explorer "<mappa>"` | `explorer /select,"<fájl>"` |
| macOS | `open "<mappa>"` | `open -R "<fájl>"` |
| Linux | `xdg-open "<mappa>"` | — (a mappát nyitjuk) |

**Linuxon a viselkedés változatlan.** A konkrét fájl kijelölésére ott nincs
egységes freedesktop-szabvány, ezért marad a szülőmappa megnyitása; a másik
két platformon viszont a rendszer maga tudja kijelölni, és a „Keresés a
lemezen" eredeti szándéka épp ez.

## ⚠️ Az `explorer` kilépési kódja NEM jelent hibát

Az `explorer.exe` **nemnulla** kóddal tér vissza akkor is, ha a mappa
rendben megnyílt — jól ismert Windows-viselkedés. A korábbi
„`returncode != 0` → `OSError`" szabály ezért Windowson **hamis
hibaüzenetet** adna a sikeres megnyitásra is. A kilépési kódot ott
szándékosan nem vizsgáljuk; a hiányzó bináris (`OSError`) továbbra is
hibára fordul.

## ⚠️ A `/select,` EGYETLEN argumentum

Az `explorer /select,<út>` alakot az Intéző **egy** argumentumként várja,
a vessző után **szóköz nélkül**. A `subprocess` listás alakja a szóközös,
ékezetes útvonalat (`OneDrive - centralmediacsoport\Képek`) így is
helyesen adja át.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

_log = logging.getLogger(__name__)


def _windows() -> bool:
    return sys.platform.startswith("win")


def _macos() -> bool:
    return sys.platform == "darwin"


def _parancs(cel: Path, *, kijelol: bool) -> list[str]:
    """A platform szerinti parancssor.

    `kijelol=True` a „mutasd a fájlt" szándék: ahol a rendszer tudja, ott a
    fájlt ki is jelöljük, egyébként a mappát nyitjuk."""
    if _windows():
        # a vessző után NINCS szóköz, és az egész EGY argumentum
        return ["explorer", f"/select,{cel}"] if kijelol else ["explorer", str(cel)]
    if _macos():
        return ["open", "-R", str(cel)] if kijelol else ["open", str(cel)]
    return ["xdg-open", str(cel)]


def _inditsd(parancs: list[str], cel: Path) -> None:
    """A parancs futtatása, egységes hibaágakkal.

    A kilépési kódot **Windowson nem** vizsgáljuk (ld. a modul
    docstringjét); mindenhol máshol a nemnulla kód hibát jelent, hogy a
    hívó (`FileOpsController`) az `operationFailed` jelzésre fordíthassa —
    a felhasználó ne maradjon néma némaságban (#112)."""
    try:
        result = subprocess.run(parancs, check=False)
    except OSError as error:
        _log.warning("A fájlkezelő megnyitása sikertelen: %s", cel)
        raise OSError(
            f"A fájlkezelő megnyitása sikertelen ({parancs[0]} hiányzik?): {cel}"
        ) from error
    if _windows():
        # az explorer sikeres megnyitásnál is nemnulla kóddal tér vissza
        return
    if result.returncode != 0:
        _log.warning(
            "A fájlkezelő megnyitása nemnulla kilépési kóddal tért vissza (%s): %s",
            result.returncode,
            cel,
        )
        raise OSError(
            f"A fájlkezelő megnyitása sikertelen (kilépési kód: "
            f"{result.returncode}): {cel}"
        )


def reveal_in_file_manager(path: Path) -> None:
    """A `path` fájl megmutatása a fájlkezelőben (#15, #112, #1104).

    Windowson és macOS-en a fájl **ki is jelölődik**; linuxon a szülőmappa
    nyílik meg (ott nincs egységes szabvány a kijelölésre).

    Hiányzó fájlkezelő-bináris esetén `OSError`-t emel, hogy a hívó
    (`FileOpsController`) az `operationFailed` jelzésre tudja fordítani."""
    cel = Path(path)
    if _windows() or _macos():
        _inditsd(_parancs(cel, kijelol=True), cel)
        return
    open_folder_in_file_manager(cel.parent)


def open_folder_in_file_manager(folder: Path) -> None:
    """MAGÁNAK a mappának a megnyitása a fájlkezelőben (#422, #1104).

    A `reveal_in_file_manager` fájlra van szabva: a kapott út SZÜLŐJÉT
    nyitja (linuxon). A mappa-kontextusmenü „Keresés a lemezen" tételéhez
    viszont a mappa saját tartalma kell — ez a függvény azt nyitja meg."""
    cel = Path(folder)
    _inditsd(_parancs(cel, kijelol=False), cel)

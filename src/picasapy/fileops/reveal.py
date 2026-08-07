"""A fájlt tartalmazó mappa megnyitása a rendszer fájlkezelőjében (#15, #112).

Linux-first (CLAUDE.md): az `xdg-open`-t hívja a szülőmappára — a konkrét
fájl kijelölése fájlkezelőnként eltérő (nincs rá egységes freedesktop-
szabvány), ezért az MVP a mappa megnyitására szorítkozik.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

_log = logging.getLogger(__name__)


def reveal_in_file_manager(path: Path) -> None:
    """A `path` fájlt tartalmazó mappa megnyitása a fájlkezelőben.

    Hiányzó `xdg-open` bináris vagy nemnulla kilépési kód esetén `OSError`-t
    emel, hogy a hívó (pl. `FileOpsController`) az `operationFailed`
    jelzésre tudja fordítani — a felhasználó ne néma némaságban maradjon,
    ha a fájlkezelő megnyitása sikertelen (#112)."""
    open_folder_in_file_manager(Path(path).parent)


def open_folder_in_file_manager(folder: Path) -> None:
    """MAGÁNAK a mappának a megnyitása a fájlkezelőben (#422).

    A `reveal_in_file_manager` fájlra van szabva: a kapott út SZÜLŐJÉT
    nyitja. A mappa-kontextusmenü „Keresés a lemezen" tételéhez viszont a
    mappa saját tartalma kell — ez a függvény azt nyitja meg. A hibaágak
    (hiányzó `xdg-open`, nemnulla kilépési kód) azonosak, ld. ott."""
    folder = Path(folder)
    try:
        result = subprocess.run(["xdg-open", str(folder)], check=False)
    except OSError as error:
        _log.warning("A fájlkezelő megnyitása sikertelen: %s", folder)
        raise OSError(
            f"A fájlkezelő megnyitása sikertelen (xdg-open hiányzik?): {folder}"
        ) from error
    if result.returncode != 0:
        _log.warning(
            "A fájlkezelő megnyitása nemnulla kilépési kóddal tért vissza "
            "(%s): %s",
            result.returncode,
            folder,
        )
        raise OSError(
            f"A fájlkezelő megnyitása sikertelen (kilépési kód: "
            f"{result.returncode}): {folder}"
        )

"""A fájlt tartalmazó mappa megnyitása a rendszer fájlkezelőjében (#15).

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

    Hiányzó `xdg-open` vagy futtatási hiba esetén csak naplóz — a művelet
    nem kritikus, nem szabad a felhasználói élményt egy hiányzó desktop-
    integráció miatt megszakítani."""
    folder = Path(path).parent
    try:
        subprocess.run(["xdg-open", str(folder)], check=False)
    except OSError:
        _log.warning("A fájlkezelő megnyitása sikertelen: %s", folder)

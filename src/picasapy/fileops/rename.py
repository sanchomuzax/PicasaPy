"""Fájl átnevezése a lemezen — a .picasa.ini szekció követi (#15).

Round-trip elv: a szekció tartalma (star/caption/rotate/filters/… és minden
ismeretlen sor) bitre pontosan megmarad, csak a `[fájlnév]` fejléc változik.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.ini import load_document, save_document
from picasapy.scanner import PICASA_INI_NAME


def rename_photo(path: Path, new_name: str) -> Path:
    """A `path` fájl átnevezése `new_name`-re, ugyanabban a mappában.

    Args:
        path: Az átnevezendő fájl jelenlegi elérési útja.
        new_name: Az új fájlnév (csak név, elérési út elem nélkül).

    Returns:
        Az új elérési út.

    Raises:
        ValueError: Ha `new_name` üres vagy elérési út elemet tartalmaz.
        FileNotFoundError: Ha `path` nem létezik.
        FileExistsError: Ha a célnév (fájl vagy ini-szekció) már foglalt.
    """
    path = Path(path)
    _validate_name(new_name)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")
    target = path.with_name(new_name)
    if target.exists():
        raise FileExistsError(f"A célnév már foglalt: {target}")

    ini_path = path.parent / PICASA_INI_NAME
    document = load_document(ini_path) if ini_path.exists() else None
    if document is not None and document.section(new_name) is not None:
        raise FileExistsError(f"A célnév ini-szekciója már foglalt: {new_name}")

    path.rename(target)

    if document is not None:
        renamed = document.with_renamed_section(path.name, new_name)
        save_document(renamed, ini_path, backup=True)

    return target


def _validate_name(name: str) -> None:
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError(f"Érvénytelen fájlnév: {name!r}")

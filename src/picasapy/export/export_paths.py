"""Célmappa-ürítés és ütközésmentes exportfájlnevek."""

from __future__ import annotations

import shutil
from pathlib import Path


class _PurgeError(Exception):
    """Az ürítés hibája — a fajtáját (`delete`/`remove`/`scan`) a
    `_purge_target` adja, hogy a hívó az eredeti üzenetet válassza."""


def _purge_target(target_dir: Path) -> str:
    """A célmappa KIÜRÍTÉSE — az eredeti „igen, felülírom" ága (#1166).

    `CExportPrefsPage::destexists` („A cél már létezik. Felülírja az új
    albummal?") — igen esetén a program az ELŐZŐ albumot törli, nem
    mellé exportál.

    ⚠️ Csak a célmappa TARTALMÁT törli, magát a mappát nem, és sosem lép
    ki belőle. Nem létező mappánál nem csinál semmit; ha a cél egy fájl,
    érintetlenül hagyja — a hívó a `mkdir` hibáján át kap jelzést
    (`IDS_DESTDIRCANNOCREATE`)."""
    if not target_dir.is_dir():
        return ""
    try:
        entries = tuple(target_dir.iterdir())
    except OSError:
        # a cél LETAPOGATÁSA bukott — `CExportPrefsPage::scanerror`
        return "scan"
    for entry in entries:
        try:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)      # `::removeerror` tartománya
            else:
                entry.unlink()            # `::deleteerror` tartománya
        except OSError:
            return "remove" if entry.is_dir() else "delete"
    return ""

def _unique_target(target_dir: Path, stem: str, suffix: str) -> Path:
    """Ütközésmentes célnév: `név.jpg`, `név-1.jpg`, `név-2.jpg`, ..."""
    candidate = target_dir / f"{stem}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = target_dir / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate

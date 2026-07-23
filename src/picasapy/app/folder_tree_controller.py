"""FolderTreeController: a Mappakezelő fa-nézetének háttér-adatforrása
(#231) — a helyi fájlrendszer mappastruktúráját LUSTÁN, csak a kinyitott
szint gyermekeit olvasva szolgáltatja a QML-nek.

Szándékosan ÖNÁLLÓ QObject, a `discovery_controller.py` mintáját követve:
NEM az `AppController` mixinje, a `controller.py`/`Main.qml` forró fájlok
(CONTRIBUTING.md) csak a végső bekötést kapják. A listázás HÁTTÉRSZÁLON
fut (NAS-mounton vagy sok fájlt tartalmazó könyvtárban lassú lehet) — ez
NEM blokkolhatja a GUI-szálat; az eredményt a `childrenLoaded` jelzi, amit
a Qt automatikusan a GUI-szálra sorol (a `LibraryMixin` háttér-szinkronjának
mintája, ld. library_controller.py docsztringje)."""

from __future__ import annotations

import os
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot


def _has_subdirectory(path: Path) -> bool:
    """Van-e legalább egy (rejtett, nem-szimlink) almappa — csak a fa
    kinyitó-nyilának megjelenítéséhez, a teljes tartalom listázása
    nélkül (első találatnál megáll)."""
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.name.startswith("."):
                    continue
                try:
                    if entry.is_dir(follow_symlinks=False):
                        return True
                except OSError:
                    continue
    except OSError:
        pass
    return False


def _list_children(path: Path) -> list[dict]:
    """Egy szint közvetlen almappái, név szerint rendezve.

    Rejtett (ponttal kezdődő) bejegyzések és szimbolikus linkek kimaradnak
    (a szimlink-kihagyás körkörös hivatkozási hurkot előz meg). Olvasási
    hiba (jogosultság, eltűnt mappa) esetén üres lista — nem hiba, a fa
    egyszerűen üresen mutatja azt az ágat."""
    try:
        with os.scandir(path) as entries:
            raw = list(entries)
    except OSError:
        return []
    children: list[dict] = []
    for entry in raw:
        if entry.name.startswith("."):
            continue
        try:
            if not entry.is_dir(follow_symlinks=False):
                continue
        except OSError:
            continue
        child_path = str(Path(path) / entry.name)
        children.append(
            {
                "name": entry.name,
                "path": child_path,
                "hasChildren": _has_subdirectory(Path(child_path)),
            }
        )
    children.sort(key=lambda item: item["name"].lower())
    return children


class FolderTreeController(QObject):
    """A `FolderManagerDialog.qml` fa-nézetének háttér-hídja."""

    # (a lekérdezett mappa útvonala, a közvetlen almappák listája — dict-ek:
    # name/path/hasChildren)
    childrenLoaded = Signal(str, list)

    @Slot(str)
    def requestChildren(self, path: str) -> None:
        """Egy mappa közvetlen almappáinak lekérése HÁTTÉRSZÁLON — a hívás
        azonnal visszatér, az eredmény a `childrenLoaded` jelzésben érkezik
        (a Qt automatikusan a GUI-szálra sorolja)."""
        target = str(path)

        def worker() -> None:
            children = _list_children(Path(target))
            self.childrenLoaded.emit(target, children)

        threading.Thread(target=worker, daemon=True).start()

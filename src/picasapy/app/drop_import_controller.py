"""DropImportController (#237): képet/mappát az ablakra ejtve importálás.

Picasa-viselkedés: egy képet az alkalmazásra húzva a kép SZÜLŐMAPPÁJA kerül
a figyelt gyökerek közé (így a mappa többi képe is bejön), mappát ejtve maga
a mappa. Több elemnél a szülőmappák deduplikálva adódnak hozzá; egymásba
ágyazott utaknál a legfelső elég. Nem támogatott elemről rövid, emberi
nyelvű visszajelzés megy (nem néma).

Szándékosan ÖNÁLLÓ QObject, NEM az `AppController` mixinje (a
`discovery_controller.py` mintája): a `controller.py`/`Main.qml` forró
fájlok — a Main.qml csak az `ImportDropArea` ráhelyezését kapja az
integrátortól, a logika itt, tőlük függetlenül él és tesztelhető.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.scanner import media_kind_of

from .formatting import to_local_path


def _is_inside(path: Path, ancestor: Path) -> bool:
    """Igaz, ha `path` az `ancestor` alatt van (vagy azonos vele)."""
    try:
        return path == ancestor or path.is_relative_to(ancestor)
    except (OSError, ValueError):
        return False


def _topmost_only(folders: Iterable[Path]) -> tuple[Path, ...]:
    """Egymásba ágyazott mappákból csak a legfelsők — a figyelt gyökér a
    teljes fáját szkenneli, az almappa külön felvétele felesleges."""
    unique = list(dict.fromkeys(folders))
    return tuple(
        folder
        for folder in unique
        if not any(
            other != folder and _is_inside(folder, other) for other in unique
        )
    )


def folders_of_dropped_urls(
    urls: Iterable[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """A ráejtett URL-ekből a hozzáadandó mappák és az elutasított elemek.

    Eredmény: (mappa-útvonalak, elutasított elemek fájlnevei) — a mappák
    deduplikálva, egymásba ágyazottaknál csak a legfelső; elutasított a nem
    létező út és a nem Picasa-média fájl.
    """
    folders: list[Path] = []
    rejected: list[str] = []
    for url in urls:
        text = to_local_path(str(url))
        if not text:
            continue
        path = Path(text)
        if path.is_dir():
            folders.append(path)
        elif path.is_file() and media_kind_of(path.name) is not None:
            folders.append(path.parent)
        else:
            rejected.append(path.name)
    return (
        tuple(str(folder) for folder in _topmost_only(folders)),
        tuple(rejected),
    )


class DropImportController(QObject):
    """Az `ImportDropArea.qml` hídja: drop-URL-ek → figyelt mappák."""

    # rövid, emberi nyelvű visszajelzés az elutasított elemekről —
    # az ImportDropArea buborékja mutatja
    dropRejected = Signal(str)

    def __init__(
        self,
        add_folder: Callable[[str], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._add_folder = add_folder

    @Slot(list)
    def importDroppedUrls(self, urls: list) -> None:
        """A ráejtett elemek importja a meglévő `addWatchedFolder` úton
        (ismételhetően; a duplikátum-szűrés ott történik). Az elutasított
        elemekről a `dropRejected` ad hírt."""
        folders, rejected = folders_of_dropped_urls(urls)
        for folder in folders:
            self._add_folder(folder)
        if rejected:
            names = ", ".join(rejected[:3])
            if len(rejected) > 3:
                names += "…"
            self.dropRejected.emit(
                self.tr("Not added (not a picture or folder): %1").replace(
                    "%1", names
                )
            )
        elif not folders:
            self.dropRejected.emit(
                self.tr("Drop pictures or folders here to add them.")
            )

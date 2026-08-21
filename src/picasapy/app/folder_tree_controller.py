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
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, Signal, Slot

from picasapy.paths import normalize_path

from .worker_thread import BackgroundWorkerMixin


def _has_subdirectory(path: Path) -> bool:
    """Van-e legalább egy (nem-szimlink) almappa — csak a fa
    kinyitó-nyilának megjelenítéséhez, a teljes tartalom listázása
    nélkül (első találatnál megáll)."""
    try:
        with os.scandir(path) as entries:
            for entry in entries:
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

    A rejtett mappák is látszanak; csak a szimbolikus linkek maradnak ki
    (ez a körkörös hivatkozási hurkot előzi meg). Olvasási
    hiba (jogosultság, eltűnt mappa) esetén üres lista — nem hiba, a fa
    egyszerűen üresen mutatja azt az ágat."""
    try:
        with os.scandir(path) as entries:
            raw = list(entries)
    except OSError:
        return []
    children: list[dict] = []
    for entry in raw:
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


def _root_entries(home: Path | None = None, user: str | None = None) -> list[dict]:
    """A Picasa-sorrendű fa-gyökerek Linuxon.

    A három felhasználói gyökér akkor is megjelenik, ha az XDG mappa még
    nem létezik. A csatolások felsorolása háttérszálon fut; egy eltűnt vagy
    olvashatatlan mount egyszerűen nem akasztja meg a dialógust.
    """
    home = home or Path.home()
    user = user or os.environ.get("USER", home.name)
    # ⚠️ #1200/9: a gyökerek neve HONOSÍTVA jelenjen meg — magyar
    # felületen az „Asztal"/„Képek"/„Dokumentumok" a helyes, nem az angol
    # mappanév.
    #
    # A nevet NEM mi fordítjuk: a `QStandardPaths.displayName()` a
    # RENDSZERTŐL kéri el, tehát pontosan azt adja, amit a felhasználó a
    # fájlkezelőjében is lát (Windowson a Known Folder honosított neve, ld.
    # a #1088 tanulságát a Képek mappáról). Ha nem ad nevet, marad az
    # angol mappanév — látható tartalék, nem néma hiba.
    def _honos(hely: QStandardPaths.StandardLocation, tartalek: str) -> str:
        try:
            nev = QStandardPaths.displayName(hely)
        except Exception:  # noqa: BLE001 - a névadás sosem akaszthatja meg a fát
            return tartalek
        return nev or tartalek

    candidates: list[tuple[str, Path]] = [
        (
            _honos(QStandardPaths.StandardLocation.DesktopLocation, "Desktop"),
            home / "Desktop",
        ),
        (
            _honos(QStandardPaths.StandardLocation.PicturesLocation, "Pictures"),
            home / "Pictures",
        ),
        (
            _honos(QStandardPaths.StandardLocation.DocumentsLocation, "Documents"),
            home / "Documents",
        ),
        ("/", Path("/")),
    ]
    for mount_parent in (Path("/media") / user, Path("/run/media") / user):
        try:
            candidates.extend((path.name, path) for path in mount_parent.iterdir())
        except OSError:
            continue

    result: list[dict] = []
    seen: set[str] = set()
    for name, path in candidates:
        normalized = normalize_path(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append({"name": name, "path": normalized, "hasChildren": True})
    return result


class FolderTreeController(BackgroundWorkerMixin, QObject):
    """A `FolderManagerDialog.qml` fa-nézetének háttér-hídja."""

    # (a lekérdezett mappa útvonala, a közvetlen almappák listája — dict-ek:
    # name/path/hasChildren)
    childrenLoaded = Signal(str, list)
    rootsLoaded = Signal(list)

    @Slot()
    def requestRoots(self) -> None:
        """Asztal/Képek/Dokumentumok és csatolt kötetek, háttérszálon."""

        def worker() -> None:
            self.rootsLoaded.emit(_root_entries())

        self._start_background(worker, name="picasapy-foldertree-roots")

    @Slot(str)
    def requestChildren(self, path: str) -> None:
        """Egy mappa közvetlen almappáinak lekérése HÁTTÉRSZÁLON — a hívás
        azonnal visszatér, az eredmény a `childrenLoaded` jelzésben érkezik
        (a Qt automatikusan a GUI-szálra sorolja)."""
        target = str(path)

        def worker() -> None:
            children = _list_children(Path(target))
            self.childrenLoaded.emit(target, children)

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-foldertree")

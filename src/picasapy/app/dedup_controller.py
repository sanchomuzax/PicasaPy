"""DedupController: a duplikátum-kezelő ablak (`DedupDialog.qml`, #287)
QML-hídja a `picasapy.dedup.find_duplicates` mag fölött.

Önálló QObject — a `FolderTreeController`/`DiscoveryController` mintáját
követve NEM az `AppController` mixinje, hogy a `controller.py` (forró
fájl, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést kapja.

A keresés a teljes indexelt könyvtáron fut HÁTTÉRSZÁLON: a hasonlósági
réteg O(n²) páronkénti összevetéssel dolgozik (ld. `dedup/similar.py`),
nagy könyvtárnál másodpercekig is tarthat — ez nem blokkolhatja a
GUI-szálat. A csoportokat (és minden elemüket) QML-nek MINDIG listaként
(dict-ek listája) adjuk át, SOHA Python tuple-ként — a tuple QML-ben nem
tömb, a `.length` undefined lenne (ld. MEMORY.md tanulság).

Alapértelmezett, NEM-destruktív feloldás (#287 DoD): a csoport minden
tagja — a megtartandó kivételével — a forrásmappájának "Duplikátumok"
alkönyvtárába kerül (`moveOthersToDuplicatesFolder`). A Kukába törlés
(`deleteOthers`) csak explicit felhasználói döntésre történik."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.dedup import find_duplicates
from picasapy.fileops import delete_to_trash, move_photo
from picasapy.index import PhotoRecord, all_photos, open_index

# A nem-destruktív áthelyezés célmappájának neve, forrásmappánként —
# létrehozva, ha még nincs (ld. `_move_one`).
DUPLICATES_SUBFOLDER_NAME = "Duplikátumok"


def _photo_path(photo: PhotoRecord) -> str:
    """A fotó teljes (abszolút) elérési útja — ez a kulcs a
    `find_duplicates` bemenetéhez és a csoportok elem-azonosításához."""
    return str(Path(photo.folder_path) / photo.name)


def _thumb_url(photo_id: int | None) -> str:
    """A `thumbs` image-provider URL-je (ld. `thumbnail_provider.py`) —
    üres string, ha a fájl nincs az indexben (ilyenkor a QML placeholder
    marad, `Image.source` üres stringre nem próbál betölteni)."""
    return f"image://thumbs/{photo_id}" if photo_id is not None else ""


def _group_dict(
    kind: str,
    paths: tuple[Path, ...],
    by_path: dict[str, PhotoRecord],
    max_distance: int | None,
) -> dict:
    """Egy duplikátum-csoport QML-barát alakja: sima `dict`, a tagok is
    `dict`-ek listájaként (nem tuple)."""
    items = [
        {
            "path": str(path),
            "thumbUrl": _thumb_url(
                by_path[str(path)].id if str(path) in by_path else None
            ),
        }
        for path in paths
    ]
    return {
        "kind": kind,
        # -1: nincs értelmezhető távolság (pontos duplikátum) — a QML
        # ebből dönti el, hogy mutassa-e a "hasonlóság" feliratot
        "maxDistance": max_distance if max_distance is not None else -1,
        "items": items,
    }


def _build_groups(report, by_path: dict[str, PhotoRecord]) -> list[dict]:
    """A `DuplicateReport` (exact + similar csoportok) egyetlen, QML-nek
    adható listává lapítva — előbb a pontos, aztán a hasonló csoportok."""
    groups = [
        _group_dict("exact", group.paths, by_path, None)
        for group in report.exact_groups
    ]
    groups += [
        _group_dict("similar", group.paths, by_path, group.max_distance)
        for group in report.similar_groups
    ]
    return groups


class DedupController(QObject):
    """A `DedupDialog.qml` háttér-hídja: keresés indítása és a csoportok
    feloldása (áthelyezés vagy törlés)."""

    scanStarted = Signal()
    scanFinished = Signal(list)  # csoportok (dict-ek listája)
    scanFailed = Signal(str)  # hibaüzenet (pl. olvashatatlan index)
    itemResolved = Signal(str)  # (feloldott elem útvonala) — a QML ebből törli a sorból
    operationFailed = Signal(str, str)  # (útvonal, hibaüzenet)

    def __init__(self, db_path: Path, provider) -> None:
        """`provider`: a `ThumbnailProvider` (vagy teszthez `None`) — a
        keresés eredményét ITT regisztráljuk nála (`register_photos`),
        hogy a csoportok `thumbUrl`-jei ténylegesen feloldhatók legyenek,
        függetlenül attól, hogy a fő rács éppen mit mutat."""
        super().__init__()
        self._db_path = Path(db_path)
        self._provider = provider

    @Slot()
    def scanForDuplicates(self) -> None:
        """A teljes (indexelt) könyvtár duplikátum-keresése HÁTTÉRSZÁLON —
        a hívás azonnal visszatér, az eredmény a `scanFinished`-ben
        érkezik (a Qt automatikusan a GUI-szálra sorolja, ahogy a
        `FolderTreeController.childrenLoaded` is teszi)."""
        self.scanStarted.emit()

        def worker() -> None:
            try:
                with open_index(self._db_path) as conn:
                    photos = all_photos(conn)
            except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
                self.scanFailed.emit(str(error))
                return

            by_path = {_photo_path(photo): photo for photo in photos}
            report = find_duplicates(list(by_path.keys()))

            # a csoportokban szereplő fotókat a thumbnail-providernél is
            # regisztráljuk, hogy az `image://thumbs/<id>` URL-ek a
            # dialógus megnyitásakor ténylegesen feloldhatók legyenek. A
            # `register_photos` egyetlen (GIL alatt atomi) dict-cserét
            # végez, nincs belső zár — emiatt háttérszálról hívva is
            # biztonságos (ugyanígy hív rá a `photo_ops_controller.py`
            # háttérszála is, csak jelzésen keresztül).
            if self._provider is not None:
                self._provider.register_photos(photos)

            groups = _build_groups(report, by_path)
            self.scanFinished.emit(groups)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(list, str)
    def deleteOthers(self, paths: list, keep_path: str) -> None:
        """A csoport minden tagját Kukába helyezi, KIVÉVE a megtartandót
        (`keep_path`). Destruktívabb út — a UI-ban csak explicit
        felhasználói döntésre elérhető, az alapértelmezés a
        `moveOthersToDuplicatesFolder`."""
        for path in paths:
            if path == keep_path:
                continue
            try:
                delete_to_trash(Path(path))
            except OSError as error:
                self.operationFailed.emit(path, str(error))
                continue
            self.itemResolved.emit(path)

    @Slot(list, str)
    def moveOthersToDuplicatesFolder(self, paths: list, keep_path: str) -> None:
        """Nem-destruktív alapértelmezés (#287 DoD): a csoport minden
        tagja — a megtartandó kivételével — a saját forrásmappájának
        "Duplikátumok" alkönyvtárába kerül (mappánként létrehozva, ha még
        nincs). Így a különböző mappákból származó duplikátumok is a
        saját kontextusukban maradnak, nem egy közös, helyfüggetlen
        gyűjtőmappában."""
        for path in paths:
            if path == keep_path:
                continue
            source = Path(path)
            dest_folder = source.parent / DUPLICATES_SUBFOLDER_NAME
            try:
                dest_folder.mkdir(exist_ok=True)
                move_photo(source, dest_folder)
            except OSError as error:
                self.operationFailed.emit(path, str(error))
                continue
            self.itemResolved.emit(path)

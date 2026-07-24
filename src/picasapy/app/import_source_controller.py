"""ImportSourceController: "Import forrásból" (#23) — külső mappa (pl.
fényképezőgép/kártya csatolt mappája) képeinek másolása/áthelyezése a
könyvtárba, dátum szerinti mappa-sablonnal.

Szándékosan ÖNÁLLÓ QObject (a `discovery_controller.py`/`drop_import_
controller.py` mintáját követve): NEM az `AppController` mixinje, hogy a
`controller.py`/`Main.qml` (forró fájlok, CONTRIBUTING.md) csak a végleges,
minimális bekötést kapja.

A forrás-beolvasás és a mappa-sablon logika a Qt-mentes
`picasapy.importsource` modulban él (önállóan unit-tesztelt); ez a
controller csak a QML-hidat adja: háttérszálas szkennelés/importálás,
haladás-jelzés, soronkénti hibakezelés (egy rossz fájl nem állíthatja meg
a köteget — az `export_controller.py` mintája).

Alapértelmezés (#23 DoD, NEM-DESZTRUKTÍV): másolás — a forrás (kártya/
mappa) érintetlen marad, kivéve ha a felhasználó KIFEJEZETTEN áthelyezést
kér. Mindkét mód a `fileops.copy_photo` ütközésbiztos névfeloldásán (a
`export/exporter.py` `_unique_target`-mintája, `név-1.jpg`, `név-2.jpg`, ...)
keresztül fut — az áthelyezés a szigorúbb (felülírást tiltó, kizárólag a
forrással azonos célnevet feltételező) `fileops.move_photo` helyett
copy+forrás-törlés kombinációval valósul meg, mert az import forrása idegen,
előre nem ismert névkészlet (gyakori azonos fájlnév különböző
kártyákról/mappákból) — ott a `move_photo` szigorú, felülírást tiltó
kivétele minden ütköző fájlnál megállítaná a köteget.

Sikeres import után a cél-mappa a meglévő `addWatchedFolder` úton válik a
könyvtár részévé (ugyanaz a callback-minta, mint a `DropImportController`/
`DiscoveryController`-nél) — az importált képek AZONNAL megjelennek a
rácsban, ahogy a valódi Picasa importja is tenné.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.fileops import copy_photo
from picasapy.importsource import (
    DEFAULT_TEMPLATE,
    ImportCandidate,
    destination_subpath,
    scan_source,
)
from picasapy.index import PhotoRecord
from picasapy.ini import load_document, save_document
from picasapy.scanner import PICASA_INI_NAME, media_kind_of

from .formatting import to_local_path

# a soronkénti importálási hibákból ennyit mutatunk a UI-nak (az
# `ExportMixin._EXPORT_FAILED_DETAILS_LIMIT` mintája) — tömeges hibánál a
# teljes lista inkább zavaró, mint hasznos
_IMPORT_FAILED_DETAILS_LIMIT = 5


def _thumb_url(photo_id: int) -> str:
    return f"image://thumbs/{photo_id}"


def _preview_photo_record(index: int, candidate: ImportCandidate) -> PhotoRecord:
    """Ideiglenes rekord a forrás-előnézethez.

    NEGATÍV id-tartományt használ (a valódi indexbeli fotók mindig pozitív,
    autoincrement id-jűek) — a thumbnail-provider `register_additional_
    photos` regisztrációja így SOSE ütközhet valódi könyvtárbeli fotóval.
    """
    try:
        stat = candidate.path.stat()
        size, mtime_ns = stat.st_size, stat.st_mtime_ns
    except OSError:
        size, mtime_ns = 0, 0
    return PhotoRecord(
        id=-(index + 1),
        folder_path=str(candidate.path.parent),
        name=candidate.path.name,
        kind=media_kind_of(candidate.path.name) or "photo",
        size=size,
        mtime_ns=mtime_ns,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=candidate.date.isoformat() if candidate.date else None,
        orientation=1,
        width=None,
        height=None,
    )


class ImportSourceController(QObject):
    """Az `ImportSourceDialog.qml` háttér-hídja: forrás-szkennelés, majd
    másolás/áthelyezés a cél-mappa dátum-sablonja szerint."""

    sourceScanStarted = Signal()
    # (előnézeti elemek — dict-ek listája: path/thumbUrl —, összes darabszám).
    # MINDIG lista (soha tuple) — a QML `.length` tuple-ön undefined lenne.
    sourceScanFinished = Signal(list, int)
    sourceScanFailed = Signal(str)  # emberi nyelvű hibaüzenet (érvénytelen forrás)

    importStarted = Signal(int)  # összes importálandó darab
    importProgress = Signal(int, int)  # (kész, összes)
    # az első néhány sikertelen fájl neve + oka — MINDIG az importFinished előtt
    importFailedDetails = Signal(list)
    importFinished = Signal(int, int)  # (importált, sikertelen)

    def __init__(
        self,
        provider,
        add_folder: Callable[[str], None],
        parent: QObject | None = None,
    ) -> None:
        """`provider`: a megosztott `ThumbnailProvider` — az előnézeti
        bélyegképek regisztrálásához (teszthez `None` is elfogadott, ekkor
        a `thumbUrl` üres marad); `add_folder`: a `controller.
        addWatchedFolder` — sikeres import után ide kerül a cél-mappa."""
        super().__init__(parent)
        self._provider = provider
        self._add_folder = add_folder
        self._candidates: tuple[ImportCandidate, ...] = ()
        # a legutóbb regisztrált előnézeti (negatív) id-k — új szkennelés
        # előtt ezeket távolítjuk el, hogy a registry ne halmozódjon
        self._preview_ids: tuple[str, ...] = ()

    @Slot(str)
    def scanSource(self, folder: str) -> None:
        """A forrás-mappa (rekurzív) beolvasása HÁTTÉRSZÁLON — kártyák
        gyakori DCIM/100XXXX szerkezete miatt a `picasapy.importsource.
        scan_source` az almappákba is belenéz. `folder` `file://` URL is
        lehet (a QML FolderDialog azt ad, a `controller.addWatchedFolder`
        mintájára). A hívás azonnal visszatér, az eredmény a
        `sourceScanFinished`/`sourceScanFailed` jelzésben érkezik (a Qt
        automatikusan a GUI-szálra sorolja)."""
        self.sourceScanStarted.emit()
        target = to_local_path(folder)
        if not target:
            self.sourceScanFailed.emit(
                self.tr("Choose a source folder first.")
            )
            return

        def worker() -> None:
            try:
                candidates = scan_source(target)
            except (FileNotFoundError, NotADirectoryError) as error:
                self.sourceScanFailed.emit(str(error))
                return

            self._candidates = candidates
            records = tuple(
                _preview_photo_record(index, candidate)
                for index, candidate in enumerate(candidates)
            )
            if self._provider is not None:
                self._provider.unregister_additional_photos(self._preview_ids)
                self._provider.register_additional_photos(records)
            self._preview_ids = tuple(str(record.id) for record in records)

            items = [
                {
                    "path": str(candidate.path),
                    "thumbUrl": _thumb_url(record.id)
                    if self._provider is not None
                    else "",
                }
                for candidate, record in zip(candidates, records)
            ]
            self.sourceScanFinished.emit(items, len(candidates))

        threading.Thread(target=worker, daemon=True).start()

    @Slot(str, str, bool)
    def runImport(self, dest_folder: str, template: str, move: bool) -> None:
        """A legutóbb szkennelt forrás importja `dest_folder` alá, a
        `template` mappa-sablon szerint (dátum-alapú alútvonal, ld.
        `picasapy.importsource.destination_subpath`); `move=True` esetén a
        forrás a másolás UTÁN törlődik. `dest_folder` `file://` URL is
        lehet. Háttérszálon fut, `importProgress`-szal soronként jelezve —
        egy sikertelen fájl nem állítja meg a köteget (a hiba a végén
        `importFailedDetails`-ben jelenik meg)."""
        candidates = self._candidates
        dest_text = to_local_path(dest_folder)
        template_text = template or DEFAULT_TEMPLATE
        total = len(candidates)
        if not dest_text:
            self.importFinished.emit(0, total)
            return
        dest_root = Path(dest_text)
        self.importStarted.emit(total)
        if total == 0:
            self.importFinished.emit(0, 0)
            return

        def worker() -> None:
            copied = 0
            failed_details: list[str] = []
            for done, candidate in enumerate(candidates, start=1):
                try:
                    subdir = dest_root / destination_subpath(
                        candidate.date, template_text
                    )
                    subdir.mkdir(parents=True, exist_ok=True)
                    _import_one(candidate.path, subdir, move)
                    copied += 1
                except OSError as error:
                    failed_details.append(f"{candidate.path.name}: {error}")
                self.importProgress.emit(done, total)
            if failed_details:
                self.importFailedDetails.emit(
                    failed_details[:_IMPORT_FAILED_DETAILS_LIMIT]
                )
            if copied > 0:
                self._add_folder(str(dest_root))
            self.importFinished.emit(copied, total - copied)

        threading.Thread(target=worker, daemon=True).start()


def _import_one(path: Path, dest_folder: Path, move: bool) -> Path:
    """Egy fájl importja: MINDIG ütközésbiztos `copy_photo`-val (ld. a
    modul docsztringje, miért nem a szigorúbb `move_photo`); `move=True`
    esetén a másolás UTÁN a forrás törlődik (fájl + ini-szekció)."""
    target = copy_photo(path, dest_folder)
    if move:
        _remove_source_after_move(path)
    return target


def _remove_source_after_move(path: Path) -> None:
    """A forrás eltávolítása sikeres másolás után (áthelyezés-szimuláció):
    a fájl törlése, majd — ha volt — az ini-szekció eltávolítása a forrás
    `.picasa.ini`-jéből. A cél a saját (ütközés esetén átnevezett)
    másolatát már megkapta a `copy_photo`-tól."""
    path.unlink(missing_ok=True)
    source_ini = path.parent / PICASA_INI_NAME
    if not source_ini.exists():
        return
    try:
        document = load_document(source_ini)
    except (OSError, ValueError):
        return
    if document.section(path.name) is not None:
        save_document(document.without_section(path.name), source_ini, backup=True)

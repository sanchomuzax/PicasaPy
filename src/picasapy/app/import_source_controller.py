"""ImportSourceController: "Import forrásból" (#23/#441) — külső mappa (pl.
fényképezőgép/kártya csatolt mappája) képeinek másolása a könyvtárba, HÁROM
célmappa-elnevezési mód, duplikátum-kizárás, egyenkénti válogatás és
háromállapotú (kétlépcsős megerősítésű) forrás-törlés mellett.

Szándékosan ÖNÁLLÓ QObject (a `discovery_controller.py`/`drop_import_
controller.py` mintáját követve): NEM az `AppController` mixinje, hogy a
`controller.py`/`Main.qml` (forró fájlok, CONTRIBUTING.md) csak a végleges,
minimális bekötést kapja.

A forrás-beolvasás, a célmappa-elnevezés (#441 HÁROM módja) és a
duplikátum-kizárás logikája a Qt-mentes `picasapy.importsource` modulban él
(önállóan unit-tesztelt); ez a controller csak a QML-hidat adja:
háttérszálas szkennelés/importálás, haladás-jelzés, soronkénti hibakezelés
(egy rossz fájl nem állíthatja meg a köteget — az `export_controller.py`
mintája).

Import mindig MÁSOLÁS — a forrás (kártya/mappa) érintetlen marad, kivéve ha
a felhasználó a #441 "After Copying:" HÁROM állapota közül a törléssel
járó kettő egyikét választja (`AFTER_COPY_DELETE_COPIED`/`AFTER_COPY_
DELETE_ALL`); a törlés MINDIG csak SIKERES másolás (legalább egy fájl
importálva) UTÁN fut le. A tényleges fájlműveletet a
`fileops.copy_photo` ütközésbiztos névfeloldása adja (a `export/exporter.py`
`_unique_target`-mintája, `név-1.jpg`, `név-2.jpg`, ...) — az import forrása
idegen, előre nem ismert névkészlet (gyakori azonos fájlnév különböző
kártyákról/mappákból), ezért a szigorúbb, felülírást tiltó `fileops.
move_photo` helyett a copy+forrás-törlés kombináció a helyes út.

Sikeres import után a cél-mappa a meglévő `addWatchedFolder` úton válik a
könyvtár részévé (ugyanaz a callback-minta, mint a `DropImportController`/
`DiscoveryController`-nél) — az importált képek AZONNAL megjelennek a
rácsban, ahogy a valódi Picasa importja is tenné."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot

from picasapy.fileops import copy_photo
from picasapy.importsource import (
    NAMING_BY_DATE,
    NAMING_MANUAL,
    NAMING_TODAY,
    ImportCandidate,
    destination_subpath_for_mode,
    duplicate_paths,
    scan_source,
)
from picasapy.index import PhotoRecord, all_photos, open_index
from picasapy.ini import load_document, save_document
from picasapy.scanner import PICASA_INI_NAME, media_kind_of

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

# a soronkénti importálási hibákból ennyit mutatunk a UI-nak (az
# `ExportMixin._EXPORT_FAILED_DETAILS_LIMIT` mintája) — tömeges hibánál a
# teljes lista inkább zavaró, mint hasznos
_IMPORT_FAILED_DETAILS_LIMIT = 5

# -- #441: "After Copying:" HÁROM állapota -----------------------------
AFTER_COPY_LEAVE = "leave"  # "Leave card alone" (alapértelmezés)
AFTER_COPY_DELETE_COPIED = "delete_copied"  # "Delete only copied photos"
AFTER_COPY_DELETE_ALL = "delete_all"  # "Delete everything on card"

_VALID_NAMING_MODES = (NAMING_MANUAL, NAMING_BY_DATE, NAMING_TODAY)
_VALID_AFTER_COPYING = (AFTER_COPY_LEAVE, AFTER_COPY_DELETE_COPIED, AFTER_COPY_DELETE_ALL)

# #441: "Exclude Duplicates" — QSettings-kulcs (a jegy szövege szerint
# "autoexclude", a Picasa eredeti `options.fen`/`General` lapjának
# megfelelő beállítás-nevét követve, ld. `docs/specs/picasa-fen-dialogs.md`).
AUTOEXCLUDE_SETTINGS_KEY = "import/autoexclude"


def _thumb_url(photo_id: int) -> str:
    return f"image://thumbs/{photo_id}"


def _preview_photo_record(index: int, candidate: ImportCandidate) -> PhotoRecord:
    """Ideiglenes rekord a forrás-előnézethez.

    NEGATÍV id-tartományt használ (a valódi indexbeli fotók mindig pozitív,
    autoincrement id-jűek) — a thumbnail-provider `register_additional_
    photos` regisztrációja így SOSE ütközhet valódi könyvtárbeli fotóval."""
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


def _library_paths(index_path: str | Path) -> tuple[Path, ...]:
    """A jelenleg indexelt könyvtár teljes fájl-útvonalai (#441 duplikátum-
    kizárás forrása). Hiányzó/olvashatatlan indexnél üres tuple — az
    "Exclude Duplicates" ekkor egyszerűen nem talál semmit, NEM hibázik."""
    try:
        with open_index(index_path) as conn:
            return tuple(
                Path(record.folder_path) / record.name
                for record in all_photos(conn)
            )
    except (OSError, sqlite3.Error):
        return ()


class ImportSourceController(BackgroundWorkerMixin, QObject):
    """Az `ImportSourceDialog.qml` háttér-hídja: forrás-szkennelés
    (duplikátum-jelöléssel), egyenkénti válogatás, majd másolás a
    cél-mappa HÁROM elnevezési módja szerint (#441)."""

    sourceScanStarted = Signal()
    # (előnézeti elemek — dict-ek listája: path/thumbUrl/duplicate/excluded
    # —, összes darabszám). MINDIG lista (soha tuple) — a QML `.length`
    # tuple-ön undefined lenne.
    sourceScanFinished = Signal(list, int)
    sourceScanFailed = Signal(str)  # emberi nyelvű hibaüzenet (érvénytelen forrás)

    # #441: egyenkénti válogatás (Exclude/Include/Exclude All/Include All) —
    # a frissített előnézeti lista (ugyanaz az alak, mint a
    # sourceScanFinished items paramétere), rescan nélkül
    selectionChanged = Signal(list)
    autoExcludeChanged = Signal()

    importStarted = Signal(int)  # összes importálandó (beválogatott) darab
    importProgress = Signal(int, int)  # (kész, összes)
    # az első néhány sikertelen fájl neve + oka — MINDIG az importFinished előtt
    importFailedDetails = Signal(list)
    importFinished = Signal(int, int)  # (importált, sikertelen)

    def __init__(
        self,
        provider,
        add_folder: Callable[[str], None],
        index_path: str | Path = "",
        settings: QSettings | None = None,
        parent: QObject | None = None,
    ) -> None:
        """`provider`: a megosztott `ThumbnailProvider` — az előnézeti
        bélyegképek regisztrálásához (teszthez `None` is elfogadott, ekkor
        a `thumbUrl` üres marad); `add_folder`: a `controller.
        addWatchedFolder` — sikeres import után ide kerül a cél-mappa;
        `index_path`: a duplikátum-kizáráshoz (#441) beolvasott SQLite
        index útvonala (üres string esetén az "Exclude Duplicates" soha
        nem talál egyezést); `settings`: a `autoexclude`-kapcsoló tárolója
        (alapból `QSettings("PicasaPy", "PicasaPy")`, a `controller.py`
        `_get_settings` mintája)."""
        super().__init__(parent)
        self._provider = provider
        self._add_folder = add_folder
        self._index_path = index_path
        self._settings = settings
        self._candidates: tuple[ImportCandidate, ...] = ()
        # a legutóbb szkennelt duplikátumok útvonalai (#441) — az
        # autoExclude kapcsoló ÉLŐBEN (rescan nélkül) alkalmazza/vonja
        # vissza ezekre a kizárást
        self._duplicate_paths: frozenset[Path] = frozenset()
        # a felhasználó (vagy az autoExclude) által kizárt jelöltek —
        # útvonal-stringek, mert a QML felől is stringgel érkeznek
        self._excluded_paths: set[str] = set()
        # a legutóbb regisztrált előnézeti (negatív) id-k — új szkennelés
        # előtt ezeket távolítjuk el, hogy a registry ne halmozódjon
        self._preview_ids: tuple[str, ...] = ()
        self._auto_exclude = self._read_auto_exclude()

    def _get_settings(self) -> QSettings:
        if self._settings is None:
            self._settings = QSettings("PicasaPy", "PicasaPy")
        return self._settings

    def _read_auto_exclude(self) -> bool:
        value = self._get_settings().value(AUTOEXCLUDE_SETTINGS_KEY, "false")
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "1")

    # -- #441: "Exclude Duplicates" ----------------------------------------

    @Property(bool, notify=autoExcludeChanged)
    def autoExclude(self) -> bool:  # noqa: N802 — QML property-konvenció
        """"Exclude Duplicates" — "Exclude photos that are already
        imported into Picasa"."""
        return self._auto_exclude

    @Slot(bool)
    def setAutoExclude(self, value: bool) -> None:  # noqa: N802
        value = bool(value)
        if value == self._auto_exclude:
            return
        self._auto_exclude = value
        self._get_settings().setValue(
            AUTOEXCLUDE_SETTINGS_KEY, "true" if value else "false"
        )
        if value:
            self._excluded_paths |= {str(path) for path in self._duplicate_paths}
        else:
            self._excluded_paths -= {str(path) for path in self._duplicate_paths}
        self.autoExcludeChanged.emit()
        self.selectionChanged.emit(self._preview_items())

    # -- #441: egyenkénti válogatás -----------------------------------------

    @Slot(str)
    def excludeFile(self, path: str) -> None:
        self._excluded_paths.add(path)
        self.selectionChanged.emit(self._preview_items())

    @Slot(str)
    def includeFile(self, path: str) -> None:
        self._excluded_paths.discard(path)
        self.selectionChanged.emit(self._preview_items())

    @Slot()
    def excludeAll(self) -> None:  # noqa: N802
        self._excluded_paths = {str(candidate.path) for candidate in self._candidates}
        self.selectionChanged.emit(self._preview_items())

    @Slot()
    def includeAll(self) -> None:  # noqa: N802
        self._excluded_paths.clear()
        self.selectionChanged.emit(self._preview_items())

    def _preview_items(self) -> list[dict]:
        """A jelenlegi jelöltlista QML-nek adható alakja — a
        `sourceScanFinished` és a `selectionChanged` is ezt küldi, hogy a
        QML-oldal egyetlen kódúton frissítse a rácsot."""
        items = []
        for index, candidate in enumerate(self._candidates):
            path_text = str(candidate.path)
            items.append(
                {
                    "path": path_text,
                    "thumbUrl": _thumb_url(-(index + 1))
                    if self._provider is not None
                    else "",
                    "duplicate": candidate.path in self._duplicate_paths,
                    "excluded": path_text in self._excluded_paths,
                }
            )
        return items

    # -- forrás-szkennelés ---------------------------------------------------

    @Slot(str)
    def scanSource(self, folder: str) -> None:
        """A forrás-mappa (rekurzív) beolvasása HÁTTÉRSZÁLON — kártyák
        gyakori DCIM/100XXXX szerkezete miatt a `picasapy.importsource.
        scan_source` az almappákba is belenéz. `folder` `file://` URL is
        lehet (a QML FolderDialog azt ad, a `controller.addWatchedFolder`
        mintájára). A hívás azonnal visszatér, az eredmény a
        `sourceScanFinished`/`sourceScanFailed` jelzésben érkezik (a Qt
        automatikusan a GUI-szálra sorolja). Duplikátum-jelölés (#441): a
        már indexelt könyvtárral tartalom-egyező jelöltek `duplicate=True`-t
        kapnak, és — ha `autoExclude` be van kapcsolva — alapból ki is
        maradnak a válogatásból."""
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

            duplicates = duplicate_paths(candidates, _library_paths(self._index_path))

            self._candidates = candidates
            self._duplicate_paths = duplicates
            self._excluded_paths = (
                {str(path) for path in duplicates} if self._auto_exclude else set()
            )
            records = tuple(
                _preview_photo_record(index, candidate)
                for index, candidate in enumerate(candidates)
            )
            if self._provider is not None:
                self._provider.unregister_additional_photos(self._preview_ids)
                self._provider.register_additional_photos(records)
            self._preview_ids = tuple(str(record.id) for record in records)

            items = self._preview_items()
            self.sourceScanFinished.emit(items, len(candidates))

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-importsource-scan")

    # -- import ---------------------------------------------------------------

    @Slot(str, str, str, str)
    def runImport(
        self,
        dest_folder: str,
        naming_mode: str,
        manual_name: str,
        after_copying: str,
    ) -> None:
        """A legutóbb szkennelt, BEVÁLOGATOTT (nem kizárt) jelöltek importja
        `dest_folder` alá, a `naming_mode` (#441 HÁROM módja: `NAMING_MANUAL`
        / `NAMING_BY_DATE` / `NAMING_TODAY`) szerint. `after_copying` (#441
        "After Copying:" HÁROM állapota) SIKERES másolás UTÁN dönt a forrás
        sorsáról — a kétlépcsős megerősítés a QML dolga, ez a metódus a
        döntést hajtja végre. `dest_folder` `file://` URL is lehet.
        Háttérszálon fut, `importProgress`-szal soronként jelezve — egy
        sikertelen fájl nem állítja meg a köteget (a hiba a végén
        `importFailedDetails`-ben jelenik meg)."""
        naming_mode = naming_mode if naming_mode in _VALID_NAMING_MODES else NAMING_BY_DATE
        after_copying = (
            after_copying if after_copying in _VALID_AFTER_COPYING else AFTER_COPY_LEAVE
        )
        all_candidates = self._candidates
        included = tuple(
            candidate
            for candidate in all_candidates
            if str(candidate.path) not in self._excluded_paths
        )
        dest_text = to_local_path(dest_folder)
        total = len(included)
        if not dest_text:
            self.importFinished.emit(0, total)
            return
        dest_root = Path(dest_text)
        self.importStarted.emit(total)
        if total == 0:
            self.importFinished.emit(0, 0)
            return

        def worker() -> None:
            copied_paths: list[Path] = []
            failed_details: list[str] = []
            for done, candidate in enumerate(included, start=1):
                try:
                    subdir = dest_root / destination_subpath_for_mode(
                        candidate.date, naming_mode, manual_name=manual_name
                    )
                    subdir.mkdir(parents=True, exist_ok=True)
                    copy_photo(candidate.path, subdir)
                    copied_paths.append(candidate.path)
                except OSError as error:
                    failed_details.append(f"{candidate.path.name}: {error}")
                self.importProgress.emit(done, total)
            if failed_details:
                self.importFailedDetails.emit(
                    failed_details[:_IMPORT_FAILED_DETAILS_LIMIT]
                )
            if copied_paths:
                self._add_folder(str(dest_root))
                # #441: a törlés CSAK sikeres másolás után futhat le
                if after_copying == AFTER_COPY_DELETE_COPIED:
                    for path in copied_paths:
                        _remove_source_file(path)
                elif after_copying == AFTER_COPY_DELETE_ALL:
                    # A "minden törlése" sem törölhet olyan fájlt, amelynek a
                    # MÁSOLÁSA elbukott — épp az nem jutott át, tehát a
                    # törlése adatvesztés lenne. A kártya kiürítésének
                    # szándéka így is teljesül minden átjutott fájlra; a
                    # bukottak a forráson maradnak, és a hibalistán
                    # (importFailedDetails) meg is jelennek.
                    failed_sources = {
                        candidate.path
                        for candidate in included
                        if candidate.path not in set(copied_paths)
                    }
                    for candidate in all_candidates:
                        if candidate.path in failed_sources:
                            continue
                        _remove_source_file(candidate.path)
            self.importFinished.emit(len(copied_paths), total - len(copied_paths))

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-importsource-run")


def _remove_source_file(path: Path) -> None:
    """Egy forrásfájl eltávolítása (#441 "After Copying:" törléssel járó két
    állapota): a fájl törlése, majd — ha volt — az ini-szekció eltávolítása
    a forrás `.picasa.ini`-jéből. A cél a saját (ütközés esetén átnevezett)
    másolatát már megkapta a `copy_photo`-tól, mielőtt ez lefut."""
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

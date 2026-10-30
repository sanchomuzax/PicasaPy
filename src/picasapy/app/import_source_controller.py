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

import ctypes as ctypes
import sqlite3 as sqlite3
import sys
import time
from collections.abc import Sequence as Sequence
from ctypes import wintypes as wintypes
from pathlib import Path, PurePosixPath as PurePosixPath, PureWindowsPath as PureWindowsPath
from typing import Callable

from PySide6.QtCore import (
    Property as Property,
    QObject,
    QSettings,
    QStandardPaths as QStandardPaths,
    QStorageInfo as QStorageInfo,
    QUrl as QUrl,
    Signal,
    Slot,
)

from picasapy.fileops import (
    companions_of as companions_of,
    copy_photo as copy_photo,
    has_enough_free_space as has_enough_free_space,
    required_bytes_for as required_bytes_for,
)
from picasapy.fileops.original_ini import remove_original_ini_sections as remove_original_ini_sections
from picasapy.importsource import (
    ATMERETEZES_EREDETI as ATMERETEZES_EREDETI,
    ATMERETEZES_OPCIOK as ATMERETEZES_OPCIOK,
    MEDIA_FILTER_PICTURES_AND_MOVIES,
    NAMING_BY_DATE as NAMING_BY_DATE,
    NAMING_MANUAL as NAMING_MANUAL,
    NAMING_TODAY as NAMING_TODAY,
    ImportCandidate,
    atmeretez_masolatot as atmeretez_masolatot,
    destination_subpath_for_mode as destination_subpath_for_mode,
    duplicate_paths as duplicate_paths,
    is_valid_folder_name as is_valid_folder_name,
    scan_files as scan_files,
    scan_source_detailed as scan_source_detailed,
)
from picasapy.index import (
    IndexFastKeySource as IndexFastKeySource,
    PhotoRecord as PhotoRecord,
    all_photos as all_photos,
    open_index as open_index,
)
from picasapy.ini import (
    has_ini_source as has_ini_source,
    load_or_empty as load_or_empty,
    update_document as update_document,
    with_backuphash as with_backuphash,
)
from picasapy.ini.names import INI_NAME as INI_NAME
from picasapy.scanner import media_kind_of as media_kind_of

from .formatting import to_file_url as to_file_url, to_local_path
from .wipe_card_warning import WipeCardFacts as WipeCardFacts
from .wipe_card_warning import wipe_card_warning as wipe_card_warning
from .worker_thread import BackgroundWorkerMixin
from .display_mode_paint import current_display_mode_suffix as current_display_mode_suffix
from .import_source_controller_scanning import ImportSourceControllerScanningMixin
from .import_source_controller_state import (
    AFTER_COPY_DELETE_ALL,
    AFTER_COPY_DELETE_COPIED,
    AFTER_COPY_LEAVE,
    AUTOEXCLUDE_DEFAULT as AUTOEXCLUDE_DEFAULT,
    AUTOEXCLUDE_SETTINGS_KEY as AUTOEXCLUDE_SETTINGS_KEY,
    DEFAULT_DESTINATION_SETTINGS_KEY as DEFAULT_DESTINATION_SETTINGS_KEY,
    ImportSourceControllerStateMixin,
    MAX_RECENT_DESTINATIONS as MAX_RECENT_DESTINATIONS,
    MAX_RECENT_SOURCES as MAX_RECENT_SOURCES,
    RECENT_DESTINATIONS_SETTINGS_KEY as RECENT_DESTINATIONS_SETTINGS_KEY,
    RECENT_SOURCES_SETTINGS_KEY as RECENT_SOURCES_SETTINGS_KEY,
    RESIZE_SETTINGS_KEY as RESIZE_SETTINGS_KEY,
    _IMPORT_FAILED_DETAILS_LIMIT,
    _VALID_AFTER_COPYING,
    _VALID_NAMING_MODES as _VALID_NAMING_MODES,
)
from .import_source_controller_import import (
    _mark_imported_ini as _mark_imported_ini,
    _remove_source_file as _remove_source_file,
    _size_of as _size_of,
)
from .import_source_controller_sources import (
    _DRIVE_REMOVABLE as _DRIVE_REMOVABLE,
    _DRIVE_REMOTE as _DRIVE_REMOTE,
    _duplikatumok as _duplikatumok,
    _has_dcim_directory_original as _has_dcim_directory,  # noqa: F401 — régi patch-pont
    _library_paths as _library_paths,
    _linux_media_mount_points as _linux_media_mount_points,
    _preview_photo_record as _preview_photo_record,
    _thumb_url as _thumb_url,
    _windows_drive_type_original as _windows_drive_type,  # noqa: F401 — régi patch-pont
    discover_linux_mounted_sources as discover_linux_mounted_sources,
    discover_mounted_sources as discover_mounted_sources,
    discover_windows_mounted_sources as discover_windows_mounted_sources,
)




def _platform() -> str:
    """A futó platform helyettesíthető fogantyúja (#1217)."""
    return sys.platform


def _read_mountinfo() -> str:
    """A Linux helyi mountlistáját olvassa be."""
    return Path("/proc/self/mountinfo").read_text(encoding="utf-8")























class ImportSourceController(
    ImportSourceControllerStateMixin,
    ImportSourceControllerScanningMixin,
    BackgroundWorkerMixin,
    QObject,
):
    """Az `ImportSourceDialog.qml` háttér-hídja: forrás-szkennelés
    (duplikátum-jelöléssel), egyenkénti válogatás, majd másolás a
    cél-mappa HÁROM elnevezési módja szerint (#441)."""

    # (előnézeti elemek — dict-ek listája: path/thumbUrl/duplicate/excluded
    # —, összes darabszám). MINDIG lista (soha tuple) — a QML `.length`
    # tuple-ön undefined lenne.
    sourceScanFinished = Signal(list, int)
    sourceScanFailed = Signal(str)  # emberi nyelvű hibaüzenet (érvénytelen forrás)

    # #441: egyenkénti válogatás (Exclude/Include/Exclude All/Include All) —
    # a frissített előnézeti lista (ugyanaz az alak, mint a
    # sourceScanFinished items paramétere), rescan nélkül
    selectionChanged = Signal(list)

    importStarted = Signal(int)  # összes importálandó (beválogatott) darab
    importProgress = Signal(int, int)  # (kész, összes)
    # #441: a másolás SEBESSÉGE bájt/másodpercben — az eredeti
    # haladásjelzője is kiírta („Copying %d of %d files at %s/sec"), és ez
    # az egyetlen jel, amiből a felhasználó megbecsülheti, mennyi van hátra.
    # Külön jelzés (nem az importProgress harmadik argumentuma), hogy a
    # meglévő hívók/tesztek szerződése ne törjön el.
    importSpeed = Signal(float)  # bájt/másodperc; 0 = még nem mérhető
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
        #: #860: a forráson lévő, NEM média fájlok száma (a kártyatörlés
        #: figyelmeztetéséhez). `-1` = még nem pásztáztunk.
        self._unrecognized = -1
        # a legutóbb szkennelt duplikátumok útvonalai (#441) — az
        # autoExclude kapcsoló ÉLŐBEN (rescan nélkül) alkalmazza/vonja
        # vissza ezekre a kizárást
        self._duplicate_paths: frozenset[Path] = frozenset()
        # a felhasználó (vagy az autoExclude) által kizárt jelöltek —
        # útvonal-stringek, mert a QML felől is stringgel érkeznek
        self._excluded_paths: set[str] = set()
        # #441: import ELŐTTI forgatás (negyed fordulatok, 0..3) és
        # csillagozás, forrás-útvonal szerint
        self._media_filter: str = MEDIA_FILTER_PICTURES_AND_MOVIES
        self._mounted_sources: list[dict[str, str]] = []
        self._rotations: dict[str, int] = {}
        self._starred: set[str] = set()
        # a legutóbb regisztrált előnézeti (negatív) id-k — új szkennelés
        # előtt ezeket távolítjuk el, hogy a registry ne halmozódjon
        self._preview_ids: tuple[str, ...] = ()
        self._auto_exclude = self._read_auto_exclude()





    # -- import ---------------------------------------------------------------

    @Slot(str)
    @Slot(str, str)
    def scanSource(self, folder: str, media_filter: str = "") -> None:
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
        # #441: a tallózó fájltípus-szűrőjének megfelelője — üres értéknél
        # a legutóbbi (vagy az alapértelmezett) fokozat marad érvényben
        if media_filter:
            self._media_filter = media_filter
        target = to_local_path(folder)
        if not target:
            self.sourceScanFailed.emit(
                self.tr("Choose a source folder first.")
            )
            return

        def worker() -> None:
            try:
                #: #860: a NEM felismert fájlok száma is kell — a
                #: kártyatörlés figyelmeztetése kimondja, hány idegen fájlt
                #: visz el a törlés
                scan = scan_source_detailed(target, self._media_filter)
                candidates = scan.candidates
                self._unrecognized = scan.unrecognized
            except (FileNotFoundError, NotADirectoryError) as error:
                self.sourceScanFailed.emit(str(error))
                return

            self._apply_scan(candidates, remember=target)

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-importsource-scan")

    def _apply_scan(
        self, candidates: tuple[ImportCandidate, ...], remember: str = ""
    ) -> None:
        """A beolvasás közös lezárása (mappa és fájllista): duplikátum-
        jelölés, kizárások, előnézeti rekordok, jelzés. Háttérszálon fut."""
        duplicates = _duplikatumok(self._index_path, candidates)

        self._candidates = candidates
        # #441: új forrás → a korábbi forgatások/csillagok nem élnek
        self._rotations = {}
        self._starred = set()
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
        # #441: a SIKERES beolvasás után jegyezzük meg a forrást — a
        # hibás/nem létező mappa ne kerüljön a legördülőbe
        if remember:
            self._remember_source(remember)
        self.sourceScanFinished.emit(items, len(candidates))

    @Slot("QVariantList")
    def scanFiles(self, files) -> None:  # noqa: N802 — QML-stílus
        """#4596: a forrás KIJELÖLT FÁJLOK listája (a QML `FileDialog`
        `selectedFiles`-a: `file://` URL-ek vagy útvonalak) — háttérszálon,
        a mappás beolvasással azonos jelzésekkel és utófeldolgozással. A
        „legutóbbi források” listája mappákat őriz, ezért fájllistát nem
        jegyzünk meg."""
        targets = [
            text for text in (to_local_path(str(item)) for item in (files or [])) if text
        ]
        if not targets:
            self.sourceScanFailed.emit(self.tr("Choose a source folder first."))
            return

        def worker() -> None:
            scan = scan_files(targets, self._media_filter)
            self._unrecognized = scan.unrecognized
            self._apply_scan(scan.candidates)

        self._start_background(worker, name="picasapy-importsource-scanfiles")

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
        # #4595: kézi elnevezésnél cím nélkül nincs import — se másolás a
        # célgyökérbe, se háttérszál (a QML-tipp kéri a címet).
        if naming_mode == NAMING_MANUAL and not manual_name.strip():
            return
        # #4837: a kézi név EGYETLEN útvonal-elem lehet (se `../`, se
        # abszolút út, se Windowson tiltott karakter) — érvénytelenre nincs import.
        if naming_mode == NAMING_MANUAL and not is_valid_folder_name(manual_name):
            return
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
            # #459: lemezhely-ellenőrzés ELŐRE (a forrás mérete a NAS-on
            # lassú lehet, ezért itt, a szálon, a másolás ELŐTT — nem a
            # GUI-szálat blokkoló main-thread stat-tal) — a művelet NE
            # induljon el félbehagyva, ha úgyis biztosan elfogyna a hely.
            required = required_bytes_for(candidate.path for candidate in included)
            if not has_enough_free_space(dest_root, required):
                self.importFailedDetails.emit(
                    [self.tr(
                        "Sorry, there is not enough free disk space to "
                        "safely download pictures."
                    )]
                )
                self.importFinished.emit(0, total)
                return
            started_at = time.monotonic()
            copied_bytes = 0
            # #1555: a beállítást a szál INDULÁSAKOR olvassuk ki egyszer —
            # a `QSettings` a GUI-szálé, és a felhasználó közben átállíthatná
            # (fél feladat két méretben már nem visszakövethető).
            resize_limit = self.resizeLimit
            for done, candidate in enumerate(included, start=1):
                try:
                    subdir = dest_root / destination_subpath_for_mode(
                        candidate.date, naming_mode, manual_name=manual_name
                    )
                    subdir.mkdir(parents=True, exist_ok=True)
                    target = copy_photo(candidate.path, subdir)
                    # #1555: a MÁSOLATOT skálázzuk le, sosem a forrást — az
                    # importálás a kártyán lévő eredetihez nem nyúlhat. A
                    # videó/RAW/sérült fájl érintetlen marad (a leskálázó
                    # `False`-szal tér vissza).
                    if resize_limit:
                        atmeretez_masolatot(target, resize_limit)
                    self._mark_imported(target, str(candidate.path))
                    copied_paths.append(candidate.path)
                    copied_bytes += _size_of(target)
                except OSError as error:
                    failed_details.append(f"{candidate.path.name}: {error}")
                self.importProgress.emit(done, total)
                elapsed = time.monotonic() - started_at
                self.importSpeed.emit(copied_bytes / elapsed if elapsed > 0 else 0.0)
            if failed_details:
                self.importFailedDetails.emit(
                    failed_details[:_IMPORT_FAILED_DETAILS_LIMIT]
                )
            if copied_paths:
                self._add_folder(str(dest_root))
                # #1785: a cél a SIKERES másolás után kerül a listába — a
                # hibás/nem létező mappa ne kínálódjon fel legközelebb.
                self._remember_destination(str(dest_root))
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

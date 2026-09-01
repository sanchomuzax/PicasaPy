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
import time
from pathlib import Path
from typing import Callable

from PySide6.QtCore import (
    Property,
    QObject,
    QSettings,
    QStandardPaths,
    Signal,
    Slot,
)

from picasapy.fileops import copy_photo, has_enough_free_space, required_bytes_for
from picasapy.importsource import (
    MEDIA_FILTER_PICTURES_AND_MOVIES,
    NAMING_BY_DATE,
    NAMING_MANUAL,
    NAMING_TODAY,
    ImportCandidate,
    destination_subpath_for_mode,
    duplicate_paths,
    scan_source,
)
from picasapy.index import PhotoRecord, all_photos, open_index
from picasapy.ini import load_document, save_document, update_document
from picasapy.scanner import PICASA_INI_NAME, media_kind_of

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin
from .display_mode_paint import current_display_mode_suffix

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

# #441: a forrásválasztó legördülőjében az eredeti a KORÁBBI importok
# listáját kínálta (`LastImport…`) a „Choose…" mellett — így a rendszeresen
# használt kártya/mappa egy kattintással újra elérhető. A lista a
# legutóbbi elöl, ismétlés nélkül; ennél többet nem tartunk meg, hogy a
# legördülő ne hízzon el.
RECENT_SOURCES_SETTINGS_KEY = "import/recentsources"
MAX_RECENT_SOURCES = 8

# #1785: az eredeti a CÉLMAPPÁKAT is megjegyzi — `Preferences\LastImport%x`
# indexelt kulcsokkal (0x00516180) —, és háromszakaszos menüben kínálja:
# korábbi importok · alapértelmezett hely · „Choose…". Nálunk a forráséval
# AZONOS legördülő adja ugyanezt; a három szakaszból a „Tallózás…" külön
# gombként már megvolt.
#
# A megőrzött célok maximális száma az eredetiben NINCS kimérve; nyolcat
# tartunk, ugyanannyit, mint a forrásokból — a legördülő így nem hízik el.
RECENT_DESTINATIONS_SETTINGS_KEY = "import/recentdestinations"
MAX_RECENT_DESTINATIONS = 8


def _thumb_url(photo_id: int) -> str:
    # #1656: a megjelenítési mód cimkéje (üres a no-op módokra)
    return f"image://thumbs/{photo_id}{current_display_mode_suffix()}"


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
    mediaFilterChanged = Signal()
    recentSourcesChanged = Signal()
    recentDestinationsChanged = Signal()

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
        self._rotations: dict[str, int] = {}
        self._starred: set[str] = set()
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

    @Property("QVariant", notify=recentSourcesChanged)
    def recentSources(self):  # noqa: N802 — QML property-konvenció
        """A korábbi import-források (#441), a legutóbbi elöl.

        A `LastImport…` legördülő adata: a felhasználó egy kattintással
        visszatérhet a rendszeresen használt kártyához/mappához."""
        return self._read_recent_sources()

    def _read_recent_sources(self) -> list[str]:
        stored = self._get_settings().value(RECENT_SOURCES_SETTINGS_KEY, [])
        if isinstance(stored, str):
            stored = [stored] if stored else []
        return [str(item) for item in (stored or [])]

    def _remember_source(self, folder: str) -> None:
        """A most beolvasott forrás a lista ELEJÉRE; ismétlés nélkül."""
        if not folder:
            return
        recent = [item for item in self._read_recent_sources() if item != folder]
        recent.insert(0, folder)
        self._get_settings().setValue(
            RECENT_SOURCES_SETTINGS_KEY, recent[:MAX_RECENT_SOURCES]
        )
        self.recentSourcesChanged.emit()

    # -- #1785: korábbi CÉLMAPPÁK -------------------------------------------

    @Property("QVariant", notify=recentDestinationsChanged)
    def recentDestinations(self):  # noqa: N802 — QML property-konvenció
        """A korábbi import-célmappák, a legutóbbi elöl (#1785).

        ⚠️ A MÁR NEM LÉTEZŐ mappa KIMARAD a listából. A döntést a jegy a
        megvalósítóra bízta („kihagyjuk vagy jelöljük"); a kihagyás mellett
        az szól, hogy a legördülőben minden tétel egy KATTINTHATÓ cél — egy
        letűnt kártyát felkínálni és hibával elutasítani rosszabb, mint meg
        sem mutatni. A tárolt lista nem csonkul: ha a mappa visszakerül (pl.
        felcsatolt hálózati meghajtó), magától újra megjelenik.
        """
        return [
            item for item in self._read_recent_destinations()
            if Path(item).is_dir()
        ]

    @Property(str, notify=recentDestinationsChanged)
    def defaultDestination(self) -> str:  # noqa: N802
        """Az alapértelmezett cél — az eredeti menü KÜLÖN szakasza
        (`-seperator-before-default_location-`).

        A képek rendszermappája alatti `Picasa` gyűjtő; ha a rendszer nem
        ad képek-mappát, a felhasználó saját mappája. Az `export_controller`
        alapértelmezésének mintája."""
        kepek = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        if not kepek:
            kepek = str(Path.home())
        return str(Path(kepek) / "Picasa")

    def _read_recent_destinations(self) -> list[str]:
        stored = self._get_settings().value(
            RECENT_DESTINATIONS_SETTINGS_KEY, []
        )
        if isinstance(stored, str):
            stored = [stored] if stored else []
        return [str(item) for item in (stored or [])]

    def _remember_destination(self, folder: str) -> None:
        """A most használt cél a lista ELEJÉRE; ismétlés nélkül.

        A forrás mintája (`_remember_source`), egy különbséggel: a célt a
        SIKERES másolás után jegyezzük meg, mert a cél létezését csak
        akkor tudjuk."""
        if not folder:
            return
        recent = [
            item for item in self._read_recent_destinations() if item != folder
        ]
        recent.insert(0, folder)
        self._get_settings().setValue(
            RECENT_DESTINATIONS_SETTINGS_KEY, recent[:MAX_RECENT_DESTINATIONS]
        )
        self.recentDestinationsChanged.emit()

    @Property(str, notify=mediaFilterChanged)
    def mediaFilter(self) -> str:  # noqa: N802 — QML property-konvenció
        """A forrás-beolvasás fájltípus-szűrője (#441) — az eredeti
        tallózó három fokozatának megfelelője."""
        return self._media_filter

    @Slot(str)
    def setMediaFilter(self, value: str) -> None:  # noqa: N802
        """A szűrő beállítása; a következő beolvasásra érvényes."""
        if value == self._media_filter:
            return
        self._media_filter = value
        self.mediaFilterChanged.emit()

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

    # -- #441: forgatás és csillagozás MÁR AZ IMPORT ELŐTT ------------------
    #
    # Az eredeti import-képernyőn az előnézeti képen ott volt a „Rotate
    # Right"/„Rotate Left" gomb és a csillagozás (`startoggle`) — a
    # felhasználó még a bemásolás előtt kiegyenesíthette és megjelölhette a
    # képeket. Nálunk ugyanez: az állapotot forrás-útvonalanként tartjuk, és
    # a MÁSOLAT `.picasa.ini`-jébe írjuk (nem a kártyán lévő eredetibe —
    # az érintetlen marad, ahogy a „Leave card alone" ág elvárja).

    @Slot(str, int)
    def rotateFile(self, path: str, delta: int) -> None:  # noqa: N802
        """Az adott jelölt forgatása negyed fordulatokkal (+1 jobbra, −1
        balra). Az érték 0..3 között körbeér; 0 = nincs forgatás."""
        if path not in {str(c.path) for c in self._candidates}:
            return
        self._rotations[path] = (self._rotations.get(path, 0) + int(delta)) % 4
        self.selectionChanged.emit(self._preview_items())

    @Slot(str)
    def toggleStar(self, path: str) -> None:  # noqa: N802
        """Csillagozás ki/be az adott jelöltre (`startoggle`)."""
        if path not in {str(c.path) for c in self._candidates}:
            return
        if path in self._starred:
            self._starred.discard(path)
        else:
            self._starred.add(path)
        self.selectionChanged.emit(self._preview_items())

    def _mark_imported(self, target: Path, source_path: str) -> None:
        """A jelölt import ELŐTT beállított forgatása/csillaga a másolatra."""
        _mark_imported_ini(
            target,
            self._rotations.get(source_path, 0),
            source_path in self._starred,
        )

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
                    # #441: import előtti forgatás/csillagozás
                    "rotation": self._rotations.get(path_text, 0),
                    "starred": path_text in self._starred,
                }
            )
        return items

    # -- forrás-szkennelés ---------------------------------------------------

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
        self.sourceScanStarted.emit()
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
                candidates = scan_source(target, self._media_filter)
            except (FileNotFoundError, NotADirectoryError) as error:
                self.sourceScanFailed.emit(str(error))
                return

            duplicates = duplicate_paths(candidates, _library_paths(self._index_path))

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
            self._remember_source(target)
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
            for done, candidate in enumerate(included, start=1):
                try:
                    subdir = dest_root / destination_subpath_for_mode(
                        candidate.date, naming_mode, manual_name=manual_name
                    )
                    subdir.mkdir(parents=True, exist_ok=True)
                    target = copy_photo(candidate.path, subdir)
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


def _size_of(path: Path) -> int:
    """A fájl mérete bájtban; olvashatatlan fájlnál 0 — a sebesség-becslés
    sosem akaszthatja meg az importot."""
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _mark_imported_ini(
    target: Path, rotation: int, starred: bool
) -> None:
    """A forgatás/csillag beírása a MÁSOLAT `.picasa.ini`-jébe (#441).

    Nem-destruktív, ahogy a rács forgatása is: `rotate=rotate(n)` és
    `star=yes`. A kártyán lévő eredetihez NEM nyúlunk — a „Leave card
    alone" ág épp azt várja el, hogy a forrás érintetlen maradjon.
    """
    if not rotation and not starred:
        return

    def _mutate(document):
        result = document
        if rotation:
            result = result.with_value(target.name, "rotate", f"rotate({rotation})")
        if starred:
            result = result.with_value(target.name, "star", "yes")
        return result

    update_document(target.parent / PICASA_INI_NAME, _mutate, backup=True)


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

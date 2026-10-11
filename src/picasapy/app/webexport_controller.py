"""WebExportController: a "Weboldal exportálása…" dialógus (#351,
`webexport.fen`, `docs/specs/picasa-fen-dialogs.md` 3.12.) QML-hídja a
`picasapy.webexport` motor fölött.

Önálló QObject — a `RelocateController`/`DedupController` mintáját követve
NEM az `AppController` mixinje, hogy a `controller.py`/`Main.qml` (forró
fájlok, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést kapja az
INTEGRÁTOR lépésében:

1. `application.py`: `WebExportController(photo_source=...)` példányosítás —
   a `photo_source` egy hívható, ami a kiválasztott mappa/album
   `PhotoRecord`-jait adja vissza (pl. `lambda: app_controller._photos.photos`
   a jelenleg megnyitott mappára — a `PhotoGridModel` ezt már tárolja).
2. `Main.qml`: `engine.rootContext().setContextProperty("webExportController", ...)`
   + a `WebExportDialog` példányosítása (a `MoveDatabaseDialog` mintája).
3. `PicasaMenuBar.qml` `webExportRequested()` jelzés bekötése a dialógus
   megnyitására (a jelzés és a menüpont MÁR készen áll ebben a jegyben).

A generálás HÁTTÉRSZÁLON fut (a kép-átméretezés/kódolás percekig tarthat
nagyobb albumnál) — a `webExportProgress` a `picasapy.webexport.images`
képenkénti előrehaladását jelzi.

#505: a háttérszál a `BackgroundWorkerMixin`-en át indul (korábban saját,
kézzel nyilvántartott `threading.Thread` volt — ez a modul íródott a
mixin ELŐTT, ld. `worker_thread.py` docstringje) — ez adja MAGÁTÓL az
alsó kék sáv busy-animációját is (`AppBusyRegistry`, `busy_registry.py`),
külön bekötés nélkül. Az `exportRunning`/`waitForExport` metódusnevek
megmaradtak (a hívók/tesztek ezekre hivatkoznak), de belül a mixin
`backgroundWorkersRunning`/`waitForBackgroundWorkers`-ét hívják."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Signal, Slot

from picasapy.fileops import has_enough_free_space, required_bytes_for
from picasapy.index import PhotoRecord
from picasapy.webexport import (
    AlbumExportData,
    WebExportSettings,
    list_templates,
    run_web_export,
)
from picasapy.webexport.images import prepare_photo_exports
from picasapy.webexport.sizes import (
    DEFAULT_SIZE_INDEX,
    SIZE_CHOICES,
    image_size_for_index,
    settings_for_template,
)

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)

#: #4610: az eredeti `Preferences\WebExportSize` / `WebExportMovie` párja —
#: a választó INDEXE és a mozgókép-mód (spec 6.1).
SIZE_SETTINGS_KEY = "webexport/size"
MOVIE_FULL_SETTINGS_KEY = "webexport/movieFull"


class WebExportController(BackgroundWorkerMixin, QObject):
    """A `WebExportDialog.qml` háttér-hídja: sablon-lista, háttérszálas
    generálás haladás-jelzéssel, hiba-visszajelzés."""

    webExportStarted = Signal()
    # (kész kép, összes kép) — a kép-generálási fázis haladása
    webExportProgress = Signal(int, int)
    # (célmappa, generált oldalak száma) — sikeres futás
    webExportFinished = Signal(str, int)
    webExportFailed = Signal(str)  # emberi nyelvű hibaüzenet

    def __init__(
        self,
        photo_source: Callable[[], Sequence[PhotoRecord]],
        parent: QObject | None = None,
        settings=None,
    ) -> None:
        """`photo_source`: hívható, ami a jelenleg kiválasztott mappa/album
        `PhotoRecord`-jait adja vissza — az integrátor köti a meglévő
        fotó-modellhez (ld. a modul docstringje). `settings`: `value()`/
        `setValue()` páros (tesztekhez); alapból `QSettings`."""
        super().__init__(parent)
        self._photo_source = photo_source
        self._settings = settings

    def _get_settings(self):
        """Lusta alapértelmezés — a `controller.py` mintájára."""
        if self._settings is None:
            self._settings = QSettings("PicasaPy", "PicasaPy")
        return self._settings

    @Slot(result="QVariantMap")
    def webExportPrefs(self) -> dict:  # noqa: N802
        r"""A méretválasztó és a mozgókép-mód megőrzött állása (#4610).

        Az eredeti a `Preferences\WebExportSize` (alap 3 → 640 képpont) és a
        `WebExportMovie` (alap 0 → „Első képkocka") kulcsból indul
        (`0x007f5310`, `0x007f5355`). Hibás tárolt érték az alapra esik."""
        settings = self._get_settings()
        return {
            "sizeIndex": _size_index(settings.value(SIZE_SETTINGS_KEY)),
            "movieFull": _truthy(settings.value(MOVIE_FULL_SETTINGS_KEY)),
        }

    def exportRunning(self) -> bool:
        """Fut-e éppen exportáló háttérszál? (a mixin nyilvántartásán át)."""
        return self.backgroundWorkersRunning()

    def waitForExport(self, timeout_s: float = 30.0) -> bool:
        """Megvárja a futó exportáló szál leállását; `True`, ha nincs (már)
        futó szál.

        A szál `daemon`, ezért az interpreter leépítése nem várja meg: ha a
        processz úgy ér véget, hogy a szál még Qt-jelzést emitál egy közben
        felszámolt objektumnak, a futás SIGSEGV-vel omlik össze (#430, a
        #53-as Qt/GIL-osztály rokona). Aki a controller élettartamát zárja
        (teszt-fixture, alkalmazás-kilépés), ezt hívja."""
        return self.waitForBackgroundWorkers(timeout_s)

    @Slot(result=list)
    def listWebExportTemplates(self) -> list[dict]:
        """A telepített sablonok a választó-lenyílóhoz: `[{"id","name",
        "description"}, ...]` (a `webexport.fen` "sablon-lista" mezője)."""
        #: #534: a `preview` a sablon előnézeti rajzának `file://` URL-je
        #: (üres sztring, ha a sablonhoz nincs rajz) — a QML `Image.source`
        #: URL-t vár, nem fájlútvonalat.
        from PySide6.QtCore import QUrl

        return [
            {
                "id": info.id,
                "name": info.name,
                "description": info.description,
                "preview": (
                    QUrl.fromLocalFile(str(info.preview_path)).toString()
                    if info.preview_path is not None
                    else ""
                ),
            }
            for info in list_templates()
        ]

    #: #534: az eredeti alapértelmezett kimeneti mappája
    #: (`CWebExporter::DefaultPath` / `IDS_DEFAULT_WEB_EXPORT_PATH`):
    #: „Picasa HTML Exports\" — KÖZVETLENÜL a rendszer képmappájában, nem a
    #: `Picasa/` alatt (ott a Kollázsok és a filmek vannak). A magyar név a
    #: mi honosított mappaneveink mintáját követi.
    HTML_EXPORT_MAPPA = "Picasa HTML exportok"

    @Slot(result=str)
    def defaultWebExportTarget(self) -> str:  # noqa: N802
        """A javasolt célmappa a párbeszéd megnyitásakor (#534).

        A képmappát a RENDSZERTŐL kérdezzük (`collage_output.pictures_dir`,
        #1088) — a `Path.home() / "Pictures"` a tulajdonos gépén rossz
        helyre mutatott, mert az OneDrive-átirányítást nem követi. A mappát
        NEM hozzuk létre: azt az export teszi, ha tényleg elindul."""
        from .collage_output import pictures_dir

        return str(pictures_dir() / self.HTML_EXPORT_MAPPA)

    @Slot(str, str, str, int, bool)
    def generateWebExport(
        self,
        target_dir: str,
        template_id: str,
        album_name: str,
        size_index: int,
        movie_full: bool,
    ) -> None:
        """A webexport indítása HÁTTÉRSZÁLON. `album_name` a cím-mező
        (`webexport.fen` "edit") tartalma — a generált oldalak
        `<%albumName%>`-je ez lesz.

        #4610 (spec `picasa-menu-parancsok-viselkedes.md` 6.1): `size_index`
        a `webexport.fen` EGYETLEN méretválasztójának indexe (`SIZE_CHOICES`,
        a nagy kép mérete); a bélyegkép méretét a sablon adja (hiányában
        144). Az árnyékolás (`shadowedThumbnails`, alapérték 1;
        `shadowedImages`, alapérték 0) nem a párbeszédből jön: a sablon
        `define`-ja adja, hiányában az alapérték (#4849). `movie_full`: „Teljes mozgófilm" (True) / „Első képkocka".
        Mindkettő megmarad a következő megnyitásig, de csak elinduló
        exportnál — az eredeti is az elfogadáskor ment.

        #1539: célzott index-újraolvasás SZÁNDÉKOSAN nincs. A kimenet egy
        WEBOLDAL (HTML + `thumbnail/` és `image/` segédmappák), amit a
        felhasználó böngészőben vagy feltöltve néz meg — nem a PicasaPy
        rácsán. A generált méretezett példányokat beindexelni kifejezetten
        káros volna: ugyanaz a kép jelenne meg többször, két külön
        felbontásban."""
        target = to_local_path(target_dir)
        if not target:
            self.webExportFailed.emit(self.tr("Choose a target folder first."))
            return
        template = next(
            (info for info in list_templates() if info.id == template_id), None
        )
        if template is None:
            self.webExportFailed.emit(
                self.tr("Unknown web export template: %1").replace("%1", template_id)
            )
            return
        try:
            photos = tuple(self._photo_source())
        except Exception as error:  # noqa: BLE001 — a hívó forrás hibája se ölje meg csendben
            self.webExportFailed.emit(str(error))
            return
        if not photos:
            self.webExportFailed.emit(self.tr("No pictures to export."))
            return
        # #459: lemezhely-ellenőrzés ELŐRE — a forrásfájlok teljes méretét
        # vetjük össze a céllal, hogy a generálás NE induljon el félbehagyva.
        required = required_bytes_for(
            Path(photo.folder_path) / photo.name for photo in photos
        )
        if not has_enough_free_space(Path(target), required):
            self.webExportFailed.emit(self.tr(
                "Sorry, there is not enough free disk space to safely "
                "download pictures."
            ))
            return

        settings = settings_for_template(
            template.path,
            image_size_for_index(_size_index(size_index)),
            WebExportSettings(movie_full=bool(movie_full)),
        )
        self._remember_choice(size_index, movie_full)
        self.webExportStarted.emit()
        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        # — a busy-bejelentkezés is ITT, a mixinben történik automatikusan
        self._start_background(
            self._run_export,
            args=(Path(target), template.path, photos, album_name, settings),
            name="picasapy-webexport",
        )

    def _remember_choice(self, size_index: int, movie_full: bool) -> None:
        """A választás megőrzése (#4610, `0x007f5ffe`/`0x007f6020`)."""
        settings = self._get_settings()
        settings.setValue(SIZE_SETTINGS_KEY, _size_index(size_index))
        settings.setValue(MOVIE_FULL_SETTINGS_KEY, bool(movie_full))

    def _run_export(
        self,
        target_dir: Path,
        template_dir: Path,
        photos: tuple[PhotoRecord, ...],
        album_name: str,
        settings: WebExportSettings,
    ) -> None:
        try:
            image_report = prepare_photo_exports(photos, target_dir, settings)
            self.webExportProgress.emit(len(image_report.photos), len(photos))
            if not image_report.photos:
                self.webExportFailed.emit(
                    self.tr("None of the selected pictures could be exported.")
                )
                return
            album = AlbumExportData(
                name=album_name or "", photos=image_report.photos
            )
            report = run_web_export(template_dir, target_dir, album, settings)
        except Exception as error:  # noqa: BLE001 — háttérszál, sose haljon el csendben
            _log.warning("webexport sikertelen: %s", error)
            self.webExportFailed.emit(str(error))
            return
        self.webExportFinished.emit(str(target_dir), len(report.output_files))


def _size_index(value) -> int:
    """Tárolt/kapott méretindex ellenőrizve: hiányzó, nem szám vagy a
    táblán kívüli érték az alapra (3 → 640) esik. (A tárolt index a mi
    kulcsunk, nem az eredeti `WebExportSize` enumja, ezért a táblán kívüli
    értéket hibásnak tekintjük, és nem az eredeti 0-ra ejtését követjük.)"""
    try:
        index = int(value)
    except (TypeError, ValueError):
        return DEFAULT_SIZE_INDEX
    return index if 0 <= index < len(SIZE_CHOICES) else DEFAULT_SIZE_INDEX


def _truthy(value) -> bool:
    """A QSettings logikai értéke (INI-ben szövegként jön vissza)."""
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false")
    return bool(value)

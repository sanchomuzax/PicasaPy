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
képenkénti előrehaladását jelzi."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.index import PhotoRecord
from picasapy.webexport import (
    AlbumExportData,
    WebExportSettings,
    list_bundled_templates,
    run_web_export,
)
from picasapy.webexport.images import prepare_photo_exports

from .formatting import to_local_path

_log = logging.getLogger(__name__)


class WebExportController(QObject):
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
    ) -> None:
        """`photo_source`: hívható, ami a jelenleg kiválasztott mappa/album
        `PhotoRecord`-jait adja vissza — az integrátor köti a meglévő
        fotó-modellhez (ld. a modul docstringje)."""
        super().__init__(parent)
        self._photo_source = photo_source

    @Slot(result=list)
    def listWebExportTemplates(self) -> list[dict]:
        """A telepített sablonok a választó-lenyílóhoz: `[{"id","name",
        "description"}, ...]` (a `webexport.fen` "sablon-lista" mezője)."""
        return [
            {"id": info.id, "name": info.name, "description": info.description}
            for info in list_bundled_templates()
        ]

    @Slot(str, str, str, int, int, bool, bool)
    def generateWebExport(
        self,
        target_dir: str,
        template_id: str,
        album_name: str,
        thumbnail_max: int,
        image_max: int,
        shadowed_thumbnails: bool,
        shadowed_images: bool,
    ) -> None:
        """A webexport indítása HÁTTÉRSZÁLON. `thumbnail_max`/`image_max`
        `<=0` = eredeti méret (a `webexport.fen` "0 = original" mintája,
        az `export.fen`-nel egyező konvenció). `album_name` a cím-mező
        (`webexport.fen` "edit") tartalma — a generált oldalak
        `<%albumName%>`-je ez lesz."""
        target = to_local_path(target_dir)
        if not target:
            self.webExportFailed.emit(self.tr("Choose a target folder first."))
            return
        template = next(
            (info for info in list_bundled_templates() if info.id == template_id), None
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

        settings = WebExportSettings(
            thumbnail_max_dimension=thumbnail_max if thumbnail_max > 0 else None,
            image_max_dimension=image_max if image_max > 0 else None,
            shadowed_thumbnails=shadowed_thumbnails,
            shadowed_images=shadowed_images,
        )
        self.webExportStarted.emit()
        threading.Thread(
            target=self._run_export,
            args=(Path(target), template.path, photos, album_name, settings),
            daemon=True,
        ).start()

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

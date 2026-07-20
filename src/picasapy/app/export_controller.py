"""Exportálás mappába (#16) — az AppController export-szelete (#150), a
`fileops_controller` melletti önálló modulban.

Mixin-osztály: az `AppController` örökli; a QML és a tesztek változatlanul
a `controller.exportRows(...)` slotot és az `exportFinished` jelzést
használják."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.export import ExportItem, ExportSettings, export_photos

from .formatting import to_local_path


class ExportMixin:
    """A kijelölés háttérszálas exportja célmappába."""

    # #16: export kész — (exportált darab, sikertelen darab); háttérszálból
    # érkezik, a Qt automatikusan a főszálra sorolja
    exportFinished = Signal(int, int)
    # #136: az első néhány sikertelen fájl neve + oka ("fájlnév: hiba") —
    # az exportFinished előtt megy ki, hogy a UI-dialógus a számmal együtt
    # a konkrét okot is megjeleníthesse.
    exportFailedDetails = Signal(list)

    # az exportResultDialog-ban ennyi hibás fájl nevét/okát mutatjuk —
    # tömeges hibánál a teljes lista inkább zavaró, mint hasznos
    _EXPORT_FAILED_DETAILS_LIMIT = 5

    @Slot(list, str, int, int)
    def exportRows(self, rows, target_dir: str, max_dimension: int,
                   jpeg_quality: int) -> None:
        """Kijelölt sorok exportja célmappába (#16, Ctrl+Shift+S).

        A forgatás (rotate_steps) ÉS a `filters=` szerkesztés-lánc (#136)
        beleég a célfájlba, hogy a rács/néző szerkesztett képe és az
        exportált fájl megegyezzen (WYSIWYG); max_dimension<=0 = eredeti
        méret. Háttérszálon fut (NAS-on percekig tarthat), a végén
        exportFinished(exportált, sikertelen), hiba esetén előtte
        exportFailedDetails(["fájlnév: ok", ...])."""
        photos = self._photos.photos
        items = tuple(
            ExportItem(
                source=Path(photos[int(r)].folder_path) / photos[int(r)].name,
                rotate_steps=photos[int(r)].rotate_steps,
                filters=photos[int(r)].filters,
            )
            for r in rows
            if 0 <= int(r) < len(photos)
        )
        target = to_local_path(target_dir)
        if not items or not target:
            self.exportFinished.emit(0, 0)
            return
        settings = ExportSettings(
            max_dimension=max_dimension if max_dimension > 0 else None,
            jpeg_quality=jpeg_quality,
        )

        def worker():
            report = export_photos(items, Path(target), settings)
            if report.failed:
                details = [
                    f"{path.name}: {reason}"
                    for path, reason in zip(report.failed, report.reasons)
                ][: self._EXPORT_FAILED_DETAILS_LIMIT]
                self.exportFailedDetails.emit(details)
            self.exportFinished.emit(len(report.exported), len(report.failed))

        threading.Thread(target=worker, daemon=True).start()

"""Exportálás mappába (#16) — az AppController export-szelete (#150), a
`fileops_controller` melletti önálló modulban.

Mixin-osztály: az `AppController` örökli; a QML és a tesztek változatlanul
a `controller.exportRows(...)` slotot és az `exportFinished` jelzést
használják."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.export import (
    ExportItem,
    ExportSettings,
    export_photos,
    resolve_export_quality,
)
from picasapy.fileops import has_enough_free_space, required_bytes_for

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin


class ExportMixin(BackgroundWorkerMixin):
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

    @Slot(str, int, result=int)
    def resolveExportQuality(self, quality_preset: str, custom_quality: int) -> int:
        """A minőség-lenyíló (#369, export.fen "Image quality" popup)
        preset-nevét konkrét JPEG-minőségre fordítja — ld.
        `picasapy.export.resolve_export_quality` docstringje a közelítés
        indoklásáért (a pontos Picasa-értékek nem dokumentáltak)."""
        return resolve_export_quality(quality_preset, custom_quality)

    @Slot(list, str, int, int, bool, str)
    def exportRows(self, rows, target_dir: str, max_dimension: int,
                   jpeg_quality: int, add_numbers: bool = False,
                   watermark_text: str = "") -> None:
        """Kijelölt sorok exportja célmappába (#16, Ctrl+Shift+S).

        A forgatás (rotate_steps) ÉS a `filters=` szerkesztés-lánc (#136)
        beleég a célfájlba, hogy a rács/néző szerkesztett képe és az
        exportált fájl megegyezzen (WYSIWYG); max_dimension<=0 = eredeti
        méret. `add_numbers` (#369): a fájlnevek elé "001-" stb. sorszám
        kerül a kijelölés sorrendjének megőrzéséhez. `watermark_text`
        (#369): nem üres esetén jobb alsó sarokba égetett, fehér, félig
        átlátszó szöveg. Háttérszálon fut (NAS-on percekig tarthat), a
        végén exportFinished(exportált, sikertelen), hiba esetén előtte
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
        # #459: lemezhely-ellenőrzés ELŐRE — a forrásfájlok teljes méretét
        # vetjük össze a céllal, hogy a művelet NE induljon el félbehagyva
        # (ld. `picasapy.fileops.diskspace` docstringje a szorzó hiányáról).
        required = required_bytes_for(item.source for item in items)
        if not has_enough_free_space(Path(target), required):
            self.exportFailedDetails.emit(
                [self.tr(
                    "Sorry, there is not enough free disk space to "
                    "safely download pictures."
                )]
            )
            self.exportFinished.emit(0, len(items))
            return
        settings = ExportSettings(
            max_dimension=max_dimension if max_dimension > 0 else None,
            jpeg_quality=jpeg_quality,
            add_numbers=add_numbers,
            watermark_text=watermark_text or None,
        )

        def worker():
            report = export_photos(items, Path(target), settings)
            if report.failed:
                details = [
                    f"{path.name}: {reason}"
                    # strict=True: az ExportReport.reasons a failed-del
                    # mindig azonos hosszú (ld. export/exporter.py docstring).
                    for path, reason in zip(report.failed, report.reasons, strict=True)
                ][: self._EXPORT_FAILED_DETAILS_LIMIT]
                self.exportFailedDetails.emit(details)
            self.exportFinished.emit(len(report.exported), len(report.failed))

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-export")

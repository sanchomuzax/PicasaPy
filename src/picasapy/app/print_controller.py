"""PrintController: kijelölt képek nyomtatása (#32, RÉSZLEGES kör) —
egyszerű, Picasa-szellemű elrendezés (teljes oldal / oldalhoz igazítva,
egy kép egy oldal). A Picasa teljes nyomtatási sablonrendszere
(`print.fen`/`reviewprint.fen`, kontaktlap, több kép egy oldalon) NEM
ebben a körben készül el.

Önálló QObject — a `WebExportController`/`RelocateController` mintáját
követve NEM az `AppController` mixinje, hogy a `controller.py`/`Main.qml`
(forró fájlok, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést
kapja az INTEGRÁTOR lépésében:

1. `application.py`: `PrintController(photo_source=...)` példányosítás —
   a `photo_source` egy hívható, ami a jelenleg megnyitott mappa/album
   `PhotoRecord`-jait adja vissza (`lambda: app_controller._photos.photos`,
   a `WebExportController` mintájára) + `setContextProperty("printController", ...)`.
2. `Main.qml`/`TrayBar.qml`: a `TrayBar.printRequested()` jelzés (MÁR kész
   ebben a jegyben) elkapása, egy nyomtatási QML-dialógus megnyitása
   (nyomtató-választó a `listPrinters()` alapján, FIT/FILL, tájolás), majd
   `printController.printRows(...)` hívása.

FONTOS Qt-korlát: az app `QGuiApplication`-t használ (nem `QApplication`),
ezért a natív, `QWidget`-alapú `QPrintDialog` NEM nyitható meg — ez a
modul ezért `listPrinters()`-t ad a QML-nek egy saját, egyszerű
nyomtató-választóhoz a natív dialógus helyett (szándékos döntés, nem
hiányosság).

A nyomtatási feladat EGYETLEN tájolást használ (a kijelölés első képéhez
igazítva, ha `orientation="auto"`) — a Qt `QPrinter` tájolása csak az
első oldal `QPainter.begin()`-je ELŐTT állítható be megbízhatóan, a
képenkénti tájolásváltás így nem lenne robosztus (ld. `_paint_pages`)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QObject, QRectF, Signal, Slot
from PySide6.QtGui import QImage, QPageLayout, QPainter
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo

from picasapy.index import PhotoRecord
from picasapy.printing.layout import (
    PageGeometry,
    PrintFitMode,
    PrintOrientation,
    compute_print_layout,
    resolve_orientation,
)

from .collage_draft_guard import CollageDraftGuard
from .formatting import to_local_path

_log = logging.getLogger(__name__)

# a margón belüli terület köré hagyott margó — az egyszerű elrendezés
# rögzített értéke (a részletes sablonrendszer, benne az állítható margóval,
# NEM ebben a körben készül el, ld. a modul docstringje)
_MARGIN_MM = 5.0


class PrintController(QObject):
    """A nyomtatás-előkészítés (PDF-be renderelés, teszthető) és a tényleges
    nyomtatás (`QPrinter` élő nyomtatóra) közös rajzoló-logikája."""

    printFinished = Signal(str)  # kimeneti fájl vagy nyomtató neve
    printFailed = Signal(str)
    #: #1472: a feladatból KIMARADT képek fájlneve. A `QImage` nem nyit meg
    #: videót és a legtöbb RAW-t — a rácsban viszont MINDKETTŐ látszik (a
    #: bélyegkép elkészül), és a képtálca nyomtatás-gombja rájuk is élő.
    #: Enélkül a felhasználó „Kész"-t látott, miközben egy kép kimaradt.
    printSkipped = Signal(list)

    def __init__(
        self,
        photo_source: Callable[[], Sequence[PhotoRecord]],
        parent: QObject | None = None,
    ) -> None:
        """`photo_source`: hívható, ami a jelenleg kiválasztott mappa/album
        `PhotoRecord`-jait adja vissza (ld. a modul docstringje)."""
        super().__init__(parent)
        self._photo_source = photo_source
        # #1072: a piszkozat-tilalom szövege és felismerése — közös a
        # `EmailController`-rel, ezért külön objektum (ld. ott a docstringet)
        self._draft_guard = CollageDraftGuard(self)

    @Slot(result=list)
    def listPrinters(self) -> list[str]:
        """Az elérhető nyomtatók neve — a natív `QPrintDialog` helyett
        (ld. a modul docstringje) a QML saját választólistájához."""
        return list(QPrinterInfo.availablePrinterNames())

    def _resolve_paths(self, rows: Sequence[int]) -> list[Path]:
        photos = tuple(self._photo_source())
        paths: list[Path] = []
        for row in rows:
            index = int(row)
            if 0 <= index < len(photos):
                paths.append(Path(photos[index].folder_path) / photos[index].name)
        return paths

    @Slot(list, str, str, str, result=bool)
    def renderPrintPreviewPdf(
        self, rows, fit_mode: str, orientation: str, output_path: str
    ) -> bool:
        """Determinisztikus, headless-ben tesztelhető nyomtatás-előkészítés:
        a kijelölt képek PDF-be renderelése (`QPrinter.PdfFormat`), egy
        oldal képenként. A `printRows` ugyanezt a `_paint_pages`-t hívja
        élő `QPrinter`-rel."""
        target = to_local_path(output_path)
        if not target:
            self.printFailed.emit(self.tr("Invalid output path."))
            return False
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(target)
        ok = self._run(printer, rows, fit_mode, orientation)
        if ok:
            self.printFinished.emit(target)
        return ok

    @Slot(list, str, str, str, result=bool)
    def printRows(
        self, rows, printer_name: str, fit_mode: str, orientation: str
    ) -> bool:
        """A kijelölt képek nyomtatása a megadott (üres `printer_name`
        esetén a rendszer alapértelmezett) nyomtatóra."""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if printer_name:
            info = QPrinterInfo.printerInfo(printer_name)
            if info.isNull():
                self.printFailed.emit(
                    self.tr("Unknown printer: %1").replace("%1", printer_name)
                )
                return False
            printer.setPrinterName(printer_name)
        ok = self._run(printer, rows, fit_mode, orientation)
        if ok:
            self.printFinished.emit(printer.printerName() or self.tr("default printer"))
        return ok

    def _run(
        self, printer: QPrinter, rows: Sequence[int], fit_mode: str, orientation: str
    ) -> bool:
        paths = self._resolve_paths(rows)
        if not paths:
            self.printFailed.emit(self.tr("No pictures to print."))
            return False
        # #1072: a befejezetlen kollázs NEM nyomtatható
        # (`projectutils::draft_collage`). A kapu itt áll, nem a
        # tálcagombon: a `printRows` és a `renderPrintPreviewPdf` egyaránt
        # ezen az egy ágon megy át, tehát a felület későbbi bekötése nem
        # kerülheti meg.
        if self._draft_guard.first_draft(paths) is not None:
            self.printFailed.emit(self._draft_guard.restriction_message())
            return False
        try:
            mode = PrintFitMode(fit_mode) if fit_mode else PrintFitMode.FIT
            requested = (
                PrintOrientation(orientation) if orientation else PrintOrientation.AUTO
            )
        except ValueError as error:
            self.printFailed.emit(str(error))
            return False

        images: list[QImage] = []
        skipped: list[str] = []
        for path in paths:
            image = QImage(str(path))
            if image.isNull():
                _log.warning("nyomtatás: nem dekódolható kép — kihagyva: %s", path)
                skipped.append(path.name)
                continue
            images.append(image)
        if not images:
            # ⚠️ a csak-videós (vagy csak-RAW) kijelölésnél a „Nincs
            # nyomtatható kép." FÉLREVEZET: a felhasználó képeket JELÖLT KI,
            # és bélyegképet is lát róluk. Nevezzük meg, mi nem ment át.
            if skipped:
                self.printFailed.emit(
                    self.tr("None of the selected pictures could be printed: %1")
                    .replace("%1", ", ".join(skipped))
                )
            else:
                self.printFailed.emit(self.tr("No pictures to print."))
            return False
        if skipped:
            # a többi kimegy — de a kihagyás NEM tűnhet el a naplóban
            self.printSkipped.emit(skipped)

        # a teljes feladat egy tájolást használ (ld. a modul docstringje) —
        # az első képhez igazítva, ha "auto"
        orientation_for_job = resolve_orientation(
            images[0].width(), images[0].height(), requested
        )
        printer.setPageOrientation(
            QPageLayout.Orientation.Landscape
            if orientation_for_job == PrintOrientation.LANDSCAPE
            else QPageLayout.Orientation.Portrait
        )
        # #1472: a `_paint_pages` `RuntimeError`-t dob, ha a Qt nem tudja
        # elindítani a feladatot (nem írható PDF-célfájl, elérhetetlen
        # nyomtató). Amíg a vezérlő nem volt bekötve, ez senkit nem zavart;
        # QML-slotból viszont a kivétel NÉMÁN elvész (csak a naplóba kerül),
        # és a felhasználó egy néma párbeszédet néz. Jelzést kell kapnia.
        try:
            self._paint_pages(printer, images, mode)
        except RuntimeError:
            _log.exception("nyomtatás: a feladat nem indítható")
            self.printFailed.emit(self.tr("The print job could not be started."))
            return False
        return True

    @staticmethod
    def _paint_pages(
        printer: QPrinter, images: Sequence[QImage], mode: PrintFitMode
    ) -> None:
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("A nyomtatási feladat nem indítható")
        try:
            margin_px = _MARGIN_MM / 25.4 * printer.resolution()
            for index, image in enumerate(images):
                if index > 0:
                    printer.newPage()
                rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                margin = min(margin_px, rect.width() / 2 - 1, rect.height() / 2 - 1)
                page = PageGeometry(
                    width=rect.width(), height=rect.height(), margin=max(margin, 0)
                )
                placement = compute_print_layout(
                    page, image.width(), image.height(), mode
                )
                target_rect = QRectF(
                    rect.x() + placement.x,
                    rect.y() + placement.y,
                    placement.width,
                    placement.height,
                )
                painter.drawImage(target_rect, image)
        finally:
            painter.end()

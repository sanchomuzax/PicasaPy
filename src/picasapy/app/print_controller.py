"""PrintController: kijelölt képek nyomtatása (#32, RÉSZLEGES kör) —
egyszerű, Picasa-szellemű elrendezés (teljes oldal / oldalhoz igazítva,
egy kép egy oldal), és #1590 óta az INDEXKÉP is (több bélyegkép egy
lapon, `printContactSheet`). A Picasa teljes nyomtatási sablonrendszere
(`print.fen`/`reviewprint.fen`, a `ytPrintSizes` mind a 17 mérete) NEM
ebben a körben készül el — a `ytPrintSizes::eContact` („Indexképek")
viszont igen.

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

from PySide6.QtCore import QObject, QRectF, Qt, Signal, Slot
from PySide6.QtGui import QFont, QImage, QPageLayout, QPainter
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo

from picasapy.index import PhotoRecord
from picasapy.printing.contact_sheet import (
    DEFAULT_COLUMNS,
    header_rect,
    sheet_pages,
)
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
        tray_source: Callable[[], Sequence[PhotoRecord]] | None = None,
    ) -> None:
        """`photo_source`: hívható, ami a jelenleg kiválasztott mappa/album
        `PhotoRecord`-jait adja vissza (ld. a modul docstringje)."""
        super().__init__(parent)
        self._photo_source = photo_source
        #: #1671: a KÉPTÁLCA rekordjai. Ha nem üres, ŐK a forrás — a rács
        #: pillanatnyi kijelölése és a látott mappa nem számít. Az eredeti
        #: súgója is így fogalmaz: „Print photos in the Photo Tray". A
        #: mező elhagyható, hogy a meglévő hívók és tesztek ne törjenek el.
        self._tray_source = tray_source
        # #1072: a piszkozat-tilalom szövege és felismerése — közös a
        # `EmailController`-rel, ezért külön objektum (ld. ott a docstringet)
        self._draft_guard = CollageDraftGuard(self)

    @Slot(result=list)
    def listPrinters(self) -> list[str]:
        """Az elérhető nyomtatók neve — a natív `QPrintDialog` helyett
        (ld. a modul docstringje) a QML saját választólistájához."""
        return list(QPrinterInfo.availablePrinterNames())

    def _resolve_records(self, rows: Sequence[int]) -> list[PhotoRecord]:
        """A művelet bemenete — #1671: HA A TÁLCA NEM ÜRES, ŐK nyernek.

        A rács pillanatnyi kijelölése és a látott mappa ilyenkor nem
        számít: a tálca épp arra való, hogy több mappából gyűjtött képekkel
        lehessen dolgozni. Az eredeti súgója is így fogalmaz — *„Print
        photos in the Photo Tray"* —, és a mappába exportálás (#455) már
        régóta így viselkedik.

        Üres tálcánál (vagy `tray_source` nélkül) marad a régi, sor-alapú
        feloldás."""
        if self._tray_source is not None:
            talca = list(self._tray_source())
            if talca:
                return talca
        photos = tuple(self._photo_source())
        return [
            photos[int(row)]
            for row in rows
            if 0 <= int(row) < len(photos)
        ]

    def _resolve_paths(self, rows: Sequence[int]) -> list[Path]:
        return [
            Path(record.folder_path) / record.name
            for record in self._resolve_records(rows)
        ]

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

    # -- Indexkép-nyomtatás (#1590) -------------------------------------

    @Slot(list, int, str, result=bool)
    def renderContactSheetPdf(self, rows, columns: int, output_path: str) -> bool:
        """#1590: indexkép PDF-be — a `renderPrintPreviewPdf` párja.

        Ugyanaz a rajzoló fut, mint az élő nyomtatásnál (`_run_contact_sheet`),
        ezért a PDF nem „előnézet", hanem BIZONYÍTÉK: amit itt látsz, az megy
        a papírra."""
        target = to_local_path(output_path)
        if not target:
            self.printFailed.emit(self.tr("Invalid output path."))
            return False
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(target)
        ok = self._run_contact_sheet(printer, rows, columns)
        if ok:
            self.printFinished.emit(target)
        return ok

    @Slot(list, str, int, result=bool)
    def printContactSheet(self, rows, printer_name: str, columns: int) -> bool:
        """#1590: `ID_FILE_PRINTCONTACTSHEET` — több bélyegkép EGY lapon.

        Az eredetiben ez nem külön párbeszéd, hanem NYOMTATÁSI MÉRET
        (`ytPrintSizes::eContact`, „Indexképek"), ezért nálunk is a
        nyomtatás-párbeszéd egyik elrendezése, nem külön ablak.
        """
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if printer_name:
            info = QPrinterInfo.printerInfo(printer_name)
            if info.isNull():
                self.printFailed.emit(
                    self.tr("Unknown printer: %1").replace("%1", printer_name)
                )
                return False
            printer.setPrinterName(printer_name)
        ok = self._run_contact_sheet(printer, rows, columns)
        if ok:
            self.printFinished.emit(printer.printerName() or self.tr("default printer"))
        return ok

    def _header_lines(self, records: Sequence[PhotoRecord]) -> tuple[str, str]:
        """A nyomtatott indexkép fejlécének KÉT sora.

        ⚠️ Ez NEM a kollázs-indexkép fejléce. Az eredeti nyomtatója
        CÍMKÉZETT mezőket rajzol — `ytPrinter::contactsheetalbum` = „Album:"
        és `ytPrinter::contactsheetdate` = „Dátum:" —, míg a kollázs a
        `CContactSheetTheme::subtitle_format` („%1$d kép, %2$s") mintát
        követi. A #1590 jegy „ugyanaz, mint a kollázs" előírása ezen a
        ponton MEGDŐLT; a rács viszont tényleg közös
        (`printing.contact_sheet` a `collage.layout`-ra épül).

        Album híján az eredeti `ytPrinter::unnamedalbum` = „Név nélküli
        album" felirata áll a helyén."""
        album = ""
        datum = ""
        if records:
            album = Path(records[0].folder_path).name
            nyers = (records[0].taken_at or "").strip()
            # a `taken_at` ISO-alakú („2023-11-04 18:20:11"); a fejlécen a
            # NAP elég — az óra-percnek egy egész lapra nézve nincs értelme
            datum = nyers[:10]
        if not album:
            album = self.tr("Unnamed Album")
        fejlec = self.tr("Album:") + " " + album
        alcim = (self.tr("Date:") + " " + datum) if datum else ""
        return fejlec, alcim

    def _run_contact_sheet(
        self, printer: QPrinter, rows: Sequence[int], columns: int
    ) -> bool:
        """Az indexkép-feladat közös útja (PDF és élő nyomtató egyaránt)."""
        records = self._resolve_records(rows)
        paths = [Path(r.folder_path) / r.name for r in records]
        if not paths:
            self.printFailed.emit(self.tr("No pictures to print."))
            return False
        # #1072: a befejezetlen kollázs itt sem nyomtatható — ugyanaz a
        # kapu, mint a képenkénti nyomtatásnál (`_run`)
        if self._draft_guard.first_draft(paths) is not None:
            self.printFailed.emit(self._draft_guard.restriction_message())
            return False
        oszlopok = int(columns) if int(columns or 0) > 0 else DEFAULT_COLUMNS

        images: list[QImage] = []
        maradok: list[PhotoRecord] = []
        skipped: list[str] = []
        for record, path in zip(records, paths, strict=True):
            image = QImage(str(path))
            if image.isNull():
                _log.warning("indexkép: nem dekódolható kép — kihagyva: %s", path)
                skipped.append(path.name)
                continue
            images.append(image)
            maradok.append(record)
        if not images:
            if skipped:
                self.printFailed.emit(
                    self.tr("None of the selected pictures could be printed: %1")
                    .replace("%1", ", ".join(skipped))
                )
            else:
                self.printFailed.emit(self.tr("No pictures to print."))
            return False
        if skipped:
            self.printSkipped.emit(skipped)

        # ⚠️ az indexkép tájolása NEM a képekhez igazodik: egy lapon sok kép
        # van, tehát nincs olyan, hogy „a kép tájolása". Marad a papír
        # alapértelmezett (portré) állása — ezt kínálja az eredeti is.
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        fejlec, alcim = self._header_lines(maradok)
        try:
            self._paint_contact_sheet(printer, images, oszlopok, fejlec, alcim)
        except (RuntimeError, ValueError):
            _log.exception("indexkép-nyomtatás: a feladat nem indítható")
            self.printFailed.emit(self.tr("The print job could not be started."))
            return False
        return True

    @staticmethod
    def _paint_contact_sheet(
        printer: QPrinter,
        images: Sequence[QImage],
        columns: int,
        header: str,
        subtitle: str,
    ) -> None:
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("A nyomtatási feladat nem indítható")
        try:
            margin_px = _MARGIN_MM / 25.4 * printer.resolution()
            rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            margin = min(margin_px, rect.width() / 2 - 1, rect.height() / 2 - 1)
            page = PageGeometry(
                width=rect.width(), height=rect.height(), margin=max(margin, 0)
            )
            lapok = sheet_pages(len(images), page, columns)
            fx, fy, fw, fh = header_rect(page)
            cim_font = QFont(painter.font())
            cim_font.setPixelSize(max(8, int(fh * 0.42)))
            alcim_font = QFont(cim_font)
            alcim_font.setPixelSize(max(7, int(fh * 0.28)))
            for lap_index, lap in enumerate(lapok):
                if lap_index > 0:
                    printer.newPage()
                painter.setFont(cim_font)
                painter.drawText(
                    QRectF(rect.x() + fx, rect.y() + fy, fw, fh * 0.6),
                    int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                    header,
                )
                if subtitle:
                    painter.setFont(alcim_font)
                    painter.drawText(
                        QRectF(
                            rect.x() + fx, rect.y() + fy + fh * 0.6, fw, fh * 0.4
                        ),
                        int(
                            Qt.AlignmentFlag.AlignLeft
                            | Qt.AlignmentFlag.AlignVCenter
                        ),
                        subtitle,
                    )
                for cell_index, cell in enumerate(lap.placements):
                    image = images[lap.first + cell_index]
                    # a cella TELJES képet mutat (nincs vágás — ez az
                    # indexkép lényege), arányosan, középre igazítva
                    cella = PageGeometry(
                        width=cell.width, height=cell.height, margin=0.0
                    )
                    hely = compute_print_layout(
                        cella, image.width(), image.height(), PrintFitMode.FIT
                    )
                    painter.drawImage(
                        QRectF(
                            rect.x() + cell.x + hely.x,
                            rect.y() + cell.y + hely.y,
                            hely.width,
                            hely.height,
                        ),
                        image,
                    )
        finally:
            painter.end()

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

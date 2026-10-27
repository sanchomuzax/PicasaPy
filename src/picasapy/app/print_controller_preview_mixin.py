"""A nyomtatási előnézet lapozásának és rajzolásának témamixinje."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QStandardPaths, QUrl, Qt, Slot
from PySide6.QtGui import QImage, QPainter, QPen
from PySide6.QtPrintSupport import QPrinter
from collections.abc import Callable, Sequence
from .formatting import to_local_path
from pathlib import Path
from picasapy.index import PhotoRecord
from picasapy.printing.contact_sheet import DEFAULT_COLUMNS, sheet_pages
from picasapy.printing.grid_layout import GridPage
from picasapy.printing.layout import (
    PageGeometry,
    PrintFitMode,
    PrintOrientation,
    compute_print_layout,
)
from picasapy.printing.options import PrintOptions, argb_to_qcolor
from picasapy.printing.resample import lanczos_resize
from .print_controller_settings_mixin import PrintControllerSettingsMixin
from .print_controller_shared import _ELONEZET_DPI


class PrintControllerPreviewMixin:
    @Slot(result=str)
    def previewImageUrl(self) -> str:  # noqa: N802 — QML-stílus
        """Az előnézeti PNG helye (#1819) — EGYETLEN fájl, felülírva, URL-ként.

        A fájl a Qt gyorsítótár-könyvtárában él, nem a munkakönyvtárban: a
        lapozás így nem szemetel a képek mellé, és a rendszer magától
        takarít, ha a hely fogy.

        ⚠️ URL-t ad vissza, nem útvonalat, és a `QUrl.fromLocalFile`-on át
        (#1019): a kézzel összefűzött `"file://" + útvonal` Windowson a
        meghajtóbetűt PORTNAK látja, `#`-es névnél pedig Linuxon is elvágja
        a nevet. A `renderPreviewPage` a `to_local_path`-en át fogadja
        vissza, tehát ugyanez az URL adható neki célként."""
        gyoker = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
        if not gyoker:
            gyoker = str(Path.home())
        mappa = Path(gyoker) / "print-preview"
        mappa.mkdir(parents=True, exist_ok=True)
        return QUrl.fromLocalFile(str(mappa / "page.png")).toString()

    @Slot(list, str, str, int, int, str, result=bool)
    @Slot(list, str, str, int, int, str, str, result=bool)
    def renderPreviewPage(  # noqa: N802 — QML-stílus
        self,
        rows,
        fit_mode: str,
        orientation: str,
        copies: int,
        page_index: int,
        output_path: str,
        printer_name: str = "",
    ) -> bool:
        """EGY LAP előnézete PNG-be (#1819, #3647) — a lapozó előnézet
        forrása.

        Miért nem a `renderPrintPreviewPdf` egy oldala: azt a `QPrinter`
        rajzolja, headless gépen (nincs nyomtató) esetleg A4-re esve vissza
        néma módon; az előnézetnek MINDIG kell egy lapja, akkor is, ha a
        párbeszéd PDF-be dolgozik.

        #3647: a lap a PAPÍRT mutatja, rajta a nyomatméretű CELLÁKKAL — nem
        egyetlen képet a nyomatméret arányában (ld. a #2494-lecke: kirajzolt
        képen mérünk, nem számolva). A tördelés (a rács, a laptörés, a
        tájolás-választás) UGYANAZ, mint az élő nyomtatásé
        (`_run`/`_paint_pages`), csak más a vászon (PNG, `_ELONEZET_DPI`-n)."""
        target = to_local_path(output_path)
        if not target:
            return False
        records = self._resolve_records(rows)
        kep_parok = []
        for record in records:
            kep = self._render_photo(record)
            if not kep.isNull():
                kep_parok.append((kep, record))
        darab = max(1, int(copies or 1))
        kep_parok = [par for par in kep_parok for _ in range(darab)]
        if not kep_parok:
            return False
        kepek = [par[0] for par in kep_parok]
        rekordok = [par[1] for par in kep_parok]

        try:
            mode = PrintFitMode(fit_mode) if fit_mode else PrintFitMode.FIT
            kert = PrintOrientation(orientation) if orientation else PrintOrientation.AUTO
        except ValueError:
            return False

        meret = self._aktiv_meret()
        portrait_page = self._preview_page_geometry(printer_name, landscape=False)
        landscape_page = self._preview_page_geometry(printer_name, landscape=True)
        try:
            _fekvo, page, grid = self._grid_for_job(
                portrait_page,
                landscape_page,
                meret.szeles_huvelyk * _ELONEZET_DPI,
                meret.magas_huvelyk * _ELONEZET_DPI,
                len(kepek),
                kert,
            )
        except ValueError:
            return False
        if not 0 <= int(page_index) < len(grid):
            return False
        lap_adat = grid[int(page_index)]

        lap = QImage(
            int(round(page.width)),
            int(round(page.height)),
            QImage.Format.Format_RGB32,
        )
        lap.fill(Qt.GlobalColor.white)
        options = self._print_options()
        painter = QPainter()
        if not painter.begin(lap):
            return False
        try:
            for offset, cell in enumerate(lap_adat.cells):
                cell_rect = QRectF(cell.x, cell.y, cell.width, cell.height)
                # #3685 (4. lelet): Crop to Fit (FILL) módban a kép a
                # cellánál nagyobbra nőhet — az előnézetnek UGYANÚGY vágnia
                # kell cellánként, mint az élő nyomtatásnak, különben a
                # levágott rész átlógna a szomszéd cellába.
                painter.save()
                painter.setClipRect(cell_rect)
                self._draw_options_page(
                    painter,
                    cell_rect,
                    kepek[lap_adat.first + offset],
                    rekordok[lap_adat.first + offset],
                    mode,
                    options,
                    _ELONEZET_DPI,
                    self._print_resampler_radius(),
                    self._printer_job_output_scale(),
                    use_proxy=self.printProxyPreview(),
                )
                painter.restore()
        finally:
            painter.end()
        return bool(lap.save(target, "PNG"))

    @Slot(list, int, result=int)
    @Slot(list, int, str, result=int)
    @Slot(list, int, str, str, result=int)
    def printPageCount(  # noqa: N802
        self, rows, copies: int = 1, orientation: str = "", printer_name: str = ""
    ) -> int:
        """Hány LAP lenne a nyomtatásból (#1819, #3647) — a lapozó előnézet
        `%d / %d` kijelzéséhez.

        #3647: a nyomatméretet CELLÁNAK tekintve, a papír nyomtatható
        területén rácsba rendezve számol — nem képenként egy lapot. Csak a
        DEKÓDOLHATÓ képek kapnak cellát: a kihagyott (videó, sérült) fájlok
        lapot sem kapnak."""
        darab = 0
        for record in self._resolve_records(rows):
            if self._is_printable(record):
                darab += 1
        count = darab * max(1, int(copies or 1))
        if count < 1:
            return 0
        try:
            kert = PrintOrientation(orientation) if orientation else PrintOrientation.AUTO
        except ValueError:
            kert = PrintOrientation.AUTO
        meret = self._aktiv_meret()
        portrait_page = self._preview_page_geometry(printer_name, landscape=False)
        landscape_page = self._preview_page_geometry(printer_name, landscape=True)
        try:
            _fekvo, _page, grid = self._grid_for_job(
                portrait_page,
                landscape_page,
                meret.szeles_huvelyk * _ELONEZET_DPI,
                meret.magas_huvelyk * _ELONEZET_DPI,
                count,
                kert,
            )
        except ValueError:
            return 0
        return len(grid)

    @Slot(list, int, result=int)
    @Slot(list, int, str, result=int)
    def contactPageCount(  # noqa: N802
        self, rows, columns: int, printer_name: str = ""
    ) -> int:
        """Hány LAP lenne az indexkép-nyomtatásból (#3712) — a darabszám-sor
        ehhez mondja a tényleges lapszámot, ugyanúgy, ahogy a méret szerinti
        nyomtatásnál a `printPageCount` teszi.

        A tájolás itt SZÁNDÉKOSAN mindig portré: az élő indexkép-nyomtatás
        (`_run_contact_sheet`) is a papír alapértelmezett állását tartja,
        mert egy lapon sok kép van, nincs „a kép tájolása" (ld. ott a
        megjegyzést)."""
        darab = 0
        for record in self._resolve_records(rows):
            if self._is_printable(record):
                darab += 1
        if darab < 1:
            return 0
        oszlopok = int(columns) if int(columns or 0) > 0 else DEFAULT_COLUMNS
        page = self._preview_page_geometry(printer_name, landscape=False)
        try:
            return len(sheet_pages(darab, page, oszlopok))
        except ValueError:
            return 0

    @staticmethod
    def _resampled_for_target(
        image: QImage,
        target: QRectF,
        radius: int | None,
        printer_output_scale: float = 1.0,
    ) -> QImage:
        """Downsample to the final cell with the selected Lanczos kernel.

        Upscaling is left to QPainter, avoiding a temporary image larger than
        the source. The same target geometry and clipping remain in use for
        both quality choices.
        """
        if radius is None or image.isNull():
            return image
        if printer_output_scale not in (0.5, 1.0):
            printer_output_scale = 1.0
        width = max(1, round(target.width() * printer_output_scale))
        height = max(1, round(target.height() * printer_output_scale))
        scale = min(width / image.width(), height / image.height(), 1.0)
        if scale >= 1.0:
            return image
        return lanczos_resize(
            image,
            max(1, round(image.width() * scale)),
            max(1, round(image.height() * scale)),
            radius,
        )

    @staticmethod
    def _proxy_for_target(image: QImage, target: QRectF) -> QImage:
        """Gyors, célméretű előnézeti proxy előállítása."""
        if image.isNull():
            return image
        width = max(1, round(target.width()))
        height = max(1, round(target.height()))
        scale = min(width / image.width(), height / image.height(), 1.0)
        if scale >= 1.0:
            return image
        return image.scaled(
            max(1, round(image.width() * scale)),
            max(1, round(image.height() * scale)),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

    @staticmethod
    def _draw_options_page(
        painter: QPainter,
        page_rect: QRectF,
        image: QImage,
        record: PhotoRecord,
        mode: PrintFitMode,
        options: PrintOptions,
        dpi: float,
        resampler_radius: int | None = None,
        printer_output_scale: float = 1.0,
        *,
        use_proxy: bool = False,
    ) -> None:
        """Egy oldal képe, szegélye és felirata közös geometriával.

        ⛔ **Önhelyesbítés (#3685 átnézése):** ez a metódus a `page_rect`-et
        korábban egy TELJES lapnak tekintette, és emiatt még egy `_MARGIN_MM`
        margót levont a szélein — de a #3647 óta a `page_rect` MÁR egy
        RÁCSCELLA, aminek a lap-margóját a `grid_layout.grid_pages` a cella
        POZÍCIÓJÁBAN már érvényesítette. A kettős margó az előnézetet
        (`renderPreviewPage`) és a szegély-/felirat-ágas nyomtatást
        (`_paint_pages_with_options`) SZŰKEBB képterületre rajzolta, mint az
        egyszerű ág (`_paint_pages`) — a cella belseje itt margó nélküli,
        pontosan úgy, ahogy az egyszerű ág is kezeli."""
        page = PageGeometry(width=page_rect.width(), height=page_rect.height(), margin=0.0)
        text = PrintControllerSettingsMixin._caption_text(record, options)
        font = PrintControllerSettingsMixin._font_for_print(options, dpi)
        caption_height = 0.0
        if text and options.textPlacement == 0:
            caption_height = min(
                page.printable_height * 0.25,
                max(float(font.pixelSize() + 8), float(font.pixelSize() * 3)),
            )
        content_height = max(1.0, page.height - caption_height)
        content_page = PageGeometry(
            width=page.width,
            height=min(page.height, content_height),
            margin=0.0,
        )
        placement = compute_print_layout(content_page, image.width(), image.height(), mode)
        target = QRectF(
            page_rect.x() + placement.x,
            page_rect.y() + placement.y,
            placement.width,
            placement.height,
        )
        source = (
            PrintControllerPreviewMixin._proxy_for_target(image, target)
            if use_proxy
            else PrintControllerPreviewMixin._resampled_for_target(
                image, target, resampler_radius, printer_output_scale
            )
        )
        painter.drawImage(target, source)

        border_width = PrintControllerSettingsMixin._border_width(options, page)
        if options.border and border_width > 0:
            color = argb_to_qcolor(options.borderColor)
            if options.borderEdge:
                painter.setPen(QPen(color, max(1.0, border_width)))
                painter.drawLine(target.bottomLeft(), target.bottomRight())
            else:
                if options.evenBorder:
                    painter.setPen(QPen(color, max(1.0, border_width)))
                    painter.drawRect(target)
                else:
                    painter.setPen(QPen(color, max(1.0, border_width / 2)))
                    painter.drawRect(target)
                    painter.setPen(QPen(color, max(1.0, border_width)))
                    painter.drawLine(target.bottomLeft(), target.bottomRight())

        if not text:
            return
        painter.setFont(font)
        painter.setPen(argb_to_qcolor(options.textColor))
        flags = int(Qt.AlignmentFlag.AlignCenter)
        if options.wrap:
            flags |= int(Qt.TextFlag.TextWordWrap)
        else:
            flags |= int(Qt.TextFlag.TextSingleLine)

        if options.textPlacement == 1:
            caption_rect = target
        elif options.textPlacement == 2 and options.border and border_width > 0:
            caption_rect = QRectF(
                target.left(),
                target.bottom() - max(border_width, font.pixelSize() + 2),
                target.width(),
                max(border_width, font.pixelSize() + 2),
            )
        else:
            caption_rect = QRectF(
                page_rect.x(),
                page_rect.y() + content_page.height,
                page.printable_width,
                max(font.pixelSize() + 4, page.height - content_page.height),
            )
        painter.drawText(caption_rect, flags, text)

    @staticmethod
    def _paint_pages_with_options(
        printer: QPrinter,
        grid: Sequence[GridPage],
        images: Sequence[QImage],
        records: Sequence[PhotoRecord],
        mode: PrintFitMode,
        options: PrintOptions,
        lap_kesz: Callable[[int, int], None] | None = None,
        resampler_radius: int | None = None,
        printer_output_scale: float = 1.0,
    ) -> None:
        """A printoptions-ág lapfestése PDF-re és élő QPrinterre.

        #3647: laponként a `grid` cellái szerint fest — egy lapon TÖBB kép
        is lehet (a nyomatméret CELLA), nem csak egy.

        #3685 (4. lelet): Crop to Fit (`FILL`) módban a kép a cellánál
        NAGYOBBRA is nőhet (a hosszabb irány levágódik) — a `painter`
        vágóterületét ezért CELLÁNKÉNT a cella téglalapjára korlátozzuk,
        különben a levágott rész átlógna a szomszéd cellába."""
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("A nyomtatási feladat nem indítható")
        ossz = len(grid)
        try:
            for index, lap in enumerate(grid):
                if index > 0:
                    printer.newPage()
                for offset, cell in enumerate(lap.cells):
                    cell_rect = QRectF(cell.x, cell.y, cell.width, cell.height)
                    painter.save()
                    painter.setClipRect(cell_rect)
                    PrintControllerPreviewMixin._draw_options_page(
                        painter,
                        cell_rect,
                        images[lap.first + offset],
                        records[lap.first + offset],
                        mode,
                        options,
                        float(printer.resolution()),
                        resampler_radius,
                        printer_output_scale,
                    )
                    painter.restore()
                if lap_kesz is not None:
                    lap_kesz(index + 1, ossz)
        finally:
            painter.end()

    @staticmethod
    def _paint_pages(
        printer: QPrinter,
        grid: Sequence[GridPage],
        images: Sequence[QImage],
        mode: PrintFitMode,
        lap_kesz: Callable[[int, int], None] | None = None,
        resampler_radius: int | None = None,
        printer_output_scale: float = 1.0,
    ) -> None:
        """A lapok megfestése; `lap_kesz(kész, összes)` LAPONKÉNT (#3016).

        #3647: a nyomatméret CELLA — egy lapon a `grid` szerint TÖBB kép is
        lehet, rácsba rendezve, nem csak egy (ld. `grid_layout.grid_pages`).

        A visszahívás alapértelmezésben `None` — a rajzolás így önmagában
        is használható marad (teszt, előnézet), jelzés nélkül.

        #3685 (4. lelet): Crop to Fit (`FILL`) módban a kép a cellánál
        NAGYOBBRA is nőhet — cellánként vágóterületre korlátozzuk a
        `painter`-t, különben a levágott rész átlógna a szomszéd cellába."""
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("A nyomtatási feladat nem indítható")
        ossz = len(grid)
        try:
            for index, lap in enumerate(grid):
                if index > 0:
                    printer.newPage()
                for offset, cell in enumerate(lap.cells):
                    image = images[lap.first + offset]
                    placement = compute_print_layout(
                        PageGeometry(width=cell.width, height=cell.height, margin=0.0),
                        image.width(),
                        image.height(),
                        mode,
                    )
                    target_rect = QRectF(
                        cell.x + placement.x,
                        cell.y + placement.y,
                        placement.width,
                        placement.height,
                    )
                    painter.save()
                    painter.setClipRect(QRectF(cell.x, cell.y, cell.width, cell.height))
                    painter.drawImage(
                        target_rect,
                        PrintControllerPreviewMixin._resampled_for_target(
                            image,
                            target_rect,
                            resampler_radius,
                            printer_output_scale,
                        ),
                    )
                    painter.restore()
                if lap_kesz is not None:
                    lap_kesz(index + 1, ossz)
        finally:
            painter.end()

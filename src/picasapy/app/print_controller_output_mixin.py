"""A nyomtatási feladatok és kimenetek témamixinje."""

from __future__ import annotations

import time
from PySide6.QtCore import QCoreApplication, QRectF, Qt, Slot
from PySide6.QtGui import QFont, QImage, QPageLayout, QPageSize, QPainter
from PySide6.QtPrintSupport import QPrinter
from collections.abc import Sequence
from .formatting import to_local_path
from pathlib import Path
from picasapy.app.busy_registry import get_app_busy_registry
from picasapy.index import PhotoRecord
from picasapy.printing.contact_sheet import DEFAULT_COLUMNS, header_rect, sheet_pages
from picasapy.printing.dpi import NyomatMeret
from picasapy.printing.grid_layout import (
    GridPage,
    choose_page_orientation,
    full_page_pages,
    grid_pages,
)
from picasapy.printing.layout import (
    PageGeometry,
    PrintFitMode,
    PrintOrientation,
    compute_print_layout,
)
from picasapy.printing.options import has_render_effects
from .print_controller_preview_mixin import PrintControllerPreviewMixin
from .print_controller_shared import _ELONEZET_DPI, _MARGIN_MM, _log


class PrintControllerOutputMixin:
    @Slot(list, str, str, str, result=bool)
    @Slot(list, str, str, str, int, result=bool)
    def renderPrintPreviewPdf(
        self,
        rows,
        fit_mode: str,
        orientation: str,
        output_path: str,
        copies: int = 1,
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
        ok = self._run(printer, rows, fit_mode, orientation, copies)
        if ok:
            self.printFinished.emit(target)
        return ok

    @Slot(list, str, str, str, result=bool)
    @Slot(list, str, str, str, int, result=bool)
    def printRows(
        self,
        rows,
        printer_name: str,
        fit_mode: str,
        orientation: str,
        copies: int = 1,
    ) -> bool:
        """A kijelölt képek nyomtatása a megadott (üres `printer_name`
        esetén a rendszer alapértelmezett) nyomtatóra."""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if printer_name:
            info = self._printer_info_api().printerInfo(printer_name)
            if info.isNull():
                self.printFailed.emit(self.tr("Unknown printer: %1").replace("%1", printer_name))
                return False
            printer.setPrinterName(printer_name)
        # #2103: ha a felhasználó járt a nyomtató saját beállítójánál, az
        # ottani elrendezés érvényes — enélkül a párbeszéd díszlet lenne.
        self._alkalmazd_az_oldalelrendezest(printer)
        ok = self._run(printer, rows, fit_mode, orientation, copies)
        if ok:
            self.printFinished.emit(printer.printerName() or self.tr("default printer"))
        return ok

    # -- Útlevélkép (#1401) ----------------------------------------------

    @staticmethod
    def _passport_record(path: Path) -> PhotoRecord:
        """Egy AD HOC `PhotoRecord` a MÁR kivágott, ideiglenes passport-
        fájlhoz — ugyanaz a minta, mint a teszteké/webexporté (ld.
        `index/queries.py`, a `PhotoRecord` docstringje): a nyomtatási
        csővezeték egyetlen bemenete a `PhotoRecord`, tehát egy kézzel
        épített példány zökkenőmentesen átmegy rajta, index- vagy
        ini-beavatkozás nélkül. A fájl a `PassportPhotoController`
        gyorstárában él — nem a fotókönyvtárban, ld. a jegy negyedik
        feltételét („a kép maga nem módosul, tartós adat nem íródik")."""
        image = QImage(str(path))
        szeles = image.width() if not image.isNull() else None
        magas = image.height() if not image.isNull() else None
        return PhotoRecord(
            id=-1,
            folder_path=str(path.parent),
            name=path.name,
            kind="image",
            size=0,
            mtime_ns=0,
            star=False,
            caption=None,
            keywords=None,
            rotate_steps=0,
            filters=None,
            taken_at=None,
            orientation=0,
            width=szeles,
            height=magas,
        )

    @Slot(str, result=bool)
    def setPassportSource(self, image_url: str) -> bool:  # noqa: N802 — QML-stílus
        """#1401: a MÁR kivágott útlevélkép a kijelölés HELYÉRE lép.

        Amíg be van állítva, a sor-alapú feloldás (`_resolve_records`) ezt
        az egy képet adja, a nyomatméret pedig `ePassport` (2,0 × 2,0
        hüvelyk) — a lapszám, az előnézet és a nyomtatás így UGYANAZON az
        úton megy, mint bármely más méretnél. A `setPrintSize` a méretet
        felülírja, a képet nem; a `clearPassportSource` mindkettőt törli."""
        target = to_local_path(image_url)
        if not target:
            return False
        self._utlevel = self._passport_record(Path(target))
        self._meret_felulirva = NyomatMeret.PASSPORT
        return True

    @Slot()
    def clearPassportSource(self) -> None:  # noqa: N802 — QML-stílus
        """Vissza a kijelölés (vagy a képtálca) képeihez és a mentett
        nyomatmérethez."""
        self._utlevel = None
        self._meret_felulirva = None

    def _aktiv_meret(self) -> NyomatMeret:
        """A feladat nyomatmérete: az Útlevélkép felülírása, különben a
        megjegyzett méret."""
        if self._meret_felulirva is not None:
            return self._meret_felulirva
        return NyomatMeret[self.printSize()]

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
            info = self._printer_info_api().printerInfo(printer_name)
            if info.isNull():
                self.printFailed.emit(self.tr("Unknown printer: %1").replace("%1", printer_name))
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
        fejlec = QCoreApplication.translate("PrintController", "Album:") + " " + album
        alcim = (self.tr("Date:") + " " + datum) if datum else ""
        return fejlec, alcim

    def _run_contact_sheet(self, printer: QPrinter, rows: Sequence[int], columns: int) -> bool:
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
            image = self._render_photo(record)
            if image.isNull():
                _log.warning("indexkép: nem dekódolható kép — kihagyva: %s", path)
                skipped.append(path.name)
                continue
            images.append(image)
            maradok.append(record)
        if not images:
            if skipped:
                self.printFailed.emit(
                    self.tr("None of the selected pictures could be printed: %1").replace(
                        "%1", ", ".join(skipped)
                    )
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
            self._paint_contact_sheet(
                printer,
                images,
                oszlopok,
                fejlec,
                alcim,
                self._print_resampler_radius(),
                self._printer_job_output_scale(),
            )
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
        resampler_radius: int | None = None,
        printer_output_scale: float = 1.0,
    ) -> None:
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("A nyomtatási feladat nem indítható")
        try:
            margin_px = _MARGIN_MM / 25.4 * printer.resolution()
            rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            margin = min(margin_px, rect.width() / 2 - 1, rect.height() / 2 - 1)
            page = PageGeometry(width=rect.width(), height=rect.height(), margin=max(margin, 0))
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
                        QRectF(rect.x() + fx, rect.y() + fy + fh * 0.6, fw, fh * 0.4),
                        int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                        subtitle,
                    )
                for cell_index, cell in enumerate(lap.placements):
                    image = images[lap.first + cell_index]
                    # a cella TELJES képet mutat (nincs vágás — ez az
                    # indexkép lényege), arányosan, középre igazítva
                    cella = PageGeometry(width=cell.width, height=cell.height, margin=0.0)
                    hely = compute_print_layout(
                        cella, image.width(), image.height(), PrintFitMode.FIT
                    )
                    target = QRectF(
                        rect.x() + cell.x + hely.x,
                        rect.y() + cell.y + hely.y,
                        hely.width,
                        hely.height,
                    )
                    painter.drawImage(
                        target,
                        PrintControllerPreviewMixin._resampled_for_target(
                            image, target, resampler_radius, printer_output_scale
                        ),
                    )
        finally:
            painter.end()

    def _run(
        self,
        printer: QPrinter,
        rows: Sequence[int],
        fit_mode: str,
        orientation: str,
        copies: int = 1,
    ) -> bool:
        # #3016: ⛔ ÚJBÓLI INDÍTÁS TILOS. A haladás-jelzés kedvéért a festés
        # ciklusa eseményeket pörget (`processEvents`), tehát a felhasználó
        # a feladat KÖZBEN újra megnyomhatja a Nyomtatás gombot — két
        # feladat viszont ugyanarra a festőre menne. A zár nem üzenetet ad:
        # a második hívás egyszerűen nem indul el.
        if self._nyomtatas_folyamatban:
            return False
        paths = self._resolve_paths(rows)
        records = self._resolve_records(rows)
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
            requested = PrintOrientation(orientation) if orientation else PrintOrientation.AUTO
        except ValueError as error:
            # #3685 (7. lelet): a nyers kivétel-szöveg NEM fordítható — a
            # felhasználó a saját nyelvén lássa a hibát, a részletet (%1)
            # betoldva.
            self.printFailed.emit(self.tr("Invalid print settings: %1").replace("%1", str(error)))
            return False

        images: list[QImage] = []
        job_records: list[PhotoRecord] = []
        skipped: list[str] = []
        for record, path in zip(records, paths, strict=True):
            image = self._render_photo(record)
            if image.isNull():
                _log.warning("nyomtatás: nem dekódolható kép — kihagyva: %s", path)
                skipped.append(path.name)
                continue
            images.append(image)
            job_records.append(record)
        if not images:
            # ⚠️ a csak-videós (vagy csak-RAW) kijelölésnél a „Nincs
            # nyomtatható kép." FÉLREVEZET: a felhasználó képeket JELÖLT KI,
            # és bélyegképet is lát róluk. Nevezzük meg, mi nem ment át.
            if skipped:
                self.printFailed.emit(
                    self.tr("None of the selected pictures could be printed: %1").replace(
                        "%1", ", ".join(skipped)
                    )
                )
            else:
                self.printFailed.emit(self.tr("No pictures to print."))
            return False
        if skipped:
            # a többi kimegy — de a kihagyás NEM tűnhet el a naplóban
            self.printSkipped.emit(skipped)

        # #1819: KÉPENKÉNTI példányszám (`addprintsbutton`/`subprintsbutton`,
        # „Add another copy of each Photo to be printed"). Ez NEM a nyomtató
        # saját példányszám-mezője: a +/− minden képhez ad egy további
        # másolatot, tehát két kép × két példány NÉGY cellát kér (#3647: a
        # cellák a nyomtatható papíron rácsba rendeződnek, a lapszám a
        # nyomatmérettől és a papírtól függ — nem feltétlenül négy lap).
        #
        # ✅ A cellák SORRENDJE MÉRVE (#3647, `docs/specs/picasa-nyomtatas.md`,
        # „A rácselrendező LAPTÖRÉSE" 4. pontja, `0x0077896e`–`0x0077899a`):
        # kívül a képek, belül a példányok — képenként csoportosítunk (A, A,
        # B, B), ahogy a felirat is képenként fogalmaz („each Photo"); a
        # másik olvasat (A, B, A, B) a nyomtató saját példányszám-mezőjének
        # viselkedése lenne, amitől ez a vezérlő épp különbözik.
        images = self._sokszorozva(images, copies)
        darab = max(1, int(copies or 1))
        job_records = [record for record in job_records for _ in range(darab)]

        # A szegély/felirat a PDF- és nyomtató-úton is ugyanabból az
        # állapotból készül. Alapállapotban megtartjuk a régi rajzolási ágat,
        # így a meglévő sebesség- és példányszám-kapuk változatlanok.
        options = self._print_options()
        # #3647/#3685: a nyomatméretet CELLÁNAK tekintve rácsba rendezzük a
        # papír nyomtatható területén — AUTO-nál a lapállás a papíré marad,
        # a KEVESEBB lapot a CELLA tájolása dönti el; explicit kérésnél a
        # kért lapállás rögzül. Ha egyik cellatájolással sem fér el, az
        # egyképes (`eFullPage`) tartalék lép életbe (`_grid_for_job`).
        meret = self._aktiv_meret()
        dpi = float(printer.resolution())
        portrait_page = self._device_page_geometry(printer, QPageLayout.Orientation.Portrait)
        landscape_page = self._device_page_geometry(printer, QPageLayout.Orientation.Landscape)
        try:
            fekvo, _page, grid = self._grid_for_job(
                portrait_page,
                landscape_page,
                meret.szeles_huvelyk * dpi,
                meret.magas_huvelyk * dpi,
                len(images),
                requested,
            )
        except ValueError as error:
            # `_grid_for_job` a #3685 óta a `full_page_pages` tartalékra
            # esik vissza, ha a cella egyik tájolással sem fér el — ez az
            # ág gyakorlatilag csak érvénytelen (nem-pozitív) bemenetnél
            # futhat le, de a néma nyers szöveg helyett itt is fordított
            # üzenet megy ki.
            self.printFailed.emit(self.tr("Invalid print settings: %1").replace("%1", str(error)))
            return False
        # `_page` nem kell külön: a `grid` celláinak abszolút koordinátái
        # már tartalmazzák a margót (`grid_layout.grid_pages`).
        printer.setPageOrientation(
            QPageLayout.Orientation.Landscape if fekvo else QPageLayout.Orientation.Portrait
        )
        # #1472: a `_paint_pages` `RuntimeError`-t dob, ha a Qt nem tudja
        # elindítani a feladatot (nem írható PDF-célfájl, elérhetetlen
        # nyomtató). Amíg a vezérlő nem volt bekötve, ez senkit nem zavart;
        # QML-slotból viszont a kivétel NÉMÁN elvész (csak a naplóba kerül),
        # és a felhasználó egy néma párbeszédet néz. Jelzést kell kapnia.
        # #3016/#505: a hosszú feladat a KÖZÖS haladásjelzőbe is
        # bejelentkezik, hogy az alsó sáv animáljon — a `finally` zárja,
        # hibára futó feladatnál is (különben a csík örökre pörögne).
        nyilvantartas = get_app_busy_registry()
        nyilvantartas.begin()
        self._nyomtatas_folyamatban = True
        # #3016: minden feladat SAJAT ritkitas-orat kap — igy az ELSO lap
        # jelzese mindig azonnal kimegy (a felhasznalo lassa, hogy elindult),
        # nem az elozo feladat ora-allasatol fugg
        self._utolso_frissites = 0.0
        try:
            if has_render_effects(options):
                self._paint_pages_with_options(
                    printer,
                    grid,
                    images,
                    job_records,
                    mode,
                    options,
                    self._lap_kesz,
                    self._print_resampler_radius(),
                    self._printer_job_output_scale(),
                )
            else:
                self._paint_pages(
                    printer,
                    grid,
                    images,
                    mode,
                    self._lap_kesz,
                    self._print_resampler_radius(),
                    self._printer_job_output_scale(),
                )
        except RuntimeError:
            _log.exception("nyomtatás: a feladat nem indítható")
            self.printFailed.emit(self.tr("The print job could not be started."))
            return False
        finally:
            self._nyomtatas_folyamatban = False
            nyilvantartas.end()
        return True

    @staticmethod
    def _device_page_geometry(
        printer: QPrinter, orientation: "QPageLayout.Orientation"
    ) -> PageGeometry:
        """A nyomtató nyomtatható területe a MEGADOTT lapállásban (#3647).

        Mellékhatásként BEÁLLÍTJA ezt a lapállást a `printer`-en — ez így
        van rendjén: a hívó (`_run`) úgyis a végül kiválasztott lapállást
        hagyja rajta, a köztes próbálgatás a `QPainter.begin()` ELŐTT
        történik (ld. a modul fejlécét)."""
        printer.setPageOrientation(orientation)
        rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        margin_px = _MARGIN_MM / 25.4 * printer.resolution()
        margin = min(margin_px, rect.width() / 2 - 1, rect.height() / 2 - 1)
        return PageGeometry(width=rect.width(), height=rect.height(), margin=max(margin, 0.0))

    def _preview_page_geometry(self, printer_name: str, *, landscape: bool) -> PageGeometry:
        """A papír mérete az ELŐNÉZETHEZ, `_ELONEZET_DPI`-n (#3647).

        Ugyanaz a forrás, mint a `paperInfo()`-é (`_papir_elrendezes`), de
        mindkét lapállásban lekérdezve, hogy a tájolás-választás
        (`_grid_for_job`) összevethesse őket — a `paperInfo()` egyetlen,
        MÁR eldöntött lapállást mutat, ez itt a döntés bemenete."""
        elrendezes = self._papir_elrendezes(printer_name)
        meret_mm = elrendezes.pageSize().size(QPageSize.Unit.Millimeter)
        szeles_mm, magas_mm = meret_mm.width(), meret_mm.height()
        if landscape:
            szeles_mm, magas_mm = magas_mm, szeles_mm
        szeles_px = szeles_mm / 25.4 * _ELONEZET_DPI
        magas_px = magas_mm / 25.4 * _ELONEZET_DPI
        margin_px = _MARGIN_MM / 25.4 * _ELONEZET_DPI
        margin = min(margin_px, szeles_px / 2 - 1, magas_px / 2 - 1)
        return PageGeometry(width=szeles_px, height=magas_px, margin=max(margin, 0.0))

    @staticmethod
    def _grid_for_job(
        portrait_page: PageGeometry,
        landscape_page: PageGeometry,
        cell_width: float,
        cell_height: float,
        count: int,
        requested: PrintOrientation,
    ) -> tuple[bool, PageGeometry, tuple[GridPage, ...]]:
        """(fekvő-e, a választott lapgeometria, a kész lapok) — #3647.

        Explicit kérésnél (`PORTRAIT`/`LANDSCAPE`) az a lapállás rögzül.
        `AUTO`-nál — #3685 önhelyesbítés — A LAPÁLLÁS A PAPÍRÉ MARAD
        (mindig portré): a KEVESEBB lapot a CELLA `(w,h)`/`(h,w)` tájolása
        közül választjuk, döntetlennél az eredeti marad — ld.
        `grid_layout.choose_page_orientation`. (Korábban ez a metódus
        tévesen a PAPÍRT forgatta el; az élő referencia — Colab EN 29,
        „1 of 3”, ÁLLÓ A4-en két FEKVŐ 6×4 cella egymás alatt — ezt
        megdöntötte.)

        Ha a cella EGYIK cellatájolással sem fér el a nyomtatható
        területen (pl. „Teljes oldal”, vagy egy A4-nél alig nagyobb 8×10-es
        nyomat), a spec 6. pontja szerint a 0. indexű (`eFullPage`)
        elrendezővel próbálunk újra: egy kép a teljes nyomtatható
        területen, laponként (`full_page_pages`) — enélkül a nyomtatás
        `printPageCount = 0` lenne, előnézet és nyomat nélkül."""
        try:
            if requested == PrintOrientation.LANDSCAPE:
                return (
                    True,
                    landscape_page,
                    grid_pages(landscape_page, cell_width, cell_height, count),
                )
            if requested == PrintOrientation.PORTRAIT:
                return (
                    False,
                    portrait_page,
                    grid_pages(portrait_page, cell_width, cell_height, count),
                )
            _fekvo_cella, lapok = choose_page_orientation(
                portrait_page, cell_width, cell_height, count
            )
            return False, portrait_page, lapok
        except ValueError:
            fekvo = requested == PrintOrientation.LANDSCAPE
            page = landscape_page if fekvo else portrait_page
            return fekvo, page, full_page_pages(page, count)

    def _lap_kesz(self, kesz: int, ossz: int) -> None:
        """Egy lap megvan (#3016): jelzés + a felület továbbengedése.

        ⚠️ A `processEvents()` nélkül a jelzésnek nincs értelme: a festés
        végig a GUI-szálon fut, tehát a felület a feladat teljes idejére
        befagyna, és a haladás-jelzés csak a végén, egy csomóban érne
        oda. Az újbóli indítást a `_nyomtatas_folyamatban` zárja ki — ez a
        `processEvents` ára, és a `_run` kapuja fizeti meg.

        ⏱️ **A jelzés MINDIG megy, a `processEvents` ritkítva** — mérve
        (12 megapixeles fotók, PDF, RPi5): laponkénti `processEvents`
        mellett a 12 lapos feladat 2388 → 2815 ms lett, **+427 ms (+18 %)**.
        Egy lapnál és négynél a különbség a zajban maradt (+10 / −11 ms),
        tehát az ár a lapszámmal nő. A `_FRISSITES_MS` ritkítás ezt vágja
        vissza úgy, hogy a felület továbbra is a szokásos UI-válaszidőn
        belül frissül. Az UTOLSÓ lap mindig átengedi az eseményeket, hogy a
        „kész" állapot azonnal kimenjen.
        """
        self.printProgress.emit(kesz, ossz)
        app = self._core_application_api().instance()
        if app is None:
            return
        most = time.monotonic()
        utolso = kesz >= ossz
        if not utolso and (most - self._utolso_frissites) * 1000 < self._print_update_interval_ms():
            return
        self._utolso_frissites = most
        app.processEvents()

    @staticmethod
    def _sokszorozva(images: list[QImage], copies: int) -> list[QImage]:
        """A képek listája képenkénti példányszámmal (#1819).

        A `copies` alsó határa 1: a nulla vagy negatív érték nem „semmit
        ne nyomtass", hanem hibás bemenet — a felület +/− vezérlője úgyis
        egynél áll meg."""
        darab = max(1, int(copies or 1))
        if darab == 1:
            return images
        return [image for image in images for _ in range(darab)]

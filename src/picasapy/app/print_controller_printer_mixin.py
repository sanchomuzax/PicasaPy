"""A nyomtatólista és az oldalbeállítás műveleteinek témamixinje."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication, Slot
from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter


class PrintControllerPrinterMixin:
    @Slot(result=list)
    def listPrinters(self) -> list[str]:
        """Az elérhető nyomtatók neve — a natív `QPrintDialog` helyett
        (ld. a modul docstringje) a QML saját választólistájához."""
        return list(self._printer_info_api().availablePrinterNames())

    @Slot(str, result=str)
    def paperInfo(self, printer_name: str) -> str:  # noqa: N802
        """A pillanatnyi LAPBEÁLLÍTÁS emberi olvasásra (#2368).

        Az eredeti panel `printpanel/paperinfo` mezőjének megfelelője: a
        nyomtató neve mellett álló, tisztán szöveges kijelző (a bináris
        állapotfrissítője, `0x00745980`, mind a négy információs mezőt
        ugyanazzal a szövegbeállítóval tölti). A felhasználó ebből látja,
        MILYEN LAPRA fog nyomtatni — a nyomat mérete és a „kis kép"
        figyelmeztetés is ettől függ.

        A forrás sorrendje:

        1. az `openPrinterSetup`-ban elfogadott elrendezés, ha van — ez az,
           amit a következő nyomtatás ténylegesen használni fog;
        2. a nyomtató saját alapértelmezett lapmérete;
        3. végül A4 — így PDF-módban (nincs nyomtató, nincs mentett
           elrendezés) sem marad üres a mező.

        ⚠️ A SZÖVEGFORMÁTUM a miénk. A `stringres`-ben nincs hozzá kulcs,
        és az eredeti futásidőben állítja össze — a #2368 mérése ezt
        kimondottan nem adta meg. A mezőnév és a méret együtt szerepel,
        mert az „A4" önmagában nem mond méretet annak, aki nem tudja fejből.
        """
        elrendezes = self._papir_elrendezes(printer_name)
        lapmeret = elrendezes.pageSize()
        merete = lapmeret.size(QPageSize.Unit.Millimeter)
        szeles, magas = merete.width(), merete.height()
        if elrendezes.orientation() == QPageLayout.Orientation.Landscape:
            szeles, magas = magas, szeles
            tajolas = self.tr("landscape")
        else:
            tajolas = self.tr("portrait")
        # A `%1`-es alak és a `.arg()` a QString sajátja; a PySide `tr()`
        # sima `str`-t ad vissza, ezért a helyettesítés a fordítót is
        # kiszolgáló `%1`-es sablonon `replace`-szel megy.
        return (
            QCoreApplication.translate("PrintController", "%1 — %2 × %3 mm, %4")
            .replace("%1", lapmeret.name())
            .replace("%2", f"{szeles:.0f}")
            .replace("%3", f"{magas:.0f}")
            .replace("%4", tajolas)
        )

    def _papir_elrendezes(self, printer_name: str) -> QPageLayout:
        """A `paperInfo` forrás-elrendezése — ld. az ottani sorrendet."""
        if self._oldalelrendezes is not None:
            return self._oldalelrendezes
        if printer_name:
            info = self._printer_info_api().printerInfo(printer_name)
            if not info.isNull():
                return QPageLayout(
                    info.defaultPageSize(),
                    QPageLayout.Orientation.Portrait,
                    QMarginsF(0, 0, 0, 0),
                )
        return QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(0, 0, 0, 0),
        )

    @Slot(str, result=bool)
    def openPrinterSetup(self, printer_name: str) -> bool:  # noqa: N802
        """A nyomtató SAJÁT oldalbeállítója (#2103).

        Az eredetiben ez a `printpanel/psetupbutton`: `OpenPrinter` →
        `DocumentProperties` (méret) → `DocumentProperties` (megjelenítés)
        — vagyis az illesztőprogram tulajdonságlapja, nem Picasa-párbeszéd.

        ⚠️ **A tartalom nem másolható:** a `DocumentProperties` a Windows
        illesztőprogramé. A Qt megfelelője a `QPageSetupDialog`, ami
        platformonként a rendszer saját lapját hozza. Ami átvehető, az a
        BELÉPÉSI PONT — a gomb helye és felirata —, nem a lap tartalma.

        Az elfogadott oldalelrendezést megjegyezzük, és a következő
        nyomtatás azt használja; enélkül a párbeszéd díszlet lenne.

        ⚠️ **Nincs hozzá jelzés.** Az eredmény a VISSZATÉRÉSI ÉRTÉK — egy
        `printerSetupClosed`-féle jelzést senki nem fogadna: az előnézet a
        választott nyomatméret arányából dolgozik (`renderPreviewPage`),
        nem a nyomtató lapjából, tehát nincs mit frissíteni rajta. A
        néma-jelzés őre ezt jogosan kifogásolta.

        Returns:
            Igaz, ha a felhasználó elfogadta a beállításokat.
        """
        if not printer_name:
            self.printFailed.emit(self.tr("No printer selected."))
            return False
        info = self._printer_info_api().printerInfo(printer_name)
        if info.isNull():
            self.printFailed.emit(self.tr("Unknown printer: %1").replace("%1", printer_name))
            return False
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPrinterName(printer_name)
        # A párbeszéd megnyitása a felhasználói felület dolga; fej nélküli
        # környezetben (teszt, CI) nincs mit mutatni, ezért ott csak a
        # jelzés megy ki, és a hívó nem akad el.
        parbeszed = self._page_setup_dialog(printer)
        if parbeszed is None:
            return False
        elfogadva = bool(parbeszed.exec())
        if elfogadva:
            self._oldalelrendezes = printer.pageLayout()
        return elfogadva

    def _page_setup_dialog(self, printer: QPrinter):
        """A `QPageSetupDialog` példánya — a teszt ezt cseréli le.

        Külön metódus, mert egy modális rendszerpárbeszéd megnyitása
        tesztben megállítaná a futást; a lecserélhető gyártó a bekötést
        mérhetővé teszi anélkül, hogy a termékkódba tesztkapcsoló kerülne.
        """
        from PySide6.QtPrintSupport import QPageSetupDialog

        return QPageSetupDialog(printer)

    def _alkalmazd_az_oldalelrendezest(self, printer: QPrinter) -> None:
        """A `openPrinterSetup`-ban elfogadott elrendezés érvényesítése.

        Ha a felhasználó nem járt a beállítónál, nincs mit tenni — a
        nyomtató a saját alapértelmezését hozza.
        """
        if self._oldalelrendezes is not None:
            printer.setPageLayout(self._oldalelrendezes)

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
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QObject,
    QRectF,
    QSettings,
    QStandardPaths,
    QUrl,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtCore import QMarginsF
from PySide6.QtGui import (
    QFont,
    QFontDatabase,
    QImage,
    QPageLayout,
    QPageSize,
    QPainter,
    QPen,
)
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo

from picasapy.app.busy_registry import get_app_busy_registry
from picasapy.index import PhotoRecord
from picasapy.printing.contact_sheet import (
    DEFAULT_COLUMNS,
    header_rect,
    sheet_pages,
)
from picasapy.printing.dpi import (
    KICSI_KUSZOB_DPI,
    METRIKUS_KESZLET,
    NyomatMeret,
    effektiv_dpi,
    keszlet_nyelvhez,
    minoseg_osszegzes,
)
from picasapy.printing.layout import (
    PageGeometry,
    PrintFitMode,
    PrintOrientation,
    compute_print_layout,
    resolve_orientation,
)
from picasapy.printing.options import (
    BORDER_SIZE_MAX,
    TEXT_SIZE_VALUES,
    PrintOptions,
    argb_to_qcolor,
    has_render_effects,
    load_print_options,
    save_print_options,
    update_print_option,
)

from .collage_draft_guard import CollageDraftGuard
from .formatting import to_local_path
from .language_controller import LANGUAGE_KEY

_log = logging.getLogger(__name__)

# a margón belüli terület köré hagyott margó — az egyszerű elrendezés
# rögzített értéke (a részletes sablonrendszer, benne az állítható margóval,
# NEM ebben a körben készül el, ld. a modul docstringje)
_MARGIN_MM = 5.0

#: #3016: legfeljebb ennyente engedjük vissza az eseményhurkot a festés
#: közben (ms). MÉRT szám, nem ízlés: a laponkénti `processEvents` a 12
#: lapos, 12 megapixeles feladatot 2388 → 2815 ms-ra nyújtotta (+18 %). A
#: 200 ms a szokásos UI-válaszidő-küszöb alatt marad (a felhasználó még
#: „élőnek" látja a felületet), de tizenkét lapnál már csak néhányszor
#: fizetjük meg az árat, nem tizenkétszer.
#:
#: A ritkítás UTÁN a 12 lapos esetet háromszor mértem: −100 / +7 / +144 ms
#: (medián +7) — a különbség tehát a futások közti SZÓRÁSBA esik, szemben a
#: ritkítás nélküli, KÖVETKEZETES +427 ms-mal. Ezzel teljesül a jegy
#: negyedik feltétele: „az észlelt megállás ideje nem nő".
_FRISSITES_MS = 200.0

# #1819: az előnézeti lap felbontása. Nem nyomdai érték — csak annyi, hogy
# a képernyőn éles legyen a legnagyobb nyomatméreten is (8×10 hüvelyk ×
# 96 = 768×960 képpont), és a PNG még gyorsan elkészüljön.
_ELONEZET_DPI = 96.0


class PrintController(QObject):
    """A nyomtatás-előkészítés (PDF-be renderelés, teszthető) és a tényleges
    nyomtatás (`QPrinter` élő nyomtatóra) közös rajzoló-logikája."""

    printFinished = Signal(str)  # kimeneti fájl vagy nyomtató neve
    printFailed = Signal(str)
    #: #3016: LAPONKÉNTI haladás — `(kész, összes)`. A #514 háttérszálas
    #: javaslatát a mérés megdöntötte (12 MP-es fotók, PDF): a festés a
    #: munka kétharmada, és a Qt festő-/nyomtató-API-ja a **GUI-szálhoz
    #: kötött**, tehát nem tolható át. A megoldás ezért nem a szál, hanem a
    #: VISSZAJELZÉS. A jelzés a festés KÖZBEN jön, nem a végén.
    printProgress = Signal(int, int)
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
        settings: QSettings | None = None,
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
        #: #3016: fut-e épp nyomtatási feladat. A haladás-jelzés
        #: `processEvents()`-et hív, tehát a felület KÖZBEN válaszol — ez a
        #: zár tartja távol a második, egyidejű feladatot.
        self._nyomtatas_folyamatban = False
        #: #3016: mikor engedtük vissza utoljára az eseményhurkot
        #: (monotonikus óra). A `_FRISSITES_MS` ritkítás alapja.
        self._utolso_frissites = 0.0
        #: #1782: a nyomatméret TARTÓS — az eredetiben a
        #: `Preferences\PrintLastSize` őrzi két indítás közt. Ugyanaz a
        #: minta, mint a #1780-nál: amit „a művelethez tapad"-nak
        #: hinnénk, az valójában globális beállítás.
        #:
        #: A `settings` átadható, hogy a TESZT ne a gép tartós
        #: beállítására üljön rá. Enélkül a nyomatméret-teszt attól függ,
        #: mi maradt a gépen (és Windowson a beállítás a registrybe megy,
        #: nem ini-fájlba) — a CI windows-lába emiatt bukott vissza a
        #: 4×6-os alapértelmezésre a beállított 8×10 helyett.
        self._settings = settings if settings is not None else QSettings()
        #: #2103: a nyomtató saját beállítójában elfogadott oldalelrendezés.
        #: `None`, amíg a felhasználó nem járt ott — ilyenkor a nyomtató a
        #: saját alapértelmezését hozza, ahogy eddig.
        self._oldalelrendezes: QPageLayout | None = None

    def _keszlet(self) -> tuple[NyomatMeret, ...]:
        """A felület nyelvéhez tartozó nyomatméret-készlet (#1961).

        A nyelvet a beállításokból olvassuk, nem gyorstárazzuk: a
        felhasználó menet közben is válthat, és a párbeszéd minden
        megnyitáskor újrakérdezi a listát."""
        return keszlet_nyelvhez(self._settings.value(LANGUAGE_KEY))

    def _alapmeret(self) -> NyomatMeret:
        """A készlet alapértelmezett mérete.

        A hüvelykesé a mért 4×6; a metrikusé a **10×15 cm** — ugyanaz a
        méret más mértékegységben, és a legelterjedtebb fotóméret. DÖNTÉS:
        az eredetiben a `PrintLastSize` hiányakor betöltött érték nincs
        mérve."""
        keszlet = self._keszlet()
        alap = NyomatMeret.M10X15CM if keszlet is METRIKUS_KESZLET \
            else NyomatMeret.M4X6
        return alap if alap in keszlet else keszlet[0]

    #: A QML-nek átadott méretnevek — a `NyomatMeret` tagjainak nevei.
    #: A felirat a QML dolga, ide csak az azonosító kell.
    @Slot(result=list)
    def printSizes(self) -> list[str]:  # noqa: N802 — QML-stílus
        """A felület nyelvéhez tartozó nyomatméretek azonosítói (#1961).

        Magyarul a metrikus hatos, angolul a mért hüvelykes ötös."""
        return [tag.name for tag in self._keszlet()]

    @Slot(result=str)
    def printSize(self) -> str:  # noqa: N802 — QML-stílus
        """A megjegyzett nyomatméret (`PrintLastSize`), alapból 4×6.

        #1961: a tárolt érték túléli a nyelvváltást, ezért a MÁSIK készlet
        tételét nem adhatjuk vissza — a párbeszéd olyan méretet mutatna,
        ami nincs is a listájában."""
        alap = self._alapmeret()
        tarolt = self._settings.value("print/lastSize", alap.name)
        nevek = {tag.name for tag in self._keszlet()}
        return tarolt if tarolt in nevek else alap.name

    @Slot(str)
    def setPrintSize(self, nev: str) -> None:  # noqa: N802 — QML-stílus
        """A nyomatméret megjegyzése. A készleten kívüli nevet nem
        tároljuk el — egy elgépelt (vagy másik készletbeli) érték némán
        elrontaná a következő indulást."""
        if nev in {tag.name for tag in self._keszlet()}:
            self._settings.setValue("print/lastSize", nev)

    # -- Szegély- és felirat-opciók (#1780) -------------------------------

    @Slot(result="QVariantMap")
    def printOptions(self):  # noqa: N802 — QML-stílus
        """A 11 tartós printoptions-beállítás QML-kompatibilis térképe."""
        return load_print_options(self._settings).as_mapping()

    @Slot(result=list)
    def printTextSizes(self):  # noqa: N802 — QML-stílus
        """A binárisból mért 16 betűméret, sorrendben."""
        return list(TEXT_SIZE_VALUES)

    @Slot(result=list)
    def printFontFamilies(self):  # noqa: N802 — QML-stílus
        """A gép tényleges Qt-betűkészlete, az aktuális Arial-lal együtt."""
        aktualis = load_print_options(self._settings).textFont
        nevek = set(QFontDatabase.families())
        nevek.add(aktualis)
        return sorted(nevek, key=str.casefold)

    @Slot(str, "QVariant")
    def setPrintOption(self, nev: str, ertek) -> None:  # noqa: N802
        """Egy vezérlő azonnali mentése, mint az eredeti panelben.

        Az `Alkalmaz` ezért nem külön mentési pont: csak a már elmentett
        állapotból kéri újra az előnézetet. A validálás közös rétegben él,
        így QML-ből érkező hibás vagy határon túli érték nem kerül a tárba.
        """
        regi = load_print_options(self._settings)
        uj = update_print_option(regi, nev, ertek)
        if uj != regi:
            save_print_options(self._settings, uj)

    @Slot("QVariantMap")
    def restorePrintOptions(self, ertekek) -> None:  # noqa: N802
        """A `Mégse` által visszatöltött állapot explicit mentése."""
        regi = load_print_options(self._settings)
        uj = regi
        for nev, ertek in dict(ertekek or {}).items():
            uj = update_print_option(uj, str(nev), ertek)
        save_print_options(self._settings, uj)

    @Slot(result=str)
    def printOptionsDisabledText(self):  # noqa: N802 — QML-stílus
        return self.tr(
            "These options cannot be used when printing contact sheets."
        )

    def _print_options(self) -> PrintOptions:
        """A renderelő mindig a tartós, legfrissebb állapotot olvassa."""
        return load_print_options(self._settings)

    @staticmethod
    def _caption_text(record: PhotoRecord, options: PrintOptions) -> str:
        """A négy mért feliratforrásból előálló szöveg."""
        if options.textSource == 0:
            return ""
        if options.textSource == 1:
            return str(getattr(record, "caption", None) or "")
        if options.textSource == 2:
            return str(getattr(record, "name", ""))
        taken = str(getattr(record, "taken_at", None) or "").strip()
        width = getattr(record, "width", None)
        height = getattr(record, "height", None)
        reszletek = [darab for darab in (taken,)
                    if darab]
        if width and height:
            reszletek.append(f"{width} × {height}")
        return " · ".join(reszletek) or str(getattr(record, "name", ""))

    @staticmethod
    def _font_for_print(options: PrintOptions, dpi: float) -> QFont:
        font = QFont(options.textFont or "Arial")
        font.setPixelSize(max(1, round(options.textSize * dpi / 72.0)))
        return font

    @staticmethod
    def _border_width(options: PrintOptions, page: PageGeometry) -> float:
        """A tárolt 0..1024 skálát a nyomtatható területre vetíti.

        A bináris a tárolási skálát méri; a renderer képpontos végső
        ecsetméretét nem adja át dokumentált konstansként. Ez az explicit,
        determinisztikus terméki leképezés a PDF és az előnézet között közös:
        nulla nincs, a maximum pedig a rövidebb nyomtatható oldal.
        """
        if options.borderSize <= 0:
            return 0.0
        return min(
            min(page.printable_width, page.printable_height),
            max(1.0, min(page.printable_width, page.printable_height)
                * options.borderSize / BORDER_SIZE_MAX),
        )

    @Slot(list, str, result="QVariantMap")
    def printQuality(self, rows, size_name: str):  # noqa: N802 — QML-stílus
        """A kijelölés minőség-összegzése a választott nyomatmérethez.

        #1782: eddig egy 640×480-as képet 8×10-re lehetett nyomtatni úgy,
        hogy a program egy szót sem szólt. A `smallest`/`small`/`ready`
        mezőkből a QML állítja össze az eredeti mondatait
        (`ThumbUIPrint::Smallest`, `::ReviewPrompt`).

        Az ISMERETLEN méretű kép kicsinek számít — ha nem tudjuk, mekkora,
        ne nyugtassuk meg a felhasználót."""
        meret = NyomatMeret.__members__.get(size_name, NyomatMeret.M4X6)
        meretek = [
            (rekord.width or 0, rekord.height or 0)
            for rekord in self._resolve_records(rows)
        ]
        osszegzes = minoseg_osszegzes(meretek, meret, kuszob=self._dpi_kuszob())
        return {
            "smallest": osszegzes.legkisebb_dpi,
            "small": osszegzes.kicsik,
            "total": osszegzes.osszes,
            "ready": osszegzes.keszen_all,
            "threshold": self._dpi_kuszob(),
        }

    @Slot(list, str, result=list)
    def smallPictures(self, rows, size_name: str):  # noqa: N802 — QML-stílus
        """A küszöb alatti képek NÉV szerint, a hozzájuk tartozó DPI-vel.

        #1953: eddig a párbeszéd kimondta, hogy *van* kis felbontású kép,
        de nem mondta meg, **melyik**. Az eredetiben erre való az
        „Ellenőrzés" gomb (`printpanel/reviewnowbutton`).

        A számítás UGYANAZ, mint az összegzésé (`effektiv_dpi` +
        `KICSI_KUSZOB_DPI`) — ha a két út külön számolna, előbb-utóbb
        ellentmondanának: a mondat N kis képet írna, a lista M-et mutatna.

        A lista a **legrosszabbal kezdődik**: a felhasználót az érdekli
        először. Az ismeretlen méretű kép ugyanúgy kicsinek számít, mint
        az összegzésben — 0 DPI-vel."""
        meret = NyomatMeret.__members__.get(size_name, NyomatMeret.M4X6)
        tetelek = [
            {
                "name": rekord.name,
                "dpi": effektiv_dpi(
                    rekord.width or 0, rekord.height or 0, meret
                ),
            }
            for rekord in self._resolve_records(rows)
        ]
        kuszob = self._dpi_kuszob()
        kicsik = [t for t in tetelek if t["dpi"] < kuszob]
        return sorted(kicsik, key=lambda t: t["dpi"])

    #: A küszöb beállítás-kulcsa. Az eredetiben `Preferences\DPIWarning`
    #: (`0x0085c076`/`0x0085c07b`), alapértéke **150** (`0x0085c08b`).
    _DPI_KUSZOB_KULCS = "printing/dpiWarning"

    def _dpi_kuszob(self) -> int:
        """A „kis kép" küszöbe — beállításból, `KICSI_KUSZOB_DPI` alapértékkel.

        ⚠️ MINDKÉT út (az összegzés és a kifogásolt lista) ezt hívja. Ha
        külön olvasnák, a mondat N kis képet írna, a lista M-et — a #1953
        épp ezt az ellentmondást szüntette meg.

        Elrontott (nem szám vagy nem pozitív) beállításnál az alapértékre
        esünk vissza: a nyomtatás-előkészítés nem dőlhet be egy rossz
        kulcstól.
        """
        try:
            ertek = int(self._settings.value(self._DPI_KUSZOB_KULCS,
                                             KICSI_KUSZOB_DPI))
        except (TypeError, ValueError):
            return KICSI_KUSZOB_DPI
        return ertek if ertek > 0 else KICSI_KUSZOB_DPI

    @Slot(result=list)
    def listPrinters(self) -> list[str]:
        """Az elérhető nyomtatók neve — a natív `QPrintDialog` helyett
        (ld. a modul docstringje) a QML saját választólistájához."""
        return list(QPrinterInfo.availablePrinterNames())

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
            self.tr("%1 — %2 × %3 mm, %4")
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
            info = QPrinterInfo.printerInfo(printer_name)
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
        info = QPrinterInfo.printerInfo(printer_name)
        if info.isNull():
            self.printFailed.emit(
                self.tr("Unknown printer: %1").replace("%1", printer_name)
            )
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
            info = QPrinterInfo.printerInfo(printer_name)
            if info.isNull():
                self.printFailed.emit(
                    self.tr("Unknown printer: %1").replace("%1", printer_name)
                )
                return False
            printer.setPrinterName(printer_name)
        # #2103: ha a felhasználó járt a nyomtató saját beállítójánál, az
        # ottani elrendezés érvényes — enélkül a párbeszéd díszlet lenne.
        self._alkalmazd_az_oldalelrendezest(printer)
        ok = self._run(printer, rows, fit_mode, orientation, copies)
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
            requested = (
                PrintOrientation(orientation) if orientation else PrintOrientation.AUTO
            )
        except ValueError as error:
            self.printFailed.emit(str(error))
            return False

        images: list[QImage] = []
        job_records: list[PhotoRecord] = []
        skipped: list[str] = []
        for record, path in zip(records, paths, strict=True):
            image = QImage(str(path))
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
                    self.tr("None of the selected pictures could be printed: %1")
                    .replace("%1", ", ".join(skipped))
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
        # másolatot, tehát két kép × két példány NÉGY lap.
        #
        # ⚠️ A lapok SORRENDJE nincs kimérve. Képenként csoportosítunk
        # (A, A, B, B), mert a felirat is képenként fogalmaz („each Photo");
        # a másik olvasat (A, B, A, B) a nyomtató példányszám-mezőjének
        # viselkedése lenne, amitől ez a vezérlő épp különbözik.
        images = self._sokszorozva(images, copies)
        darab = max(1, int(copies or 1))
        job_records = [record for record in job_records for _ in range(darab)]

        # A szegély/felirat a PDF- és nyomtató-úton is ugyanabból az
        # állapotból készül. Alapállapotban megtartjuk a régi rajzolási ágat,
        # így a meglévő sebesség- és példányszám-kapuk változatlanok.
        options = self._print_options()
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
                    printer, images, job_records, mode, options, self._lap_kesz
                )
            else:
                self._paint_pages(printer, images, mode, self._lap_kesz)
        except RuntimeError:
            _log.exception("nyomtatás: a feladat nem indítható")
            self.printFailed.emit(self.tr("The print job could not be started."))
            return False
        finally:
            self._nyomtatas_folyamatban = False
            nyilvantartas.end()
        return True

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
        app = QCoreApplication.instance()
        if app is None:
            return
        most = time.monotonic()
        utolso = kesz >= ossz
        if not utolso and (most - self._utolso_frissites) * 1000 < _FRISSITES_MS:
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
        gyoker = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.CacheLocation
        )
        if not gyoker:
            gyoker = str(Path.home())
        mappa = Path(gyoker) / "print-preview"
        mappa.mkdir(parents=True, exist_ok=True)
        return QUrl.fromLocalFile(str(mappa / "page.png")).toString()

    @Slot(list, str, str, int, int, str, result=bool)
    def renderPreviewPage(  # noqa: N802 — QML-stílus
        self,
        rows,
        fit_mode: str,
        orientation: str,
        copies: int,
        page_index: int,
        output_path: str,
    ) -> bool:
        """EGY lap előnézete PNG-be (#1819) — a lapozó előnézet forrása.

        Miért nem a `renderPrintPreviewPdf` egy oldala: azt a `QPrinter`
        rajzolja, és a lapméretet a NYOMTATÓ adja. Az előnézetnek a
        VÁLASZTOTT nyomatméret arányát kell mutatnia (`NyomatMeret`), akkor
        is, ha a gépen nincs is nyomtató — a párbeszéd PDF-be is dolgozhat.
        A tördelés maga UGYANAZ (`compute_print_layout`, `_MARGIN_MM`),
        tehát az előnézet nem külön elrendezés, csak más vászon.
        """
        target = to_local_path(output_path)
        if not target:
            return False
        paths = self._resolve_paths(rows)
        records = self._resolve_records(rows)
        kep_parok = []
        for record, path in zip(records, paths, strict=True):
            kep = QImage(str(path))
            if not kep.isNull():
                kep_parok.append((kep, record))
        darab = max(1, int(copies or 1))
        kep_parok = [par for par in kep_parok for _ in range(darab)]
        if not 0 <= int(page_index) < len(kep_parok):
            return False
        kepek = [par[0] for par in kep_parok]
        rekordok = [par[1] for par in kep_parok]
        kep = kepek[int(page_index)]

        meret = NyomatMeret[self.printSize()]
        try:
            mode = PrintFitMode(fit_mode) if fit_mode else PrintFitMode.FIT
            kert = (
                PrintOrientation(orientation)
                if orientation
                else PrintOrientation.AUTO
            )
        except ValueError:
            return False
        # A tájolás a TELJES feladaté (ld. a modul docstringje): az első
        # kép dönti el, nem a most mutatott lap — különben a lapozás közben
        # elfordulna az előnézet.
        elso = kepek[0]
        fekvo = (
            resolve_orientation(elso.width(), elso.height(), kert)
            == PrintOrientation.LANDSCAPE
        )
        huvelyk_sz, huvelyk_ma = meret.szeles_huvelyk, meret.magas_huvelyk
        if fekvo:
            huvelyk_sz, huvelyk_ma = huvelyk_ma, huvelyk_sz

        vaszon_sz = _ELONEZET_DPI * huvelyk_sz
        vaszon_ma = _ELONEZET_DPI * huvelyk_ma
        lap = QImage(
            int(round(vaszon_sz)),
            int(round(vaszon_ma)),
            QImage.Format.Format_RGB32,
        )
        lap.fill(Qt.GlobalColor.white)
        options = self._print_options()
        painter = QPainter()
        if not painter.begin(lap):
            return False
        try:
            self._draw_options_page(
                painter,
                QRectF(0, 0, lap.width(), lap.height()),
                kep,
                rekordok[int(page_index)],
                mode,
                options,
                _ELONEZET_DPI,
            )
        finally:
            painter.end()
        return bool(lap.save(target, "PNG"))

    @Slot(list, int, result=int)
    def printPageCount(self, rows, copies: int = 1) -> int:  # noqa: N802
        """Hány lap lenne a nyomtatásból (#1819) — a lapozó előnézet
        `%d / %d` kijelzéséhez.

        Csak a DEKÓDOLHATÓ képeket számolja: a kihagyott (videó, sérült)
        fájlok lapot sem kapnak, tehát a lapszám sem tartalmazhatja őket."""
        darab = 0
        for path in self._resolve_paths(rows):
            if not QImage(str(path)).isNull():
                darab += 1
        return darab * max(1, int(copies or 1))

    @staticmethod
    def _draw_options_page(
        painter: QPainter,
        page_rect: QRectF,
        image: QImage,
        record: PhotoRecord,
        mode: PrintFitMode,
        options: PrintOptions,
        dpi: float,
    ) -> None:
        """Egy oldal képe, szegélye és felirata közös geometriával."""
        margin = min(
            _MARGIN_MM / 25.4 * dpi,
            page_rect.width() / 2 - 1,
            page_rect.height() / 2 - 1,
        )
        margin = max(0.0, margin)
        page = PageGeometry(
            width=page_rect.width(), height=page_rect.height(), margin=margin
        )
        text = PrintController._caption_text(record, options)
        font = PrintController._font_for_print(options, dpi)
        caption_height = 0.0
        if text and options.textPlacement == 0:
            caption_height = min(
                page.printable_height * 0.25,
                max(float(font.pixelSize() + 8), float(font.pixelSize() * 3)),
            )
        content_height = max(margin * 2 + 1, page.height - caption_height)
        content_page = PageGeometry(
            width=page.width,
            height=min(page.height, content_height),
            margin=min(margin, max(0.0, min(page.width, content_height) / 2 - 1)),
        )
        placement = compute_print_layout(
            content_page, image.width(), image.height(), mode
        )
        target = QRectF(
            page_rect.x() + placement.x,
            page_rect.y() + placement.y,
            placement.width,
            placement.height,
        )
        painter.drawImage(target, image)

        border_width = PrintController._border_width(options, page)
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
                page_rect.x() + margin,
                page_rect.y() + content_page.height,
                page.printable_width,
                max(font.pixelSize() + 4, page.height - content_page.height - margin),
            )
        painter.drawText(caption_rect, flags, text)

    @staticmethod
    def _paint_pages_with_options(
        printer: QPrinter,
        images: Sequence[QImage],
        records: Sequence[PhotoRecord],
        mode: PrintFitMode,
        options: PrintOptions,
        lap_kesz: Callable[[int, int], None] | None = None,
    ) -> None:
        """A printoptions-ág lapfestése PDF-re és élő QPrinterre."""
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("A nyomtatási feladat nem indítható")
        ossz = len(images)
        try:
            for index, (image, record) in enumerate(zip(images, records, strict=True)):
                if index > 0:
                    printer.newPage()
                rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                PrintController._draw_options_page(
                    painter,
                    QRectF(rect),
                    image,
                    record,
                    mode,
                    options,
                    float(printer.resolution()),
                )
                if lap_kesz is not None:
                    lap_kesz(index + 1, ossz)
        finally:
            painter.end()

    @staticmethod
    def _paint_pages(
        printer: QPrinter,
        images: Sequence[QImage],
        mode: PrintFitMode,
        lap_kesz: Callable[[int, int], None] | None = None,
    ) -> None:
        """A lapok megfestése; `lap_kesz(kész, összes)` LAPONKÉNT (#3016).

        A visszahívás alapértelmezésben `None` — a rajzolás így önmagában
        is használható marad (teszt, előnézet), jelzés nélkül."""
        painter = QPainter()
        if not painter.begin(printer):
            raise RuntimeError("A nyomtatási feladat nem indítható")
        ossz = len(images)
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
                if lap_kesz is not None:
                    lap_kesz(index + 1, ossz)
        finally:
            painter.end()

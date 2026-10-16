"""PrintController: kijelölt képek nyomtatása (#32, RÉSZLEGES kör) —
a nyomatméret CELLAKÉNT rácsba rendezve a papíron, laptöréssel (#3647,
`picasapy.printing.grid_layout`), és #1590 óta az INDEXKÉP is (több
bélyegkép egy lapon, `printContactSheet`). A Picasa teljes nyomtatási
sablonrendszere (`print.fen`/`reviewprint.fen`, a `ytPrintSizes` mind a 17
mérete) NEM ebben a körben készül el — a `ytPrintSizes::eContact`
(„Indexképek") viszont igen.

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

A nyomtatási feladat EGYETLEN lapállást használ — a Qt `QPrinter` tájolása
csak az első oldal `QPainter.begin()`-je ELŐTT állítható be megbízhatóan,
laponkénti váltás így nem lenne robosztus. `orientation="auto"` esetén A
LAPÁLLÁS A PAPÍRÉ MARAD (mindig portré) — a KEVESEBB lapot a CELLA
tájolása (`(w,h)`/`(h,w)`) közül választjuk, nem a papír elforgatásával
(#3647, #3685 önhelyesbítés, `_grid_for_job`); explicit kérésnél a kért
lapállás rögzül. Ha a cella egyik cellatájolással sem fér el a papíron, a
0. indexű (`eFullPage`) egyképes ágra esünk vissza (`full_page_pages`)."""

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

from picasapy.export import render_photo_pixels
from picasapy.export.exporter import _decode_image
from picasapy.app.busy_registry import get_app_busy_registry
from picasapy.ini import PhotoCropReader
from picasapy.ini.filters import parse_filters_prefix
from picasapy.index import PhotoRecord
from picasapy.lazy_cv2 import cv2
from picasapy.printing.contact_sheet import (
    DEFAULT_COLUMNS,
    header_rect,
    sheet_pages,
)
from picasapy.printing.dpi import (
    KICSI_KUSZOB_DPI,
    JO_MINOSEGI_KUSZOB_DPI,
    NyomatMeret,
    alapmeretek_teruleti_mereshez,
    effektiv_dpi,
    keszlet_teruleti_mereshez,
    minoseg_osszegzes,
    nyomtatasi_minoseg_kod,
)
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
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS
from picasapy.printing.resample import lanczos_resize
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
from picasapy.render import normalize_crop_ops
from picasapy.scanner import PICASA_INI_NAME

from .collage_draft_guard import CollageDraftGuard
from .formatting import to_local_path

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
_PRINT_SIZE_PRESET_KEYS = tuple(
    f"printing/sizePreset{index}" for index in range(1, 6)
)
_PRINT_OPTION_SIZES = (
    "M3X4",
    "M3_5X5",
    "M4X5",
    "M4X6",
    "M5X7",
    "M8X10",
    "M5X8CM",
    "M9X13CM",
    "M10X15CM",
    "M13X18CM",
    "M15X20CM",
    "M20X25CM",
    "TARCA",
    "CDSIZE",
    "PASSPORT",
    "CONTACT",
    "TELJES_OLDAL",
)


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
        self._crop_reader = PhotoCropReader()
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
        #: #1401: az Útlevélkép kivágott képe és a hozzá tartozó méret-
        #: felülírás (`setPassportSource`); `None`, ha nincs érvényben.
        self._utlevel: PhotoRecord | None = None
        self._meret_felulirva: NyomatMeret | None = None
        #: #4275: a tálcás és útlevél-forrású képeknek nincs rácssoruk;
        #: az Ellenőrzés panelből itt jelöljük ki, mely rekordok maradjanak
        #: ki a nyomtatási munkából. Új párbeszédnyitáskor ürül.
        self._review_excluded_ids: set[int] = set()

    @Slot(result=list)
    def printSizePresets(self) -> list[str]:  # noqa: N802 — QML-stílus
        """A Nyomtatás fül öt, a panel gyorsgombjaihoz tartozó mérete.

        A rendszer területi mértékegysége adja az eredeti Picasa ötösének
        kezdőértékeit (#4435). A mentett PrintSize0–4 azonosítók felülírják
        ezeket; a bővebb PicasaPy-katalógus további méretei nem változnak.
        """
        sizes = set(_PRINT_OPTION_SIZES)
        result = []
        defaults = tuple(
            meret.name for meret in alapmeretek_teruleti_mereshez()
        )
        for key, default in zip(_PRINT_SIZE_PRESET_KEYS, defaults, strict=True):
            value = str(self._settings.value(key, default))
            result.append(value if value in sizes else default)
        return result

    @Slot(int, str)
    def setPrintSizePreset(self, index: int, name: str) -> None:  # noqa: N802
        """A kiválasztott gyorsgomb méretét azonnal elmenti."""
        sizes = set(_PRINT_OPTION_SIZES)
        if 0 <= int(index) < len(_PRINT_SIZE_PRESET_KEYS) and name in sizes:
            self._settings.setValue(_PRINT_SIZE_PRESET_KEYS[int(index)], name)

    @Slot(result=list)
    def printOptionSizes(self) -> list[str]:  # noqa: N802
        """Az `options.fen` 17 elemű `ytPrintSizes` listája (#4318)."""
        return list(_PRINT_OPTION_SIZES)

    @Slot(str, result=bool)
    def canUsePrintSizePreset(self, name: str) -> bool:  # noqa: N802
        """A méretgomb csak ismert méretet vagy Indexképek módot választhat.

        A CD-borító mérete a projekt specében nem kapott fizikai méretet,
        ezért a konfigurálható listában szerepel, de a gomb nem nyomtatható.
        """
        return name in NyomatMeret.__members__ or name == "CONTACT"

    @Slot(str, result=bool)
    def setPresetPrintSize(self, name: str) -> bool:  # noqa: N802
        """A Beállításokban kiosztott gyorsgomb méretét használja a nyomathoz."""
        if name not in NyomatMeret.__members__:
            return False
        self._meret_felulirva = NyomatMeret[name]
        return True

    @Slot(result=bool)
    def printProxyPreview(self) -> bool:  # noqa: N802
        """Igaz, ha az előnézet a gyorsabb, proxy felbontást használja."""
        value = self._settings.value("printing/proxyPreview", True)
        if isinstance(value, str):
            return value.strip().casefold() not in {"0", "false", "no", "off"}
        return bool(value)

    @Slot(bool)
    def setPrintProxyPreview(self, enabled: bool) -> None:  # noqa: N802
        self._settings.setValue("printing/proxyPreview", bool(enabled))

    @Slot(result=str)
    def printerQuality(self) -> str:  # noqa: N802
        """A Windows-only FEN fél- vagy teljes felbontású nyomtatási módja."""
        value = str(self._settings.value("printing/printerQuality", "compatible"))
        return value if value in {"compatible", "highQuality"} else "compatible"

    @Slot(str)
    def setPrinterQuality(self, value: str) -> None:  # noqa: N802
        if value in {"compatible", "highQuality"}:
            self._settings.setValue("printing/printerQuality", value)

    def _printer_output_scale(self) -> float:
        """Az options.fen minősége: kompatibilis fél, magas teljes felbontás."""
        return 0.5 if self.printerQuality() == "compatible" else 1.0

    @Slot(result=int)
    def printResamplerQuality(self) -> int:  # noqa: N802
        """A nyomtatási átméretező Lanczos-sugara (3 vagy 8)."""
        try:
            value = int(self._settings.value("printing/resamplerQuality", 3))
        except (TypeError, ValueError):
            return 3
        return value if value in {3, 8} else 3

    @Slot(int)
    def setPrintResamplerQuality(self, value: int) -> None:  # noqa: N802
        if int(value) in {3, 8}:
            self._settings.setValue("printing/resamplerQuality", int(value))

    def _keszlet(self) -> tuple[NyomatMeret, ...]:
        """A rendszer területi mértékegységéhez tartozó készlet (#4435)."""
        return keszlet_teruleti_mereshez()

    def _alapmeret(self) -> NyomatMeret:
        """A készlet alapértelmezett mérete: **Teljes oldal** (#3733).

        A `docs/specs/picasa-nyomtatas.md` élő mérése (Colab EN 29/30,
        picasa-colab-jobs #55) szerint az eredeti nyomtatási nézet
        alapállása FullPage — mindkét készletben ez az utolsó tétel
        (`TELJES_OLDAL`), ugyanaz a méret mindkét területi készletben. Korábban itt
        a mért 4×6/10×15 cm állt, ami az eredetiben csak GOMB, nem
        alapállás."""
        return NyomatMeret.TELJES_OLDAL

    #: A QML-nek átadott méretnevek — a `NyomatMeret` tagjainak nevei.
    #: A felirat a QML dolga, ide csak az azonosító kell.
    @Slot(result=list)
    def printSizes(self) -> list[str]:  # noqa: N802 — QML-stílus
        """A területi mértékegységhez tartozó nyomatméretek azonosítói (#4435).

        A `#3712-review` a korábbi Full Page nélküli ötöst javította;
        a #4257 az eredeti sorrendben egészíti ki a hiányzó méretekkel."""
        return [tag.name for tag in self._keszlet()]

    @Slot(result=str)
    def printSize(self) -> str:  # noqa: N802 — QML-stílus
        """A megjegyzett nyomatméret (`PrintLastSize`), alapból Teljes oldal.

        #4435: a tárolt érték túléli a területi mérés váltását, ezért a MÁSIK készlet
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
            self._meret_felulirva = None

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
        meret = NyomatMeret.__members__.get(size_name) or self._alapmeret()
        meretek = [
            (rekord.width or 0, rekord.height or 0)
            for rekord in self._resolve_records(rows)
        ]
        best_kuszob = self._dpi_kuszob()
        good_kuszob = self._dpi_jo_kuszob()
        osszegzes = minoseg_osszegzes(meretek, meret, kuszob=best_kuszob)
        return {
            "smallest": osszegzes.legkisebb_dpi,
            "small": osszegzes.kicsik,
            "total": osszegzes.osszes,
            "ready": osszegzes.keszen_all,
            # `threshold` marad a #4275 figyelmeztető panel szerződése.
            "threshold": best_kuszob,
            "bestThreshold": best_kuszob,
            "goodThreshold": good_kuszob,
        }

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
        kuszob = self._dpi_kuszob()
        return [
            item for item in self._quality_picture_rows(rows, size_name)
            if item["dpi"] < kuszob
        ]

    @Slot(list, str, result=list)
    def reviewPictures(self, rows, size_name: str):  # noqa: N802
        """Minden nyomtatandó kép DPI-je és az eredeti 0/1/2 minőségi kódja.

        A figyelmeztető panel a teljes listát mutatja, hogy a Best és Good
        képek se tűnjenek el az ellenőrzésből. A sorok a legrosszabb DPI-től
        indulnak, a kód pedig a bináris két küszöbtesztjének összege.
        """
        return self._quality_picture_rows(rows, size_name)

    def _quality_picture_rows(self, rows, size_name: str) -> list[dict]:
        """A közös soradat a teljes Review listához és a kis-kép szűréshez."""
        meret = NyomatMeret.__members__.get(size_name) or self._alapmeret()
        best_kuszob = self._dpi_kuszob()
        good_kuszob = self._dpi_jo_kuszob()
        van_talca = (
            self._utlevel is None
            and self._tray_source is not None
            and bool(self._tray_source())
        )
        tetelek = []
        for index, rekord in enumerate(self._resolve_records(rows)):
            dpi = effektiv_dpi(rekord.width or 0, rekord.height or 0, meret)
            tetelek.append({
                "row": (
                    int(rows[index])
                    if not van_talca and self._utlevel is None
                    and index < len(rows)
                    else -1
                ),
                "recordId": int(getattr(rekord, "id", -1)),
                "name": rekord.name,
                "dpi": dpi,
                "qualityCode": nyomtatasi_minoseg_kod(
                    dpi,
                    best_kuszob=best_kuszob,
                    good_kuszob=good_kuszob,
                ),
            })
        return sorted(tetelek, key=lambda item: item["dpi"])

    @Slot(list)
    def excludeReviewPictures(self, record_ids) -> None:  # noqa: N802 — QML-stílus
        """#4275: rácssor nélküli (tálca/útlevél) képek kizárása."""
        self._review_excluded_ids.update(int(record_id) for record_id in record_ids)

    @Slot()
    def clearReviewExclusions(self) -> None:  # noqa: N802 — QML-stílus
        """Új nyomtatási párbeszéd előtt az előző felülvizsgálat ürítése."""
        self._review_excluded_ids.clear()

    #: A küszöb beállítás-kulcsa. Az eredetiben `Preferences\DPIWarning`
    #: (`0x0085c076`/`0x0085c07b`), alapértéke **150** (`0x0085c08b`).
    _DPI_KUSZOB_KULCS = "printing/dpiWarning"
    #: A Best/Good határ kulcsa az eredetiben `Preferences\DPISevere`,
    #: alapértéke **100** (`0x0085c28a`).
    _DPI_JO_KUSZOB_KULCS = "printing/dpiSevere"

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

    def _dpi_jo_kuszob(self) -> int:
        """A Good/Bad küszöb beállításból, 100 DPI alapértékkel."""
        try:
            ertek = int(self._settings.value(
                self._DPI_JO_KUSZOB_KULCS, JO_MINOSEGI_KUSZOB_DPI
            ))
        except (TypeError, ValueError):
            return JO_MINOSEGI_KUSZOB_DPI
        return ertek if ertek > 0 else JO_MINOSEGI_KUSZOB_DPI

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
        feloldás.

        #1401: az Útlevélkép kivágott képe (`setPassportSource`) mindkettőt
        megelőzi — a nyomtatási nézet ilyenkor EZT az egy képet nyomtatja."""
        if self._utlevel is not None:
            rekordok = [self._utlevel]
        else:
            talca = list(self._tray_source()) if self._tray_source is not None else []
            if talca:
                rekordok = talca
            else:
                photos = tuple(self._photo_source())
                rekordok = [
                    photos[int(row)]
                    for row in rows
                    if 0 <= int(row) < len(photos)
                ]
        if self._review_excluded_ids:
            rekordok = [
                rekord for rekord in rekordok
                if int(getattr(rekord, "id", -1)) not in self._review_excluded_ids
            ]
        return rekordok

    def _resolve_paths(self, rows: Sequence[int]) -> list[Path]:
        return [
            Path(record.folder_path) / record.name
            for record in self._resolve_records(rows)
        ]

    def _render_photo(self, record: PhotoRecord) -> QImage:
        """A rácson látott szerkesztett fotó képpontjai QImage-ként (#4602)."""
        path = Path(record.folder_path) / record.name
        if getattr(record, "kind", "") == "video" or path.suffix.lower() in VIDEO_EXTENSIONS:
            return QImage()
        filters = getattr(record, "filters", None)
        ops = parse_filters_prefix(filters) if filters else ()
        crop, crop_ini_readable = (
            self._crop_reader.read(path.parent / PICASA_INI_NAME, path.name)
            if ops
            else (None, True)
        )
        ops = normalize_crop_ops(
            ops,
            crop,
            crop_ini_readable=crop_ini_readable,
            warning_key=str(path),
        )
        try:
            image = render_photo_pixels(
                path,
                ops,
                rotate_steps=int(getattr(record, "rotate_steps", 0) or 0),
                flip_flags=int(getattr(record, "flip_flags", 0) or 0),
            )
        except (OSError, ValueError) as error:
            _log.warning(
                "nyomtatás: nem dekódolható kép — kihagyva: %s (%s)", path, error
            )
            return QImage()

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = rgb.shape[:2]
        return QImage(
            rgb.data,
            width,
            height,
            int(rgb.strides[0]),
            QImage.Format.Format_RGB888,
        ).copy()

    @staticmethod
    def _is_printable(record: PhotoRecord) -> bool:
        """A teljes dekóderrel ellenőrzi, hogy nyomtatható-e a forrás."""
        path = Path(record.folder_path) / record.name
        if getattr(record, "kind", "") == "video" or path.suffix.lower() in VIDEO_EXTENSIONS:
            return False
        try:
            _decode_image(path)
        except (OSError, ValueError) as error:
            _log.warning(
                "nyomtatás: nem dekódolható kép — kihagyva: %s (%s)", path, error
            )
            return False
        return True

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
            self._paint_contact_sheet(
                printer,
                images,
                oszlopok,
                fejlec,
                alcim,
                self.printResamplerQuality(),
                self._printer_output_scale(),
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
                    target = QRectF(
                        rect.x() + cell.x + hely.x,
                        rect.y() + cell.y + hely.y,
                        hely.width,
                        hely.height,
                    )
                    painter.drawImage(
                        target,
                        PrintController._resampled_for_target(
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
            requested = (
                PrintOrientation(orientation) if orientation else PrintOrientation.AUTO
            )
        except ValueError as error:
            # #3685 (7. lelet): a nyers kivétel-szöveg NEM fordítható — a
            # felhasználó a saját nyelvén lássa a hibát, a részletet (%1)
            # betoldva.
            self.printFailed.emit(
                self.tr("Invalid print settings: %1").replace("%1", str(error))
            )
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
        portrait_page = self._device_page_geometry(
            printer, QPageLayout.Orientation.Portrait
        )
        landscape_page = self._device_page_geometry(
            printer, QPageLayout.Orientation.Landscape
        )
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
            self.printFailed.emit(
                self.tr("Invalid print settings: %1").replace("%1", str(error))
            )
            return False
        # `_page` nem kell külön: a `grid` celláinak abszolút koordinátái
        # már tartalmazzák a margót (`grid_layout.grid_pages`).
        printer.setPageOrientation(
            QPageLayout.Orientation.Landscape
            if fekvo
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
                    printer,
                    grid,
                    images,
                    job_records,
                    mode,
                    options,
                    self._lap_kesz,
                    self.printResamplerQuality(),
                    self._printer_output_scale(),
                )
            else:
                self._paint_pages(
                    printer,
                    grid,
                    images,
                    mode,
                    self._lap_kesz,
                    self.printResamplerQuality(),
                    self._printer_output_scale(),
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
        return PageGeometry(
            width=rect.width(), height=rect.height(), margin=max(margin, 0.0)
        )

    def _preview_page_geometry(
        self, printer_name: str, *, landscape: bool
    ) -> PageGeometry:
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
            kert = (
                PrintOrientation(orientation)
                if orientation
                else PrintOrientation.AUTO
            )
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
                    self.printResamplerQuality(),
                    self._printer_output_scale(),
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
            kert = (
                PrintOrientation(orientation) if orientation else PrintOrientation.AUTO
            )
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
        page = PageGeometry(
            width=page_rect.width(), height=page_rect.height(), margin=0.0
        )
        text = PrintController._caption_text(record, options)
        font = PrintController._font_for_print(options, dpi)
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
        placement = compute_print_layout(
            content_page, image.width(), image.height(), mode
        )
        target = QRectF(
            page_rect.x() + placement.x,
            page_rect.y() + placement.y,
            placement.width,
            placement.height,
        )
        source = (
            PrintController._proxy_for_target(image, target)
            if use_proxy
            else PrintController._resampled_for_target(
                image, target, resampler_radius, printer_output_scale
            )
        )
        painter.drawImage(target, source)

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
                    PrintController._draw_options_page(
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
                    painter.setClipRect(
                        QRectF(cell.x, cell.y, cell.width, cell.height)
                    )
                    painter.drawImage(
                        target_rect,
                        PrintController._resampled_for_target(
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

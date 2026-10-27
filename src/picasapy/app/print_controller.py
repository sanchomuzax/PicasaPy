"""PrintController: kijelölt képek nyomtatása (#32, részleges kör) —
a nyomatméret CELLAKÉNT rácsba rendezve a papíron, laptöréssel (#3647,
`picasapy.printing.grid_layout`), és #1590 óta az INDEXKÉP is (több
bélyegkép egy lapon, `printContactSheet`). A Picasa teljes nyomtatási
sablonrendszere (`print.fen`/`reviewprint.fen`) nem ebben a körben készül
el. A #5683 óta a `ytPrintSizes` mind a 17 azonosítóját megkapja a QML
méretválasztó; az `eContact` külön indexképelrendezést indít, az ismeretlen
fizikai méretű `eCDSize` pedig letiltva marad.

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

from collections.abc import Callable, Sequence

from PySide6.QtCore import QCoreApplication, QObject, QSettings
from PySide6.QtGui import QPageLayout
from PySide6.QtPrintSupport import QPrinterInfo

from picasapy.export import render_photo_pixels
from picasapy.export.exporter import _decode_image
from picasapy.index import PhotoRecord
from picasapy.ini import PhotoCropReader
from picasapy.printing.dpi import NyomatMeret
from picasapy.printing.layout import PageGeometry as PageGeometry

from .collage_draft_guard import CollageDraftGuard
from .print_controller_output_mixin import PrintControllerOutputMixin
from .print_controller_preview_mixin import PrintControllerPreviewMixin
from .print_controller_printer_mixin import PrintControllerPrinterMixin
from .print_controller_quality_mixin import PrintControllerQualityMixin
from .print_controller_settings_mixin import PrintControllerSettingsMixin
from .print_controller_shared import (
    _ELONEZET_DPI as _ELONEZET_DPI,
    _FRISSITES_MS as _FRISSITES_MS,
    _MARGIN_MM as _MARGIN_MM,
    _PICASA_PRINT_SIZE_IDS as _PICASA_PRINT_SIZE_IDS,
    _PRINT_OPTION_SIZES as _PRINT_OPTION_SIZES,
    _PRINT_SIZE_PRESET_KEYS as _PRINT_SIZE_PRESET_KEYS,
    _log as _log,
)
from .print_controller_signals import PrintControllerSignalsMixin
from .print_controller_source_mixin import PrintControllerSourceMixin


class PrintController(
    PrintControllerSettingsMixin,
    PrintControllerQualityMixin,
    PrintControllerPrinterMixin,
    PrintControllerSourceMixin,
    PrintControllerOutputMixin,
    PrintControllerPreviewMixin,
    PrintControllerSignalsMixin,
    QObject,
):
    """A nyomtatás-előkészítés (PDF-be renderelés, teszthető) és a tényleges
    nyomtatás (`QPrinter` élő nyomtatóra) közös rajzoló-logikája."""

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

    def _printer_info_api(self):
        """A modulban maradó teszt-felülírásokhoz dinamikusan olvasott API."""
        return QPrinterInfo

    def _core_application_api(self):
        """A modulban maradó teszt-felülírásokhoz dinamikusan olvasott Qt API."""
        return QCoreApplication

    def _print_update_interval_ms(self):
        """A modulban maradó teszt-felülírásokhoz dinamikusan olvasott érték."""
        return _FRISSITES_MS

    def _decode_print_image(self, path):
        """A modulban maradó teszt-felülírásokhoz dinamikusan olvasott dekóder."""
        return _decode_image(path)

    def _render_print_pixels(self, *args, **kwargs):
        """A modulban maradó teszt-felülírásokhoz dinamikusan olvasott renderelő."""
        return render_photo_pixels(*args, **kwargs)

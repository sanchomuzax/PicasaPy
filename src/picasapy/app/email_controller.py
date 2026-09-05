"""EmailController: kijelölt képek küldése a rendszer levelezőjével
(#32, RÉSZLEGES kör).

Önálló QObject — a `WebExportController`/`PrintController` mintáját
követve NEM az `AppController` mixinje (ld. `print_controller.py`
docstringje az indoklásért). Integrátor-teendők:

1. `application.py`: `EmailController(photo_source=...)` példányosítás
   (`lambda: app_controller._photos.photos`) + `setContextProperty(
   "emailController", ...)`.
2. `Main.qml`/`TrayBar.qml`: a `TrayBar.emailRequested()` jelzés (MÁR kész
   ebben a jegyben) elkapása → tárgy/szöveg bekérése (egyszerű dialógus)
   → `emailController.sendRows(...)`.
3. `OptionsDialog.qml` már ide köti (`OptionsTabEmail.qml`) a méret-
   csúszdákat és az alapértelmezett-kliens kapcsolót — ez a jegy már
   elvégezte, nincs további teendő.

A tényleges küldés a rendszer levelezőjét indítja (freedesktop.org
`xdg-email`, csatolmányokkal; ha nincs telepítve, `mailto:` URL-lel a
rendszer alapértelmezett kezelőjén át — csatolmány nélkül, ld.
`picasapy.mailer` docstringje). Ez SOSEM tesztelhető ténylegesen (nincs
determinisztikus, oldalhatás-mentes módja) — a parancs-összeállítás
(`picasapy.mailer.command`) és az átméretezés-előkészítés
(`prepareAttachments`) igen."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QUrl, Property, Signal, Slot
from PySide6.QtGui import QDesktopServices

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.index import PhotoRecord
from picasapy.mailer import (
    EMAIL_SIZE_DEFAULT,
    EREDETI_MERET,
    build_mailto_url,
    build_xdg_email_argv,
    resolve_email_max_dimension,
)

from .collage_draft_guard import CollageDraftGuard

#: A `shutil.which` és a `subprocess.Popen` MODULSZINTŰ fogantyúja (#1375) —
#: a teszt EZEKET cserélje.
#:
#: A `patch("picasapy.app.email_controller.shutil.which", …)` alak nem a
#: modult módosítja: az `email_controller.shutil` MAGA a globális `shutil`,
#: tehát a csere minden más modulra is hat, amíg a teszt fut.
_which = shutil.which
_popen = subprocess.Popen

_log = logging.getLogger(__name__)

# QSettings-kulcsok — a `mail/` névtér az OptionsTabEmail élő mezőié
#
# #2020: a méret KÉPPONTBAN tárolódik, nem listaindexként — ezért ÚJ kulcs
# (`mail/exportSize`), nem a régi átértelmezése. A régi kulcs értéke egy
# 0..4 index volt egy MÁSIK (becsült) fokozatlistán; ha ugyanazt a kulcsot
# olvasnánk képpontként, a meglévő felhasználók 0…4 KÉPPONTOS méretet
# kapnának — némán, a legkisebb bosszúság nélkül. A migráció egyszeri, és
# az `_atvett_meret` végzi.
_EXPORT_SIZE_KEY = "mail/exportSize"
_SINGLE_ORIGINAL_KEY = "mail/singlePictureOriginal"
_USE_DEFAULT_CLIENT_KEY = "mail/useDefaultClient"

#: A régi, INDEX-alapú kulcsok — csak a migrációhoz olvassuk őket.
_REGI_MULTI_INDEX_KEY = "mail/multiSizeIndex"
_REGI_SINGLE_INDEX_KEY = "mail/singleSizeIndex"

#: A #350 becsült fokozatlistája — kizárólag a régi index feloldásához.
#: Élesben SEHOL nem használjuk; a mért lista az `EMAIL_SIZE_STEPS`.
_REGI_FOKOZATOK: tuple[int, ...] = (640, 800, 1024, 1600, EREDETI_MERET)

_TRUE_VALUES = ("true", "1")


def _coerce_bool(value, default: bool) -> bool:
    """A `QSettings` platformonként bool-t vagy szöveget ad vissza ugyanarra
    az írásra (ld. `appearance_controller.coerce_dark_flag` mintája);
    ismeretlen/hiányzó érték a hívott alapértékre esik vissza."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_VALUES
    return default


def _meret(value, default: int) -> int:
    """A tárolt e-mail méret képpontban; hibás/hiányzó értékre az alapérték.

    ⚠️ NEM szűkítjük az `EMAIL_SIZE_STEPS` nyolc fokozatára: a mező az
    eredetiben is szabad képpontszám (#2020), és egy másik Picasa-verzió
    vagy egy kézi szerkesztés más értéket is hagyhat ott. Csak a
    értelmetlen (negatív) értéket utasítjuk vissza.
    """
    try:
        meret = int(value)
    except (TypeError, ValueError):
        return default
    if meret < 0:
        return default
    return meret


class EmailController(QObject):
    """A `OptionsTabEmail.qml` méret-beállításai + a küldés-előkészítés
    (átméretezés) és a tényleges elküldés (subprocess/mailto) hídja."""

    emailSizeChanged = Signal()
    singlePictureOriginalChanged = Signal()
    useDefaultClientChanged = Signal()
    emailFailed = Signal(str)
    #: #1798b: az előkészítés FOLYAMATJELZŐJE. Az eredeti a
    #: „Preparing attachments…" sorral jelez, amíg a mellékleteket
    #: készíti — a `prepareAttachments` a beállított méretre KICSINYÍTI a
    #: képeket, ami nagy fájloknál másodpercekig tart. Jelzés nélkül a
    #: felhasználó azt látja, hogy nem történik semmi.
    #:
    #: `True` = elkezdődött, `False` = véget ért (sikerrel vagy sem).
    preparingChanged = Signal(bool)

    #: #1798: a felület KÉRDEZZE meg, hogyan küldjön. Akkor dördül el, ha a
    #: felhasználó a Beállításokban a „minden küldéskor kérdezz" módot
    #: választotta. Paraméterei: csatolmány-útvonalak, tárgy, szöveg — a
    #: válasz a `sendWithDefaultClient()`.
    mailChoiceRequested = Signal(list, str, str)

    def __init__(
        self,
        photo_source: Callable[[], Sequence[PhotoRecord]],
        settings: QSettings | None = None,
        parent: QObject | None = None,
        tray_source: Callable[[], Sequence[PhotoRecord]] | None = None,
    ) -> None:
        """`photo_source`: ld. a modul docstringje. `settings`: teszthez
        beinjektálható `QSettings`-példány (`QSettings("...", "...")` egy
        ideiglenes fájlra) — élesben az alapértelmezett globális beállítás
        (az `application.py`-ban már beállított szervezet/app-név alatt)."""
        super().__init__(parent)
        self._photo_source = photo_source
        #: #1671: a KÉPTÁLCA rekordjai. Ha nem üres, ŐK a forrás — a rács
        #: pillanatnyi kijelölése és a látott mappa nem számít. Az eredeti
        #: súgója is így fogalmaz: „Print photos in the Photo Tray". A
        #: mező elhagyható, hogy a meglévő hívók és tesztek ne törjenek el.
        self._tray_source = tray_source
        # #1072: a piszkozat-tilalom — közös a `PrintController`-rel
        self._draft_guard = CollageDraftGuard(self)
        self._settings = settings if settings is not None else QSettings()
        self._email_size = self._betolt_meretet()
        self._single_original = self._betolt_egy_kep_kapcsolot()
        #: #2184: friss profilon a program MEGKÉRDEZI, mivel küldjön.
        #: Az eredetiben a `DoNotPromptForEmailPref` alapértéke 0
        #: (`0x00742154`: `ebp = 0`, majd `0x00742168 je` → MUTASD a
        #: párbeszédet). Nálunk az alapérték `True` volt, vagyis alapból
        #: NEM kérdeztünk — így a választó párbeszéd (és benne a „ne
        #: kérdezz többé" jelölőnégyzet) elérhetetlen maradt annak, aki
        #: sosem nyitja meg az Opciókat.
        self._use_default_client = _coerce_bool(
            self._settings.value(_USE_DEFAULT_CLIENT_KEY), False
        )

    # -- méret-beállítások (OptionsTabEmail.qml csúszdái) ------------------

    def _betolt_meretet(self) -> int:
        """A tárolt méret képpontban — a régi, INDEX-alapú kulcs migrálásával.

        #2020: a #350 `mail/multiSizeIndex` kulcsa egy 0..4 index volt egy
        BECSÜLT fokozatlistán. Az új kulcs képpontot tárol. A régi értéket
        egyszer, a régi listán feloldva vesszük át — enélkül a meglévő
        felhasználó beállítása némán 0…4 KÉPPONTRA romlana.
        """
        tarolt = self._settings.value(_EXPORT_SIZE_KEY)
        if tarolt is not None:
            return _meret(tarolt, EMAIL_SIZE_DEFAULT)
        regi = self._settings.value(_REGI_MULTI_INDEX_KEY)
        if regi is None:
            return EMAIL_SIZE_DEFAULT
        try:
            index = int(regi)
        except (TypeError, ValueError):
            return EMAIL_SIZE_DEFAULT
        if not 0 <= index < len(_REGI_FOKOZATOK):
            return EMAIL_SIZE_DEFAULT
        atvett = _REGI_FOKOZATOK[index]
        self._settings.setValue(_EXPORT_SIZE_KEY, atvett)
        return atvett

    def _betolt_egy_kep_kapcsolot(self) -> bool:
        """Az „egy kép eredeti méretben" kapcsoló — a régi kulcs átvételével.

        #2020: a #350-ben ez egy MÁSODIK méret-csúszka volt
        (`mail/singleSizeIndex`), aminek az utolsó fokozata jelentette az
        eredeti méretet. Az új alapérték a MÉRT viselkedés („ugyanakkora,
        mint a többi"), ami a régi alapértéknek az ELLENTÉTE — ezért a
        meglévő felhasználó beállítását át KELL venni, különben a
        következő indításnál némán megváltozna, amit küld.
        """
        tarolt = self._settings.value(_SINGLE_ORIGINAL_KEY)
        if tarolt is not None:
            return _coerce_bool(tarolt, False)
        regi = self._settings.value(_REGI_SINGLE_INDEX_KEY)
        if regi is None:
            return False
        try:
            index = int(regi)
        except (TypeError, ValueError):
            return False
        if not 0 <= index < len(_REGI_FOKOZATOK):
            return False
        # a régi listán az EREDETI MÉRET az utolsó fokozat volt
        eredeti = _REGI_FOKOZATOK[index] == EREDETI_MERET
        self._settings.setValue(_SINGLE_ORIGINAL_KEY, eredeti)
        return eredeti

    @Property(int, notify=emailSizeChanged)
    def emailSize(self) -> int:  # noqa: N802 — QML-stílus
        """A csatolmányok leghosszabb oldala KÉPPONTBAN; 0 = eredeti méret.

        MÉRVE (#2020): az eredeti a `Preferences\\EmailExportSize` mezőben
        képpontszámot tárol, alapértéke **480**; a csúszka nyolc fokozata
        az `EMAIL_SIZE_STEPS`. A 0 az „eredeti méret" jelzőérték, de az
        eredetiben azt NEM a csúszka adja, hanem a
        `singlePictureOriginal` kapcsoló.
        """
        return self._email_size

    @Slot(int)
    def setEmailSize(self, size_px: int) -> None:  # noqa: N802 — QML-stílus
        size_px = _meret(size_px, self._email_size)
        if size_px == self._email_size:
            return
        self._email_size = size_px
        self._settings.setValue(_EXPORT_SIZE_KEY, size_px)
        self.emailSizeChanged.emit()

    @Property(bool, notify=singlePictureOriginalChanged)
    def singlePictureOriginal(self) -> bool:  # noqa: N802 — QML-stílus
        """Igaz: EGYETLEN kép küldésekor az EREDETI méret megy.

        MÉRVE (#2020): az eredetiben ez **kapcsoló**, nem méret — az
        „Egyedülálló képek mérete" két választógombja („Több elemmel
        azonos (N képpont)" / „Eredeti méret"). A `EmailSinglePicture`
        alapértéke **0**, tehát alapból a közös méret érvényes; a képernyőkép
        is ezt mutatja.

        ⚠️ Ez MEGVÁLTOZTATJA a korábbi viselkedést: a #350 külön
        méret-csúszkát adott egy képre, és annak alapértéke az eredeti
        méret volt. Mostantól egy kép alapból ugyanakkora, mint több.
        """
        return self._single_original

    @Slot(bool)
    def setSinglePictureOriginal(self, eredeti: bool) -> None:  # noqa: N802
        eredeti = bool(eredeti)
        if eredeti == self._single_original:
            return
        self._single_original = eredeti
        self._settings.setValue(_SINGLE_ORIGINAL_KEY, eredeti)
        self.singlePictureOriginalChanged.emit()

    @Property(bool, notify=useDefaultClientChanged)
    def useDefaultClient(self) -> bool:
        """Igaz: a rendszer alapértelmezett levelezőjét használjuk kérdés
        nélkül; hamis: (jövőbeli finomítás) minden küldésnél rákérdezünk —
        a PicasaPy-ban ma mindkét eset ugyanazt az `xdg-email`/`mailto:`
        utat járja, a kapcsoló egyelőre csak a beállítás megőrzését
        szolgálja (FEN-paritás, ld. `OptionsTabEmail.qml`)."""
        return self._use_default_client

    @Slot(bool)
    def setUseDefaultClient(self, use_default: bool) -> None:
        use_default = bool(use_default)
        if use_default == self._use_default_client:
            return
        self._use_default_client = use_default
        self._settings.setValue(
            _USE_DEFAULT_CLIENT_KEY, "true" if use_default else "false"
        )
        self.useDefaultClientChanged.emit()

    # -- küldés-előkészítés + küldés ---------------------------------------

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

    def _resolve_items(self, rows: Sequence[int]) -> list[ExportItem]:
        items = []
        for photo in self._resolve_records(rows):
            items.append(
                ExportItem(
                    source=Path(photo.folder_path) / photo.name,
                    rotate_steps=photo.rotate_steps,
                    filters=photo.filters,
                )
            )
        return items

    @Slot(list, bool, result=list)
    def prepareAttachments(self, rows, multi: bool) -> list[str]:
        """A kijelölt sorok csatolmány-fájllá alakítása: a beállított
        méret-fokozatnak megfelelő átméretezéssel (a forgatás/`filters=`
        lánc a `picasapy.export.export_photos` motorral égetve bele, mint
        exportnál) egy ideiglenes mappába. `multi`: melyik méret-beállítást
        (`multiSizeIndex`/`singleSizeIndex`) alkalmazza. Eredeti méretnél
        (utolsó fokozat) a forrásfájlt közvetlenül adja vissza — nincs
        felesleges másolat."""
        items = self._resolve_items(rows)
        if not items:
            return []
        # a jelzés a KORAI kilépések UTÁN indul: üres kijelölésre nincs mit
        # előkészíteni, és egy azonnal eltűnő jelző csak villanna
        self.preparingChanged.emit(True)
        try:
            return self._keszitsd_elo(items, multi)
        finally:
            # a `finally` KÖTELEZŐ: ha az előkészítés kivétellel áll meg, a
            # jelző beragadna, és a felület örökre „dolgozom" állapotban
            # maradna
            self.preparingChanged.emit(False)

    def _keszitsd_elo(self, items, multi: bool) -> list[str]:
        """Az előkészítés törzse — a jelzés a hívóban van, hogy a korai
        kilépések ne villantsanak feleslegesen."""
        # #1072: a befejezetlen kollázst nem küldjük el
        # (`projectutils::draft_collage`: a megosztás a befejezés
        # feltétele). Az egész küldés áll meg, nem csak a piszkozat marad
        # ki — egy csendben elhagyott csatolmányról a feladó nem tudna.
        if self._draft_guard.first_draft(item.source for item in items) is not None:
            self.emailFailed.emit(self._draft_guard.restriction_message())
            return []
        # #2020: egyetlen KÉPPONT-beállítás van; az „egy kép" nem külön
        # méret, hanem kapcsoló az eredeti méretre.
        meret = (
            EREDETI_MERET
            if (not multi and self._single_original)
            else self._email_size
        )
        max_dimension = resolve_email_max_dimension(meret)
        if max_dimension is None:
            return [str(item.source) for item in items]
        target_dir = Path(tempfile.mkdtemp(prefix="picasapy-mail-"))
        settings = ExportSettings(max_dimension=max_dimension, jpeg_quality=85)
        report = export_photos(items, target_dir, settings)
        if report.failed:
            _log.warning(
                "e-mail előkészítés: %d elem sikertelen", len(report.failed)
            )
        return [str(path) for path in report.exported]

    @Slot(list, str, str, result=bool)
    def sendRows(self, attachment_paths, subject: str, body: str) -> bool:
        """A már előkészített (`prepareAttachments`) fájlok elküldése.

        #1798: ELŐBB a beállítás. Ha a felhasználó a „minden küldéskor
        kérdezz" módot választotta, itt NEM küldünk, hanem a
        `mailChoiceRequested` jelzéssel kérdést kérünk a felülettől — a
        válasz a `sendWithDefaultClient()`. Enélkül a beállítás néma volt:
        tárolódott, visszajelzett, és a küldés átlépett rajta.

        A visszatérési `False` itt azt jelenti, hogy a küldés MÉG nem
        történt meg — nem azt, hogy elbukott."""
        if not self._use_default_client:
            self.mailChoiceRequested.emit(
                list(attachment_paths), subject, body
            )
            return False
        return self._kuldes(attachment_paths, subject, body)

    @Slot(list, str, str, bool, result=bool)
    def sendWithDefaultClient(
        self, attachment_paths, subject: str, body: str, remember: bool
    ) -> bool:
        """A választó-párbeszéd válasza: küldés az alapértelmezett
        levelezővel.

        A `remember` a mért `DoNotPromptForEmailPref` megfelelője — ha be
        van jelölve, a Beállítások rádiója is visszaáll, tehát legközelebb
        nem kérdezünk."""
        if remember:
            self.setUseDefaultClient(True)
        return self._kuldes(attachment_paths, subject, body)

    def _kuldes(self, attachment_paths, subject: str, body: str) -> bool:
        """A tényleges indítás: `xdg-email`, annak hiányában `mailto:`
        visszaesés — csatolmány NÉLKÜL (ld. a modul docstringje), erről az
        `emailFailed` jelez, hogy a UI figyelmeztethesse a felhasználót."""
        attachments = [Path(path) for path in attachment_paths]
        xdg_email = _which("xdg-email")
        if xdg_email is not None:
            argv = build_xdg_email_argv(subject, body, attachments)
            try:
                _popen(argv)  # noqa: S603 — argv-lista, nincs shell
            except OSError as error:
                self.emailFailed.emit(str(error))
                return False
            return True

        if attachments:
            self.emailFailed.emit(
                self.tr(
                    "No email program with attachment support was found; "
                    "opening a blank email without the pictures attached."
                )
            )
        url = build_mailto_url(subject, body)
        opened = QDesktopServices.openUrl(QUrl(url))
        if not opened:
            self.emailFailed.emit(self.tr("No email program was found."))
        return bool(opened)

"""Exportálás mappába (#16) — az AppController export-szelete (#150), a
`fileops_controller` melletti önálló modulban.

Mixin-osztály: az `AppController` örökli; a QML és a tesztek változatlanul
a `controller.exportRows(...)` slotot és az `exportFinished` jelzést
használják."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QStandardPaths, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from picasapy.export.earth import export_google_earth
from picasapy.export import (
    ExportItem,
    ExportSettings,
    export_photos,
    is_automatic_quality,
    resolve_export_quality,
)
from picasapy.fileops import has_enough_free_space, required_bytes_for
from picasapy.lazy_cv2 import elore_betolt

from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

from .formatting import to_local_path
from .export_prefs import EXPORT_PATH_SETTINGS_KEY as _EXPORT_PATH_KEY
from .export_prefs import MOVIE_FULL_SETTINGS_KEY as _MOVIE_FULL_KEY
from .export_prefs import (
    SIZE_PRESETS,
    read_export_prefs,
    write_export_prefs,
)
from .exported_folders import (
    EXPORTED_FOLDERS_SETTINGS_KEY,
    existing_exported_folders,
    remember_exported_folder,
)
from .worker_thread import BackgroundWorkerMixin

#: #1589: a rendszer társított programjának indítása — MODULSZINTŰ fogantyú
#: (a `version._run`, `index.sync._stat` és a `fileops.reveal._run` mintája).
#: A teszt EZT cseréli ki: a `QDesktopServices` globális osztályát átírni
#: tilos, arra külön őrünk van (#1375), és egy elszabadult teszt valódi
#: Google Earth-öt (vagy böngészőt) indítana a fejlesztő gépén.
_open_url = QDesktopServices.openUrl


#: az eredeti fájlnév-tisztítása (`0x009946f0`): a Windows tiltott
#: karakterhalmaza. Ugyanez a rutin szolgál ki minden névképzést a
#: programban, ezért itt is egy helyen mondjuk ki.
_TILTOTT_FAJLNEV_KARAKTEREK = '\\/:*?"<>|'


def _tiszta_fajlnev(nev: str) -> str:
    return "".join(k for k in nev if k not in _TILTOTT_FAJLNEV_KARAKTEREK).strip()


def _export_item(record) -> ExportItem:
    """Egy fotó-rekord export-elemmé — a forgatás és a szerkesztési lánc
    beleég a célfájlba (#136), hogy a rács képe és az exportált fájl
    megegyezzen."""
    return ExportItem(
        source=Path(record.folder_path) / record.name,
        rotate_steps=record.rotate_steps,
        filters=record.filters,
        # #1166: a felirat és a címkék átkerülnek a célmappa
        # `.picasa.ini`-jébe — az eredetiben ezt a közös kimeneti mag
        # (`CImageOutput`, `0x0073f320`) végzi.
        caption=record.caption,
        keywords=",".join(record.keywords) if record.keywords else None,
    )


class ExportMixin(BackgroundWorkerMixin):
    """A kijelölés háttérszálas exportja célmappába."""

    # #16: export kész — (exportált darab, sikertelen darab); háttérszálból
    # érkezik, a Qt automatikusan a főszálra sorolja
    exportFinished = Signal(int, int)
    # #530: Google Earth-export vége — a kiírt KML útvonala (üres string, ha
    # nem készült), a térképre került képek száma, és hány maradt ki
    # koordináta híján (ezt a felhasználónak meg kell tudni mondani).
    earthExportFinished = Signal(str, int, int)
    # #1589: a „Megtekintés a Google Earth programban…" ága. Ugyanaz a
    # kiírás, MÁS folytatás: a felület ezután megnyittatja a fájlt
    # (`openKml`). Azért külön jelzés, mert a megnyitást a FŐSZÁLON kell
    # kérni — a háttérszálból indított `QDesktopServices.openUrl` nem
    # biztonságos.
    earthViewReady = Signal(str, int, int)
    # #457: „Exportált képek" — az exportált célmappák listája változott.
    # Az eredeti külön csomópont alá gyűjtötte őket a navigációban: az
    # export így NYOMON KÖVETHETŐ maradt, nem tűnt el a fájlrendszerben.
    exportedFoldersChanged = Signal()
    # #136: az első néhány sikertelen fájl neve + oka ("fájlnév: hiba") —
    # az exportFinished előtt megy ki, hogy a UI-dialógus a számmal együtt
    # a konkrét okot is megjeleníthesse.
    exportFailedDetails = Signal(list)

    # az exportResultDialog-ban ennyi hibás fájl nevét/okát mutatjuk —
    # tömeges hibánál a teljes lista inkább zavaró, mint hasznos
    _EXPORT_FAILED_DETAILS_LIMIT = 5

    #: #1166: a film-rádió állása — az eredeti `Preferences\FileExportMovie`
    #: megfelelője (`0x00738c88`–`0x00738cb3`): nem nulla → „Teljes film",
    #: nulla/hiányzó → „Első képkocka". A mi alapértékünk ezért False.
    #: #1138: a kulcsnév a közös `export_prefs` modulból jön — a
    #: párbeszéd kilenc kulcsa egy helyen él.
    MOVIE_FULL_SETTINGS_KEY = _MOVIE_FULL_KEY

    #: #1166: a hely alapértéke — az eredetiben a `DefaultExportPath`
    #: korábbi értéke, hiányában a honosított `Picasa\Exportálások\`
    #: (`0x00738d16`, nyers alapérték `Picasa\Exports\`, kulcs
    #: `CExportPrefsDialog::deffolder`).
    EXPORT_PATH_SETTINGS_KEY = _EXPORT_PATH_KEY

    @Slot(result=str)
    def defaultExportName(self) -> str:
        r"""Az exportált mappa nevének alapértéke (#1166).

        Mérve (`docs/specs/export-parbeszed.md` 12.1): a név **a
        kiválasztott album/mappa neve** (`0x0073b500`, a bemeneti szerkezet
        `+8` mezője); ha az üres, a honosított `export`
        (`CExportPrefsDialog::exportname`, magyarul „exportálás").

        A nevet fájlnév-tisztításon engedjük át — az eredeti is ezt teszi
        (`0x009946f0`, tiltott halmaz `\ / : * ? " < > |`)."""
        mappa = self.currentFolder
        nev = Path(mappa).name if mappa else ""
        if not nev:
            nev = self.tr("export")
        return _tiszta_fajlnev(nev)

    @Slot(result=str)
    def defaultExportLocation(self) -> str:
        """A kimeneti hely alapértéke (#1166) — a korábban használt hely,
        hiányában a képek mappájában a honosított gyűjtő."""
        tarolt = self._get_settings().value(self.EXPORT_PATH_SETTINGS_KEY)
        if isinstance(tarolt, str) and tarolt.strip():
            return tarolt
        kepek = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        if not kepek:
            kepek = str(Path.home())
        return str(Path(kepek) / "Picasa" / self.tr("Exports"))

    @Slot(str)
    def rememberExportLocation(self, target_dir: str) -> None:
        """A választott hely megőrzése a következő exporthoz (#1166)."""
        target = to_local_path(target_dir)
        if target:
            self._get_settings().setValue(self.EXPORT_PATH_SETTINGS_KEY, target)

    @Slot(result=bool)
    def exportMovieFull(self) -> bool:
        """A film-rádió tárolt állása (#1166) — a párbeszéd ebből indul."""
        ertek = self._get_settings().value(self.MOVIE_FULL_SETTINGS_KEY)
        if ertek is None:
            return False
        if isinstance(ertek, str):
            return ertek.strip().lower() not in ("", "0", "false")
        return bool(int(ertek)) if isinstance(ertek, (int, float)) else bool(ertek)

    @Slot(bool)
    def setExportMovieFull(self, full: bool) -> None:
        """A film-rádió állásának megőrzése a következő exportig (#1166)."""
        self._get_settings().setValue(self.MOVIE_FULL_SETTINGS_KEY, bool(full))

    # -- a párbeszéd megőrzött beállításai (#1138) ---------------------------

    @Slot(result="QVariantMap")
    def exportSettings(self) -> dict:
        """A párbeszéd MEGŐRZÖTT beállításai (#1138, spec 4. szakasz).

        A leképezés, az alapértékek és a `FileExportSize` körüli kimondott
        bizonytalanság az `app/export_prefs.py` modul-docstringjében."""
        return read_export_prefs(self._get_settings())

    @Slot("QVariantMap")
    def saveExportSettings(self, values) -> None:
        """A beállítások kiírása — EGYETLEN menetben, az ELFOGADÁSKOR.

        Spec 13.7 (mért): a közös párbeszéd-lezáró (`0x008d2720`) csak
        akkor hívja a kiírót (`vt[0x164]` = `0x00739960`), ha a lezárási
        kód 0; a Mégse ága az üres tő (`0x00b0d990`, egyetlen `ret`).
        Ezért a felület sem menthet vezérlőnként — egyetlen hívás, az
        `onAccepted`-ben."""
        write_export_prefs(self._get_settings(), values)

    @Slot(result="QVariantList")
    def exportSizePresets(self) -> list:
        """A méret-csúszka hét fogása (`export.fen` `bind17.list`).

        A felület innen kéri el: egyetlen igazságforrás, hogy a QML és a
        mentett méret-index ne csússzon szét."""
        return list(SIZE_PRESETS)

    @Slot(str, result=bool)
    def exportQualityIsAutomatic(self, quality_preset: str) -> bool:
        """Az „Automatikus" fokozat van-e kiválasztva (#1138).

        Külön kérdés a `resolveExportQuality`-tól, mert az eredetiben is
        külön logikai jelző hordozza (`[objektum+0xa40] = 1`,
        `0x00739c4d`), nem a szám: az „Automatikus" és a „Normál"
        ugyanarra a 85-re megy."""
        return is_automatic_quality(quality_preset)

    @Slot("QVariantList", result=bool)
    def selectionHasVideo(self, rows) -> bool:
        """Van-e videó a megadott sorok között (#1166).

        A `.fen` nem ad kötést a film-rádiók engedélyezésére: a
        képernyőképen mindkettő szürke, ha a kijelölésben nincs film —
        futásidejű döntés (a spec 9.3/2. pontja)."""
        photos = self._photos.photos
        for nyers in rows or ():
            try:
                row = int(nyers)
            except (TypeError, ValueError):
                continue
            if 0 <= row < len(photos):
                nev = photos[row].name
                if Path(nev).suffix.lower() in VIDEO_EXTENSIONS:
                    return True
        return False

    @Slot(result=bool)
    def trayHasVideo(self) -> bool:
        """Van-e film a KÉPTÁLCÁN (#455 · #1166).

        A film-rádiók engedélyezését eddig `useTray ? true` alakban
        rövidítette a párbeszéd: amíg a tálca csak külön művelettel telt
        meg, ez ritka és láthatatlan pontatlanság volt. A #455 óta a tálca
        a kijelölés tükre, tehát MINDIG az a forrás — a rövidítés így
        minden exportnál engedélyezte volna a film-rádiókat, film nélkül is.
        """
        felold = getattr(self, "_tray_records", None)
        if felold is None:
            return False
        return any(
            Path(record.name).suffix.lower() in VIDEO_EXTENSIONS
            for record in felold()
        )

    def _export_error_text(self, kind: str) -> str:
        """A köteg-szintű hiba fajtájából az EREDETI Picasa üzenete (#1166).

        A tíz hibaág szövege a `Picasa3i18n.dll`-ből, a kulcsok a
        `CExportPrefsPage` (`0x007f6650`) és a `CImageOutput`
        (`0x0073f320`) függvényéből; a leképezés indoklása a
        `docs/specs/export-parbeszed.md` 8. szakaszában."""
        if kind == "destdir":
            # IDS_DESTDIRCANNOCREATE
            return self.tr("The destination directory could not be created.")
        if kind == "delete":
            # CExportPrefsPage::deleteerror
            return self.tr(
                "An internal error occured, while deleting the previous album."
            )
        if kind == "remove":
            # CExportPrefsPage::removeerror
            return self.tr(
                "An internal error occured, while removing a directory."
            )
        if kind == "scan":
            # CExportPrefsPage::scanerror
            return self.tr(
                "An internal error occured, while scanning directories."
            )
        if kind == "scanfile":
            # CExportPrefsPage::scanfileerror
            return self.tr("An internal error occured, while scanning files.")
        if kind == "write":
            # CImageOutput::filewriteerr
            return self.tr(
                "Unable to write all files due to a disk error. "
                "The disk may be full or read-only."
            )
        if kind == "noimages":
            # IDS_NO_IMAGES_TO_SEND
            return self.tr("No images were available to send.")
        return ""

    @Slot(str, result=bool)
    def exportTargetExists(self, target_dir: str) -> bool:
        """Létezik-e már a célmappa, ÉS van-e benne bármi (#1166).

        Az eredetiben ilyenkor jön a kérdés (`CExportPrefsPage::destexists`
        — „A cél már létezik. Felülírja az új albummal?"), és igen esetén
        a program az ELŐZŐ albumot törli. Üres mappánál nincs mit
        felülírni, ezért arra sem kérdezünk."""
        target = to_local_path(target_dir)
        if not target:
            return False
        path = Path(target)
        if not path.is_dir():
            return False
        return any(path.iterdir())

    @Slot(str, int, result=int)
    def resolveExportQuality(self, quality_preset: str, custom_quality: int) -> int:
        """A minőség-lenyíló (#369, export.fen "Image quality" popup)
        preset-nevét konkrét JPEG-minőségre fordítja — ld.
        `picasapy.export.resolve_export_quality` docstringje a közelítés
        indoklásáért (a pontos Picasa-értékek nem dokumentáltak)."""
        return resolve_export_quality(quality_preset, custom_quality)

    @Slot(list, str, int, int, bool, str, bool, bool)
    def exportRows(self, rows, target_dir: str, max_dimension: int,
                   jpeg_quality: int, add_numbers: bool = False,
                   watermark_text: str = "", purge_existing: bool = False,
                   quality_automatic: bool = False) -> None:
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
            _export_item(photos[int(r)])
            for r in rows
            if 0 <= int(r) < len(photos)
        )
        self._export_items(items, target_dir, max_dimension, jpeg_quality,
                           add_numbers, watermark_text, purge_existing,
                           quality_automatic)

    @Slot(str, int, int, bool, str, bool, bool)
    def exportHeld(self, target_dir: str, max_dimension: int,
                   jpeg_quality: int, add_numbers: bool = False,
                   watermark_text: str = "", purge_existing: bool = False,
                   quality_automatic: bool = False) -> None:
        """A KÉPTÁLCA tartalmának exportja célmappába (#455, 3. teendő).

        Az eredetiben a tálca alatti műveletsor a **tálca tartalmán**
        dolgozott, nem a pillanatnyi kijelölésen — a Picasa buboréksúgói is
        végig „a képtálca képeire" hivatkoznak. A tálca mappákon átnyúlik,
        ezért itt nem rács-sorokkal, hanem a globális indexből felolvasott
        fotó-rekordokkal dolgozunk (a forgatás és a `filters=` lánc így
        ugyanúgy beleég, mint a kijelölés-alapú úton).
        """
        self._export_items(
            self._held_export_items(), target_dir, max_dimension,
            jpeg_quality, add_numbers, watermark_text, purge_existing,
            quality_automatic,
        )

    def _held_export_items(self) -> tuple[ExportItem, ...]:
        """A tálca tartalma export-tételként, beszúrási sorrendben.

        A rekordokat a `TrayMixin._tray_records()` oldja fel: a nyitott
        mappa képeit a memóriabeli modellből, a máshonnan tartottakat az
        indexből (egyetlen kapcsolatban, megjegyezve). Az időközben eltűnt
        kép ott egyszerűen kimarad — nem hiba, és nem akaszt meg köteget.
        """
        felold = getattr(self, "_tray_records", None)
        if felold is None:
            return ()
        return tuple(_export_item(record) for record in felold())

    def _export_items(self, items, target_dir: str, max_dimension: int,
                      jpeg_quality: int, add_numbers: bool,
                      watermark_text: str, purge_existing: bool = False,
                      quality_automatic: bool = False) -> None:
        target = to_local_path(target_dir)
        if not items or not target:
            # #1166: az eredeti sem hallgat — `IDS_NO_IMAGES_TO_SEND`
            if not items:
                self.exportFailedDetails.emit([self._export_error_text("noimages")])
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
            # #1166: a film-rádió állását a párbeszéd az indítás ELŐTT
            # elmenti (`setExportMovieFull`), ezért itt a tárolt érték
            # MINDIG a most választott — nem kell nyolcadik paraméter.
            movie_full=self.exportMovieFull(),
            # #1138: az „Automatikus" fokozat — a kimenet a FORRÁS
            # kvantálási tábláit veszi át (spec 3.3/7.1), nem a
            # `jpeg_quality`-t. Az utóbbi csak visszaesés marad.
            quality_automatic=bool(quality_automatic),
        )

        # #457: a célmappa a „Exportált képek" nyilvántartásba kerül —
        # MÉG az export előtt, hogy egy félbeszakadt művelet célja se
        # vesszen el a felhasználó szeme elől
        self._remember_exported_folder(target)
        # #1539: a bekötés a GUI-szálon, a háttérszál indítása ELŐTT
        self._ensure_output_resync_wired()

        def worker():
            report = export_photos(
                items, Path(target), settings, purge_existing=purge_existing
            )
            if report.failed:
                details = [
                    f"{path.name}: {reason}"
                    # strict=True: az ExportReport.reasons a failed-del
                    # mindig azonos hosszú (ld. export/exporter.py docstring).
                    for path, reason in zip(report.failed, report.reasons, strict=True)
                ][: self._EXPORT_FAILED_DETAILS_LIMIT]
                # #1166: a lista ÉLÉN az eredeti Picasa saját üzenete áll a
                # hiba fajtájáról; a fájlonkénti okok utána következnek.
                fejlec = self._export_error_text(report.error_kind)
                if fejlec:
                    details = [fejlec, *details]
                self.exportFailedDetails.emit(details)
            # #1539: ha a cél a figyelt gyökér ALATT van, célzott
            # újraolvasás kell — mérve, figyelő nélkül az exportált kép
            # 25 s alatt sem jelent meg. Elég EGY fájlt bejelenteni: az
            # export mind egyetlen mappába ír.
            #
            # #1565: ugyanez a bejelentés viszi a figyelt körön KÍVÜLI célt
            # is (az export ALAPÉRTELMEZETT helyét,
            # `<Képek>/Picasa/Exports`) — ott a `resyncOutputFolder`
            # szándékosan kilép, és az `indexExportedFolder` veszi át: a
            # célmappa SAJÁT GYÖKÉRKÉNT kerül az indexbe. Figyelt gyökeret
            # ez sem vesz fel a felhasználó nevében; a kapu az „Exportált
            # képek" nyilvántartása, amibe a fenti sor épp most tette be a
            # célt — ezért kell a `_remember_exported_folder` ELŐBB.
            if report.exported:
                self.noteOutputWritten(str(report.exported[0]))
            self.exportFinished.emit(len(report.exported), len(report.failed))

        # #2370: a cv2-t a HÍVÓ (GUI-)szálon hozzuk be, a háttérszál
        # INDÍTÁSA ELŐTT. Ha ez itt kimarad, az első `import cv2` az
        # export-munkaszálon fut le (`exporter._decode_image` →
        # `lazy_cv2.__getattr__`), és Windowson a párhuzamos
        # szemétgyűjtéssel ACCESS_VIOLATION-t adott — hat egymást követő
        # main-futáson. Ugyanaz a szándék, mint a fenti
        # `_ensure_output_resync_wired()`-nél (#1539): ami a GUI-szálra
        # való, az a szálindítás elé kerül.
        elore_betolt()
        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-export")

    # -- Google Earth-export (#530) ------------------------------------------

    @Slot(list, str, str)
    def exportGoogleEarth(self, rows, target_dir: str, folder_name: str = "") -> None:
        """A kijelölt képek kiírása Google Earth-höz: `doc.kml` + `thumbs/`.

        Csak a GEOCÍMKÉZETT képek kerülnek a térképre; a többit a jelentés
        `skipped` mezője számolja, hogy a felület meg tudja mondani, miért
        kevesebb a helyjelző a kijelölésnél. Egyetlen geocímkézett kép nélkül
        nem írunk fájlt — üres térkép félrevezető lenne.

        Háttérszálon fut (a bélyegképek NAS-on percekig tarthatnak), a végén
        `earthExportFinished(kmlPath, helyjelzők, kihagyottak)`.

        #1539: itt SZÁNDÉKOSAN nincs célzott újraolvasás, és ez nem
        feledékenység. A kimenet nem böngészendő fotógyűjtemény, hanem egy
        `doc.kml` + a hozzá tartozó `thumbs/` segédmappa: a bélyegképek a
        térkép helyjelzőinek buborékképei, önmagukban nem valók a rácsra.
        A `doc.kml` ráadásul nem is indexelt médiatípus. A rendeltetési
        hely a Google Earth, nem a PicasaPy könyvtára.
        """
        self._earth_export(rows, target_dir, folder_name, self.earthExportFinished)

    @Slot(list, str, str)
    def viewGoogleEarth(self, rows, target_dir: str, folder_name: str = "") -> None:
        """#1589: `ID_VIEW_EARTH` — ugyanaz a KML, de utána MEGNYITJUK.

        Az eredetiben KÉT külön menütétel van ugyanarra a kiírásra: az
        `ID_EXPORT_EARTH` csak kiírja a fájlt, az `ID_VIEW_EARTH` kiírja
        **és megnyitja** (`docs/specs/picasa-menu-parancsok-viselkedes.md`
        `ID_VIEW_EARTH` szakasza). Ezért nincs itt külön motor: ugyanaz az
        `_earth_export` fut, csak a befejező jelzés más — a felület a
        `earthViewReady`-re hívja az `openKml`-t.
        """
        self._earth_export(rows, target_dir, folder_name, self.earthViewReady)

    def _earth_export(self, rows, target_dir: str, folder_name: str, kesz) -> None:
        """A két Google Earth-menütétel KÖZÖS útja; `kesz` a záró jelzés."""
        target = to_local_path(target_dir)
        photos = self._photos.photos
        records = tuple(
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        )
        if not records or not target:
            kesz.emit("", 0, 0)
            return

        cel = Path(target)
        nev = folder_name or cel.name

        def worker():
            report = export_google_earth(records, cel, folder_name=nev)
            kesz.emit(
                str(report.kml_path) if report.kml_path else "",
                report.placemarks,
                report.skipped_without_location,
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-earth-export")

    @Slot(str, result=bool)
    def openKml(self, kml_path: str) -> bool:
        """#1589: a kiírt KML átadása a rendszer társított programjának.

        Igazat ad, ha a megnyitás elindult. HAMISAT ad, ha nincs társítva
        program — a felületnek ezt KI KELL MONDANIA, mert különben a
        „Megtekintés…" némán hatástalan marad (#936).

        ⚠️ Az eredeti a Windows-registryből olvassa a Google Earth
        verzióját, és két külön ágon („telepítenie kell" / „frissítenie
        kell") kínálja a `http://earth.google.com` címet. Linuxon nincs
        registry, és a #1589 döntése szerint a Google letöltőoldalára
        mutató hivatkozást NEM vesszük át — marad az egyetlen, mérhető ág:
        elindult-e a társított program.
        """
        local = to_local_path(kml_path)
        if not local or not Path(local).exists():
            return False
        return bool(_open_url(QUrl.fromLocalFile(local)))

    # -- „Exportált képek" (#457) --------------------------------------------

    def _remember_exported_folder(self, folder: str) -> None:
        settings = self._get_settings()
        updated = remember_exported_folder(
            settings.value(EXPORTED_FOLDERS_SETTINGS_KEY), folder
        )
        settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, updated)
        self.exportedFoldersChanged.emit()

    @Property("QVariantList", notify=exportedFoldersChanged)
    def exportedFolders(self):  # noqa: N802 — QML-property-stílus
        """A létező exportált mappák, legutóbbi elöl — `[{path, name}]`.

        A már törölt/átnevezett mappákat kiszűrjük: a navigációban nincs
        értelme halott csomópontot mutatni."""
        settings = self._get_settings()
        return [
            {"path": path, "name": Path(path).name or path}
            for path in existing_exported_folders(
                settings.value(EXPORTED_FOLDERS_SETTINGS_KEY)
            )
        ]

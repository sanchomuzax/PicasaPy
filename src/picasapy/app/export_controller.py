"""Exportálás mappába (#16) — az AppController export-szelete (#150), a
`fileops_controller` melletti önálló modulban.

Mixin-osztály: az `AppController` örökli; a QML és a tesztek változatlanul
a `controller.exportRows(...)` slotot és az `exportFinished` jelzést
használják."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QStandardPaths, Signal, Slot

from picasapy.export.earth import export_google_earth
from picasapy.export import (
    ExportItem,
    ExportSettings,
    export_photos,
    resolve_export_quality,
)
from picasapy.fileops import has_enough_free_space, required_bytes_for

from picasapy.index import open_index, photo_by_id
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

from .formatting import to_local_path
from .exported_folders import (
    EXPORTED_FOLDERS_SETTINGS_KEY,
    existing_exported_folders,
    remember_exported_folder,
)
from .worker_thread import BackgroundWorkerMixin


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
    MOVIE_FULL_SETTINGS_KEY = "export/moviefull"

    #: #1166: a hely alapértéke — az eredetiben a `DefaultExportPath`
    #: korábbi értéke, hiányában a honosított `Picasa\Exportálások\`
    #: (`0x00738d16`, nyers alapérték `Picasa\Exports\`, kulcs
    #: `CExportPrefsDialog::deffolder`).
    EXPORT_PATH_SETTINGS_KEY = "export/defaultpath"

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

    @Slot(list, str, int, int, bool, str, bool)
    def exportRows(self, rows, target_dir: str, max_dimension: int,
                   jpeg_quality: int, add_numbers: bool = False,
                   watermark_text: str = "", purge_existing: bool = False) -> None:
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
                           add_numbers, watermark_text, purge_existing)

    @Slot(str, int, int, bool, str, bool)
    def exportHeld(self, target_dir: str, max_dimension: int,
                   jpeg_quality: int, add_numbers: bool = False,
                   watermark_text: str = "", purge_existing: bool = False) -> None:
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
        )

    def _held_export_items(self) -> tuple[ExportItem, ...]:
        held = list(getattr(self, "_held_ids", ()) or ())
        if not held:
            return ()
        items = []
        with open_index(self._db_path) as conn:
            for photo_id in held:
                record = photo_by_id(conn, photo_id)
                # az időközben eltűnt kép egyszerűen kimarad (a heldPaths
                # ugyanezt teszi) — nem hiba, és nem is akaszt meg semmit
                if record is not None:
                    items.append(_export_item(record))
        return tuple(items)

    def _export_items(self, items, target_dir: str, max_dimension: int,
                      jpeg_quality: int, add_numbers: bool,
                      watermark_text: str, purge_existing: bool = False) -> None:
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
        )

        # #457: a célmappa a „Exportált képek" nyilvántartásba kerül —
        # MÉG az export előtt, hogy egy félbeszakadt művelet célja se
        # vesszen el a felhasználó szeme elől
        self._remember_exported_folder(target)

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
            self.exportFinished.emit(len(report.exported), len(report.failed))

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
        """
        target = to_local_path(target_dir)
        photos = self._photos.photos
        records = tuple(
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        )
        if not records or not target:
            self.earthExportFinished.emit("", 0, 0)
            return

        cel = Path(target)
        nev = folder_name or cel.name

        def worker():
            report = export_google_earth(records, cel, folder_name=nev)
            self.earthExportFinished.emit(
                str(report.kml_path) if report.kml_path else "",
                report.placemarks,
                report.skipped_without_location,
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-earth-export")

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

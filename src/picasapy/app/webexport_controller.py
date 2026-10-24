"""WebExportController: a "Weboldal exportálása…" dialógus (#351,
`webexport.fen`, `docs/specs/picasa-fen-dialogs.md` 3.12.) QML-hídja a
`picasapy.webexport` motor fölött.

Önálló QObject — a `RelocateController`/`DedupController` mintáját követve
NEM az `AppController` mixinje, hogy a `controller.py`/`Main.qml` (forró
fájlok, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést kapja az
INTEGRÁTOR lépésében:

1. `application.py`: `WebExportController(photo_source=...)` példányosítás —
   a `photo_source` egy hívható, ami a kiválasztott mappa/album
   `PhotoRecord`-jait adja vissza (pl. `lambda: app_controller._photos.photos`
   a jelenleg megnyitott mappára — a `PhotoGridModel` ezt már tárolja).
2. `Main.qml`: `engine.rootContext().setContextProperty("webExportController", ...)`
   + a `WebExportDialog` példányosítása (a `MoveDatabaseDialog` mintája).
3. `PicasaMenuBar.qml` `webExportRequested()` jelzés bekötése a dialógus
   megnyitására (a jelzés és a menüpont MÁR készen áll ebben a jegyben).

A generálás HÁTTÉRSZÁLON fut (a kép-átméretezés/kódolás percekig tarthat
nagyobb albumnál) — a `webExportProgress` a `picasapy.webexport.images`
képenkénti előrehaladását jelzi.

#505: a háttérszál a `BackgroundWorkerMixin`-en át indul (korábban saját,
kézzel nyilvántartott `threading.Thread` volt — ez a modul íródott a
mixin ELŐTT, ld. `worker_thread.py` docstringje) — ez adja MAGÁTÓL az
alsó kék sáv busy-animációját is (`AppBusyRegistry`, `busy_registry.py`),
külön bekötés nélkül. Az `exportRunning`/`waitForExport` metódusnevek
megmaradtak (a hívók/tesztek ezekre hivatkoznak), de belül a mixin
`backgroundWorkersRunning`/`waitForBackgroundWorkers`-ét hívják."""

from __future__ import annotations

import logging
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QStandardPaths, Signal, Slot

from picasapy.fileops import has_enough_free_space, required_bytes_for
from picasapy.index import PhotoRecord
from picasapy.webexport import (
    AlbumExportData,
    WebExportSettings,
    list_templates,
    run_web_export,
)
from picasapy.webexport.images import prepare_photo_exports
from picasapy.webexport.ftp_publish import FtpAccount, FtpAccountStore, FtpPublisher
from picasapy.webexport.sizes import (
    DEFAULT_SIZE_INDEX,
    SIZE_CHOICES,
    image_size_for_index,
    settings_for_template,
)

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)

#: #4610: az eredeti `Preferences\WebExportSize` / `WebExportMovie` párja —
#: a választó INDEXE és a mozgókép-mód (spec 6.1).
SIZE_SETTINGS_KEY = "webexport/size"
MOVIE_FULL_SETTINGS_KEY = "webexport/movieFull"
WEB_EXPORT_TARGET_SETTINGS_KEY = "webexport/targetDir"
WEB_EXPORT_TEMPLATE_SETTINGS_KEY = "webexport/templateId"


def _platform() -> str:
    """A futó platform — a Windows-alapértelmezés külön is tesztelhető."""
    return sys.platform


class WebExportController(BackgroundWorkerMixin, QObject):
    """A `WebExportDialog.qml` háttér-hídja: sablon-lista, háttérszálas
    generálás haladás-jelzéssel, hiba-visszajelzés."""

    webExportStarted = Signal()
    # (kész kép, összes kép) — a kép-generálási fázis haladása
    webExportProgress = Signal(int, int)
    # (célmappa, generált oldalak száma) — sikeres futás
    webExportFinished = Signal(str, int)
    # (fióknév, ténylegesen feltöltött helyi fájlok száma)
    ftpPublishFinished = Signal(str, int)
    webExportFailed = Signal(str)  # emberi nyelvű hibaüzenet

    def __init__(
        self,
        photo_source: Callable[[], Sequence[PhotoRecord]],
        parent: QObject | None = None,
        settings=None,
        ftp_account_store: FtpAccountStore | None = None,
        ftp_publisher: FtpPublisher | None = None,
    ) -> None:
        """`photo_source`: hívható, ami a jelenleg kiválasztott mappa/album
        `PhotoRecord`-jait adja vissza — az integrátor köti a meglévő
        fotó-modellhez (ld. a modul docstringje). `settings`: `value()`/
        `setValue()` páros (tesztekhez); alapból `QSettings`."""
        super().__init__(parent)
        self._photo_source = photo_source
        self._settings = settings
        self._ftp_account_store = ftp_account_store
        self._ftp_publisher = ftp_publisher or FtpPublisher()

    def _get_settings(self):
        """Lusta alapértelmezés — a `controller.py` mintájára."""
        if self._settings is None:
            self._settings = QSettings("PicasaPy", "PicasaPy")
        return self._settings

    def _get_ftp_accounts(self) -> FtpAccountStore:
        if self._ftp_account_store is None:
            self._ftp_account_store = FtpAccountStore(self._get_settings())
        return self._ftp_account_store

    @Slot(result=list)
    def ftpAccounts(self) -> list[dict]:  # noqa: N802
        """A felületnek csak nem titkos fiókmezőket ad vissza."""
        return [
            {
                "id": account.account_id,
                "name": account.name,
                "domain": account.domain,
                "user": account.user,
                "root": account.root,
            }
            for account in self._get_ftp_accounts().list_accounts()
        ]

    @Slot(result=str)
    def selectedFtpAccountId(self) -> str:  # noqa: N802
        account = self._get_ftp_accounts().selected_account()
        return account.account_id if account else ""

    @Slot(str, result="QVariantMap")
    def ftpAccount(self, account_id: str) -> dict:  # noqa: N802
        account = next(
            (
                item
                for item in self._get_ftp_accounts().list_accounts()
                if item.account_id == account_id
            ),
            None,
        )
        if account is None:
            return {}
        return {
            "id": account.account_id,
            "name": account.name,
            "domain": account.domain,
            "user": account.user,
            "root": account.root,
        }

    @Slot(str, str, str, str, str, str, result="QVariantMap")
    def saveFtpAccount(
        self,
        account_id: str,
        name: str,
        domain: str,
        user: str,
        root: str,
        password: str,
    ) -> dict:  # noqa: N802
        try:
            account = self._get_ftp_accounts().save_account(
                account_id=account_id,
                name=name,
                domain=domain,
                user=user,
                root=root,
                password=password,
            )
            return {"ok": True, "id": account.account_id, "name": account.name}
        except ValueError as error:
            return {"ok": False, "error": self.tr(str(error))}
        except Exception:  # noqa: BLE001 — a kulcstár hibája nem részletezhető
            return {
                "ok": False,
                "error": self.tr("The system key store is unavailable."),
            }

    @Slot(str, result=bool)
    def selectFtpAccount(self, account_id: str) -> bool:  # noqa: N802
        try:
            self._get_ftp_accounts().select_account(account_id)
        except ValueError:
            return False
        return True

    @Slot(str, result=bool)
    def deleteFtpAccount(self, account_id: str) -> bool:  # noqa: N802
        try:
            self._get_ftp_accounts().delete_account(account_id)
        except Exception:  # noqa: BLE001 — a kulcstár hibája esetén ne hamisítsunk sikert
            return False
        return True

    @Slot(result="QVariantMap")
    def webExportPrefs(self) -> dict:  # noqa: N802
        r"""A webexport megőrzött beállításai (#4610, #5714).

        Az eredeti a `Preferences\WebExportSize` (alap 3 → 640 képpont) és a
        `WebExportMovie` (alap 0 → „Első képkocka") kulcsból indul
        (`0x007f5310`, `0x007f5355`); a célmappát és sablont a
        `WebExportPath`/`WebExportTemplate` tárolja (`0x007f52b0`). A hibás
        méretérték az alapra esik, hiányzó sablonnál a QML a 0. indexet adja."""
        settings = self._get_settings()
        return {
            "sizeIndex": _size_index(settings.value(SIZE_SETTINGS_KEY)),
            "movieFull": _truthy(settings.value(MOVIE_FULL_SETTINGS_KEY)),
            "targetDir": str(settings.value(WEB_EXPORT_TARGET_SETTINGS_KEY) or ""),
            "templateId": str(settings.value(WEB_EXPORT_TEMPLATE_SETTINGS_KEY) or ""),
        }

    def exportRunning(self) -> bool:
        """Fut-e éppen exportáló háttérszál? (a mixin nyilvántartásán át)."""
        return self.backgroundWorkersRunning()

    def waitForExport(self, timeout_s: float = 30.0) -> bool:
        """Megvárja a futó exportáló szál leállását; `True`, ha nincs (már)
        futó szál.

        A szál `daemon`, ezért az interpreter leépítése nem várja meg: ha a
        processz úgy ér véget, hogy a szál még Qt-jelzést emitál egy közben
        felszámolt objektumnak, a futás SIGSEGV-vel omlik össze (#430, a
        #53-as Qt/GIL-osztály rokona). Aki a controller élettartamát zárja
        (teszt-fixture, alkalmazás-kilépés), ezt hívja."""
        return self.waitForBackgroundWorkers(timeout_s)

    @Slot(result=list)
    def listWebExportTemplates(self) -> list[dict]:
        """A telepített sablonok a választó-lenyílóhoz: `[{"id","name",
        "description"}, ...]` (a `webexport.fen` "sablon-lista" mezője)."""
        #: #534: a `preview` a sablon előnézeti rajzának `file://` URL-je
        #: (üres sztring, ha a sablonhoz nincs rajz) — a QML `Image.source`
        #: URL-t vár, nem fájlútvonalat.
        from PySide6.QtCore import QUrl

        return [
            {
                "id": info.id,
                "name": info.name,
                "description": info.description,
                "preview": (
                    QUrl.fromLocalFile(str(info.preview_path)).toString()
                    if info.preview_path is not None
                    else ""
                ),
            }
            for info in list_templates()
        ]

    #: Nem Windows platformon az alapértelmezett célmappa neve (#534).
    HTML_EXPORT_MAPPA = "Picasa HTML exportok"

    @Slot(result=str)
    def defaultWebExportTarget(self) -> str:  # noqa: N802
        """A javasolt célmappa a párbeszéd megnyitásakor (#534, #5714).

        Windowson az eredeti Picasa a `Personal` (Qt:
        `DocumentsLocation`) mappa alá írja a `Picasa HTML Exports` mappát.
        Más platformon megmarad a rendszer képmappája és a meglévő
        honosított mappanév. Egyik útvonalat sem hozzuk létre; azt az export
        teszi, ha tényleg elindul."""
        if _platform() == "win32":
            personal = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )
            return (
                str(Path(personal) / "Picasa HTML Exports") if personal else ""
            )

        from .collage_output import pictures_dir

        return str(pictures_dir() / self.HTML_EXPORT_MAPPA)

    @Slot(str, str, str, int, bool)
    def generateWebExport(
        self,
        target_dir: str,
        template_id: str,
        album_name: str,
        size_index: int,
        movie_full: bool,
    ) -> None:
        """A webexport indítása HÁTTÉRSZÁLON. `album_name` a cím-mező
        (`webexport.fen` "edit") tartalma — a generált oldalak
        `<%albumName%>`-je ez lesz.

        #4610 (spec `picasa-menu-parancsok-viselkedes.md` 6.1): `size_index`
        a `webexport.fen` EGYETLEN méretválasztójának indexe (`SIZE_CHOICES`,
        a nagy kép mérete); a bélyegkép méretét a sablon adja (hiányában
        144). `movie_full`: „Teljes mozgófilm" (True) / „Első képkocka".
        Az árnyékolás (`shadowedThumbnails`, alapérték 1;
        `shadowedImages`, alapérték 0) nem a párbeszédből jön: a sablon
        `define`-ja adja, hiányában az alapérték (#4849).
        Mindkettő megmarad a következő megnyitásig, de csak elinduló
        exportnál — az eredeti is az elfogadáskor ment.

        #1539: célzott index-újraolvasás SZÁNDÉKOSAN nincs. A kimenet egy
        WEBOLDAL (HTML + `thumbnail/` és `image/` segédmappák), amit a
        felhasználó böngészőben vagy feltöltve néz meg — nem a PicasaPy
        rácsán. A generált méretezett példányokat beindexelni kifejezetten
        káros volna: ugyanaz a kép jelenne meg többször, két külön
        felbontásban."""
        target = to_local_path(target_dir)
        if not target:
            self.webExportFailed.emit(self.tr("Choose a target folder first."))
            return
        template = next(
            (info for info in list_templates() if info.id == template_id), None
        )
        if template is None:
            self.webExportFailed.emit(
                self.tr("Unknown web export template: %1").replace("%1", template_id)
            )
            return
        try:
            photos = tuple(self._photo_source())
        except Exception as error:  # noqa: BLE001 — a hívó forrás hibája se ölje meg csendben
            self.webExportFailed.emit(str(error))
            return
        if not photos:
            self.webExportFailed.emit(self.tr("No pictures to export."))
            return
        # #459: lemezhely-ellenőrzés ELŐRE — a forrásfájlok teljes méretét
        # vetjük össze a céllal, hogy a generálás NE induljon el félbehagyva.
        required = required_bytes_for(
            Path(photo.folder_path) / photo.name for photo in photos
        )
        if not has_enough_free_space(Path(target), required):
            self.webExportFailed.emit(self.tr(
                "Sorry, there is not enough free disk space to safely "
                "download pictures."
            ))
            return

        settings = settings_for_template(
            template.path,
            image_size_for_index(_size_index(size_index)),
            WebExportSettings(movie_full=bool(movie_full)),
        )
        self._remember_choice(size_index, movie_full, target, template.id)
        self.webExportStarted.emit()
        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        # — a busy-bejelentkezés is ITT, a mixinben történik automatikusan
        self._start_background(
            self._run_export,
            args=(Path(target), template.path, photos, album_name, settings),
            name="picasapy-webexport",
        )

    @Slot(str, str, str, int, bool)
    def publishWebExport(
        self,
        account_id: str,
        template_id: str,
        album_name: str,
        size_index: int,
        movie_full: bool,
    ) -> None:  # noqa: N802
        """Helyi, ideiglenes galériát készít, majd a teljes fájlfát feltölti."""
        store = self._get_ftp_accounts()
        account = next(
            (item for item in store.list_accounts() if item.account_id == account_id),
            None,
        )
        if account is None:
            self.webExportFailed.emit(self.tr("Choose an FTP account first."))
            return
        try:
            password = store.password_for(account.account_id)
        except Exception:  # noqa: BLE001 — a kulcstár nem elérhető
            self.webExportFailed.emit(self.tr("The system key store is unavailable."))
            return
        if not password:
            self.webExportFailed.emit(self.tr("The saved FTP password is unavailable."))
            return
        template = next(
            (info for info in list_templates() if info.id == template_id), None
        )
        if template is None:
            self.webExportFailed.emit(
                self.tr("Unknown web export template: %1").replace("%1", template_id)
            )
            return
        try:
            photos = tuple(self._photo_source())
        except Exception as error:  # noqa: BLE001 — a hívó forrás hibája
            self.webExportFailed.emit(str(error))
            return
        if not photos:
            self.webExportFailed.emit(self.tr("No pictures to export."))
            return
        required = required_bytes_for(
            Path(photo.folder_path) / photo.name for photo in photos
        )
        if not has_enough_free_space(Path(tempfile.gettempdir()), required):
            self.webExportFailed.emit(self.tr(
                "Sorry, there is not enough free disk space to safely "
                "download pictures."
            ))
            return
        settings = settings_for_template(
            template.path,
            image_size_for_index(_size_index(size_index)),
            WebExportSettings(movie_full=bool(movie_full)),
        )
        try:
            store.select_account(account.account_id)
        except ValueError:
            self.webExportFailed.emit(self.tr("Choose an FTP account first."))
            return
        self.webExportStarted.emit()
        self._start_background(
            self._run_ftp_publish,
            args=(account, password, template.path, photos, album_name, settings),
            name="picasapy-ftp-publish",
        )

    def _remember_choice(
        self, size_index: int, movie_full: bool, target_dir: Path, template_id: str
    ) -> None:
        """A webexport választásainak megőrzése (#4610, #5714)."""
        settings = self._get_settings()
        settings.setValue(SIZE_SETTINGS_KEY, _size_index(size_index))
        settings.setValue(MOVIE_FULL_SETTINGS_KEY, bool(movie_full))
        settings.setValue(WEB_EXPORT_TARGET_SETTINGS_KEY, str(target_dir))
        settings.setValue(WEB_EXPORT_TEMPLATE_SETTINGS_KEY, template_id)

    def _run_export(
        self,
        target_dir: Path,
        template_dir: Path,
        photos: tuple[PhotoRecord, ...],
        album_name: str,
        settings: WebExportSettings,
    ) -> None:
        try:
            image_report = prepare_photo_exports(photos, target_dir, settings)
            self.webExportProgress.emit(len(image_report.photos), len(photos))
            if not image_report.photos:
                self.webExportFailed.emit(
                    self.tr("None of the selected pictures could be exported.")
                )
                return
            album = AlbumExportData(
                name=album_name or "", photos=image_report.photos
            )
            report = run_web_export(template_dir, target_dir, album, settings)
        except Exception as error:  # noqa: BLE001 — háttérszál, sose haljon el csendben
            _log.warning("webexport sikertelen: %s", error)
            self.webExportFailed.emit(str(error))
            return
        self.webExportFinished.emit(str(target_dir), len(report.output_files))

    def _run_ftp_publish(
        self,
        account: FtpAccount,
        password: str,
        template_dir: Path,
        photos: tuple[PhotoRecord, ...],
        album_name: str,
        settings: WebExportSettings,
    ) -> None:
        try:
            with tempfile.TemporaryDirectory(prefix="picasapy-ftp-") as temporary:
                target_dir = Path(temporary)
                image_report = prepare_photo_exports(photos, target_dir, settings)
                self.webExportProgress.emit(len(image_report.photos), len(photos))
                if not image_report.photos:
                    self.webExportFailed.emit(
                        self.tr("None of the selected pictures could be exported.")
                    )
                    return
                album = AlbumExportData(name=album_name or "", photos=image_report.photos)
                run_web_export(template_dir, target_dir, album, settings)
                uploaded = self._ftp_publisher.upload(target_dir, account, password)
        except Exception as error:  # noqa: BLE001 — a háttérszál hibája a felületre kerül
            _log.warning("FTP-közzététel sikertelen: %s", error)
            self.webExportFailed.emit(
                self.tr("FTP publication failed: %1").replace("%1", str(error))
            )
            return
        self.ftpPublishFinished.emit(account.name, uploaded)


def _size_index(value) -> int:
    """Tárolt/kapott méretindex ellenőrizve: hiányzó, nem szám vagy a
    táblán kívüli érték az alapra (3 → 640) esik. (A tárolt index a mi
    kulcsunk, nem az eredeti `WebExportSize` enumja, ezért a táblán kívüli
    értéket hibásnak tekintjük, és nem az eredeti 0-ra ejtését követjük.)"""
    try:
        index = int(value)
    except (TypeError, ValueError):
        return DEFAULT_SIZE_INDEX
    return index if 0 <= index < len(SIZE_CHOICES) else DEFAULT_SIZE_INDEX


def _truthy(value) -> bool:
    """A QSettings logikai értéke (INI-ben szövegként jön vissza)."""
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false")
    return bool(value)

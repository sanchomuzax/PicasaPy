"""GitHub kiadások ellenőrzése és Windows-frissítés letöltése (#6340).

SAJÁT FUNKCIÓ (#6340): az eredeti Picasa a Google külső háttérfrissítőjével
frissült; ez a PicasaPy saját, GitHub-alapú, jóváhagyásos frissítője.

A hálózati réteg szándékosan egy vékony, behelyettesíthető urllib-kliens.
Az időzítés, a verziószabályok és a SHA-256 ellenőrzés külön függvények,
hogy a működés GitHub-hozzáférés nélkül is mérhető legyen.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hmac
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import time
from collections.abc import Callable

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QTimer, Signal, Slot

from . import update_checksums as _update_checksums
from . import update_release_client as _update_release_client
from .update_checksums import SHA256SUMS_NAME, parse_sha256sums
from .update_helper import (
    KILEPESI_HATARIDO_MP,
    inditsd_a_segedet,
    utolso_inditasi_hiba,
    installation_kind,
    kenyszeritett_kilepes_ha_beragad,
    mappa_irhato,
    update_command,
)
from .update_release_client import (
    WINDOWS_ASSET_NAME,
    GitHubReleaseClient,
    ReleaseInfo,
    automatic_check_is_due,
    olvashato_jegyzet,
    release_is_newer,
)

LATEST_RELEASE_API = _update_release_client.LATEST_RELEASE_API
REPOSITORY = _update_release_client.REPOSITORY
UPDATE_API_ENV = _update_release_client.UPDATE_API_ENV
ReleaseAsset = _update_release_client.ReleaseAsset
_latest_release_api_url = _update_release_client._latest_release_api_url
_version_parts = _update_release_client._version_parts
verify_sha256 = _update_checksums.verify_sha256

logger = logging.getLogger(__name__)

AUTO_CHECK_KEY = "updates/autoCheck"
LAST_AUTO_CHECK_KEY = "updates/lastAutomaticCheckDate"
SKIPPED_VERSION_KEY = "updates/skippedVersion"
NOTIFIED_VERSION_KEY = "updates/notifiedVersion"
DEFERRED_VERSION_KEY = "updates/deferredVersion"
AUTO_CHECK_DELAY_MS = 30_000
#: #6379: futás közben ennyi időnként keres újra (6 óra)
AUTO_CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000


#: a futtató folyamat (`executable`) — modulszintű fogantyú a tesztnek (#1375)
_futtato = sys


def _platform() -> str:
    """Platformfogantyú, hogy a Windows-specifikus indítás helyettesíthető legyen."""
    return sys.platform


def _as_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "off"}
    return bool(value)


class WorkerSignals(QObject):
    finished = Signal(int, object)
    failed = Signal(int, str)
    progress = Signal(int, int, int)


class _Worker(QRunnable):
    def __init__(self, job_id: int, action: Callable[[Callable[[int, int], None]], object]) -> None:
        super().__init__()
        self.job_id = job_id
        self.action = action
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            def report_progress(received: int, total: int) -> None:
                self.signals.progress.emit(self.job_id, received, total)

            self.signals.finished.emit(self.job_id, self.action(report_progress))
        except Exception as error:  # noqa: BLE001 - háttérhiba a vezérlő jelzésén megy vissza
            self.signals.failed.emit(self.job_id, str(error))


#: A kényszerített kilépés cserélhető fogantyúja (#1375, #6383).
_azonnali_kilepes = os._exit


def _kenyszeritett_kilepes_ha_beragad(hatarido_mp: float = KILEPESI_HATARIDO_MP) -> None:
    """Ha a lezárás beragad, a folyamat a határidő után kilép (#6383).

    A frissítősegéd addig vár, amíg ez a folyamat él; egy beragadt háttérszál
    miatt a csere soha nem indulna el. A démonszálas időzítő az értelmező
    leállása közben is lefut, ezért a nem démon szálakra várakozást is
    átvágja. A rendes lezárás (index, beállítások) a határidőn belül végez."""
    kenyszeritett_kilepes_ha_beragad(
        hatarido_mp,
        azonnali_kilepes=_azonnali_kilepes,
        logger=logger,
    )


def _inditsd_a_segedet(args: list[str], *, emelt: bool) -> bool:
    """A frissítő segéd indítása; UAC-ot csak akkor kér, ha `emelt` (#6340)."""
    return inditsd_a_segedet(args, emelt=emelt, platform=_platform())


#: A `tempfile.gettempdir` modulszintű fogantyúja (#1375): a teszt EZT cserélje.
_tempdir = tempfile.gettempdir


def _seged_inditasi_helyek(install_dir: Path) -> list[Path]:
    """#6458: ahonnan a frissítősegéd indulhat, a próbálás sorrendjében.

    A testvérmappa ugyanabban a fában van, ahonnan maga a program is fut (ha
    ott futhat program, ott a segéd is); a csere a telepítési mappát
    átnevezi, ezért a segéd nem lehet annak a belsejében."""
    return [install_dir.parent / "PicasaPy-update", Path(_tempdir())]


def _masold_a_segedet(forras: Path, cel: Path) -> None:
    cel.parent.mkdir(parents=True, exist_ok=True)
    cel.write_bytes(forras.read_bytes())


#: #6436: az „Újraindítás most” legfeljebb ennyit vár a háttérmunka végére;
#: utána akkor is újraindul, ha a munka még fut (a tulajdonos gépén sosem ért véget)
UJRAINDITAS_MAX_VARAKOZAS_MS = 4000


class UpdateController(QObject):
    """Napi frissítésellenőrzés és a QML-frissítőablak állapotforrása."""

    updateAvailableChanged = Signal()
    checkingChanged = Signal()
    progressChanged = Signal()
    autoCheckEnabledChanged = Signal()
    activityChanged = Signal()
    notificationRequested = Signal()
    manualCheckFinished = Signal(bool, str)
    downloadFinished = Signal(bool, str)

    def __init__(
        self,
        current_version: str,
        *,
        settings=None,
        client: GitHubReleaseClient | None = None,
        pool: QThreadPool | None = None,
        schedule: bool = True,
        install_kind: str | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        from PySide6.QtCore import QSettings

        self._settings = settings or QSettings("PicasaPy", "PicasaPy")
        #: #6394: a „Verzió kihagyása” megszűnt; a régi kihagyást egyszer töröljük,
        #: hogy a korábban kihagyott verzió újra felkínálható legyen
        self._settings.remove(SKIPPED_VERSION_KEY)
        self._settings.sync()
        self._client = client or GitHubReleaseClient()
        self._pool = pool or QThreadPool.globalInstance()
        self._current_version = current_version.removeprefix("v")
        self._kind = install_kind or installation_kind()
        from .busy_registry import get_app_busy_registry

        self._busy_registry = get_app_busy_registry()
        self._busy_registry.activeCountChanged.connect(self.activityChanged)
        self._release: ReleaseInfo | None = None
        self._checking = False
        self._progress = 0
        self._progress_total = 0
        self._download_path: Path | None = None
        self._helper_error = ""
        from . import update_eredmeny

        #: #6458: ha az előző frissítés visszaállt, az okát egyszer kiírjuk
        self._elozo_hiba = update_eredmeny.olvasd_es_torold(
            update_eredmeny.jelzo_utvonal(), self._current_version
        )
        #: #6471: a „Frissítés kilépéskor” után a verziójelző ezt mutatja
        self._install_scheduled = False
        if self._elozo_hiba:
            logger.warning("Az előző frissítés nem sikerült (#6458): %s", self._elozo_hiba)
        self._workers: dict[int, _Worker] = {}
        self._worker_callbacks: dict[
            int, tuple[Callable[[object], None], Callable[[str], None]]
        ] = {}
        self._next_job_id = 0
        self._automatic_check_started = False
        self._download_requested = False
        self._periodic_check_timer = QTimer(self)
        self._periodic_check_timer.setInterval(AUTO_CHECK_INTERVAL_MS)
        self._periodic_check_timer.timeout.connect(self._automatic_check_if_due)
        self._restart_pending = False
        from .update_cleanup import start_startup_cleanup

        start_startup_cleanup()
        self._restart_timer = QTimer(self)
        self._restart_timer.setInterval(250)
        self._restart_timer.timeout.connect(self._restart_when_idle)
        self._test_diagnostic_timer: QTimer | None = None
        self._last_test_diagnostic = ""
        if os.environ.get("PICASAPY_UPDATE_TEST_DIAGNOSTICS") == "1":
            self._test_diagnostic_timer = QTimer(self)
            self._test_diagnostic_timer.setInterval(100)
            self._test_diagnostic_timer.timeout.connect(self._write_test_diagnostics)
            self._test_diagnostic_timer.start()
            QTimer.singleShot(0, self._write_test_diagnostics)
            if os.environ.get("PICASAPY_UPDATE_TEST_BUSY") == "1":
                # #6436: a CI-próba a letöltés után soha véget nem érő
                # háttérmunkát indít: a tulajdonos gépén az „Újraindítás most”
                # megnyomásakor ilyen futott (a jelzés munka közben rejtett)
                self.downloadFinished.connect(self._teszt_vegtelen_munka)
        if schedule:
            self.start_automatic_check()

    @Property(bool, notify=autoCheckEnabledChanged)
    def autoCheckEnabled(self) -> bool:  # noqa: N802
        return _as_bool(self._settings.value(AUTO_CHECK_KEY, True), True)

    @Slot(bool)
    def setAutoCheckEnabled(self, enabled: bool) -> None:  # noqa: N802
        enabled = bool(enabled)
        if enabled == self.autoCheckEnabled:
            return
        self._settings.setValue(AUTO_CHECK_KEY, enabled)
        self._settings.sync()
        self.autoCheckEnabledChanged.emit()

    @Property(bool, notify=updateAvailableChanged)
    def updateAvailable(self) -> bool:  # noqa: N802
        return self._release is not None

    @Property(str, notify=updateAvailableChanged)
    def availableVersion(self) -> str:  # noqa: N802
        return self._release.version if self._release else ""

    @Property(str, notify=updateAvailableChanged)
    def releaseNotes(self) -> str:  # noqa: N802
        return olvashato_jegyzet(self._release.notes) if self._release else ""

    @Property(str, notify=updateAvailableChanged)
    def releaseUrl(self) -> str:  # noqa: N802
        return self._release.url if self._release else ""

    @Property(bool, notify=updateAvailableChanged)
    def oneClickUpdateSupported(self) -> bool:  # noqa: N802
        return self._kind == "windows" and self._release is not None

    @Property(str, notify=updateAvailableChanged)
    def updateCommand(self) -> str:  # noqa: N802
        return update_command(self._kind)

    @Property(bool, notify=checkingChanged)
    def checking(self) -> bool:
        return self._checking

    @Property(int, notify=progressChanged)
    def downloadProgress(self) -> int:  # noqa: N802
        if self._progress_total <= 0:
            return 0
        return min(100, round(self._progress * 100 / self._progress_total))

    installScheduledChanged = Signal()

    @Property(bool, notify=installScheduledChanged)
    def installScheduled(self) -> bool:  # noqa: N802
        """#6471: a frissítés a program bezárásakor települ."""
        return self._install_scheduled

    @Property(str, constant=True)
    def previousUpdateFailure(self) -> str:  # noqa: N802
        """#6458: az előző, visszaállt frissítés okkódja (üres, ha nem volt ilyen)."""
        return self._elozo_hiba

    @Property(str, notify=progressChanged)
    def helperErrorDetail(self) -> str:  # noqa: N802
        """#6458: miért nem indult el a frissítősegéd (üres, ha nincs hiba)."""
        return self._helper_error

    def _set_helper_error(self, szoveg: str) -> None:
        self._helper_error = szoveg
        self.progressChanged.emit()

    @Property(str, notify=progressChanged)
    def downloadState(self) -> str:  # noqa: N802
        if self._download_path is not None:
            return "ready"
        # #6380: a kattintás pillanatától "downloading", ne csak az első adag után
        if self._download_requested or self._progress_total or self._progress:
            return "downloading"
        return "idle"

    @Property(bool, notify=activityChanged)
    def applicationBusy(self) -> bool:  # noqa: N802
        return self._busy_registry.activeCount > 0

    def _submit(
        self,
        action: Callable[[Callable[[int, int], None]], object],
        done: Callable[[object], None],
        failed: Callable[[str], None],
    ) -> None:
        self._next_job_id += 1
        job_id = self._next_job_id
        worker = _Worker(job_id, action)
        self._workers[job_id] = worker
        self._worker_callbacks[job_id] = (done, failed)
        worker_signals = worker.signals
        worker_signals.finished.connect(self._on_worker_finished)
        worker_signals.failed.connect(self._on_worker_failed)
        worker_signals.progress.connect(self._on_worker_progress)
        self._pool.start(worker)

    @Slot(int, object)
    def _on_worker_finished(self, job_id: int, value: object) -> None:
        self._workers.pop(job_id, None)
        callbacks = self._worker_callbacks.pop(job_id, None)
        if callbacks:
            callbacks[0](value)

    @Slot(int, str)
    def _on_worker_failed(self, job_id: int, message: str) -> None:
        self._workers.pop(job_id, None)
        callbacks = self._worker_callbacks.pop(job_id, None)
        if callbacks:
            callbacks[1](message)

    @Slot(int, int, int)
    def _on_worker_progress(self, job_id: int, received: int, total: int) -> None:
        if job_id != self._next_job_id:
            return
        self._progress, self._progress_total = received, total
        self.progressChanged.emit()

    @Slot()
    def _automatic_check_if_due(self) -> None:
        if not automatic_check_is_due(enabled=self.autoCheckEnabled):
            return
        most = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._settings.setValue(LAST_AUTO_CHECK_KEY, most)
        self._settings.sync()
        self._check_latest(manual=False)

    def start_automatic_check(self) -> None:
        """A főablak betöltése után 30 másodperccel keres, utána 6 óránként."""
        if self._automatic_check_started:
            return
        self._automatic_check_started = True
        QTimer.singleShot(AUTO_CHECK_DELAY_MS, self._automatic_check_if_due)
        self._periodic_check_timer.start()

    def _write_test_diagnostics(self) -> None:
        """A Windows-csomagpróba számára helyi QML-elemkoordinátákat ír ki.

        Kizárólag a külön, tesztben beállított környezeti jelzővel fut; az
        eredmény PID-nkénti fájlba kerül, hogy az updater által újraindított
        folyamat is külön követhető legyen.
        """
        directory = os.environ.get("PICASAPY_UPDATE_TEST_DIAGNOSTICS_DIR")
        if os.environ.get("PICASAPY_UPDATE_TEST_DIAGNOSTICS") != "1" or not directory:
            return
        try:
            from PySide6.QtCore import QPointF, QObject
            from PySide6.QtGui import QGuiApplication
            from PySide6.QtQuick import QQuickItem  # noqa: F401 - a contentItem átalakítója

            app = QGuiApplication.instance()
            if app is None:
                return
            watched_names = {
                "versionLabel",
                "updateDialog",
                "updateDialogDownloadButton",
                "updateDialogRestartButton",
                "aboutDialog",
                "initialScanContinue",
            }
            objects: list[dict[str, object]] = []
            for window in app.allWindows():
                # A QML-ben az ablakba írt elemek Qt-szülője maga az ablak, nem
                # a tartalomelem: mindkét fát be kell járni (#6383). Nem
                # Quick-ablaknak (pl. az indulóablak) nincs tartalomeleme.
                root = window.property("contentItem")
                if not isinstance(root, QObject):
                    root = None
                fak = [window.findChildren(QObject)]
                if root is not None:
                    fak.insert(0, [root, *root.findChildren(QObject)])
                bejart: dict[int, QObject] = {}
                for fa in fak:
                    for item in fa:
                        bejart.setdefault(id(item), item)
                for item in bejart.values():
                    try:
                        name = str(item.objectName() or "")
                        text = str(item.property("text") or "")
                        title = str(item.property("title") or "")
                        current_version_text = str(
                            item.property("currentVersionText") or ""
                        )
                        normalized = text.replace("&", "").strip().casefold()
                        normalized_title = title.replace("&", "").strip().casefold()
                        interesting = (
                            name in watched_names
                            or normalized in {"help", "about picasapy"}
                            or normalized_title in {"help", "about picasapy"}
                            or text.startswith("PicasaPy ")
                        )
                        if not interesting:
                            continue
                        visible_value = item.property("visible")
                        visible = (
                            bool(visible_value)
                            if visible_value is not None
                            else bool(item.isVisible())
                        )
                        rect: dict[str, float] | None = None
                        if callable(getattr(item, "mapToGlobal", None)):
                            point = item.mapToGlobal(QPointF(0, 0))
                            ratio = float(window.devicePixelRatio() or 1.0)
                            rect = {
                                "x": float(point.x()) * ratio,
                                "y": float(point.y()) * ratio,
                                "width": float(item.property("width") or 0.0) * ratio,
                                "height": float(item.property("height") or 0.0) * ratio,
                            }
                        objects.append(
                            {
                                "name": name,
                                "text": text,
                                "title": title,
                                "current_version_text": current_version_text,
                                "visible": visible,
                                "rect": rect,
                            }
                        )
                    except (AttributeError, RuntimeError, TypeError, ValueError):
                        continue
            snapshot = {
                "at": time.time(),
                "pid": os.getpid(),
                "test_mode": any(
                    option in sys.argv
                    for option in ("--onellenorzes", "--indulasellenorzes")
                ),
                "update_available": self.updateAvailable,
                "available_version": self.availableVersion,
                "download_state": self.downloadState,
                "objects": objects,
            }
            encoded = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
            if encoded == self._last_test_diagnostic:
                return
            target = Path(directory) / f"{os.getpid()}.jsonl"
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as output:
                output.write(encoded + "\n")
            self._last_test_diagnostic = encoded
        except Exception:  # noqa: BLE001 - diagnosztika nem állíthatja le az alkalmazást
            logger.debug("A frissítési tesztdiagnosztika nem írható", exc_info=True)

    @Slot()
    def checkForUpdates(self) -> None:  # noqa: N802
        """Kézi ellenőrzés, a napi automatikus korláttól függetlenül."""
        self._check_latest(manual=True)

    def _check_latest(self, *, manual: bool) -> None:
        if self._checking:
            return
        self._checking = True
        self.checkingChanged.emit()

        def completed(value: object) -> None:
            self._checking = False
            self.checkingChanged.emit()
            release = value if isinstance(value, ReleaseInfo) else None
            is_newer = bool(release and release_is_newer(release.version, self._current_version))
            if is_newer and release:
                self._release = release
                self.updateAvailableChanged.emit()
                if manual:
                    self.manualCheckFinished.emit(True, "available")
                else:
                    notified = str(self._settings.value(NOTIFIED_VERSION_KEY, "") or "")
                    if notified != release.version:
                        self._settings.setValue(NOTIFIED_VERSION_KEY, release.version)
                        self._settings.sync()
                        self.notificationRequested.emit()
            else:
                if self._release is not None:
                    self._release = None
                    self.updateAvailableChanged.emit()
                if manual:
                    self.manualCheckFinished.emit(False, "up-to-date")

        def failed(message: str) -> None:
            logger.debug("Frissítésellenőrzés nem sikerült: %s", message)
            self._checking = False
            self.checkingChanged.emit()
            if manual:
                self.manualCheckFinished.emit(False, "error")

        self._submit(lambda _progress: self._letoltheto_kiadas(), completed, failed)

    def _letoltheto_kiadas(self) -> ReleaseInfo | None:
        """A legújabb kiadás, de windowsos telepítésnél csak ha letölthető.

        #6389: a kiadási lap percekkel előbb nyilvános, mint ahogy a Package
        feltölti a windowsos csomagot; addig nem ajánljuk fel, mert a
        letöltés hibára futna. A következő keresés újra megnézi."""
        release = self._client.latest_release()
        if self._kind != "windows" or release is None:
            return release
        if release.asset(WINDOWS_ASSET_NAME) is None:
            return None
        manifest = release.asset(SHA256SUMS_NAME)
        if manifest is None:
            return None
        try:
            hashes = parse_sha256sums(self._client.download(manifest).decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            return None
        return release if WINDOWS_ASSET_NAME in hashes else None

    @Slot()
    def deferAvailableVersion(self) -> None:  # noqa: N802
        if self._release is not None:
            self._settings.setValue(DEFERRED_VERSION_KEY, self._release.version)
            self._settings.sync()

    @Slot()
    def downloadUpdate(self) -> None:  # noqa: N802
        """A Windows portable csomagot és SHA256SUMS-t háttérben ellenőrzi."""
        release = self._release
        if not release or self._kind != "windows":
            return
        archive = release.asset(WINDOWS_ASSET_NAME)
        manifest = release.asset(SHA256SUMS_NAME)
        if archive is None or manifest is None:
            self.downloadFinished.emit(False, "missing-assets")
            return
        self._progress = self._progress_total = 0
        self._download_path = None
        self._download_requested = True
        self.progressChanged.emit()

        def download(report_progress: Callable[[int, int], None]) -> Path:
            manifest_data = self._client.download(manifest)
            hashes = parse_sha256sums(manifest_data.decode("utf-8"))
            expected = hashes.get(archive.name)
            if expected is None:
                raise ValueError("A SHA256SUMS nem tartalmazza a Windows-zipet")
            folder = Path(tempfile.gettempdir()) / "picasapy-update"
            folder.mkdir(parents=True, exist_ok=True)
            destination = folder / f"PicasaPy-{release.version}.zip"
            actual = self._client.download_to(archive, destination, progress=report_progress)
            if not hmac.compare_digest(actual, expected.lower()):
                destination.unlink(missing_ok=True)
                raise ValueError("A letöltött fájl SHA-256 ujjlenyomata nem egyezik")
            return destination

        def complete(path: object) -> None:
            self._download_requested = False
            self._download_path = Path(path)
            self._progress = self._progress_total = 1
            self.progressChanged.emit()
            self.downloadFinished.emit(True, "ready")

        def failed(message: str) -> None:
            logger.warning("A frissítés letöltése nem sikerült: %s", message)
            self._download_requested = False
            self._progress = self._progress_total = 0
            self._download_path = None
            self.progressChanged.emit()
            self.downloadFinished.emit(False, "integrity-error" if "SHA-256" in message else "download-error")

        self._submit(download, complete, failed)

    @Slot(bool, result=bool)
    def installWhenExiting(self, restart_now: bool = False) -> bool:  # noqa: N802
        """Starts the bundled helper; it waits for this process to exit."""
        if self._kind != "windows" or self._download_path is None:
            return False
        if restart_now:
            from .busy_registry import get_app_busy_registry

            if get_app_busy_registry().activeCount > 0:
                self._restart_pending = True
                self._restart_hatarido = time.monotonic() + UJRAINDITAS_MAX_VARAKOZAS_MS / 1000
                self._restart_timer.start()
                return True
        return self._start_helper(restart_now)

    @Slot(bool, str)
    def _teszt_vegtelen_munka(self, sikeres: bool, _ok: str) -> None:
        if sikeres and not getattr(self, "_teszt_munka_fut", False):
            from .busy_registry import get_app_busy_registry

            self._teszt_munka_fut = True
            get_app_busy_registry().begin()

    @Slot()
    def _restart_when_idle(self) -> None:
        if not self._restart_pending:
            self._restart_timer.stop()
            return
        from .busy_registry import get_app_busy_registry

        if (
            get_app_busy_registry().activeCount > 0
            and time.monotonic() < getattr(self, "_restart_hatarido", 0.0)
        ):
            return
        if get_app_busy_registry().activeCount > 0:
            logger.warning("Újraindítás frissítéshez a még futó háttérmunka ellenére (#6436)")
        self._restart_pending = False
        self._restart_timer.stop()
        self._start_helper(True)

    def _start_helper(self, restart_now: bool) -> bool:
        exe = Path(_futtato.executable).resolve()
        helper = exe.with_name("PicasaPyUpdateHelper.exe")
        if not helper.is_file():
            self._set_helper_error(f"hiányzik: {helper.name}")
            self.downloadFinished.emit(False, "missing-helper")
            return False
        install_dir = exe.parent
        emelt = not mappa_irhato(install_dir.parent)
        hibak: list[str] = []
        from . import update_eredmeny

        # #6471: ha a segéd el sem jut a végéig, a következő indulás ebből tudja meg
        jelzo = update_eredmeny.jelzo_utvonal()
        update_eredmeny.ird_varakozik(jelzo, self.availableVersion)
        # #6458: előbb a program mellől (a telepítési mappa testvérmappájából),
        # mert céges gépen a %TEMP%-ből induló programok gyakran tiltottak
        for mappa in _seged_inditasi_helyek(install_dir):
            cel = mappa / f"PicasaPyUpdateHelper-{os.getpid()}.exe"
            try:
                _masold_a_segedet(helper, cel)
            except OSError as hiba:
                hibak.append(f"{mappa}: {hiba}")
                continue
            args = [
                str(cel),
                "--pid",
                str(os.getpid()),
                "--archive",
                str(self._download_path),
                "--install-dir",
                str(install_dir),
                "--executable",
                exe.name,
            ]
            if emelt:
                args.append("--uac-emelt")
            if _inditsd_a_segedet(args, emelt=emelt):
                self._set_helper_error("")
                break
            hibak.append(f"{mappa}: az indítás nem sikerült ({utolso_inditasi_hiba()})")
        else:
            update_eredmeny.torold(jelzo)
            self._set_helper_error("; ".join(hibak) or "ismeretlen ok")
            logger.warning("A frissítősegéd nem indult el: %s", self._helper_error)
            self.downloadFinished.emit(False, "helper-start-failed")
            return False
        if not restart_now:
            self._install_scheduled = True
            self.installScheduledChanged.emit()
        if restart_now:
            from PySide6.QtCore import QCoreApplication

            _kenyszeritett_kilepes_ha_beragad()
            QCoreApplication.quit()
        return True

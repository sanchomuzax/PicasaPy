"""GitHub kiadások ellenőrzése és Windows-frissítés letöltése (#6340).

A hálózati réteg szándékosan egy vékony, behelyettesíthető urllib-kliens.
Az időzítés, a verziószabályok és a SHA-256 ellenőrzés külön függvények,
hogy a működés GitHub-hozzáférés nélkül is mérhető legyen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import re
import sys
import tempfile
from collections.abc import Callable
from urllib.request import Request, urlopen

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QTimer, Signal, Slot

logger = logging.getLogger(__name__)

REPOSITORY = "sanchomuzax/PicasaPy"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
SHA256SUMS_NAME = "SHA256SUMS"
WINDOWS_ASSET_NAME = "PicasaPy-windows-x64.zip"
AUTO_CHECK_KEY = "updates/autoCheck"
LAST_AUTO_CHECK_KEY = "updates/lastAutomaticCheckDate"
SKIPPED_VERSION_KEY = "updates/skippedVersion"
NOTIFIED_VERSION_KEY = "updates/notifiedVersion"
DEFERRED_VERSION_KEY = "updates/deferredVersion"
AUTO_CHECK_DELAY_MS = 30_000


def _platform() -> str:
    """Platformfogantyú, hogy a Windows-specifikus indítás helyettesíthető legyen."""
    return sys.platform


@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    name: str
    download_url: str


@dataclass(frozen=True, slots=True)
class ReleaseInfo:
    version: str
    notes: str
    url: str
    assets: tuple[ReleaseAsset, ...]

    def asset(self, name: str) -> ReleaseAsset | None:
        return next((asset for asset in self.assets if asset.name == name), None)


def _version_parts(value: str) -> tuple[tuple[int, ...], int, int] | None:
    """A kiadási verzió számait és előkiadási rangját adja vissza."""
    match = re.fullmatch(
        r"v?(\d+(?:\.\d+)*)(?:(?:-|\.)?(dev|a|alpha|b|beta|rc)(?:[.-]?(\d+))?)?"
        r"(?:\+[0-9A-Za-z.-]+)?",
        value.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    numbers = tuple(int(part) for part in match.group(1).split("."))
    stage = (match.group(2) or "").lower()
    stage_rank = {"dev": 0, "a": 1, "alpha": 1, "b": 2, "beta": 2, "rc": 3}
    return numbers, stage_rank.get(stage, 4), int(match.group(3) or 0)


def release_is_newer(latest: str, current: str) -> bool:
    """Igaz, ha a latest szemantikus kiadásverziója nagyobb a futónál."""
    newest = _version_parts(latest)
    installed = _version_parts(current)
    if newest is None or installed is None:
        return False
    width = max(len(newest[0]), len(installed[0]))
    left = (*newest[0], *(0 for _ in range(width - len(newest[0]))))
    right = (*installed[0], *(0 for _ in range(width - len(installed[0]))))
    return (left, newest[1], newest[2]) > (right, installed[1], installed[2])


def automatic_check_is_due(
    last_check_date: object,
    now: datetime | None = None,
    *,
    enabled: bool = True,
) -> bool:
    """Naponta legfeljebb egyszer engedi az indulás utáni automatikus kört."""
    if not enabled:
        return False
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return str(last_check_date or "") != now.astimezone(timezone.utc).date().isoformat()


def should_offer_release(version: str, *, skipped_version: str = "") -> bool:
    """A kihagyott kiadást többé nem ajánlja fel."""
    return bool(version) and version != skipped_version


def parse_sha256sums(manifest: str) -> dict[str, str]:
    """GNU sha256sum formátumú manifesztből fájlnév → hex digest térképet ad."""
    result: dict[str, str] = {}
    for line in manifest.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
        if not match:
            raise ValueError("Érvénytelen SHA256SUMS sor")
        result[match.group(2).strip()] = match.group(1).lower()
    return result


def verify_sha256(payload: bytes, expected: str) -> bool:
    """Eltérésnél kivételt dob, hogy hibás fájl ne juthasson telepítésig."""
    actual = hashlib.sha256(payload).hexdigest()
    if not hmac.compare_digest(actual, expected.lower()):
        raise ValueError("A letöltött fájl SHA-256 ujjlenyomata nem egyezik")
    return True


class GitHubReleaseClient:
    """A GitHub Releases API és asset letöltésének behelyettesíthető kliensrétege."""

    def __init__(
        self,
        *,
        opener: Callable[..., object] | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._opener = opener or urlopen
        self.timeout = timeout

    def _read(self, url: str, *, accept: str = "application/vnd.github+json") -> bytes:
        request = Request(
            url,
            headers={"Accept": accept, "User-Agent": "PicasaPy-updater"},
        )
        with self._opener(request, timeout=self.timeout) as response:
            return response.read()

    def latest_release(self) -> ReleaseInfo:
        """A GitHub `releases/latest` végpontjáról beolvassa a kiadás adatait."""
        raw = json.loads(self._read(LATEST_RELEASE_API).decode("utf-8"))
        assets = tuple(
            ReleaseAsset(str(asset["name"]), str(asset["browser_download_url"]))
            for asset in raw.get("assets", [])
            if asset.get("name") and asset.get("browser_download_url")
        )
        tag = str(raw.get("tag_name", "")).strip()
        if not tag:
            raise ValueError("A GitHub-kiadás nem tartalmaz verziócímkét")
        return ReleaseInfo(
            version=tag.removeprefix("v"),
            notes=str(raw.get("body", "") or ""),
            url=str(raw.get("html_url", "") or f"https://github.com/{REPOSITORY}/releases/latest"),
            assets=assets,
        )

    def download(self, asset: ReleaseAsset, *, progress: Callable[[int, int], None] | None = None) -> bytes:
        """Darabokban tölti le az assetet, opcionális bájt-haladás jelzéssel."""
        request = Request(asset.download_url, headers={"User-Agent": "PicasaPy-updater"})
        chunks: list[bytes] = []
        received = 0
        with self._opener(request, timeout=self.timeout) as response:
            total = int(response.headers.get("Content-Length", "0") or 0)
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
                received += len(chunk)
                if progress:
                    progress(received, total)
        return b"".join(chunks)


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


def installation_kind(
    *,
    frozen: bool | None = None,
    platform: str | None = None,
    executable: str | None = None,
    package_path: str | Path | None = None,
) -> str:
    """A csomagfajtát futásidőben azonosítja: `windows`, `deb` vagy `pip`."""
    frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    platform = os.name if platform is None else platform
    executable = sys.executable if executable is None else executable
    if frozen and platform == "nt":
        return "windows"
    executable_path = Path(executable).resolve()
    installed_module = Path(package_path or __file__).resolve().as_posix()
    if platform != "nt" and (
        "/usr/lib/python3/dist-packages/" in installed_module
        or ("/usr/lib/python3." in installed_module and "/dist-packages/" in installed_module)
        or "/usr/lib/python3/dist-packages" in executable_path.as_posix()
        or Path("/usr/share/doc/picasapy").is_dir()
    ):
        return "deb"
    return "pip"


def update_command(kind: str) -> str:
    if kind == "deb":
        return "sudo apt update && sudo apt install --only-upgrade picasapy"
    return "python -m pip install --upgrade picasapy"


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
        self._workers: dict[int, _Worker] = {}
        self._worker_callbacks: dict[
            int, tuple[Callable[[object], None], Callable[[str], None]]
        ] = {}
        self._next_job_id = 0
        self._automatic_check_started = False
        self._restart_pending = False
        self._restart_timer = QTimer(self)
        self._restart_timer.setInterval(250)
        self._restart_timer.timeout.connect(self._restart_when_idle)
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
        return self._release.notes if self._release else ""

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

    @Property(str, notify=progressChanged)
    def downloadState(self) -> str:  # noqa: N802
        if self._download_path is not None:
            return "ready"
        if self._progress_total or self._progress:
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
        if not automatic_check_is_due(
            self._settings.value(LAST_AUTO_CHECK_KEY), enabled=self.autoCheckEnabled
        ):
            return
        today = datetime.now(timezone.utc).date().isoformat()
        self._settings.setValue(LAST_AUTO_CHECK_KEY, today)
        self._settings.sync()
        self._check_latest(manual=False)

    def start_automatic_check(self) -> None:
        """A főablak betöltése után egyszer elindítja a 30 másodperces várást."""
        if self._automatic_check_started:
            return
        self._automatic_check_started = True
        QTimer.singleShot(AUTO_CHECK_DELAY_MS, self._automatic_check_if_due)

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
            if is_newer and release and should_offer_release(
                release.version,
                skipped_version=str(self._settings.value(SKIPPED_VERSION_KEY, "") or ""),
            ):
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

        self._submit(lambda _progress: self._client.latest_release(), completed, failed)

    @Slot()
    def skipAvailableVersion(self) -> None:  # noqa: N802
        if self._release is None:
            return
        self._settings.setValue(SKIPPED_VERSION_KEY, self._release.version)
        self._settings.sync()
        self._release = None
        self.updateAvailableChanged.emit()

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
        self.progressChanged.emit()

        def download(report_progress: Callable[[int, int], None]) -> Path:
            manifest_data = self._client.download(manifest)
            hashes = parse_sha256sums(manifest_data.decode("utf-8"))
            payload = self._client.download(archive, progress=report_progress)
            expected = hashes.get(archive.name)
            if expected is None:
                raise ValueError("A SHA256SUMS nem tartalmazza a Windows-zipet")
            verify_sha256(payload, expected)
            folder = Path(tempfile.gettempdir()) / "picasapy-update"
            folder.mkdir(parents=True, exist_ok=True)
            destination = folder / f"PicasaPy-{release.version}.zip"
            destination.write_bytes(payload)
            return destination

        def complete(path: object) -> None:
            self._download_path = Path(path)
            self._progress = self._progress_total = 1
            self.progressChanged.emit()
            self.downloadFinished.emit(True, "ready")

        def failed(message: str) -> None:
            logger.warning("A frissítés letöltése nem sikerült: %s", message)
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
                self._restart_timer.start()
                return True
        return self._start_helper(restart_now)

    @Slot()
    def _restart_when_idle(self) -> None:
        if not self._restart_pending:
            self._restart_timer.stop()
            return
        from .busy_registry import get_app_busy_registry

        if get_app_busy_registry().activeCount > 0:
            return
        self._restart_pending = False
        self._restart_timer.stop()
        self._start_helper(True)

    def _start_helper(self, restart_now: bool) -> bool:
        helper = Path(sys.executable).resolve().with_name("PicasaPyUpdateHelper.exe")
        if not helper.is_file():
            self.downloadFinished.emit(False, "missing-helper")
            return False
        copied = Path(tempfile.gettempdir()) / f"PicasaPyUpdateHelper-{os.getpid()}.exe"
        copied.write_bytes(helper.read_bytes())
        install_dir = Path(sys.executable).resolve().parent
        args = [
            str(copied),
            "--pid",
            str(os.getpid()),
            "--archive",
            str(self._download_path),
            "--install-dir",
            str(install_dir),
            "--executable",
            Path(sys.executable).name,
        ]
        if _platform() == "win32":
            import ctypes
            import subprocess

            params = subprocess.list2cmdline(args[1:])
            result = ctypes.windll.shell32.ShellExecuteW(None, "runas", str(copied), params, None, 0)
            if result <= 32:
                return False
        else:
            import subprocess

            subprocess.Popen(args, close_fds=True)
        if restart_now:
            from PySide6.QtCore import QCoreApplication

            QCoreApplication.quit()
        return True

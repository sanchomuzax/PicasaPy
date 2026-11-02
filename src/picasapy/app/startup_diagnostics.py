"""Indulási napló és PySide6-verziójelzés (#4687)."""

from __future__ import annotations

import faulthandler
import os
import re
import socket
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_PYSIDE6_MAX_MINOR = 12
_VERSION_PREFIX = re.compile(r"^\s*(\d+)\.(\d+)(?:\.|$)")
_thread = threading.Thread


def _platform(platform: str = sys.platform) -> str:
    """A platform-ellenőrzés egyetlen tesztelhető fogantyúja (#1217)."""
    return platform


def pyside6_is_supported(version: str) -> bool:
    """A projekt függőségi korlátja szerint PySide6 < 6.12 támogatott."""
    match = _VERSION_PREFIX.match(str(version))
    if match is None:
        return False
    major, minor = (int(part) for part in match.groups())
    return major == 6 and minor < _PYSIDE6_MAX_MINOR


def runtime_version_messages(pyside6_version: str, qt_version: str) -> tuple[str, ...]:
    """A konzolon és a hibanaplóban megjelenő verzióüzenetek."""
    messages = [
        f"PicasaPy futtatókörnyezet: PySide6 {pyside6_version}; Qt {qt_version}."
    ]
    if not pyside6_is_supported(pyside6_version):
        messages.append(
            "Nem támogatott PySide6-verzió. A PicasaPy PySide6 <6.12 "
            "verzióval használható; telepítsd a támogatott csomagot ezzel: "
            'python -m pip install "PySide6<6.12", majd indítsd újra a programot.'
        )
    return tuple(messages)


def process_age_ms(platform: str = sys.platform) -> int | None:
    """A folyamat létrehozása óta eltelt idő ezredmásodpercben (#6344).

    A hibanapló első saját jelzése a Python-modulok betöltése UTÁN
    születik; ami előtte történt (a PyInstaller-indító, a DLL-ek betöltése
    és a víruskereső vizsgálata), az eddig sehol nem látszott. Windowson a
    `GetProcessTimes`, Linuxon a `/proc` adja; ahol egyik sincs, `None`.
    Diagnosztika: semmilyen hibával nem dobhat."""
    try:
        if platform == "win32":
            return _windows_process_age_ms()
        if platform.startswith("linux"):
            return _linux_process_age_ms()
    except Exception:  # noqa: BLE001 — diagnosztika: az indulást SOHA nem akadályozhatja
        return None
    return None


def _windows_process_age_ms() -> int | None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32")
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    # ⚠️ argtypes NÉLKÜL a 64 bites ál-leíró (-1) C `int`-ként menne át, és
    # `ctypes.ArgumentError`-ral elszállna — mérve a windowsos CI-n: a
    # csomagolt program hibaablakkal állt meg.
    kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [
        ctypes.POINTER(wintypes.FILETIME)
    ] * 4
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.GetSystemTimeAsFileTime.argtypes = [ctypes.POINTER(wintypes.FILETIME)]
    creation, exited, kernel, user, now = (wintypes.FILETIME() for _ in range(5))
    if not kernel32.GetProcessTimes(
        kernel32.GetCurrentProcess(),
        ctypes.byref(creation),
        ctypes.byref(exited),
        ctypes.byref(kernel),
        ctypes.byref(user),
    ):
        return None
    kernel32.GetSystemTimeAsFileTime(ctypes.byref(now))

    def ticks(filetime) -> int:
        return (filetime.dwHighDateTime << 32) | filetime.dwLowDateTime

    return (ticks(now) - ticks(creation)) // 10_000


def _linux_process_age_ms() -> int:
    import os

    fields = Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()
    started = int(fields[19]) / os.sysconf("SC_CLK_TCK")
    uptime = float(Path("/proc/uptime").read_text().split()[0])
    return max(0, round((uptime - started) * 1000))


def write_console(message: str, *, error: bool = False) -> None:
    """Üzenet kiírása, ha a platform a folyamatnak konzolt adott."""
    stream = sys.stderr if error else sys.stdout
    if stream is None:
        return
    try:
        print(message, file=stream, flush=True)
    except (OSError, UnicodeError):
        # GUI-csomagban hiányozhat a konzol, vagy megszűnhet a cső.
        return


@dataclass(frozen=True)
class _MultimediaDeviceSnapshot:
    """Qt multimédia-eszközök száma és a ténylegesen betöltött háttér neve."""

    video_input_count: int | None
    audio_input_count: int | None
    backend_name: str


def _multimedia_backend_name(messages: list[str] | tuple[str, ...]) -> str:
    """A Qt qt.multimedia.plugin naplójából kivett betöltött háttérnév."""
    backend = "ismeretlen"
    for message in messages:
        match = re.search(
            r'Loading media backend\s+["\']?([A-Za-z0-9_.-]+)',
            str(message),
            re.IGNORECASE,
        )
        if match is not None:
            backend = match.group(1)
    return backend


def _multimedia_device_summary(snapshot: _MultimediaDeviceSnapshot) -> str:
    """Eszköznevek nélkül adja meg a bemenetek számát és a Qt-hátteret."""
    video_count = (
        str(snapshot.video_input_count)
        if snapshot.video_input_count is not None
        else "nem mérhető"
    )
    audio_count = (
        str(snapshot.audio_input_count)
        if snapshot.audio_input_count is not None
        else "nem mérhető"
    )
    return (
        "Qt multimédia: "
        f"videóbemenetek={video_count}; "
        f"hangbemenetek={audio_count}; "
        f"háttér={snapshot.backend_name}"
    )


def _linux_audio_service_available() -> bool:
    """Kerülje el a PulseAudio-hívás több másodperces várakozását socket nélkül.

    Mérés: a helyi, hangszolgáltatás nélküli környezetben a közvetlen
    QMediaDevices.audioInputs() 8 másodperc alatt sem tért vissza (#6390).
    """
    if not _platform().startswith("linux") or os.environ.get("PULSE_SERVER"):
        return True

    runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    for relative_path in ("pipewire-0", "pulse/native"):
        path = runtime_dir / relative_path
        if not path.exists():
            continue
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(0.1)
        try:
            if client.connect_ex(str(path)) == 0:
                return True
        except OSError:
            continue
        finally:
            client.close()
    return False


def _multimedia_device_snapshot() -> _MultimediaDeviceSnapshot:
    """Felsorolja a Qt bemeneteit, és a plugin naplójából azonosítja a hátteret.

    A Qt nyilvános API-ja nem adja vissza a backend nevét. A Qt által
    dokumentált qt.multimedia.plugin naplókategória betöltési sorát olvassuk,
    és csak a bemenetek darabszámát írjuk tovább.
    """
    logging_category = None
    old_filter_rules = None
    old_handler = None
    handler_installed = False
    backend_messages: list[str] = []
    video_count: int | None = None
    audio_count: int | None = None

    try:
        from PySide6.QtCore import (
            QLoggingCategory,
            qFormatLogMessage,
            qInstallMessageHandler,
        )
        from PySide6.QtMultimedia import QMediaDevices

        logging_category = QLoggingCategory
        old_filter_rules = os.environ.get("QT_LOGGING_RULES", "")

        def receive_qt_message(message_type, context, message: str) -> None:
            category_name = getattr(context, "category", "")
            if str(category_name).startswith("qt.multimedia"):
                if category_name == "qt.multimedia.plugin":
                    backend_messages.append(str(message))
                return
            if old_handler is not None:
                old_handler(message_type, context, message)
                return
            stream = sys.stderr
            if stream is not None:
                try:
                    print(qFormatLogMessage(message_type, context, message), file=stream)
                except (OSError, UnicodeError):
                    pass

        old_handler = qInstallMessageHandler(receive_qt_message)
        handler_installed = True
        rules = old_filter_rules.strip()
        if rules:
            rules += ";"
        logging_category.setFilterRules(rules + "qt.multimedia.plugin.debug=true")

        video_count = len(QMediaDevices.videoInputs())
        if _linux_audio_service_available():
            audio_count = len(QMediaDevices.audioInputs())
    except Exception as error:  # noqa: BLE001 - diagnosztika nem állíthatja meg az indulást
        import logging

        logging.getLogger("picasapy.startup").warning(
            "Qt multimédia-eszközfelsorolás nem sikerült (%s)", type(error).__name__
        )
    finally:
        if logging_category is not None and old_filter_rules is not None:
            try:
                logging_category.setFilterRules(old_filter_rules)
            except Exception:  # noqa: BLE001 - diagnosztikai takarítás
                pass
        if handler_installed:
            try:
                qInstallMessageHandler(old_handler)
            except Exception:  # noqa: BLE001 - diagnosztikai takarítás
                pass

    return _MultimediaDeviceSnapshot(
        video_input_count=video_count,
        audio_input_count=audio_count,
        backend_name=_multimedia_backend_name(backend_messages),
    )


def _log_multimedia_device_diagnostics(
    progress_log: StartupProgressLog,
) -> _MultimediaDeviceSnapshot:
    """Az eszközszámokat és az üres kamerabemenet lehetséges okait naplózza."""
    snapshot = _multimedia_device_snapshot()
    progress_log.mark(_multimedia_device_summary(snapshot))
    if snapshot.video_input_count == 0:
        if _platform().startswith("win"):
            progress_log.mark(
                "A Qt nem talált kamerabemenetet; ellenőrizd a Windows "
                "kamera-adatvédelmi hozzáférését, és hogy másik program nem "
                "használja-e a kamerát."
            )
        else:
            progress_log.mark(
                "A Qt nem talált kamerabemenetet; ellenőrizd a kamera "
                "csatlakozását, és hogy másik program nem használja-e."
            )
    elif snapshot.video_input_count is None:
        progress_log.mark("A Qt kamerabemenet-felsorolása nem sikerült.")
    return snapshot


def _schedule_multimedia_device_diagnostics(
    progress_log: StartupProgressLog,
) -> None:
    """Az első főablak-képkocka után, késleltetve és háttérszálon mérjen."""
    from PySide6.QtCore import QTimer

    def start_worker() -> None:
        _thread(
            target=_log_multimedia_device_diagnostics,
            args=(progress_log,),
            name="multimedia-device-diagnostics",
            daemon=True,
        ).start()

    QTimer.singleShot(2000, start_worker)


class StartupProgressLog:
    """Időbélyeges indulási jelzések, a hibanapló elérhetővé válása előtt is.

    A korai szakaszokat memóriában tartja, majd az `install()` után kiírja
    őket az `errorlog.txt`-be. A későbbi jelzések azonnal bekerülnek; az
    írási hiba nem akadályozhatja meg az alkalmazás indulását.
    """

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or (lambda: datetime.now().astimezone())
        self._path: Path | None = None
        self._history: list[str] = []
        self._written_count = 0
        self._lock = threading.Lock()
        self._write_failure_reported = False

    def mark(self, stage: str) -> None:
        """Egy statikus, személyes útvonalat nem tartalmazó szakaszt rögzít."""
        with self._lock:
            timestamp = self._now().isoformat(timespec="milliseconds")
            clean_stage = " ".join(str(stage).splitlines())
            line = f"{timestamp} INFO picasapy.startup: {clean_stage}\n"
            self._history.append(line)
            self._flush()

    def install(self, path: str | Path) -> None:
        """A megadott hibanaplóra irányít, és kiírja a korábbi szakaszokat."""
        with self._lock:
            new_path = Path(path)
            if new_path != self._path:
                self._path = new_path
                self._written_count = 0
            self._flush()

    def _flush(self) -> None:
        if self._path is None or self._written_count >= len(self._history):
            return
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8", newline="") as log:
                log.writelines(self._history[self._written_count :])
            self._written_count = len(self._history)
        except OSError as error:
            if not self._write_failure_reported:
                write_console(f"Az indulási szakasznapló nem írható: {error}", error=True)
                self._write_failure_reported = True


class StartupRunLog:
    """A futás teljes idejére nyitva tartott, rotáló indulási napló."""

    def __init__(self, directory: str | Path) -> None:
        self.path = Path(directory) / "indulas-utolso.txt"
        self.previous_path = Path(directory) / "indulas-elozo.txt"
        self._started = time.perf_counter()
        self._lock = threading.Lock()
        self._file = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                self.path.replace(self.previous_path)
            self._file = self.path.open("w", encoding="utf-8", buffering=1)
        except OSError:
            self._file = None

    @property
    def file(self):
        """A faulthandler számára használható, nyitott fájlobjektum."""
        return self._file

    def mark(self, stage: str) -> None:
        """Rögzít egy statikus indulási lépést és a kezdettől eltelt időt."""
        clean_stage = " ".join(str(stage).splitlines())
        elapsed_ms = (time.perf_counter() - self._started) * 1000.0
        self.write(f"{elapsed_ms:10.1f} ms  {clean_stage}\n")

    def write(self, text: str) -> None:
        """Szöveget fűz a naplóhoz; fájlhiba esetén nem állítja meg az appot."""
        if self._file is None:
            return
        try:
            with self._lock:
                self._file.write(text)
                self._file.flush()
        except (OSError, UnicodeError):
            return

    def close(self) -> None:
        """A teszt és a rendezett kilépés számára lezárja a fájlt."""
        if self._file is None:
            return
        try:
            self._file.flush()
            self._file.close()
        except OSError:
            pass
        self._file = None


class StartupHangTraceback:
    """Két, 15 másodperces késleltetésű veremkiírás, első képkockáig."""

    def __init__(
        self,
        file,
        *,
        dump_later=faulthandler.dump_traceback_later,
        cancel_dump=faulthandler.cancel_dump_traceback_later,
        timer_factory=threading.Timer,
    ) -> None:
        self._file = file
        self._dump_later = dump_later
        self._cancel_dump = cancel_dump
        self._timer_factory = timer_factory
        self._lock = threading.Lock()
        self._active = file is not None
        self._timer = None
        if not self._active:
            return
        try:
            self._dump_later(15, repeat=False, file=self._file)
            self._timer = self._timer_factory(15, self._arm_second_dump)
            self._timer.daemon = True
            self._timer.start()
        except Exception:  # noqa: BLE001 - a diagnosztika nem akadályozhatja az indulást
            self.cancel()

    def _arm_second_dump(self) -> None:
        with self._lock:
            if not self._active:
                return
            try:
                self._dump_later(15, repeat=False, file=self._file)
            except Exception:  # noqa: BLE001 - a diagnosztika nem akadályozhatja az indulást
                return

    def cancel(self) -> None:
        """A főablak első képkockáján leállítja mindkét időzítést."""
        with self._lock:
            was_active = self._active
            self._active = False
            timer = self._timer
        if timer is not None:
            timer.cancel()
        if was_active:
            try:
                self._cancel_dump()
            except Exception:  # noqa: BLE001 - a diagnosztika nem akadályozhatja az indulást
                pass


__all__ = [
    "StartupHangTraceback",
    "StartupProgressLog",
    "StartupRunLog",
    "pyside6_is_supported",
    "runtime_version_messages",
    "write_console",
]

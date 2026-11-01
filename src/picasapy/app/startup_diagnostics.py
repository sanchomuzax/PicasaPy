"""Indulási napló és PySide6-verziójelzés (#4687)."""

from __future__ import annotations

import re
import sys
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

_PYSIDE6_MAX_MINOR = 12
_VERSION_PREFIX = re.compile(r"^\s*(\d+)\.(\d+)(?:\.|$)")


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


def process_age_ms() -> int | None:
    """A folyamat létrehozása óta eltelt idő ezredmásodpercben (#6344).

    A hibanapló első saját jelzése a Python-modulok betöltése UTÁN
    születik; ami előtte történt (a PyInstaller-indító, a DLL-ek betöltése
    és a víruskereső vizsgálata), az eddig sehol nem látszott. Windowson a
    `GetProcessTimes`, Linuxon a `/proc` adja; ahol egyik sincs, `None`."""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32")
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
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
        if sys.platform.startswith("linux"):
            import os

            fields = Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()
            started = int(fields[19]) / os.sysconf("SC_CLK_TCK")
            uptime = float(Path("/proc/uptime").read_text().split()[0])
            return max(0, round((uptime - started) * 1000))
    except (OSError, ValueError, IndexError, AttributeError):
        return None
    return None


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


__all__ = [
    "StartupProgressLog",
    "pyside6_is_supported",
    "runtime_version_messages",
    "write_console",
]

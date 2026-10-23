"""Print Screen-képernyőkép rögzítés (#5639).

Windows alatt a globális billentyűfigyelő a Picasa háttérbeli
`GetAsyncKeyState`-ciklusát követi. Linuxon és Wayland alatt nincs
alkalmazásfüggetlen Qt-billentyűfigyelés; ott a szolgáltatás hiba nélkül,
figyelőszál indítása nélkül marad ki.

A rögzítési cél, a névképzés és a BMP-írás külön tesztelhető, a platformos
képforrástól független művelet. A mappa `[Picasa] P2category` mezőjét kizárólag
a `picasapy.ini` API írja.
"""

from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Protocol

from PySide6.QtCore import (
    Property,
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QObject,
    QSettings,
    QThread,
    QTime,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage

from picasapy.ini.folder_category import (
    CATEGORY_KEY,
    FOLDER_SECTION,
    PROJECTS_CATEGORY,
    read_folder_category,
)
from picasapy.ini.io import load_or_empty, save_document
from picasapy.ini.names import INI_NAME

logger = logging.getLogger(__name__)


def _platform() -> str:
    """A platform olvasási fogantyúja (#1217)."""
    return sys.platform


ENABLE_SCREEN_CAP_KEY = "Preferences/EnableScreenCap"
VK_PRINT = 0x2A
VK_SNAPSHOT = 0x2C
VK_CONTROL = 0x11
VK_MENU = 0x12
POLL_INTERVAL_MS = 20


class CaptureMode(Enum):
    """A Picasa-képernyőkép három célmódja."""

    DESKTOP = "desktop"
    FOREGROUND_WINDOW = "foreground-window"
    CURSOR_WINDOW = "cursor-window"


@dataclass(frozen=True, slots=True)
class CaptureTarget:
    """Rögzítési cél; az asztalhoz nem tartozik ablakfogantyú."""

    mode: CaptureMode
    window_handle: int | None = None


def select_capture_target(
    ctrl_pressed: bool,
    alt_pressed: bool,
    *,
    foreground: int | None,
    cursor: int | None,
) -> CaptureTarget:
    """Alt esetén a kurzor alatti ablakot választja; az Alt megelőzi a Ctrl-t."""
    if alt_pressed:
        return CaptureTarget(CaptureMode.CURSOR_WINDOW, cursor)
    if ctrl_pressed:
        return CaptureTarget(CaptureMode.FOREGROUND_WINDOW, foreground)
    return CaptureTarget(CaptureMode.DESKTOP)


class CaptureSource(Protocol):
    """A képernyő és a globális billentyűállapot platformfüggő forrása."""

    supported: bool

    def is_key_down(self, virtual_key: int) -> bool: ...

    def foreground_window(self) -> int | None: ...

    def cursor_window(self) -> int | None: ...

    def capture(self, target: CaptureTarget) -> QImage | None: ...

    def window_title(self, target: CaptureTarget) -> str: ...


def print_screen_pressed(source: CaptureSource) -> bool:
    """A Print Screen és Print állapotát a specifikáció szerinti sorrendben kéri."""
    return source.is_key_down(VK_SNAPSHOT) or source.is_key_down(VK_PRINT)


_INVALID_FILENAME_CHARS = frozenset('<>:"/\\|?*')


def _safe_filename_part(value: str) -> str:
    cleaned = "".join(
        "_" if ord(char) < 32 or char in _INVALID_FILENAME_CHARS else char
        for char in str(value)
    )
    return " ".join(cleaned.split()).rstrip(" .")


def _localized_date_time(when: datetime) -> str:
    """A helyi dátum-idő a rendszer locale-jának rövid alakjában.

    A Picasa specifikációja sem rögzít egyetlen alakot: a COM
    `VarBstrFromDate` a felhasználó locale-ját használja. A fájlnévben az
    operációs rendszer által érvényesnek tekintett karakterek maradnak.
    """
    value = QDateTime(
        QDate(when.year, when.month, when.day),
        QTime(when.hour, when.minute, when.second, when.microsecond // 1000),
        Qt.TimeSpec.LocalTime,
    )
    return QLocale.system().toString(value, QLocale.FormatType.ShortFormat)


def _fallback_title() -> str:
    return QCoreApplication.translate("ScreenCapture", "Fullscreen capture")


def _next_path(folder: Path, title: str, date_time_text: str) -> Path:
    safe_title = _safe_filename_part(title) or _safe_filename_part(_fallback_title())
    safe_time = _safe_filename_part(date_time_text)
    stem = f"{safe_title} {safe_time}".strip()
    candidate = folder / f"{stem}.bmp"
    if not candidate.exists():
        return candidate
    serial = 1
    while True:
        candidate = folder / f"{stem}-{serial:03d}.bmp"
        if not candidate.exists():
            return candidate
        serial += 1


def _mark_project_folder(folder: Path) -> None:
    """A projektbesorolást a meglévő `.picasa.ini` író API-val állítja be."""
    ini_path = folder / INI_NAME
    document = load_or_empty(ini_path)
    if read_folder_category(document) == PROJECTS_CATEGORY:
        return
    changed = document.with_value(FOLDER_SECTION, CATEGORY_KEY, PROJECTS_CATEGORY)
    # A videokimenet és a kollázs is az in-place IniDocument API-t használja:
    # így a létező (akár rejtett) .picasa.ini fájl identitása megmarad.
    save_document(changed, ini_path, in_place=True)


def save_screenshot(
    image: QImage,
    folder: str | Path,
    window_title: str,
    when: datetime | None = None,
    *,
    date_time_text: str | None = None,
) -> Path:
    """24 bites, tömörítetlen BMP mentése egyedi néven, és az útvonal visszaadása."""
    if image is None or image.isNull():
        raise ValueError("üres képet nem lehet képernyőképként menteni")

    target_folder = Path(folder)
    target_folder.mkdir(parents=True, exist_ok=True)
    _mark_project_folder(target_folder)

    timestamp = when or datetime.now().astimezone()
    formatted = date_time_text if date_time_text is not None else _localized_date_time(timestamp)
    prepared = image.convertToFormat(QImage.Format.Format_RGB888)
    while True:
        candidate = _next_path(target_folder, window_title, formatted)
        # Exkluzív helyfoglalás: két egyidejű Print Screen se írhassa felül
        # egymás kimenetét. A kész BMP ideiglenes fájlból kerül a végleges névre.
        try:
            with candidate.open("xb"):
                pass
        except FileExistsError:
            continue
        temporary = candidate.with_name(candidate.name + ".tmp")
        try:
            if not prepared.save(str(temporary), "BMP"):
                raise OSError(f"a BMP-írás sikertelen: {candidate}")
            os.replace(temporary, candidate)
            return candidate
        except Exception:
            temporary.unlink(missing_ok=True)
            candidate.unlink(missing_ok=True)
            raise


def capture_once(
    source: CaptureSource,
    folder: str | Path,
    *,
    ctrl_pressed: bool = False,
    alt_pressed: bool = False,
    now: datetime | None = None,
    date_time_text: str | None = None,
) -> Path | None:
    """Egy injektálható forrásból célt választ, rögzít, majd BMP-be ment."""
    foreground = source.foreground_window() if ctrl_pressed and not alt_pressed else None
    cursor = source.cursor_window() if alt_pressed else None
    target = select_capture_target(
        ctrl_pressed,
        alt_pressed,
        foreground=foreground,
        cursor=cursor,
    )
    image = source.capture(target)
    if image is None or image.isNull():
        return None
    return save_screenshot(
        image,
        folder,
        source.window_title(target),
        now,
        date_time_text=date_time_text,
    )


def screen_capture_folder(
    pictures_directory: str | Path | None = None, language: str | None = None
) -> Path:
    """A rendszer Képek/Picasa/Screen Captures (vagy honosított) mappája."""
    from .collage_output import _felulet_nyelve, pictures_dir
    from .project_folder_names import ProjectFolderKind, letezo_vagy_honos_mappa

    root = Path(pictures_directory) if pictures_directory is not None else pictures_dir()
    return letezo_vagy_honos_mappa(
        root / "Picasa",
        ProjectFolderKind.SCREEN_CAPTURES,
        language or _felulet_nyelve(),
    )


class WindowsScreenCaptureSource:
    """A Windows GDI-képforrás és `GetAsyncKeyState` billentyűlekérdező."""

    supported = _platform() == "win32"

    def __init__(self) -> None:
        if not self.supported:
            raise OSError("a globális képernyőrögzítés csak Windows alatt érhető el")

        from ctypes import wintypes

        self._wintypes = wintypes
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
        self._user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self._user32.GetAsyncKeyState.restype = ctypes.c_short
        self._user32.GetDesktopWindow.restype = wintypes.HWND
        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        self._user32.GetCursorPos.restype = wintypes.BOOL
        self._user32.WindowFromPoint.argtypes = [wintypes.POINT]
        self._user32.WindowFromPoint.restype = wintypes.HWND
        self._user32.GetWindowRect.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.RECT),
        ]
        self._user32.GetWindowRect.restype = wintypes.BOOL
        self._user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self._user32.GetWindowTextW.restype = ctypes.c_int
        self._user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        self._user32.GetSystemMetrics.restype = ctypes.c_int
        self._user32.GetDC.argtypes = [wintypes.HWND]
        self._user32.GetDC.restype = wintypes.HDC
        self._user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        self._user32.ReleaseDC.restype = ctypes.c_int
        self._gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
        self._gdi32.CreateCompatibleDC.restype = wintypes.HDC
        self._gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
        self._gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
        self._gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        self._gdi32.SelectObject.restype = wintypes.HGDIOBJ
        self._gdi32.BitBlt.argtypes = [
            wintypes.HDC,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HDC,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.DWORD,
        ]
        self._gdi32.BitBlt.restype = wintypes.BOOL
        self._gdi32.GetDIBits.argtypes = [
            wintypes.HDC,
            wintypes.HBITMAP,
            wintypes.UINT,
            wintypes.UINT,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.UINT,
        ]
        self._gdi32.GetDIBits.restype = ctypes.c_int
        self._gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        self._gdi32.DeleteObject.restype = wintypes.BOOL
        self._gdi32.DeleteDC.argtypes = [wintypes.HDC]
        self._gdi32.DeleteDC.restype = wintypes.BOOL

    def is_key_down(self, virtual_key: int) -> bool:
        # A specifikáció a `GetAsyncKeyState` 15. bitjét vizsgálja.
        return bool(self._user32.GetAsyncKeyState(int(virtual_key)) & 0x8000)

    def foreground_window(self) -> int | None:
        value = self._user32.GetForegroundWindow()
        return int(value) if value else None

    def cursor_window(self) -> int | None:
        point = self._wintypes.POINT()
        if not self._user32.GetCursorPos(ctypes.byref(point)):
            return None
        value = self._user32.WindowFromPoint(point)
        return int(value) if value else None

    def window_title(self, target: CaptureTarget) -> str:
        if target.mode is CaptureMode.DESKTOP or not target.window_handle:
            return ""
        buffer = ctypes.create_unicode_buffer(32768)
        length = self._user32.GetWindowTextW(
            self._wintypes.HWND(target.window_handle), buffer, len(buffer)
        )
        return buffer.value[:length] if length > 0 else ""

    def capture(self, target: CaptureTarget) -> QImage | None:
        from ctypes import wintypes

        hwnd = (
            self._user32.GetDesktopWindow()
            if target.mode is CaptureMode.DESKTOP
            else self._wintypes.HWND(target.window_handle or 0)
        )
        if not hwnd:
            return None
        window_rect = wintypes.RECT()
        if not self._user32.GetWindowRect(hwnd, ctypes.byref(window_rect)):
            return None

        virtual_left = self._user32.GetSystemMetrics(76)
        virtual_top = self._user32.GetSystemMetrics(77)
        virtual_right = virtual_left + self._user32.GetSystemMetrics(78)
        virtual_bottom = virtual_top + self._user32.GetSystemMetrics(79)
        left = max(int(window_rect.left), virtual_left)
        top = max(int(window_rect.top), virtual_top)
        right = min(int(window_rect.right), virtual_right)
        bottom = min(int(window_rect.bottom), virtual_bottom)
        width, height = right - left, bottom - top
        if width <= 0 or height <= 0:
            return None

        screen_dc = self._user32.GetDC(None)
        if not screen_dc:
            return None
        memory_dc = self._gdi32.CreateCompatibleDC(screen_dc)
        bitmap = self._gdi32.CreateCompatibleBitmap(screen_dc, width, height)
        if not memory_dc or not bitmap:
            if bitmap:
                self._gdi32.DeleteObject(bitmap)
            if memory_dc:
                self._gdi32.DeleteDC(memory_dc)
            self._user32.ReleaseDC(None, screen_dc)
            return None

        old_object = self._gdi32.SelectObject(memory_dc, bitmap)
        try:
            copied = self._gdi32.BitBlt(
                memory_dc,
                0,
                0,
                width,
                height,
                screen_dc,
                left,
                top,
                0x00CC0020,  # SRCCOPY
            )
            self._gdi32.SelectObject(memory_dc, old_object)
            if not copied:
                return None

            class BitmapInfoHeader(ctypes.Structure):
                _fields_ = [
                    ("biSize", wintypes.DWORD),
                    ("biWidth", wintypes.LONG),
                    ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD),
                    ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD),
                    ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG),
                    ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD),
                ]

            class RgbQuad(ctypes.Structure):
                _fields_ = [
                    ("rgbBlue", wintypes.BYTE),
                    ("rgbGreen", wintypes.BYTE),
                    ("rgbRed", wintypes.BYTE),
                    ("rgbReserved", wintypes.BYTE),
                ]

            class BitmapInfo(ctypes.Structure):
                _fields_ = [("bmiHeader", BitmapInfoHeader), ("bmiColors", RgbQuad * 1)]

            info = BitmapInfo()
            info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)
            info.bmiHeader.biWidth = width
            info.bmiHeader.biHeight = -height  # felülről lefelé kérjük a képpontokat
            info.bmiHeader.biPlanes = 1
            info.bmiHeader.biBitCount = 32
            info.bmiHeader.biCompression = 0  # BI_RGB
            info.bmiHeader.biSizeImage = width * height * 4
            pixels = ctypes.create_string_buffer(info.bmiHeader.biSizeImage)
            lines = self._gdi32.GetDIBits(
                screen_dc,
                bitmap,
                0,
                height,
                pixels,
                ctypes.byref(info),
                0,  # DIB_RGB_COLORS
            )
            if lines != height:
                return None
            return QImage(
                pixels.raw,
                width,
                height,
                width * 4,
                QImage.Format.Format_RGB32,
            ).copy()
        finally:
            self._gdi32.DeleteObject(bitmap)
            self._gdi32.DeleteDC(memory_dc)
            self._user32.ReleaseDC(None, screen_dc)


class _ScreenCaptureWorker(QThread):
    saved = Signal(str)

    def __init__(self, source: CaptureSource, folder_resolver, parent=None) -> None:
        super().__init__(parent)
        self._source = source
        self._folder_resolver = folder_resolver
        self._completion = threading.Event()

    def acknowledge(self) -> None:
        self._completion.set()

    def run(self) -> None:
        while not self.isInterruptionRequested():
            try:
                if print_screen_pressed(self._source):
                    alt_pressed = self._source.is_key_down(VK_MENU)
                    ctrl_pressed = self._source.is_key_down(VK_CONTROL)
                    target = capture_once(
                        self._source,
                        self._folder_resolver(),
                        ctrl_pressed=ctrl_pressed,
                        alt_pressed=alt_pressed,
                    )
                    if target is not None:
                        self.saved.emit(str(target))
                        # Az eredeti a főablak visszajelzésére legfeljebb
                        # 0x7d0 ms-ot vár, majd 20 ms múlva kérdez újra.
                        self._completion.wait(2.0)
                        self._completion.clear()
            except Exception:
                logger.exception("#5639: a képernyőkép rögzítése vagy mentése elbukott")
            self.msleep(POLL_INTERVAL_MS)


def _as_bool(value, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    normalized = str(value).strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


class ScreenCaptureController(QObject):
    """A preferencia és a Windowsos figyelőszál életciklusának QML-hídja."""

    screenCaptureSaved = Signal(str)
    enabledChanged = Signal()
    listeningChanged = Signal()

    def __init__(
        self,
        settings: QSettings | None = None,
        *,
        source: CaptureSource | None = None,
        folder_resolver=screen_capture_folder,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings or QSettings("PicasaPy", "PicasaPy")
        if source is None and _platform() == "win32":
            source = WindowsScreenCaptureSource()
        self._source = source
        self._folder_resolver = folder_resolver
        self._worker: _ScreenCaptureWorker | None = None
        self._enabled = _as_bool(
            self._settings.value(ENABLE_SCREEN_CAP_KEY, True), True
        )
        if self._enabled:
            self._start_listener()

    @Property(bool, notify=enabledChanged)
    def enabled(self) -> bool:
        return self._enabled

    @Property(bool, notify=listeningChanged)
    def isListening(self) -> bool:
        return bool(self._worker and self._worker.isRunning())

    @Slot(bool)
    def setEnabled(self, enabled: bool) -> None:
        value = bool(enabled)
        self._settings.setValue(ENABLE_SCREEN_CAP_KEY, value)
        if value == self._enabled:
            return
        self._enabled = value
        self.enabledChanged.emit()
        if value:
            self._start_listener()
        else:
            self._stop_listener()

    def _start_listener(self) -> None:
        if self._source is None or not getattr(self._source, "supported", False):
            # Linux/Wayland nem biztosít alkalmazásfüggetlen Qt billentyűfigyelést;
            # ilyen környezetben a funkció hibaüzenet nélkül marad ki.
            logger.debug("#5639: globális Print Screen-figyelés nem támogatott ezen a platformon")
            return
        if self._worker is not None:
            return
        worker = _ScreenCaptureWorker(
            self._source,
            self._folder_resolver,
            parent=self,
        )
        worker.saved.connect(self._worker_saved)
        self._worker = worker
        worker.start()
        self.listeningChanged.emit()

    @Slot(str)
    def _worker_saved(self, path: str) -> None:
        self.screenCaptureSaved.emit(path)
        worker = self._worker
        if worker is not None:
            worker.acknowledge()

    def _stop_listener(self) -> None:
        worker = self._worker
        if worker is None:
            return
        worker.requestInterruption()
        worker.wait()
        worker.deleteLater()
        self._worker = None
        self.listeningChanged.emit()

    @Slot()
    def shutdown(self) -> None:
        """Kilépéskor leállítja és bevárja a háttérbeli billentyűfigyelőt."""
        self._stop_listener()


__all__ = [
    "CaptureMode",
    "CaptureTarget",
    "ENABLE_SCREEN_CAP_KEY",
    "ScreenCaptureController",
    "WindowsScreenCaptureSource",
    "capture_once",
    "print_screen_pressed",
    "save_screenshot",
    "screen_capture_folder",
    "select_capture_target",
]

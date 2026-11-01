"""A QML-motor előtti, könnyű indulóablak (#6367)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import sys

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QSettings
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QPainter,
    QPixmap,
    QRasterWindow,
)

from picasapy import __version__
from .startup_diagnostics import (
    StartupHangTraceback,
    StartupProgressLog,
    StartupRunLog,
)


_NOSPLASH = "/nosplash"
_ONELLENORZES = "--onellenorzes"
_KEPERNYOVEDO = "--screensaver"
_SPLASH_MERET = QSize(420, 248)
_LOGO_MAGASSAG = 72


@dataclass
class EarlyStartup:
    """A fő alkalmazás által átveendő korai Qt-állapot."""

    argv: list[str]
    app: QGuiApplication
    splash: "IndulasAblak | None"
    qml_splash_enabled: bool
    progress_log: StartupProgressLog
    run_log: StartupRunLog | None
    hang_traceback: StartupHangTraceback | None


_EARLY_STARTUP: EarlyStartup | None = None


def _strip_nosplash(argv: list[str]) -> list[str]:
    """A régi Picasa-kapcsolót eltávolítja a Qt és az alkalmazás argumentumai közül."""
    return [argument for argument in argv if argument.casefold() != _NOSPLASH]


def _setting_bool(value: object, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().casefold() not in {"0", "false", "no", "off", "disabled"}


def _setting_value(settings, key: str, default=None):
    if hasattr(settings, "value"):
        return settings.value(key, default)
    return settings.get(key, default)


def _splash_preference_enabled(argv: list[str], settings=None) -> bool:
    if any(argument.casefold() == _NOSPLASH for argument in argv):
        return False
    if settings is None:
        settings = QSettings("PicasaPy", "PicasaPy")
    preference = _setting_value(settings, "Preferences/usesplashscreen")
    if preference is None:
        preference = _setting_value(settings, "usesplashscreen", True)
    return _setting_bool(preference)


def _splash_is_enabled(
    argv: list[str], *, platform: str | None = None, settings=None
) -> bool:
    """A képernyővédő, ellenőrző, offscreen és felhasználói kapuk kezelése."""
    if any(argument.casefold() in {_ONELLENORZES, _KEPERNYOVEDO} for argument in argv):
        return False

    qpa_platform = (platform or os.environ.get("QT_QPA_PLATFORM", "")).casefold()
    if qpa_platform.split(":", 1)[0] in {"offscreen", "minimal"}:
        return False

    return _splash_preference_enabled(argv, settings)


def _center_splash_position(available: QRect, splash_size: QSize) -> QPoint:
    """A splash bal felső pontja a képernyő munkaterületének közepén."""
    return QPoint(
        available.x() + (available.width() - splash_size.width()) // 2,
        available.y() + (available.height() - splash_size.height()) // 2,
    )


def _version_label(version: str) -> str:
    return version


def _logo_pixmap() -> QPixmap:
    assets = Path(__file__).resolve().parent / "assets"
    logo = QPixmap(str(assets / "logo.svg"))
    if logo.isNull():
        logo = QPixmap(str(assets / "icon.png"))
    return logo


def _create_splash_pixmap(version: str, *, dark: bool = False) -> QPixmap:
    """A meglévő QML-splash statikus, QML nélküli raszteres párja."""
    canvas = QColor("#232323" if dark else "#eaeaea")
    panel = QColor("#2e2e2e" if dark else "#ffffff")
    topbar = QColor("#303030" if dark else "#e2e2e2")
    border = QColor("#4a4a4a" if dark else "#cdcdcd")
    ink = QColor("#ececea" if dark else "#1c1b19")
    subdued = QColor("#b0aca4" if dark else "#5a5750")
    bar = QColor("#3c6382" if dark else "#568fb7")

    pixmap = QPixmap(_SPLASH_MERET)
    pixmap.fill(canvas)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(border)
    painter.setBrush(panel)
    painter.drawRoundedRect(QRect(0, 0, pixmap.width() - 1, pixmap.height() - 1), 6, 6)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(topbar)
    painter.drawRoundedRect(QRect(1, 1, pixmap.width() - 2, 34), 5, 5)
    painter.fillRect(QRect(1, 28, pixmap.width() - 2, 7), topbar)

    title_font = QFont()
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(ink)
    painter.drawText(QRect(8, 1, pixmap.width() - 16, 33), Qt.AlignmentFlag.AlignCenter, "PicasaPy")

    logo = _logo_pixmap()
    if not logo.isNull():
        logo = logo.scaledToHeight(_LOGO_MAGASSAG, Qt.TransformationMode.SmoothTransformation)
        logo_rect = QRect(
            (pixmap.width() - logo.width()) // 2,
            66,
            logo.width(),
            logo.height(),
        )
        if dark:
            painter.setBrush(QColor("#ffffff"))
            painter.drawRoundedRect(logo_rect.adjusted(-2, -2, 2, 2), 8, 8)
        painter.drawPixmap(logo_rect, logo)

    version_font = QFont()
    version_font.setPointSizeF(max(8.0, version_font.pointSizeF() - 1.0))
    painter.setFont(version_font)
    painter.setPen(subdued)
    painter.drawText(
        QRect(16, 160, pixmap.width() - 32, 28),
        Qt.AlignmentFlag.AlignCenter,
        _version_label(version),
    )

    painter.fillRect(QRect(1, pixmap.height() - 14, pixmap.width() - 2, 13), bar)
    painter.end()
    return pixmap


def _splash_window_flags():
    return (
        Qt.WindowType.SplashScreen
        | Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.WindowDoesNotAcceptFocus
        | Qt.WindowType.WindowTransparentForInput
    )


class IndulasAblak(QRasterWindow):
    """Keret nélküli, kattintást nem fogadó indulóablak QtWidgets nélkül.

    A program `QGuiApplication`-nel fut (ld. `print_controller.py`), ezért a
    widgetes `QSplashScreen` nem használható; ez a QtGui-s ablak csak a kész
    képet rajzolja ki."""

    def __init__(self, pixmap: QPixmap) -> None:
        super().__init__()
        self._pixmap = pixmap
        self.setFlags(_splash_window_flags())
        self.setTitle("PicasaPy startup")
        self.resize(pixmap.size())

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt-felülírás
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pixmap)
        painter.end()


def _make_splash(app: QGuiApplication, settings) -> IndulasAblak:
    dark = _setting_bool(_setting_value(settings, "view/darkTheme", False), False)
    pixmap = _create_splash_pixmap(f"v{__version__}", dark=dark)
    splash = IndulasAblak(pixmap)
    screen = app.primaryScreen()
    if screen is not None:
        splash.setPosition(_center_splash_position(screen.availableGeometry(), pixmap.size()))
    return splash


def _platform() -> str:
    """A platform cserélhető fogantyúja (#1217)."""
    return sys.platform


def _alkalmazas_elotti_beallitasok() -> None:
    """Amit a Qt-alkalmazás LÉTREHOZÁSA ELŐTT kell beállítani.

    Ugyanaz, mint az `application_startup_prepare` lépésében (ott a hívás
    ismétlése ártalmatlan): Linuxon/macOS-en a saját QML-párbeszédek (#58),
    Windowson a tálca-azonosító (#67), hogy az indulóablak már a helyes
    ikonnal és csoportosítással jelenjen meg."""
    if _platform() != "win32":
        QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PicasaPy.PicasaPy")
    except (AttributeError, OSError):
        pass


def start_early_startup(argv: list[str]) -> EarlyStartup:
    """Qt-alkalmazást és indulóablakot hoz létre az alkalmazásimport előtt."""
    global _EARLY_STARTUP

    run_log = None
    try:
        from .platform_storage import default_storage_paths

        run_log = StartupRunLog(default_storage_paths(_platform()).data)
    except Exception:  # noqa: BLE001 - a diagnosztika nem akadályozhatja az indulást
        pass
    if run_log is not None:
        run_log.mark("Korai indulás elkezdődött")
    hang_traceback = StartupHangTraceback(run_log.file if run_log is not None else None)
    if run_log is not None:
        try:
            from picasapy.perf.tesztuzem import tarolo_tipusa

            run_log.write(
                f"Tároló típusa: {tarolo_tipusa(run_log.path.parent)}\n"
            )
        except Exception:  # noqa: BLE001 - a diagnosztika nem akadályozhatja az indulást
            pass

    progress_log = StartupProgressLog()
    progress_log.mark("Qt-alkalmazás létrehozása elkezdődött")
    settings = QSettings("PicasaPy", "PicasaPy")
    qml_splash_enabled = _splash_preference_enabled(argv, settings)
    show_splash = _splash_is_enabled(argv, settings=settings)
    app = QGuiApplication.instance()
    if app is None:
        _alkalmazas_elotti_beallitasok()
        app = QGuiApplication(_strip_nosplash(argv))
    app.setApplicationName("PicasaPy")
    app.setOrganizationName("PicasaPy")
    app.setDesktopFileName("picasapy")
    app.setQuitOnLastWindowClosed(True)
    progress_log.mark("Qt-alkalmazás létrehozva")
    if run_log is not None:
        run_log.mark("Qt-alkalmazás létrehozva")

    splash = None
    if show_splash:
        splash = _make_splash(app, settings)
        splash.show()
        app.processEvents()
        progress_log.mark("Az indulóablak megjelent")
        if run_log is not None:
            run_log.mark("Az indulóablak megjelent")

    _EARLY_STARTUP = EarlyStartup(
        _strip_nosplash(argv),
        app,
        splash,
        qml_splash_enabled,
        progress_log,
        run_log,
        hang_traceback,
    )
    return _EARLY_STARTUP


def take_early_startup() -> EarlyStartup | None:
    """Átadja a belépési pont által létrehozott állapotot az alkalmazásnak."""
    global _EARLY_STARTUP
    early, _EARLY_STARTUP = _EARLY_STARTUP, None
    return early


def _close_after_first_frame(window, splash) -> None:
    """A külön ablakot az első megjelenített főablak-képkockánál bezárja."""
    if splash is None:
        return
    finished = False

    def close() -> None:
        nonlocal finished
        if finished:
            return
        finished = True
        try:
            window.frameSwapped.disconnect(close)
        except (RuntimeError, TypeError):
            pass
        splash.close()

    window.frameSwapped.connect(close)


__all__ = ["EarlyStartup", "start_early_startup", "take_early_startup"]

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
    QFontDatabase,
    QFontMetrics,
    QGuiApplication,
    QPainter,
    QPixmap,
    QRasterWindow,
    QSurfaceFormat,
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
_TARTALOM_MERET = QSize(640, 235)
_ARNYEKSAV = 14
_SPLASH_MERET = QSize(
    _TARTALOM_MERET.width() + 2 * _ARNYEKSAV,
    _TARTALOM_MERET.height() + 2 * _ARNYEKSAV,
)
_EMBLEMA_HELYE = QRect(41, 57, 123, 123)
_SZOJEL_HELYE = QRect(182, 93, 458, 52)
_SZOJEL_SZIN = QColor("#4C5B5E")
_SZOJEL_BETUCSALAD = "Open Sans"
_SZOJEL_BETUMERET = 53
_SZOJEL = "PicasaPy"
_FONT_AZONOSITO: int | None = None


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
    """A Picasa elrendezésű, témafüggetlen, QML nélküli indulókép."""
    pixmap = QPixmap(_SPLASH_MERET)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    kartya = QRect(
        _ARNYEKSAV,
        _ARNYEKSAV,
        _TARTALOM_MERET.width(),
        _TARTALOM_MERET.height(),
    )
    _draw_splash_shadow(painter, kartya)
    painter.fillRect(kartya, QColor("#ffffff"))

    logo = _logo_pixmap()
    if not logo.isNull():
        if logo.width() > logo.height() * 2:
            logo = logo.copy(QRect(0, 0, logo.height(), logo.height()))
        logo = logo.scaled(
            _EMBLEMA_HELYE.size(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(_EMBLEMA_HELYE.translated(kartya.topLeft()), logo)

    font = _splash_wordmark_font()
    metrics = QFontMetrics(font)
    text_bounds = metrics.tightBoundingRect(_SZOJEL)
    text_x = _SZOJEL_HELYE.left() - text_bounds.left()
    text_y = (
        _SZOJEL_HELYE.top()
        + (_SZOJEL_HELYE.height() - text_bounds.height()) // 2
        - text_bounds.top()
    )
    painter.setFont(font)
    painter.setPen(_SZOJEL_SZIN)
    painter.drawText(
        kartya.topLeft() + QPoint(text_x, text_y),
        _SZOJEL,
    )
    painter.end()
    return pixmap


def _draw_splash_shadow(painter: QPainter, kartya: QRect) -> None:
    """14 képpontos, finom alpha-sávot rajzol a fehér kép köré."""
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for inset in range(_ARNYEKSAV, 0, -1):
        alpha = round(26 * ((15 - inset) / _ARNYEKSAV) ** 2)
        painter.setPen(QColor(0, 0, 0, alpha))
        painter.drawRect(kartya.adjusted(-inset, -inset, inset, inset))


def _splash_wordmark_font() -> QFont:
    global _FONT_AZONOSITO
    if _FONT_AZONOSITO is None:
        font_path = Path(__file__).resolve().parent / "assets" / "fonts" / "OpenSans-Regular.ttf"
        _FONT_AZONOSITO = QFontDatabase.addApplicationFont(str(font_path))
    families = QFontDatabase.applicationFontFamilies(_FONT_AZONOSITO)
    font = QFont(families[0] if families else _SZOJEL_BETUCSALAD)
    font.setPixelSize(_SZOJEL_BETUMERET)
    return font


def _splash_window_flags():
    return (
        Qt.WindowType.SplashScreen
        | Qt.WindowType.FramelessWindowHint
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
        surface_format = QSurfaceFormat(self.format())
        surface_format.setAlphaBufferSize(8)
        self.setFormat(surface_format)
        self.setFlags(_splash_window_flags())
        # keret nélkül a cím nem látszik; a csomagmérő erről ismeri fel
        self.setTitle("PicasaPy startup")
        self.resize(pixmap.size())
        self.create()
        self._alpha_supported = self.format().alphaBufferSize() >= 8
        self.requestUpdate()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt-felülírás
        painter = QPainter(self)
        try:
            window_rect = QRect(QPoint(0, 0), self.size())
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.fillRect(window_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            if not self._alpha_supported:
                painter.fillRect(window_rect, QColor("#ffffff"))
            painter.drawPixmap(0, 0, self._pixmap)
        finally:
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


def _close_pyinstaller_splash() -> None:
    """A PyInstaller korai képét a Qt-ablak felépülése után zárja be."""
    try:
        import pyi_splash

        if pyi_splash.is_alive():
            pyi_splash.close()
    except Exception:  # noqa: BLE001 — a korai jelzés nem akadályozhatja az indulást
        return


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
    _close_pyinstaller_splash()

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

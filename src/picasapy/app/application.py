"""Alkalmazás-bootstrap: Qt, fordítások, adat-útvonalak, QML-betöltés.

Könyvtár-gyökerek: parancssori argumentumok, vagy a Picasa-paritású
~/.config/picasapy/WatchedFolders.txt (soronként egy abszolút útvonal).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import shutil
import sys

from PySide6.QtCore import QLocale, QLockFile, QTranslator
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from picasapy.scanner import read_watched_folders
from picasapy.thumbs import ThumbnailCache
from .controller import AppController
from .thumbnail_provider import ThumbnailProvider

_APP_DIR = Path(__file__).parent
_I18N_DIR = _APP_DIR / "i18n"


def _data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(base) / "picasapy"


def _cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(base) / "picasapy"


def _config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / "picasapy"


def _resolve_roots(argv: list[str]) -> tuple[str, ...]:
    if len(argv) > 1:
        return tuple(argv[1:])
    return read_watched_folders(_config_dir() / "WatchedFolders.txt")


def _acquire_instance_lock(data_dir: Path) -> QLockFile | None:
    """Egy-példányos futás: zárolófájl; ha már fut a PicasaPy, None.

    A QLockFile a PID-et is tárolja, így az összeomlott példány elavult
    zárját magától felismeri és átveszi.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(data_dir / "picasapy.lock"))
    if lock.tryLock(100):
        return lock
    return None


def _install_desktop_entry() -> None:
    """Asztali bejegyzés + ikon telepítése (~/.local/share) — Waylanden a
    tálca az app_id ↔ .desktop párosításból kapja az ikont. Idempotens."""
    base = Path(
        os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    )
    icon_target = base / "icons" / "hicolor" / "256x256" / "apps" / "picasapy.png"
    icon_source = _APP_DIR / "assets" / "icon.png"
    launcher = Path(__file__).resolve().parents[3] / "picasapy"
    exec_line = str(launcher) if launcher.exists() else "picasapy"
    desktop_text = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=PicasaPy\n"
        "Comment=Picasa-kompatibilis fotókezelő\n"
        f"Exec={exec_line} %U\n"
        "Icon=picasapy\n"
        "Terminal=false\n"
        "Categories=Graphics;Photography;Viewer;\n"
        "StartupWMClass=picasapy\n"
    )
    desktop_target = base / "applications" / "picasapy.desktop"
    try:
        if (
            not icon_target.exists()
            or icon_target.read_bytes() != icon_source.read_bytes()
        ):
            icon_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(icon_source, icon_target)
        if (
            not desktop_target.exists()
            or desktop_target.read_text(encoding="utf-8") != desktop_text
        ):
            desktop_target.parent.mkdir(parents=True, exist_ok=True)
            desktop_target.write_text(desktop_text, encoding="utf-8")
    except OSError:
        pass  # csak kényelmi funkció — hibája nem akadályozhat indulást


def _install_translator(app: QGuiApplication) -> QTranslator | None:
    language = os.environ.get("PICASAPY_LANG") or QLocale.system().name()
    translator = QTranslator(app)
    if translator.load(f"picasapy_{language.split('_')[0]}", str(_I18N_DIR)):
        app.installTranslator(translator)
        return translator
    return None


def run(argv: list[str]) -> int:
    app = QGuiApplication(argv)
    app.setApplicationName("PicasaPy")
    app.setOrganizationName("PicasaPy")
    app.setDesktopFileName("picasapy")  # Wayland app_id → tálca-ikon
    app.setWindowIcon(QIcon(str(_APP_DIR / "assets" / "icon.png")))
    _install_translator(app)

    roots = _resolve_roots(argv)
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    instance_lock = _acquire_instance_lock(data_dir)
    if instance_lock is None:
        print(
            "A PicasaPy már fut — egyszerre csak egy példány engedélyezett.",
            file=sys.stderr,
        )
        return 0
    _install_desktop_entry()

    provider = ThumbnailProvider(ThumbnailCache(_cache_dir() / "thumbs"))
    controller = AppController(data_dir / "index.db", roots, provider)

    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImportPath(str(_APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.load(str(_APP_DIR / "qml" / "Main.qml"))
    if not engine.rootObjects():
        return 1
    controller.start()
    exit_code = app.exec()
    controller.shutdown()
    return exit_code

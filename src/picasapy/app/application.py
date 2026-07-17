"""Alkalmazás-bootstrap: Qt, fordítások, adat-útvonalak, QML-betöltés.

Könyvtár-gyökerek: parancssori argumentumok, vagy a Picasa-paritású
~/.config/picasapy/WatchedFolders.txt (soronként egy abszolút útvonal).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtGui import QGuiApplication
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
    _install_translator(app)

    roots = _resolve_roots(argv)
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

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
    return app.exec()

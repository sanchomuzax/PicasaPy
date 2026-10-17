"""A `picasapy --screensaver` belépési pont (#4613).

A tétlenség-figyelő (`screensaver_idle.py`) ezt hívja: a mentett
képernyővédő-beállításokkal (források, effekt, képidő, felirat) teljes
képernyős vetítést indít a már indexelt képtárból, és bármely bevitelre
kilép. Főablakot nem nyit, a példányzárat nem veszi fel (futó PicasaPy
mellett is elindul), és az indexet csak olvasó kapcsolattal nyitja
(nem állít WAL-t, nem migrál sémát).
"""

from __future__ import annotations

import os
import sqlite3
import sys

from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .display_mode_controller import DEFAULT_DISPLAY_MODE
from .models import PhotoGridModel
from .screensaver_controller import (
    load_screensaver_slides,
    saved_effect,
    saved_seconds,
    saved_show_captions,
)
from .screensaver_idle import SCREENSAVER_FLAG

_NO_PICTURES = (
    "A képernyővédő nem indult: a kiválasztott képernyővédő-forrásokban "
    "nincs elérhető kép (vagy még nincs képtár). A forrásokat a PicasaPy "
    "Eszközök ▸ Képernyővédő konfigurálása… ablakában választhatod ki."
)


def argv_kepernyovedo(argv: list[str]) -> tuple[bool, list[str]]:
    """`(kérték-e, a kapcsoló nélküli argumentumlista)`."""
    if SCREENSAVER_FLAG not in argv:
        return False, list(argv)
    return True, [elem for elem in argv if elem != SCREENSAVER_FLAG]


class ScreensaverRunBridge(QObject):
    """A `ScreensaverWindow.qml` szűk hídja — pontosan azt adja, amit olvas."""

    finished = Signal()

    def __init__(self, slides, settings: QSettings, parent: QObject | None = None):
        super().__init__(parent)
        self._photos = PhotoGridModel(self)
        self._photos.set_display_mode(DEFAULT_DISPLAY_MODE)
        self._photos.set_photos(tuple(slides))
        self._effect = saved_effect(settings)
        self._seconds = saved_seconds(settings)
        self._captions = saved_show_captions(settings)

    @Property(QObject, constant=True)
    def photos(self):
        return self._photos

    @Property(str, constant=True)
    def effect(self) -> str:
        return self._effect

    @Property(int, constant=True)
    def seconds(self) -> int:
        return self._seconds

    @Property(bool, constant=True)
    def showCaptions(self) -> bool:  # noqa: N802
        return self._captions

    @Slot()
    def finish(self) -> None:
        self.finished.emit()

    @Slot(int, int, int, int, result="QVariantList")
    def slideshowPanZoomRectangles(  # noqa: N802 - QML metódusnév
        self,
        forras_szelesseg: int,
        forras_magassag: int,
        nezet_szelesseg: int,
        nezet_magassag: int,
    ) -> list[dict[str, float]]:
        """A külön képernyővédő-ablak ugyanazt az illesztőt használja."""
        if min(
            forras_szelesseg,
            forras_magassag,
            nezet_szelesseg,
            nezet_magassag,
        ) <= 0:
            return []
        from .slideshow_pan_zoom import qml_pan_zoom_rectangles

        return qml_pan_zoom_rectangles(
            forras_szelesseg,
            forras_magassag,
            nezet_szelesseg,
            nezet_magassag,
        )


def _settings() -> QSettings:
    return QSettings("PicasaPy", "PicasaPy")


def _saved_language(settings: QSettings) -> str:
    """A mentett nyelv CSAK OLVASVA — tétlenségkor nem nyílhat nyelvkérdés,
    és a függő nyelvválasztást a következő rendes indulás érleli be."""
    from .language_controller import LANGUAGE_KEY, coerce_language

    return coerce_language(os.environ.get("PICASAPY_LANG") or settings.value(LANGUAGE_KEY))


def _prepare(argv: list[str]):
    """Qt-alkalmazás + a mentett beállítások + a vetítendő képek."""
    from . import application as app_module

    app_module.allitsd_be_a_stilust()
    app = QGuiApplication.instance() or QGuiApplication(argv)
    app.setApplicationName("PicasaPy")
    app.setOrganizationName("PicasaPy")
    app.setDesktopFileName("picasapy")
    app_module._install_ui_font(app)
    settings = _settings()
    app_module._install_translator(app, _saved_language(settings))
    db_path = app_module._data_dir() / "index.db"
    if not db_path.is_file():
        return app, settings, ()
    try:
        slides = load_screensaver_slides(db_path, settings, app_module._resolve_roots(argv))
    except (sqlite3.DatabaseError, RuntimeError) as error:
        print(f"A képernyővédő nem tudta megnyitni a képtárat: {error}", file=sys.stderr)
        return app, settings, ()
    return app, settings, slides


def run_screensaver(argv: list[str]) -> int:
    app, settings, slides = _prepare(argv)
    if not slides:
        print(_NO_PICTURES, file=sys.stderr)
        return 1
    screensaver_run_bridge = ScreensaverRunBridge(slides, settings)
    from .application import load_screensaver_window

    engine = QQmlApplicationEngine()
    window = load_screensaver_window(engine, screensaver_run_bridge)
    if window is None:
        return 1
    screensaver_run_bridge.finished.connect(app.quit)
    return app.exec()

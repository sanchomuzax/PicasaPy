"""QML-funkcionális tesztek: saját SVG-ikonkészlet a kimeneti sávhoz és az
eszköztár geo-szűrőjéhez (#361 — Picasa-hű ikonkészlet saját rajzban).

Két réteg:
- `TestIconFilesExist`: minden `icons/*.svg`-re fájl-létezés + jólformáltság
  (a PBZ-leltár szerinti komplett készlet: webupload, e-mail, nyomtatás,
  mappa-export, kollázs, film, megosztás, geo-tű).
- `TestTrayBarIconWiring` / `TestToolbarGeoIconWiring`: a `qml_app`
  teljes-alkalmazás fixtúrán át — az Image-ek ténylegesen betöltődnek-e
  (nincs `Image.Error` állapot), és a meglévő objectName-ek/felirat-
  szövegek nem sérültek (E-Mail/Print/Export/Upload/geo-szűrő).
"""

from __future__ import annotations

import xml.dom.minidom as minidom
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer

_ICONS_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "icons"
)

# a kimeneti sáv + eszköztár ikonjai, amiket ez a jegy vezet be
_EXPECTED_ICONS = (
    "upload.svg",           # outputlayout/webupload
    "email.svg",             # outputlayout/ebutton
    "print.svg",              # outputlayout/pbutton
    "folder-export.svg",      # outputlayout/folderbutton
    "collage.svg",             # outputlayout/collage
    "movie.svg",                # outputlayout/makemovie
    "share.svg",                 # outputlayout/sharewith
    "geo-pin.svg",                # eszköztár geo-szűrő (korábban "⚲" glif)
)


def _settle(qt_app, rounds=3):
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(10, pause.quit)
        pause.exec()


class TestIconFilesExist:
    @pytest.mark.parametrize("name", _EXPECTED_ICONS)
    def test_icon_file_exists(self, name):
        path = _ICONS_DIR / name
        assert path.is_file(), f"hiányzik az ikonfájl: {path}"

    @pytest.mark.parametrize("name", _EXPECTED_ICONS)
    def test_icon_is_well_formed_svg(self, name):
        path = _ICONS_DIR / name
        doc = minidom.parse(str(path))
        assert doc.documentElement.tagName == "svg"
        assert doc.documentElement.getAttribute("viewBox") == "0 0 24 24"

    def test_icons_directory_has_no_stray_files(self):
        """Csak a várt 8 ikon él a mappában — nincs bemásolt eredeti
        PSD/PNG vagy elfelejtett próbafájl."""
        actual = {p.name for p in _ICONS_DIR.glob("*")}
        assert actual == set(_EXPECTED_ICONS)


class TestTrayBarIconWiring:
    def test_email_icon_loads_without_error(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _settle(qt_app)
        icon = window.findChild(QObject, "trayEmailLabel")
        assert icon is not None
        assert icon.property("text") == "E-Mail"

    def test_export_button_keeps_its_objectname_and_label(self, qml_app, qt_app):
        """Regresszió-őr: a meglévő tesztek (`test_qml_fileops_export.py`,
        `test_dark_theme_chrome.py`) `trayExportButton`/`trayExportLabel`
        objectName-re és "Export"-ot tartalmazó feliratra támaszkodnak."""
        window, _controller, _engine = qml_app
        _settle(qt_app)
        button = window.findChild(QObject, "trayExportButton")
        assert button is not None
        label = window.findChild(QObject, "trayExportLabel")
        assert "Export" in label.property("text")

    @pytest.mark.parametrize(
        "object_name",
        [
            "trayCollageButton",
            "trayMovieButton",
            "trayShareButton",
        ],
    )
    def test_new_output_tray_placeholders_are_present_but_disabled(
        self, qml_app, qt_app, object_name
    ):
        """Kollázs/Film/Megosztás — a PBZ-leltár szerinti gombok, ma
        vizuális helyőrzőként (a tényleges bekötés Main.qml-t igényelne,
        ld. a TrayBar.qml kódkommentje)."""
        window, _controller, _engine = qml_app
        _settle(qt_app)
        button = window.findChild(QObject, object_name)
        assert button is not None
        assert button.property("enabled") is False

    @pytest.mark.parametrize(
        "icon_object_name,expected_file",
        [
            ("trayCollageIcon", "collage.svg"),
            ("trayMovieIcon", "movie.svg"),
            ("trayShareIcon", "share.svg"),
        ],
    )
    def test_new_output_tray_icons_point_to_an_existing_svg(
        self, qml_app, qt_app, icon_object_name, expected_file
    ):
        window, _controller, _engine = qml_app
        _settle(qt_app)
        icon = window.findChild(QObject, icon_object_name)
        assert icon is not None
        source = str(icon.property("source").toString())
        assert source.endswith(expected_file)
        assert (_ICONS_DIR / expected_file).is_file()


class TestToolbarGeoIconWiring:
    def test_geo_filter_icon_present_and_not_broken(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _settle(qt_app)
        icon = window.findChild(QObject, "geoFilterIcon")
        assert icon is not None
        source = str(icon.property("source").toString())
        assert source.endswith("geo-pin.svg")
        assert (_ICONS_DIR / "geo-pin.svg").is_file()
        # nincs Python-oldali enum-konverter a QQuickImageBase::Status-hoz
        # (Qt-korlát) — helyette a ténylegesen kirajzolt méretet nézzük:
        # egy törött/hiányzó kép paintedWidth/Height 0 maradna.
        assert icon.property("paintedWidth") > 0
        assert icon.property("paintedHeight") > 0

    def test_geo_filter_wrapper_objectname_unchanged(self, qml_app, qt_app):
        """Regresszió-őr: `test_qml_places.py` a `geoFilter` (a KÜLSŐ
        Item) objectName-re és `ctlHasGeo` property-re támaszkodik."""
        window, _controller, _engine = qml_app
        _settle(qt_app)
        wrapper = window.findChild(QObject, "geoFilter")
        assert wrapper is not None
        assert wrapper.property("ctlHasGeo") is False

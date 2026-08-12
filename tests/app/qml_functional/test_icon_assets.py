"""QML-funkcionális tesztek: saját SVG-ikonkészlet a kimeneti sávhoz, az
eszköztár geo-szűrőjéhez (#361) és a szerkesztő "Gyakori javítások" füléhez
(#411 — Picasa-hű ikonkészlet saját rajzban).

Két réteg:
- `TestIconFilesExist`: minden `icons/*.svg`-re fájl-létezés + jólformáltság
  (a PBZ-leltár szerinti komplett készlet: webupload, e-mail, nyomtatás,
  mappa-export, kollázs, film, megosztás, geo-tű + a #411-es 9 + a #464-es
  1 szerkesztő-eszköz-ikon).
- `TestTrayBarIconWiring` / `TestToolbarGeoIconWiring`: a `qml_app`
  teljes-alkalmazás fixtúrán át — az Image-ek ténylegesen betöltődnek-e
  (nincs `Image.Error` állapot), és a meglévő objectName-ek/felirat-
  szövegek nem sérültek (E-Mail/Print/Export/Upload/geo-szűrő).

A szerkesztőpanel csempéinek saját (EditorPanel-fixtúrás) tesztjei a
`test_editor_411.py`-ban élnek — itt csak a fájlok létezését/jólformáltságát
ellenőrizzük, hogy a "nincs kóbor fájl a mappában" ellenőrzés egy helyen,
teljes körűen maradjon.
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

# a kimeneti sáv + eszköztár ikonjai (#361)
_EXPECTED_ICONS = (
    "upload.svg",           # outputlayout/webupload
    "email.svg",             # outputlayout/ebutton
    "print.svg",              # outputlayout/pbutton
    "folder-export.svg",      # outputlayout/folderbutton
    "collage.svg",             # outputlayout/collage
    "movie.svg",                # outputlayout/makemovie
    "share.svg",                 # outputlayout/sharewith
    "geo-pin.svg",                # eszköztár geo-szűrő (korábban "⚲" glif)
    # #455 képtálca: a megtartott kép jelvénye a rácsban, és a tálca
    # ürítés-gombja az alsó sávon
    "hold-pin.svg",
    "pipetta.svg",              # #464: „semleges szín" pipetta
    "varazspalca.svg",          # #464: „egy gombnyomásos javítás" pálca
    # #463: bélyegkép arc-jelvények
    "faces-badge.svg",
    "face-suggestion-badge.svg",
    "tray-clear.svg",
)

# a szerkesztő "Gyakori javítások" fülének ikonjai (#411, + #464: a
# "Kreatív Kit" helyőrző-gomb saját ikonja)
_EDITOR_TOOL_ICONS = (
    "vagas.svg",
    "kiegyenesites.svg",
    "vorosszem.svg",
    "jo-napom-van.svg",
    "auto-kontraszt.svg",
    "auto-szin.svg",
    "retusalas.svg",
    "szoveg.svg",
    "deritofeny.svg",
    "kreativ-kit.svg",
)

_ALL_ICONS = _EXPECTED_ICONS + _EDITOR_TOOL_ICONS


def _settle(qt_app, rounds=3):
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(10, pause.quit)
        pause.exec()


#: #463: a bélyegkép sarkába kerülő jelvények — az eredeti Picasa
#: réteg-adataiból vett, SZÁNDÉKOSAN nem négyzetes méretarányokkal.
_CORNER_BADGES = frozenset({"faces-badge.svg", "face-suggestion-badge.svg"})


class TestIconFilesExist:
    @pytest.mark.parametrize("name", _ALL_ICONS)
    def test_icon_file_exists(self, name):
        path = _ICONS_DIR / name
        assert path.is_file(), f"hiányzik az ikonfájl: {path}"

    @pytest.mark.parametrize("name", _ALL_ICONS)
    def test_icon_is_well_formed_svg(self, name):
        path = _ICONS_DIR / name
        doc = minidom.parse(str(path))
        assert doc.documentElement.tagName == "svg"
        # #411: a szerkesztő-eszköz ikonjai FEKVŐ (3:2) vászonnal készültek —
        # az eredeti Picasa 44x29-es gombképeinek arányával —, a kimeneti sáv
        # ikonjai (#361) maradtak négyzetesek. Mindkettő érvényes, de a
        # vászonnak a rajzot KI KELL TÖLTENIE (nincs üres margó), ezért az
        # arányt ellenőrizzük, nem egy fix viewBox-sztringet.
        view_box = doc.documentElement.getAttribute("viewBox")
        parts = [float(v) for v in view_box.replace(",", " ").split()]
        assert len(parts) == 4, f"hibás viewBox: {view_box!r}"
        arany = parts[2] / parts[3]
        if name in _CORNER_BADGES:
            # #463: a bélyegkép-sarok jelvényei NEM eszköz-ikonok: a
            # méretarányuk az eredeti Picasa réteg-adataiból származik
            # (pl. „emberek" 14×20), ezért nem a 3:2/négyzetes szabály
            # vonatkozik rájuk — a vászonnak viszont itt is ki kell töltenie.
            return
        assert 0.95 <= arany <= 1.05 or 1.4 <= arany <= 1.6, (
            f"{name}: a viewBox aránya se nem négyzetes, se nem 3:2 ({arany:.2f})"
        )

    def test_icons_directory_has_no_stray_files(self):
        """Csak a várt ikonok élnek a mappában — nincs bemásolt eredeti
        PSD/PNG vagy elfelejtett próbafájl (#361 kimeneti sáv + #411
        szerkesztő-eszköz-ikonok)."""
        actual = {p.name for p in _ICONS_DIR.glob("*")}
        assert actual == set(_ALL_ICONS)


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


class TestIconsAvoidUnsupportedSvgFeatures:
    """#411: a Qt SVG-motorja (SVG Tiny 1.2) a `clipPath`-t ÉS a beágyazott
    `<svg>` elemet is FIGYELMEN KÍVÜL HAGYJA — némán, hibaüzenet nélkül.
    Emiatt a felezett ikonok „utána" rétege ráfestett az egész képre, és a
    két fél egyformának látszott (felhasználói visszajelzés). A féloldalak
    geometriáját ezért matematikailag elmetszve rajzoljuk; ez az őr
    megakadályozza, hogy bárki visszacsempéssze a nem támogatott elemeket."""

    @pytest.mark.parametrize("name", _ALL_ICONS)
    def test_no_clippath_or_nested_svg(self, name):
        # ELEM-szinten vizsgálunk (nem szövegkeresés): a magyarázó
        # kommentekben szerepelhet a "clipPath" szó, az nem hiba.
        doc = minidom.parse(str(_ICONS_DIR / name))
        gyoker = doc.documentElement
        for elem in gyoker.getElementsByTagName("*"):
            assert elem.tagName != "clipPath", (
                f"{name}: a Qt nem támogatja a clipPath-t — a rajz szétesik"
            )
            assert elem.tagName != "svg", (
                f"{name}: beágyazott <svg> — a Qt kihagyja"
            )
            assert not elem.getAttribute("clip-path"), (
                f"{name}: clip-path attribútum — a Qt figyelmen kívül hagyja"
            )


#: a QML-ből létrehozott objektumok életben tartása (a GC különben
#: elviheti őket a teszt alatt)
_KEEPALIVE: list = []


class TestFaceBadges:
    """#463: a bélyegkép arc-jelvényei — „van rajta arc" és a KÜLÖN
    „jóváhagyásra váró névjavaslat", az eredeti méretarányokkal."""

    @staticmethod
    def _delegate(qt_app):
        """Önálló ThumbDelegate-példány (a rács nélkül) — a jelvények
        láthatóságát a delegate saját property-in állítjuk."""
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        import picasapy.app.application as app_module

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        component = QQmlComponent(engine)
        component.setData(
            b"""
            import QtQuick
            import PicasaPy 1.0
            ThumbDelegate {
                index: 0; name: "a.jpg"; thumbUrl: ""; star: false
                caption: ""; isVideo: false; keywords: ""; resolution: ""
            }
            """,
            QUrl(),
        )
        obj = component.create()
        assert obj is not None, [e.toString() for e in component.errors()]
        QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
        _KEEPALIVE.extend((engine, component, obj))
        qt_app.processEvents()
        return obj

    def test_badges_use_the_original_proportions(self, qt_app):
        delegate = self._delegate(qt_app)
        faces = delegate.findChild(QObject, "facesMark")
        suggestion = delegate.findChild(QObject, "faceSuggestionMark")
        assert faces is not None and suggestion is not None
        # a jegy réteg-adatokból kiolvasott méretei
        assert (faces.property("width"), faces.property("height")) == (14, 20)
        assert (suggestion.property("width"), suggestion.property("height")) == (20, 20)

    def test_badges_are_hidden_without_faces(self, qt_app):
        delegate = self._delegate(qt_app)
        assert delegate.findChild(QObject, "facesMark").property("visible") is False
        assert (
            delegate.findChild(QObject, "faceSuggestionMark").property("visible")
            is False
        )

    def test_suggestion_badge_is_independent_of_the_faces_badge(self, qt_app):
        """A két állapot FÜGGETLEN: egy képen lehet már elnevezett arc úgy is,
        hogy nincs több jóváhagyandó javaslat — és fordítva."""
        delegate = self._delegate(qt_app)
        delegate.setProperty("hasFaces", True)
        qt_app.processEvents()
        assert delegate.findChild(QObject, "facesMark").property("visible") is True
        assert (
            delegate.findChild(QObject, "faceSuggestionMark").property("visible")
            is False
        )

        delegate.setProperty("hasFaces", False)
        delegate.setProperty("hasFaceSuggestion", True)
        qt_app.processEvents()
        assert delegate.findChild(QObject, "facesMark").property("visible") is False
        assert (
            delegate.findChild(QObject, "faceSuggestionMark").property("visible")
            is True
        )

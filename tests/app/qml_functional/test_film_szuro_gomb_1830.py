"""#1830 — a „csak filmek” szűrő a keresősávon, a felületről.

Az index-oldali lekérdezést a `tests/index/test_film_szuro_1830.py` méri;
ez a fájl azt, hogy a felhasználó **el is éri**, és hogy a gomb az
állapotot tükrözi.

⚠️ A gomb aktív állapota a `viewModeName`-ből jön, NEM a `filterActive`-ból.
Az utóbbi csak azt mondja, hogy szűrünk — azt nem, hogy MIVEL: a csillag-
és a film-gomb egyszerre látszana bekapcsoltnak.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

_TOOLBAR = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/MainToolbar.qml"
)


class TestAGombMegvan:
    def test_a_szuro_zonaban_ott_a_film_gomb(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "movieFilter") is not None, (
            "nincs „csak filmek” szűrő a keresősávon (#1830)"
        )

    def test_van_hozza_buborekusgo(self):
        """`moviesearch` — az eredeti buboréksúgója."""
        assert "Show movies only" in _TOOLBAR.read_text(encoding="utf-8")


class TestAzAllapotTukrozese:
    def test_a_gomb_a_viewModeName_bol_dolgozik(self):
        forras = _TOOLBAR.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "movieFilter"')
        blokk = forras[kezdet : kezdet + 900]
        assert "viewModeName" in blokk, (
            "a film-gomb a `filterActive`-ból dolgozik — akkor a csillag-"
            "szűrő bekapcsolásakor is aktívnak látszana (#1830)"
        )

    def test_a_vezerlo_megnevezi_a_nezetet(self, qml_app, qt_app):
        _window, controller, _engine = qml_app
        assert controller.viewModeName == "folder"


class TestAVezerloUt:
    def test_a_szuro_bekapcsol_es_kikapcsol(self, qml_app, qt_app):
        _window, controller, _engine = qml_app
        controller.showVideosOnly()
        qt_app.processEvents()
        assert controller.viewModeName == "videos"

        controller.clearFilter()
        qt_app.processEvents()
        assert controller.viewModeName != "videos"

    def test_a_csillag_szuro_NEM_teszi_aktivva(self, qml_app, qt_app):
        """A két szűrő nem látszhat egyszerre bekapcsoltnak."""
        _window, controller, _engine = qml_app
        try:
            controller.showStarred()
            qt_app.processEvents()
            assert controller.viewModeName == "starred"
        finally:
            controller.clearFilter()
            qt_app.processEvents()

"""#2187 — az arc ↔ teljes kép nagyításváltó a személy-album fejlécén.

MÉRT geometria (`respack.yt`, a spec 15.5 táblája): `face_zoom` (457,4)–
(492,25) és `picture_zoom` (492,4)–(527,25), mindkettő **35 × 21**, egymás
mellett, a fejléc JOBB FELSŐ sarkában (`zoom_container`, 70 × 21). MÉRT
súgók (15.4): „View zoomed in to the face" / „View zoomed out to the full
picture".

Amit ez a fájl MÉR: a két gomb létét, méretét, egymáshoz képesti helyét, a
láthatósági feltételt, az állapotjelzést (melyik a benyomott) és azt, hogy
a kattintás a megfelelő állapotot kéri.
Amit NEM mér: hogy a rács csempéi tényleg vágódnak-e — az a vezérlő és a
szolgáltató dolga (`tests/app/test_arc_nagyitas_2187.py`).
"""

from __future__ import annotations

import picasapy.app.application as app_module
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

_KEEP_ALIVE: list = []
_ARC = "headerFaceZoomButton"
_KEP = "headerPictureZoomButton"


def _fejlec(engine, **props):
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    fejlec = comp.createWithInitialProperties(props)
    assert comp.errors() == [], comp.errors()
    assert fejlec is not None
    _KEEP_ALIVE.append(fejlec)
    return fejlec


def _gomb(fejlec, nev):
    gomb = fejlec.findChild(QObject, nev)
    assert gomb is not None, f"{nev} nem található"
    return gomb


class TestLathatosag:
    def test_mappa_fejlecen_nincs(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, folderName="Nyaralás", personName="")
        assert _gomb(fejlec, _ARC).property("visible") is False
        assert _gomb(fejlec, _KEP).property("visible") is False

    def test_szemely_albumban_latszik(self, qml_app):
        """Javaslat nélkül is: a váltó nem a javaslat-munkafolyamaté."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=0)
        assert _gomb(fejlec, _ARC).property("visible") is True
        assert _gomb(fejlec, _KEP).property("visible") is True


class TestGeometria:
    def test_a_mert_35x21(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna")
        for nev in (_ARC, _KEP):
            gomb = _gomb(fejlec, nev)
            assert gomb.property("width") == 35
            assert gomb.property("height") == 21

    def test_az_arc_all_balra_szorosan(self, qml_app):
        """MÉRT: `face_zoom` 457–492, `picture_zoom` 492–527 — hézag nélkül."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna")
        arc, kep = _gomb(fejlec, _ARC), _gomb(fejlec, _KEP)
        assert kep.property("x") == arc.property("x") + arc.property("width")
        assert arc.property("y") == kep.property("y")


class TestAllapot:
    def test_alapbol_a_teljes_kep_a_benyomott(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", faceZoom=False)
        assert _gomb(fejlec, _KEP).property("checked") is True
        assert _gomb(fejlec, _ARC).property("checked") is False

    def test_arc_modban_az_arc_a_benyomott(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", faceZoom=True)
        assert _gomb(fejlec, _ARC).property("checked") is True
        assert _gomb(fejlec, _KEP).property("checked") is False


class TestJelzes:
    def test_az_arc_gomb_arc_modot_ker(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", faceZoom=False)
        kert = []
        fejlec.faceZoomToggled.connect(lambda arc: kert.append(arc))
        _gomb(fejlec, _ARC).clicked.emit()
        assert kert == [True]

    def test_a_kep_gomb_teljes_kepet_ker(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", faceZoom=True)
        kert = []
        fejlec.faceZoomToggled.connect(lambda arc: kert.append(arc))
        _gomb(fejlec, _KEP).clicked.emit()
        assert kert == [False]

    def test_a_benyomott_gomb_ujra_nem_ker(self, qml_app):
        """Váltópár, nem kapcsoló: a már érvényes állapot gombja nem vált."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", faceZoom=True)
        kert = []
        fejlec.faceZoomToggled.connect(lambda arc: kert.append(arc))
        _gomb(fejlec, _ARC).clicked.emit()
        assert kert == []

    def test_a_pipa_a_gazda_allapotat_koveti(self, qml_app):
        """#1468 rádió-csapda: kattintás után a gomb a GAZDA állapotát
        mutatja (itt nincs bekötött vezérlő, tehát nem változik)."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", faceZoom=False)
        arc = _gomb(fejlec, _ARC)
        arc.clicked.emit()
        assert arc.property("checked") is False
        assert _gomb(fejlec, _KEP).property("checked") is True


class TestSugo:
    def test_a_sugok_a_mert_angol_alakok(self, qml_app):
        forras = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml"
        ).read_text(encoding="utf-8")
        assert 'qsTr("View zoomed in to the face")' in forras
        assert 'qsTr("View zoomed out to the full picture")' in forras


class TestBekotes:
    def test_a_kepfolyam_a_gazdaablakhoz_koti(self):
        """A fejléc a képfolyamon át a gazdaablak `personFaceZoom` /
        `setPersonFaceZoom` párjához jut — a szűrő mintájára."""
        qml = app_module._APP_DIR / "qml"
        feed = (qml / "PicasaPy" / "LightboxFeed.qml").read_text(encoding="utf-8")
        main = (qml / "Main.qml").read_text(encoding="utf-8")
        assert "grid.appWindow.personFaceZoom" in feed
        assert "grid.appWindow.setPersonFaceZoom" in feed
        assert "controller.setPersonFaceZoom" in main
        assert "controller.personFaceZoom" in main

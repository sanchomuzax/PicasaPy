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


_ROY = "b8e4117cf1d6615b"


def _szemely_album(qml_app, tmp_path, qt_app):
    """A valódi app személy-albuma: `a.jpg`-n Roy MEGERŐSÍTETT arca.

    A fixture könyvtára (`tmp_path/kepek`) már indexelt; az ini-t utólag
    írjuk bele, és újraszinkronizálunk, hogy a személy megjelenjen."""
    from picasapy.index import open_index, sync_tree

    window, controller, _ = qml_app
    lib = tmp_path / "kepek"
    (lib / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n"
        f"[a.jpg]\nfaces=rect64(40004000c000c000),{_ROY};\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller.showPerson("Roy Avery")
    qt_app.processEvents()
    return window, controller


def _vizualis_utodok(elem):
    """Az elem összes VIZUÁLIS utódja. A `findChildren` a QObject-fát
    járja, a képfolyam (`ListView`) delegáltjai viszont csak a vizuális
    fában lógnak a gazdán — ott a fejléc nem található meg."""
    for gyerek in elem.childItems():
        yield gyerek
        yield from _vizualis_utodok(gyerek)


def _ablak_gombja(window, nev):
    latok = [
        g for g in _vizualis_utodok(window.contentItem())
        if g.objectName() == nev and g.isVisible()
    ]
    assert len(latok) == 1, f"{nev}: {len(latok)} látható példány"
    return latok[0]


def _kattints(window, gomb, qt_app):
    """VALÓDI egérkattintás a gomb közepére — nem `clicked.emit()`.

    A gomb `checkable`: egy igazi kattintás a `checked`-et az `onClicked`
    ELŐTT átbillenti (#1468). A jel közvetlen kibocsátása ezt a lépést
    kihagyja, tehát épp a csapdát nem mérné."""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    qt_app.processEvents()
    os_ = gomb
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _racs_url(controller):
    return controller.photos.thumbUrlAt(0)


class TestKattintas:
    def test_az_arc_gomb_arcra_kozelit(self, qml_app, tmp_path, qt_app):
        window, controller = _szemely_album(qml_app, tmp_path, qt_app)
        assert controller.personFaceZoom is False
        assert "&fz=" not in _racs_url(controller)
        _kattints(window, _ablak_gombja(window, _ARC), qt_app)
        assert controller.personFaceZoom is True
        assert "&fz=" in _racs_url(controller)
        assert _ablak_gombja(window, _ARC).property("checked") is True
        assert _ablak_gombja(window, _KEP).property("checked") is False

    def test_a_kep_gomb_visszavalt(self, qml_app, tmp_path, qt_app):
        window, controller = _szemely_album(qml_app, tmp_path, qt_app)
        _kattints(window, _ablak_gombja(window, _ARC), qt_app)
        _kattints(window, _ablak_gombja(window, _KEP), qt_app)
        assert controller.personFaceZoom is False
        assert "&fz=" not in _racs_url(controller)
        assert _ablak_gombja(window, _KEP).property("checked") is True
        assert _ablak_gombja(window, _ARC).property("checked") is False

    def test_a_benyomott_gomb_benyomva_marad(self, qml_app, tmp_path, qt_app):
        """#1468 rádió-csapda: a már benyomott gombra kattintva a `checkable`
        gomb kiugrana — a kötés-visszaállítás tartja benyomva, és a vezérlő
        állapota sem változik."""
        window, controller = _szemely_album(qml_app, tmp_path, qt_app)
        _kattints(window, _ablak_gombja(window, _KEP), qt_app)
        assert controller.personFaceZoom is False
        assert _ablak_gombja(window, _KEP).property("checked") is True
        assert _ablak_gombja(window, _ARC).property("checked") is False
        assert "&fz=" not in _racs_url(controller)


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

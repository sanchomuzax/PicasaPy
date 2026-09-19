"""#857 — album-ugró gombpár a rács görgetősávján (ADR-015).

## A mérés (#856)

Az eredeti Picasa görgetősávján NÉGY gomb van, nem kettő: a fel/le mellett egy
`prevalbum` és egy `nextalbum` ugrógomb (`respack.yt` `scrollart/` + `throttle/`,
`throttle.tre`). Mind a hat elem `m_autorepeat` — nyomva tartva ismétel.

## A döntés (a tulajdonos, 2026-09-18)

> Legyen két külön gomb a görgetősávon is, ugyanúgy, mint az eredetiben.

⇒ a két **album-ugró** megépül; a sáv 10 képpontos, lapos stílusa marad, és a
fel/le nyílgombok nem épülnek meg (ADR-015, `docs/decisions/`).

## Amit ez a fájl mér

A bekötést: a gombok csak a RÁCS sávján jelennek meg, a jelzésük a feed
album-ugrására megy, és nyomva tartva ismételnek. Az ugrás ELMOZDULÁSÁT az élő
rácson mérjük — nem formulát hasonlítunk formulához.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app as app_csomag
from tests.support.qml_blokk import blokk_horgonyra

_QML = Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
_SAV = (_QML / "PicasaScrollBar.qml").read_text(encoding="utf-8")
_FEED = (_QML / "LightboxFeed.qml").read_text(encoding="utf-8")
_DONTES = (
    Path(__file__).resolve().parents[3]
    / "docs" / "decisions" / "gorgetosav-album-ugro.md"
).read_text(encoding="utf-8")


class TestASav:
    def test_van_ket_kulon_gomb(self):
        assert 'objectName: "scrollPrevAlbum"' in _SAV
        assert 'objectName: "scrollNextAlbum"' in _SAV

    def test_a_gombok_JELZEST_bocsatanak_ki(self):
        assert "signal elozoAlbum()" in _SAV
        assert "signal kovetkezoAlbum()" in _SAV

    def test_ALAPBOL_ki_vannak_kapcsolva(self):
        """A mappafa és a párbeszédek sávján az album-ugrásnak nincs értelme."""
        assert "property bool albumUgras: false" in _SAV

    def test_a_gomb_a_SAJAT_elemunk_nem_Qt_alapgomb(self):
        """A sín belsejébe ültetett, saját rajzú elem — nem `Button`."""
        assert "AlbumUgroGomb {" in _SAV

    def test_a_sav_szelessege_VALTOZATLAN(self):
        """ADR-015: a 10 képpontos, lapos stílus marad."""
        assert "readonly property real barThickness: 10" in _SAV


class TestAFeedBekotes:
    def test_a_racs_savja_BEKAPCSOLJA_a_gombokat(self):
        blokk = blokk_horgonyra(_FEED, 'objectName: "feedScrollBar"')
        assert "albumUgras: true" in blokk

    def test_a_jelzeseknek_van_kezeloje(self):
        """Kezelő nélkül a gomb néma maradna (#936 hibaosztálya)."""
        blokk = blokk_horgonyra(_FEED, 'objectName: "feedScrollBar"')
        assert "onElozoAlbum" in blokk
        assert "onKovetkezoAlbum" in blokk

    def test_van_album_ugro_fuggveny(self):
        assert "function ugrasAlbumra(" in _FEED


class TestADontesRogzitve:
    """A jegy első elfogadási feltétele: a döntés a `docs/decisions/`-ben áll."""

    def test_a_dontes_lap_letezik_es_ELFOGADVA(self):
        assert "Státusz:** ELFOGADVA" in _DONTES

    def test_kimondja_mi_epul_meg_es_mi_NEM(self):
        assert "album-ugró" in _DONTES
        assert "Nem épül meg" in _DONTES

    def test_a_MEGDOLT_indoklast_is_kimondja(self):
        """A „natív Windows-króm" érv megdőlt — a stílus más okból áll."""
        assert "megdőlt" in _DONTES


# --- ÉLŐ mérés: a gomb tényleg ismétel-e nyomva tartva ------------------

from PySide6.QtCore import (  # noqa: E402
    QEventLoop,
    QMetaObject,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtCore import Q_ARG  # noqa: E402

from tests.support.jpeg_factory import make_jpeg  # noqa: E402
from PySide6.QtGui import QMouseEvent  # noqa: E402
from PySide6.QtQml import QQmlComponent, QQmlEngine  # noqa: E402
from PySide6.QtQuick import QQuickItem  # noqa: E402

import picasapy.app.application as app_module  # noqa: E402

_ELETBEN: list = []


def _gomb(qt_app):
    """Az `AlbumUgroGomb.qml` ÖNÁLLÓ betöltése — így a viselkedése mérhető."""
    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    elem = QQmlComponent(
        engine, QUrl.fromLocalFile(str(_QML / "AlbumUgroGomb.qml"))
    )
    assert elem.status() == QQmlComponent.Status.Ready, elem.errorString()
    obj = elem.create()
    assert [e.toString() for e in elem.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _ELETBEN.extend([engine, elem, obj])
    return obj


def _egerlenyomas(pont: QPointF) -> QMouseEvent:
    return QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        pont,
        pont,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )


def _egerfelengedes(pont: QPointF) -> QMouseEvent:
    return QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        pont,
        pont,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )


def _var(qt_app, ms: int) -> None:
    hurok = QEventLoop()
    QTimer.singleShot(ms, hurok.quit)
    hurok.exec()
    qt_app.processEvents()


def _terulet(gomb):
    for gyermek in gomb.findChildren(QQuickItem):
        if gyermek.objectName() == "albumUgroTerulet":
            return gyermek
    raise AssertionError("nincs egérterület a gombon")


class TestAzISMETLES:
    """#856: az eredeti mind a hat eleme `m_autorepeat` — nyomva tartva ismétel."""

    def test_egy_KATTINTAS_egy_kivaltas(self, qt_app):
        gomb = _gomb(qt_app)
        terulet = _terulet(gomb)
        darab: list[int] = []
        gomb.aktivalva.connect(lambda: darab.append(1))
        pont = QPointF(3, 3)
        terulet.setWidth(10)
        terulet.setHeight(24)
        terulet.mousePressEvent(
            _egerlenyomas(pont)
        )
        terulet.mouseReleaseEvent(
            _egerfelengedes(pont)
        )
        qt_app.processEvents()
        assert len(darab) == 1, f"egy kattintás {len(darab)} kiváltást adott"

    def test_NYOMVA_TARTVA_tobbszor_sul_el(self, qt_app):
        gomb = _gomb(qt_app)
        terulet = _terulet(gomb)
        terulet.setWidth(10)
        terulet.setHeight(24)
        darab: list[int] = []
        gomb.aktivalva.connect(lambda: darab.append(1))
        pont = QPointF(3, 3)
        terulet.mousePressEvent(
            _egerlenyomas(pont)
        )
        # az első késleltetés + két ismétlés ideje bőven elég
        _var(qt_app, gomb.property("elsoKesleltetes") + 3 * gomb.property("ismetlesKoz"))
        terulet.mouseReleaseEvent(
            _egerfelengedes(pont)
        )
        assert len(darab) >= 3, (
            f"nyomva tartva csak {len(darab)} kiváltás — nem ismétel"
        )

    def test_ELENGEDES_utan_MEGALL(self, qt_app):
        gomb = _gomb(qt_app)
        terulet = _terulet(gomb)
        terulet.setWidth(10)
        terulet.setHeight(24)
        darab: list[int] = []
        gomb.aktivalva.connect(lambda: darab.append(1))
        pont = QPointF(3, 3)
        terulet.mousePressEvent(
            _egerlenyomas(pont)
        )
        _var(qt_app, gomb.property("elsoKesleltetes") + gomb.property("ismetlesKoz"))
        terulet.mouseReleaseEvent(
            _egerfelengedes(pont)
        )
        qt_app.processEvents()
        elengedeskor = len(darab)
        _var(qt_app, 5 * gomb.property("ismetlesKoz"))
        assert len(darab) == elengedeskor, "elengedés után is ismételt"


class TestAzUgrasAZELORACSON:
    """A NAVIGÁCIÓ maga — nem a jelzés, hanem az elmozdulás a rácson.

    ⚠️ A `qml_app` alap-könyvtárában EGY mappa van, tehát album-ugrást nem
    lehetne mérni rajta. A próba ezért maga hoz létre két mappát és
    újraolvastat — kihagyni (`skip`) nem szabad: egy környezetfüggő skip
    sosem fut le, és úgy az őr nem őr.
    """

    @staticmethod
    def _ket_mappas(qml_app, qt_app):
        window, controller, _engine = qml_app
        konyvtar = Path(controller.watchedFolders[0])
        for mappa in ("alma", "korte"):
            (konyvtar / mappa).mkdir(exist_ok=True)
            for i in range(3):
                make_jpeg(konyvtar / mappa / f"{mappa}{i}.jpg", size=(80, 60))
        controller.rescan()
        for _ in range(200):
            qt_app.processEvents()
            if controller.waitForBackgroundWorkers(0.05):
                break
        qt_app.processEvents()
        csoportok = controller.feedGroups
        assert len(csoportok) >= 2, (
            f"kevés csoport: {[c['name'] for c in csoportok]}"
        )
        return window, csoportok

    def test_a_gombok_ott_vannak_a_racs_savjan(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        for nev in ("scrollPrevAlbum", "scrollNextAlbum"):
            assert window.findChild(QQuickItem, nev) is not None, (
                f"{nev} nem található a betöltött felületen"
            )

    def test_a_KOVETKEZO_album_lejjebb_viszi_a_racsot(self, qml_app, qt_app):
        window, _csoportok = self._ket_mappas(qml_app, qt_app)
        racs = window.findChild(QQuickItem, "photoGrid")
        assert racs is not None
        racs.setProperty("contentY", 0.0)
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            racs, "ugrasAlbumra", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 1),
        )
        qt_app.processEvents()
        assert racs.property("contentY") > 0.0, (
            "a következő albumra ugrás nem mozdította a rácsot"
        )

    def test_az_ELOZO_album_VISSZAVISZ(self, qml_app, qt_app):
        window, _csoportok = self._ket_mappas(qml_app, qt_app)
        racs = window.findChild(QQuickItem, "photoGrid")
        racs.setProperty("contentY", 0.0)
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            racs, "ugrasAlbumra", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 1),
        )
        qt_app.processEvents()
        lent = racs.property("contentY")
        assert lent > 0.0
        # kétszer: előbb a saját album elejére, majd az előzőre
        for _ in range(2):
            QMetaObject.invokeMethod(
                racs, "ugrasAlbumra", Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", -1),
            )
            qt_app.processEvents()
        assert racs.property("contentY") < lent, "a visszaugrás nem mozdított"

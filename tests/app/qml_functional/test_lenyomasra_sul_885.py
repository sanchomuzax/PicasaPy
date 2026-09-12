"""#885: 49 vezérlő LENYOMÁSRA sül el az eredetiben, nem felengedésre.

## A mérés forrása

`Property mousedown 1` a `runtime/respack.yt` `.tre` leírásaiban — 49 elem,
és a csoportosításuk következetes: ami **nézetet vált vagy menüt nyit**,
az azonnal hat; ami **műveletet hajt végre** (Mentés, Mégse, Kollázs
létrehozása), az a szabványos felengedésre.

Ellenpélda ugyanabból a forrásból: a `Mégse` gombokon nincs `mousedown`,
viszont 11 helyen van `Property escapekey 1`.

## Amit ez a próba mér

A `PicasaButton` opt-in kapcsolóját (`lenyomasra`) és azt, hogy a
felsorolt vezérlőkön BE van kapcsolva, a művelet-gombokon pedig NINCS. A
kapcsoló nélkül a Qt alapértelmezése (felengedés) marad, és a felület
érezhetően lomhább ugyanazokon a helyeken.

⚠️ A próba a VISELKEDÉST méri: lenyomásra elsül-e a jelzés, és
felengedéskor nem sül-e el MÁSODSZOR. A puszta tulajdonság-olvasás azt
nem mutatná meg, hogy a gomb kétszer hat.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

_QML = Path(picasapy.app.__file__).parent / "qml"

#: a mért csoportok közül azok, amelyeknek MA van vezérlőjük nálunk
LENYOMASRA = [
    "viewerPrevButton",
    "viewerNextButton",
    "faceFilter",
    "movieFilter",
    "geoFilter",
    "dupeFilter",
    "toolbarFlatViewButton",
    "toolbarTreeViewButton",
]

#: a szerkesztő öt füle — `editpanel/tab1`…`tab5`
EDITOR_FULEK = ["editTab0", "editTab1", "editTab2"]

#: MŰVELET-gombok: ezeken NINCS `mousedown` az eredetiben sem — itt a
#: „lenyomtam, de elhúztam, mégsem" visszavonhatóság a fontos
FELENGEDESRE = [
    "toolbarImportButton",
    "toolbarNewAlbumButton",
]


def _lenyom(gomb, qt_app):
    """VALÓDI egér-lenyomás az ABLAKON, a gomb közepére.

    ⚠️ A `QCoreApplication.sendEvent(item, …)` nem elég: a Qt Quick az
    egéreseményeket az ABLAK-on át kézbesíti és ott dönt a megfogásról, egy
    elemre küldött szintetikus esemény pedig a `MouseArea`-ig el sem jut."""
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mousePress(
        gomb.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _felenged(gomb, qt_app):
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mouseRelease(
        gomb.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


@pytest.fixture
def gomb(qt_app):
    """Egyetlen `PicasaButton`, izoláltan — a kapcsoló a komponensé."""
    nezet = QQuickView()
    nezet.engine().addImportPath(str(_QML))
    nezet.setSource(QUrl.fromLocalFile(str(_QML / "PicasaPy" / "PicasaButton.qml")))
    assert nezet.status() == QQuickView.Status.Ready, [
        h.toString() for h in nezet.errors()
    ]
    elem = nezet.rootObject()
    elem.setProperty("width", 60)
    elem.setProperty("height", 24)
    nezet.show()
    qt_app.processEvents()
    yield elem, qt_app
    nezet.deleteLater()


class TestAKapcsolo:
    def test_alapbol_FELENGEDESRE_sul(self, gomb):
        """A többségnek ez a helyes: elhúzva vissza lehet vonni."""
        elem, qt_app = gomb
        szamlalo = []
        elem.clicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)
        assert szamlalo == [], "lenyomásra elsült, pedig nem kértük"
        _felenged(elem, qt_app)
        assert szamlalo == [1]

    def test_bekapcsolva_LENYOMASRA_sul(self, gomb):
        elem, qt_app = gomb
        elem.setProperty("lenyomasra", True)
        qt_app.processEvents()
        szamlalo = []
        elem.clicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)

        assert szamlalo == [1], "a gomb nem sült el lenyomásra"

    def test_felengedeskor_NEM_sul_el_masodszor(self, gomb):
        """A kétszeres hatás rosszabb a lomhaságnál: egy fülváltó kétszer
        váltana, egy léptető kettőt lépne."""
        elem, qt_app = gomb
        elem.setProperty("lenyomasra", True)
        qt_app.processEvents()
        szamlalo = []
        elem.clicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)
        _felenged(elem, qt_app)

        assert szamlalo == [1], f"a gomb {len(szamlalo)}-szor sült el"

    def test_TILTOTT_gomb_nem_sul_el(self, gomb):
        elem, qt_app = gomb
        elem.setProperty("lenyomasra", True)
        elem.setProperty("enabled", False)
        qt_app.processEvents()
        szamlalo = []
        elem.clicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)

        assert szamlalo == []


class TestAHasznalatiHelyek:
    """A mért lista: melyik vezérlőn van bekapcsolva, és melyiken nincs."""

    @pytest.mark.parametrize("nev", LENYOMASRA)
    def test_a_nezetvaltok_es_leptetok_lenyomasra(self, qml_app, nev):
        from PySide6.QtCore import QObject

        window = qml_app[0]
        elem = window.findChild(QObject, nev)
        assert elem is not None, f"{nev} nem található"
        assert elem.property("lenyomasra") is True, (
            f"a(z) {nev} felengedésre sül el, pedig az eredetiben "
            "`mousedown` van rajta (#885)"
        )

    @pytest.mark.parametrize("nev", FELENGEDESRE)
    def test_a_MUVELET_gombok_felengedesre(self, qml_app, nev):
        from PySide6.QtCore import QObject

        window = qml_app[0]
        elem = window.findChild(QObject, nev)
        assert elem is not None, f"{nev} nem található"
        assert not elem.property("lenyomasra"), (
            f"a(z) {nev} lenyomásra sül el, pedig művelet-gomb — elhúzva "
            "vissza kell tudni vonni"
        )


class TestASzerkesztoFulek:
    """`editpanel/tab1`…`tab5`: a fülváltás NÉZETET vált, tehát azonnal hat.

    ⚠️ Ez FORRÁS-szintű állítás, nem viselkedési: a fülgomb `required
    property`-kkel épül (a gazda `EditorPanel`-t várja), tehát önmagában
    nem tölthető be, és így nem is nyomható meg. A viselkedési oldalt a
    `PicasaButton` próbái fedik — ott a kétszeres elsülés is mérve van."""

    def test_a_fulgomb_lenyomasra_valt(self):
        forras = (_QML / "PicasaPy" / "EditTabButton.qml").read_text(
            encoding="utf-8"
        )
        assert "onPressed: panel.activeTab" in forras, (
            "a fülgomb nem lenyomásra vált (#885)"
        )
        assert "onClicked: panel.activeTab" not in forras

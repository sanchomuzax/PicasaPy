"""A „Kollázs szerkesztése" gomb a nézőben (#1002).

A tulajdonos a v0.8.17-ről: *„Ez a gomb mindig megjelenik, ha megnyitom a
kollázst. Jelenleg ennek hiányában nem szerkeszthető a kollázs."*

Az eredeti vezérlő a SZERKESZTŐPANELÉ (`editpanel/editcollage`,
`editpanel.tre:1350`), `m_hidden`-nel: alapból rejtett, és csak akkor jön
elő, ha a megnyitott képnek van kollázs-projektfájlja.

⚠️ Nem azonos a `collagepanel::back_to_collage` = „Vissza a kollázshoz"
gombbal — az a KÖNYVTÁR lapján áll.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

from picasapy.collage.cxf import dumps
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.nodes import SHEET_UNITS, CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.themes import NOBORDER, PICTUREPILE

GOMB = "viewerEditCollageButton"


def _gomb(window):
    return window.findChild(QObject, GOMB)


def _ujraolvas(controller, qt_app) -> None:
    """A frissen lerakott fájl az INDEXBE — enélkül a modell nem látja.

    A `qml_app` a könyvtárat a felállásakor olvassa be; a teszt utána teszi
    oda a kollázst. A `rescan` a felület saját újraolvasása, tehát ez a
    valódi út, nem tesztsegéd-kerülő."""
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _kollazst_keszit(mappa: Path, kep_nev: str, forras: Path) -> Path:
    """JPEG + `.cxf` pár — pontosan az, amit a mentés hagy maga után."""
    from support.jpeg_factory import make_jpeg

    kep = mappa / kep_nev
    make_jpeg(kep, size=(200, 150))
    beallitas = PicasaCollageSettings(
        theme=PICTUREPILE, border=NOBORDER, width=1600, height=1200
    )
    csomopont = CollageNode(
        path=str(forras), center_x=SHEET_UNITS * 0.5, center_y=SHEET_UNITS * 0.3,
        width=280.0, height=337.0, theta=0.0, border=NOBORDER,
    )
    projekt = project_from_nodes([csomopont], beallitas, album_title="Próba")
    kep.with_suffix(".cxf").write_bytes(dumps(projekt))
    return kep


def _nezot_nyit(window, qt_app, sor: int):
    window.setProperty("viewerOpen", True)
    nezo = window.findChild(QObject, "photoViewer")
    if nezo is not None:
        QMetaObject.invokeMethod(
            nezo, "show", Qt.ConnectionType.DirectConnection,
        )
        nezo.setProperty("currentIndex", sor)
    qt_app.processEvents()


class TestAGombLathatosaga:
    def test_sima_fenykepnel_NEM_latszik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        _nezot_nyit(window, qt_app, 0)

        gomb = _gomb(window)
        assert gomb is None or gomb.property("visible") is False

    def test_kollazsnal_LATSZIK(self, qml_app, qt_app, tmp_path):
        """⚠️ Ez a tulajdonos panasza: a gomb nem volt sehol."""
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        kollazs = _kollazst_keszit(lib, "kollazs.jpg", lib / "a.jpg")
        _ujraolvas(controller, qt_app)
        controller.selectFolder(str(lib))
        qt_app.processEvents()
        sor = controller.photos.rowOfPath(str(kollazs))
        assert sor >= 0, "a kollázs nem került a nézetbe"

        _nezot_nyit(window, qt_app, sor)

        gomb = _gomb(window)
        assert gomb is not None
        assert gomb.property("visible") is True


class TestAGombHatasa:
    def test_kattintasra_megnyilik_a_kollazs_lap(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        kollazs = _kollazst_keszit(lib, "kollazs.jpg", lib / "a.jpg")
        _ujraolvas(controller, qt_app)
        controller.selectFolder(str(lib))
        qt_app.processEvents()
        _nezot_nyit(window, qt_app, controller.photos.rowOfPath(str(kollazs)))

        QMetaObject.invokeMethod(
            _gomb(window), "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert controller.collageOpen is True

    def test_kattintas_utan_ELHAGYJUK_a_nezot(self, qml_app, qt_app, tmp_path):
        """#1055: a panel `!viewerOpen`-re látszik — enélkül a lap megnyílna,
        és a felhasználó közben a képet nézné."""
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        kollazs = _kollazst_keszit(lib, "kollazs.jpg", lib / "a.jpg")
        _ujraolvas(controller, qt_app)
        controller.selectFolder(str(lib))
        qt_app.processEvents()
        _nezot_nyit(window, qt_app, controller.photos.rowOfPath(str(kollazs)))

        QMetaObject.invokeMethod(
            _gomb(window), "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert window.property("viewerOpen") is False
        sav = window.findChild(QObject, "documentTabStrip")
        assert sav.property("activeTabId") == window.property("collageTabId")

"""A „Létrehozás" gomb a PISZKOZAT képe fölött (#1072).

A jegy szerint a piszkozatnak **külön befejező lépése** van, és az
eredetiben ez egy ÉLŐ felületi elem a kép fölött: `editpanel/render_now`
= **„Létrehozás"** (spec 4.1/4.3). A bélyegképen nincs rajta — a JPEG-be
csak a „PISZKOZAT" felirat van beleégetve —, tehát nem a képből, hanem a
felületről kell jönnie.

Spec 4.1 két további pontja is ide tartozik, és mindkettő a MEGJELENÉSRŐL
szól, nem a jelzésről:

* a piszkozaton a **„Kollázs szerkesztése" gomb is aktív** (spec 6.),
* sima fényképen egyik gomb sem látszik.

⚠️ A gombra **KATTINTUNK** (a vezérlő metódusát nem hívjuk közvetlenül):
egy nem bekötött gomb ugyanúgy „zöld" volna, ha csak a slotot mérnénk —
ez a #1001 tanulsága.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY
from picasapy.collage.autosave import AUTOSAVE_NAME
from picasapy.collage.cxf import dumps
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.nodes import SHEET_UNITS, CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.themes import NOBORDER, PICTUREPILE

LETREHOZAS = "viewerCreateNowButton"
SZERKESZTES = "viewerEditCollageButton"


def _gomb(window, nev: str):
    return window.findChild(QObject, nev)


def _latszik(window, nev: str) -> bool:
    elem = _gomb(window, nev)
    return elem is not None and elem.property("visible") is True


def _ujraolvas(controller, qt_app) -> None:
    """A frissen lerakott fájl az INDEXBE — a felület saját újraolvasása."""
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _piszkozatot_keszit(mappa: Path, forras: Path) -> Path:
    """Kép + `autosave.cxf`, SAJÁT `.cxf` nélkül — ez a piszkozat (spec 1.)."""
    from support.jpeg_factory import make_jpeg

    mappa.mkdir(parents=True, exist_ok=True)
    kep = mappa / "AI10.jpg"
    make_jpeg(kep, size=(200, 150))
    beallitas = PicasaCollageSettings(
        theme=PICTUREPILE, border=NOBORDER, width=400, height=300
    )
    csomopont = CollageNode(
        path=str(forras), center_x=SHEET_UNITS * 0.5, center_y=SHEET_UNITS * 0.5,
        width=280.0, height=337.0, theta=0.0, border=NOBORDER,
    )
    projekt = project_from_nodes([csomopont], beallitas, album_title="AI10")
    (mappa / AUTOSAVE_NAME).write_bytes(dumps(projekt))
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


def _piszkozatra_nyit(qml_app, qt_app, tmp_path) -> tuple[object, object, Path]:
    window, controller, _engine = qml_app
    lib = tmp_path / "kepek"
    # a piszkozat a KOLLÁZSOK albumban él (spec 1.) — a takarítás
    # (`autosave.cxf` eldobása) is a beállított kimeneti mappára néz. A
    # figyelt gyökér alá tesszük, hogy a `rescan` megtalálja.
    kollazsok = lib / "Kollazsok"
    controller._get_settings().setValue(COLLAGE_OUTPUT_DIR_KEY, str(kollazsok))
    piszkozat = _piszkozatot_keszit(kollazsok, lib / "a.jpg")
    _ujraolvas(controller, qt_app)
    controller.selectFolder(str(kollazsok))
    qt_app.processEvents()
    sor = controller.photos.rowOfPath(str(piszkozat))
    assert sor >= 0, "a piszkozat nem került a nézetbe"
    _nezot_nyit(window, qt_app, sor)
    return window, controller, piszkozat


class TestAGombLathatosaga:
    def test_sima_fenykepnel_NINCS_letrehozas_gomb(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        _nezot_nyit(window, qt_app, 0)

        assert _latszik(window, LETREHOZAS) is False

    def test_piszkozaton_LATSZIK_a_letrehozas(self, qml_app, qt_app, tmp_path):
        """Ez a jegy hiánya: a piszkozatot nem lehetett befejezni."""
        window, _controller, _piszkozat = _piszkozatra_nyit(
            qml_app, qt_app, tmp_path
        )

        assert _latszik(window, LETREHOZAS) is True

    def test_piszkozaton_a_KOLLAZS_SZERKESZTESE_is_latszik(
        self, qml_app, qt_app, tmp_path
    ):
        """Spec 6.: a visszaút a piszkozatról is nyitva áll."""
        window, _controller, _piszkozat = _piszkozatra_nyit(
            qml_app, qt_app, tmp_path
        )

        assert _latszik(window, SZERKESZTES) is True


class TestAGombHatasa:
    def test_kattintasra_KESZ_kollazs_lesz(self, qml_app, qt_app, tmp_path):
        """A befejezés után a kép mellett ott a `.cxf`, az `autosave.cxf`
        pedig eltűnik — a kép többé nem piszkozat."""
        window, controller, piszkozat = _piszkozatra_nyit(
            qml_app, qt_app, tmp_path
        )
        # az éles 5120 képpont egy tesztben másodperceket jelentene; az
        # állítás a fájlpárról szól, nem a felbontásról
        controller._collage_output_width = lambda: 400

        QMetaObject.invokeMethod(
            _gomb(window, LETREHOZAS), "clicked", Qt.ConnectionType.DirectConnection
        )

        hatarido = time.monotonic() + 30.0
        while time.monotonic() < hatarido:
            qt_app.processEvents()
            if piszkozat.with_suffix(".cxf").exists():
                break
            time.sleep(0.02)
        controller.waitForBackgroundWorkers(10.0)
        qt_app.processEvents()

        assert piszkozat.with_suffix(".cxf").exists(), "a kollázs nem készült el"
        assert not (piszkozat.parent / AUTOSAVE_NAME).exists()
        assert controller.isCollageDraft(str(piszkozat)) is False

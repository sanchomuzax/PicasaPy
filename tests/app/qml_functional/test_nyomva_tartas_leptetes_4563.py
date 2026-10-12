"""#4563: a néző ◀ és ▶ léptetőgombjai nyomva tartva folyamatosan lépnek.

Az eredetiben a `prev`/`next` gombok lenyomásra hatnak ÉS ismétlődnek
(`m_autorepeat`). Nálunk a `PicasaButton` lenyomásra sülő ága egy saját
`MouseArea`-ban él, amely el is nyeli az eseményt — a Qt beépített
`autoRepeat`-je ezért sosem indul, és a gomb felengedés nélkül csak egyszer
lép.

A próba VALÓDI egér-lenyomással méri a viselkedést a nézőben: lenyomva tartva
többet léptet egynél, felengedéskor megáll, és a végén tiltott gombbal nem
lép tovább. Ablakmagassággal −5 / 0 / +5 px-en fut, mert a léptetőgombok
helye a felső sáv magasságától függ.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg

_MAPPA = "nyomva_tartas_4563"
_KEPEK = 40
#: ennyi ideig tartjuk nyomva a gombot — a Qt alapértelmezett ismétlési
#: késleltetése (300 ms) után több léptetésnek kell megtörténnie
_TARTAS_MS = 1200
_FELENGEDES_UTANI_MS = 600


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    return window.findChild(QQuickItem, name)


def _var(qt_app, predicate, seconds: float = 5.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if predicate():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _varj(qt_app, ms: int) -> None:
    """Eseményhurok futtatása `ms` ezredmásodpercig (a Timer-ek ettől jönnek)."""
    deadline = time.monotonic() + ms / 1000
    while time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.005)


def _folder_start(controller) -> int:
    for row in range(controller.photos.rowCount()):
        if _MAPPA in controller.photos.filePathAt(row):
            return row
    return -1


def _nyit(qml_app, qt_app):
    """A negyven képes próbamappa megnyitva a nézőben, az első képen."""
    window, controller, _engine = qml_app
    folder = Path(controller.watchedFolders[0]) / _MAPPA
    folder.mkdir(exist_ok=True)
    for index in range(_KEPEK):
        make_jpeg(folder / f"photo-{index:02d}.jpg", size=(60, 40))

    controller.rescan()
    assert _var(
        qt_app,
        lambda: _folder_start(controller) >= 0
        and controller.photos.folderRowRange(_folder_start(controller))[1]
        == _KEPEK,
    ), "a negyvenképes próbamappa nem került be a modellbe"

    start = _folder_start(controller)
    window.setProperty("selectedIndexes", [start])
    window.setProperty("selectedIndex", start)
    viewer = _elem(window, "photoViewer")
    assert viewer is not None, "a nézőt nem találom"
    viewer.setProperty("currentIndex", start)
    window.setProperty("viewerOpen", True)
    assert _var(qt_app, lambda: window.property("viewerOpen") is True)
    qt_app.processEvents()
    return window, viewer, start


def _kozep(gomb):
    """A gomb közepe az ablak koordinátáiban — ugyanúgy, mint egy egérkattintás."""
    return gomb.mapToScene(gomb.boundingRect().center()).toPoint()


def _lenyom(gomb, qt_app) -> None:
    """VALÓDI egér-lenyomás az ABLAKON.

    A `sendEvent` egy elemre nem jut el a `MouseArea`-ig; az ablakon át
    kézbesített esemény igen (ugyanaz a mintát követi, mint a `_lenyom`
    a `test_lenyomasra_sul_885.py`-ben)."""
    QTest.mousePress(
        gomb.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        _kozep(gomb),
    )
    qt_app.processEvents()


def _felenged(gomb, qt_app) -> None:
    QTest.mouseRelease(
        gomb.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        _kozep(gomb),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
class TestNyomvaTartasLeptetes:
    def test_nyomva_tartva_tobbet_lep_mint_egyet(
        self, qml_app, qt_app, height_delta
    ):
        window, viewer, start = _nyit(qml_app, qt_app)
        window.setHeight(window.height() + height_delta)
        qt_app.processEvents()
        gomb = _elem(window, "viewerNextButton")
        assert gomb is not None, "a ▶ gomb nem található"
        assert _var(qt_app, lambda: gomb.isVisible() and gomb.property("enabled"))

        _lenyom(gomb, qt_app)
        _varj(qt_app, _TARTAS_MS)
        _felenged(gomb, qt_app)

        lepesek = viewer.property("currentIndex") - start
        assert lepesek >= 3, (
            f"nyomva tartva a ▶ csak {lepesek} lépést tett, "
            "pedig folyamatosan léptetnie kell"
        )

    def test_felengedeskor_megall(self, qml_app, qt_app, height_delta):
        window, viewer, start = _nyit(qml_app, qt_app)
        window.setHeight(window.height() + height_delta)
        qt_app.processEvents()
        gomb = _elem(window, "viewerNextButton")
        assert gomb is not None

        _lenyom(gomb, qt_app)
        _varj(qt_app, _TARTAS_MS)
        _felenged(gomb, qt_app)
        felengedve = viewer.property("currentIndex")
        _varj(qt_app, _FELENGEDES_UTANI_MS)

        assert viewer.property("currentIndex") == felengedve, (
            "felengedés után is léptet a ▶ gomb"
        )
        assert felengedve > start

    def test_a_bal_gomb_is_nyomva_tartva_lep(self, qml_app, qt_app, height_delta):
        window, viewer, _start = _nyit(qml_app, qt_app)
        window.setHeight(window.height() + height_delta)
        qt_app.processEvents()
        # Előbb a mappa közepére lépünk, hogy legyen hova visszafelé lépni.
        viewer.setProperty("currentIndex", _start + 20)
        qt_app.processEvents()
        gomb = _elem(window, "viewerPrevButton")
        assert gomb is not None, "a ◀ gomb nem található"
        assert _var(qt_app, lambda: gomb.isVisible() and gomb.property("enabled"))

        _lenyom(gomb, qt_app)
        _varj(qt_app, _TARTAS_MS)
        _felenged(gomb, qt_app)

        lepesek = _start + 20 - viewer.property("currentIndex")
        assert lepesek >= 3, (
            f"nyomva tartva a ◀ csak {lepesek} lépést tett"
        )

    def test_a_konyvtar_vegen_a_tiltott_gomb_leall(
        self, qml_app, qt_app, height_delta
    ):
        """Az utolsó képnél a ▶ tiltott: a tartás nem léphet tovább."""
        window, controller, _engine = qml_app
        window.setHeight(window.height() + height_delta)
        qt_app.processEvents()
        _window, viewer, _start = _nyit(qml_app, qt_app)
        utolso = controller.photos.rowCount() - 1
        viewer.setProperty("currentIndex", utolso - 1)
        qt_app.processEvents()
        gomb = _elem(window, "viewerNextButton")
        assert gomb is not None
        assert _var(qt_app, lambda: gomb.property("enabled"))

        _lenyom(gomb, qt_app)
        _varj(qt_app, _TARTAS_MS)
        _felenged(gomb, qt_app)

        assert viewer.property("currentIndex") == utolso, (
            "az utolsó képen túl is léptetett a ▶ gomb"
        )

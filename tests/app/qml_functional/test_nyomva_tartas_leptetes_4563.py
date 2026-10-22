"""#5529: a néző ◀ és ▶ gombja nyomva tartva is csak egyszer lép.

Az eredeti `oneup/prev` és `oneup/next` `mousedown` gomb, de nincs rajtuk
`setautorepeat` (`oneup.tre:75-81`). A külön `plusone`/`minusone` gombok
ismételnek (`oneup.tre:133-143`), ezért az ismétlést csak a néző két
kép-léptetőjéről vesszük le.

A próba VALÓDI egér-lenyomással tartja nyomva mindkét gombot legalább 800 ms-ig,
és pontosan egy képlépést vár. Az ablakmagasságot -5, 0 és +5 px-en is méri,
mert a kattintási pontot a gomb aktuális helyéből kell venni.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from support.jpeg_factory import make_jpeg

_MAPPA = "nyomva_tartas_5529"
_KEPEK = 40
_TARTAS_MS = 800


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    return window.findChild(QQuickItem, name)


def _var(qt_app, predicate, seconds: float = 10.0) -> bool:
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


def _folder_start(controller) -> int:
    for row in range(controller.photos.rowCount()):
        if _MAPPA in controller.photos.filePathAt(row):
            return row
    return -1


def _nyit(qml_app, qt_app):
    """A negyven képes próbamappa megnyitva a nézőben, középső képpel."""
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
    viewer.setProperty("currentIndex", start + 20)
    window.setProperty("viewerOpen", True)
    assert _var(qt_app, lambda: window.property("viewerOpen") is True)
    assert _var(qt_app, lambda: viewer.property("currentIndex") == start + 20)
    return window, viewer, start


def _kozep(gomb):
    """A gomb közepe az ablak koordinátáiban, valódi egérkattintáshoz."""
    return gomb.mapToScene(gomb.boundingRect().center()).toPoint()


def _lenyom(gomb, qt_app) -> None:
    """Az ablakon át kézbesített valódi lenyomás eléri a `MouseArea`-t."""
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


def _lenyomva_tart(
    gomb, qt_app, viewer, kiindulo_index: int, vart_index: int, tartas_ms: int
) -> None:
    lenyomas_ideje = time.monotonic()
    _lenyom(gomb, qt_app)
    tortent_lepes = _var(
        qt_app,
        lambda: viewer.property("currentIndex") != kiindulo_index,
    )
    hatarido = lenyomas_ideje + tartas_ms / 1000
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        time.sleep(0.005)
    _felenged(gomb, qt_app)
    assert tortent_lepes, "a gomb lenyomásra nem lépett képet"
    assert viewer.property("currentIndex") == vart_index, (
        f"nyomva tartva a gomb a {vart_index} helyett "
        f"{viewer.property('currentIndex')} indexre lépett"
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_a_nezo_leptetoi_nyomva_tartva_sem_ismetlik(
    qml_app, qt_app, height_delta
):
    window, viewer, start = _nyit(qml_app, qt_app)
    elvart_magassag = window.height() + height_delta
    window.setHeight(elvart_magassag)
    assert _var(qt_app, lambda: window.height() == elvart_magassag)

    kovetkezo = _elem(window, "viewerNextButton")
    elozo = _elem(window, "viewerPrevButton")
    assert kovetkezo is not None, "a ▶ gomb nem található"
    assert elozo is not None, "a ◀ gomb nem található"
    assert _var(
        qt_app,
        lambda: kovetkezo.isVisible() and kovetkezo.property("enabled")
        and elozo.isVisible() and elozo.property("enabled"),
    ), "a néző két léptetőgombja nem épült fel"

    if height_delta == 0:
        kep = window.grabWindow()
        assert not kep.isNull(), "a néző képernyőképe üres"
        output = Path(__file__).resolve().parents[3] / ".bt" / "kep5529.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        assert kep.save(str(output)), f"a néző képe nem menthető: {output}"

    kezdet = start + 10
    viewer.setProperty("currentIndex", kezdet)
    assert _var(qt_app, lambda: viewer.property("currentIndex") == kezdet)
    _lenyomva_tart(
        kovetkezo, qt_app, viewer, kezdet, kezdet + 1, _TARTAS_MS
    )

    kezdet = start + 20
    viewer.setProperty("currentIndex", kezdet)
    assert _var(qt_app, lambda: viewer.property("currentIndex") == kezdet)
    _lenyomva_tart(elozo, qt_app, viewer, kezdet, kezdet - 1, _TARTAS_MS)

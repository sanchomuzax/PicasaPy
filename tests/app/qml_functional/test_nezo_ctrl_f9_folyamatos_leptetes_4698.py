"""#4698: Ctrl+F9 a nézőben a mappa végéig lép, és kézi műveletre leáll."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg

_MAPPA = "ctrl_f9_folyamatos_4698"
_KEPEK = 8


def _var(qt_app, predicate, seconds: float = 3.0) -> bool:
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


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    return window.findChild(QObject, name)


def _folder_start(controller) -> int:
    for row in range(controller.photos.rowCount()):
        if _MAPPA in controller.photos.filePathAt(row):
            return row
    return -1


def _nyit(qml_app, qt_app):
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
    ), "a nyolcképes próbamappa nem került be a modellbe"

    start = _folder_start(controller)
    window.setProperty("selectedIndexes", [start])
    window.setProperty("selectedIndex", start)
    viewer = _elem(window, "photoViewer")
    assert viewer is not None, "a nézőt nem találom"
    viewer.setProperty("currentIndex", start)
    window.setProperty("viewerOpen", True)
    assert _var(qt_app, lambda: window.property("viewerOpen") is True)
    viewer.setProperty("focus", True)
    viewer.forceActiveFocus()
    qt_app.processEvents()
    timer = window.findChild(QObject, "ctrlF9AutoAdvanceTimer")
    return window, viewer, timer, start


def _ctrl_f9(window) -> None:
    QTest.keyClick(
        window, Qt.Key.Key_F9, Qt.KeyboardModifier.ControlModifier
    )


def test_ctrl_f9_az_utolso_kepig_lep_es_az_ismetelt_nyomas_nem_allitja_meg(
    qml_app, qt_app
):
    window, viewer, timer, start = _nyit(qml_app, qt_app)
    assert timer is not None, "a néző folyamatos léptető időzítője hiányzik"

    _ctrl_f9(window)
    _ctrl_f9(window)

    utolso = start + _KEPEK - 1
    assert _var(
        qt_app,
        lambda: viewer.property("currentIndex") == utolso
        and timer.property("running") is False,
    ), (
        "a Ctrl+F9 nem léptetett el a mappa utolsó képéig, vagy az időzítő "
        f"nem állt le ott (aktuális sor: {viewer.property('currentIndex')}, "
        f"utolsó sor: {utolso})"
    )


def test_kezi_lapozas_leallitja_a_folyamatos_leptetest(qml_app, qt_app):
    window, viewer, timer, start = _nyit(qml_app, qt_app)
    assert timer is not None
    _ctrl_f9(window)
    assert _var(qt_app, lambda: viewer.property("currentIndex") >= start + 2)

    elotte = viewer.property("currentIndex")
    QTest.keyClick(window, Qt.Key.Key_Right)
    qt_app.processEvents()

    assert viewer.property("currentIndex") == elotte + 1
    assert timer.property("running") is False, "a kézi lapozás nem állította le"


def test_nezo_bezarasa_leallitja_a_folyamatos_leptetest(qml_app, qt_app):
    window, viewer, timer, start = _nyit(qml_app, qt_app)
    assert timer is not None
    _ctrl_f9(window)
    assert _var(qt_app, lambda: viewer.property("currentIndex") > start)

    window.setProperty("viewerOpen", False)
    qt_app.processEvents()

    assert timer.property("running") is False, "a néző bezárása nem állította le"


def test_konyvtarnezetben_nincs_hatas_es_az_autorepeat_nem_indit(qml_app, qt_app):
    window, viewer, timer, start = _nyit(qml_app, qt_app)
    assert timer is not None
    window.setProperty("viewerOpen", False)
    qt_app.processEvents()

    QTest.keyClick(window, Qt.Key.Key_F9, Qt.KeyboardModifier.ControlModifier)
    assert viewer.property("currentIndex") == start
    assert timer.property("running") is False

    window.setProperty("viewerOpen", True)
    viewer.forceActiveFocus()
    qt_app.processEvents()
    repeat = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_F9,
        Qt.KeyboardModifier.ControlModifier,
        "",
        True,
        1,
    )
    QCoreApplication.sendEvent(viewer, repeat)
    qt_app.processEvents()

    assert timer.property("running") is False, "az automatikus ismétlés elindította"

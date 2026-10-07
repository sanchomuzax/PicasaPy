"""#4462: a néző helyi menüjében az eredeti képhez vezető kattintás."""

from __future__ import annotations

import time
from pathlib import Path

import shiboken6
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _menu_sor(menu, nev: str) -> QQuickItem:
    kifejezes = QQmlExpression(
        qmlContext(menu),
        menu,
        "(function () {"
        "  for (var i = 0; i < count; ++i) {"
        "    var item = itemAt(i);"
        f'    if (item && item.objectName === "{nev}") return item;'
        "  }"
        "  return null;"
        "})()",
    )
    eredmeny, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    assert eredmeny is not None, f"{nev} menüsor nem található"
    return shiboken6.wrapInstance(
        shiboken6.getCppPointer(eredmeny)[0], QQuickItem
    )


def _kattint(qt_app, elem) -> None:
    assert elem.isEnabled(), f"{elem.objectName()} le van tiltva"
    assert elem.width() > 0 and elem.height() > 0
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_nezo_jobbklikk_es_eredeti_menu_kattintas_a_fajlkezelobe_vezet(
    qml_app, qt_app, monkeypatch, magassag_eltolas
):
    import picasapy.app.fileops_controller as fileops_module

    window, controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.show()
    window.requestActivate()

    viewer = _gyerek(window, "photoViewer")
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", 0)
    assert _varj(qt_app, lambda: viewer.isVisible())
    kep = Path(str(viewer.property("currentPath")))
    assert kep.exists()
    eredeti = kep.parent / ".picasaoriginals" / kep.name
    eredeti.parent.mkdir(parents=True, exist_ok=True)
    eredeti.write_bytes(b"#4462 eredeti")

    megmutatott = []
    monkeypatch.setattr(
        fileops_module, "reveal_in_file_manager", megmutatott.append
    )

    pont = viewer.mapToScene(QPointF(viewer.width() / 2, viewer.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()
    menu = _gyerek(window, "viewerContextMenu")
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        "a nagy képen végzett valódi jobbklikk nem nyitotta meg a helyi menüt"
    )

    almenutetel = _menu_sor(menu, "viewerMenuLocateMenuItem")
    _kattint(qt_app, almenutetel)
    almen = _gyerek(window, "viewerMenuLocateMenu")
    assert _varj(qt_app, lambda: almen.property("opened") is True), (
        "a feltételes Keresés almenü nem nyílt meg"
    )
    eredeti_tetel = _gyerek(window, "viewerMenuLocateOriginal")
    assert eredeti_tetel.isEnabled(), "a megőrzött eredeti tétele letiltott"
    _kattint(qt_app, eredeti_tetel)

    assert _varj(qt_app, lambda: len(megmutatott) == 1), (
        "az Eredeti a lemezen kattintás nem a FileOpsController műveletét hívta"
    )
    assert megmutatott == [eredeti]
    assert Path(controller.photos.filePathAt(0)) == kep

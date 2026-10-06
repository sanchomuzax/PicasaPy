"""#4462: a mappalista helyi menüje valódi jobbklikkel és kattintással."""

from __future__ import annotations

import time

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


def _menu_sor(menu, *, object_name: str | None = None, submenu_name: str | None = None):
    feltetel = []
    if object_name is not None:
        feltetel.append(f'item.objectName === "{object_name}"')
    if submenu_name is not None:
        feltetel.append(
            f'item.subMenu && item.subMenu.objectName === "{submenu_name}"'
        )
    kifejezes = QQmlExpression(
        qmlContext(menu),
        menu,
        "(function () {"
        "  for (var i = 0; i < count; ++i) {"
        "    var item = itemAt(i);"
        f"    if (item && ({' || '.join(feltetel)})) return item;"
        "  }"
        "  return null;"
        "})()",
    )
    eredmeny, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    assert eredmeny is not None, (
        f"nem található menüsor: objectName={object_name!r}, "
        f"submenu={submenu_name!r}"
    )
    return shiboken6.wrapInstance(
        shiboken6.getCppPointer(eredmeny)[0], QQuickItem
    )


def _kattint(qt_app, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    assert elem is not None and elem.isEnabled(), (
        f"{elem.objectName() if elem is not None else 'menüsor'} le van tiltva"
    )
    assert elem.width() > 0 and elem.height() > 0
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        gomb,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _jobbklikk_a_mappalista_ures_reszen(window, qt_app) -> None:
    pane = _gyerek(window, "folderPane")
    assert pane.width() > 0 and pane.height() > 0
    pont = pane.mapToScene(QPointF(pane.width() / 2, pane.height() - 8))
    QTest.mouseClick(
        window,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()
    menu = _gyerek(window, "folderListContextMenu")
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        "a bal oldali mappalista üres részén a valódi jobbklikk nem nyitotta meg a menüt"
    )


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_indexkepek_kapcsolo_valodi_jobbkattintas_utan_kattintassal_mukodik(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.show()
    window.requestActivate()

    pane = _gyerek(window, "folderPane")
    hierarchy = pane.property("hierarchyController")
    elotte = bool(hierarchy.property("albumThumbs"))
    _jobbklikk_a_mappalista_ures_reszen(window, qt_app)

    tetel = _gyerek(window, "folderListMenuShowThumbnails")
    assert tetel.isEnabled(), "az eredeti indexkép-kapcsoló helyfoglaló maradt"
    _kattint(qt_app, tetel)

    assert _varj(
        qt_app,
        lambda: bool(hierarchy.property("albumThumbs")) is not elotte,
    ), "a helyi menü kattintása nem a meglévő indexkép-kapcsolót billentette"


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_asztal_gyorsugras_valodi_menukattintassal_mukodik(
    qml_app, qt_app, monkeypatch, magassag_eltolas
):
    import picasapy.app.folder_hierarchy_controller as hierarchy_module

    window, controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.show()
    window.requestActivate()
    pane = _gyerek(window, "folderPane")
    hierarchy = pane.property("hierarchyController")
    desktop_path = str(controller.watchedFolders[0])
    eredeti_feloldo = hierarchy_module._rendszermappa

    def _rendszermappa(token: str) -> str:
        if token == "desktop":
            return desktop_path
        return eredeti_feloldo(token)

    monkeypatch.setattr(hierarchy_module, "_rendszermappa", _rendszermappa)
    _jobbklikk_a_mappalista_ures_reszen(window, qt_app)

    menu = _gyerek(window, "folderListContextMenu")
    shortcuts = _gyerek(window, "folderListMenuShortcuts")
    sor = _menu_sor(menu, submenu_name="folderListMenuShortcuts")
    _kattint(qt_app, sor)
    assert _varj(qt_app, lambda: shortcuts.property("opened") is True), (
        "a Gyorsbillentyűk almenü nem nyílt meg kattintásra"
    )

    desktop = _gyerek(window, "folderListMenuDesktop")
    assert desktop.isEnabled(), "az Asztal gyorsugrás helyfoglaló maradt"
    _kattint(qt_app, desktop)
    assert _varj(
        qt_app,
        lambda: hierarchy.property("viewRoot") == "desktop",
    ), "az Asztal tétel kattintása nem választotta ki az Asztal gyökeret"

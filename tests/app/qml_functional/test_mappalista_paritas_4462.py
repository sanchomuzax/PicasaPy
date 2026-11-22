"""#4462: a mappalista menüje a ▾ gombról, valódi kattintással.

A hasáb üres részén a jobbklikk nem nyit menüt (#7349, Colab job-801).
"""

from __future__ import annotations

import shiboken6
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


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


def _nezetbeallito_megnyitasa(window, qt_app) -> None:
    """Valódi kattintás a ▾ gombra. A hasáb üres részén nincs menü (#7349),
    a mappalista menüjének egyetlen belépése a nézetbeállító gomb."""
    _kattint(qt_app, _gyerek(window, "toolbarFolderViewPopupButton"))
    menu = _gyerek(window, "toolbarFolderListMenu")
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        "a ▾ gomb valódi kattintása nem nyitotta meg a mappalista menüjét"
    )


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_indexkepek_kapcsolo_a_nezetbeallito_nyil_utan_kattintassal_mukodik(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.show()
    window.requestActivate()

    pane = _gyerek(window, "folderPane")
    hierarchy = pane.property("hierarchyController")
    elotte = bool(hierarchy.property("albumThumbs"))
    _nezetbeallito_megnyitasa(window, qt_app)

    tetel = _gyerek(window, "toolbarFolderListMenuShowThumbnails")
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
    # #7350: az Asztal tétel engedélyezettsége a mappalista cseréjekor számolódik
    # újra; a gyökér-csere az app indulása után történt, ezért újratöltjük a
    # mappalistát (ugyanaz a jel, amit a szinkron végén a program is kiad)
    controller.syncFinished.emit()
    assert _varj(qt_app, lambda: hierarchy.property("desktopAvailable") is True), (
        "az Asztal gyökere alatt van könyvtári mappa, a tételnek engedélyezettnek kell lennie"
    )
    _nezetbeallito_megnyitasa(window, qt_app)

    menu = _gyerek(window, "toolbarFolderListMenu")
    shortcuts = _gyerek(window, "toolbarFolderListMenuShortcuts")
    sor = _menu_sor(menu, submenu_name="toolbarFolderListMenuShortcuts")
    _kattint(qt_app, sor)
    assert _varj(qt_app, lambda: shortcuts.property("opened") is True), (
        "a Gyorsbillentyűk almenü nem nyílt meg kattintásra"
    )

    desktop = _gyerek(window, "toolbarFolderListMenuDesktop")
    assert desktop.isEnabled(), "az Asztal gyorsugrás helyfoglaló maradt"
    _kattint(qt_app, desktop)
    assert _varj(
        qt_app,
        lambda: hierarchy.property("viewRoot") == "desktop",
    ), "az Asztal tétel kattintása nem választotta ki az Asztal gyökeret"

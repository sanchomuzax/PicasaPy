"""#7037: A Tulajdonságok panel helyi menüje sortípus szerint.

- A kulcsszó-sor szerkesztése (gomb és helyi menü) a jobb oldali Tags panelt
  kapcsolja (nyitja/zárja, mint a Ctrl+T).
- A dátumsor helyi menüjében a Dátum és idő beállítása nyitja a meglévő
  dátumállítót az adott kép dátumával.
- Más sor nem kap dátumállítót vagy címkekapcsolót.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


def _kepek_datummal_es_cimkevel(lib: Path) -> None:
    make_jpeg(
        lib / "foto.jpg",
        size=(320, 240),
        taken_at="2020:05:15 14:30:00",
        datetime_0th="2020:05:15 14:30:00",
        keywords=("tesztcimke",),
    )


@pytest.fixture
def properties_app_7037(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_kepek_datummal_es_cimkevel
    )


def _item(root, name: str):
    found = root.findChild(QObject, name)
    if found is not None:
        return found
    visual_root = root.contentItem() if hasattr(root, "contentItem") else root
    if hasattr(visual_root, "childItems"):
        stack = [visual_root]
        while stack:
            current = stack.pop()
            if current.objectName() == name:
                return current
            stack.extend(current.childItems())
    assert found is not None, f"Nem található elem: {name}"


def _click(window, item, button, qt_app):
    assert item.width() > 0 and item.height() > 0, (
        f"{item.objectName()} kattintási céljának mérete nulla"
    )
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    target_window = window if button == Qt.MouseButton.RightButton else item.window()
    assert target_window is not None, f"{item.objectName()} nincs ablakban"
    QTest.mouseClick(
        target_window,
        button,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _list_item_at(lista, index: int):
    expr = QQmlExpression(qmlContext(lista), lista, f"itemAtIndex({index})")
    item, err = expr.evaluate()
    if err:
        return None
    return item


def _wait_for(qt_app, predicate, timeout_ms: int = 10000) -> bool:
    return var_feltetelre(qt_app, predicate, timeout_ms / 1000)


def _wait_for_drawer_open(qt_app, window, drawer, panel) -> None:
    def drawer_fully_open():
        target_width = float(drawer.property("kivantSzelesseg"))
        return (
            panel.isVisible()
            and panel.height() > 0
            and abs(float(drawer.width()) - target_width) <= 3
        )

    assert _wait_for(qt_app, drawer_fully_open), "a jobb fiók nem nyílt ki teljesen"


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_keywords_gomb_es_helyi_menu_tags_panelt_kapcsolja(
    properties_app_7037, qt_app, magassag_eltolas
):
    """A kulcsszó-sor szerkesztése a Tags panelt nyitja/zárja (Ctrl+T úton)."""
    window, controller, _engine = properties_app_7037
    window.show()
    window.requestActivate()

    original_height = int(window.height())
    window.setHeight(original_height + magassag_eltolas)

    library = Path(controller._roots[0])
    controller.selectFolder(str(library))
    assert _wait_for(qt_app, lambda: controller.photos.rowCount() == 1)

    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.setProperty("activeDrawerTab", "properties")

    panel = _item(window, "propertiesPanel")
    drawer = _item(window, "rightDrawer")
    _wait_for_drawer_open(qt_app, window, drawer, panel)

    # 1. A Keywords gomb (editKeywordsButton) a Tags panelt nyitja meg
    edit_button = _item(panel, "editKeywordsButton")
    assert edit_button.isVisible() and edit_button.isEnabled()
    _click(window, edit_button, Qt.MouseButton.LeftButton, qt_app)

    # Elvárás: az activeDrawerTab átvált "tags"-ra, és a tagsPanel látható
    assert _wait_for(
        qt_app,
        lambda: window.property("activeDrawerTab") == "tags"
        and _item(window, "tagsPanel").isVisible(),
    ), "A Keywords gomb nem a Tags panelt nyitotta meg"

    # 2. Visszaváltunk a Properties panelre
    window.setProperty("activeDrawerTab", "properties")
    _wait_for_drawer_open(qt_app, window, drawer, panel)

    # 3. Jobb kattintás a kulcsszó-sorra (keywordsPropertyRow)
    kw_row = _item(panel, "keywordsPropertyRow")
    assert kw_row.isVisible()
    _click(window, kw_row, Qt.MouseButton.RightButton, qt_app)

    menu = panel.findChild(QObject, "propertiesPanelContextMenu")
    assert menu is not None, "A helyi menü nem található"
    assert _wait_for(
        qt_app, lambda: bool(menu.property("opened"))
    ), "Jobbklikkre nem nyílt meg a helyi menü a kulcsszó-soron"

    edit_tags = menu.findChild(QQuickItem, "propertiesMenuEditTags")
    assert edit_tags is not None, "Az Edit Tags menüpont hiányzik"
    assert edit_tags.isVisible(), "Az Edit Tags menüpont nem látható a kulcsszó-soron"
    assert edit_tags.property("text") in ("Edit Tags", "Szerkesztési címkék")

    _click(window, edit_tags, Qt.MouseButton.LeftButton, qt_app)

    assert _wait_for(
        qt_app,
        lambda: window.property("activeDrawerTab") == "tags"
        and _item(window, "tagsPanel").isVisible(),
    ), "Az Edit Tags menüpont nem nyitotta meg a Tags panelt"


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_datumsor_helyi_menuje_datumallitot_nyit(
    properties_app_7037, qt_app, magassag_eltolas
):
    """A dátumsor helyi menüjében a Dátum és idő beállítása az adott képpel nyílik."""
    window, controller, _engine = properties_app_7037
    window.show()
    window.requestActivate()

    original_height = int(window.height())
    window.setHeight(original_height + magassag_eltolas)

    library = Path(controller._roots[0])
    controller.selectFolder(str(library))
    assert _wait_for(qt_app, lambda: controller.photos.rowCount() == 1)

    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.setProperty("activeDrawerTab", "properties")

    panel = _item(window, "propertiesPanel")
    drawer = _item(window, "rightDrawer")
    _wait_for_drawer_open(qt_app, window, drawer, panel)

    property_list = _item(panel, "propertyList")
    assert property_list.isVisible()

    # Megvárjuk az entries betöltését
    assert _wait_for(
        qt_app,
        lambda: len(panel.property("entries") or []) > 0,
    ), "A tulajdonságok nem töltődtek be a panelbe"

    def get_date_row_item():
        entries = panel.property("entries")
        if not entries:
            return None
        for idx, entry in enumerate(entries):
            lbl = entry.get("label", "")
            if lbl in ("Camera Date", "Fényképezőgép dátuma"):
                return _list_item_at(property_list, idx)
        return None

    assert _wait_for(qt_app, lambda: get_date_row_item() is not None), (
        "A dátumsor (Camera Date) nem jelent meg a listában"
    )

    date_item = get_date_row_item()
    assert date_item is not None

    # Jobb kattintás a dátumsorra
    _click(window, date_item, Qt.MouseButton.RightButton, qt_app)

    menu = panel.findChild(QObject, "propertiesPanelContextMenu")
    assert menu is not None
    assert _wait_for(
        qt_app, lambda: bool(menu.property("opened"))
    ), "Jobbklikkre nem nyílt meg a helyi menü a dátumsoron"

    adjust_item = menu.findChild(QQuickItem, "propertiesMenuAdjustTimestamp")
    assert adjust_item is not None, "A propertiesMenuAdjustTimestamp menüpont hiányzik"
    assert adjust_item.isVisible(), "A dátumállító menüpont nem látható a dátumsoron"
    assert adjust_item.property("text") in (
        "Adjust &Date and Time...",
        "&Dátum és idő beállítása…",
        "&Dátum és idő beállítása...",
    )

    _click(window, adjust_item, Qt.MouseButton.LeftButton, qt_app)

    timestamp_dialog = _item(window, "adjustTimestampDialog")
    assert _wait_for(
        qt_app, lambda: bool(timestamp_dialog.property("visible"))
    ), "Az AdjustTimestampDialog nem nyílt meg"

    assert int(timestamp_dialog.property("selectedYear")) == 2020
    assert int(timestamp_dialog.property("selectedMonth")) == 5
    assert int(timestamp_dialog.property("selectedDay")) == 15


def test_mas_sor_nem_kap_datumallitot_vagy_cimkekapcsolot(
    properties_app_7037, qt_app
):
    """Más sor (pl. File Size, File Path) nem kap dátumállítót vagy címkekapcsolót."""
    window, controller, _engine = properties_app_7037
    window.show()
    window.requestActivate()

    library = Path(controller._roots[0])
    controller.selectFolder(str(library))
    assert _wait_for(qt_app, lambda: controller.photos.rowCount() == 1)

    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.setProperty("activeDrawerTab", "properties")

    panel = _item(window, "propertiesPanel")
    drawer = _item(window, "rightDrawer")
    _wait_for_drawer_open(qt_app, window, drawer, panel)

    property_list = _item(panel, "propertyList")

    assert _wait_for(
        qt_app,
        lambda: len(panel.property("entries") or []) > 0,
    ), "A tulajdonságok nem töltődtek be"

    def get_other_row_item():
        entries = panel.property("entries")
        if not entries:
            return None
        for idx, entry in enumerate(entries):
            lbl = entry.get("label", "")
            if lbl not in (
                "Camera Date",
                "Fényképezőgép dátuma",
                "Keywords",
                "Tags",
                "Címkék",
                "Kulcsszavak",
            ):
                return _list_item_at(property_list, idx)
        return None

    assert _wait_for(qt_app, lambda: get_other_row_item() is not None), (
        "Nem található egyéb sor a listában"
    )

    other_item = get_other_row_item()
    _click(window, other_item, Qt.MouseButton.RightButton, qt_app)

    menu = panel.findChild(QObject, "propertiesPanelContextMenu")
    if menu and bool(menu.property("opened")):
        edit_tags = menu.findChild(QQuickItem, "propertiesMenuEditTags")
        adjust_item = menu.findChild(QQuickItem, "propertiesMenuAdjustTimestamp")
        assert not (edit_tags and edit_tags.isVisible()), (
            "Az Edit Tags látható volt egy egyéb tulajdonságsoron!"
        )
        assert not (adjust_item and adjust_item.isVisible()), (
            "A dátumállító látható volt egy egyéb tulajdonságsoron!"
        )

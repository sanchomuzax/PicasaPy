"""#4581: a Tulajdonságok panel címkemenüje valódi jobbklikkel nyílik."""

from __future__ import annotations

from PySide6.QtCore import QElapsedTimer, QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


def _item(window, name: str):
    item = window.findChild(QQuickItem, name)
    assert item is not None, f"{name} nincs a felületen"
    return item


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


def _wait_for(qt_app, predicate, timeout_ms: int = 3000) -> bool:
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < timeout_ms:
        qt_app.processEvents()
        if predicate():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(predicate())


def test_right_click_edit_tags_opens_tags_panel_at_variable_window_heights(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    window.show()
    window.requestActivate()
    window.setProperty("activeDrawerTab", "properties")
    panel = _item(window, "propertiesPanel")
    drawer = _item(window, "rightDrawer")

    def drawer_fully_open():
        target_width = float(drawer.property("kivantSzelesseg"))
        return (
            panel.isVisible()
            and panel.height() > 0
            and abs(float(drawer.width()) - target_width) <= 3
        )

    assert _wait_for(qt_app, drawer_fully_open)
    original_height = int(window.height())
    context_area = panel.findChild(QQuickItem, "propertiesPanelContextArea")
    assert context_area is not None, "a Tulajdonságok panel jobbklikk-területe hiányzik"
    assert context_area.parentItem().objectName() == "propertiesPanel", (
        f"a jobbklikk-terület szülője: {context_area.parentItem()}"
    )
    assert context_area.isVisible(), f"rejtett a jobbklikk-terület: {context_area}"
    assert abs(context_area.width() - panel.width()) <= 3, (
        f"a jobbklikk-terület mérete: {context_area.width()} × "
        f"{context_area.height()}"
    )
    menu = panel.findChild(QObject, "propertiesPanelContextMenu")
    assert menu is not None, "a Tulajdonságok panel helyi menüje hiányzik"

    for offset in (-5, 0, 5):
        window.setHeight(original_height + offset)
        assert _wait_for(qt_app, drawer_fully_open)
        _click(window, context_area, Qt.MouseButton.RightButton, qt_app)

        assert _wait_for(
            qt_app, lambda: bool(menu.property("opened"))
        ), "jobbklikkre nem nyílt meg a Tulajdonságok panel helyi menüje"

        edit_tags = menu.findChild(QQuickItem, "propertiesMenuEditTags")
        assert edit_tags is not None, "a Címkék szerkesztése menüpont hiányzik"
        assert edit_tags.property("text") == "Edit Tags"
        _click(window, edit_tags, Qt.MouseButton.LeftButton, qt_app)

        assert _wait_for(
            qt_app,
            lambda: window.property("activeDrawerTab") == "tags"
            and _item(window, "tagsPanel").isVisible(),
        ), "a Címkék szerkesztése menüpont nem nyitotta meg a Címkék panelt"

        if offset != 5:
            window.setProperty("activeDrawerTab", "properties")
            assert _wait_for(qt_app, drawer_fully_open)

"""QML-funkcionális teszt: a #422 3. lépcsőjének menü-BEKÖTÉSEI.

A menük szerkezetét a `tests/app/test_stage3_context_menus_422.py` őrzi
(komponensenként, önmagában). Itt az a tárgy, hogy a jelzés tényleg
elvégzi-e a műveletet a teljes alkalmazásban.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _selected(window):
    """A QML-oldali tömb `QJSValue`-ként jön vissza — a projektben
    szokásos módon variánssá alakítva hasonlítjuk."""
    value = window.property("selectedIndexes")
    rows = value.toVariant() if hasattr(value, "toVariant") else value
    return [int(row) for row in rows]


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestFolderListMenuWiring:
    def test_pane_has_a_right_click_handler_of_its_own(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        handler = _child(window, "folderPaneContextMenuHandler")
        assert handler.property("acceptedButtons") == Qt.MouseButton.RightButton

    # #461/3: a bal panel SAJÁT menüje a PANELT rendezi (az eredeti
    # `AlbumList` menüje is ezt tette — ui-audit-context-menus.md A.2), a
    # felső Nézet ▸ Mappanézet pedig a RÁCSOT (#321). A kettő külön
    # beállítás; korábban mindkét menü a rács-rendezést írta, ezért a panel
    # menüjének pipái hazudtak.
    def test_opening_the_menu_takes_the_current_sort_state(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setPaneSort("size")
        qt_app.processEvents()
        pane = _child(window, "folderPane")
        QMetaObject.invokeMethod(
            pane, "openFolderListContextMenu", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert _child(window, "folderListContextMenu").property("sortMode") == "size"

    def test_sort_request_reaches_the_controller(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        grid_before = controller.folderSort
        menu = _child(window, "folderListContextMenu")
        menu.sortModeRequested.emit("name")
        qt_app.processEvents()
        assert controller.paneSort == "name"
        assert controller.folderSort == grid_before  # a rácsot NEM piszkálja

    def test_reverse_request_flips_the_controller_state(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        before = controller.paneSortReverse
        menu = _child(window, "folderListContextMenu")
        menu.sortReverseRequested.emit()
        qt_app.processEvents()
        assert controller.paneSortReverse is not before


class TestTagMenuWiring:
    def _tag_a_photo(self, window, controller, qt_app, keyword="nyaralas"):
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        controller.addKeywordToRows([0], keyword)
        qt_app.processEvents()
        return keyword

    def test_add_to_selection_tags_every_selected_photo(
        self, qml_app, qt_app
    ):
        """A tétel a TELJES kijelölésre teszi rá a címkét, nem csak a
        jobbklikkelt képre."""
        window, controller, _engine = qml_app
        keyword = self._tag_a_photo(window, controller, qt_app)
        window.setProperty("selectedIndexes", [0, 1])
        qt_app.processEvents()

        panel = _child(window, "tagsPanel")
        panel.addToSelectionRequested.emit(keyword)
        qt_app.processEvents()
        assert keyword in (controller.photos.photos[1].keywords or "")

    def test_find_tagged_starts_a_search_for_the_keyword(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        keyword = self._tag_a_photo(window, controller, qt_app)
        panel = _child(window, "tagsPanel")
        panel.findTaggedRequested.emit(keyword)
        qt_app.processEvents()
        assert controller.searchQuery == keyword


class TestTrayMenuWiring:
    def test_keep_selection_narrows_to_the_anchor(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 1)
        qt_app.processEvents()
        _child(window, "trayContextMenu").keepSelectionRequested.emit()
        qt_app.processEvents()
        assert _selected(window) == [1]

    def test_remove_selection_drops_the_anchor(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 1)
        qt_app.processEvents()
        _child(window, "trayContextMenu").removeSelectionRequested.emit()
        qt_app.processEvents()
        assert _selected(window) == [0]
        assert window.property("selectedIndex") == 0

    def test_tray_has_its_own_right_click_handler(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        handler = _child(window, "trayContextMenuHandler")
        assert handler.property("acceptedButtons") == Qt.MouseButton.RightButton

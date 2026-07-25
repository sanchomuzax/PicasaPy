"""QML-funkcionális tesztek: Helyek-panel és geo-szűrő (#30).

A panel a Nézet → Helyek menüponttal nyílik, a jelölő-lista a látszó
képeket tükrözi, a geocímke-törlés a kijelölésre hat, és a térkép hiánya
(QtLocation nélküli telepítés) nem viszi el sem a panelt, sem az appot.
"""

from PySide6.QtCore import QEventLoop, QObject, QTimer


def _settle(qt_app, rounds=3):
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(10, pause.quit)
        pause.exec()


class TestPlacesMenu:
    def test_menu_item_is_enabled_and_checkable(self, qml_app):
        window, controller, lib, engine = qml_app
        item = window.findChild(QObject, "menuViewPlaces")
        assert item is not None
        assert item.property("enabled") is True
        assert item.property("checkable") is True
        assert item.property("checked") is False

    def test_panel_hidden_by_default(self, qml_app):
        window, controller, lib, engine = qml_app
        panel = window.findChild(QObject, "placesPanel")
        assert panel is not None
        assert panel.property("visible") is False

    def test_panel_opens_from_the_window_state(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("placesPanelOpen", True)
        _settle(qt_app)
        assert window.findChild(QObject, "placesPanel").property("visible") is True
        assert window.findChild(QObject, "menuViewPlaces").property("checked") is True


class TestPlacesContent:
    def test_marker_count_label_follows_the_controller(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("placesPanelOpen", True)
        _settle(qt_app)
        label = window.findChild(QObject, "placesCountLabel")
        assert label is not None
        # a teszt-könyvtár képein nincs geocímke → nulla jelölő
        assert "0" in label.property("text")

    def test_markers_appear_after_geotagging(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("placesPanelOpen", True)
        controller.setGeotagRows([0], 47.5, 19.05)
        _settle(qt_app)
        assert controller.geoMarkerCount == 1
        panel = window.findChild(QObject, "placesPanel")
        assert len(panel.property("markers")) == 1

    def test_clear_button_needs_a_selection(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("placesPanelOpen", True)
        _settle(qt_app)
        button = window.findChild(QObject, "placesClearButton")
        assert button.property("enabled") is False
        window.setProperty("selectedIndexes", [0])
        _settle(qt_app, 1)
        assert button.property("enabled") is True

    def test_open_panel_either_shows_the_map_or_the_fallback(self, qml_app, qt_app):
        """A panel sosem marad üresen: vagy a térkép jön be, vagy — ha a
        QtLocation nincs telepítve — a magyarázó szöveg."""
        window, controller, lib, engine = qml_app
        window.setProperty("placesPanelOpen", True)
        _settle(qt_app)
        loader = window.findChild(QObject, "placesMapLoader")
        fallback = window.findChild(QObject, "placesFallbackText")
        assert loader.property("active") is True
        map_item = window.findChild(QObject, "placesMap")
        assert map_item is not None or fallback.property("visible") is True

    def test_map_loader_is_inactive_while_hidden(self, qml_app, qt_app):
        """Rejtett panel nem tölt térképet (és nem tölt le csempéket)."""
        window, controller, lib, engine = qml_app
        loader = window.findChild(QObject, "placesMapLoader")
        assert loader is not None
        assert loader.property("active") is False


class TestGeoFilterIcon:
    def test_icon_is_inert_without_geotagged_photos(self, qml_app):
        window, controller, lib, engine = qml_app
        icon = window.findChild(QObject, "geoFilter")
        assert icon is not None
        assert icon.property("ctlHasGeo") is False

    def test_icon_activates_with_geotagged_photos(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.setGeotagRows([0], 47.5, 19.05)
        _settle(qt_app, 1)
        assert window.findChild(QObject, "geoFilter").property("ctlHasGeo") is True

    def test_filter_shows_only_located_photos(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.setGeotagRows([0], 47.5, 19.05)
        controller.showGeotagged()
        _settle(qt_app, 1)
        assert controller.photos.rowCount() == 1
        assert controller.filterActive is True

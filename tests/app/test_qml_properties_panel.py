"""QML-funkcionális tesztek: Tulajdonságok-panel (#13, Alt+Enter).

A panel csak olvas: a kijelölt kép fájl- és EXIF-adatait mutatja; a
Nézet → Tulajdonságok menüpont és az Alt+Enter kapcsolja.
"""

from PySide6.QtCore import QObject


def _panel(window):
    panel = window.findChild(QObject, "propertiesPanel")
    assert panel is not None, "propertiesPanel nincs a Main.qml-ben"
    return panel


def _entries(panel) -> list:
    value = panel.property("entries")
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value or [])


class TestPropertiesPanelInMain:
    def test_hidden_by_default_and_toggles(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        panel = _panel(window)
        assert panel.property("visible") is False
        window.setProperty("propertiesPanelOpen", True)
        qt_app.processEvents()
        assert panel.property("visible") is True

    def test_menu_items_enabled(self, qml_app):
        window, controller, lib, engine = qml_app
        for name in ("menuViewProperties", "menuPictureProperties"):
            item = window.findChild(QObject, name)
            assert item is not None, name
            assert item.property("enabled") is True

    def test_entries_follow_selection(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("propertiesPanelOpen", True)
        panel = _panel(window)
        assert panel.property("hasSelection") is False
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        assert panel.property("hasSelection") is True
        entries = _entries(panel)
        values = {e["label"]: e["value"] for e in entries}
        assert values.get("File name") == "a.jpg"
        assert "File size" in values
        assert "Dimensions" in values

    def test_no_selection_empty_entries(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("propertiesPanelOpen", True)
        qt_app.processEvents()
        assert _entries(_panel(window)) == []

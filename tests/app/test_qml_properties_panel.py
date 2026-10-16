"""QML-funkcionális tesztek: Tulajdonságok-panel (#13, Alt+Enter).

A panel csak olvas: a kijelölt kép fájl- és EXIF-adatait mutatja; a
Nézet → Tulajdonságok menüpont és az Alt+Enter kapcsolja.
"""

from dataclasses import replace

from PySide6.QtCore import QDateTime, QLocale, QObject

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
        window.setProperty("activeDrawerTab", "properties")
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
        window.setProperty("activeDrawerTab", "properties")
        panel = _panel(window)
        assert panel.property("hasSelection") is False
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        assert panel.property("hasSelection") is True
        entries = _entries(panel)
        values = {e["label"]: e["value"] for e in entries}
        assert values.get("File Path", "").endswith("a.jpg")
        assert "File Size" in values
        assert "Dimensions" in values

    def test_no_selection_empty_entries(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("activeDrawerTab", "properties")
        qt_app.processEvents()
        assert _entries(_panel(window)) == []

    def test_taken_at_override_megjelenik_a_racs_adataban_es_a_tulajdonsagokban(
        self, qml_app, qt_app
    ):
        window, controller, _lib, _engine = qml_app
        eredeti = controller.photos.photos[0]
        felulirt = "2099-02-03T04:05:06"
        controller.photos.update_photo(
            eredeti.id,
            replace(
                eredeti,
                taken_at=felulirt,
                taken_at_override=felulirt,
            ),
        )
        row = controller.photos.row_of_id(eredeti.id)
        assert controller.photos.itemAt(row)["takenAt"] == felulirt

        window.setProperty("activeDrawerTab", "properties")
        window.setProperty("selectedIndexes", [row])
        window.setProperty("selectedIndex", row)
        qt_app.processEvents()
        values = [str(entry["value"]) for entry in _entries(_panel(window))]
        expected = QLocale().toString(
            QDateTime.fromString(felulirt, "yyyy-MM-ddTHH:mm:ss"),
            QLocale.FormatType.ShortFormat,
        )
        assert expected in values

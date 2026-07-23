"""QML-funkcionális tesztek: Gyorscímkék (#193) — a Címkék-panel alján
lévő 2×4 gombrács és a fogaskerék-ikon konfigurációs dialógusa.

A `qml_app` közös fixture-t használja (tests/app/conftest.py) — a
teljes Main.qml-t offscreen betöltve, valódi controller mögötte."""

from PySide6.QtCore import QMetaObject, QObject, Qt

from picasapy.metadata import read_file_metadata


def _invoke(obj, method) -> None:
    QMetaObject.invokeMethod(obj, method, Qt.ConnectionType.DirectConnection)


class TestQuickTagsGrid:
    def _panel(self, window):
        panel = window.findChild(QObject, "tagsPanel")
        assert panel is not None, "tagsPanel nincs a Main.qml-ben"
        return panel

    def test_eight_buttons_present(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        for i in range(8):
            button = window.findChild(QObject, f"quickTagButton{i}")
            assert button is not None, f"quickTagButton{i} hiányzik"

    def test_default_buttons_show_placeholder_and_are_disabled(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        button = window.findChild(QObject, "quickTagButton0")
        assert button.property("text") == "?"
        assert button.property("enabled") is False

    def test_click_configured_quick_tag_adds_to_selection(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.setQuickTagsReserveRecent(False)
        controller.setQuickTagLabel(3, "vitorlás")
        window.setProperty("tagsPanelOpen", True)
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        button = window.findChild(QObject, "quickTagButton3")
        assert button.property("text") == "vitorlás"
        assert button.property("enabled") is True
        _invoke(button, "clicked")
        qt_app.processEvents()
        assert read_file_metadata(lib / "a.jpg").keywords == ("vitorlás",)
        panel = self._panel(window)
        assert list(panel.property("tags")) == ["vitorlás"]

    def test_empty_quick_tag_button_disabled_even_with_selection(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        button = window.findChild(QObject, "quickTagButton7")
        assert button.property("text") == "?"
        assert button.property("enabled") is False

    def test_top_two_buttons_reflect_recently_used_tag_live(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        window.setProperty("selectedIndexes", [1])
        window.setProperty("selectedIndex", 1)
        qt_app.processEvents()
        controller.addKeywordToRows([1], "friss cimke")
        qt_app.processEvents()
        button = window.findChild(QObject, "quickTagButton0")
        assert button.property("text") == "friss cimke"


class TestQuickTagsConfigDialog:
    def _open_dialog(self, window, qt_app):
        gear = window.findChild(QObject, "quickTagsGearButton")
        assert gear is not None, "quickTagsGearButton hiányzik"
        dialog = window.findChild(QObject, "quickTagsConfigDialog")
        assert dialog is not None, "quickTagsConfigDialog hiányzik"
        _invoke(dialog, "open")
        qt_app.processEvents()
        return dialog

    def test_gear_click_opens_dialog(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        dialog = self._open_dialog(window, qt_app)
        assert dialog.property("visible") is True

    def test_dialog_shows_current_labels(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.setQuickTagLabel(4, "hegyek")
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        self._open_dialog(window, qt_app)
        field = window.findChild(QObject, "quickTagField4")
        assert field.property("text") == "hegyek"

    def test_editing_a_field_persists_to_controller(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        self._open_dialog(window, qt_app)
        field = window.findChild(QObject, "quickTagField5")
        field.setProperty("text", "tengerpart")
        _invoke(field, "editingFinished")
        qt_app.processEvents()
        assert controller.quickTagConfigLabels[5] == "tengerpart"

    def test_reserve_checkbox_default_checked_and_disables_top_two_fields(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        self._open_dialog(window, qt_app)
        checkbox = window.findChild(QObject, "quickTagsReserveRecentCheck")
        assert checkbox.property("checked") is True
        field0 = window.findChild(QObject, "quickTagField0")
        assert field0.property("enabled") is False

    def test_unchecking_reserve_persists_and_reenables_fields(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        self._open_dialog(window, qt_app)
        checkbox = window.findChild(QObject, "quickTagsReserveRecentCheck")
        checkbox.setProperty("checked", False)
        _invoke(checkbox, "toggled")
        qt_app.processEvents()
        assert controller.quickTagsReserveRecent is False
        field0 = window.findChild(QObject, "quickTagField0")
        assert field0.property("enabled") is True

    def test_autofill_checkbox_toggle_persists(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("tagsPanelOpen", True)
        qt_app.processEvents()
        self._open_dialog(window, qt_app)
        checkbox = window.findChild(QObject, "quickTagsAutoFillCheck")
        assert checkbox.property("checked") is False
        checkbox.setProperty("checked", True)
        _invoke(checkbox, "toggled")
        qt_app.processEvents()
        assert controller.quickTagsAutoFillFrequent is True

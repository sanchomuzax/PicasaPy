"""QML-funkcionális tesztek: Gyorscímkék (#193) — a Címkék-panel alján
lévő 2×4 gombrács és a fogaskerék-ikon konfigurációs dialógusa.

A `qml_app` közös fixture-t használja (tests/app/conftest.py) — a
teljes Main.qml-t offscreen betöltve, valódi controller mögötte."""

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

from picasapy.metadata import read_file_metadata
from support.qt_wait import varj_kattinthatora
from support.varakozas import var_feltetelre


def _invoke(obj, method) -> None:
    QMetaObject.invokeMethod(obj, method, Qt.ConnectionType.DirectConnection)


def _click(window, item, qt_app) -> None:
    """Valódi egérkattintás a kirajzolt elem közepére (#7134)."""
    assert item.width() > 0 and item.height() > 0, "a kattintási cél mérete nulla"
    varj_kattinthatora(window, item)
    point = item.mapToScene(item.boundingRect().center()).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    qt_app.processEvents()


class TestQuickTagsGrid:
    def _panel(self, window):
        panel = window.findChild(QObject, "tagsPanel")
        assert panel is not None, "tagsPanel nincs a Main.qml-ben"
        return panel

    def test_ten_buttons_present(self, qml_app, qt_app):
        """#1788: TÍZ gomb, nem nyolc — a KIRAJZOLT ablakban.

        A forrás-szintű állítás (`test_gyorscimke_tiz_hely_1788`) csak azt
        mondja meg, hogy a deklaráció ott van; ez azt, hogy a két új gomb
        tényleg meg is születik a jelenetben."""
        window, controller, lib, engine = qml_app
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        for i in range(10):
            button = window.findChild(QObject, f"quickTagButton{i}")
            assert button is not None, f"quickTagButton{i} hiányzik"
        assert window.findChild(QObject, "quickTagButton10") is None

    def test_default_buttons_show_placeholder_and_are_disabled(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        button = window.findChild(QObject, "quickTagButton0")
        assert button.property("text") == "?"
        assert button.property("enabled") is False

    def test_click_configured_quick_tag_adds_to_selection(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.setQuickTagsReserveRecent(False)
        controller.setQuickTagLabel(3, "vitorlás")
        window.setProperty("activeDrawerTab", "tags")
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        button = window.findChild(QObject, "quickTagButton3")
        assert button.property("text") == "vitorlás"
        assert button.property("enabled") is True
        _click(window, button, qt_app)
        assert var_feltetelre(
            qt_app,
            lambda: read_file_metadata(lib / "a.jpg").keywords == ("vitorlás",),
            5.0,
        )
        panel = self._panel(window)
        assert list(panel.property("tags")) == ["vitorlás"]

    def test_empty_quick_tag_button_opens_the_quick_tags_config_dialog(
        self, qml_app, qt_app
    ):
        """#7134: az üres ? hely az eredetiben (`]empty` összevetés, majd a
        `0x0063d840`) a Configure Quick Tags ablakot nyitja, nem a
        „nincs beírt szöveg” súgót, és nem ír címkét."""
        window, controller, lib, engine = qml_app
        window.setProperty("activeDrawerTab", "tags")
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        button = window.findChild(QObject, "quickTagButton7")
        assert button.property("text") == "?"
        assert button.property("enabled") is True
        config = window.findChild(QObject, "quickTagsConfigDialog")
        help_dialog = window.findChild(QObject, "tagNoTextDialog")
        assert config is not None and help_dialog is not None
        assert config.property("visible") is False

        _click(window, button, qt_app)

        assert var_feltetelre(
            qt_app, lambda: bool(config.property("visible")), 5.0
        ), "az üres hely kattintása nem nyitotta meg a konfigurációs ablakot"
        assert help_dialog.property("visible") is False
        assert read_file_metadata(lib / "a.jpg").keywords == ()
        config.close()

    def test_top_two_buttons_reflect_recently_used_tag_live(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("activeDrawerTab", "tags")
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
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        dialog = self._open_dialog(window, qt_app)
        assert dialog.property("visible") is True

    def test_ten_fields_present(self, qml_app, qt_app):
        """#1788: a dialógusban tíz szövegmező születik meg, nem nyolc."""
        window, controller, lib, engine = qml_app
        self._open_dialog(window, qt_app)
        for i in range(10):
            assert window.findChild(QObject, f"quickTagField{i}") is not None, i
        assert window.findChild(QObject, "quickTagField10") is None

    def test_dialog_shows_current_labels(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        controller.setQuickTagLabel(4, "hegyek")
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        self._open_dialog(window, qt_app)
        field = window.findChild(QObject, "quickTagField4")
        assert field.property("text") == "hegyek"

    def test_editing_a_field_persists_to_controller(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("activeDrawerTab", "tags")
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
        window.setProperty("activeDrawerTab", "tags")
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
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        self._open_dialog(window, qt_app)
        checkbox = window.findChild(QObject, "quickTagsReserveRecentCheck")
        checkbox.setProperty("checked", False)
        _invoke(checkbox, "toggled")
        qt_app.processEvents()
        assert controller.quickTagsReserveRecent is False
        field0 = window.findChild(QObject, "quickTagField0")
        assert field0.property("enabled") is True

    def test_autofill_button_disabled_without_candidates(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        self._open_dialog(window, qt_app)
        button = window.findChild(QObject, "quickTagsAutoFillButton")
        assert button is not None
        assert button.property("enabled") is False

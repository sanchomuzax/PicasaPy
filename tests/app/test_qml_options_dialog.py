"""#350: OptionsDialog.qml — önállóan betöltve, fake controllerrel és fake
`confirmSettings`-szel (a `test_qml_move_database.py` mintája). A Main.qml-be
illesztés (Eszközök → Beállítások... menüpont bekötése) az integrátoré."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, Qt, Signal, Slot


class FakeController(QObject):
    """A nyelvválasztáshoz szükséges felület (#333) — csak annyi, amennyit
    az OptionsDialog "General" füle ténylegesen használ."""

    languageChanged = Signal()

    def __init__(self, language="en"):
        super().__init__()
        self._language = language
        self.set_language_calls = []

    def _get_language(self):
        return self._language

    language = Property(str, _get_language, notify=languageChanged)

    def _get_available_languages(self):
        return ["en", "hu"]

    availableLanguages = Property(list, _get_available_languages, constant=True)

    @Slot(str)
    def setLanguage(self, code) -> None:
        self.set_language_calls.append(code)
        self._language = code
        self.languageChanged.emit()


class FakeConfirmSettings(QObject):
    """A #367-es confirmSettings bridge felülete."""

    def __init__(self, suppressed=None):
        super().__init__()
        self._suppressed = dict(suppressed or {})

    @Slot(str, result=bool)
    def isSuppressed(self, decision_key) -> bool:
        return self._suppressed.get(decision_key, False)

    @Slot(str, bool)
    def setSuppressed(self, decision_key, remember) -> None:
        self._suppressed[decision_key] = bool(remember)


@pytest.fixture
def fake_controller():
    return FakeController()


@pytest.fixture
def fake_confirm_settings():
    return FakeConfirmSettings()


@pytest.fixture
def dialog(qt_app, fake_controller, fake_confirm_settings):
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", fake_controller)
    engine.rootContext().setContextProperty("confirmSettings", fake_confirm_settings)
    factory = QQmlComponent(
        engine,
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "OptionsDialog.qml"),
    )
    item = factory.create()
    assert item is not None, factory.errorString()
    yield item, fake_controller, fake_confirm_settings, qt_app
    item.deleteLater()
    qt_app.processEvents()


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


TAB_OBJECT_NAMES = [
    "optionsTabGeneral",
    "optionsTabEmail",
    "optionsTabFileTypes",
    "optionsTabSlideshow",
    "optionsTabPrinting",
    "optionsTabNetwork",
    "optionsTabWebAlbums",
    "optionsTabNameTags",
]


class TestDialogWindow:
    def test_is_a_standalone_resizable_window(self, dialog):
        window, *_ = dialog
        assert window.property("minimumWidth") is not None
        assert window.property("minimumWidth") >= 400
        assert window.property("minimumHeight") is not None

    def test_starts_hidden(self, dialog):
        window, *_ = dialog
        assert window.property("visible") is False

    def test_open_makes_it_visible(self, dialog, qt_app):
        window, *_ = dialog
        from PySide6.QtCore import QMetaObject

        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert window.property("visible") is True

    def test_close_button_hides_the_window(self, dialog, qt_app):
        window, *_ = dialog
        window.setProperty("visible", True)
        qt_app.processEvents()
        close_button = _child(window, "optionsCloseButton")
        close_button.clicked.emit()
        qt_app.processEvents()
        assert window.property("visible") is False


class TestTabStructure:
    """A `options.fen` 8, dokumentált fülének megléte és sorrendje
    (docs/specs/picasa-fen-dialogs.md 3.11. szak.)."""

    def test_has_eight_tabs(self, dialog):
        window, *_ = dialog
        tab_bar = _child(window, "optionsTabBar")
        assert tab_bar.property("count") == len(TAB_OBJECT_NAMES)

    @pytest.mark.parametrize("name", TAB_OBJECT_NAMES)
    def test_each_tab_button_exists(self, dialog, name):
        window, *_ = dialog
        _child(window, name)

    def test_stack_switches_with_tab_bar(self, dialog, qt_app):
        window, *_ = dialog
        tab_bar = _child(window, "optionsTabBar")
        stack = _child(window, "optionsTabStack")
        tab_bar.setProperty("currentIndex", 2)
        qt_app.processEvents()
        assert stack.property("currentIndex") == 2


class TestGeneralTabLiveLanguage:
    """A nyelvválasztás (#333) az OptionsDialogból is elérhető — ugyanaz a
    controller.language/setLanguage, mint az Eszközök → Nyelv menüben."""

    def test_combo_reflects_current_language(self, dialog):
        window, fake_controller, _cs, _qt = dialog
        combo = _child(window, "optionsLanguageCombo")
        assert combo.property("currentIndex") == 0  # "en"

    def test_combo_reflects_hungarian(self, qt_app, fake_confirm_settings):
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        controller = FakeController(language="hu")
        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", controller)
        engine.rootContext().setContextProperty(
            "confirmSettings", fake_confirm_settings
        )
        factory = QQmlComponent(
            engine,
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "OptionsDialog.qml"),
        )
        item = factory.create()
        assert item is not None, factory.errorString()
        combo = _child(item, "optionsLanguageCombo")
        assert combo.property("currentIndex") == 1  # "hu"
        item.deleteLater()
        qt_app.processEvents()

    def test_choosing_a_language_calls_controller(self, dialog, qt_app):
        window, fake_controller, _cs, _qt = dialog
        combo = _child(window, "optionsLanguageCombo")
        combo.activated.emit(1)
        qt_app.processEvents()
        assert fake_controller.set_language_calls == ["hu"]


class TestGeneralTabLiveDeleteConfirmSuppression:
    """A "Törlés a lemezről megerősítés nélkül" checkbox a #367-es
    confirmSettings "delete" döntés-kulcsát olvassa/írja — ugyanazt, amit
    a FileOpsDialogs ConfirmDialog-ja használ."""

    def test_unchecked_by_default(self, dialog):
        window, *_ = dialog
        checkbox = _child(window, "optionsSkipDeleteConfirmCheck")
        assert checkbox.property("checked") is False

    def test_reflects_already_suppressed_state(
        self, qt_app, fake_controller
    ):
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        confirm_settings = FakeConfirmSettings(suppressed={"delete": True})
        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", fake_controller)
        engine.rootContext().setContextProperty("confirmSettings", confirm_settings)
        factory = QQmlComponent(
            engine,
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "OptionsDialog.qml"),
        )
        item = factory.create()
        assert item is not None, factory.errorString()
        checkbox = _child(item, "optionsSkipDeleteConfirmCheck")
        assert checkbox.property("checked") is True
        item.deleteLater()
        qt_app.processEvents()

    def test_toggling_writes_through_to_confirm_settings(self, dialog, qt_app):
        window, _fc, fake_confirm_settings, _qt = dialog
        checkbox = _child(window, "optionsSkipDeleteConfirmCheck")
        checkbox.setProperty("checked", True)
        checkbox.toggled.emit()
        qt_app.processEvents()
        assert fake_confirm_settings.isSuppressed("delete") is True


class TestPlaceholderTabsAreDisabled:
    """A funkció nélküli fülek gyökér-tartalma tiltott — a struktúra a
    FEN-paritás kedvéért él, de nem sugall működést. Egy-egy jellemző
    vezérlőn ellenőrizzük (a `Rectangle.enabled` a QtQuick-ben lefelé
    öröklődik, de a `.property("enabled")` a saját effektív értéket adja,
    ezért az egyes gyökér-ColumnLayoutokon kérdezzük le)."""

    @pytest.mark.parametrize(
        "control_name",
        [
            "optionsMailDefaultRadio",
            "optionsFileTypeBmpCheck",
            "optionsSlideshowLoopCheck",
            "optionsPrintHiResPreviewCheck",
            "optionsNetworkAutoDetectCheck",
            "optionsWebStripedUploadCheck",
            "optionsFaceDetectionCheck",
        ],
    )
    def test_placeholder_control_disabled(self, dialog, control_name):
        window, *_ = dialog
        control = _child(window, control_name)
        assert control.property("enabled") is False

    @pytest.mark.parametrize(
        "control_name",
        [
            "optionsUiTransitionsCheck",
            "optionsShowTooltipsCheck",
            "optionsSingleClickExitCheck",
            "optionsAutoExcludeCheck",
            "optionsClearCacheButton",
            "optionsSkipRemoveConfirmCheck",
            "optionsUsageStatsCheck",
        ],
    )
    def test_general_tab_placeholder_controls_disabled(self, dialog, control_name):
        """A General fülön is csak a nyelv + törlés-megerősítés élő —
        a többi vezérlő ott is tiltott."""
        window, *_ = dialog
        control = _child(window, control_name)
        assert control.property("enabled") is False

    def test_general_tab_live_controls_are_enabled(self, dialog):
        window, *_ = dialog
        assert _child(window, "optionsLanguageCombo").property("enabled") is True
        assert (
            _child(window, "optionsSkipDeleteConfirmCheck").property("enabled")
            is True
        )

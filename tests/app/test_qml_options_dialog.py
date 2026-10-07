"""#350: OptionsDialog.qml — önállóan betöltve, fake controllerrel és fake
`confirmSettings`-szel (a `test_qml_move_database.py` mintája). A Main.qml-be
illesztés (Eszközök → Beállítások... menüpont bekötése) az integrátoré."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    Property,
    QObject,
    QPoint,
    QPointF,
    QSettings,
    QTranslator,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtTest import QTest

from picasapy.app.language_controller import OWN_LANGUAGE_NAMES
from picasapy.app.filetype_preferences import (
    file_type_enabled,
    set_file_type_enabled,
)


class FakeController(QObject):
    """A nyelvválasztáshoz szükséges felület (#333/#3555) — csak annyi,
    amennyit az OptionsDialog "General" füle ténylegesen használ.

    #3555: a `setLanguage` a valódi vezérlőhöz hasonlóan CSAK a
    `pendingLanguage`-et írja — a `language` (a futó felület nyelve) a
    következő indításig nem változik."""

    languageChanged = Signal()
    pendingLanguageChanged = Signal()
    uiTransitionsEnabledChanged = Signal()
    showTooltipsEnabledChanged = Signal()
    singleClickExitEnabledChanged = Signal()

    _OWN_NAMES = OWN_LANGUAGE_NAMES

    def __init__(self, language="en", pending_language=None, filetype_settings=None):
        super().__init__()
        self._language = language
        self._pending_language = pending_language if pending_language is not None else language
        self.set_language_calls = []
        self._filetype_settings = (
            filetype_settings or QSettings("PicasaPy", "PicasaPy")
        )
        self._ui_transitions_enabled = True
        self._show_tooltips_enabled = True
        self._single_click_exit_enabled = False

    def _get_language(self):
        return self._language

    language = Property(str, _get_language, notify=languageChanged)

    def _get_pending_language(self):
        return self._pending_language

    pendingLanguage = Property(str, _get_pending_language, notify=pendingLanguageChanged)

    uiTransitionsEnabled = Property(
        bool,
        lambda self: self._ui_transitions_enabled,
        notify=uiTransitionsEnabledChanged,
    )
    showTooltipsEnabled = Property(
        bool,
        lambda self: self._show_tooltips_enabled,
        notify=showTooltipsEnabledChanged,
    )
    singleClickExitEnabled = Property(
        bool,
        lambda self: self._single_click_exit_enabled,
        notify=singleClickExitEnabledChanged,
    )

    def _get_available_languages(self):
        return ["en", "hu"]

    availableLanguages = Property(list, _get_available_languages, constant=True)

    systemLanguageCode = Property(str, lambda self: "system", constant=True)
    systemLanguageSuffix = Property(str, lambda self: "hu-HU", constant=True)

    @Slot(str, result=str)
    def ownLanguageName(self, code) -> str:
        return self._OWN_NAMES.get(code, code)

    @Slot(str)
    def setLanguage(self, code) -> None:
        self.set_language_calls.append(code)
        self._pending_language = code
        self.pendingLanguageChanged.emit()

    @Slot(str, result=bool)
    def fileTypeEnabled(self, group) -> bool:
        return file_type_enabled(self._filetype_settings, group)

    @Slot(str, bool)
    def setFileTypeEnabled(self, group, enabled) -> None:
        set_file_type_enabled(self._filetype_settings, group, enabled)
    @Slot(bool)
    def setUITransitionsEnabled(self, enabled) -> None:
        self._ui_transitions_enabled = bool(enabled)
        self.uiTransitionsEnabledChanged.emit()

    @Slot(bool)
    def setShowTooltipsEnabled(self, enabled) -> None:
        self._show_tooltips_enabled = bool(enabled)
        self.showTooltipsEnabledChanged.emit()

    @Slot(bool)
    def setSingleClickExitEnabled(self, enabled) -> None:
        self._single_click_exit_enabled = bool(enabled)
        self.singleClickExitEnabledChanged.emit()


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


class FakeFaceScanController(QObject):
    def __init__(self, enabled=True):
        super().__init__()
        self.enabled = enabled
        self.calls = []
        self.suggestions_enabled = True
        self.suggestion_threshold = 85
        self.cluster_threshold = 70
        self.persist_face_to_file = True
        self.setting_calls = []

    @Slot(result=bool)
    def automaticDetectionEnabled(self):
        return self.enabled

    @Slot(bool)
    def setAutomaticDetectionEnabled(self, enabled):
        self.calls.append(enabled)
        self.enabled = enabled

    @Slot(result=bool)
    def suggestionsEnabled(self):
        return self.suggestions_enabled

    @Slot(bool)
    def setSuggestionsEnabled(self, enabled):
        self.setting_calls.append(("suggestions", enabled))
        self.suggestions_enabled = enabled

    @Slot(result=int)
    def suggestionThreshold(self):
        return self.suggestion_threshold

    @Slot(int)
    def setSuggestionThreshold(self, value):
        self.setting_calls.append(("suggestionThreshold", value))
        self.suggestion_threshold = value

    @Slot(result=int)
    def clusterThreshold(self):
        return self.cluster_threshold

    @Slot(int)
    def setClusterThreshold(self, value):
        self.setting_calls.append(("clusterThreshold", value))
        self.cluster_threshold = value

    @Slot(result=bool)
    def persistFaceToFile(self):
        return self.persist_face_to_file

    @Slot(bool)
    def setPersistFaceToFile(self, enabled):
        self.setting_calls.append(("persistFaceToFile", enabled))
        self.persist_face_to_file = enabled


class FakeEmailController(QObject):
    """A #32-es EmailController QML-felülete — a valódi
    `email_controller.py` ugyanezt a property/slot-készletet exportálja.

    #2020: a méret KÉPPONT (`emailSize`), az „egy kép" pedig KAPCSOLÓ
    (`singlePictureOriginal`), nem második méret-csúszka.
    """

    emailSizeChanged = Signal()
    singlePictureOriginalChanged = Signal()
    useDefaultClientChanged = Signal()
    movieFullChanged = Signal()

    def __init__(
        self, size=480, single_original=False, use_default=True, movie_full=False
    ):
        super().__init__()
        self._size = size
        self._single_original = single_original
        self._use_default = use_default
        self._movie_full = movie_full
        self.set_size_calls = []
        self.set_single_calls = []
        self.set_use_default_calls = []
        self.set_movie_calls = []

    emailSize = Property(int, lambda self: self._size, notify=emailSizeChanged)
    singlePictureOriginal = Property(
        bool, lambda self: self._single_original,
        notify=singlePictureOriginalChanged,
    )
    useDefaultClient = Property(
        bool, lambda self: self._use_default, notify=useDefaultClientChanged
    )
    movieFull = Property(
        bool, lambda self: self._movie_full, notify=movieFullChanged
    )

    @Slot(int)
    def setEmailSize(self, size_px) -> None:
        self.set_size_calls.append(size_px)
        self._size = size_px
        self.emailSizeChanged.emit()

    @Slot(bool)
    def setSinglePictureOriginal(self, eredeti) -> None:
        self.set_single_calls.append(eredeti)
        self._single_original = eredeti
        self.singlePictureOriginalChanged.emit()

    @Slot(bool)
    def setUseDefaultClient(self, use_default) -> None:
        self.set_use_default_calls.append(use_default)
        self._use_default = use_default
        self.useDefaultClientChanged.emit()

    @Slot(bool)
    def setMovieFull(self, movie_full) -> None:
        self.set_movie_calls.append(movie_full)
        self._movie_full = movie_full
        self.movieFullChanged.emit()


class FakeImportSourceController(QObject):
    """#2893: az `ImportSourceController` autoExclude-szelete.

    A valódi vezérlő ugyanezt a property/slot-párt exportálja, és az
    `import/autoexclude` QSettings-kulcsba ír — a Beállítások jelölője és az
    importáló párbeszéd jelölője EZEN az egy állapoton osztozik."""

    autoExcludeChanged = Signal()

    def __init__(self, auto_exclude=False):
        super().__init__()
        self._auto_exclude = auto_exclude
        self.set_calls = []

    autoExclude = Property(
        bool, lambda self: self._auto_exclude, notify=autoExcludeChanged
    )

    @Slot(bool)
    def setAutoExclude(self, value) -> None:  # noqa: N802 — QML-konvenció
        self.set_calls.append(value)
        self._auto_exclude = value
        self.autoExcludeChanged.emit()


@pytest.fixture
def fake_import_source_controller():
    return FakeImportSourceController()


@pytest.fixture
def fake_controller(tmp_path):
    settings = QSettings(
        str(tmp_path / "options.ini"), QSettings.Format.IniFormat
    )
    return FakeController(filetype_settings=settings)


@pytest.fixture
def fake_email_controller():
    return FakeEmailController()


@pytest.fixture
def fake_confirm_settings():
    return FakeConfirmSettings()


@pytest.fixture
def fake_face_scan_controller():
    return FakeFaceScanController()


@pytest.fixture
def dialog(
    qt_app, fake_controller, fake_confirm_settings, fake_face_scan_controller
):
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", fake_controller)
    engine.rootContext().setContextProperty("confirmSettings", fake_confirm_settings)
    engine.rootContext().setContextProperty(
        "faceScanController", fake_face_scan_controller
    )
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


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(window, qt_app, elem) -> None:
    """Valódi bal kattintás a vezérlő KÖZEPÉRE (jelenet-koordinátában)."""
    assert _var(qt_app, lambda: elem.width() > 0 and elem.height() > 0), (
        f"{elem.objectName()}: nincs mérete, nem kattintható"
    )
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _csuszkara_kattint(window, qt_app, slider, value) -> None:
    """A csúszka tényleges fogantyúútjából számolt pontra kattint."""
    assert _var(qt_app, lambda: slider.width() > 0 and slider.height() > 0)
    handle = slider.property("handle")
    assert handle is not None, f"{slider.objectName()}: nincs fogantyú"
    fraction = (value - slider.property("from")) / (
        slider.property("to") - slider.property("from")
    )
    x = (
        slider.property("leftPadding")
        + handle.width() / 2
        + fraction * (slider.property("availableWidth") - handle.width())
    )
    point = slider.mapToScene(QPointF(x, slider.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
    qt_app.processEvents()


def _csuszkahuzas(window, qt_app, slider, value) -> None:
    """Valódi fogantyúhúzás a vezérlő pillanatnyi geometriájából számolva."""
    assert _var(qt_app, lambda: slider.width() > 0 and slider.height() > 0)
    handle = slider.property("handle")
    assert handle is not None, f"{slider.objectName()}: nincs fogantyú"
    start = slider.mapToScene(
        QPointF(handle.x() + handle.width() / 2, handle.y() + handle.height() / 2)
    ).toPoint()
    fraction = (value - slider.property("from")) / (
        slider.property("to") - slider.property("from")
    )
    target_x = (
        slider.property("leftPadding")
        + handle.width() / 2
        + fraction * (slider.property("availableWidth") - handle.width())
    )
    target = slider.mapToScene(QPointF(target_x, slider.height() / 2)).toPoint()
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    QTest.mouseMove(window, target)
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, target
    )
    qt_app.processEvents()


def _lathato_sorok(window):
    """A nyitott legördülő LÁTHATÓ sorai, fentről lefelé. (A sor saját
    `text`-je üres — a feliratot a belső `Text` rajzolja —, ezért a sorrend
    azonosít: a modell sorrendje.)"""
    sorok = []
    sor = [window.contentItem().parentItem() or window.contentItem()]
    while sor:
        elem = sor.pop()
        if elem.isVisible() and "ItemDelegate" in elem.metaObject().className():
            sorok.append(elem)
        sor.extend(elem.childItems())
    return sorted(sorok, key=lambda e: e.mapToScene(QPointF(0, 0)).y())


def _nyelvet_valaszt(window, qt_app, felirat) -> None:
    """A Beállítások ablak nyelv-legördülőjének lenyitása és a `felirat`
    sorának kiválasztása — mindkettő KATTINTÁS."""
    window.setProperty("visible", True)
    assert _var(qt_app, lambda: window.isExposed()), "a Beállítások ablak nem jelent meg"
    combo = _child(window, "optionsLanguageCombo")
    modell = combo.property("model")
    assert felirat in modell, f"„{felirat}” nincs a listában: {modell}"
    _kattints(window, qt_app, combo)
    assert _var(qt_app, lambda: len(_lathato_sorok(window)) == len(modell)), (
        "a legördülő lista nem nyílt le"
    )
    _kattints(window, qt_app, _lathato_sorok(window)[modell.index(felirat)])


def _kerdes_nyitva(window) -> bool:
    return _child(window, "optionsLanguageConfirmDialog").property("opened") is True


def _valaszol(window, qt_app, *, igen: bool) -> None:
    assert _var(qt_app, lambda: _kerdes_nyitva(window)), "a megerősítő kérdés nem nyílt meg"
    gomb = "optionsLanguageConfirmYesButton" if igen else "optionsLanguageConfirmNoButton"
    _kattints(window, qt_app, _child(window, gomb))
    assert _var(qt_app, lambda: not _kerdes_nyitva(window)), "a kérdés nyitva maradt"


class TestGeneralTabLiveLanguage:
    """A nyelvválasztás (#333/#3555) az OptionsDialogból is elérhető —
    ugyanaz a controller.pendingLanguage/setLanguage, mint az Eszközök →
    Nyelv menüben. A lista első tétele a rendszer szerinti (spec A szakasz);
    a `currentIndex` a FÜGGŐ (nem a mai) nyelvet tükrözi (spec D szakasz), és
    a váltás csak a megerősítő kérdés UTÁN íródik.

    ⚠️ A legördülőre, a sorára és a kérdés gombjaira VALÓDI egérkattintás
    megy — a jel kibocsátása a néma bekötési hibát nem fogná meg."""

    def test_combo_lists_system_first(self, dialog):
        window, _fc, _cs, _qt = dialog
        combo = _child(window, "optionsLanguageCombo")
        assert combo.property("model") == [
            "System Default (hu-HU)", "English (US)", "Magyar",
        ]

    def test_combo_reflects_current_language(self, dialog):
        window, _fc, _cs, _qt = dialog
        combo = _child(window, "optionsLanguageCombo")
        assert combo.property("currentIndex") == 1  # "en"

    def test_combo_reflects_hungarian(self, qt_app, fake_confirm_settings):
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        controller = FakeController(language="hu", pending_language="hu")
        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", controller)
        engine.rootContext().setContextProperty("confirmSettings", fake_confirm_settings)
        factory = QQmlComponent(
            engine,
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "OptionsDialog.qml"),
        )
        item = factory.create()
        assert item is not None, factory.errorString()
        combo = _child(item, "optionsLanguageCombo")
        assert combo.property("currentIndex") == 2  # "hu"
        item.deleteLater()
        qt_app.processEvents()

    def test_choosing_a_language_asks_for_confirmation_first(self, dialog, qt_app):
        window, fake_controller, _cs, _qt = dialog
        _nyelvet_valaszt(window, qt_app, "Magyar")
        assert _var(qt_app, lambda: _kerdes_nyitva(window)), "a kérdés nem nyílt meg"
        assert fake_controller.set_language_calls == [], (
            "#3555: a váltás csak a megerősítés UTÁN íródhat"
        )
        uzenet = _child(window, "optionsLanguageConfirmMessageLabel").property("text")
        assert uzenet.startswith("Change the language Picasa uses?")

    def test_yes_click_calls_the_controller(self, dialog, qt_app):
        window, fake_controller, _cs, _qt = dialog
        _nyelvet_valaszt(window, qt_app, "Magyar")
        _valaszol(window, qt_app, igen=True)
        assert fake_controller.set_language_calls == ["hu"]
        assert _child(window, "optionsLanguageCombo").property("currentIndex") == 2

    def test_no_click_leaves_the_controller_untouched(self, dialog, qt_app):
        window, fake_controller, _cs, _qt = dialog
        _nyelvet_valaszt(window, qt_app, "Magyar")
        _valaszol(window, qt_app, igen=False)
        assert fake_controller.set_language_calls == []
        assert _child(window, "optionsLanguageCombo").property("currentIndex") == 1

    def test_choosing_the_already_pending_language_asks_nothing(self, dialog, qt_app):
        window, fake_controller, _cs, _qt = dialog
        _nyelvet_valaszt(window, qt_app, "English (US)")  # már "en"
        qt_app.processEvents()
        assert fake_controller.set_language_calls == []
        assert not _kerdes_nyitva(window)


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


class TestGeneralTabLiveRemoveFromAlbumConfirmSuppression:
    """#3539: a "Eltávolítás az albumból megerősítés nélkül" checkbox a
    confirmSettings "removeFromAlbum" döntés-kulcsát olvassa/írja — ugyanaz
    a kulcs, amit a Main.qml album-eltávolító ConfirmDialog-ja használ."""

    def test_unchecked_by_default(self, dialog):
        window, *_ = dialog
        checkbox = _child(window, "optionsSkipRemoveConfirmCheck")
        assert checkbox.property("checked") is False

    def test_reflects_already_suppressed_state(
        self, qt_app, fake_controller
    ):
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        confirm_settings = FakeConfirmSettings(suppressed={"removeFromAlbum": True})
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
        checkbox = _child(item, "optionsSkipRemoveConfirmCheck")
        assert checkbox.property("checked") is True
        item.deleteLater()
        qt_app.processEvents()

    def test_toggling_writes_through_to_confirm_settings(self, dialog, qt_app):
        window, _fc, fake_confirm_settings, _qt = dialog
        checkbox = _child(window, "optionsSkipRemoveConfirmCheck")
        checkbox.setProperty("checked", True)
        checkbox.toggled.emit()
        qt_app.processEvents()
        assert fake_confirm_settings.isSuppressed("removeFromAlbum") is True


class TestPlaceholderTabsAreDisabled:
    """A funkció nélküli fülek gyökér-tartalma tiltott — a struktúra a
    FEN-paritás kedvéért él, de nem sugall működést. Egy-egy jellemző
    vezérlőn ellenőrizzük (a `Rectangle.enabled` a QtQuick-ben lefelé
    öröklődik, de a `.property("enabled")` a saját effektív értéket adja,
    ezért az egyes gyökér-ColumnLayoutokon kérdezzük le)."""

    @pytest.mark.parametrize(
        "control_name",
        [
            # #4451: a videómód az EmailControllerhez kötve él; vezérlő
            # nélkül a két rádiógomb letiltva marad.
            "optionsMailMovieFirstFrameRadio",
            "optionsMailMovieFullRadio",
            "optionsMailUseHtmlCheck",
            "optionsNetworkAutoDetectCheck",
            "optionsWebStripedUploadCheck",
        ],
    )
    def test_placeholder_control_disabled(self, dialog, control_name):
        window, *_ = dialog
        control = _child(window, control_name)
        assert control.property("enabled") is False


class TestSlideshowTab:
    def test_preferences_are_live_and_music_folder_follows_checkbox(self, dialog):
        window, *_ = dialog
        loop = _child(window, "optionsSlideshowLoopCheck")
        music = _child(window, "optionsSlideshowPlayMusicCheck")
        browse = _child(window, "optionsSlideshowMusicBrowseButton")

        # #4377: a vezérlő nélküli QML-alapértékek a binárisból igazolt
        # LoopSlideshow=0 és PlayMP3Tracks=1 értékeket követik.
        assert loop.property("enabled") is True
        assert loop.property("checked") is False
        assert music.property("enabled") is True
        assert music.property("checked") is True
        assert browse.property("enabled") is True


class TestFileTypesTab:
    @pytest.mark.parametrize("height_offset", [-5, 0, 5])
    def test_kattintas_utan_ujraolvasasbol_kikerul_a_kikapcsolt_tipus(
        self, dialog, qt_app, tmp_path, height_offset
    ):
        from picasapy.index import open_index, sync_tree
        from support.jpeg_factory import make_jpeg

        window, controller, *_ = dialog
        window.setHeight(window.height() + height_offset)
        window.setProperty("visible", True)
        assert _var(qt_app, lambda: window.isExposed())

        root = tmp_path / "kepek"
        folder = root / "nyaralas"
        folder.mkdir(parents=True)
        make_jpeg(folder / "kep.jpg", size=(12, 8))
        (folder / "kep.cr2").write_bytes(b"raw-data")
        ini = folder / ".picasa.ini"
        ini_tartalom = "[kep.jpg]\nstar=yes\n[kep.cr2]\ncaption=megmarad\n"
        ini.write_text(ini_tartalom, encoding="utf-8")
        adatbazis = tmp_path / "index.db"
        with open_index(adatbazis) as conn:
            sync_tree(conn, root, incremental=False)
            kezdeti_nevek = {
                sor["name"]
                for sor in conn.execute("SELECT name FROM photos").fetchall()
            }
        assert kezdeti_nevek == {"kep.jpg", "kep.cr2"}

        _kattints(window, qt_app, _child(window, "optionsTabFileTypes"))
        assert _var(
            qt_app, lambda: _child(window, "optionsTabStack").property("currentIndex") == 2
        )
        raw = _child(window, "optionsFileTypeRawCheck")
        assert raw.property("enabled") is True
        assert raw.property("checked") is True
        assert controller.fileTypeEnabled("gif") is True
        assert controller.fileTypeEnabled("png") is True
        for object_name in (
            "optionsFileTypeBmpCheck",
            "optionsFileTypeGifCheck",
            "optionsFileTypePngCheck",
            "optionsFileTypeTgaCheck",
            "optionsFileTypeTiffCheck",
            "optionsFileTypeWebpCheck",
            "optionsFileTypePsdCheck",
            "optionsFileTypeMoviesCheck",
            "optionsFileTypeQuickTimeCheck",
        ):
            assert _child(window, object_name).property("enabled") is True
        _kattints(window, qt_app, raw)

        assert raw.property("checked") is False
        assert controller.fileTypeEnabled("raw") is False
        controller._filetype_settings.sync()
        reopened_settings = QSettings(
            controller._filetype_settings.fileName(),
            controller._filetype_settings.format(),
        )
        assert FakeController(filetype_settings=reopened_settings).fileTypeEnabled(
            "raw"
        ) is False
        from picasapy.scanner.filetypes import FILETYPE_GROUPS

        enabled = {
            group for group in FILETYPE_GROUPS if controller.fileTypeEnabled(group)
        }
        with open_index(adatbazis) as conn:
            sync_tree(conn, root, incremental=False, enabled_filetypes=enabled)
            uj_nevek = {
                sor["name"]
                for sor in conn.execute("SELECT name FROM photos").fetchall()
            }

        assert uj_nevek == {"kep.jpg"}
        assert ini.read_text(encoding="utf-8") == ini_tartalom
        if height_offset == 0:
            screenshot = window.grabWindow()
            evidence = Path(__file__).resolve().parents[2] / ".bt" / "4447-filetypes.png"
            evidence.parent.mkdir(parents=True, exist_ok=True)
            assert screenshot.save(str(evidence))


class TestFaceDetectionOption:
    @pytest.mark.parametrize("height_offset", [-5, 0, 5])
    def test_face_detection_setting_is_live(self, dialog, qt_app, height_offset):
        from PySide6.QtQml import QQmlEngine

        window, *_ = dialog
        window.setHeight(window.height() + height_offset)
        window.setProperty("visible", True)
        assert _var(qt_app, lambda: window.isExposed()), "a Beállítások ablak nem jelent meg"
        _child(window, "optionsTabBar").setProperty("currentIndex", 7)
        assert _var(
            qt_app,
            lambda: _child(window, "optionsFaceDetectionCheck").isVisible(),
        ), "a Névcímkék fül nem jelent meg"
        qt_app.processEvents()
        checkbox = _child(window, "optionsFaceDetectionCheck")
        face_controller = QQmlEngine.contextForObject(window).contextProperty(
            "faceScanController"
        )

        assert checkbox.property("enabled") is True
        assert checkbox.property("checked") is True

        _kattints(window, qt_app, checkbox)

        assert face_controller.calls == [False]
        assert face_controller.enabled is False

    @pytest.mark.parametrize("height_offset", [-5, 0, 5])
    def test_name_tag_settings_respond_to_real_clicks(
        self, dialog, qt_app, height_offset
    ):
        from PySide6.QtQml import QQmlEngine

        window, *_ = dialog
        window.setHeight(window.height() + height_offset)
        window.setProperty("visible", True)
        assert _var(qt_app, lambda: window.isExposed()), "a Beállítások ablak nem jelent meg"
        _child(window, "optionsTabBar").setProperty("currentIndex", 7)
        assert _var(
            qt_app,
            lambda: _child(window, "optionsFaceSuggestionsCheck").isVisible(),
        ), "a Névcímkék fül nem jelent meg"
        controller = QQmlEngine.contextForObject(window).contextProperty(
            "faceScanController"
        )
        suggestions = _child(window, "optionsFaceSuggestionsCheck")
        suggestion_slider = _child(window, "optionsFaceSuggestionThresholdSlider")
        cluster_slider = _child(window, "optionsFaceClusterThresholdSlider")
        persist = _child(window, "optionsFacePersistToFileCheck")
        suggestion_value = _child(window, "optionsFaceSuggestionThresholdValue")
        cluster_value = _child(window, "optionsFaceClusterThresholdValue")
        suggestion_ticks = _child(window, "optionsFaceSuggestionThresholdTicks")
        cluster_ticks = _child(window, "optionsFaceClusterThresholdTicks")
        suggestion_label = _child(window, "optionsFaceSuggestionThresholdLabel")
        cluster_label = _child(window, "optionsFaceClusterThresholdLabel")
        content = _child(window, "optionsNameTagsControls")
        stack = _child(window, "optionsTabStack")
        contact_upload = _child(window, "optionsFaceUploadContactPhotosCheck")
        assert contact_upload.property("visible") is False

        assert suggestions.property("enabled") is True
        assert suggestions.property("checked") is True
        assert suggestion_slider.property("value") == 85
        assert cluster_slider.property("value") == 70
        assert suggestion_value.property("text") == "85"
        assert cluster_value.property("text") == "70"
        assert suggestion_ticks.property("tickCount") == 10
        assert cluster_ticks.property("tickCount") == 10
        assert persist.property("checked") is True

        # A referencia kb. 434 px-es középre tett vezérlőcsoportot mutat;
        # a saját elemgeometriát mérjük, a képernyőképhez ±3 px-et engedve.
        assert abs(content.width() - 434) <= 3
        content_origin = content.mapToItem(stack, QPointF(0, 0))
        assert abs(
            content_origin.x() + content.width() / 2 - stack.width() / 2
        ) <= 3
        assert abs(content_origin.y() - 8) <= 3
        assert abs(suggestion_slider.width() - 297) <= 3
        assert abs(cluster_slider.width() - 297) <= 3
        suggestion_center = suggestion_slider.mapToItem(
            stack, QPointF(suggestion_slider.width() / 2, suggestion_slider.height() / 2)
        )
        cluster_center = cluster_slider.mapToItem(
            stack, QPointF(cluster_slider.width() / 2, cluster_slider.height() / 2)
        )
        detection_center = _child(window, "optionsFaceDetectionCheck").mapToItem(
            stack, QPointF(0, _child(window, "optionsFaceDetectionCheck").height() / 2)
        )
        suggestions_center = suggestions.mapToItem(
            stack, QPointF(0, suggestions.height() / 2)
        )
        persist_center = persist.mapToItem(
            stack, QPointF(0, persist.height() / 2)
        )
        assert abs(suggestions_center.y() - detection_center.y() - 22) <= 3
        assert abs(suggestion_center.y() - suggestions_center.y() - 24) <= 3
        assert abs(
            cluster_center.y() - suggestion_center.y()
            - 41
        ) <= 3
        assert abs(persist_center.y() - cluster_center.y() - 39) <= 3
        for label, slider in (
            (suggestion_label, suggestion_slider),
            (cluster_label, cluster_slider),
        ):
            assert label.property("rightAligned") is True
            label_right = label.mapToItem(
                stack, QPointF(label.width(), 0)
            ).x()
            slider_left = slider.mapToItem(stack, QPointF(0, 0)).x()
            assert abs(slider_left - label_right - 8) <= 2

        rendered = window.grabWindow()
        assert not rendered.isNull(), "a fül nem rajzolódott ki"
        dpr = rendered.devicePixelRatio()
        for ticks, _slider, tick_prefix in (
            (suggestion_ticks, suggestion_slider, "optionsFaceSuggestionTick"),
            (cluster_ticks, cluster_slider, "optionsFaceClusterTick"),
        ):
            marks = [
                item for item in ticks.childItems()
                if item.objectName().startswith(tick_prefix)
            ]
            assert len(marks) == 10
            mark_centers = [item.x() + item.width() / 2 for item in marks]
            assert abs(mark_centers[-1] - mark_centers[0] - 287) <= 3
            assert all(
                abs((right - left) - 32) <= 3
                for left, right in zip(mark_centers, mark_centers[1:], strict=False)
            )
            for mark in marks:
                scene_point = mark.mapToScene(
                    QPointF(mark.width() / 2, mark.height() / 2)
                )
                px, py = round(scene_point.x() * dpr), round(scene_point.y() * dpr)
                pixels = [
                    rendered.pixelColor(x, y)
                    for x in range(max(0, px - 1), min(rendered.width(), px + 2))
                    for y in range(max(0, py - 1), min(rendered.height(), py + 2))
                ]
                assert any(
                    175 <= color.red() <= 220
                    and abs(color.red() - color.green()) <= 3
                    and abs(color.green() - color.blue()) <= 3
                    for color in pixels
                ), f"{mark.objectName()}: nem rajzolódott ki a beosztás"

        _kattints(window, qt_app, suggestions)
        assert controller.setting_calls[-1] == ("suggestions", False)
        assert controller.suggestions_enabled is False
        assert suggestion_slider.property("enabled") is False
        assert cluster_slider.property("enabled") is False

        _kattints(window, qt_app, suggestions)
        assert controller.setting_calls[-1] == ("suggestions", True)
        assert suggestion_slider.property("enabled") is True
        assert cluster_slider.property("enabled") is True

        _csuszkara_kattint(window, qt_app, suggestion_slider, 90)
        assert controller.setting_calls[-1] == ("suggestionThreshold", 90)
        assert controller.suggestion_threshold == 90
        _csuszkahuzas(window, qt_app, suggestion_slider, 95)
        assert _var(qt_app, lambda: controller.suggestion_threshold == 95)
        assert suggestion_value.property("text") == "95"

        _csuszkara_kattint(window, qt_app, cluster_slider, 75)
        assert controller.setting_calls[-1] == ("clusterThreshold", 75)
        assert controller.cluster_threshold == 75

        _kattints(window, qt_app, persist)
        assert controller.setting_calls[-1] == ("persistFaceToFile", False)
        assert controller.persist_face_to_file is False

    @pytest.mark.parametrize(
        "control_name",
        [
            # #2893: az `optionsAutoExcludeCheck` KIKERÜLT innen — a
            # másodpéldány-észlelés ÉLŐ lett (ld.
            # `TestGeneralTabAutoExclude`). Vezérlő NÉLKÜL viszont továbbra
            # is tiltott, ezt ott állítjuk.
            # #598: az `optionsClearCacheButton` is KIKERÜLT — a
            # bélyegkép-gyorsítótár kézi ürítése ÉLŐ lett
            # (`controller.clearThumbnailCache`), az őre a
            # `test_belyegkep_szint_598.py`.
            # #3539: az `optionsSkipRemoveConfirmCheck` KIKERÜLT innen — az
            # albumból eltávolítás megerősítése ÉLŐ lett, ld.
            # `TestGeneralTabLiveRemoveFromAlbumConfirmSuppression`.
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
        assert (
            _child(window, "optionsSkipRemoveConfirmCheck").property("enabled")
            is True
        )

    def test_general_tab_ui_preferences_toggle_their_controller_state(
        self, dialog, qt_app
    ):
        window, controller, *_ = dialog
        atmenetek = _child(window, "optionsUiTransitionsCheck")
        tippek = _child(window, "optionsShowTooltipsCheck")
        kilepes = _child(window, "optionsSingleClickExitCheck")

        assert atmenetek.property("enabled") is True
        assert atmenetek.property("checked") is True
        assert tippek.property("enabled") is True
        assert tippek.property("checked") is True
        assert kilepes.property("enabled") is True
        assert kilepes.property("checked") is False

        _kattints(window, qt_app, atmenetek)
        assert controller.uiTransitionsEnabled is False
        assert atmenetek.property("checked") is False

        _kattints(window, qt_app, tippek)
        assert controller.showTooltipsEnabled is False
        assert tippek.property("checked") is False

        _kattints(window, qt_app, kilepes)
        assert controller.singleClickExitEnabled is True
        assert kilepes.property("checked") is True
        _kattints(window, qt_app, kilepes)
        assert controller.singleClickExitEnabled is False
        assert kilepes.property("checked") is False


class TestEmailTabLiveSettings:
    """#32: az OptionsTabEmail méret-csúszdái/kliens-választása az
    `emailController`-hez kötve; #4451: a videómód is mentett, élő
    beállítás, az Outlook-jelölő továbbra is tiltott."""

    def _dialog_with_email(self, qt_app, fake_controller, fake_confirm_settings,
                            fake_email_controller):
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", fake_controller)
        engine.rootContext().setContextProperty("confirmSettings", fake_confirm_settings)
        engine.rootContext().setContextProperty("emailController", fake_email_controller)
        factory = QQmlComponent(
            engine,
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "OptionsDialog.qml"),
        )
        item = factory.create()
        assert item is not None, factory.errorString()
        # a factory-t életben kell tartani, különben a Python GC idő előtt
        # eltünteti (a C++ tulajdonjog rajta keresztül fut, ld. a
        # test_qml_widget_chrome.py mintája)
        engine._email_factory = factory
        return item, engine

    def test_size_controls_are_enabled(
        self, qt_app, fake_controller, fake_confirm_settings, fake_email_controller
    ):
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email_controller
        )
        assert _child(window, "optionsMailSizeSlider").property("enabled") is True
        assert _child(window, "optionsMailSingleSameRadio").property("enabled") is True
        assert _child(window, "optionsMailDefaultRadio").property("enabled") is True
        assert _child(window, "optionsMailMovieFirstFrameRadio").property("enabled") is True
        assert _child(window, "optionsMailMovieFullRadio").property("enabled") is True
        assert _child(window, "optionsMailMovieFirstFrameRadio").property("checked") is True
        assert _child(window, "optionsMailMovieFullRadio").property("checked") is False
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_videomodus_valasztas_mentes_es_mindharom_ablakmagassagon_latszik(
        self, qt_app, fake_controller, fake_confirm_settings, tmp_path
    ):
        """#4451: a rádiók kattinthatók, kizárják egymást és visszakötnek.

        A referencia 466 px magas Opciók-ablakát ±5 px eltéréssel is
        végigpróbáljuk; a kattintási pont mindig a vezérlő tényleges
        scene-geometriájából származik.
        """
        email = FakeEmailController()
        translator = QTranslator(qt_app)
        qm = (
            Path(__file__).resolve().parents[2]
            / "src" / "picasapy" / "app" / "i18n" / "picasapy_hu.qm"
        )
        assert translator.load(str(qm))
        qt_app.installTranslator(translator)
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, email
        )
        window.setProperty("width", 769)
        window.setProperty("height", 466)
        window.show()
        tab_bar = _child(window, "optionsTabBar")
        tab_bar.setProperty("currentIndex", 1)
        first = _child(window, "optionsMailMovieFirstFrameRadio")
        full = _child(window, "optionsMailMovieFullRadio")

        hatarido = time.monotonic() + 3.0
        while time.monotonic() < hatarido:
            qt_app.processEvents()
            if first.isVisible() and full.isVisible() and full.height() > 0:
                break
            time.sleep(0.05)
        assert first.isVisible() and full.isVisible() and full.height() > 0
        assert first.property("enabled") is True
        assert full.property("enabled") is True
        stack = _child(window, "optionsTabStack")
        html = _child(window, "optionsMailUseHtmlCheck")
        close = _child(window, "optionsCloseButton")

        def _bottom(item):
            return item.mapToScene(QPointF(0, item.height())).y()

        stack_top = stack.mapToScene(QPointF(0, 0)).y()
        stack_bottom = _bottom(stack)
        close_top = close.mapToScene(QPointF(0, 0)).y()
        assert stack_top <= _bottom(full) <= stack_bottom
        assert stack_top <= _bottom(html) <= stack_bottom
        assert close_top >= stack_bottom
        assert _bottom(close) <= window.height()

        kep = window.grabWindow()
        assert not kep.isNull(), "az E-mail fül nem adott renderelt képet"
        assert kep.save(str(tmp_path / "options-email-4451.png"))

        for elteres in (-5, 0, 5):
            window.setHeight(466 + elteres)
            qt_app.processEvents()
            assert window.height() == 466 + elteres
            pont = full.mapToScene(QPointF(full.width() / 2, full.height() / 2))
            assert 0 <= pont.x() < window.width()
            assert 0 <= pont.y() < window.height()
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(pont.x()), round(pont.y())),
            )
            qt_app.processEvents()
            assert full.property("checked") is True
            assert first.property("checked") is False
            assert email.set_movie_calls[-1] is True

            pont = first.mapToScene(
                QPointF(first.width() / 2, first.height() / 2)
            )
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(pont.x()), round(pont.y())),
            )
            qt_app.processEvents()
            assert first.property("checked") is True
            assert full.property("checked") is False
            assert email.set_movie_calls[-1] is False

        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()
        qt_app.removeTranslator(translator)

    def test_a_HARMADIK_levelezogomb_letezik_es_TILTOTT_2432(
        self, qt_app, fake_controller, fake_confirm_settings, fake_email_controller
    ):
        """#2432: az eredetiben HÁROM gomb van, nálunk kettő volt.

        A harmadik — „A Google Fiók használata" (`options/radio42.title`) —
        tiltott helyőrző: a PicasaPy-nak nincs Google-fiók-integrációja, egy
        engedélyezett, de semmit nem tevő gomb pedig rosszabb a hiányzónál
        (#1895). A fül szerkezete így hű marad, és a tiltás kimondja, hogy
        nem működik.
        """
        window, _engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email_controller
        )
        gomb = _child(window, "optionsMailGoogleRadio")

        assert gomb is not None, "a harmadik levelezőgomb hiányzik"
        assert gomb.property("enabled") is False, (
            "a gomb nem működik — engedélyezve nem létező funkciót ígérne"
        )

    def test_a_harom_gomb_KIZARJA_egymast_2432(
        self, qt_app, fake_controller, fake_confirm_settings, fake_email_controller
    ):
        """A csoporttagságot a VISELKEDÉSÉN mérjük, nem a tulajdonságán.

        ⚠️ A `ButtonGroup.group` csatolt tulajdonság Pythonból nem olvasható
        — sem `QObject.property`, sem `QQmlProperty.read` nem adja vissza
        (mindhárom gombra `None`). Az arra épülő állítás ÜRESEN ZÖLD lett
        volna: `len({id(None)}) == 1` mindig igaz. Ezt menet közben mértem
        ki, és ezért cseréltem le.

        Amit a csoporttagság valójában garantál, az a KIZÁRÓLAGOSSÁG: ha az
        egyik gomb bejelölődik, a többi kijelölése megszűnik. Ez a harmadik,
        TILTOTT gombra is igaz — a tiltás a kattintást akadályozza, a
        tulajdonság-írást nem.
        """
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email_controller
        )
        gombok = {
            nev: _child(window, nev)
            for nev in (
                "optionsMailDefaultRadio",
                "optionsMailChooseRadio",
                "optionsMailGoogleRadio",
            )
        }

        gombok["optionsMailGoogleRadio"].setProperty("checked", True)
        qt_app.processEvents()

        assert gombok["optionsMailGoogleRadio"].property("checked") is True
        for nev in ("optionsMailDefaultRadio", "optionsMailChooseRadio"):
            assert gombok[nev].property("checked") is False, (
                f"a(z) {nev} bejelölve maradt — a három gomb nem zárja ki "
                "egymást, tehát nem egy ButtonGroupban vannak"
            )

        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_a_csuszka_a_MERT_fokozatra_all(
        self, qt_app, fake_controller, fake_confirm_settings
    ):
        """#2020: a vezérlő KÉPPONTOT ad, a csúszka INDEXET mozgat.

        1024 a nyolc mért fokozat (160, 320, 480, 640, 800, 1024, 1200,
        1600) ÖTÖDIK eleme, tehát az index 5."""
        fake_email = FakeEmailController(size=1024, use_default=False)
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email
        )
        assert _child(window, "optionsMailSizeSlider").property("value") == 5
        assert _child(window, "optionsMailChooseRadio").property("checked") is True
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_a_csuszka_MELLE_kiirja_a_keppontszamot(
        self, qt_app, fake_controller, fake_confirm_settings
    ):
        """MÉRVE: az eredetiben a csúszka mellett ott a szám („480 képpont")."""
        fake_email = FakeEmailController(size=800)
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email
        )
        assert "800" in _child(window, "optionsMailSizeValue").property("text")
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_az_egy_kep_gombjaba_BELE_van_irva_az_aktualis_meret(
        self, qt_app, fake_controller, fake_confirm_settings
    ):
        """MÉRVE: „Több elemmel azonos (480 képpont)" — élő kötés.

        Fog: ha valaki statikus feliratot ír a gombra, ez bukik."""
        fake_email = FakeEmailController(size=1600)
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email
        )
        assert "1600" in _child(window, "optionsMailSingleSameRadio").property("text")
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_az_egy_kep_KAPCSOLO_nem_csuszka(
        self, qt_app, fake_controller, fake_confirm_settings
    ):
        """#2020: két választógomb, nem méret-csúszka."""
        fake_email = FakeEmailController(single_original=True)
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email
        )
        assert window.findChild(QObject, "optionsMailSingleSizeSlider") is None
        assert _child(window, "optionsMailSingleOriginalRadio").property("checked") is True
        assert _child(window, "optionsMailSingleSameRadio").property("checked") is False
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_a_csuszka_mozgatasa_KEPPONTOT_ad_at(
        self, qt_app, fake_controller, fake_confirm_settings, fake_email_controller
    ):
        """Fog: index-átadásnál a hívás 3 lenne, nem 640."""
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email_controller
        )
        slider = _child(window, "optionsMailSizeSlider")
        slider.setProperty("value", 3)
        slider.moved.emit()
        qt_app.processEvents()
        assert fake_email_controller.set_size_calls == [640]
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_az_eredeti_meret_gomb_a_KAPCSOLOT_allitja(
        self, qt_app, fake_controller, fake_confirm_settings, fake_email_controller
    ):
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email_controller
        )
        gomb = _child(window, "optionsMailSingleOriginalRadio")
        gomb.setProperty("checked", True)
        gomb.toggled.emit()
        qt_app.processEvents()
        assert fake_email_controller.set_single_calls == [True]
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_choosing_client_radio_calls_controller(
        self, qt_app, fake_controller, fake_confirm_settings, fake_email_controller
    ):
        window, engine = self._dialog_with_email(
            qt_app, fake_controller, fake_confirm_settings, fake_email_controller
        )
        choose_radio = _child(window, "optionsMailChooseRadio")
        choose_radio.setProperty("checked", True)
        choose_radio.toggled.emit()
        qt_app.processEvents()
        assert fake_email_controller.set_use_default_calls == [False]
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

    def test_without_email_controller_uses_sensible_defaults(self, dialog):
        """A `dialog` fixture NEM regisztrál `emailController`-t — a
        null-őr miatt a mezők a modul dokumentált alapértékével jelennek
        meg, írás nélkül (nincs kivétel/QML-hiba)."""
        window, *_ = dialog
        # #2020: vezérlő nélkül a MÉRT alapérték látszik — 480 képpont, ami
        # a nyolc fokozat HARMADIKA (index 2), és „azonos a többivel".
        assert _child(window, "optionsMailSizeSlider").property("value") == 2
        assert "480" in _child(window, "optionsMailSizeValue").property("text")
        assert _child(window, "optionsMailSingleSameRadio").property("checked") is True
        assert _child(window, "optionsMailDefaultRadio").property("checked") is True


class TestGeneralTabAutoExclude:
    """#2893: a „Detect duplicates on import" jelölő ÉLŐ lett.

    A képesség a #1398 óta megvolt (a forrás-beolvasás megjelöli a
    másodpéldányokat, és az `import/autoexclude` szerint hagyja ki őket), csak
    a Beállítások jelölője maradt szürke helyfoglaló, hazug kommenttel.
    """

    def _dialog(self, qt_app, fake_controller, fake_confirm_settings, importer):
        import picasapy.app.application as app_module
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", fake_controller)
        engine.rootContext().setContextProperty(
            "confirmSettings", fake_confirm_settings
        )
        engine.rootContext().setContextProperty(
            "importSourceController", importer
        )
        factory = QQmlComponent(
            engine,
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "OptionsDialog.qml"),
        )
        item = factory.create()
        assert item is not None, factory.errorString()
        engine._factory = factory  # a tulajdonjog a factory-n fut (ld. fentebb)
        return item, engine

    def test_vezerlovel_ELO(
        self, qt_app, fake_controller, fake_confirm_settings,
        fake_import_source_controller,
    ):
        window, engine = self._dialog(
            qt_app, fake_controller, fake_confirm_settings,
            fake_import_source_controller,
        )
        try:
            assert _child(window, "optionsAutoExcludeCheck").property(
                "enabled"
            ) is True
        finally:
            window.deleteLater()
            engine.deleteLater()
            qt_app.processEvents()

    def test_vezerlo_NELKUL_tiltott(self, dialog):
        """Hazug „élő" állapot tilos: ha nincs kihez kötni, a pipa semmit nem
        tárolna el."""
        window, *_ = dialog
        assert _child(window, "optionsAutoExcludeCheck").property(
            "enabled"
        ) is False

    def test_a_pipa_a_vezerlo_allapotat_MUTATJA(
        self, qt_app, fake_controller, fake_confirm_settings,
    ):
        importer = FakeImportSourceController(auto_exclude=True)
        window, engine = self._dialog(
            qt_app, fake_controller, fake_confirm_settings, importer
        )
        try:
            assert _child(window, "optionsAutoExcludeCheck").property(
                "checked"
            ) is True
        finally:
            window.deleteLater()
            engine.deleteLater()
            qt_app.processEvents()

    def test_a_kattintas_UGYANARRA_az_allapotra_ir(
        self, qt_app, fake_controller, fake_confirm_settings,
        fake_import_source_controller,
    ):
        """A jelölő SAJÁT `toggled` jelét bocsátjuk ki — ugyanazt, amit a
        kattintás ad (a fájl `optionsSkipDeleteConfirmCheck`-próbájának
        mintája). A `toggle()` metódus önmagában nem jelez."""
        window, engine = self._dialog(
            qt_app, fake_controller, fake_confirm_settings,
            fake_import_source_controller,
        )
        try:
            pipa = _child(window, "optionsAutoExcludeCheck")
            pipa.setProperty("checked", True)
            pipa.toggled.emit()
            qt_app.processEvents()
            assert fake_import_source_controller.set_calls == [True], (
                "a Beállítások jelölője nem az importáló állapotára írt — "
                "két külön állapot lenne belőle (#2893)"
            )
        finally:
            window.deleteLater()
            engine.deleteLater()
            qt_app.processEvents()

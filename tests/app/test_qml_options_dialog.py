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


class FakeEmailController(QObject):
    """A #32-es EmailController QML-felülete — a valódi
    `email_controller.py` ugyanezt a property/slot-készletet exportálja.

    #2020: a méret KÉPPONT (`emailSize`), az „egy kép" pedig KAPCSOLÓ
    (`singlePictureOriginal`), nem második méret-csúszka.
    """

    emailSizeChanged = Signal()
    singlePictureOriginalChanged = Signal()
    useDefaultClientChanged = Signal()

    def __init__(self, size=480, single_original=False, use_default=True):
        super().__init__()
        self._size = size
        self._single_original = single_original
        self._use_default = use_default
        self.set_size_calls = []
        self.set_single_calls = []
        self.set_use_default_calls = []

    emailSize = Property(int, lambda self: self._size, notify=emailSizeChanged)
    singlePictureOriginal = Property(
        bool, lambda self: self._single_original,
        notify=singlePictureOriginalChanged,
    )
    useDefaultClient = Property(
        bool, lambda self: self._use_default, notify=useDefaultClientChanged
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


@pytest.fixture
def fake_controller():
    return FakeController()


@pytest.fixture
def fake_email_controller():
    return FakeEmailController()


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
            # #32: az E-Mail fül méret-csúszdái/kliens-választása mostantól
            # élő (ld. TestEmailTabLiveSettings) — a "Send movies as"/HTML
            # mező viszont Outlook-specifikus, maradt tiltott placeholder.
            "optionsMailMovieFirstFrameRadio",
            "optionsMailUseHtmlCheck",
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


class TestEmailTabLiveSettings:
    """#32: az OptionsTabEmail méret-csúszdái/kliens-választása az
    `emailController`-hez kötve (a többi mező — "Send movies as"/HTML —
    Outlook-specifikus, maradt tiltott)."""

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
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()

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

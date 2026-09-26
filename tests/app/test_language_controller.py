"""#333/#3555: nyelvválasztás — alapértelmezés az ANGOL, a döntés a
KÖVETKEZŐ indításig vár.

A fordítás Qt Linguist-alapú (`.ts` → `.qm` + `QTranslator`). #3555 előtt a
`setLanguage` AZONNAL váltott; az eredeti Picasa viszont a döntést csak
megerősítteti, és a program következő megnyitásakor lép érvénybe — ezt a
viselkedést vesszük át: a `language` az EBBEN a futásban érvényes nyelv (nem
változik), a `pendingLanguage` a következő indításra kért érték.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.language_controller import (
    DEFAULT_LANGUAGE,
    LANGUAGE_KEY,
    PENDING_LANGUAGE_KEY,
    SUPPORTED_LANGUAGES,
    SYSTEM_LANGUAGE_CODE,
    coerce_language,
    format_system_suffix,
    resolve_startup_language,
    resolve_system_language,
)


class TestLanguageCatalogue:
    def test_default_is_english(self):
        assert DEFAULT_LANGUAGE == "en"

    def test_hungarian_is_offered(self):
        assert set(SUPPORTED_LANGUAGES) == {"en", "hu"}

    def test_spec_order_english_before_hungarian(self):
        # docs/specs/picasa-fo-ablak-elrendezes.md — a langnames.xml
        # sorrendjében az angol (enUK/enUS, #5-6) megelőzi a magyart (#13)
        assert SUPPORTED_LANGUAGES == ("en", "hu")

    def test_key_is_namespaced(self):
        assert LANGUAGE_KEY == "general/language"
        assert PENDING_LANGUAGE_KEY == "general/language_pending"

    @pytest.mark.parametrize("value", ["en", "hu"])
    def test_supported_values_pass_through(self, value):
        assert coerce_language(value) == value

    @pytest.mark.parametrize("value", ["de", "", None, 42, "hu_HU", "EN"])
    def test_unknown_values_fall_back(self, value):
        # a kézzel elrontott beállítás sosem tehet elérhetetlenné a felületet;
        # a nyelvi VÁLTOZATOT (hu_HU) viszont ismerjük fel
        result = coerce_language(value)
        assert result in SUPPORTED_LANGUAGES
        if value == "hu_HU":
            assert result == "hu"
        elif value == "EN":
            assert result == "en"
        else:
            assert result == DEFAULT_LANGUAGE


class TestResolveSystemLanguage:
    def test_returns_a_supported_code(self):
        # bármi is a próbagép rendszernyelve, csak a mi katalógusunkból jön
        assert resolve_system_language() in SUPPORTED_LANGUAGES


@pytest.fixture
def settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


class TestResolveStartupLanguage:
    def test_empty_settings_default_to_english(self, settings):
        assert resolve_startup_language(settings) == "en"
        assert settings.value(LANGUAGE_KEY) == "en"
        assert settings.value(PENDING_LANGUAGE_KEY) == "en"

    def test_no_pending_change_keeps_current(self, settings):
        settings.setValue(LANGUAGE_KEY, "hu")
        assert resolve_startup_language(settings) == "hu"
        assert settings.value(LANGUAGE_KEY) == "hu"

    def test_pending_change_is_applied_and_synced(self, settings):
        # a Beállítások OK-jára beállt, de MÉG nem alkalmazott választás
        settings.setValue(LANGUAGE_KEY, "en")
        settings.setValue(PENDING_LANGUAGE_KEY, "hu")
        assert resolve_startup_language(settings) == "hu"
        assert settings.value(LANGUAGE_KEY) == "hu"
        # a következő induláson már nincs mit alkalmazni
        assert resolve_startup_language(settings) == "hu"

    def test_second_call_is_a_no_op(self, settings):
        settings.setValue(LANGUAGE_KEY, "en")
        settings.setValue(PENDING_LANGUAGE_KEY, "hu")
        resolve_startup_language(settings)
        assert resolve_startup_language(settings) == "hu"

    def test_system_pending_resolves_and_stays_pending(self, settings):
        # a "rendszer szerint" választás minden induláskor ÚJRA feloldódik,
        # nem konkrét kódra dermed (spec D szakasz — `langchange` maradhat 0)
        settings.setValue(LANGUAGE_KEY, "en")
        settings.setValue(PENDING_LANGUAGE_KEY, SYSTEM_LANGUAGE_CODE)
        resolved = resolve_startup_language(settings)
        assert resolved == resolve_system_language()
        assert settings.value(LANGUAGE_KEY) == resolved
        assert settings.value(PENDING_LANGUAGE_KEY) == SYSTEM_LANGUAGE_CODE

    def test_unknown_pending_falls_back_to_current(self, settings):
        settings.setValue(LANGUAGE_KEY, "hu")
        settings.setValue(PENDING_LANGUAGE_KEY, "klingon")
        assert resolve_startup_language(settings) == "hu"
        assert settings.value(PENDING_LANGUAGE_KEY) == "hu"


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "kepek"
    library.mkdir()
    with open_index(tmp_path / "index.db"):
        pass
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )


class TestLanguageSetting:
    def test_defaults_to_english(self, controller):
        assert controller.language == "en"
        assert controller.pendingLanguage == "en"

    def test_set_language_queues_but_does_not_switch(self, controller):
        controller.setLanguage("hu")
        assert controller.pendingLanguage == "hu"
        assert controller.language == "en", (
            "#3555: a futó felület nyelve csak a következő indításkor vált"
        )

    def test_pending_is_persisted_separately(self, controller):
        controller.setLanguage("hu")
        assert controller._get_settings().value(PENDING_LANGUAGE_KEY) == "hu"
        assert controller._get_settings().value(LANGUAGE_KEY) == "en"

    def test_unknown_language_is_ignored(self, controller):
        controller.setLanguage("hu")
        controller.setLanguage("klingon")
        assert controller.pendingLanguage == "hu", "a hibás választás nem ronthatja el"

    def test_system_choice_is_accepted_as_pending(self, controller):
        controller.setLanguage("hu")
        controller.setLanguage(SYSTEM_LANGUAGE_CODE)
        assert controller.pendingLanguage == SYSTEM_LANGUAGE_CODE

    def test_signal_fires_only_on_pending_change(self, controller):
        seen = []
        controller.pendingLanguageChanged.connect(
            lambda: seen.append(controller.pendingLanguage)
        )
        controller.setLanguage("hu")
        controller.setLanguage("hu")
        assert seen == ["hu"]

    def test_language_changed_does_not_fire_on_setlanguage(self, controller):
        seen = []
        controller.languageChanged.connect(lambda: seen.append(controller.language))
        controller.setLanguage("hu")
        assert seen == [], "a setLanguage nem válthat fordítót futás közben"

    def test_applied_by_a_new_controller_next_start(self, controller, tmp_path):
        controller.setLanguage("hu")

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        second = AppController(
            tmp_path / "index.db",
            (str(tmp_path / "kepek"),),
            ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs2", size=32)),
            settings=controller._get_settings(),
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        assert second.language == "hu"
        assert second.pendingLanguage == "hu"


class TestOwnLanguageNames:
    def test_names_are_not_translated(self, controller):
        # a nevek a SAJÁT nyelvükön állnak, a felület nyelvétől függetlenül
        # a hivatalos `Lang::enUS` felirat — a mi `en` kódunk ez (spec A: #6)
        assert controller.ownLanguageName("en") == "English (US)"
        assert controller.ownLanguageName("hu") == "Magyar"

    def test_system_suffix_is_a_locale_code(self, controller):
        suffix = controller.systemLanguageSuffix
        assert isinstance(suffix, str) and suffix != ""

    def test_system_language_code_constant(self, controller):
        assert controller.systemLanguageCode == SYSTEM_LANGUAGE_CODE


class TestSystemSuffixFormat:
    """A rendszer-tétel utótagja (spec B): `xx-YY`; hiányzó, számjegyes vagy
    háromnál hosszabb országkódnál az ország `US`."""

    def test_language_and_country(self):
        assert format_system_suffix("hu", "HU") == "hu-HU"

    @pytest.mark.parametrize("country", ["", "419", "ABCD", "U1"])
    def test_invalid_country_falls_back_to_us(self, country):
        assert format_system_suffix("es", country) == "es-US"

    def test_c_locale_is_not_a_language_code(self):
        # a POSIX „C” locale nyelve nem ISO-kód — a felület alapnyelvére esik
        assert format_system_suffix("C", "") == "en-US"

    def test_language_already_ending_in_country_gives_language_only(self):
        # az eredeti „végződik-e” próbája (0x00987150) KIS-NAGYBETŰ-ÉRZÉKENY:
        # a spec példája `hu-HU`, tehát a `hu` nem „végződik” a `HU`-ra
        assert format_system_suffix("xx-US", "US") == "xx-US"
        assert format_system_suffix("fi", "FI") == "fi-FI"


class TestApplicationLanguagePath:
    """Az `application` két belépője (#3555): a futás KÖZBENI olvasás nem
    érleli be a függő választást, csak az induláskori."""

    def test_configured_language_is_read_only(self, settings, monkeypatch):
        from picasapy.app import application

        monkeypatch.delenv("PICASAPY_LANG", raising=False)
        settings.setValue(LANGUAGE_KEY, "en")
        settings.setValue(PENDING_LANGUAGE_KEY, "hu")
        assert application._configured_language(settings) == "en"
        assert settings.value(LANGUAGE_KEY) == "en"
        assert settings.value(PENDING_LANGUAGE_KEY) == "hu"

    def test_startup_language_applies_the_pending_choice(self, settings, monkeypatch):
        from picasapy.app import application

        monkeypatch.delenv("PICASAPY_LANG", raising=False)
        settings.setValue(LANGUAGE_KEY, "en")
        settings.setValue(PENDING_LANGUAGE_KEY, "hu")
        assert application._startup_language(settings) == "hu"
        assert application._configured_language(settings) == "hu"

    def test_environment_wins_on_both_paths(self, settings, monkeypatch):
        from picasapy.app import application

        monkeypatch.setenv("PICASAPY_LANG", "hu_HU")
        settings.setValue(PENDING_LANGUAGE_KEY, "en")
        assert application._configured_language(settings) == "hu"
        assert application._startup_language(settings) == "hu"

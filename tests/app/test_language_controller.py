"""#333: nyelvválasztás — alapértelmezés az ANGOL, a választás megmarad.

A fordítás Qt Linguist-alapú (`.ts` → `.qm` + `QTranslator`), a nyelvet
viszont eddig a RENDSZER nyelve döntötte el, ezért magyar Windowson nem
lehetett angolra váltani. Mostantól a felhasználó választ, és a döntése a
QSettings-ben él.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.language_controller import (
    DEFAULT_LANGUAGE,
    LANGUAGE_KEY,
    SUPPORTED_LANGUAGES,
    coerce_language,
)


class TestLanguageCatalogue:
    def test_default_is_english(self):
        assert DEFAULT_LANGUAGE == "en"

    def test_hungarian_is_offered(self):
        assert set(SUPPORTED_LANGUAGES) == {"en", "hu"}

    def test_key_is_namespaced(self):
        assert LANGUAGE_KEY == "general/language"

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

    def test_switch_to_hungarian(self, controller):
        controller.setLanguage("hu")
        assert controller.language == "hu"

    def test_persisted(self, controller):
        controller.setLanguage("hu")
        assert controller._get_settings().value(LANGUAGE_KEY) == "hu"

    def test_unknown_language_is_ignored(self, controller):
        controller.setLanguage("hu")
        controller.setLanguage("klingon")
        assert controller.language == "hu", "a hibás választás nem ronthatja el"

    def test_signal_fires_only_on_change(self, controller):
        seen = []
        controller.languageChanged.connect(lambda: seen.append(controller.language))
        controller.setLanguage("hu")
        controller.setLanguage("hu")
        assert seen == ["hu"]

    def test_restored_by_a_new_controller(self, controller, tmp_path):
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

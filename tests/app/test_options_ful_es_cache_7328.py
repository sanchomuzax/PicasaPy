"""Az Opciók ablak két paritási eltérése (#7328, #7332): egységszintű próbák.

#7328: az eredeti a `Preferences\\LastUsedOptionsPage` kulcsba írja a fül
indexét minden lezáráskor, és a menüből hívott megnyitás erre a fülre áll.
#7332: az eredeti az OK után, ha a `disposepreviews` nem nulla, nullát ír
vissza, és a memóriabeli bélyegképtárakat azonnal újrainicializálja; a
lemezes tárhoz az OK nem nyúl, kilépéskor semmi nem üríti.

A valódi kattintásos próba a `qml_functional/test_options_ful_es_cache_7328.py`.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings
from PySide6.QtGui import QImage

from picasapy.app.appearance_controller import (
    DISPOSE_PREVIEWS_ON_EXIT_KEY,
    AppearanceMixin,
)
from picasapy.app.library_controller_activity import _LibraryActivityMixin
from picasapy.app.option_settings import (
    LAST_OPTIONS_TAB_KEY,
    read_last_options_tab,
    save_last_options_tab,
)
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.thumbs import ThumbnailCache

TAB_COUNT = 9


@pytest.fixture
def settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


class TestLastOptionsTab:
    def test_missing_key_opens_the_first_tab(self, settings):
        assert read_last_options_tab(settings, TAB_COUNT) == 0

    @pytest.mark.parametrize("index", range(TAB_COUNT))
    def test_every_tab_index_is_saved_and_restored(self, settings, tmp_path, index):
        save_last_options_tab(settings, index)

        restored = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        assert read_last_options_tab(restored, TAB_COUNT) == index

    def test_google_photos_tab_is_the_last_one_and_can_be_saved(self, settings):
        save_last_options_tab(settings, TAB_COUNT - 1)

        assert read_last_options_tab(settings, TAB_COUNT) == TAB_COUNT - 1

    @pytest.mark.parametrize("stored", [TAB_COUNT, TAB_COUNT + 40, -1, -7])
    def test_out_of_range_value_falls_back_to_the_first_tab(self, settings, stored):
        settings.setValue(LAST_OPTIONS_TAB_KEY, stored)

        assert read_last_options_tab(settings, TAB_COUNT) == 0

    @pytest.mark.parametrize("stored", ["talán", "", None, "3.5", [1, 2]])
    def test_garbage_value_falls_back_to_the_first_tab(self, settings, stored):
        settings.setValue(LAST_OPTIONS_TAB_KEY, stored)

        assert read_last_options_tab(settings, TAB_COUNT) == 0

    def test_a_string_number_from_the_ini_file_is_accepted(self, settings):
        settings.setValue(LAST_OPTIONS_TAB_KEY, "7")

        assert read_last_options_tab(settings, TAB_COUNT) == 7

    def test_smaller_tab_count_falls_back_to_the_first_tab(self, settings):
        save_last_options_tab(settings, 8)

        assert read_last_options_tab(settings, 8) == 0

    def test_out_of_range_index_is_not_written(self, settings):
        save_last_options_tab(settings, 3)
        save_last_options_tab(settings, -2)

        assert read_last_options_tab(settings, TAB_COUNT) == 3


class _Probe(_LibraryActivityMixin, AppearanceMixin, QObject):
    """A két mixin a teljes AppController nélkül, saját szolgáltatóval."""

    def __init__(self, settings, provider):
        super().__init__()
        self._settings = settings
        self._provider = provider
        self._init_appearance()

    def _get_settings(self):
        return self._settings


@pytest.fixture
def provider(qt_app, tmp_path):
    return ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))


def _betolt_memoriat_es_lemezt(provider, tmp_path):
    """Tölti mindkét tárat: a szűrt memóriarekeszt, a lánc-gyorstárat és a lemezt."""
    image = QImage(8, 8, QImage.Format.Format_RGB32)
    image.fill(0x336699)
    provider._memo.put(("kulcs",), image)
    provider._ops_cache["filters=crop64"] = ((), 0)
    lemezes = tmp_path / "thumbs" / "ab" / "abcdef.jpg"
    lemezes.parent.mkdir(parents=True)
    lemezes.write_bytes(b"jpeg")
    return lemezes


class TestProviderMemoryClear:
    def test_clear_memory_cache_empties_only_the_memory_stores(
        self, provider, tmp_path
    ):
        lemezes = _betolt_memoriat_es_lemezt(provider, tmp_path)
        assert provider._memo.get(("kulcs",)) is not None

        provider.clear_memory_cache()

        assert provider._memo.get(("kulcs",)) is None
        assert provider._ops_cache == {}
        assert lemezes.is_file(), "a memóriaürítés nem érinthet lemezes fájlt"

    def test_clear_cache_still_empties_disk_and_memory(self, provider, tmp_path):
        lemezes = _betolt_memoriat_es_lemezt(provider, tmp_path)

        provider.clear_cache()

        assert provider._memo.get(("kulcs",)) is None
        assert not lemezes.exists()


class TestAcceptClearCacheFiles:
    @pytest.fixture
    def controller(self, settings, provider):
        return _Probe(settings, provider)

    def test_checked_ok_clears_memory_and_keeps_disk(
        self, controller, provider, tmp_path
    ):
        lemezes = _betolt_memoriat_es_lemezt(provider, tmp_path)

        controller.acceptClearCacheFiles(True)

        assert provider._memo.get(("kulcs",)) is None
        assert provider._ops_cache == {}
        assert lemezes.is_file(), (
            "az OK a lemezes bélyegkép-tárat nem törölheti (#7332 Nem része)"
        )

    def test_checked_ok_resets_the_saved_flag_to_unchecked(
        self, settings, provider
    ):
        settings.setValue(DISPOSE_PREVIEWS_ON_EXIT_KEY, "true")
        controller = _Probe(settings, provider)
        assert controller.disposePreviewsOnExit is True

        controller.acceptClearCacheFiles(True)

        assert controller.disposePreviewsOnExit is False
        assert settings.value(DISPOSE_PREVIEWS_ON_EXIT_KEY) == "false"

    def test_checked_ok_on_a_fresh_profile_keeps_the_flag_unchecked(
        self, controller
    ):
        controller.acceptClearCacheFiles(True)

        assert controller.disposePreviewsOnExit is False

    def test_checked_ok_announces_the_reset_flag(self, controller):
        controller.setDisposePreviewsOnExit(True)  # régi, mentett érték
        jelzesek = []
        controller.disposePreviewsOnExitChanged.connect(
            lambda: jelzesek.append(controller.disposePreviewsOnExit)
        )

        controller.acceptClearCacheFiles(True)

        assert jelzesek == [False]

    def test_unchecked_ok_clears_nothing(self, controller, provider, tmp_path):
        lemezes = _betolt_memoriat_es_lemezt(provider, tmp_path)

        controller.acceptClearCacheFiles(False)

        assert provider._memo.get(("kulcs",)) is not None
        assert provider._ops_cache != {}
        assert lemezes.is_file()
        assert controller.disposePreviewsOnExit is False

    def test_unchecked_ok_also_resets_an_old_persistent_flag(
        self, settings, provider
    ):
        settings.setValue(DISPOSE_PREVIEWS_ON_EXIT_KEY, "true")
        controller = _Probe(settings, provider)
        assert controller.disposePreviewsOnExit is True

        controller.acceptClearCacheFiles(False)

        assert controller.disposePreviewsOnExit is False

    def test_exit_does_not_clear_even_with_an_old_persistent_flag(
        self, settings, provider, tmp_path
    ):
        """Az #5897 kilépéskori ürítése megszűnt: a lemezhez semmi sem nyúl."""
        settings.setValue(DISPOSE_PREVIEWS_ON_EXIT_KEY, "true")
        controller = _Probe(settings, provider)
        lemezes = _betolt_memoriat_es_lemezt(provider, tmp_path)
        _kilepesi_takaritas(controller)

        assert lemezes.is_file()
        assert provider._memo.get(("kulcs",)) is not None


def _kilepesi_takaritas(controller) -> None:
    """A `shutdown()` kilépéskori ága a teljes AppController nélkül.

    A valódi `shutdown()` leállítja a figyelőt és az időzítőket is; ehhez a
    próbához a cache-ág számít, ezért a vezérlő-keverék metódusát a
    szükséges, üres háttér-állapottal hívjuk."""
    controller._wait_for_rename_workers = lambda _timeout: None
    controller._rename_result_timer = None
    controller._watcher_start_timer = None
    controller._rescan_timer = None
    controller._folder_poll_timer = None
    controller._locked_dirty_retry_timer = None
    controller._watcher = None
    controller.shutdown()

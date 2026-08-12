"""Első indítás: mit olvassunk be — #449.

A Picasa első indításkor egyetlen kérdést tett fel („a teljes számítógép"
vs. „csak a Dokumentumok és a Képek mappa, valamint az asztal"), egyetlen
OK gombbal. A linuxos leképezés: a „teljes gép" a **home-könyvtár** (nem a
teljes fájlrendszer), a szűk halmaz pedig az XDG szerinti három mappa.
"""

import pytest

from picasapy.app.initial_scan import (
    SCAN_NARROW,
    SCAN_WIDE,
    folders_for_choice,
    narrow_folders,
    needs_initial_scan,
    wide_folders,
)


@pytest.fixture
def home(tmp_path, monkeypatch):
    for name in ("Documents", "Pictures", "Desktop"):
        (tmp_path / name).mkdir()
    for variable in (
        "XDG_DOCUMENTS_DIR",
        "XDG_PICTURES_DIR",
        "XDG_DESKTOP_DIR",
    ):
        monkeypatch.delenv(variable, raising=False)
    # a vezérlő a VALÓDI home-ot kérdezi (`Path.home()`), ami a HOME-ból
    # jön — a teszt így a saját, ideiglenes home-jában marad
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


class TestNarrowChoice:
    def test_the_three_folders_are_offered(self, home):
        found = narrow_folders(home)

        assert {p.rsplit("/", 1)[-1] for p in found} == {
            "Documents",
            "Pictures",
            "Desktop",
        }

    def test_a_missing_folder_is_left_out(self, home):
        (home / "Desktop").rmdir()

        found = narrow_folders(home)

        assert all(not p.endswith("/Desktop") for p in found)

    def test_the_xdg_variable_wins(self, home, monkeypatch, tmp_path):
        custom = tmp_path / "Kepek"
        custom.mkdir()
        monkeypatch.setenv("XDG_PICTURES_DIR", str(custom))

        assert str(custom) in narrow_folders(home)

    def test_a_relative_xdg_value_is_measured_from_home(self, home, monkeypatch):
        (home / "sajat").mkdir()
        monkeypatch.setenv("XDG_PICTURES_DIR", "sajat")

        assert str(home / "sajat") in narrow_folders(home)


class TestWideChoice:
    def test_the_wide_choice_is_the_home_directory(self, home):
        assert wide_folders(home) == (str(home),)

    def test_it_is_not_the_whole_filesystem(self, home):
        # linuxon a „teljes gép" végigolvasása rossz ötlet (hálózati
        # meghajtók, konténerek, rendszermappák) — a home a megfelelője
        assert wide_folders(home) != ("/",)


class TestChoiceMapping:
    def test_narrow_and_wide_map_to_their_sets(self, home):
        assert folders_for_choice(SCAN_WIDE, home) == wide_folders(home)
        assert folders_for_choice(SCAN_NARROW, home) == narrow_folders(home)

    def test_an_unknown_choice_falls_back_to_the_safe_one(self, home):
        assert folders_for_choice("nincs-ilyen", home) == narrow_folders(home)


class TestWhenToAsk:
    def test_asks_only_when_there_is_nothing_watched(self):
        assert needs_initial_scan((), skip=False) is True
        assert needs_initial_scan(("/kepek",), skip=False) is False

    def test_the_skip_key_silences_the_wizard(self):
        assert needs_initial_scan((), skip=True) is False


class TestControllerSlice:
    """A vezérlő oldala: mikor kérdez, és mit tesz a válasszal."""

    @pytest.fixture
    def controller(self, qt_app, tmp_path, home):
        from PySide6.QtCore import QSettings

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index
        from picasapy.thumbs import ThumbnailCache

        db = tmp_path / "index.db"
        with open_index(db):
            pass
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        return AppController(db, (), provider, settings=settings)

    def test_it_asks_when_there_is_no_watched_folder(self, controller):
        assert controller.needsInitialScan is True

    def test_the_choice_adds_the_folders_and_silences_the_wizard(
        self, controller, home
    ):
        controller.applyInitialScan("narrow")

        watched = set(controller.watchedFolders)
        assert watched == set(narrow_folders(home))
        assert controller.needsInitialScan is False

    def test_the_wide_choice_adds_the_home_directory(self, controller, home):
        controller.applyInitialScan("wide")

        assert set(controller.watchedFolders) == {str(home)}

    def test_the_dialog_can_show_the_scope_in_advance(self, controller, home):
        assert list(controller.initialScanFolders("wide")) == [str(home)]
        assert list(controller.initialScanFolders("narrow")) == list(
            narrow_folders(home)
        )

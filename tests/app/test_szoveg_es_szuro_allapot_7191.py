"""#7191/#7264: a keresőszöveg és a csillag/arc/geocímke/film gomb közös állapota.

A vezérlő-szintű széljárások: a gomb nem szivároghat át egy másik nézetmódba,
a szöveg törlése a gombot megtartja, a mappára szűkített keresés és a
frissítés is a metszetet adja. A felületi (kattintás, gépelés) próbák a
`qml_functional/test_szoveg_es_szuro_egyutt_7191.py`-ban vannak.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.search_button_filter import intersect_with_button
from picasapy.index import open_index, search_photos, sync_tree
from support.jpeg_factory import make_jpeg

KULCS = "zqsearch"


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    for mappa in ("elso", "masodik"):
        (root / mappa).mkdir(parents=True)
    for nev in ("x1.jpg", "x2.jpg", "x3.jpg"):
        make_jpeg(root / "elso" / nev)
    make_jpeg(root / "masodik" / "y1.jpg")
    (root / "elso" / ".picasa.ini").write_text(
        f"[x1.jpg]\ncaption={KULCS}\nstar=yes\n"
        f"[x2.jpg]\ncaption={KULCS}\n"
        "[x3.jpg]\nstar=yes\n",
        encoding="utf-8",
    )
    (root / "masodik" / ".picasa.ini").write_text(
        f"[y1.jpg]\ncaption={KULCS}\nstar=yes\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )


@pytest.fixture
def video_controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "videok"
    library.mkdir()
    (library / "feliratos.mp4").write_bytes(b"video")
    (library / "felirat_nelkuli.avi").write_bytes(b"video")
    (library / ".picasa.ini").write_text(
        "[feliratos.mp4]\ncaption=zqvid\n", encoding="utf-8"
    )
    db = tmp_path / "video-index.db"
    with open_index(db) as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(
        ThumbnailCache(tmp_path / "video-thumbs", size=32)
    )
    settings = QSettings(
        str(tmp_path / "video-settings.ini"), QSettings.Format.IniFormat
    )
    return AppController(db, (str(library),), provider, settings=settings)


def _nevek(controller) -> set[str]:
    return {foto.name for foto in controller.photos.photos}


class TestAGombNemSzivarog:
    def test_a_film_gomb_aktiv_marad_a_kereses_kozben(self, controller):
        controller.showVideosOnly()
        assert controller.buttonFilterName == "videos"
        controller.search("zqvid")

        assert controller.viewModeName == "search"
        assert controller.searchQuery == "zqvid"
        assert controller.buttonFilterName == "videos"
        assert _nevek(controller) == set()

    def test_a_csillagozott_album_nem_visz_gombot_a_keresesbe(self, controller):
        controller.showStarredAlbum()

        controller.search(KULCS)

        assert controller.buttonFilterName == ""
        assert _nevek(controller) == {"x1.jpg", "x2.jpg", "y1.jpg"}

    def test_a_clearFilter_a_szoveget_es_a_gombot_is_torli(self, controller):
        controller.search(KULCS)
        controller.showStarred()

        controller.clearFilter()

        assert controller.viewModeName == "folder"
        assert controller.buttonFilterName == ""
        assert controller.searchActive is False
        controller.search(KULCS)
        assert _nevek(controller) == {"x1.jpg", "x2.jpg", "y1.jpg"}


class TestASzovegEsAGomb:
    def test_gomb_utan_gepelt_szoveg_a_gomb_nezetebol_indul(self, controller):
        controller.showStarred()
        assert _nevek(controller) == {"x1.jpg", "x3.jpg", "y1.jpg"}

        controller.search(KULCS)

        assert controller.viewModeName == "search"
        assert controller.buttonFilterName == "starred"
        assert _nevek(controller) == {"x1.jpg", "y1.jpg"}

    def test_a_szoveg_torlese_a_gomb_nezetere_ter_vissza(self, controller):
        controller.showStarred()
        controller.search(KULCS)

        controller.search("")

        assert controller.viewModeName == "starred"
        assert controller.filterActive is True
        assert _nevek(controller) == {"x1.jpg", "x3.jpg", "y1.jpg"}
        # a bal hasáb a teljes mappalistára áll vissza
        assert controller.folders.rowCount() >= 2

    def test_ures_kereses_gomb_nezetben_megtartja_a_gombot(self, controller):
        controller.showStarred()

        controller.search("")

        assert controller.viewModeName == "starred"
        assert _nevek(controller) == {"x1.jpg", "x3.jpg", "y1.jpg"}

    def test_a_gomb_kikapcsolasa_keresesnel_a_szoveget_hagyja(self, controller):
        controller.search(KULCS)
        controller.showStarred()

        controller.clearButtonFilter()

        assert controller.searchQuery == KULCS
        assert controller.buttonFilterName == ""
        assert _nevek(controller) == {"x1.jpg", "x2.jpg", "y1.jpg"}

    def test_a_gomb_kikapcsolasa_kereses_nelkul_mint_a_clearFilter(
        self, controller
    ):
        controller.showStarred()

        controller.clearButtonFilter()

        assert controller.viewModeName == "folder"
        assert controller.filterActive is False

    def test_mappara_szukitett_keresesben_a_gomb_megmarad(
        self, controller, library
    ):
        controller.search(KULCS)
        controller.showStarred()

        controller.selectFolderKeepSearch(str(library / "elso"))

        assert controller.viewModeName == "search-folder"
        assert controller.buttonFilterName == "starred"
        assert _nevek(controller) == {"x1.jpg"}
        # a hasáb az összes találatos mappát mutatja (a metszetből)
        assert controller.searchResultCount == 2

    def test_a_gomb_kikapcsolasa_a_mappara_szukitest_megtartja(
        self, controller, library
    ):
        controller.search(KULCS)
        controller.showStarred()
        controller.selectFolderKeepSearch(str(library / "elso"))

        controller.clearButtonFilter()

        assert controller.viewModeName == "search-folder"
        assert _nevek(controller) == {"x1.jpg", "x2.jpg"}

    def test_a_ket_gomb_egymast_kizarja(self, controller):
        controller.search(KULCS)
        controller.showStarred()

        controller.showFacesOnly()

        assert controller.buttonFilterName == "faces"
        assert controller.searchQuery == KULCS
        assert _nevek(controller) == set()


class TestAMetszetSegedfuggveny:
    def test_ures_gombnal_valtozatlan(self, tmp_path, library):
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
            talalatok = search_photos(conn, KULCS)

            assert intersect_with_button(conn, talalatok, "") == talalatok

    def test_a_metszet_a_talalatok_sorrendjet_orzi(self, tmp_path, library):
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
            talalatok = search_photos(conn, KULCS)

            metszet = intersect_with_button(conn, talalatok, "starred")

        assert [r.name for r in metszet] == [
            r.name for r in talalatok if r.star
        ]


class TestAFilmGombMetszete:
    def test_film_nezet_es_szoveg_metszete_torles_es_kikapcsolas(
        self, video_controller
    ):
        controller = video_controller

        controller.showVideosOnly()
        assert controller.buttonFilterName == "videos"
        assert _nevek(controller) == {"feliratos.mp4", "felirat_nelkuli.avi"}

        controller.search("zqvid")
        assert controller.searchQuery == "zqvid"
        assert controller.buttonFilterName == "videos"
        assert _nevek(controller) == {"feliratos.mp4"}

        controller.clearButtonFilter()
        assert controller.viewModeName == "search"
        assert controller.searchQuery == "zqvid"
        assert controller.buttonFilterName == ""
        assert _nevek(controller) == {"feliratos.mp4"}

        controller.showVideosOnly()
        controller.search("")
        assert controller.viewModeName == "videos"
        assert controller.buttonFilterName == "videos"
        assert _nevek(controller) == {"feliratos.mp4", "felirat_nelkuli.avi"}

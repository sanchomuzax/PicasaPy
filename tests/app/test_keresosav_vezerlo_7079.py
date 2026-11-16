"""#7079: a vezérlő `searchBarText` és `searchFeedback` tulajdonsága a valódi indexen.

A QML-próba (`qml_functional/test_keresomezo_szine_7079.py`) a kirajzolt színt és
a popup szövegét méri; ez a fájl a vezérlő oldalát: a látszó képek tényleges
száma, a keresési állapotok és az ezres tagolás kapcsolata.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(
        root / "nyaralas" / "IMG_0001.jpg",
        taken_at="2025:05:01 07:00:00",
        caption="balatoni naplemente",
    )
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    (root / "nyaralas" / ".picasa.ini").write_text(
        "[IMG_0001.jpg]\nstar=yes\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QCoreApplication, QEvent

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("view/showOnlyBigImages", False)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    with open_index(ctl._db_path) as conn:
        ctl._precompute_side_pane(conn)
    ctl._reload()
    assert var_feltetelre(qt_app, lambda: not ctl.backgroundWorkersRunning(), 10.0)
    ctl.selectFolder(str(library / "nyaralas"))
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál maradt futva a teardownban"
    ctl.deleteLater()
    QCoreApplication.sendPostedEvents(ctl, QEvent.Type.DeferredDelete)


def test_keresesi_talalatnal_az_eredeti_fejlec_es_a_zold_jelzes(controller):
    controller.search("naplemente")
    assert controller.searchBarText == 'Search results for "naplemente"'
    assert controller.searchFeedback == "found"


def test_talalat_nelkul_nincs_talalat_es_a_piros_jelzes(controller):
    controller.search("nincstalalat")
    assert controller.searchBarText == "No matches"
    assert controller.searchFeedback == "notfound"


def test_a_torles_utan_nincs_jelzes_es_nincs_kulon_szoveg(controller):
    controller.search("naplemente")
    controller.search("")
    assert controller.searchFeedback == "none"
    assert controller.searchBarText == controller.filterStatusText == ""


def test_mappara_szukitett_kereses_az_osszes_talalat_alapjan_jelez(controller, library):
    controller.search("naplemente")
    controller.selectFolderKeepSearch(str(library / "nyaralas"))
    assert controller.searchActive
    assert controller.searchFeedback == "found"
    assert controller.searchBarText == 'Search results for "naplemente"'


def test_a_csillagszuro_a_latszo_kepek_valodi_szamat_irja(controller):
    controller.showStarred()
    assert controller.searchFeedback == "none"
    assert controller.searchBarText == "1 results: starred"


def test_a_filmszuro_nulla_talalatot_es_a_gomb_szavat_irja(controller):
    controller.showVideosOnly()
    assert controller.searchBarText == "0 results: movies"


def test_masik_szuronel_a_zold_sav_szovege_marad(controller):
    controller.showStarred()
    controller.clearFilter()
    assert controller.searchBarText == controller.filterStatusText == ""

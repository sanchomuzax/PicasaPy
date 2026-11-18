"""Keresés és rejtett képek paritása (#7194).

A keresés darabszáma, a bal hasáb, a zöld sáv és a képrács ugyanabból a
látható halmazból épül:
- ShowHidden ki mellett a rejtett találat nem növeli a bal hasáb, a mezőjelzés,
  a sáv és a rács darabszámát;
- ShowHidden be mellett a találat mind a négyben megjelenik;
- a kapcsoló átváltása után a számok frissülnek;
- a hasáb, a sáv és a rács ugyanazt a látható halmazt mutatja.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from PySide6.QtCore import QSettings

from picasapy.app.controller import AppController
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path: Path) -> Path:
    root = tmp_path / "kepek"
    m1 = root / "nyaralas"
    m2 = root / "kirandulas"
    m1.mkdir(parents=True)
    m2.mkdir(parents=True)

    # nyaralas: 1 látható kép és 1 rejtett kép
    make_jpeg(m1 / "lathato1.jpg", caption="tavaszi virag")
    make_jpeg(m1 / "rejtett1.jpg", caption="tavaszi fagy")

    # kirandulas: csak 1 rejtett kép
    make_jpeg(m2 / "rejtett2.jpg", caption="tavaszi eso")

    (m1 / ".picasa.ini").write_text("[rejtett1.jpg]\nhidden=yes\n", encoding="utf-8")
    (m2 / ".picasa.ini").write_text("[rejtett2.jpg]\nhidden=yes\n", encoding="utf-8")
    return root


@pytest.fixture
def controller(qt_app, tmp_path: Path, library: Path) -> AppController:
    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(conn, library)

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        db_path,
        (str(library),),
        provider,
        settings=settings,
    )
    ctl._reload()
    return ctl


def test_search_hidden_off_excludes_hidden_from_all_four_views(controller, library):
    """ShowHidden ki mellett a rejtett találat sehol nem növeli a számot."""
    assert controller.showHidden is False

    controller.search("tavaszi")

    # 1. Mezőjelzés (searchResultCount)
    assert controller.searchResultCount == 1

    # 2. Rács fotói
    assert controller.photos.rowCount() == 1
    assert [p.name for p in controller.photos.photos] == ["lathato1.jpg"]

    # 3. Bal hasáb (folders modell)
    # A kirandulas mappa csak rejtett találatot tartalmaz, így meg sem jelenhet
    mappa_sorok = [
        controller.folders.data(controller.folders.index(r, 0), controller.folders.NameRole)
        for r in range(controller.folders.rowCount())
        if controller.folders.data(controller.folders.index(r, 0), controller.folders.KindRole) == "folder"
    ]
    assert mappa_sorok == ["nyaralas"]

    # A nyaralas mappa darabszáma csak a látható találat (1)
    mappa_darabok = [
        controller.folders.data(controller.folders.index(r, 0), controller.folders.CountRole)
        for r in range(controller.folders.rowCount())
        if controller.folders.data(controller.folders.index(r, 0), controller.folders.KindRole) == "folder"
    ]
    assert mappa_darabok == [1]

    # 4. Zöld sáv szövege (filterStatusText)
    # 1 látható kép van benne
    assert "1 pictures visible" in controller.filterStatusText
    assert "3 pictures visible" not in controller.filterStatusText


def test_search_toggle_show_hidden_updates_all_views(controller, library):
    """A ShowHidden kapcsoló átváltása után mind a négy helyen frissülnek a találatok."""
    controller.search("tavaszi")
    assert controller.searchResultCount == 1

    # Bekapcsolás
    controller.setShowHidden(True)
    assert controller.showHidden is True

    # Mind a négy helyen 3 kép jelenik meg
    assert controller.searchResultCount == 3
    assert controller.photos.rowCount() == 3
    assert sorted(p.name for p in controller.photos.photos) == [
        "lathato1.jpg",
        "rejtett1.jpg",
        "rejtett2.jpg",
    ]

    mappa_sorok = sorted(
        controller.folders.data(controller.folders.index(r, 0), controller.folders.NameRole)
        for r in range(controller.folders.rowCount())
        if controller.folders.data(controller.folders.index(r, 0), controller.folders.KindRole) == "folder"
    )
    assert mappa_sorok == ["kirandulas", "nyaralas"]

    # Kikapcsolás
    controller.setShowHidden(False)
    assert controller.showHidden is False

    assert controller.searchResultCount == 1
    assert controller.photos.rowCount() == 1
    assert [p.name for p in controller.photos.photos] == ["lathato1.jpg"]


def test_select_folder_keep_search_respects_show_hidden(controller, library):
    """selectFolderKeepSearch esetén a hasáb, a darabszám és a rács is rejtett-szűrt."""
    controller.search("tavaszi")
    nyaralas_ut = str(library / "nyaralas")
    controller.selectFolderKeepSearch(nyaralas_ut)

    # A mezőjelzés az összes látható találat (1)
    assert controller.searchResultCount == 1
    # A rács a mappára szűkült, 1 látható találat
    assert controller.photos.rowCount() == 1
    assert [p.name for p in controller.photos.photos] == ["lathato1.jpg"]

    # ShowHidden be
    controller.setShowHidden(True)
    assert controller.searchResultCount == 3
    assert controller.photos.rowCount() == 2
    assert sorted(p.name for p in controller.photos.photos) == [
        "lathato1.jpg",
        "rejtett1.jpg",
    ]


def test_search_only_hidden_match_yields_zero_when_hidden_off(controller, library):
    """Ha a keresésre CSAK rejtett találat van, ShowHidden ki mellett 0 a darabszám és üres a hasáb."""
    controller.search("eso")  # csak a rejtett2.jpg-re illeszkedik
    assert controller.searchResultCount == 0
    assert controller.photos.rowCount() == 0
    mappa_sorok = [
        controller.folders.data(controller.folders.index(r, 0), controller.folders.NameRole)
        for r in range(controller.folders.rowCount())
        if controller.folders.data(controller.folders.index(r, 0), controller.folders.KindRole) == "folder"
    ]
    assert mappa_sorok == []

    # Átváltás toggleShowHidden-nel
    controller.toggleShowHidden()
    assert controller.showHidden is True
    assert controller.searchResultCount == 1
    assert controller.photos.rowCount() == 1
    assert [p.name for p in controller.photos.photos] == ["rejtett2.jpg"]
    mappa_sorok = [
        controller.folders.data(controller.folders.index(r, 0), controller.folders.NameRole)
        for r in range(controller.folders.rowCount())
        if controller.folders.data(controller.folders.index(r, 0), controller.folders.KindRole) == "folder"
    ]
    assert mappa_sorok == ["kirandulas"]

    # Visszaváltás
    controller.toggleShowHidden()
    assert controller.showHidden is False
    assert controller.searchResultCount == 0
    assert controller.photos.rowCount() == 0


def test_search_clear_restores_folders(controller, library):
    """Keresés után a keresés törlése visszaállítja a teljes mappalistát."""
    controller.search("tavaszi")
    assert controller.searchResultCount == 1

    controller.search("")
    assert controller.searchActive is False
    # A teljes mappalista mindkét mappát tartalmazza
    mappa_sorok = sorted(
        controller.folders.data(controller.folders.index(r, 0), controller.folders.NameRole)
        for r in range(controller.folders.rowCount())
        if controller.folders.data(controller.folders.index(r, 0), controller.folders.KindRole) == "folder"
    )
    assert mappa_sorok == ["kirandulas", "nyaralas"]


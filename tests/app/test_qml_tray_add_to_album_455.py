"""#455: „Add to" — a TÁLCA TARTALMA egyenesen albumhoz adható.

Az eredeti Picasa tálcáján külön gomb kínálta ezt: a böngészés közben,
mappákon átnyúlóan gyűjtött képek egy lépésben albumba tehetők. A tálca
mappákon átnyúlik, ezért a rács-sor alapú út (`addRowsToAlbum`) itt nem
járható — a tartott fotók a globális indexből oldódnak fel.
"""

from __future__ import annotations

import pytest

from picasapy.ini import load_document, parse_album_refs
from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "lib"
    (library / "egy").mkdir(parents=True)
    (library / "ketto").mkdir(parents=True)
    make_jpeg(library / "egy" / "a.jpg")
    make_jpeg(library / "ketto" / "b.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    yield ctl, library
    assert ctl.waitForBackgroundWorkers(30.0), "a háttérszál nem állt le"


def _rows_by_name(ctl, *names) -> list:
    by_name = {p.name: i for i, p in enumerate(ctl.photos.photos)}
    return [by_name[name] for name in names]


def _hold_from_both_folders(ctl, library):
    """Egy-egy képet tart meg KÉT KÜLÖN mappából — ez a tálca lényege."""
    for folder, name in (("egy", "a.jpg"), ("ketto", "b.jpg")):
        ctl.selectFolder(str(library / folder))
        ctl.holdRows(_rows_by_name(ctl, name))
    return ctl.heldCount


def _albums_of(library, folder, name):
    """A fotó `albums=` CSV-jében szereplő album-tokenek."""
    document = load_document(library / folder / ".picasa.ini")
    section = document.section(name)
    raw = section.get("albums") if section is not None else None
    return parse_album_refs(raw or "")


class TestAddHeldToAlbum:
    def test_adds_every_held_picture_across_folders(self, controller):
        ctl, library = controller
        assert _hold_from_both_folders(ctl, library) == 2
        assert ctl.addHeldToAlbum("token123") is True
        assert "token123" in _albums_of(library, "egy", "a.jpg")
        assert "token123" in _albums_of(library, "ketto", "b.jpg")

    def test_empty_tray_is_a_noop(self, controller):
        ctl, _library = controller
        assert ctl.addHeldToAlbum("token123") is False

    def test_empty_token_is_rejected(self, controller):
        ctl, library = controller
        _hold_from_both_folders(ctl, library)
        assert ctl.addHeldToAlbum("   ") is False

    def test_held_paths_span_folders(self, controller):
        """A `heldPaths` a műveletsor bemenete — mappákon átnyúlik."""
        ctl, library = controller
        _hold_from_both_folders(ctl, library)
        paths = list(ctl.heldPaths)
        assert len(paths) == 2
        assert any(p.endswith("a.jpg") for p in paths)
        assert any(p.endswith("b.jpg") for p in paths)

    def test_held_paths_are_empty_for_an_empty_tray(self, controller):
        ctl, _library = controller
        assert list(ctl.heldPaths) == []

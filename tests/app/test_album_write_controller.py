"""#9 (2. lépés): albumtagság ÍRÁSA a vezérlőn át (`addRowsToAlbum`,
`removeRowsFromAlbum`, `createAlbum`).

Az ini-réteg (`picasapy.ini.albums`) és az olvasó oldal
(`tests/app/test_album_controller.py`) már megvan — ez a teszt a TÉNYLEGES
ini-tartalmat ellenőrzi a művelet után, mappánkénti köteges íróutakon
(`_apply_batch`, a `setGeotagRows` mintája, `geo_controller.py`), és több
mappát átfogó kijelöléssel is (#331 tanulsága: a rács a #64 óta a teljes
könyvtárat mutatja, a kijelölés simán átnyúlhat mappákon)."""

from __future__ import annotations

import re

import pytest

from picasapy.ini import load_document
from support.jpeg_factory import make_jpeg

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"


@pytest.fixture
def library(tmp_path):
    """Két mappa: „nyaralas" (egy meglévő albummal, a.jpg taggal, b.jpg
    nélküle) és „varos" (album nélkül) — a keresztmappás kijelöléshez."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "varos").mkdir()
    make_jpeg(root / "nyaralas" / "a.jpg")
    make_jpeg(root / "nyaralas" / "b.jpg")
    make_jpeg(root / "varos" / "c.jpg")
    (root / "nyaralas" / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\n"
        f"name=Nyár\n"
        f"token={_TOKEN}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN}\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    return ctl


def _row_of(controller, name: str) -> int:
    for row, photo in enumerate(controller.photos.photos):
        if photo.name == name:
            return row
    raise AssertionError(f"{name} nincs a rácsban")


def _rows_of(controller, names) -> list:
    wanted = set(names)
    return [
        row
        for row, photo in enumerate(controller.photos.photos)
        if photo.name in wanted
    ]


class TestAddRowsToAlbum:
    def test_writes_the_albums_key(self, controller, library):
        row = _row_of(controller, "b.jpg")
        controller.addRowsToAlbum([row], _TOKEN)
        document = load_document(library / "nyaralas" / ".picasa.ini")
        assert document.section("b.jpg").get("albums") == _TOKEN

    def test_index_count_reflects_new_membership(self, controller, library):
        row = _row_of(controller, "b.jpg")
        controller.addRowsToAlbum([row], _TOKEN)
        by_token = {a["token"]: a for a in controller.albums}
        assert by_token[_TOKEN]["count"] == 2

    def test_is_idempotent(self, controller, library):
        row = _row_of(controller, "a.jpg")
        controller.addRowsToAlbum([row], _TOKEN)
        document = load_document(library / "nyaralas" / ".picasa.ini")
        assert document.section("a.jpg").get("albums") == _TOKEN

    def test_spans_multiple_folders_in_one_call(self, controller, library):
        """A kijelölés két mappán nyúlik át (#331) — mindkét ini-fájl
        megkapja a tagságot, mappánként egyetlen íróművelettel."""
        rows = _rows_of(controller, ["b.jpg", "c.jpg"])
        assert len(rows) == 2
        controller.addRowsToAlbum(rows, _TOKEN)

        nyaralas = load_document(library / "nyaralas" / ".picasa.ini")
        varos = load_document(library / "varos" / ".picasa.ini")
        assert nyaralas.section("b.jpg").get("albums") == _TOKEN
        assert varos.section("c.jpg").get("albums") == _TOKEN

        by_token = {a["token"]: a for a in controller.albums}
        assert by_token[_TOKEN]["count"] == 3

    def test_empty_token_is_a_no_op(self, controller, library):
        row = _row_of(controller, "b.jpg")
        controller.addRowsToAlbum([row], "")
        document = load_document(library / "nyaralas" / ".picasa.ini")
        assert document.section("b.jpg") is None

    def test_empty_selection_writes_nothing(self, controller, library):
        before = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        controller.addRowsToAlbum([], _TOKEN)
        after = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert before == after

    def test_emits_albums_changed(self, controller, library):
        seen = []
        controller.albumsChanged.connect(lambda: seen.append(True))
        row = _row_of(controller, "b.jpg")
        controller.addRowsToAlbum([row], _TOKEN)
        assert seen


class TestRemoveRowsFromAlbum:
    def test_removes_the_key_when_it_was_the_only_membership(
        self, controller, library
    ):
        row = _row_of(controller, "a.jpg")
        controller.removeRowsFromAlbum([row], _TOKEN)
        document = load_document(library / "nyaralas" / ".picasa.ini")
        # az utolsó tagság törlésekor maga az `albums=` kulcs is kikerül —
        # ha a fotónak nem volt más kulcsa, az egész szekció is eltűnik
        section = document.section("a.jpg")
        assert section is None or section.get("albums") is None

    def test_keeps_other_memberships(self, controller, library):
        other_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        row = _row_of(controller, "a.jpg")
        controller.addRowsToAlbum([row], other_token)
        controller.removeRowsFromAlbum([row], _TOKEN)
        document = load_document(library / "nyaralas" / ".picasa.ini")
        assert document.section("a.jpg").get("albums") == other_token

    def test_album_definition_survives_removal(self, controller, library):
        """A `[.album:token]` definíció a mappában marad — csak a tagság
        törlődik, ahogy a Picasa is teszi."""
        row = _row_of(controller, "a.jpg")
        controller.removeRowsFromAlbum([row], _TOKEN)
        document = load_document(library / "nyaralas" / ".picasa.ini")
        assert document.section(f".album:{_TOKEN}") is not None

    def test_index_count_drops(self, controller, library):
        row = _row_of(controller, "a.jpg")
        controller.removeRowsFromAlbum([row], _TOKEN)
        by_token = {a["token"]: a for a in controller.albums}
        assert by_token[_TOKEN]["count"] == 0

    def test_absent_token_is_a_no_op(self, controller, library):
        row = _row_of(controller, "b.jpg")
        controller.removeRowsFromAlbum([row], _TOKEN)
        document = load_document(library / "nyaralas" / ".picasa.ini")
        assert document.section("b.jpg") is None

    def test_empty_selection_writes_nothing(self, controller, library):
        before = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        controller.removeRowsFromAlbum([], _TOKEN)
        after = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert before == after


class TestCreateAlbum:
    def test_returns_a_32_char_hex_token(self, controller, library):
        row = _row_of(controller, "b.jpg")
        token = controller.createAlbum("Új album", [row])
        assert re.fullmatch(r"[0-9a-f]{32}", token)

    def test_two_calls_get_different_tokens(self, controller, library):
        row = _row_of(controller, "b.jpg")
        first = controller.createAlbum("Egyik", [row])
        second = controller.createAlbum("Másik", [row])
        assert first != second

    def test_writes_definition_and_membership(self, controller, library):
        row = _row_of(controller, "b.jpg")
        token = controller.createAlbum("Új album", [row])
        document = load_document(library / "nyaralas" / ".picasa.ini")
        section = document.section(f".album:{token}")
        assert section is not None
        assert section.get("name") == "Új album"
        assert document.section("b.jpg").get("albums") == token

    def test_writes_definition_into_every_involved_folder(
        self, controller, library
    ):
        """A Picasa minden mappába kiírja az album definícióját, ahol van
        tagja — a kijelölés itt két mappát fog át."""
        rows = _rows_of(controller, ["b.jpg", "c.jpg"])
        assert len(rows) == 2
        token = controller.createAlbum("Kirándulás", rows)

        nyaralas = load_document(library / "nyaralas" / ".picasa.ini")
        varos = load_document(library / "varos" / ".picasa.ini")
        assert nyaralas.section(f".album:{token}").get("name") == "Kirándulás"
        assert varos.section(f".album:{token}").get("name") == "Kirándulás"
        assert nyaralas.section("b.jpg").get("albums") == token
        assert varos.section("c.jpg").get("albums") == token

    def test_appends_to_existing_membership(self, controller, library):
        # a.jpg már tagja a _TOKEN albumnak — az új token a sor VÉGÉRE kerül
        row = _row_of(controller, "a.jpg")
        token = controller.createAlbum("Másik", [row])
        document = load_document(library / "nyaralas" / ".picasa.ini")
        assert document.section("a.jpg").get("albums") == f"{_TOKEN},{token}"

    def test_blank_name_is_stored_as_unnamed(self, controller, library):
        row = _row_of(controller, "b.jpg")
        token = controller.createAlbum("   ", [row])
        document = load_document(library / "nyaralas" / ".picasa.ini")
        assert document.section(f".album:{token}").get("name") is None

    def test_empty_selection_returns_empty_string(self, controller, library):
        token = controller.createAlbum("Semmi", [])
        assert token == ""

    def test_new_album_appears_in_controller_albums(self, controller, library):
        row = _row_of(controller, "b.jpg")
        token = controller.createAlbum("Friss", [row])
        by_token = {a["token"]: a for a in controller.albums}
        assert by_token[token]["name"] == "Friss"
        assert by_token[token]["count"] == 1

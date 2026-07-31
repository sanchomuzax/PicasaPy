"""#9 (2. lépés): albumtagság ÍRÁSA a `.picasa.ini`-be.

Amit írunk, azt az eredeti Picasának is olvasnia kell (round-trip elv,
CLAUDE.md 1. döntés): az `albums=` kulcs vesszővel elválasztott token-lista,
a `[.album:<token>]` szekció pedig az album definíciója.

Ezek tiszta függvények az immutable dokumentumon — a fájlba írást (ütközés-
biztosan) a hívó `update_document` végzi.
"""

from __future__ import annotations

from picasapy.ini.albums import (
    albums_of,
    ensure_album,
    with_album,
    without_album,
)
from picasapy.ini.document import parse_document

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_MASIK = "1f2e3d4c5b6a79880123456789abcdef"


class TestAddMembership:
    def test_adds_the_key_when_missing(self):
        document = parse_document("[a.jpg]\nstar=yes\n")
        result = with_album(document, "a.jpg", _TOKEN)
        assert result.section("a.jpg").get("albums") == _TOKEN

    def test_appends_to_an_existing_list(self):
        document = parse_document(f"[a.jpg]\nalbums={_MASIK}\n")
        result = with_album(document, "a.jpg", _TOKEN)
        assert result.section("a.jpg").get("albums") == f"{_MASIK},{_TOKEN}"

    def test_is_idempotent(self):
        document = parse_document(f"[a.jpg]\nalbums={_TOKEN}\n")
        result = with_album(document, "a.jpg", _TOKEN)
        assert result.section("a.jpg").get("albums") == _TOKEN

    def test_creates_the_section_for_a_new_photo(self):
        document = parse_document("")
        result = with_album(document, "uj.jpg", _TOKEN)
        assert result.section("uj.jpg").get("albums") == _TOKEN

    def test_keeps_other_keys(self):
        document = parse_document("[a.jpg]\nstar=yes\ncaption=nyár\n")
        result = with_album(document, "a.jpg", _TOKEN)
        section = result.section("a.jpg")
        assert section.get("star") == "yes"
        assert section.get("caption") == "nyár"

    def test_does_not_mutate_the_input(self):
        document = parse_document("[a.jpg]\n")
        with_album(document, "a.jpg", _TOKEN)
        section = document.section("a.jpg")
        assert section is None or section.get("albums") is None


class TestRemoveMembership:
    def test_removes_one_token(self):
        document = parse_document(f"[a.jpg]\nalbums={_MASIK},{_TOKEN}\n")
        result = without_album(document, "a.jpg", _TOKEN)
        assert result.section("a.jpg").get("albums") == _MASIK

    def test_last_token_removes_the_key(self):
        document = parse_document(f"[a.jpg]\nalbums={_TOKEN}\nstar=yes\n")
        result = without_album(document, "a.jpg", _TOKEN)
        section = result.section("a.jpg")
        assert section.get("albums") is None
        assert section.get("star") == "yes", "a többi kulcs marad"

    def test_unknown_token_is_a_no_op(self):
        document = parse_document(f"[a.jpg]\nalbums={_MASIK}\n")
        result = without_album(document, "a.jpg", _TOKEN)
        assert result.section("a.jpg").get("albums") == _MASIK

    def test_missing_photo_is_a_no_op(self):
        document = parse_document("[a.jpg]\n")
        result = without_album(document, "nincs.jpg", _TOKEN)
        assert result.section("nincs.jpg") is None


class TestAlbumDefinition:
    def test_creates_the_album_section(self):
        document = ensure_album(parse_document(""), _TOKEN, "Nyár 2025")
        album = albums_of(document)[0]
        assert album.token == _TOKEN
        assert album.name == "Nyár 2025"

    def test_writes_the_token_key_like_picasa(self):
        """A Picasa a szekciónév mellé a `token=` kulcsot is kiírja."""
        document = ensure_album(parse_document(""), _TOKEN, "Nyár")
        assert document.section(f".album:{_TOKEN}").get("token") == _TOKEN

    def test_existing_album_keeps_its_name(self):
        document = parse_document(f"[.album:{_TOKEN}]\nname=Eredeti\n")
        result = ensure_album(document, _TOKEN, "Új név")
        assert albums_of(result)[0].name == "Eredeti", "a meglévőt nem írjuk át"

    def test_is_idempotent(self):
        document = ensure_album(parse_document(""), _TOKEN, "Nyár")
        result = ensure_album(document, _TOKEN, "Nyár")
        assert len(albums_of(result)) == 1


class TestRoundTrip:
    """Amit írunk, azt vissza is olvassuk — és a nem érintett sorok
    változatlanok maradnak (a dokumentum-réteg byte-hű megőrzése)."""

    def test_write_then_read(self):
        document = parse_document("[Picasa]\nname=Kepek\n[a.jpg]\nstar=yes\n")
        document = ensure_album(document, _TOKEN, "Nyár 2025")
        document = with_album(document, "a.jpg", _TOKEN)

        text = document.serialize()
        reread = parse_document(text)
        assert reread.section("a.jpg").get("albums") == _TOKEN
        assert albums_of(reread)[0].name == "Nyár 2025"
        assert reread.section("Picasa").get("name") == "Kepek"
        assert reread.section("a.jpg").get("star") == "yes"

    def test_untouched_lines_survive_an_unknown_key(self):
        document = parse_document("[a.jpg]\nbackuphash=36003\nstar=yes\n")
        result = with_album(document, "a.jpg", _TOKEN)
        text = result.serialize()
        assert "backuphash=36003" in text, "amit nem értünk, változatlanul marad"

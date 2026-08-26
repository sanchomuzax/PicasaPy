"""A `color:`/`szín:` keresőtoken (#383): tokenizálás + a keresés-
integráció (sync → háttér-feltöltés → `search_photos`)."""

import cv2
import numpy as np
import pytest

from picasapy.index import backfill_colors, open_index, search_photos, sync_tree
from picasapy.index.search_color import parse_color_terms


class TestParseColorTerms:
    def test_plain_text_untouched(self):
        assert parse_color_terms("balatoni naplemente") == (
            "balatoni naplemente",
            (),
        )

    def test_single_english_token(self):
        assert parse_color_terms("color:blue") == ("", ("blue",))

    def test_single_hungarian_token(self):
        assert parse_color_terms("szín:kék") == ("", ("blue",))

    def test_accent_free_hungarian_prefix(self):
        assert parse_color_terms("szin:piros") == ("", ("red",))

    def test_color_token_combined_with_text_is_and(self):
        remainder, colors = parse_color_terms("color:red naplemente")
        assert remainder == "naplemente"
        assert colors == ("red",)

    def test_multiple_color_tokens_are_collected(self):
        remainder, colors = parse_color_terms("color:red color:blue")
        assert remainder == ""
        assert set(colors) == {"red", "blue"}

    def test_unknown_color_word_stays_as_free_text(self):
        # Elgépelt/ismeretlen szín — ne vesszen el a keresési szándék.
        assert parse_color_terms("color:türkiz") == ("color:türkiz", ())

    def test_case_insensitive(self):
        assert parse_color_terms("COLOR:BLUE") == ("", ("blue",))

    def test_empty_query(self):
        assert parse_color_terms("") == ("", ())


def _write_solid_jpeg(path, bgr: tuple[int, int, int]) -> None:
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    image[:, :] = bgr
    ok = cv2.imwrite(str(path), image)
    assert ok


@pytest.fixture
def color_conn(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    _write_solid_jpeg(root / "piros.jpg", (0, 0, 255))  # BGR: piros
    _write_solid_jpeg(root / "kek.jpg", (255, 0, 0))  # BGR: kék
    _write_solid_jpeg(root / "szurke.jpg", (128, 128, 128))
    (root / ".picasa.ini").write_text(
        "[piros.jpg]\ncaption=naplemente\n", encoding="utf-8"
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        yield conn


class TestSearchIntegration:
    def test_color_only_search_finds_matching_photo(self, color_conn):
        processed = backfill_colors(color_conn, limit=10)
        assert processed == 3
        names = {r.name for r in search_photos(color_conn, "color:red")}
        assert names == {"piros.jpg"}

    def test_hungarian_token_is_equivalent(self, color_conn):
        backfill_colors(color_conn, limit=10)
        names = {r.name for r in search_photos(color_conn, "szín:piros")}
        assert names == {"piros.jpg"}

    def test_gray_photo_matches_gray_token(self, color_conn):
        backfill_colors(color_conn, limit=10)
        names = {r.name for r in search_photos(color_conn, "color:gray")}
        assert names == {"szurke.jpg"}

    @pytest.mark.parametrize("token", ["color:black", "color:white", "color:gray"])
    def test_all_three_achromatic_tokens_find_the_gray_photo(self, color_conn, token):
        """#1480: az eredeti a fekete/fehér/szürke között nem tesz
        különbséget — mindhárom token ugyanazt a képet adja."""
        backfill_colors(color_conn, limit=10)
        names = {r.name for r in search_photos(color_conn, token)}
        assert names == {"szurke.jpg"}

    def test_multiple_color_tokens_are_ored(self, color_conn):
        backfill_colors(color_conn, limit=10)
        names = {r.name for r in search_photos(color_conn, "color:red color:blue")}
        assert names == {"piros.jpg", "kek.jpg"}

    def test_color_and_text_is_anded(self, color_conn):
        backfill_colors(color_conn, limit=10)
        # a "naplemente" felirat csak a piros.jpg-n van
        names = {r.name for r in search_photos(color_conn, "color:blue naplemente")}
        assert names == set()
        names = {r.name for r in search_photos(color_conn, "color:red naplemente")}
        assert names == {"piros.jpg"}

    def test_missing_color_token_is_silently_excluded(self, color_conn):
        # Nincs háttér-feltöltés lefuttatva — a photo_colors tábla üres,
        # a keresés ne dobjon hibát, csak üres találati listát adjon.
        names = {r.name for r in search_photos(color_conn, "color:red")}
        assert names == set()

    def test_backfill_is_idempotent_and_incremental(self, color_conn):
        first = backfill_colors(color_conn, limit=2)
        assert first == 2
        second = backfill_colors(color_conn, limit=10)
        assert second == 1
        third = backfill_colors(color_conn, limit=10)
        assert third == 0

    def test_unrelated_text_search_still_works(self, color_conn):
        # A meglévő szöveges keresés (color: nélkül) nem sérülhet.
        names = {r.name for r in search_photos(color_conn, "naplemente")}
        assert names == {"piros.jpg"}

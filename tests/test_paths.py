"""`picasapy.paths`: a #507 egységes útvonal-normalizálása."""

from __future__ import annotations

import sys

import pytest

from picasapy.paths import normalize_path, path_key


class TestNormalizePath:
    def test_empty(self):
        assert normalize_path("") == ""
        assert normalize_path("   ") == ""

    def test_absolute_already(self, tmp_path):
        folder = tmp_path / "kepek"
        folder.mkdir()
        assert normalize_path(str(folder)) == str(folder)

    def test_trailing_slash_collapses(self, tmp_path):
        folder = tmp_path / "kepek"
        folder.mkdir()
        assert normalize_path(str(folder) + "/") == str(folder)

    def test_dotdot_segment_resolved(self, tmp_path):
        folder = tmp_path / "kepek"
        folder.mkdir()
        sibling = tmp_path / "kepek2"
        sibling.mkdir()
        dotdot = str(tmp_path / "kepek2" / ".." / "kepek")
        assert normalize_path(dotdot) == str(folder)

    @pytest.mark.skipif(sys.platform == "win32", reason="szimbolikus link csak POSIX-on")
    def test_symlink_resolved(self, tmp_path):
        folder = tmp_path / "kepek"
        folder.mkdir()
        link = tmp_path / "kepek_link"
        link.symlink_to(folder, target_is_directory=True)
        assert normalize_path(str(link)) == str(folder)

    def test_nonexistent_path_still_absolute(self, tmp_path):
        # nemlétező végpontnál is abszolút, `..`-mentes alakot ad
        missing = str(tmp_path / "a" / ".." / "nincs-ilyen")
        result = normalize_path(missing)
        assert result == str(tmp_path / "nincs-ilyen")


class TestPathKey:
    def test_posix_case_sensitive(self, tmp_path):
        # Linuxon/macOS-en a kis-nagybetű VALÓDI különbség — a path_key nem
        # foldolhat, különben két különböző mappa összemosódna.
        if sys.platform == "win32":
            pytest.skip("csak POSIX-on érvényes elvárás")
        a = tmp_path / "Kepek"
        b = tmp_path / "kepek"
        assert path_key(str(a)) != path_key(str(b))

    def test_matches_normalize_path_identity_on_posix(self, tmp_path):
        folder = tmp_path / "kepek"
        folder.mkdir()
        if sys.platform != "win32":
            assert path_key(str(folder)) == normalize_path(str(folder))

    def test_dedup_via_dotdot_and_trailing_slash(self, tmp_path):
        folder = tmp_path / "kepek"
        folder.mkdir()
        forms = [
            str(folder),
            str(folder) + "/",
            str(folder / ".." / "kepek"),
        ]
        keys = {path_key(f) for f in forms}
        assert len(keys) == 1

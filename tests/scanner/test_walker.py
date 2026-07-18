"""Mappa-fa bejárás: média-fájlok + .picasa.ini felderítés."""

import pytest

from picasapy.scanner import scan_tree


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "nyaralas").mkdir()
    (tmp_path / "nyaralas" / "IMG_0001.jpg").write_bytes(b"x" * 10)
    (tmp_path / "nyaralas" / "IMG_0002.cr2").write_bytes(b"y" * 20)
    (tmp_path / "nyaralas" / ".picasa.ini").write_text("[IMG_0001.jpg]\nstar=yes\n", encoding="utf-8")
    (tmp_path / "nyaralas" / "jegyzet.txt").write_text("nem média", encoding="utf-8")
    (tmp_path / "nyaralas" / "telek").mkdir()
    (tmp_path / "nyaralas" / "telek" / "video.mp4").write_bytes(b"z" * 30)
    (tmp_path / "ures").mkdir()
    (tmp_path / "nyaralas" / ".picasaoriginals").mkdir()
    (tmp_path / "nyaralas" / ".picasaoriginals" / "IMG_0001.jpg").write_bytes(b"o")
    return tmp_path


class TestScanTree:
    def test_finds_media_folders_sorted(self, tree):
        folders = scan_tree(tree)
        assert [f.path for f in folders] == [
            tree / "nyaralas",
            tree / "nyaralas" / "telek",
        ]

    def test_empty_and_medialess_folders_skipped(self, tree):
        paths = [f.path for f in scan_tree(tree)]
        assert tree / "ures" not in paths

    def test_hidden_folders_skipped(self, tree):
        # .picasaoriginals (és minden rejtett mappa) nem kerül indexbe.
        paths = [f.path for f in scan_tree(tree)]
        assert tree / "nyaralas" / ".picasaoriginals" not in paths

    def test_files_sorted_with_metadata(self, tree):
        folder = scan_tree(tree)[0]
        assert [(f.name, f.kind, f.size) for f in folder.files] == [
            ("IMG_0001.jpg", "photo", 10),
            ("IMG_0002.cr2", "raw", 20),
        ]
        assert all(f.mtime_ns > 0 for f in folder.files)

    def test_ini_detection(self, tree):
        folders = scan_tree(tree)
        assert folders[0].has_ini
        assert not folders[1].has_ini

    def test_non_media_files_excluded(self, tree):
        names = [f.name for f in scan_tree(tree)[0].files]
        assert "jegyzet.txt" not in names
        assert ".picasa.ini" not in names

    def test_stat_failure_skips_file(self, tree):
        # Élő NAS-on a fájl eltűnhet a listázás és a stat() között —
        # törött symlinkkel szimuláljuk; nem buktathatja el a scant.
        try:
            (tree / "nyaralas" / "eltunt.jpg").symlink_to(tree / "nincs-ilyen.jpg")
        except OSError:
            # Windowson a symlink-létrehozás jogosultsághoz kötött
            # (Developer Mode vagy admin) — enélkül a teszt nem futtatható.
            pytest.skip("symlink-létrehozás nem engedélyezett ezen a rendszeren")
        names = [f.name for f in scan_tree(tree)[0].files]
        assert "eltunt.jpg" not in names
        assert "IMG_0001.jpg" in names

    def test_missing_root_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            scan_tree(tmp_path / "nincs")

    def test_scan_is_immutable(self, tree):
        folder = scan_tree(tree)[0]
        with pytest.raises(AttributeError):
            folder.has_ini = False

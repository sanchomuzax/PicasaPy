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


class TestScanTreeExclude:
    """#145: FRExcludeFolders.txt — kizárt mappák (és alfáik) ne kerüljenek
    az eredménybe."""

    def test_excluded_folder_skipped(self, tree):
        folders = scan_tree(tree, exclude=(tree / "nyaralas" / "telek",))
        assert [f.path for f in folders] == [tree / "nyaralas"]

    def test_excluded_folder_and_subfolders_skipped(self, tmp_path):
        root = tmp_path / "gyoker"
        excluded = root / "privat"
        child = excluded / "gyerek"
        child.mkdir(parents=True)
        (child / "titkos.jpg").write_bytes(b"x" * 5)
        (root / "kozos").mkdir()
        (root / "kozos" / "kep.jpg").write_bytes(b"y" * 5)
        folders = scan_tree(root, exclude=(excluded,))
        assert [f.path for f in folders] == [root / "kozos"]

    def test_no_exclude_keeps_everything(self, tree):
        with_exclude = scan_tree(tree, exclude=())
        without_exclude = scan_tree(tree)
        assert with_exclude == without_exclude


class TestScanTreeSkip:
    """#143: inkrementális rescan — a skip-predikátum igaz válasza esetén a
    mappa fájljai nem kerülnek stat-olásra (files üres, skipped=True)."""

    def test_skip_predicate_receives_folder_and_mtimes(self, tree):
        latott = []

        def skip(path, mtime_ns, ini_mtime_ns):
            latott.append((path, mtime_ns, ini_mtime_ns))
            return False

        scan_tree(tree, skip=skip)
        paths = [item[0] for item in latott]
        assert tree / "nyaralas" in paths
        assert all(item[1] > 0 for item in latott)
        ini_by_path = dict((item[0], item[2]) for item in latott)
        assert ini_by_path[tree / "nyaralas"] is not None  # van .picasa.ini
        assert ini_by_path[tree / "nyaralas" / "telek"] is None  # nincs ini

    def test_skipped_folder_has_no_files_but_is_listed(self, tree):
        folders = scan_tree(tree, skip=lambda *_: True)
        assert [f.path for f in folders] == [
            tree / "nyaralas",
            tree / "nyaralas" / "telek",
        ]
        assert all(f.skipped and f.files == () for f in folders)
        assert folders[0].has_ini  # ini-jelenlét stat nélkül is ismert

    def test_no_skip_scans_everything(self, tree):
        folders = scan_tree(tree, skip=lambda *_: False)
        assert not any(f.skipped for f in folders)
        assert [f.name for f in folders[0].files] == [
            "IMG_0001.jpg",
            "IMG_0002.cr2",
        ]

    def test_skip_none_keeps_legacy_behaviour(self, tree):
        # skip nélkül a mappa-mtime-ot sem kérdezzük le (nincs plusz stat)
        folder = scan_tree(tree)[0]
        assert folder.skipped is False
        assert folder.mtime_ns == 0


class TestScanFolder:
    """#143: egyetlen mappa nem-rekurzív scanje a watcher-ág számára."""

    def test_scans_single_folder_without_recursion(self, tree):
        from picasapy.scanner import scan_folder

        scan = scan_folder(tree / "nyaralas")
        assert scan is not None
        assert scan.path == tree / "nyaralas"
        assert [f.name for f in scan.files] == ["IMG_0001.jpg", "IMG_0002.cr2"]
        assert scan.has_ini
        assert scan.mtime_ns > 0
        assert scan.ini_mtime_ns is not None

    def test_missing_folder_returns_none(self, tmp_path):
        from picasapy.scanner import scan_folder

        assert scan_folder(tmp_path / "nincs") is None

    def test_medialess_folder_returns_none(self, tree):
        from picasapy.scanner import scan_folder

        assert scan_folder(tree / "ures") is None

    def test_hidden_folder_returns_none(self, tree):
        from picasapy.scanner import scan_folder

        assert scan_folder(tree / "nyaralas" / ".picasaoriginals") is None


class TestScanTreeLegacyIni:
    """A spec szerint korai Picasa-verziók a `Picasa.ini` (pont nélküli,
    nagybetűs) nevet használták a `.picasa.ini` helyett."""

    def test_legacy_ini_name_detected(self, tmp_path):
        folder = tmp_path / "regi"
        folder.mkdir()
        (folder / "kep.jpg").write_bytes(b"x" * 5)
        (folder / "Picasa.ini").write_text("[kep.jpg]\nstar=yes\n", encoding="utf-8")
        folders = scan_tree(tmp_path)
        assert folders[0].has_ini

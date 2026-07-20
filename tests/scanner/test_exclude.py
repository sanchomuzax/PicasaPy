"""FRExcludeFolders.txt olvasás, kis-nagybetű-független keresés és a
kizárt-mappa eldöntés (#145)."""

from picasapy.scanner import find_exclude_folders_file, is_excluded, read_exclude_folders


class TestReadExcludeFolders:
    def test_one_path_per_line(self, tmp_path):
        f = tmp_path / "FRExcludeFolders.txt"
        f.write_text("/home/sancho/Privat\n/mnt/nas/titkos\n", encoding="utf-8")
        assert read_exclude_folders(f) == (
            "/home/sancho/Privat",
            "/mnt/nas/titkos",
        )

    def test_windows_paths_and_crlf(self, tmp_path):
        f = tmp_path / "FRExcludeFolders.txt"
        f.write_bytes(b"C:\\Users\\sancho\\Privat\r\n")
        assert read_exclude_folders(f) == ("C:\\Users\\sancho\\Privat",)

    def test_missing_file_is_empty(self, tmp_path):
        assert read_exclude_folders(tmp_path / "nincs.txt") == ()


class TestFindExcludeFoldersFile:
    def test_finds_canonical_case(self, tmp_path):
        f = tmp_path / "FRExcludeFolders.txt"
        f.write_text("/a\n", encoding="utf-8")
        assert find_exclude_folders_file(tmp_path) == f

    def test_finds_lowercase_variant(self, tmp_path):
        # Élesben (#145 / MEMORY 2026-07-16) kisbetűs néven is előfordul.
        f = tmp_path / "frexcludefolders.txt"
        f.write_text("/a\n", encoding="utf-8")
        assert find_exclude_folders_file(tmp_path) == f

    def test_missing_returns_none(self, tmp_path):
        assert find_exclude_folders_file(tmp_path) is None


class TestIsExcluded:
    def test_exact_match_excluded(self, tmp_path):
        folder = tmp_path / "privat"
        folder.mkdir()
        assert is_excluded(folder, (folder,))

    def test_subfolder_of_excluded_is_excluded(self, tmp_path):
        root = tmp_path / "privat"
        child = root / "alfa"
        child.mkdir(parents=True)
        assert is_excluded(child, (root,))

    def test_unrelated_folder_not_excluded(self, tmp_path):
        excluded = tmp_path / "privat"
        other = tmp_path / "publikus"
        excluded.mkdir()
        other.mkdir()
        assert not is_excluded(other, (excluded,))

    def test_empty_exclude_list_excludes_nothing(self, tmp_path):
        assert not is_excluded(tmp_path, ())

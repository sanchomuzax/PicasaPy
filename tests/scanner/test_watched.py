"""WatchedFolders.txt olvasás: soronként egy abszolút útvonal (Scan Always)."""

from picasapy.scanner import find_watched_folders_file, read_watched_folders


class TestReadWatchedFolders:
    def test_one_path_per_line(self, tmp_path):
        f = tmp_path / "WatchedFolders.txt"
        f.write_text("/home/sancho/Kepek\n/mnt/nas/fotok\n", encoding="utf-8")
        assert read_watched_folders(f) == ("/home/sancho/Kepek", "/mnt/nas/fotok")

    def test_windows_paths_and_crlf(self, tmp_path):
        # Importnál az eredeti (Windows-os) fájlt is olvasnunk kell.
        f = tmp_path / "WatchedFolders.txt"
        f.write_bytes(b"C:\\Users\\sancho\\Pictures\r\nD:\\Fotok\r\n")
        assert read_watched_folders(f) == (
            "C:\\Users\\sancho\\Pictures",
            "D:\\Fotok",
        )

    def test_blank_lines_skipped(self, tmp_path):
        f = tmp_path / "WatchedFolders.txt"
        f.write_text("/a\n\n/b\n\n", encoding="utf-8")
        assert read_watched_folders(f) == ("/a", "/b")

    def test_utf8_bom_tolerated(self, tmp_path):
        f = tmp_path / "WatchedFolders.txt"
        f.write_bytes(b"\xef\xbb\xbf/k\xc3\xa9pek\n")
        assert read_watched_folders(f) == ("/képek",)

    def test_write_roundtrip(self, tmp_path):
        from picasapy.scanner import write_watched_folders

        f = tmp_path / "WatchedFolders.txt"
        write_watched_folders(f, ("/mnt/nas/fotok", "/home/sancho/Képek"))
        assert read_watched_folders(f) == ("/mnt/nas/fotok", "/home/sancho/Képek")

    def test_write_creates_parent_dir(self, tmp_path):
        from picasapy.scanner import write_watched_folders

        f = tmp_path / "mely" / "WatchedFolders.txt"
        write_watched_folders(f, ("/a",))
        assert read_watched_folders(f) == ("/a",)

    def test_write_empty_clears(self, tmp_path):
        from picasapy.scanner import write_watched_folders

        f = tmp_path / "WatchedFolders.txt"
        write_watched_folders(f, ("/a",))
        write_watched_folders(f, ())
        assert read_watched_folders(f) == ()

    def test_missing_file_is_empty(self, tmp_path):
        assert read_watched_folders(tmp_path / "nincs.txt") == ()


class TestFindWatchedFoldersFile:
    def test_finds_canonical_case(self, tmp_path):
        f = tmp_path / "WatchedFolders.txt"
        f.write_text("/a\n", encoding="utf-8")
        assert find_watched_folders_file(tmp_path) == f

    def test_finds_lowercase_variant(self, tmp_path):
        # Élesben (#145 / MEMORY 2026-07-16) kisbetűs néven is előfordul.
        f = tmp_path / "watchedfolders.txt"
        f.write_text("/a\n", encoding="utf-8")
        assert find_watched_folders_file(tmp_path) == f

    def test_missing_returns_none(self, tmp_path):
        assert find_watched_folders_file(tmp_path) is None

    def test_missing_directory_returns_none(self, tmp_path):
        assert find_watched_folders_file(tmp_path / "nincs") is None

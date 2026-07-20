"""Meglévő Picasa-telepítés felderítése (#146): ismert Wine-útvonalak és
kézzel megadott mappák (pl. NAS-ra másolt db3-könyvtár) vizsgálata,
`WatchedFolders.txt` átvétele path-remappel."""

from __future__ import annotations

from pathlib import Path

from picasapy.pmpimport.remap import PathRemapper
from picasapy.scanner.discovery import (
    PicasaInstallation,
    discover_installations,
    propose_watched_folders,
)


def _make_appdata_with_watched(base: Path, folders: tuple[str, ...] = ("C:\\Kepek",)) -> Path:
    """Segéd: `<base>/Google/Picasa2Albums/WatchedFolders.txt` létrehozása."""
    albums_dir = base / "Google" / "Picasa2Albums"
    albums_dir.mkdir(parents=True)
    (albums_dir / "WatchedFolders.txt").write_text(
        "".join(f"{f}\n" for f in folders), encoding="utf-8"
    )
    (base / "Google" / "Picasa2").mkdir(parents=True)
    return albums_dir


class TestDiscoverInstallationsNoWine:
    def test_no_wine_no_extra_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.delenv("WINEPREFIX", raising=False)
        result = discover_installations(home=tmp_path / "sehol")
        assert result == ()


class TestDiscoverInstallationsWine:
    def test_finds_installation_under_wine_prefix(self, tmp_path, monkeypatch):
        monkeypatch.delenv("WINEPREFIX", raising=False)
        home = tmp_path / "home"
        wine = home / ".wine"
        user_appdata = wine / "drive_c" / "users" / "sancho" / "AppData" / "Local"
        _make_appdata_with_watched(user_appdata)

        result = discover_installations(home=home)

        assert len(result) == 1
        installation = result[0]
        assert installation.picasa2_dir == user_appdata / "Google" / "Picasa2"
        assert (
            installation.picasa2albums_dir
            == user_appdata / "Google" / "Picasa2Albums"
        )
        assert installation.watched_folders_file == (
            user_appdata / "Google" / "Picasa2Albums" / "WatchedFolders.txt"
        )

    def test_finds_installation_under_xp_style_profile(self, tmp_path, monkeypatch):
        monkeypatch.delenv("WINEPREFIX", raising=False)
        home = tmp_path / "home"
        wine = home / ".wine"
        user_appdata = (
            wine
            / "drive_c"
            / "users"
            / "sancho"
            / "Local Settings"
            / "Application Data"
        )
        _make_appdata_with_watched(user_appdata)

        result = discover_installations(home=home)

        assert len(result) == 1
        assert result[0].picasa2albums_dir == user_appdata / "Google" / "Picasa2Albums"

    def test_lowercase_google_dir_is_found(self, tmp_path, monkeypatch):
        # A Google-alkönyvtár és a Picasa2/Picasa2Albums neve is
        # kis-nagybetű-független (Samba/NAS-másolatoknál gyakori).
        monkeypatch.delenv("WINEPREFIX", raising=False)
        home = tmp_path / "home"
        user_appdata = home / ".wine" / "drive_c" / "users" / "sancho" / "AppData" / "Local"
        albums_dir = user_appdata / "google" / "picasa2albums"
        albums_dir.mkdir(parents=True)
        (albums_dir / "watchedfolders.txt").write_text("/a\n", encoding="utf-8")

        result = discover_installations(home=home)

        assert len(result) == 1
        assert result[0].watched_folders_file == albums_dir / "watchedfolders.txt"

    def test_explicit_wineprefix_overrides_default(self, tmp_path):
        other_prefix = tmp_path / "custom-prefix"
        user_appdata = (
            other_prefix / "drive_c" / "users" / "sancho" / "AppData" / "Local"
        )
        _make_appdata_with_watched(user_appdata)

        result = discover_installations(
            home=tmp_path / "sehol-otthon", wineprefix=other_prefix
        )

        assert len(result) == 1
        assert result[0].picasa2_dir == user_appdata / "Google" / "Picasa2"

    def test_no_picasa_under_wine_is_ignored(self, tmp_path, monkeypatch):
        monkeypatch.delenv("WINEPREFIX", raising=False)
        home = tmp_path / "home"
        user_appdata = home / ".wine" / "drive_c" / "users" / "sancho" / "AppData" / "Local"
        user_appdata.mkdir(parents=True)

        result = discover_installations(home=home)

        assert result == ()


class TestDiscoverInstallationsManual:
    def test_manual_dir_is_picasa2albums_directly(self, tmp_path):
        albums_dir = tmp_path / "nas-mentes" / "Picasa2Albums"
        albums_dir.mkdir(parents=True)
        (albums_dir / "WatchedFolders.txt").write_text("/a\n", encoding="utf-8")

        result = discover_installations(
            extra_candidates=(albums_dir,), home=tmp_path / "sehol"
        )

        assert len(result) == 1
        assert result[0].picasa2albums_dir == albums_dir
        assert result[0].picasa2_dir is None
        assert result[0].watched_folders_file == albums_dir / "WatchedFolders.txt"

    def test_manual_dir_is_google_parent(self, tmp_path):
        google_dir = tmp_path / "nas-mentes" / "Google"
        (google_dir / "Picasa2Albums").mkdir(parents=True)
        (google_dir / "Picasa2Albums" / "WatchedFolders.txt").write_text(
            "/a\n", encoding="utf-8"
        )
        (google_dir / "Picasa2").mkdir()

        result = discover_installations(
            extra_candidates=(google_dir,), home=tmp_path / "sehol"
        )

        assert len(result) == 1
        assert result[0].picasa2_dir == google_dir / "Picasa2"
        assert result[0].picasa2albums_dir == google_dir / "Picasa2Albums"

    def test_manual_dir_is_appdata_like_parent(self, tmp_path):
        appdata = tmp_path / "nas-mentes" / "AppData" / "Local"
        _make_appdata_with_watched(appdata)

        result = discover_installations(
            extra_candidates=(appdata,), home=tmp_path / "sehol"
        )

        assert len(result) == 1
        assert result[0].picasa2albums_dir == appdata / "Google" / "Picasa2Albums"

    def test_manual_dir_without_picasa_is_ignored(self, tmp_path):
        empty_dir = tmp_path / "ures"
        empty_dir.mkdir()

        result = discover_installations(
            extra_candidates=(empty_dir,), home=tmp_path / "sehol"
        )

        assert result == ()

    def test_manual_nonexistent_dir_is_ignored(self, tmp_path):
        result = discover_installations(
            extra_candidates=(tmp_path / "nincs-ilyen",), home=tmp_path / "sehol"
        )
        assert result == ()

    def test_duplicate_installations_are_deduplicated(self, tmp_path, monkeypatch):
        monkeypatch.delenv("WINEPREFIX", raising=False)
        home = tmp_path / "home"
        user_appdata = home / ".wine" / "drive_c" / "users" / "sancho" / "AppData" / "Local"
        _make_appdata_with_watched(user_appdata)
        albums_dir = user_appdata / "Google" / "Picasa2Albums"

        result = discover_installations(
            extra_candidates=(albums_dir,), home=home
        )

        assert len(result) == 1


class TestProposeWatchedFolders:
    def test_remaps_matching_prefix(self, tmp_path):
        albums_dir = tmp_path / "Picasa2Albums"
        albums_dir.mkdir()
        (albums_dir / "WatchedFolders.txt").write_bytes(
            b"C:\\Users\\anna\\Pictures\\2024\r\n"
        )
        installation = PicasaInstallation(
            label="teszt",
            picasa2_dir=None,
            picasa2albums_dir=albums_dir,
            watched_folders_file=albums_dir / "WatchedFolders.txt",
        )
        remap = PathRemapper.from_dict(
            {"C:\\Users\\anna\\Pictures": "/mnt/nas/fotok"}
        )

        result = propose_watched_folders(installation, remap)

        assert result == (Path("/mnt/nas/fotok/2024"),)

    def test_unmapped_entries_are_skipped(self, tmp_path):
        albums_dir = tmp_path / "Picasa2Albums"
        albums_dir.mkdir()
        (albums_dir / "WatchedFolders.txt").write_text(
            "C:\\Kepek\nD:\\Egyeb\n", encoding="utf-8"
        )
        installation = PicasaInstallation(
            label="teszt",
            picasa2_dir=None,
            picasa2albums_dir=albums_dir,
            watched_folders_file=albums_dir / "WatchedFolders.txt",
        )
        remap = PathRemapper.from_dict({"C:\\Kepek": "/mnt/nas"})

        result = propose_watched_folders(installation, remap)

        assert result == (Path("/mnt/nas"),)

    def test_duplicate_targets_deduplicated(self, tmp_path):
        albums_dir = tmp_path / "Picasa2Albums"
        albums_dir.mkdir()
        (albums_dir / "WatchedFolders.txt").write_text(
            "C:\\Kepek\\a\nc:\\kepek\\a\n", encoding="utf-8"
        )
        installation = PicasaInstallation(
            label="teszt",
            picasa2_dir=None,
            picasa2albums_dir=albums_dir,
            watched_folders_file=albums_dir / "WatchedFolders.txt",
        )
        remap = PathRemapper.from_dict({"C:\\Kepek": "/mnt/nas"})

        result = propose_watched_folders(installation, remap)

        assert result == (Path("/mnt/nas/a"),)

    def test_missing_watched_file_returns_empty(self):
        installation = PicasaInstallation(
            label="teszt",
            picasa2_dir=None,
            picasa2albums_dir=None,
            watched_folders_file=None,
        )
        remap = PathRemapper.from_dict({"C:\\Kepek": "/mnt/nas"})

        assert propose_watched_folders(installation, remap) == ()

    def test_is_idempotent(self, tmp_path):
        # 7. döntés: az ajánlás ismételhető, ugyanazt az eredményt adja.
        albums_dir = tmp_path / "Picasa2Albums"
        albums_dir.mkdir()
        (albums_dir / "WatchedFolders.txt").write_text(
            "C:\\Kepek\\a\n", encoding="utf-8"
        )
        installation = PicasaInstallation(
            label="teszt",
            picasa2_dir=None,
            picasa2albums_dir=albums_dir,
            watched_folders_file=albums_dir / "WatchedFolders.txt",
        )
        remap = PathRemapper.from_dict({"C:\\Kepek": "/mnt/nas"})

        first = propose_watched_folders(installation, remap)
        second = propose_watched_folders(installation, remap)

        assert first == second

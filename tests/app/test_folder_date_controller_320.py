"""#320: `FolderDateMixin` — a mappa-dátum kézi felülírásának `.picasa.ini`-
írása/olvasása + a resync-kérés.

A mixin ÖNÁLLÓAN, egy minimális host-osztályon tesztelt (a
`folder_tree_controller.py` tesztelési mintája) — a valódi `AppController`-
be kötés (`controller.py`, forró fájl) az integrátor feladata."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject


@pytest.fixture
def host():
    from picasapy.app.folder_date_controller import FolderDateMixin

    class _Host(FolderDateMixin, QObject):
        def __init__(self):
            super().__init__()
            self.resynced: list[str] = []

        def resyncFolder(self, path):
            self.resynced.append(path)

    return _Host()


@pytest.fixture
def folder(tmp_path):
    path = tmp_path / "balaton"
    path.mkdir()
    return path


class TestReadOverride:
    def test_missing_ini_yields_empty_string(self, host, folder):
        assert host.folderDateOverride(str(folder)) == ""

    def test_empty_path_yields_empty_string(self, host):
        assert host.folderDateOverride("") == ""

    def test_existing_override_is_returned(self, host, folder):
        (folder / ".picasa.ini").write_text(
            "[Picasa]\ndate=2019-07-04\n", encoding="utf-8"
        )
        assert host.folderDateOverride(str(folder)) == "2019-07-04"


class TestSetFolderDate:
    def test_writes_ini_and_triggers_resync(self, host, folder):
        host.setFolderDate(str(folder), "2019-07-04")
        assert host.folderDateOverride(str(folder)) == "2019-07-04"
        assert host.resynced == [str(folder)]

    def test_preserves_other_picasa_keys(self, host, folder):
        (folder / ".picasa.ini").write_text(
            "[Picasa]\nname=Nyár\n", encoding="utf-8"
        )
        host.setFolderDate(str(folder), "2020-01-15")
        text = (folder / ".picasa.ini").read_text(encoding="utf-8")
        assert "name=Nyár" in text
        # #2353: a kiírt alak OLE VARIANT, nem ISO — a Picasa `atof`-fal
        # olvassa, és az ISO-ból 1905-öt csinálna. (43845 = 2020-01-15.)
        assert "date=43845.000000" in text

    def test_invalid_format_is_ignored(self, host, folder):
        host.setFolderDate(str(folder), "nem-datum")
        assert not (folder / ".picasa.ini").exists()
        assert host.resynced == []

    def test_empty_folder_path_is_ignored(self, host):
        host.setFolderDate("", "2019-07-04")
        assert host.resynced == []


class TestClearFolderDate:
    def test_removes_override_and_triggers_resync(self, host, folder):
        host.setFolderDate(str(folder), "2019-07-04")
        host.resynced.clear()
        host.clearFolderDate(str(folder))
        assert host.folderDateOverride(str(folder)) == ""
        assert host.resynced == [str(folder)]

    def test_clearing_missing_override_is_noop_but_still_resyncs(self, host, folder):
        host.clearFolderDate(str(folder))
        assert host.resynced == [str(folder)]

    def test_empty_folder_path_is_ignored(self, host):
        host.clearFolderDate("")
        assert host.resynced == []


class TestNoResyncMethodOnHost:
    def test_write_does_not_crash_without_resync_folder(self, folder):
        """A mixin `resyncFolder` NÉLKÜL is működjön (védekező `getattr`) —
        pl. egy jövőbeli host, amely még nincs a LibraryMixinnel
        összeépítve, ne omoljon el."""
        from picasapy.app.folder_date_controller import FolderDateMixin

        class _BareHost(FolderDateMixin, QObject):
            pass

        bare = _BareHost()
        bare.setFolderDate(str(folder), "2019-07-04")
        assert bare.folderDateOverride(str(folder)) == "2019-07-04"

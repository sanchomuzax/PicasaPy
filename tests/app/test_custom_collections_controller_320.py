"""#320/#4589: `CustomCollectionsMixin` — QSettings nevek és ini-tagság,
valamint a QML-nek adott `customCollections` property/slotok.

A mixin ÖNÁLLÓAN, egy minimális host-osztályon tesztelt (a
`folder_tree_controller.py` tesztelési mintája) — a valódi `AppController`-
be kötés (`controller.py`, forró fájl) az integrátor feladata."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.ini import load_document, read_folder_category
from picasapy.scanner import PICASA_INI_NAME


@pytest.fixture
def host(tmp_path):
    from picasapy.app.custom_collections_controller import CustomCollectionsMixin

    class _Host(CustomCollectionsMixin, QObject):
        def __init__(self, settings):
            super().__init__()
            self._settings = settings

        def _get_settings(self):
            return self._settings

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    host = _Host(settings)
    host.folder_path = tmp_path / "kepek" / "balaton"
    host.folder_path.mkdir(parents=True)
    (host.folder_path / PICASA_INI_NAME).write_text(
        "[Picasa]\nP2category=Folders on Disk\n", encoding="utf-8"
    )
    return host


class TestEmptyState:
    def test_no_collections_by_default(self, host):
        assert host.customCollections == []


class TestCreateCollection:
    def test_creates_and_lists(self, host):
        host.createCollection("Nyaralások")
        assert host.customCollections == [{"name": "Nyaralások", "folders": [], "closed": False}]

    def test_persisted_across_instances(self, host, tmp_path):
        from picasapy.app.custom_collections_controller import CustomCollectionsMixin

        host.createCollection("Munka")

        class _Host2(CustomCollectionsMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings

            def _get_settings(self):
                return self._settings

        same_settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        other = _Host2(same_settings)
        assert other.customCollections == [{"name": "Munka", "folders": [], "closed": False}]

    def test_blank_name_creates_nothing(self, host):
        host.createCollection("   ")
        assert host.customCollections == []

    def test_signal_emitted_on_create(self, host):
        events = []
        host.customCollectionsChanged.connect(lambda: events.append(True))
        host.createCollection("Nyaralások")
        assert events == [True]


class TestRenameAndDelete:
    def test_rename_updates_listing(self, host):
        host.createCollection("Régi")
        host.renameCollection("Régi", "Új")
        assert host.customCollections == [{"name": "Új", "folders": [], "closed": False}]

    def test_delete_removes_entry(self, host):
        host.createCollection("Munka")
        host.deleteCollection("Munka")
        assert host.customCollections == []


class TestMoveFolderToCollection:
    def test_move_adds_folder(self, host):
        host.createCollection("Nyaralások")
        host.moveFolderToCollection(str(host.folder_path), "Nyaralások")
        assert host.customCollections == [
            {
                "name": "Nyaralások",
                "folders": [str(host.folder_path)],
                "closed": False,
            }
        ]
        assert read_folder_category(
            load_document(host.folder_path / PICASA_INI_NAME)
        ) == "Nyaralások"

    def test_move_between_collections_is_exclusive(self, host):
        host.createCollection("Régi")
        host.createCollection("Új")
        host.moveFolderToCollection(str(host.folder_path), "Régi")
        host.moveFolderToCollection(str(host.folder_path), "Új")
        assert host.customCollections == [
            {"name": "Régi", "folders": [], "closed": False},
            {
                "name": "Új",
                "folders": [str(host.folder_path)],
                "closed": False,
            },
        ]
        assert read_folder_category(
            load_document(host.folder_path / PICASA_INI_NAME)
        ) == "Új"

    def test_move_to_empty_target_clears_membership(self, host):
        host.createCollection("Nyaralások")
        host.moveFolderToCollection(str(host.folder_path), "Nyaralások")
        host.moveFolderToCollection(str(host.folder_path), "")
        assert host.customCollections == [{"name": "Nyaralások", "folders": [], "closed": False}]
        assert read_folder_category(
            load_document(host.folder_path / PICASA_INI_NAME)
        ) == "Folders on Disk"

"""#320: `CustomCollectionsMixin` — a QSettings-alapú perzisztencia és a
QML-nek adott `customCollections` property/slotok.

A mixin ÖNÁLLÓAN, egy minimális host-osztályon tesztelt (a
`folder_tree_controller.py` tesztelési mintája) — a valódi `AppController`-
be kötés (`controller.py`, forró fájl) az integrátor feladata."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings


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
    return _Host(settings)


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
        host.moveFolderToCollection("/kepek/balaton", "Nyaralások")
        assert host.customCollections == [
            {"name": "Nyaralások", "folders": ["/kepek/balaton"], "closed": False}
        ]

    def test_move_between_collections_is_exclusive(self, host):
        host.createCollection("Régi")
        host.createCollection("Új")
        host.moveFolderToCollection("/kepek/balaton", "Régi")
        host.moveFolderToCollection("/kepek/balaton", "Új")
        assert host.customCollections == [
            {"name": "Régi", "folders": [], "closed": False},
            {"name": "Új", "folders": ["/kepek/balaton"], "closed": False},
        ]

    def test_move_to_empty_target_clears_membership(self, host):
        host.createCollection("Nyaralások")
        host.moveFolderToCollection("/kepek/balaton", "Nyaralások")
        host.moveFolderToCollection("/kepek/balaton", "")
        assert host.customCollections == [{"name": "Nyaralások", "folders": [], "closed": False}]

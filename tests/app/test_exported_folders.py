"""„Exportált képek" — az exportált mappák nyilvántartása (#457).

Az eredeti Picasa külön csomópont alá gyűjtötte az exportált mappákat: az
export így NYOMON KÖVETHETŐ maradt, nem tűnt el a fájlrendszerben.
"""

from pathlib import Path

from picasapy.app.exported_folders import (
    MAX_EXPORTED_FOLDERS,
    existing_exported_folders,
    remember_exported_folder,
)


class TestRemember:
    def test_the_newest_goes_first(self):
        result = remember_exported_folder(["/a", "/b"], "/c")

        assert result == ["/c", "/a", "/b"]

    def test_a_repeat_moves_to_the_front_without_duplicating(self):
        result = remember_exported_folder(["/a", "/b"], "/b")

        assert result == ["/b", "/a"]

    def test_the_list_is_bounded(self):
        existing = [f"/mappa{i}" for i in range(MAX_EXPORTED_FOLDERS + 5)]

        result = remember_exported_folder(existing, "/uj")

        assert len(result) == MAX_EXPORTED_FOLDERS
        assert result[0] == "/uj"

    def test_a_single_string_from_qsettings_is_accepted(self):
        """A Qt egyetlen elemnél stringet ad vissza, nem listát."""
        assert remember_exported_folder("/a", "/b") == ["/b", "/a"]

    def test_an_empty_folder_is_ignored(self):
        assert remember_exported_folder(["/a"], "  ") == ["/a"]

    def test_nothing_stored_yet_is_not_an_error(self):
        assert remember_exported_folder(None, "/a") == ["/a"]


class TestExisting:
    def test_only_folders_that_still_exist_are_listed(self, tmp_path):
        alive = tmp_path / "el"
        alive.mkdir()
        dead = tmp_path / "torolt"

        result = existing_exported_folders([str(alive), str(dead)])

        assert result == [str(alive)]

    def test_a_file_is_not_a_folder(self, tmp_path):
        target = tmp_path / "nem-mappa.txt"
        target.write_text("x", encoding="utf-8")

        assert existing_exported_folders([str(target)]) == []


class TestControllerSide:
    def test_exporting_remembers_the_target(self, qt_app, tmp_path):
        from PySide6.QtCore import QObject, QSettings

        from picasapy.app.export_controller import ExportMixin

        class _Host(ExportMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings_obj = settings

            def _get_settings(self):
                return self._settings_obj

        target = tmp_path / "Exports" / "nyaralas"
        target.mkdir(parents=True)
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        host = _Host(settings)

        host._remember_exported_folder(str(target))

        listed = host.exportedFolders
        assert [entry["path"] for entry in listed] == [str(target)]
        assert listed[0]["name"] == "nyaralas"

    def test_a_deleted_target_disappears_from_the_list(self, qt_app, tmp_path):
        from PySide6.QtCore import QObject, QSettings

        from picasapy.app.export_controller import ExportMixin

        class _Host(ExportMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings_obj = settings

            def _get_settings(self):
                return self._settings_obj

        target = tmp_path / "eltunik"
        target.mkdir()
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        host = _Host(settings)
        host._remember_exported_folder(str(target))

        Path(target).rmdir()

        assert host.exportedFolders == []

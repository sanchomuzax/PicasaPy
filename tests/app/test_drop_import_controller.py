"""#237: képet/mappát az ablakra ejtve figyelt mappa lesz (Picasa-viselkedés).

Kép ráejtése → a kép SZÜLŐMAPPÁJA kerül a figyelt gyökerek közé; mappa
ráejtése → maga a mappa; több elemnél deduplikálva, egymásba ágyazott
utaknál a legfelső elég. Nem támogatott elem → emberi nyelvű visszajelzés.
"""

import pytest

from picasapy.app.drop_import_controller import (
    DropImportController,
    folders_of_dropped_urls,
)


@pytest.fixture
def library(tmp_path):
    """Két mappa: képekkel és egy nem-média fájllal."""
    folder_a = tmp_path / "nyaralas"
    folder_a.mkdir()
    (folder_a / "kep1.jpg").write_bytes(b"x")
    (folder_a / "jegyzet.txt").write_bytes(b"x")
    nested = folder_a / "reszlet"
    nested.mkdir()
    (nested / "kep2.png").write_bytes(b"x")
    folder_b = tmp_path / "csalad"
    folder_b.mkdir()
    (folder_b / "kep3.jpeg").write_bytes(b"x")
    return tmp_path


def _url(path) -> str:
    return path.as_uri()


class TestFoldersOfDroppedUrls:
    def test_image_maps_to_parent_folder(self, library):
        folders, rejected = folders_of_dropped_urls(
            [_url(library / "nyaralas" / "kep1.jpg")]
        )
        assert folders == (str(library / "nyaralas"),)
        assert rejected == ()

    def test_folder_maps_to_itself(self, library):
        folders, rejected = folders_of_dropped_urls([_url(library / "csalad")])
        assert folders == (str(library / "csalad"),)
        assert rejected == ()

    def test_multiple_items_deduplicated(self, library):
        folders, _rejected = folders_of_dropped_urls(
            [
                _url(library / "nyaralas" / "kep1.jpg"),
                _url(library / "nyaralas" / "kep1.jpg"),
                _url(library / "csalad" / "kep3.jpeg"),
            ]
        )
        assert folders == (
            str(library / "nyaralas"),
            str(library / "csalad"),
        )

    def test_nested_paths_keep_topmost_only(self, library):
        # a mappa ÉS az almappájának képe → csak a felső mappa kell
        folders, _rejected = folders_of_dropped_urls(
            [
                _url(library / "nyaralas" / "reszlet" / "kep2.png"),
                _url(library / "nyaralas"),
            ]
        )
        assert folders == (str(library / "nyaralas"),)

    def test_unsupported_file_rejected_by_name(self, library):
        folders, rejected = folders_of_dropped_urls(
            [_url(library / "nyaralas" / "jegyzet.txt")]
        )
        assert folders == ()
        assert rejected == ("jegyzet.txt",)

    def test_missing_path_rejected(self, library):
        folders, rejected = folders_of_dropped_urls(
            [_url(library / "nincs-ilyen" / "kep.jpg")]
        )
        assert folders == ()
        assert rejected == ("kep.jpg",)

    def test_video_counts_as_media(self, library):
        video = library / "csalad" / "mozgokep.mp4"
        video.write_bytes(b"x")
        folders, rejected = folders_of_dropped_urls([_url(video)])
        assert folders == (str(library / "csalad"),)
        assert rejected == ()


class TestDropImportController:
    def test_adds_folders_via_add_folder(self, qt_app, library):
        added = []
        controller = DropImportController(add_folder=added.append)
        controller.importDroppedUrls(
            [
                _url(library / "nyaralas" / "kep1.jpg"),
                _url(library / "csalad"),
            ]
        )
        assert added == [str(library / "nyaralas"), str(library / "csalad")]

    def test_rejected_items_emit_human_message(self, qt_app, library):
        messages = []
        controller = DropImportController(add_folder=lambda _p: None)
        controller.dropRejected.connect(messages.append)
        controller.importDroppedUrls([_url(library / "nyaralas" / "jegyzet.txt")])
        assert len(messages) == 1
        assert "jegyzet.txt" in messages[0]

    def test_mixed_drop_adds_and_reports(self, qt_app, library):
        added, messages = [], []
        controller = DropImportController(add_folder=added.append)
        controller.dropRejected.connect(messages.append)
        controller.importDroppedUrls(
            [
                _url(library / "csalad" / "kep3.jpeg"),
                _url(library / "nyaralas" / "jegyzet.txt"),
            ]
        )
        assert added == [str(library / "csalad")]
        assert len(messages) == 1

    def test_valid_drop_is_silent(self, qt_app, library):
        messages = []
        controller = DropImportController(add_folder=lambda _p: None)
        controller.dropRejected.connect(messages.append)
        controller.importDroppedUrls([_url(library / "csalad")])
        assert messages == []

    def test_empty_drop_reports(self, qt_app):
        messages = []
        controller = DropImportController(add_folder=lambda _p: None)
        controller.dropRejected.connect(messages.append)
        controller.importDroppedUrls([])
        assert len(messages) == 1

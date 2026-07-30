"""#322: a bal oldali mappapanel szélessége állítható és megjegyződik.

A szélesség a QSettings `view/folderPaneWidth` kulcsában él (mint a
`view/folderSort` és társai), és ésszerű határok közé szorul — így egy
elrontott (0 vagy képernyőnél szélesebb) érték sem tudja használhatatlanná
tenni a felületet a következő induláskor.
"""

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg

from picasapy.app.controller import (
    FOLDER_PANE_WIDTH_DEFAULT,
    FOLDER_PANE_WIDTH_MAX,
    FOLDER_PANE_WIDTH_MIN,
)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    # elszigetelt QSettings — a valós PicasaPy-beállításokat ne írja a teszt
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    yield ctl
    ctl.shutdown() if hasattr(ctl, "shutdown") else None


class TestFolderPaneWidth:
    def test_default_when_unset(self, controller):
        assert controller.folderPaneWidth == FOLDER_PANE_WIDTH_DEFAULT

    def test_set_and_read_back(self, controller):
        controller.setFolderPaneWidth(310)
        assert controller.folderPaneWidth == 310

    def test_persisted_to_settings(self, controller):
        controller.setFolderPaneWidth(275)
        assert int(controller._get_settings().value("view/folderPaneWidth")) == 275

    def test_too_narrow_is_clamped(self, controller):
        controller.setFolderPaneWidth(10)
        assert controller.folderPaneWidth == FOLDER_PANE_WIDTH_MIN

    def test_too_wide_is_clamped(self, controller):
        controller.setFolderPaneWidth(5000)
        assert controller.folderPaneWidth == FOLDER_PANE_WIDTH_MAX

    def test_garbage_in_settings_falls_back_to_default(self, controller):
        controller._get_settings().setValue("view/folderPaneWidth", "nem-szám")
        assert controller.folderPaneWidth == FOLDER_PANE_WIDTH_DEFAULT

    def test_survives_a_new_controller_on_the_same_settings(
        self, controller, tmp_path, library
    ):
        controller.setFolderPaneWidth(288)

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        second = AppController(
            tmp_path / "index.db",
            (str(library),),
            ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs2", size=32)),
            settings=controller._get_settings(),
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        assert second.folderPaneWidth == 288

"""AppController: arcfelismerés be/ki kapcsolója mappánként (#449) — a
Mappakezelő negyedik, a Scan Always/Once/Remove hármastól FÜGGETLEN
vezérlője. Arcfelismerés-motor MÉG NINCS a projektben: itt csak azt
ellenőrizzük, hogy a szándék (`FRExcludeFolders.txt`) helyesen íródik/
olvasódik, és a három scan-állapottól függetlenül viselkedik."""

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(lib),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
        exclude_file=tmp_path / "FRExcludeFolders.txt",
    )
    ctl._reload()
    yield ctl, lib, tmp_path
    assert ctl.waitForBackgroundWorkers(30.0), (
        "háttérszál nem állt le a controller teardownban (#430/#438)"
    )


class TestFaceDetectionToggle:
    def test_enabled_by_default(self, controller):
        ctl, lib, _tmp_path = controller
        assert ctl.faceDetectionEnabledFor(str(lib)) is True

    def test_disable_excludes_folder(self, controller):
        ctl, lib, _tmp_path = controller
        ctl.setFaceDetectionEnabled(str(lib), False)
        assert ctl.faceDetectionEnabledFor(str(lib)) is False

    def test_disable_excludes_subfolders_too(self, controller):
        ctl, lib, _tmp_path = controller
        child = lib / "alalbum"
        child.mkdir()
        ctl.setFaceDetectionEnabled(str(lib), False)
        assert ctl.faceDetectionEnabledFor(str(child)) is False

    def test_re_enable_clears_exclusion(self, controller):
        ctl, lib, _tmp_path = controller
        ctl.setFaceDetectionEnabled(str(lib), False)
        ctl.setFaceDetectionEnabled(str(lib), True)
        assert ctl.faceDetectionEnabledFor(str(lib)) is True

    def test_independent_from_watched_state(self, controller):
        """A #449-es jegy szerint a kapcsoló FÜGGETLEN a Scan Always/Once/
        Remove hármastól: kikapcsolt arcfelismerés mellett a mappa
        maradjon figyelt (ne kerüljön ki a watchedFolders-ből)."""
        ctl, lib, _tmp_path = controller
        ctl.setFaceDetectionEnabled(str(lib), False)
        assert str(lib) in ctl.watchedFolders
        assert ctl.faceDetectionEnabledFor(str(lib)) is False

    def test_persists_to_exclude_file(self, controller):
        from picasapy.scanner import read_exclude_folders

        ctl, lib, tmp_path = controller
        ctl.setFaceDetectionEnabled(str(lib), False)
        assert read_exclude_folders(tmp_path / "FRExcludeFolders.txt") == (
            str(lib),
        )

    def test_re_enable_removes_from_exclude_file(self, controller):
        from picasapy.scanner import read_exclude_folders

        ctl, lib, tmp_path = controller
        ctl.setFaceDetectionEnabled(str(lib), False)
        ctl.setFaceDetectionEnabled(str(lib), True)
        assert read_exclude_folders(tmp_path / "FRExcludeFolders.txt") == ()

    def test_face_excluded_folders_property(self, controller):
        ctl, lib, _tmp_path = controller
        ctl.setFaceDetectionEnabled(str(lib), False)
        assert ctl.faceExcludedFolders == [str(lib)]

    def test_loads_exclude_file_at_startup(self, qt_app, tmp_path):
        """A `face_excluded` konstruktor-paraméter (application.py a
        `_exclude_folders_path()`-ból tölti be indításkor) — itt közvetlenül
        átadva ellenőrizzük a bekötést."""
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache
        from PySide6.QtCore import QSettings

        lib = tmp_path / "kepek2"
        lib.mkdir()
        make_jpeg(lib / "a.jpg")
        with open_index(tmp_path / "index2.db") as conn:
            sync_tree(conn, lib)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs2", size=32))
        settings = QSettings(
            str(tmp_path / "settings2.ini"), QSettings.Format.IniFormat
        )
        ctl = AppController(
            tmp_path / "index2.db",
            (str(lib),),
            provider,
            settings=settings,
            watched_file=tmp_path / "WatchedFolders2.txt",
            exclude_file=tmp_path / "FRExcludeFolders2.txt",
            face_excluded=(str(lib),),
        )
        try:
            assert ctl.faceDetectionEnabledFor(str(lib)) is False
        finally:
            assert ctl.waitForBackgroundWorkers(30.0)

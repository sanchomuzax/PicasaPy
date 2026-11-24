"""#7414: a kikapcsolt fájltípus ne számítson a bal hasáb gyűjteményeiben."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.scanner.filetypes import FILETYPE_GROUPS
    from picasapy.thumbs import ThumbnailCache
    from support.jpeg_factory import make_jpeg

    root = tmp_path / "kepek"
    project = root / "projekt"
    other = root / "egyeb"
    project.mkdir(parents=True)
    other.mkdir(parents=True)
    make_jpeg(project / "target.jpg", size=(80, 60))
    make_jpeg(other / "target.jpg", size=(80, 60))
    (project / "target.mp4").write_bytes(b"movie-data")
    (other / "target.mp4").write_bytes(b"movie-data")
    (project / ".picasa.ini").write_text(
        "[Picasa]\nP2category=Projects (internal)\n", encoding="utf-8"
    )
    (other / ".picasa.ini").write_text(
        "[Picasa]\nP2category=Other Stuff\n", encoding="utf-8"
    )

    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(
            conn,
            root,
            incremental=False,
            enabled_filetypes=set(FILETYPE_GROUPS),
        )
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    app_controller = AppController(
        db_path,
        (str(root),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )

    def prepare_cache():
        with open_index(db_path) as conn:
            app_controller._precompute_side_pane(conn)

    app_controller._start_background(
        prepare_cache, name="test-filetype-side-pane-cache-warmup"
    )
    assert app_controller.waitForBackgroundWorkers(20.0)
    app_controller._reload_after_sync()
    yield app_controller, db_path
    assert app_controller.waitForBackgroundWorkers(20.0)


def test_projects_and_other_stuff_counts_refresh_when_filetype_changes(
    controller,
):
    from picasapy.index import open_index

    app, db_path = controller
    assert app.projectFolders[0]["count"] == 2
    assert app.otherStuffFolders[0]["count"] == 2

    app.setFileTypeEnabled("movies", False)

    assert app.projectFolders[0]["count"] == 1
    assert app.otherStuffFolders[0]["count"] == 1
    with open_index(db_path) as conn:
        names = {row["name"] for row in conn.execute("SELECT name FROM photos")}
    assert names == {"target.jpg", "target.mp4"}

    app.setFileTypeEnabled("movies", True)
    assert app.projectFolders[0]["count"] == 2
    assert app.otherStuffFolders[0]["count"] == 2

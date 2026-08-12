"""#465: a visszavonás adatvesztéses eseteinek felismerése.

Az eredeti Picasa a teljes visszaállítás előtt KÜLÖN figyelmeztet, ha az
adott képen vörösszem-javítás van (`IDS_CONFIRM_REDEYE_REVERT`), mert az
régió-adatot hordoz és a törléssel véglegesen elvész.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "lib"
    library.mkdir()
    make_jpeg(library / "a.jpg")
    make_jpeg(library / "b.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    yield ctl, library
    assert ctl.waitForBackgroundWorkers(30.0), "a háttérszál nem állt le"


class TestSelectionHasRedeye:
    def _rows(self, ctl):
        return list(range(ctl.photos.rowCount()))

    def test_no_edits_means_no_redeye(self, controller):
        ctl, _library = controller
        assert ctl.selectionHasRedeye(self._rows(ctl)) is False

    def test_detects_redeye_in_any_selected_picture(self, controller):
        ctl, library = controller
        (library / ".picasa.ini").write_text(
            "[b.jpg]\nfilters=crop64=1,10000000f1ddff49;redeye=1;\n",
            encoding="utf-8",
        )
        assert ctl.selectionHasRedeye(self._rows(ctl)) is True

    def test_other_effects_do_not_count(self, controller):
        ctl, library = controller
        (library / ".picasa.ini").write_text(
            "[a.jpg]\nfilters=enhance=1;sepia=1;\n", encoding="utf-8"
        )
        assert ctl.selectionHasRedeye(self._rows(ctl)) is False

    def test_manual_redeye_regions_also_count(self, controller):
        """A kézi régiós alak (#445) is vörösszem-javítás."""
        ctl, library = controller
        (library / ".picasa.ini").write_text(
            "[a.jpg]\nfilters=redeye=1,333333334ccd4ccd;\n", encoding="utf-8"
        )
        assert ctl.selectionHasRedeye(self._rows(ctl)) is True

    def test_empty_selection_is_false(self, controller):
        ctl, _library = controller
        assert ctl.selectionHasRedeye([]) is False

    def test_broken_ini_does_not_raise(self, controller):
        """Sérült/idegen ini nem szökhet ki kivétellel (#301-elv)."""
        ctl, library = controller
        (library / ".picasa.ini").write_text("nem ini tartalom\x00", encoding="utf-8")
        assert ctl.selectionHasRedeye(self._rows(ctl)) is False

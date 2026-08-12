"""A műveletsor a KÉPTÁLCA tartalmán dolgozzon — #455, 3. teendő.

Az eredeti Picasában az alsó sáv gombjai nem a pillanatnyi kijelölésen,
hanem a **tálca tartalmán** futottak (a buboréksúgók végig „a képtálca
képeire" hivatkoznak). A tálca mappákon átnyúlik, ezért a művelet nem
rács-sorokkal, hanem a globális indexből felolvasott rekordokkal dolgozik.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    """Két mappa, mindegyikben egy-egy képpel — a tálca lényege épp az,
    hogy MAPPÁKON ÁTNYÚLVA gyűjt."""
    first = tmp_path / "elso"
    second = tmp_path / "masodik"
    first.mkdir()
    second.mkdir()
    make_jpeg(first / "a.jpg", size=(32, 24))
    make_jpeg(second / "b.jpg", size=(32, 24))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, first)
        sync_tree(conn, second)
    return tmp_path, first, second, db


@pytest.fixture
def controller(qt_app, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    tmp_path, first, second, db = library
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    return AppController(
        db, (str(first), str(second)), provider, settings=settings
    )


def _wait_for_export(controller, qt_app, timeout_ms=15000):
    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    result = {}
    controller.exportFinished.connect(
        lambda done, failed: (result.update(done=done, failed=failed), loop.quit())
    )
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    qt_app.processEvents()
    return result


def _load_grid(controller, qt_app, folder):
    """A rács feltöltése — induláskor üres, az első mappaválasztás tölti
    fel (a feed a könyvtár összes gyökeréből mutat képet)."""
    controller.selectFolder(str(folder))
    qt_app.processEvents()


def _row_of(controller, folder):
    """A `folder`-ben lévő kép sorindexe a rácsban. A feed a könyvtár
    ÖSSZES gyökeréből mutat képet, ezért nem a mappaválasztás, hanem az
    útvonal alapján keressük meg a sort."""
    for row in range(controller.photos.rowCount()):
        path = controller.photos.filePathAt(row)
        if path and Path(path).parent == Path(folder):
            return row
    raise AssertionError(f"nincs kép a rácsban ebből a mappából: {folder}")


def _hold_everything(controller, qt_app, first, second):
    """Mindkét MAPPÁBÓL egy-egy kép a tálcára — a tálca lényege, hogy
    mappákon átnyúlva gyűjt."""
    _load_grid(controller, qt_app, first)
    controller.holdRows([_row_of(controller, first), _row_of(controller, second)])
    qt_app.processEvents()


class TestExportHeld:
    def test_the_tray_export_reaches_across_folders(
        self, controller, qt_app, library, tmp_path
    ):
        _, first, second, _db = library
        _hold_everything(controller, qt_app, first, second)
        assert controller.heldCount == 2

        target = tmp_path / "cel"
        target.mkdir()
        controller.exportHeld(str(target), 0, 85, False, "")
        result = _wait_for_export(controller, qt_app)

        assert result.get("done") == 2
        assert {p.name for p in target.glob("*.jpg")} == {"a.jpg", "b.jpg"}

    def test_an_empty_tray_exports_nothing(self, controller, qt_app, tmp_path):
        target = tmp_path / "cel2"
        target.mkdir()
        # üres tálcánál a jelzés AZONNAL (szinkron) megy ki — a figyelőt
        # ezért a hívás ELŐTT kell bekötni
        seen = []
        controller.exportFinished.connect(
            lambda done, failed: seen.append((done, failed))
        )

        controller.exportHeld(str(target), 0, 85, False, "")
        qt_app.processEvents()

        assert seen == [(0, 0)]
        assert list(target.glob("*")) == []

    def test_the_selection_is_not_used(
        self, controller, qt_app, library, tmp_path
    ):
        # a tálcán CSAK az első mappa képe van, miközben a rácsban mindkettő
        # látszik — az export a TÁLCÁT viszi, nem a rács tartalmát
        _, first, _second, _db = library
        _load_grid(controller, qt_app, first)
        controller.holdRows([_row_of(controller, first)])
        qt_app.processEvents()

        target = tmp_path / "cel3"
        target.mkdir()
        controller.exportHeld(str(target), 0, 85, False, "")
        _wait_for_export(controller, qt_app)

        assert [p.name for p in target.glob("*.jpg")] == ["a.jpg"]

    def test_a_missing_file_is_skipped_not_fatal(
        self, controller, qt_app, library, tmp_path
    ):
        _, first, second, _db = library
        _hold_everything(controller, qt_app, first, second)
        Path(first / "a.jpg").unlink()

        target = tmp_path / "cel4"
        target.mkdir()
        controller.exportHeld(str(target), 0, 85, False, "")
        result = _wait_for_export(controller, qt_app)

        # a megmaradt kép átmegy; az eltűnt nem akasztja meg a köteget
        assert [p.name for p in target.glob("*.jpg")] == ["b.jpg"]
        assert result.get("done") == 1


class TestDialogUsesTheTray:
    def test_the_dialog_switches_source_with_the_tray(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        dialog = window.findChild(QObject, "exportDialog")
        assert dialog is not None

        assert dialog.property("useTray") is False
        controller.holdRows([0])
        qt_app.processEvents()
        assert dialog.property("useTray") is True

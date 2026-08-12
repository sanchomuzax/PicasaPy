"""Mentés a lemezre / Visszaállítás / Utolsó mentés visszavonása — #444.

A mag (`picasapy.edit.save`) régóta tesztelt; itt az a tárgy, hogy a
felületről elérhető legyen, és hogy a **nem renderelhető láncelemre**
figyelmeztetni lehessen a mentés előtt (#484: a mentés azt véglegesen
eldobná).
"""

from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QSettings, QTimer

from picasapy.edit.save import ORIGINALS_DIR_NAME
from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache


def _jpeg(path: Path, colour=(20, 30, 200)) -> Path:
    image = np.zeros((24, 32, 3), dtype=np.uint8)
    image[:, :] = colour
    cv2.imwrite(str(path), image)
    return path


@pytest.fixture
def library(tmp_path):
    folder = tmp_path / "kepek"
    folder.mkdir()
    _jpeg(folder / "IMG_0001.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, folder)
    return tmp_path, folder, db


@pytest.fixture
def controller(qt_app, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    tmp_path, folder, db = library
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(db, (str(folder),), provider, settings=settings)
    controller.selectFolder(str(folder))
    return controller


def _wait(signal, qt_app, timeout_ms=15000):
    loop = QEventLoop()
    result = {}
    signal.connect(
        lambda done, failed: (result.update(done=done, failed=failed), loop.quit())
    )
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    qt_app.processEvents()
    return result


def _set_filters(controller, qt_app, library, value: str) -> None:
    """A lánc beállítása és BEOLVASTATÁSA: az indexbe a `sync_tree` viszi be
    a `.picasa.ini` tartalmát, a modell onnan kapja a `filters` mezőt."""
    _tmp, folder, db = library
    (folder / ".picasa.ini").write_text(
        f"[IMG_0001.jpg]\nfilters={value}\n", encoding="utf-8"
    )
    with open_index(db) as conn:
        sync_tree(conn, folder)
    controller.selectFolder(str(folder))
    qt_app.processEvents()
    assert controller.photos.photos[0].filters == value


class TestUnrenderableWarning:
    def test_a_renderable_chain_needs_no_warning(
        self, controller, qt_app, library
    ):
        _set_filters(controller, qt_app, library, "sepia=1;bw=1;")

        assert controller.unrenderableFiltersIn([0]) == []

    def test_an_unrenderable_entry_is_reported(self, controller, qt_app, library):
        # a `gamma` a „Régi effektek" fülön szürkén látszik: ismerjük a
        # nevét, de renderelőnk nincs hozzá — a mentés eldobná
        _set_filters(controller, qt_app, library, "sepia=1;gamma=1,0.5;")

        assert controller.unrenderableFiltersIn([0]) == ["gamma"]

    def test_the_empty_selection_is_silent(self, controller):
        assert controller.unrenderableFiltersIn([]) == []


class TestSaveToDisk:
    def test_the_edit_is_burned_into_the_file(self, controller, qt_app, library):
        _, folder, _db = library
        _set_filters(controller, qt_app, library, "bw=1;")
        before = cv2.imread(str(folder / "IMG_0001.jpg"))

        controller.saveRowsToDisk([0])
        result = _wait(controller.saveFinished, qt_app)

        assert result.get("done") == 1
        after = cv2.imread(str(folder / "IMG_0001.jpg"))
        # a fekete-fehér lánc után a három csatorna megegyezik
        assert after[0, 0, 0] == after[0, 0, 1] == after[0, 0, 2]
        assert not np.array_equal(before, after)

    def test_a_backup_is_made_before_saving(self, controller, qt_app, library):
        _, folder, _db = library
        _set_filters(controller, qt_app, library, "bw=1;")

        controller.saveRowsToDisk([0])
        _wait(controller.saveFinished, qt_app)

        originals = folder / ORIGINALS_DIR_NAME
        assert originals.is_dir()
        assert (originals / "IMG_0001.jpg").exists()

    def test_the_empty_selection_reports_nothing_done(self, controller, qt_app):
        seen = []
        controller.saveFinished.connect(
            lambda done, failed: seen.append((done, failed))
        )

        controller.saveRowsToDisk([])
        qt_app.processEvents()

        assert seen == [(0, 0)]


class TestRevertAndUndoSave:
    def _save_once(self, controller, qt_app, library):
        _set_filters(controller, qt_app, library, "bw=1;")
        controller.saveRowsToDisk([0])
        _wait(controller.saveFinished, qt_app)

    def test_revert_brings_the_original_back(self, controller, qt_app, library):
        _, folder, _db = library
        original = cv2.imread(str(folder / "IMG_0001.jpg"))
        self._save_once(controller, qt_app, library)

        controller.revertRowsToOriginal([0])
        result = _wait(controller.revertFinished, qt_app)

        assert result.get("done") == 1
        assert np.array_equal(cv2.imread(str(folder / "IMG_0001.jpg")), original)

    def test_undo_save_keeps_the_edits(self, controller, qt_app, library):
        _, folder, _db = library
        original = cv2.imread(str(folder / "IMG_0001.jpg"))
        self._save_once(controller, qt_app, library)

        controller.undoLastSave([0])
        result = _wait(controller.undoSaveFinished, qt_app)

        assert result.get("done") == 1
        # a FÁJL visszaáll…
        assert np.array_equal(cv2.imread(str(folder / "IMG_0001.jpg")), original)
        # …de a szerkesztési lánc megmarad (ez a Picasa köztes fokozata)
        ini = (folder / ".picasa.ini").read_text(encoding="utf-8")
        assert "bw=1" in ini

    def test_the_menu_can_tell_whether_there_is_anything_to_restore(
        self, controller, qt_app, library
    ):
        _, folder, _db = library
        assert controller.hasSavedBackup([0]) is False

        self._save_once(controller, qt_app, library)

        assert controller.hasSavedBackup([0]) is True

"""#1425 — a felület is lássa a régi `Originals` mappát.

A mag (`picasapy.edit.save`) hiába ismeri mindkét mappanevet, ha a Fájl
menü „Visszaállítás" tétele szürke marad: a `hasSavedBackup()` tiltja a
parancsot, és a felhasználó **magyarázat nélkül** nem tud mit kezdeni a
képével. Ez a néma elutasítás felületi alakja (#1003, #1207, #1213).

A második eset azt méri, hogy amikor a visszaállítás mégis lefut és nincs
megőrzött eredeti, a felhasználó **érthető üzenetet** kap — a
`saveFailedDetails` jelzést a `SaveDialogs.qml` teszi párbeszédbe.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QSettings, QTimer

from picasapy.edit.save import LEGACY_ORIGINALS_DIR_NAME, ORIGINALS_DIR_NAME
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
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(db, (str(folder),), provider, settings=settings)
    controller.selectFolder(str(folder))
    return controller


def _wait(signal, qt_app, timeout_ms=15000):
    loop = QEventLoop()
    result = {}
    signal.connect(
        lambda *args: (result.update(args=args), loop.quit())
    )
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    qt_app.processEvents()
    # #2408: idotullepeskor a `result` uresen maradna, es a bukas egy
    # kesobbi allitason jelentkezne — a muvelet helyett a VARAKOZASRA
    # mutatva. A segito ezert maga all meg.
    assert result, f"#2408: a jelzes {timeout_ms} ms alatt nem erkezett meg"
    return result


class TestAMenuLatjaARegiMappat:
    def test_a_regi_Originals_mappa_is_engedelyezi_a_visszaallitast(
        self, controller, library
    ):
        _tmp, folder, _db = library
        regi = folder / LEGACY_ORIGINALS_DIR_NAME
        regi.mkdir()
        _jpeg(regi / "IMG_0001.jpg", colour=(1, 2, 3))

        assert controller.hasSavedBackup([0]) is True

    def test_ures_regi_mappa_nem_engedelyezi(self, controller, library):
        _tmp, folder, _db = library
        (folder / LEGACY_ORIGINALS_DIR_NAME).mkdir()

        assert controller.hasSavedBackup([0]) is False

    def test_az_uj_mappanev_valtozatlanul_engedelyez(self, controller, library):
        _tmp, folder, _db = library
        uj = folder / ORIGINALS_DIR_NAME
        uj.mkdir()
        _jpeg(uj / "IMG_0001.jpg", colour=(1, 2, 3))

        assert controller.hasSavedBackup([0]) is True


class TestNincsNemaElutasitas:
    def test_a_visszaallitas_erthetoen_megmondja_ha_nincs_eredeti(
        self, controller, qt_app
    ):
        reszletek: list = []
        controller.saveFailedDetails.connect(reszletek.append)

        controller.revertRowsToOriginal([0])
        _wait(controller.revertFinished, qt_app)
        qt_app.processEvents()

        assert reszletek, "a felhasználó semmilyen visszajelzést nem kapott"
        uzenet = "\n".join(reszletek[0])
        assert ORIGINALS_DIR_NAME in uzenet
        assert LEGACY_ORIGINALS_DIR_NAME in uzenet
        assert "Visszaállítás" in uzenet

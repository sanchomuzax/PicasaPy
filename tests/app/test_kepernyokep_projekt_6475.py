"""#6475: a képernyőmentés után megjelenik a Képernyőfelvételek projektmappa.

A tulajdonos (1.0.26, Windows): a program jelezte a képernyőmentést (jobb
alsó lebegő panel), de a Projektek alatt nem volt „Képernyőfelvételek”
mappa. Az ok: a mentés jelzését (`screenCaptureSaved`) csak az értesítő
figyelte, a könyvtár nem; a célmappa (`<Képek>/Picasa/Képernyőfelvételek`)
pedig tipikusan egyetlen figyelt gyökér alatt sincs, így semmi nem vette fel
az indexbe. A javítás a kollázs mintáját követi (`_index_saved_collage`):
a mappa SAJÁT gyökérként kerül be, a figyelt mappákhoz nem nyúlunk.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import pytest
from PySide6.QtGui import QColor, QImage

from support.jpeg_factory import make_jpeg


def _var(qt_app, feltetel, masodperc: float = 15.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.02)
    return bool(feltetel())


@pytest.fixture
def controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    gyoker = tmp_path / "kepek"
    (gyoker / "nyaralas").mkdir(parents=True)
    make_jpeg(gyoker / "nyaralas" / "IMG_0001.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
    ctl = AppController(
        tmp_path / "index.db",
        (str(gyoker),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl.start()
    assert _var(qt_app, lambda: not ctl._sync_running, 20.0)
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0)


def _ment(cel: Path) -> Path:
    from picasapy.app.screen_capture import save_screenshot

    kep = QImage(64, 48, QImage.Format.Format_RGB888)
    kep.fill(QColor(30, 120, 200))
    return save_screenshot(kep, cel, "Jegyzettomb", datetime(2026, 11, 3, 10, 0))


def test_az_elso_kepernyomentes_utan_megjelenik_a_projektmappa(controller, qt_app, tmp_path):
    cel = tmp_path / "Kepek" / "Picasa" / "Képernyőfelvételek"
    ut = _ment(cel)
    assert controller._root_for_folder(str(cel)) is None, "a cél a figyelt körön kívül van"

    controller.indexScreenCapture(str(ut))

    def megjelent() -> bool:
        return any(Path(p["path"]) == cel for p in controller.projectFolders)

    assert _var(qt_app, megjelent), "a Képernyőfelvételek nem jelent meg a Projektek alatt"
    sor = next(p for p in controller.projectFolders if Path(p["path"]) == cel)
    assert sor["count"] == 1


def test_a_figyelt_mappak_nem_bovulnek(controller, qt_app, tmp_path):
    elotte = tuple(controller._roots)
    ut = _ment(tmp_path / "Kepek" / "Picasa" / "Képernyőfelvételek")

    controller.indexScreenCapture(str(ut))
    assert controller.waitForBackgroundWorkers(15.0)

    assert tuple(controller._roots) == elotte


def test_a_mentes_jelzese_a_konyvtarhoz_is_eljut():
    """A gyári bekötés: a jelzés a vezérlő indexelőjéhez is be van kötve."""
    forras = Path(__file__).resolve().parents[2] / "src/picasapy/app/application_startup_qml.py"
    szoveg = forras.read_text(encoding="utf-8")
    assert "screenCaptureSaved.connect(controller.indexScreenCapture)" in szoveg

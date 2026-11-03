"""A célzott szinkron változás nélkül nem ismétlődik (#6476).

A tulajdonos naplójában (1.0.26, Windows) a „könyvtárszinkron befejeződött”
és a mappafa-frissítés kb. tízmásodpercenként újra lefutott, akkor is, ha
semmi nem változott, és a felület akadt. Az ok: a látott mappa lekérdező
időzítője (#1275) minden körben teljes célzott szinkront indított, a
`syncFinished` pedig a felület szálán teljes újratöltést (mappafa, albumok,
ini-söprés) vált ki.

A javítás: a célzott szinkron előtt a mappa fájllistájából (név, idő,
méret) ujjlenyomat készül; ha ez azonos az előző sikeres szinkronéval, a
mappa kimarad, és ha egyik mappa sem változott, `syncFinished` sem megy ki.
A helyben átírt fájl (amit a mappa-pecsét nem lát, #1435) az ujjlenyomatban
látszik, mert a fájl ideje és mérete is benne van.
"""

from __future__ import annotations

import os
import time

import pytest

from support.figyelo import allitsd_le_a_figyelot
from support.jpeg_factory import make_jpeg


def _var(qt_app, feltetel, masodperc: float = 20.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.02)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _porgess(qt_app, masodperc: float) -> None:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        time.sleep(0.02)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library, monkeypatch):
    """Élő vezérlő, rövid lekérdezési időközzel (a valódi időzítőt méri)."""
    from PySide6.QtCore import QSettings

    from picasapy.app import library_controller
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    monkeypatch.setattr(library_controller, "FOLDER_POLL_MS", 150)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl.start()
    assert _var(qt_app, lambda: not ctl._sync_running, 20.0)
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _csendes_mappa(controller, library, qt_app):
    mappa = library / "nyaralas"
    controller.selectFolder(str(mappa))
    assert _var(qt_app, lambda: controller.photos.rowCount() == 2)
    allitsd_le_a_figyelot(controller)
    # az első lekérdezési kör még szinkronizál (nincs előző ujjlenyomat)
    _porgess(qt_app, 0.6)
    assert _var(qt_app, lambda: not controller._dirty_running)
    return mappa


def test_valtozas_nelkul_nem_fut_ujra_a_szinkron(controller, library, qt_app):
    _csendes_mappa(controller, library, qt_app)
    jelzesek = []
    controller.syncFinished.connect(lambda: jelzesek.append(1))

    _porgess(qt_app, 1.5)  # kb. tíz lekérdezési kör

    assert jelzesek == [], (
        f"változatlan mappán {len(jelzesek)} szinkron futott le 1,5 s alatt"
    )


def test_uj_kep_utan_ujra_fut(controller, library, qt_app):
    mappa = _csendes_mappa(controller, library, qt_app)

    make_jpeg(mappa / "IMG_7777.jpg")

    assert _var(qt_app, lambda: controller.photos.rowCount() == 3)


def test_helyben_atirt_fajl_utan_ujra_fut(controller, library, qt_app):
    """A mappa-pecsét ezt nem látja (#1435), az ujjlenyomat igen."""
    mappa = _csendes_mappa(controller, library, qt_app)
    jelzesek = []
    controller.syncFinished.connect(lambda: jelzesek.append(1))

    cel = mappa / "IMG_0001.jpg"
    make_jpeg(cel, size=(64, 48))
    regi = cel.stat()
    os.utime(cel, ns=(regi.st_atime_ns, regi.st_mtime_ns + 5_000_000_000))

    assert _var(qt_app, lambda: jelzesek, 10.0), "az átírt fájl után nem futott szinkron"


def test_felhasznaloi_frissites_valtozas_nelkul_is_fut(controller, library, qt_app):
    mappa = _csendes_mappa(controller, library, qt_app)
    jelzesek = []
    controller.syncFinished.connect(lambda: jelzesek.append(1))

    controller._on_folders_dirty([str(mappa)], felhasznaloi=True)

    assert _var(qt_app, lambda: jelzesek, 10.0), "a kért frissítés kimaradt"


def test_a_varolista_valtozas_nelkul_is_kiurul(controller, library, qt_app):
    """A kimaradt szinkron után is behozza a közben érkezett jelzéseket."""
    mappa = _csendes_mappa(controller, library, qt_app)
    masik = library / "masik"
    masik.mkdir()
    make_jpeg(masik / "IMG_0100.jpg")
    controller._pending_dirty.add(str(masik))

    controller._on_folders_dirty([str(mappa)])

    assert _var(qt_app, lambda: not controller._pending_dirty, 10.0)

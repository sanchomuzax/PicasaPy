"""#6697: a meglévő könyvtár képei a teljes bejárás előtt jelenjenek meg."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from PySide6.QtCore import QSettings

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


def test_a_kepterkep_hatterben_megjelenik_a_bejaras_vege_elott(
    qt_app, tmp_path: Path, monkeypatch
):
    """A kezdeti indexlekérdezés háttérben fut, és nem vár a mappaszinkronra."""
    library = tmp_path / "kepek"
    library.mkdir()
    make_jpeg(library / "a.jpg", size=(32, 24))
    make_jpeg(library / "b.jpg", size=(32, 24))
    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(conn, library)

    from picasapy.app import controller as controller_module
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    fo_szal = threading.get_ident()
    lekerdezo_szalak: list[int] = []
    eredeti_all_photos = controller_module.all_photos

    def naplozott_all_photos(conn):
        lekerdezo_szalak.append(threading.get_ident())
        return eredeti_all_photos(conn)

    monkeypatch.setattr(controller_module, "all_photos", naplozott_all_photos)
    controller = AppController(
        db_path,
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )

    bejaras_elindult = threading.Event()
    bejaras_feloldva = threading.Event()

    def lassu_mappabejaras():
        bejaras_elindult.set()
        bejaras_feloldva.wait(10.0)
        controller.syncFinished.emit()

    monkeypatch.setattr(controller, "_sync_worker", lassu_mappabejaras)
    try:
        controller.start()
        assert bejaras_elindult.wait(3.0), "a próba mappabejárás nem indult el"

        hatarido = time.monotonic() + 5.0
        while time.monotonic() < hatarido and controller.photos.rowCount() < 2:
            qt_app.processEvents()
            time.sleep(0.01)

        assert lekerdezo_szalak, "a meglévő indexet nem kérdezte le a vezérlő"
        assert all(szal != fo_szal for szal in lekerdezo_szalak), (
            "a teljes könyvtár lekérdezése a felület szálán futott"
        )
        assert controller.photos.rowCount() == 2, (
            "a képrács nem töltődött fel, amíg a mappabejárás blokkolt"
        )
        assert not bejaras_feloldva.is_set(), (
            "a képrács csak a teljes mappabejárás után töltődhetett fel"
        )
    finally:
        bejaras_feloldva.set()
        controller.waitForBackgroundWorkers(10.0)
        qt_app.processEvents()
        controller.shutdown()


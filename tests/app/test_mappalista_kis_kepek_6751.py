"""A bal sáv a „Kis képek” beállítás szerint számol és mutat mappát (#6751).

## A tulajdonos jelentése (1.0.85, Windows)

A `202611-b (5)` mappa a bal sávban öt képet mutatott, a rácsban viszont
egy sem látszott: mind az öt kicsi képernyőkép, és a „Csak nagy képek”
szűrő (Nézet ▸ Kis képek kikapcsolva) elrejtette őket. „Miért látja, ha
mégsem látja?”

## Az eredeti

A szűrő a binárisban a kép GYŰJTEMÉNYBE vételénél dönt (a közös hozzáadási
ág, `0x0065f3c6`-`0x0065f5a9`, küszöb `0x0065d010` / `0x0065f521`), tehát a
kiszűrt kép a mappába sem kerül be: a darabszám csak a látható képeket
számolja, a csak kis képeket tartalmazó mappa pedig nem jelenik meg.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def index(tmp_path):
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "kepek"
    kicsi = gyoker / "kicsi"
    vegyes = gyoker / "vegyes"
    kicsi.mkdir(parents=True)
    vegyes.mkdir()
    make_jpeg(kicsi / "k1.jpg", size=(146, 107))
    make_jpeg(kicsi / "k2.jpg", size=(96, 134))
    make_jpeg(vegyes / "v1.jpg", size=(120, 90))
    make_jpeg(vegyes / "v2.jpg", size=(800, 600))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    return db, kicsi, vegyes


def _mappak(model) -> dict[str, int]:
    return {
        sor[2]: sor[3] for sor in model._rows if sor[0] == "folder"
    }


def test_szuro_nelkul_minden_kep_szamit(qt_app, index):
    from picasapy.app.folder_list_model import FolderListModel
    from picasapy.index import open_index

    db, kicsi, vegyes = index
    model = FolderListModel()
    with open_index(db) as conn:
        model.load(conn, kis_kepek_rejtve=False)
    mappak = _mappak(model)
    assert mappak[str(kicsi)] == 2
    assert mappak[str(vegyes)] == 2


def test_szurovel_csak_a_lathato_kepek_szamitanak(qt_app, index):
    from picasapy.app.folder_list_model import FolderListModel
    from picasapy.index import open_index

    db, kicsi, vegyes = index
    model = FolderListModel()
    with open_index(db) as conn:
        model.load(conn, kis_kepek_rejtve=True)
    mappak = _mappak(model)
    assert str(kicsi) not in mappak, (
        "a csak kis képeket tartalmazó mappa a bal sávban maradt, pedig a "
        "rácsban egy képe sem látszik"
    )
    assert mappak[str(vegyes)] == 1, "a darabszám a rejtett kis képet is számolja"


def test_a_kapcsolo_a_bal_savot_is_frissiti(qt_app, tmp_path):
    """A vezérlőn át: a Kis képek bekapcsolása visszahozza a mappát."""
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    gyoker = tmp_path / "kepek"
    kicsi = gyoker / "kicsi"
    nagy = gyoker / "nagy"
    kicsi.mkdir(parents=True)
    nagy.mkdir()
    make_jpeg(kicsi / "k1.jpg", size=(146, 107))
    make_jpeg(nagy / "n1.jpg", size=(800, 600))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(gyoker),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    try:
        ctl.setShowOnlyBigImages(True)
        ctl._reload()
        assert str(kicsi) not in ctl._folders.folder_paths()
        ctl.setShowOnlyBigImages(False)
        assert str(kicsi) in ctl._folders.folder_paths(), (
            "a Kis képek bekapcsolása után a mappa nem jelent meg a bal sávban"
        )
    finally:
        ctl.shutdown()
        assert ctl.waitForBackgroundWorkers(30.0)

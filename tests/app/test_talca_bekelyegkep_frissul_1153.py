"""A tálca (és a Klipek lap) bélyegképe KÖVETI a fájl változását (#1153).

## A bejelentett tünet

> „a kollázs-szerkesztő Klipek füle nem frissíti az indexképeket"

## A lánc, mérve

A bélyegkép-URL már **gyorstár-törő** (a #1186 óta): benne van az
`mtime_ns` és a méret, tehát egy felülírt fájl ÚJ URL-t kap, és a Qt
URL szerinti gyorstára nem tarthatja meg a régi képpontokat.

⛔ **Csakhogy senki nem kérte el az újat.** A `trayItems` értesítője a
`heldChanged`, ami KIZÁRÓLAG a tálca-állapot (tartás/felhasználtság)
változásakor szól. A `_tray_records_cache` szintén csak ott ürül. Egy
SZERKESZTÉS — ami a rács modelljét frissíti (`set_photos` → új rekordok,
új `mtime_ns`) — a tálcát nem érintette:

    fájl felülírva → a rács új URL-t számol → a rács frissül
                   → a tálca ugyanazt a RÉGI URL-t adja tovább

Ez a #1798 hibaosztályának a rokona: a gépezet megvan, csak a jelzés nem
ér el odáig.

## A foga

A teszt a VALÓDI úton megy: a rekordokat kicseréli (ahogy egy
szerkesztés utáni újraolvasás tenné), és a `trayItems`-ből kiolvasott
URL-t hasonlítja. A régi kódon a két URL AZONOS — ott bukik.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "a").mkdir(parents=True)
    make_jpeg(root / "a" / "x.jpg", size=(80, 60))
    make_jpeg(root / "a" / "y.jpg", size=(80, 60))
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    return ctl


def _url(controller, nev: str) -> str:
    for elem in controller.trayItems:
        if elem["name"] == nev:
            return elem["thumbUrl"]
    raise AssertionError(f"{nev} nincs a tálcán")


def _felulir(controller, ut) -> None:
    """A fájl felülírása + a VALÓDI út: célzott mappa-újraolvasás.

    ⚠️ NEM `rescan()`: az inkrementális bejárás a MAPPA mtime-jára szűr, egy
    helyben felülírt fájl viszont nem változtatja meg a mappa mtime-ját —
    a folyamat átugraná. Az alkalmazásban a szerkesztés-mentés is a célzott
    `resyncFolder`-t hívja (`wire_fileops`), ezért a teszt is azt.
    """
    from PySide6.QtCore import QEventLoop, QTimer

    make_jpeg(ut, size=(300, 200))
    loop = QEventLoop()
    controller.syncFinished.connect(loop.quit)
    controller.resyncFolder(str(ut.parent))
    QTimer.singleShot(10000, loop.quit)
    loop.exec()


def _sor(controller, nev: str) -> int:
    for i, photo in enumerate(controller.photos.photos):
        if photo.name == nev:
            return i
    raise AssertionError(nev)


class TestABelyegkepKovetiAFajlt:
    def test_a_SZERKESZTES_uj_URL_t_ad(self, controller, library):
        """A foga: a régi kódon a két URL azonos, mert a `trayItems` nem
        számol újra."""
        controller.holdRows([_sor(controller, "x.jpg")])
        elotte = _url(controller, "x.jpg")

        # a fájl felülírása — pontosan az, amit egy szerkesztés-mentés tesz
        _felulir(controller, library / "a" / "x.jpg")

        utana = _url(controller, "x.jpg")
        assert utana != elotte, (
            "a tálca bélyegkép-URL-je NEM változott a fájl felülírása után "
            "— a Qt a régi képpontokat tartaná meg"
        )

    def test_a_TOBBI_elem_URL_je_valtozatlan(self, controller, library):
        """Ne az egész tálca köttessen újra minden változásnál."""
        controller.holdRows(
            [_sor(controller, "x.jpg"), _sor(controller, "y.jpg")]
        )
        y_elotte = _url(controller, "y.jpg")

        _felulir(controller, library / "a" / "x.jpg")

        assert _url(controller, "y.jpg") == y_elotte


class TestAJelzesIsElmegy:
    def test_a_heldChanged_JELZ_a_rekord_csereje_utan(self, controller, library):
        """A QML-kötés csak jelzésre értékelődik újra — az érték magától
        nem jut el a felületre.

        A `trayItems` értesítője a `heldChanged`; ha az nem szól, a Klipek
        lap és a tálca a RÉGI listát mutatja akkor is, ha az érték már jó
        volna.
        """
        controller.holdRows([_sor(controller, "x.jpg")])
        jelzesek = []
        controller.heldChanged.connect(lambda: jelzesek.append(1))

        _felulir(controller, library / "a" / "x.jpg")

        assert jelzesek, (
            "a rekordok cseréje után a tálca nem jelzett — a felület a régi "
            "bélyegképeket mutatná"
        )

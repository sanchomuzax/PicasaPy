"""#1438: a csillagozás TELJES lánca — `.picasa.ini` → index → csillagozott nézet.

A #1436 mérése közben úgy tűnt, hogy a `toggleStar()` után a csillagozott
nézet üresen marad. A kimérés (ez a fájl) megmutatta, hogy a lánc mindhárom
lépése ép; a tünetet a művelet ASZINKRON volta okozta: a `toggleStar` a
lemezírást és az index-frissítést háttérszálon végzi (#141/#438), és a
mérés nem várta meg a `photoOpFinished` jelzést.

Ez a fájl ezért két dolgot rögzít, KÜLÖN állításokkal:

1. **A lánc mindhárom lépése** — eddig csak az ini-írás és a rács-modell
   volt őrizve (`test_controller.py::TestToggleStar`); hogy az INDEX
   tényleg `star = 1`-re vált, és hogy a csillagozott nézet (`showStarred`)
   tényleg meg is találja a képet, semmi nem mondta ki.
2. **Az aszinkronitás maga** — a `test_a_varakozas_nelkuli_meres_uresen_lat`
   determinisztikusan előállítja a #1438-ban jelentett tünetet, hogy a
   következő mérés ne terméki hibának nézze.

A felületi belépési pontokat (tálca- és diavetítés-gomb) VALÓDI kattintással
a `qml_functional/test_csillag_belepesi_pontok_1438.py` méri.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """Két csillagozatlan kép egy mappában — a kiindulás tiszta lap."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg", taken_at="2025:05:01 07:00:00")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg", taken_at="2025:05:02 07:00:00")
    return root


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "index.db"


@pytest.fixture
def controller(qt_app, tmp_path: Path, library: Path, db_path: Path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(db_path) as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    # elszigetelt QSettings — a valódi felhasználói beállításokat ne írjuk
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        db_path,
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le a teardownban"


def _ini_text(library: Path) -> str:
    ini = library / "nyaralas" / ".picasa.ini"
    return ini.read_text(encoding="utf-8") if ini.exists() else ""


def _index_star(db_path: Path, name: str) -> int:
    """A kép `star` oszlopa az SQLite-indexben — a lánc KÖZÉPSŐ lépése."""
    with open_index(db_path) as conn:
        row = conn.execute(
            "SELECT star FROM photos WHERE name = ?", (name,)
        ).fetchone()
    assert row is not None, f"{name} nincs az indexben"
    return int(row[0])


def _starred_names(controller) -> list[str]:
    """A csillagozott nézet tartalma — a lánc HARMADIK, látható lépése."""
    controller.showStarred()
    return [photo.name for photo in controller.photos.photos]


class TestACsillagozasTeljesLanca:
    """A csillag útja a lemeztől a látható nézetig, lépésenként kimondva."""

    def test_egy_kep_csillagozasa_mindharom_lepesen_atmegy(
        self, controller, library: Path, db_path: Path
    ) -> None:
        controller.selectFolder(str(library / "nyaralas"))
        wait_for_photo_op(controller, lambda: controller.toggleStar(0))

        # (a) igazságforrás: a .picasa.ini
        assert "star=yes" in _ini_text(library).split("[IMG_0001.jpg]")[1]
        # (b) index: a csillagozott nézet ebből dolgozik
        assert _index_star(db_path, "IMG_0001.jpg") == 1
        assert _index_star(db_path, "IMG_0002.jpg") == 0
        # (c) a látható nézet
        assert _starred_names(controller) == ["IMG_0001.jpg"]

    def test_csillag_levetele_mindharom_lepesen_atmegy(
        self, controller, library: Path, db_path: Path
    ) -> None:
        controller.selectFolder(str(library / "nyaralas"))
        wait_for_photo_op(controller, lambda: controller.toggleStar(0))
        assert _starred_names(controller) == ["IMG_0001.jpg"]

        # a levételhez vissza a mappára: a csillagozott nézet sorindexei
        # nem a mappáéi
        controller.selectFolder(str(library / "nyaralas"))
        wait_for_photo_op(controller, lambda: controller.toggleStar(0))

        assert "star=yes" not in _ini_text(library)
        assert _index_star(db_path, "IMG_0001.jpg") == 0
        assert _starred_names(controller) == []

    def test_tobb_kep_csillagozasa_mindharom_lepesen_atmegy(
        self, controller, library: Path, db_path: Path
    ) -> None:
        """A tálca TÖBBES útja (`toggleStarMany`) — ez szinkron, kötegelt."""
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStarMany([0, 1])

        ini = _ini_text(library)
        assert "star=yes" in ini.split("[IMG_0001.jpg]")[1]
        assert "star=yes" in ini.split("[IMG_0002.jpg]")[1]
        assert _index_star(db_path, "IMG_0001.jpg") == 1
        assert _index_star(db_path, "IMG_0002.jpg") == 1
        assert _starred_names(controller) == ["IMG_0001.jpg", "IMG_0002.jpg"]

    def test_tobb_kep_csillagjanak_levetele(
        self, controller, library: Path, db_path: Path
    ) -> None:
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStarMany([0, 1])
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStarMany([0, 1])

        assert "star=yes" not in _ini_text(library)
        assert _index_star(db_path, "IMG_0001.jpg") == 0
        assert _starred_names(controller) == []


class TestACsillagozasAszinkron:
    """A #1438-ban jelentett tünet forrása — nem terméki hiba, de csapda."""

    def test_a_varakozas_nelkuli_meres_uresen_lat(
        self, controller, library: Path, monkeypatch
    ) -> None:
        """A lassított ini-írás determinisztikusan előállítja a tünetet.

        A `toggleStar` azonnal visszatér, a lemezírás és az index-UPDATE a
        háttérszálon fut. Aki a hívás UTÁN rögtön a csillagozott nézetet
        kérdezi, üres listát lát — pontosan ezt jelentette a #1438. A
        `photoOpFinished` bevárása (`wait_for_photo_op`) után viszont ott a
        kép. A teszt mindkét oldalt kimondja, hogy a különbség ne legyen
        többé találgatás kérdése.
        """
        from picasapy.app import photo_ops_controller as ops

        eredeti_update_document = ops.update_document

        def lassitott(*args, **kwargs):
            # a főszálnak biztosan legyen ideje lekérdezni a nézetet, mielőtt
            # a háttérszál végez
            time.sleep(0.4)
            return eredeti_update_document(*args, **kwargs)

        monkeypatch.setattr(ops, "update_document", lassitott)

        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(0)  # SZÁNDÉKOSAN nem várunk a jelzésre
        assert _starred_names(controller) == [], (
            "a lassított írás alatt a nézetnek még üresnek KELL lennie — ha "
            "ez a sor elbukik, a művelet már nem aszinkron, és a fenti "
            "magyarázat elavult"
        )

        assert controller.waitForBackgroundWorkers(15.0)
        assert _starred_names(controller) == ["IMG_0001.jpg"], (
            "a háttérmunka befejeződése után a csillagnak látszania kell"
        )

    def test_toggle_star_jelez_a_vegen(self, controller, library: Path) -> None:
        """A `photoOpFinished` tényleg megérkezik — enélkül nincs mit várni."""
        controller.selectFolder(str(library / "nyaralas"))
        # a segéd maga bukik el, ha a jelzés elmarad (#475)
        wait_for_photo_op(controller, lambda: controller.toggleStar(1))
        assert controller.photos.photos[1].star is True

    def test_ervenytelen_sorindex_nem_ad_jelzest(
        self, controller, library: Path
    ) -> None:
        """Ismert csapda: érvénytelen sorra a `toggleStar` NÉMÁN nem csinál
        semmit — jelzés sem jön, tehát a `wait_for_photo_op` időtúllépéssel
        bukik, ami tartalmi hibának LÁTSZIK. Aki a jövőben ilyen bukást lát,
        előbb a sorindexet nézze meg."""
        from PySide6.QtCore import QEventLoop, QTimer

        controller.selectFolder(str(library / "nyaralas"))
        jelzesek: list[bool] = []
        controller.photoOpFinished.connect(lambda: jelzesek.append(True))

        controller.toggleStar(99)

        loop = QEventLoop()
        QTimer.singleShot(300, loop.quit)
        loop.exec()
        assert jelzesek == []
        assert "star=yes" not in _ini_text(library)

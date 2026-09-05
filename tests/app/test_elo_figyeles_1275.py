"""Az élő mappa-figyelés a MODELLIG elér (#1275).

## A tulajdonos jelentése (v0.8.51, Windows)

> „A PicasaPy nem veszi észre működés közben, ha egy új kép kerül a
> mappáiba. Feltárás volt rá elvileg. Restart után észreveszi."

## Miért nem fogta meg egyetlen meglévő teszt sem

A lánc négy szakaszból áll, és **mindkét vége** tesztelve volt, a közepe
nem:

| szakasz | ki mérte |
|---|---|
| watchdog → mappa-jelzés | `tests/scanner/test_watcher.py` |
| jelzés → index → modell | `test_controller.py::TestLiveWatch` — de a `_on_folders_dirty()` **KÖZVETLEN hívásával** |
| a kettő ÖSSZEKÖTVE | **senki** |

A `controller` fixture soha nem hívta a `start()`-ot, tehát a valódi
figyelő el sem indult a tesztekben. Így az a hiba, hogy a figyelő nem
jut el a vezérlőig, zöld tesztek mellett mehetett ki.

⚠️ Ez ugyanaz a hibaosztály, mint a #1153-nál: ott a slot közvetlen
hívása adott hamis zöldet a kattinthatatlan gomb fölött.
"""

from __future__ import annotations

import time

import pytest

from support.jpeg_factory import make_jpeg


def _var(qt_app, feltetel, masodperc: float = 20.0) -> bool:
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő)."""
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


def _nyugalom(qt_app, ctl, masodperc: float = 20.0) -> bool:
    """Megvárja, amíg NINCS futó szinkron.

    ⚠️ A `rescan()` első sora: `if self._sync_running: return` — egy író
    elég. A `start()` maga is indít egy szinkront, tehát ha a teszt
    azonnal `rescan()`-t hív, az NÉMÁN elnyelődik. Helyi gépen ez sosem
    látszott (a kezdeti szinkron milliszekundumok alatt lefut), a CI
    terhelt futtatóján viszont elbukott — a hiba a tesztben volt, nem a
    termékben."""
    return _var(qt_app, lambda: not ctl._sync_running, masodperc)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    return root


@pytest.fixture
def elo_controller(qt_app, tmp_path, library):
    """Vezérlő ÉLŐ figyeléssel — a `start()` ezt is felhúzza."""
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

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
    # a kezdeti szinkron fusson le, mielőtt a teszt bármit állít
    assert _var(qt_app, lambda: not ctl._sync_running, 20.0), (
        "#2408: a szinkron nem állt le 20 s alatt — a teszt hiányos "
        "állapoton menne tovább"
    )
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


class TestAzUjKepMegjelenik:
    def test_a_futas_kozben_bemasolt_kep_megjelenik(
        self, elo_controller, library, qt_app
    ):
        """A tulajdonos tünete: csak újraindítás után veszi észre."""
        mappa = library / "nyaralas"
        elo_controller.selectFolder(str(mappa))
        assert _var(qt_app, lambda: elo_controller.photos.rowCount() == 2), (
            "a kiinduló állapot nem állt be"
        )

        make_jpeg(mappa / "IMG_9999.jpg")

        assert _var(qt_app, lambda: elo_controller.photos.rowCount() == 3), (
            "a futás közben bemásolt kép nem jelent meg — az élő figyelés "
            "nem ér el a modellig"
        )

    def test_a_torolt_kep_eltunik(self, elo_controller, library, qt_app):
        mappa = library / "nyaralas"
        elo_controller.selectFolder(str(mappa))
        assert _var(qt_app, lambda: elo_controller.photos.rowCount() == 2)

        (mappa / "IMG_0002.jpg").unlink()

        assert _var(qt_app, lambda: elo_controller.photos.rowCount() == 1), (
            "a futás közben törölt kép a nézetben maradt"
        )


class TestAHalozatiTartalek:
    r"""NAS-mounton (SMB/NFS) NEM érkezik inotify-esemény — mérve a
    `docs/benchmarks/rpi5-sqlite-inotify.md`-ben. Ilyenkor az 5 percenkénti
    periodikus `rescan()` az egyetlen út, amin az új kép bejöhet.

    ⚠️ A tulajdonos gyűjteménye NAS-on van (`\\DS215j\...`), tehát nála
    GYAKORLATILAG ez a tartalék működik — vagy nem működik semmi."""

    def test_a_periodikus_rescan_behozza_az_uj_kepet(
        self, elo_controller, library, qt_app
    ):
        mappa = library / "nyaralas"
        elo_controller.selectFolder(str(mappa))
        assert _var(qt_app, lambda: elo_controller.photos.rowCount() == 2)
        # a figyelőt LEÁLLÍTJUK: ez a hálózati megosztás helyzete
        elo_controller._watcher.stop()
        elo_controller._watcher = None
        assert _nyugalom(qt_app, elo_controller), "a kezdeti szinkron nem állt le"

        make_jpeg(mappa / "IMG_8888.jpg")
        elo_controller.rescan()

        assert _var(qt_app, lambda: elo_controller.photos.rowCount() == 3), (
            "a periodikus rescan sem hozta be az új képet — hálózati "
            "meghajtón ez az EGYETLEN út"
        )

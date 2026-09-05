"""A MÁSOLÁS is indítson célzott resyncet a célmappára (#1522).

## Mit mértünk, és miért lett ebből javítás

A #1515 mérése közben derült ki, hogy a `_run_batch` csak `move` esetén
bocsát ki jelzést, tehát a `wire_fileops` célzott újraolvasása kimaradt a
másolásnál. A kérdés az volt: elfedi-e ezt a `LibraryWatcher`.

A mérés (valódi vezérlő, valódi időzítők, produkciós `FOLDER_POLL_MS`)
szerint **többnyire igen, egy esetben viszont NEM**:

| eset | watcher | késés |
|---|---|---|
| másolás a LÁTOTT mappába | be | 1,05 s |
| másolás a LÁTOTT mappába | ki | 9,78 s (#1275 lekérdezés) |
| másolás MÁS, indexelt mappába | be | 1,05 s |
| másolás MÁS, indexelt mappába | ki | 9,82 s (#1435 sweep) |
| **másolás ÚJ, indexeletlen mappába** | **ki** | **nem jelent meg 25 s alatt** |
| ugyanaz ÁTHELYEZÉSSEL (kontroll) | ki | 0,06 s |

Az utolsó két sor a lelet: **azonos helyzetben az áthelyezés 0,06 s, a
másolás öt percig (a teljes rescanig) láthatatlan.** Az indexeletlen
célmappát ugyanis a #1275 lekérdezés nem nézi (nem az a látott mappa), és
a #1435 sweep sem (csak a feedben MÁR SZEREPLŐ mappákat pecsételi).

## Miért nem elég azt mondani, hogy „majd a watcher"

A projekt álláspontja végig az volt, hogy a figyelőre nem építünk (a
`LibraryWatcher` docstringje, a #1275 és a #1435 is kikapcsolt figyelővel
mér). Ennek itt két, NAS-tól független oka is van: a `LibraryWatcher.start`
csak azokat a gyökereket veszi fel, amelyek INDULÁSKOR léteznek, és az
inotify figyelőkeret (`max_user_watches`) nagy gyűjteménynél elfogyhat —
mindkét esetben a figyelő némán nem szól, a másolat pedig öt percig
láthatatlan marad.

Ezért a másolás is kap célzott resyncet, ahogy az áthelyezés.
"""

from __future__ import annotations

import time

import pytest

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


class TestAMasolasResyncetKer:
    """A bekötés szintje: a VEZÉRLŐ slotját hívjuk, valódi fájlokkal."""

    class _StubController:
        def __init__(self, roots):
            self.watchedFolders = list(roots)
            self.resynced = []

        def resyncFolder(self, folder):
            self.resynced.append(folder)

    @pytest.fixture
    def wired(self, qt_app, tmp_path):
        from picasapy.app import application
        from picasapy.app.fileops_controller import FileOpsController

        root = tmp_path / "kepek"
        (root / "forras").mkdir(parents=True)
        (root / "cel").mkdir()
        make_jpeg(root / "forras" / "IMG_0001.jpg")
        stub = self._StubController([str(root)])
        fileops = FileOpsController()
        application.wire_fileops(fileops, stub)
        return fileops, stub, root

    def test_a_masolas_a_celmappat_ujraolvastatja(self, wired):
        """A `copyPhotos` slot — nem a jelzés kézi kibocsátása."""
        fileops, stub, root = wired

        fileops.copyPhotos(
            [str(root / "forras" / "IMG_0001.jpg")], str(root / "cel"), "rename"
        )

        assert str(root / "cel") in stub.resynced, (
            "a másolás nem kért célzott újraolvasást a célmappára — a "
            "másolat az ötperces rescanig láthatatlan marad"
        )

    def test_a_sikertelen_masolas_nem_ker_resyncet(self, wired, tmp_path):
        """Nem létező forrás: ne kérjünk fölösleges újraolvasást."""
        fileops, stub, root = wired

        fileops.copyPhotos(
            [str(root / "forras" / "NINCS_ILYEN.jpg")], str(root / "cel"), "rename"
        )

        assert stub.resynced == []

    def test_figyelt_koron_kivuli_cel_kimarad(self, wired, tmp_path):
        """Export-cél a figyelt gyökereken kívül: nem megy az indexbe."""
        fileops, stub, root = wired
        kivul = tmp_path / "kivul"
        kivul.mkdir()

        fileops.copyPhotos(
            [str(root / "forras" / "IMG_0001.jpg")], str(kivul), "rename"
        )

        assert stub.resynced == []


class TestAMasolatMegjelenikAFigyeloNelkul:
    """A jegy tényleges helyzete, végponttól végpontig.

    A figyelő ÉS a #1275 lekérdezés is le van állítva — így egyedül a
    másolás célzott resyncje maradhat, ami a képet behozza. Ez a foga:
    a javítás nélkül a másolat csak az ötperces rescannel jönne be.
    """

    @pytest.fixture
    def egyseg(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app import application as app_module
        from picasapy.app.controller import AppController
        from picasapy.app.fileops_controller import FileOpsController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        library = tmp_path / "kepek"
        (library / "forras").mkdir(parents=True)
        make_jpeg(library / "forras" / "IMG_0001.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = AppController(
            tmp_path / "index.db",
            (str(library),),
            provider,
            settings=settings,
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        ctl.start()
        assert _var(qt_app, lambda: not ctl._sync_running), (
            "#2408: a szinkron nem állt le időben — a teszt hiányos "
            "állapoton menne tovább"
        )
        # a figyelő és a lekérdezés is LE: csak a célzott resync maradhat
        if ctl._watcher is not None:
            ctl._watcher.stop()
            ctl._watcher = None
        if ctl._folder_poll_timer is not None:
            ctl._folder_poll_timer.stop()
        assert _var(qt_app, lambda: not ctl._sync_running), (
            "#2408: a szinkron nem állt le időben — a teszt hiányos "
            "állapoton menne tovább"
        )
        fileops = FileOpsController()
        app_module.wire_fileops(fileops, ctl)
        yield ctl, fileops, library
        ctl.shutdown()
        assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"

    def test_uj_mappaba_masolt_kep_megjelenik(self, egyseg, qt_app):
        ctl, fileops, library = egyseg
        ctl.selectFolder(str(library / "forras"))
        assert _var(qt_app, lambda: ctl.photos.rowCount() == 1)
        uj = library / "ujmappa"
        uj.mkdir()

        fileops.copyPhotos(
            [str(library / "forras" / "IMG_0001.jpg")], str(uj), "rename"
        )

        assert _var(qt_app, lambda: ctl.photos.rowCount() == 2), (
            "a másolat nem jelent meg a rácson — figyelő és #1275 "
            "lekérdezés nélkül csak a célzott resync hozhatja be"
        )

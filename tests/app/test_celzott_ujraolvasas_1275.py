"""A LÁTOTT mappa célzott újraolvasása — a hálózati garancia (#1275).

## A bináris mondja meg az irányt

Az eredeti Picasa **nem használ operációs rendszer-szintű fájlfigyelést**:
a `ReadDirectoryChangesW` és a `SHChangeNotifyRegister` nincs is
importálva, a `FindFirstChangeNotification`-re **nulla** hivatkozás van.
Helyette újraolvas és összehasonlít (`ytDirScannerChangeList`), amit a
beépített `WriteDirscannerCSV` három pillanatképe is megerősít.
Levezetés: `docs/specs/picasa-mappakezelo.md` 16. szakasz.

➡️ **Az esemény a gyorsítás, a lekérdezés a garancia.** Hálózati
megosztáson az esemény notóriusan elmarad — ott ez az EGYETLEN út.

## Miért csak a látott mappa

Egyetlen könyvtár listázása olcsó, a teljes gyűjteményé nem. A tulajdonos
gyűjteménye NAS-on van, mért napló-korláttal; a teljes fa sűrű pásztázása
ott valódi kárt okozna. A teljes rescan ezért marad ötpercenként.
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


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library, monkeypatch):
    """Élő vezérlő, RÖVID lekérdezési időközzel.

    Az időköz a modul konstansából jön, ezért a teszt átírhatja — így a
    valódi időzítőt méri, nem a slot közvetlen hívását."""
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
    _var(qt_app, lambda: not ctl._sync_running, 20.0)
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


class TestAzIdozitoLetezik:
    def test_az_idozito_fut_es_a_slotra_van_kotve(self, controller):
        idozito = controller._folder_poll_timer
        assert idozito is not None, "nincs célzott újraolvasó időzítő"
        assert idozito.isActive(), "az időzítő nem fut"

    def test_leallitaskor_megall(self, controller):
        """Kilépéskor ne maradjon futó időzítő."""
        controller.shutdown()

        assert controller._folder_poll_timer is None


class TestAFigyeloNELKUL:
    """Ez a hálózati megosztás helyzete: esemény nincs, csak lekérdezés."""

    def test_az_uj_kep_megjelenik(self, controller, library, qt_app):
        mappa = library / "nyaralas"
        controller.selectFolder(str(mappa))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 2)
        controller._watcher.stop()
        controller._watcher = None
        assert _var(qt_app, lambda: not controller._sync_running)

        make_jpeg(mappa / "IMG_7777.jpg")

        assert _var(qt_app, lambda: controller.photos.rowCount() == 3), (
            "a célzott újraolvasás nem hozta be az új képet — hálózati "
            "megosztáson ez az EGYETLEN út"
        )

    def test_a_torolt_kep_is_eltunik(self, controller, library, qt_app):
        mappa = library / "nyaralas"
        controller.selectFolder(str(mappa))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 2)
        controller._watcher.stop()
        controller._watcher = None
        assert _var(qt_app, lambda: not controller._sync_running)

        (mappa / "IMG_0002.jpg").unlink()

        assert _var(qt_app, lambda: controller.photos.rowCount() == 1)


class TestNemPazarol:
    def test_mappa_nelkul_nem_indit_szinkront(self, controller, monkeypatch):
        """Ha nincs látott mappa, ne csináljunk semmit."""
        hivasok = []
        monkeypatch.setattr(
            controller, "_on_folders_dirty", lambda mappak: hivasok.append(mappak)
        )
        controller._current_folder = ""

        controller._poll_current_folder()

        assert hivasok == []

    def test_futo_szinkron_alatt_kihagyja(self, controller, library, monkeypatch):
        hivasok = []
        monkeypatch.setattr(
            controller, "_on_folders_dirty", lambda mappak: hivasok.append(mappak)
        )
        controller._current_folder = str(library / "nyaralas")
        controller._sync_running = True
        try:
            controller._poll_current_folder()
        finally:
            controller._sync_running = False

        assert hivasok == [], "futó szinkron mellé nem indítunk másodikat"

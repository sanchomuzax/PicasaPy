"""Élő frissülés a rácson — új, MEGVÁLTOZOTT és törölt fájl (#1435).

## Mit mér ez a fájl

A #1275 már bevezette a LÁTOTT mappa célzott újraolvasását, és őrzi is az
„új fájl" és a „törölt fájl" esetét. A tulajdonos bejelentése viszont a
HARMADIK esetről szól:

> „a Picasa 3-mal módosított kollázst a PicasaPy megnyitja, de a rácsban
> látszó indexkép a régi marad"

Ez a **helyben átírt** fájl esete: az útvonal ugyanaz, a sor ugyanaz, csak
a tartalom más. Két, egymástól független ponton bukhat el:

1. **az index** nem veszi észre a változást (mtime/méret nem frissül), és
2. **a rács** nem kér új képet, mert a bélyegkép-URL változatlan (a Qt
   URL szerint gyorstáraz — ld. `models._thumb_url`, #1186).

## A hálózati megosztás a mérce

A tulajdonos gyűjteménye NAS-on van, és ugyanazt a mappát a windowsos
Picasa 3 is írja. Ott **inotify-esemény nem érkezik** (a `LibraryWatcher`
docstringje is kimondja), tehát a figyelő ágra semmit nem szabad építeni:
minden teszt kikapcsolt figyelővel mér, ahogy a #1275 tette.
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
    """Két mappa: a rács feedje (#64) mindkettőt egyszerre mutatja."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "kollazsok").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    make_jpeg(root / "kollazsok" / "kollazs.jpg")
    # ⚠️ MÁSODIK kép a kollázs-mappában: az utolsó kép törlése ÜRESSÉ tenné
    # a mappát, amit a #459/5 szándékosan „nem elérhető"-nek minősít (a
    # lecsatolt NAS-mount pontosan így néz ki), és a sor bent maradna az
    # indexben. A törlés-eset így a valódi helyzetet méri, nem azt.
    make_jpeg(root / "kollazsok" / "masik.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library, monkeypatch):
    """Élő vezérlő, RÖVID lekérdezési időközzel — a valódi időzítőt mérjük."""
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
    # A figyelőt MINDIG leállítjuk: a NAS-on sincs esemény, és a teszt a
    # lekérdezési garanciát méri, nem az inotify-gyorsítást.
    if ctl._watcher is not None:
        ctl._watcher.stop()
        ctl._watcher = None
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _thumb_url_for(controller, nev: str) -> str:
    """A megadott nevű kép bélyegkép-URL-je a RÁCS modelljéből."""
    for sor in range(controller.photos.rowCount()):
        adat = controller.photos.itemAt(sor)
        if adat.get("name") == nev:
            return adat.get("thumbUrl", "")
    return ""


class TestMegvaltozottFajl:
    """A jegy magja: helyben átírt fájl a LÁTOTT mappában."""

    def test_a_megvaltozott_kep_belyegkepe_frissul(
        self, controller, library, qt_app
    ):
        mappa = library / "kollazsok"
        controller.selectFolder(str(mappa))
        assert _var(qt_app, lambda: _thumb_url_for(controller, "kollazs.jpg"))
        regi_url = _thumb_url_for(controller, "kollazs.jpg")

        # a windowsos Picasa 3 helyben írja át a kollázst: más tartalom,
        # ugyanaz az útvonal
        time.sleep(0.01)
        make_jpeg(mappa / "kollazs.jpg", size=(64, 48))

        assert _var(
            qt_app,
            lambda: _thumb_url_for(controller, "kollazs.jpg") != regi_url,
        ), (
            "a helyben átírt fájl bélyegkép-URL-je NEM változott — a Qt "
            "URL szerint gyorstáraz, tehát a rácson a RÉGI kép marad"
        )


class TestMasikMappaAFeedben:
    """A rács feedje (#64) egyszerre több mappát mutat — a célzott
    újraolvasás viszont CSAK a kiválasztott mappát nézi."""

    def test_a_nem_valasztott_mappa_uj_kepe_is_megjelenik(
        self, controller, library, qt_app
    ):
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 4)

        # a felhasználó a „nyaralas"-t nézi, de a feedben a „kollazsok" is
        # látszik — oda érkezik új kép
        make_jpeg(library / "kollazsok" / "uj_kollazs.jpg")

        assert _var(
            qt_app, lambda: controller.photos.rowCount() == 5
        ), (
            "a feedben LÁTSZÓ másik mappa új képe nem jelent meg — a "
            "célzott újraolvasás csak a kiválasztott mappát nézi"
        )

    def test_a_nem_valasztott_mappa_torolt_kepe_eltunik(
        self, controller, library, qt_app
    ):
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 4)

        (library / "kollazsok" / "masik.jpg").unlink()

        assert _var(
            qt_app, lambda: controller.photos.rowCount() == 3
        ), "a feedben látszó másik mappa törölt képe ottmaradt"

class TestANASTerheles:
    """A jegy kemény feltétele: a sweep NE terhelje a hálózati megosztást."""

    def test_a_sweep_koltsege_ket_muvelet_mappankent(
        self, controller, library, qt_app, monkeypatch
    ):
        """Körönként legfeljebb 2 × SWEEP_FOLDERS_PER_TICK művelet."""
        import os as os_modul

        from picasapy.app.library_controller import SWEEP_FOLDERS_PER_TICK

        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 4)

        hivasok = []
        eredeti = os_modul.stat

        def szamlalo(*args, **kwargs):
            hivasok.append(args[0] if args else None)
            return eredeti(*args, **kwargs)

        batch = controller._sweep_candidates(str(library / "nyaralas"))
        monkeypatch.setattr(
            "picasapy.app.folder_freshness.os.stat", szamlalo
        )
        controller._stale_feed_folders(batch)

        assert len(hivasok) <= 2 * SWEEP_FOLDERS_PER_TICK, (
            f"a sweep {len(hivasok)} műveletet generált — a NAS mért "
            f"200/mp korlátja mellett ez a költség körönként fizetendő"
        )

    def test_valtozatlan_mappara_NEM_fut_teljes_ujraolvasas(
        self, controller, library, qt_app
    ):
        """A drága lépés (`sync_folder`) csak eltérő pecsétnél indulhat."""
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 4)
        assert _var(qt_app, lambda: not controller._sync_running)

        # semmi nem változott a lemezen
        aktualis = str(library / "nyaralas")
        elavult = controller._stale_feed_folders(
            controller._sweep_candidates(aktualis)
        )

        assert elavult == (), (
            f"változatlan mappára is teljes újraolvasást kérnénk: {elavult}"
        )

    def test_a_keret_fuggetlen_a_konyvtar_meretetol(
        self, controller, library, qt_app
    ):
        """Sok mappánál sem nő a körönkénti költség."""
        from picasapy.app.library_controller import SWEEP_FOLDERS_PER_TICK

        controller._feed_groups = tuple(
            {"path": f"/nincs/ilyen/{i}"} for i in range(500)
        )

        adag = controller._sweep_candidates("/nincs/ilyen/0")

        assert len(adag) <= SWEEP_FOLDERS_PER_TICK

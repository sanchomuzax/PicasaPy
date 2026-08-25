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
    # HARMADIK mappa: enélkül a sweep adagja egyetlen elemű lenne, és a
    # költség-őr gyakorlatilag semmit nem mérne (a keret 8).
    (root / "regi").mkdir(parents=True)
    make_jpeg(root / "regi" / "IMG_9001.jpg")
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
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)

        # a felhasználó a „nyaralas"-t nézi, de a feedben a „kollazsok" is
        # látszik — oda érkezik új kép
        make_jpeg(library / "kollazsok" / "uj_kollazs.jpg")

        assert _var(
            qt_app, lambda: controller.photos.rowCount() == 6
        ), (
            "a feedben LÁTSZÓ másik mappa új képe nem jelent meg — a "
            "célzott újraolvasás csak a kiválasztott mappát nézi"
        )

    def test_a_nem_valasztott_mappa_torolt_kepe_eltunik(
        self, controller, library, qt_app
    ):
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)

        (library / "kollazsok" / "masik.jpg").unlink()

        assert _var(
            qt_app, lambda: controller.photos.rowCount() == 4
        ), "a feedben látszó másik mappa törölt képe ottmaradt"


class TestAtfedoKorok:
    """Tickenként EGY sweep és EGY szinkron-worker — két egyidejű
    index-író `OperationalError`-t és felhasználói hibajelzést adna."""

    def test_futo_sweep_alatt_nem_indul_masodik(
        self, controller, library, qt_app, monkeypatch
    ):
        """Akadó mounton a pecsét-kör túlfuthat a 10 másodpercen — MÁSODIK
        PECSÉT-KÖR akkor sem indulhat.

        ⚠️ #1440: ez a teszt korábban azt is állította, hogy futó sweep
        alatt a `_on_folders_dirty` SEM hívódik. Az az elvárás a #1440-cal
        MEGDŐLT, és szándékosan: az indoka („két egyidejű index-író")
        azóta nem áll, mert az írók átfedése ellen a `_on_folders_dirty`
        SAJÁT jelzője (`_dirty_running`) véd. A pecsét-kör csak OLVAS,
        tehát a kiválasztott mappa jelzése biztonságos — és nélküle a
        #1275 alapgaranciája minden lassú körben kiesne egy tickre.
        A megfordított irányt a `test_futo_sweep_alatt_is_frissul_a_valasztott`
        őrzi."""
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)
        inditasok = []
        monkeypatch.setattr(
            controller,
            "_start_background",
            lambda *a, **k: inditasok.append(k.get("name")),
        )
        monkeypatch.setattr(controller, "_on_folders_dirty", lambda m: None)
        controller._sweep_running = True
        try:
            controller._poll_current_folder()
        finally:
            controller._sweep_running = False

        assert inditasok == [], "az előző kör mellé másodikat indítottunk"

    def test_futo_sweep_alatt_is_frissul_a_valasztott(
        self, controller, library, qt_app, monkeypatch
    ):
        """#1440: bent ragadt pecsét-kör mellett is ki kell mennie a
        LÁTOTT mappa jelzésének — ez a #1275 alapgaranciája, és a #1435
        kényelmi gyorsítása nem eheti meg."""
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)
        piszkos = []
        monkeypatch.setattr(
            controller, "_on_folders_dirty", lambda m: piszkos.append(m)
        )
        controller._sweep_running = True
        try:
            controller._poll_current_folder()
        finally:
            controller._sweep_running = False

        assert piszkos == [[str(library / "nyaralas")]], (
            "a lassú pecsét-kör miatt a kiválasztott mappa kimaradt a körből"
        )

    def test_a_kapu_a_kor_vegen_felnyilik(self, controller, library, qt_app):
        """A jelző nem ragadhat be — különben a frissülés örökre leáll."""
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)

        controller._poll_current_folder()

        assert _var(
            qt_app, lambda: not getattr(controller, "_sweep_running", False)
        ), "a sweep-kapu beragadt"

    def test_bukott_szalinditas_utan_a_kapu_NYITVA_marad(
        self, controller, library, qt_app, monkeypatch
    ):
        """⚠️ A `_start_background` ÚJRADOBJA a `thread.start()` hibáját
        (`RuntimeError: can't start new thread`, ld. #550) — ilyenkor a
        worker `finally` ága SOSEM fut le.

        A kapu a `_poll_current_folder` ELEJÉN áll, tehát ha beragadna,
        onnantól nemcsak a sweep, hanem a `_on_folders_dirty` alapág is
        néma maradna: a rács a munkamenet végéig soha többé nem frissülne
        magától. Egyetlen tranziens szálindítási hiba örökre elrontaná."""
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)
        controller._folder_poll_timer.stop()

        def nem_indul(*args, **kwargs):
            raise RuntimeError("can't start new thread")

        monkeypatch.setattr(controller, "_start_background", nem_indul)
        with pytest.raises(RuntimeError):
            controller._poll_current_folder()

        assert not getattr(controller, "_sweep_running", False), (
            "a kapu beragadt True-n: innentől MINDEN következő kör azonnal "
            "visszatér, a rács némán sosem frissül többé"
        )

    def test_bukott_pecset_utan_is_frissul_a_valasztott_mappa(
        self, controller, library, qt_app, monkeypatch
    ):
        """A #1435 kényelmi gyorsítása NEM béníthatja meg a #1275
        alapgaranciáját: ha a pecsét-ellenőrzés hibára fut, a kiválasztott
        mappa jelzésének akkor is ki kell mennie."""
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)
        # az élő időzítő minden tickre újra hívna (és a `robban` minden
        # körben dobna) — a jelzés-számlálás így összecsúszhatna
        controller._folder_poll_timer.stop()
        jelzesek = []
        controller.watcherDirty.connect(lambda m: jelzesek.append(m))

        def robban(_batch):
            raise RuntimeError("szimulált index-hiba")

        monkeypatch.setattr(controller, "_stale_feed_folders", robban)
        controller._poll_current_folder()

        assert _var(qt_app, lambda: len(jelzesek) >= 1), (
            "a pecsét bukása elnyelte a kiválasztott mappa jelzését is"
        )
        assert jelzesek[0] == [str(library / "nyaralas")]


class TestANASTerheles:
    """A jegy kemény feltétele: a sweep NE terhelje a hálózati megosztást."""

    def test_a_sweep_koltsege_ket_muvelet_mappankent(
        self, controller, library, qt_app, monkeypatch
    ):
        """Mappánként legfeljebb HÁROM művelet, semmivel sem több.

        ⚠️ Az állítás PONTOS, nem nagyvonalú felső korlát: egy 8-szoros
        tartalékkal mérő őr akkor is zöld maradna, ha a pecsét mappánként
        16 műveletbe kerülne — azaz semmit nem bizonyítana."""
        import os as os_modul

        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)

        hivasok = []
        eredeti = os_modul.stat

        def szamlalo(*args, **kwargs):
            hivasok.append(args[0] if args else None)
            return eredeti(*args, **kwargs)

        batch = controller._sweep_candidates(str(library / "nyaralas"))
        assert len(batch) >= 2, (
            f"üres/egyelemű adaggal a mérés semmit nem bizonyít: {batch}"
        )
        monkeypatch.setattr(
            "picasapy.app.folder_freshness.os.stat", szamlalo
        )
        controller._stale_feed_folders(batch)

        assert len(hivasok) <= 3 * len(batch), (
            f"a sweep {len(hivasok)} műveletet generált {len(batch)} "
            f"mappára — a felső korlát 3/mappa"
        )

    def test_valtozatlan_mappara_NEM_fut_teljes_ujraolvasas(
        self, controller, library, qt_app
    ):
        """A drága lépés (`sync_folder`) csak eltérő pecsétnél indulhat."""
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 5)
        assert _var(qt_app, lambda: not controller._sync_running)

        # semmi nem változott a lemezen
        aktualis = str(library / "nyaralas")
        batch = controller._sweep_candidates(aktualis)
        assert batch, "üres adagon a „nem elavult” állítás üresen is igaz"
        elavult = controller._stale_feed_folders(batch)

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

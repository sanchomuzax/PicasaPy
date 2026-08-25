"""A célzott mappa-szinkron saját futásjelzője (#1440).

## Mit mér ez a fájl

A `_on_folders_dirty` (`app/library_controller.py`) indítja a watcher- és
a lekérdezés-ág célzott, mappa-pontos szinkronját — ez az egyetlen ág,
ami az indexbe ÍR a periodikus rescanen kívül. A #1440 előtt **nem
állított semmilyen futásjelzőt**: a `_sync_running` a `rescan()`-é, a
#1435 `_sweep_running`-ja pedig a *pecsét-körök* átfedését zárja ki, a
belőlük születő szinkron-workerekét nem.

A mért forgatókönyv (a #1435 kódellenőrzéséből):

- t = 9,9 s — az N. kör sweepje végez, jelez → indul egy dirty-worker,
  ami 9 mappát szinkronizál hálózati megosztáson (30+ s).
- t = 10,0 s — a `_sweep_running` már hamis, a `_sync_running` is → új
  kör → új jelzés → **második dirty-worker az elsővel párhuzamosan** →
  két egyidejű index-író → `sqlite3.OperationalError` → a felhasználó
  `syncFailed` hibajelzést lát.

A #1435 érdemben megnövelte a kitettséget: a dirty-worker addig egy
mappát vitt, azóta akár nyolcat-kilencet, tehát sokkal tovább él.

## Amit a fájl őriz

1. két gyors egymás utáni jelzésből EGYETLEN író indul,
2. a futás alatt érkezett mappák nem vesznek el (`_pending_dirty`),
3. a jelző NEM ragad be bukott szálindításnál (#550 mintája) — ez a
   csendes halál: onnantól a rács a munkamenet végéig sosem frissülne,
4. a kör végén a lemaradás magától behozódik.
"""

from __future__ import annotations

import threading
import time

import pytest

from support.jpeg_factory import make_jpeg


def _var(qt_app, feltetel, masodperc: float = 20.0) -> bool:
    """Aktív várakozás eseményfeldolgozással (a jelzések queued módon
    érkeznek a háttérszálról)."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.02)
    return bool(feltetel())


@pytest.fixture
def library(tmp_path):
    """Három mappa: a célzott szinkron több mappát is kaphat egy jelzésben."""
    root = tmp_path / "kepek"
    for nev in ("nyaralas", "kollazsok", "regi"):
        (root / nev).mkdir(parents=True)
        make_jpeg(root / nev / "IMG_0001.jpg")
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
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


class TestAtfedoIrok:
    """Két gyors jelzésből EGY író — a jegy magja."""

    def test_ket_gyors_jelzes_egyetlen_irot_indit(
        self, controller, library, monkeypatch
    ):
        """A második jelzés a FUTÓ első worker mellé nem indíthat másikat.

        A `_start_background` itt csak jegyzetel, futni nem enged: így a
        „még fut az első" állapot determinista, valódi időzítés nélkül."""
        inditasok: list[str | None] = []
        monkeypatch.setattr(
            controller,
            "_start_background",
            lambda *a, **k: inditasok.append(k.get("name")),
        )

        controller._on_folders_dirty([str(library / "nyaralas")])
        controller._on_folders_dirty([str(library / "kollazsok")])

        assert inditasok == ["picasapy-sync-dirty"], (
            "két egyidejű index-író indult: ebből a felhasználónál "
            "sqlite3.OperationalError és syncFailed lesz"
        )

    def test_a_masodik_jelzes_mappaja_nem_vesz_el(
        self, controller, library, monkeypatch
    ):
        """A visszatartott mappáknak MIND be kell kerülniük a következő
        körbe — a `_pending_dirty` a #1181 óta pont ezt szolgálja."""
        monkeypatch.setattr(controller, "_start_background", lambda *a, **k: None)

        controller._on_folders_dirty([str(library / "nyaralas")])
        controller._on_folders_dirty([str(library / "kollazsok")])
        controller._on_folders_dirty([str(library / "regi")])

        assert controller._pending_dirty == {
            str(library / "kollazsok"),
            str(library / "regi"),
        }

    def test_valodi_szalon_sincs_atfedes(self, controller, library, monkeypatch):
        """Ugyanez VALÓDI háttérszállal: a lassú `sync_folder` alatt
        érkező jelzés nem nyithat második index-írót.

        Az első worker addig áll a `sync_folder`-ben, amíg a teszt el nem
        engedi — pontosan a jegyben leírt 30 másodperces NAS-szinkron
        szerepét játssza."""
        import picasapy.app.library_controller as lc

        egyidejuleg = 0
        csucs = 0
        zar = threading.Lock()
        engedely = threading.Event()

        def lassu_sync(conn, root, folder, exclude=(), should_stop=None):
            nonlocal egyidejuleg, csucs
            with zar:
                egyidejuleg += 1
                csucs = max(csucs, egyidejuleg)
            engedely.wait(10.0)
            with zar:
                egyidejuleg -= 1

        monkeypatch.setattr(lc, "sync_folder", lassu_sync)

        controller._on_folders_dirty([str(library / "nyaralas")])
        # megvárjuk, hogy az első worker tényleg BENT legyen a syncben
        hatarido = time.monotonic() + 10.0
        while time.monotonic() < hatarido and csucs == 0:
            time.sleep(0.01)
        controller._on_folders_dirty([str(library / "kollazsok")])
        time.sleep(0.2)  # ha indulna második szál, itt már bent lenne
        engedely.set()

        assert controller.waitForBackgroundWorkers(30.0)
        assert csucs == 1, f"{csucs} index-író futott egyszerre"


class TestJelzoNemRagadBe:
    """A beragadt jelző NÉMA halál: onnantól sosem indul több frissítés."""

    def test_bukott_szalinditas_utan_a_jelzo_nyitva_marad(
        self, controller, library, monkeypatch
    ):
        """⚠️ A `_start_background` ÚJRADOBJA a `thread.start()` hibáját
        (`RuntimeError: can't start new thread`, #550) — ilyenkor a worker
        `finally` ága SOSEM fut le. Ha a jelző igazon maradna, a célzott
        szinkron minden további kérése a várólistára kerülne, és onnan
        soha senki nem hozná be: a rács a munkamenet végéig némán állna."""

        def nem_indul(*args, **kwargs):
            raise RuntimeError("can't start new thread")

        monkeypatch.setattr(controller, "_start_background", nem_indul)
        with pytest.raises(RuntimeError):
            controller._on_folders_dirty([str(library / "nyaralas")])

        assert controller._dirty_running is False, (
            "a jelző beragadt True-n: innentől MINDEN célzott frissítés "
            "némán a várólistán ragad"
        )

    def test_a_kor_vegen_a_jelzo_felnyilik(self, controller, library, qt_app):
        controller._on_folders_dirty([str(library / "nyaralas")])

        assert _var(
            qt_app, lambda: controller._dirty_running is False
        ), "a jelző beragadt a kör végén"


class TestLemaradasBehozasa:
    """A visszatartott mappák a kör végén MAGUKTÓL sorra kerülnek."""

    def test_a_visszatartott_mappa_a_kor_vegen_szinkronizalodik(
        self, controller, library, qt_app, monkeypatch
    ):
        """A `syncFinished` → `_flush_pending_dirty` úton kell behozódnia:
        a jelzőt ezért ELŐBB engedjük el, mint a jelzést küldjük."""
        import picasapy.app.library_controller as lc

        szinkronizalt: list[str] = []
        elso_bent = threading.Event()
        engedely = threading.Event()
        eredeti = lc.sync_folder

        def figyelt_sync(conn, root, folder, exclude=(), should_stop=None):
            szinkronizalt.append(folder)
            if not elso_bent.is_set():
                elso_bent.set()
                engedely.wait(10.0)
            return eredeti(conn, root, folder, exclude=exclude, should_stop=should_stop)

        monkeypatch.setattr(lc, "sync_folder", figyelt_sync)

        controller._on_folders_dirty([str(library / "nyaralas")])
        try:
            assert elso_bent.wait(10.0)
            controller._on_folders_dirty([str(library / "kollazsok")])
            assert controller._pending_dirty == {str(library / "kollazsok")}, (
                "a második mappa nem a várólistára ment, hanem saját írót kapott"
            )
        finally:
            # bukó állítás mellett is engedjük el a workert, különben a
            # teardown `waitForBackgroundWorkers` fölöslegesen kivárna
            engedely.set()

        assert _var(
            qt_app, lambda: str(library / "kollazsok") in szinkronizalt
        ), "a visszatartott mappa sosem került sorra"
        assert controller.waitForBackgroundWorkers(30.0)

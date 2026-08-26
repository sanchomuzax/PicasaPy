"""#1500: a `color:`/`szín:` keresés ÉLŐVÉ tétele — a gyorsítótárat
tényleg feltölti valaki, és a felhasználó megtudja, ha még nem teljes.

## Mit adott a kód a jegy előtt (mérés)

A `photo_colors` táblát feltöltő `backfill_colors()`-t a `src/` alatt
SENKI nem hívta — csak a `tests/index/test_search_color.py`. A
`search_photos()` (`index/queries.py:173`) helyesen kérdezte a táblát, de
az mindig üres maradt, ezért a keresősávba írt `szín:kék` MINDIG nulla
találatot adott, néma, üres találati listával. A felhasználó nem tudta
megkülönböztetni a „nincs ilyen színű képem" és a „ezt még sosem
számoltuk ki" esetet.

## Amit ez a fájl őriz

1. **A VALÓDI út**: friss index → keresés → feltöltés → újra keresés,
   és a második keresés TALÁLATOT ad. Ez a jegy sikerkritériuma.
2. **Nem néma**: a hiányos gyorsítótárral futó színkeresés jelzést küld a
   felületnek (`colorIndexIncomplete`), a kész számokkal együtt.
3. **Csak színkeresésnél**: a sima szöveges keresés nem indít 81 ms/képes
   háttérmunkát.
4. **A futásjelző nem ragad be** bukott szálindításnál (#550/#1435/#1440
   mintája) — beragadt jelzővel a feltöltés a munkamenet végéig NÉMÁN
   soha többé nem indulna el.
5. **Megszakítható**: a `cancelColorIndex()` mappa/kép-határon megállítja.
"""

from __future__ import annotations

import time

import cv2
import numpy as np
import pytest


def _tomor_jpeg(path, bgr: tuple[int, int, int]) -> None:
    kep = np.zeros((32, 32, 3), dtype=np.uint8)
    kep[:, :] = bgr
    assert cv2.imwrite(str(path), kep)


@pytest.fixture
def konyvtar(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    _tomor_jpeg(root / "piros.jpg", (0, 0, 255))
    _tomor_jpeg(root / "kek.jpg", (255, 0, 0))
    _tomor_jpeg(root / "szurke.jpg", (128, 128, 128))
    return root


@pytest.fixture
def controller(qt_app, tmp_path, konyvtar):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, konyvtar)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(konyvtar),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    yield ctl
    ctl.cancelColorIndex()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _talalat_nevek(ctl) -> set[str]:
    """A rácsmodellben ÉPP LÁTHATÓ fájlnevek — nem belső lekérdezés,
    hanem az, amit a felhasználó lát."""
    return {record.name for record in ctl.photos.photos}


class TestValodiUt:
    """A jegy sikerkritériuma: a keresés TALÁLATOT ad, magától."""

    def test_friss_index_utan_a_szinkereses_talalatot_ad(self, controller, qt_app):
        # 1. kör: a gyorsítótár üres — a régi kódban ez volt a végállapot
        controller.search("color:red")
        assert _talalat_nevek(controller) == set(), (
            "friss indexen még nincs kiszámolt szín"
        )
        # a keresés MAGA indította el a feltöltést (nincs külön gomb)
        assert controller.colorIndexRunning(), (
            "a színkeresés nem indította el a gyorsítótár feltöltését — "
            "a funkció néma marad"
        )
        assert controller.waitForBackgroundWorkers(60.0)

        # 2. kör: ugyanaz a keresés, most már adattal
        controller.search("color:red")
        assert _talalat_nevek(controller) == {"piros.jpg"}

    def test_a_feltoltes_a_teljes_konyvtarat_lefedi(self, controller):
        controller.startColorIndex()
        assert controller.waitForBackgroundWorkers(60.0)
        from picasapy.index import color_index_progress, open_index

        with open_index(controller._db_path) as conn:
            kesz, osszes = color_index_progress(conn)
        assert kesz == osszes == 3
        controller.search("szín:szürke")
        assert _talalat_nevek(controller) == {"szurke.jpg"}


class TestMagatolFrissul:
    """A tájékoztatás kevés: ha a feltöltés kész, a találatok jöjjenek is meg."""

    def test_a_feltoltes_vegen_a_szinkereses_magatol_frissul(
        self, controller, qt_app
    ):
        """A felhasználó egyszer keres rá — és a képek megjelennek.

        A záró jelzés a munkásszálról QUEUED módon ér a GUI-szálra, ezért
        a teszt eseménysort pörget; ezt teszi az alkalmazás is."""
        controller.search("color:red")
        assert controller.waitForBackgroundWorkers(60.0)
        hatarido = time.monotonic() + 10.0
        while time.monotonic() < hatarido and _talalat_nevek(controller) != {
            "piros.jpg"
        }:
            qt_app.processEvents()
            time.sleep(0.02)
        assert _talalat_nevek(controller) == {"piros.jpg"}, (
            "a feltöltés lefutott, de a felhasználónak újra be kellene "
            "gépelnie ugyanazt a keresést"
        )

    def test_mas_nezetbe_lepve_nem_ir_bele_a_racsba(self, controller, qt_app):
        """Ha a felhasználó közben továbblépett, a kész feltöltés NEM
        rántja vissza a régi keresés találatait."""
        controller.search("color:red")
        controller.search("kek")  # szöveges keresés fájlnévre, más nézet
        assert _talalat_nevek(controller) == {"kek.jpg"}, "a szöveges keresés nem talált"
        assert controller.waitForBackgroundWorkers(60.0)
        for _ in range(50):
            qt_app.processEvents()
            time.sleep(0.01)
        assert _talalat_nevek(controller) == {"kek.jpg"}, (
            "a kész feltöltés visszarántotta a felhasználó által elhagyott "
            "keresés találatait"
        )
        assert controller._view_mode == ("search", "kek")


class TestNemNema:
    """A „0 találat" és a „még nem indexeltük" NEM ugyanaz."""

    def test_hianyos_gyorsitotarnal_jelzes_megy_a_feluletnek(self, controller):
        latott: list[tuple[int, int]] = []
        controller.colorIndexIncomplete.connect(
            lambda kesz, osszes: latott.append((kesz, osszes))
        )
        controller.search("color:red")
        assert latott, (
            "a felhasználó néma, üres találati listát kapott — nem tudja "
            "megkülönböztetni a nincs-ilyen-kép esetet a még-nem-"
            "számoltuk-ki esettől"
        )
        assert latott[0] == (0, 3)
        # a felület EBBŐL rajzolja a sáv szövegét (`Main.qml`)
        szoveg = controller.colorIndexNoticeText(*latott[0])
        assert szoveg.strip(), "üres tájékoztató szöveg"
        assert "0" in szoveg and "3" in szoveg, (
            "a mondat nem mondja meg, hol tart a feldolgozás"
        )

    def test_kesz_gyorsitotarnal_nincs_figyelmeztetes(self, controller):
        controller.startColorIndex()
        assert controller.waitForBackgroundWorkers(60.0)
        latott: list = []
        controller.colorIndexIncomplete.connect(lambda *a: latott.append(a))
        controller.search("color:red")
        assert latott == [], "kész gyorsítótárnál nincs mit jelenteni"

    def test_szoveges_kereses_nem_indit_feltoltest(self, controller):
        controller.search("piros")
        assert not controller.colorIndexRunning(), (
            "szín nélküli keresés nem indíthat 81 ms/képes háttérmunkát"
        )


class TestJelzoNemRagadBe:
    """⚠️ Beragadt jelzővel a feltöltés NÉMÁN soha többé nem indulna el."""

    def test_bukott_szalinditas_utan_a_jelzo_hamis_marad(
        self, controller, monkeypatch
    ):
        import picasapy.app.worker_thread as wt

        def nem_indul(*args, **kwargs):
            raise RuntimeError("can't start new thread")

        monkeypatch.setattr(wt, "_Thread", nem_indul)
        with pytest.raises(RuntimeError):
            controller.startColorIndex()
        assert not controller.colorIndexRunning(), (
            "a futásjelző igazon ragadt — innentől a színkeresés soha "
            "többé nem töltené fel a gyorsítótárat"
        )

        monkeypatch.undo()
        controller.startColorIndex()
        assert controller.waitForBackgroundWorkers(60.0)
        controller.search("color:blue")
        assert _talalat_nevek(controller) == {"kek.jpg"}

    def test_a_keresest_nem_oli_meg_a_bukott_szalinditas(
        self, controller, monkeypatch
    ):
        """A szálindítás bukása a KERESÉST nem teheti tönkre — a szöveges
        találatoknak akkor is meg kell jönniük."""
        import picasapy.app.worker_thread as wt

        monkeypatch.setattr(
            wt, "_Thread", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("nincs szál"))
        )
        controller.search("color:red")  # nem dobhat
        assert not controller.colorIndexRunning()


class TestMegszakithato:
    def test_a_megszakitas_leallitja_a_feltoltest(self, controller):
        controller.startColorIndex()
        controller.cancelColorIndex()
        assert controller.waitForBackgroundWorkers(60.0)
        assert not controller.colorIndexRunning()

    def test_ket_inditas_egy_szalat_ad(self, controller, monkeypatch):
        inditasok: list = []
        monkeypatch.setattr(
            controller,
            "_start_background",
            lambda *a, **k: inditasok.append(k.get("name")),
        )
        controller.startColorIndex()
        controller.startColorIndex()
        assert inditasok == ["picasapy-szinindex"]
        controller._color_index_running = False


class TestHaladas:
    def test_a_haladas_futas_kozben_ertelmezheto(self, controller, qt_app):
        """⚠️ A haladásjelzés a munkásszálról QUEUED módon érkezik a
        GUI-szálra: eseménysor pörgetése nélkül SOHA nem kézbesülne, és a
        teszt hamis zöldet adna arra, hogy „nincs jelzés"."""
        latott: list[tuple[int, int]] = []
        controller.colorIndexProgress.connect(
            lambda kesz, osszes: latott.append((kesz, osszes))
        )
        controller.startColorIndex()
        assert controller.waitForBackgroundWorkers(60.0)
        hatarido = time.monotonic() + 5.0
        while time.monotonic() < hatarido and latott[-1:] != [(3, 3)]:
            qt_app.processEvents()
            time.sleep(0.02)
        assert latott, "haladásjelzés nélkül futott a háttérmunka"
        assert latott[-1] == (3, 3)

    def test_a_zaro_jelzes_megerkezik(self, controller, qt_app):
        """A `colorIndexFinished` a `Main.qml`-ben oltja el a sáv élő
        frissítését — enélkül egy későbbi futás felélesztené a régi
        üzenetet."""
        vegek: list[tuple[int, int]] = []
        controller.colorIndexFinished.connect(
            lambda kesz, osszes: vegek.append((kesz, osszes))
        )
        controller.startColorIndex()
        assert controller.waitForBackgroundWorkers(60.0)
        hatarido = time.monotonic() + 5.0
        while time.monotonic() < hatarido and not vegek:
            qt_app.processEvents()
            time.sleep(0.02)
        assert vegek == [(3, 3)]

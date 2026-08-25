"""#1457: a bélyegkép-válasz élettartama — a mappaváltás közbeni SIGSEGV.

Mit mértünk (a javítás előtt): a `_ThumbResponse` C++ oldalát a QML-motor
kezeli (a saját olvasószálán hozza létre és ott is pusztítja el), a PySide
viszont a Python-oldali referenciaszámot is figyeli — a válasz
`ownedByPython` marad azután is, hogy visszaadtuk a motornak. Az egyetlen
Python-hivatkozást a pool-feladat (`_ThumbJob`) tartotta, amit a
`QThreadPool` a `run()` után AZONNAL eldob (`autoDelete()` alapból igaz).
Ha ez megelőzte a motor feldolgozását, akkor a Python semmisítette meg a
választ a motor alól, miközben az még nyers mutatót tartott rá — ez a
use-after-free omlasztotta össze a programot mappaváltáskor, amikor sok
bélyegkép készült egyszerre.

Az itteni négy őr ezt a szerződést méri:
  1. a válasz TÚLÉLI a pool-feladatot (a provider tartja életben);
  2. amikor a motor elengedi, a nyilvántartás is ürül (nincs szivárgás);
  3. egy már megszűnt válasz lezárása nem omlik össze;
  4. a lemondott (`cancel`) válaszba nem írunk képet.
"""

import gc
import weakref

import shiboken6
from PySide6.QtGui import QImage

from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def _provider(tmp_path):
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    return ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=64))


def _response(tmp_path):
    """Egy lefutott kérés válasza — ismeretlen id is jó, a lényeg az
    életciklus, nem a képtartalom."""
    provider = _provider(tmp_path)
    response = provider.requestImageResponse("99999", None)
    assert response._done.wait(10)
    provider.wait_for_done()
    return provider, response


class TestValaszElettartam:
    def test_valasz_tulel_a_pool_feladaton(self, qt_app, tmp_path):
        """A DoD magja: miután MINDEN Python-hivatkozás kiesett, a válasz
        C++ oldalának ÉLNIE kell — a motor még nyers mutatót tart rá.
        A javítás visszavételekor (a provider nyilvántartása nélkül) itt a
        `_ThumbJob` eldobásával a válasz megszűnne, és a figyelő elszállna."""
        provider, response = _response(tmp_path)
        figyelo = weakref.ref(response)
        del response
        gc.collect()
        assert figyelo() is not None, (
            "a válasz megszűnt, miközben a motor még használhatja (#1457)"
        )
        assert provider.live_response_count() == 1

    def test_a_motor_elengedese_uriti_a_nyilvantartast(self, qt_app, tmp_path):
        """A nyilvántartás nem szivároghat: amint a motor elpusztítja a
        választ (`destroyed`), a provider elengedi a hivatkozását."""
        provider, response = _response(tmp_path)
        assert provider.live_response_count() == 1
        shiboken6.delete(response)  # ezt teszi a motor, amikor végzett
        assert provider.live_response_count() == 0

    def test_megszunt_valasz_lezarasa_nem_omlik_ossze(self, qt_app, tmp_path):
        """A jelentett veremben szereplő eset: a pool-szál egy már megszűnt
        válaszon hívna `finished.emit()`-et. Ez SIGSEGV volt; most néma
        visszatérés, a várakozók elengedésével."""
        from picasapy.app.thumbnail_provider import _ThumbResponse

        response = _ThumbResponse()
        shiboken6.delete(response)
        response._finish(QImage(4, 4, QImage.Format.Format_RGB32))
        assert response._done.is_set()

    def test_lemondott_valaszba_nem_irunk_kepet(self, qt_app, tmp_path):
        """Lemondás után a kép beírása fölösleges munka — de a `finished`
        jelzésnek ki KELL mennie, különben a motor sosem takarítaná el a
        választ. A jelzés #1457 óta queued, ezért kell a `processEvents`."""
        from picasapy.app.thumbnail_provider import _ThumbResponse

        response = _ThumbResponse()
        jelzesek = []
        response.finished.connect(lambda: jelzesek.append(1))
        response.cancel()
        response._finish(QImage(8, 8, QImage.Format.Format_RGB32))
        assert response._image.isNull(), "lemondott válaszba nem írunk képet"
        qt_app.processEvents()
        assert jelzesek == [1], "a motornak jeleznünk kell, hogy eltakaríthassa"

    def test_a_jelzes_a_valasz_sajat_szalan_megy_ki(self, qt_app, tmp_path):
        """#1457 magja: nem elég, hogy a jelzés KÉZBESÍTÉSE a főszálra
        sorolódik (azt a Qt auto-kapcsolata amúgy is megteszi) — maga a
        KIBOCSÁTÁS sem futhat a dolgozó szálon, mert az a válasz-objektumot
        érinti, amit közben a motor a saját szálán elpusztíthat.

        Ezért azt mérjük, MELYIK SZÁLON fut le a kibocsátó lépés."""
        import threading

        from picasapy.app.thumbnail_provider import _ThumbResponse

        rogzitett: list[int] = []

        class Figyelt(_ThumbResponse):
            def _emit_finished(self) -> None:
                rogzitett.append(threading.get_ident())
                super()._emit_finished()

        response = Figyelt()
        fo_szal = threading.get_ident()

        dolgozo: list[int] = []

        def munka():
            dolgozo.append(threading.get_ident())
            response._finish(QImage(8, 8, QImage.Format.Format_RGB32))

        t = threading.Thread(target=munka)
        t.start()
        t.join()
        assert response._done.is_set()
        assert rogzitett == [], (
            "a kibocsátás nem futhat le a dolgozó szálon (#1457)"
        )
        qt_app.processEvents()
        assert rogzitett == [fo_szal], (
            "a kibocsátásnak a válasz saját szálán kell lefutnia; "
            f"dolgozó szál: {dolgozo}, mért: {rogzitett}"
        )


class TestPoolFeladatViszony:
    def test_a_pool_feladat_autodelete_marad(self, qt_app, tmp_path):
        """A `_ThumbJob` továbbra is önpusztító (ez a QThreadPool helyes
        használata) — a válasz élettartama NEM ezen múlik többé (#1457)."""
        from picasapy.app.thumbnail_provider import _ThumbJob, _ThumbResponse

        provider = _provider(tmp_path)
        job = _ThumbJob(provider, "1", _ThumbResponse())
        assert job.autoDelete() is True


class TestRendesUtValtozatlan:
    def test_kep_tovabbra_is_megerkezik(self, qt_app, tmp_path):
        """A javítás nem tompíthatja a rendes utat: valódi képre a válasz
        továbbra is kész képet szállít."""
        from picasapy.index import open_index, photos_in_folder, sync_tree

        lib = tmp_path / "kepek"
        lib.mkdir()
        make_jpeg(lib / "kep0.jpg", size=(320, 160))
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, lib)
            records = photos_in_folder(conn, lib)
        provider = _provider(tmp_path)
        provider.register_photos(records)
        response = provider.requestImageResponse(str(records[0].id), None)
        assert response._done.wait(10)
        assert not response._image.isNull()


class TestAKepMezoVersenyMentes:
    """A `_image` mezőhöz HÁROM szál nyúl — mindhárom a zár alatt.

    A `_finish` a pool-szálon ÍR, a `textureFactory` a motor szálán
    OLVAS, a `cancel` pedig a motor szálán állít jelzőt. A `QImage`
    implicit megosztású: a másolat a hivatkozásszámlálót lépteti. Ha az
    írás és az olvasás átfedi egymást, a számláló sérül — és a hiba nem
    ott csattan, ahol keletkezett, hanem egy későbbi felszabadításnál,
    látszólag véletlenszerű helyen.

    Ez volt a #1457 utolsó nyitott ablaka: a jelzés kibocsátását már egy
    szálra soroltuk, a KÉP MEZŐT viszont még nem védte semmi."""

    def test_a_textureFactory_a_zar_alatt_olvas(self, qt_app):
        """Az olvasás nem kezdődhet el, amíg az írás tart.

        Az őr foga: ha a `textureFactory`-ból kivesszük a zárat, az
        olvasás átcsúszik a félbehagyott írás alatt, és a teszt bukik."""
        from picasapy.app.thumbnail_provider import _ThumbResponse

        valasz = _ThumbResponse()
        sorrend: list[str] = []
        eredeti_lock = valasz._lock

        class _NaplozoZar:
            """A valódi zár, ami feljegyzi, ki mikor lép be és ki."""

            def __enter__(self):
                sorrend.append("be")
                return eredeti_lock.__enter__()

            def __exit__(self, *args):
                sorrend.append("ki")
                return eredeti_lock.__exit__(*args)

        valasz._lock = _NaplozoZar()
        valasz.textureFactory()

        assert sorrend == ["be", "ki"], (
            "a `textureFactory` nem a zár alatt olvassa a `_image` mezőt — "
            "a pool-szál írásával átfedve a QImage hivatkozásszámlálója "
            "sérül, és a program egy későbbi felszabadításnál omlik össze"
        )


class TestAKetSZOLGALTATOUgyanazokatAVedelmeketKapja:
    """A két aszinkron bélyegkép-szolgáltató UGYANAZT a mintát futtatja.

    A #1457 első köre CSAK a `thumbnail_provider`-t javította, és az
    összeomlások **folytatódtak** — mert az `effect_thumbnails` betűre
    ugyanazt a hibás mintát vitte tovább (pool-szálról kibocsátott jelzés,
    zár nélküli képmező, a válaszra semmilyen hivatkozás). A javítás
    fájlonkénti foltozása pontosan az a hiba, amit a #999 kizár:

    > „nem fájlonkénti foltozás, hanem ott, ahol a szálat indítjuk"

    Ez az őr azt tartja karban, hogy a kettő **együtt** mozogjon: ha
    valaki az egyiket javítja vagy megváltoztatja, a másik ne maradjon le
    csendben.
    """

    @staticmethod
    def _valasz_osztalyok():
        from picasapy.app.effect_thumbnails import _EffectThumbResponse
        from picasapy.app.thumbnail_provider import _ThumbResponse

        return {"thumbnail_provider": _ThumbResponse,
                "effect_thumbnails": _EffectThumbResponse}

    def test_mindketto_ismeri_a_lemondast(self):
        for nev, osztaly in self._valasz_osztalyok().items():
            assert hasattr(osztaly, "cancel"), (
                f"a(z) {nev} válasza nem kezeli a motor lemondását — a "
                "lemondott válaszba írás és a jelzés elmaradása is kárt okoz"
            )

    def test_mindketto_a_sajat_szalan_bocsatja_ki_a_jelzest(self):
        """A pool-szálról kibocsátott jelzés a törléssel versenyzik."""
        import inspect

        for nev, osztaly in self._valasz_osztalyok().items():
            forras = inspect.getsource(osztaly)
            assert "invokeMethod" in forras and "QueuedConnection" in forras, (
                f"a(z) {nev} válasza a POOL-szálról bocsátja ki a jelzést; a "
                "motor ugyanakkor a saját szálán hívja a deleteLater-t, és a "
                "kettő ugyanazon az objektumon fut"
            )

    def test_mindketto_a_zar_alatt_olvassa_a_kepet(self):
        import inspect

        for nev, osztaly in self._valasz_osztalyok().items():
            forras = inspect.getsource(osztaly.textureFactory)
            assert "self._lock" in forras, (
                f"a(z) {nev} `textureFactory`-ja zár nélkül olvassa a "
                "képmezőt, amit a pool-szál közben írhat"
            )

    def test_mindket_szolgaltato_nyilvantartja_az_elo_valaszokat(self):
        from picasapy.app.effect_thumbnails import EffectThumbnailProvider
        from picasapy.app.thumbnail_provider import ThumbnailProvider

        for szolgaltato in (ThumbnailProvider, EffectThumbnailProvider):
            assert hasattr(szolgaltato, "live_response_count"), (
                f"a(z) {szolgaltato.__name__} nem tart hivatkozást az élő "
                "válaszokra — a Python megsemmisítheti őket a motor alól"
            )

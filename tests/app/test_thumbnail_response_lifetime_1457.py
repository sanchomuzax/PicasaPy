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
from PySide6.QtCore import Qt
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
    """⚠️ **A bizonyító erő korlátja — kimondva.**

    Ezek a tesztek **közvetlenül Pythonból** hívják a
    `requestImageResponse()`-t, tehát NEM haladnak át azon a PySide
    C++ virtual-call hídon, amelyik a válasz tulajdonjogát C++-ra
    ruházná. Ezért az `ownedByPython=True` itt **várható**, nem lelet — és
    a `shiboken6.delete()` sem azt csinálja, amit a valódi motor
    (queued feldolgozás után `deleteLater()`).

    ⇒ Az itteni nyilvántartás-őrök azt mérik, hogy a MI könyvelésünk
    következetes (a válasz túléli a pool-feladatot, és a `destroyed`-re
    kiürül) — azt NEM bizonyítják, hogy a valódi motorban lett volna
    tulajdonjog-hiba. Az erős hivatkozás óvatos kerülőmegoldás, nem
    bizonyított javítás.

    A valódi próbához a kérést egy QML `Image`-nek kell indítania, és
    response-onként rögzíteni a C++ mutatót, az `ownedByPython`
    értéket és a szálat — a visszahívásban, egy utána queued próbában, a
    `textureFactory()`-ban és a `destroyed`-kor. Ez a #1457 nyitott
    feladata (független átnézés javaslata).
    """

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
        választ. (A `processEvents` azért marad, hogy a kötés akkor is
        lefusson, ha a Qt később mégis sorba tenné a kézbesítést.)"""
        from picasapy.app.thumbnail_provider import _ThumbResponse

        response = _ThumbResponse()
        jelzesek = []
        response.finished.connect(lambda: jelzesek.append(1))
        response.cancel()
        response._finish(QImage(8, 8, QImage.Format.Format_RGB32))
        assert response._image.isNull(), "lemondott válaszba nem írunk képet"
        qt_app.processEvents()
        assert jelzesek == [1], "a motornak jeleznünk kell, hogy eltakaríthassa"

    def test_a_jelzes_ma_a_POOL_szalrol_megy_ki_es_ezt_kimondjuk(self, qt_app):
        """A #1457 NYITOTT része — az őr a mai állapotot rögzíti, nem a vágyat.

        A `finished` ma a pool-szálról megy ki, miközben a motor a saját
        szálán hívja a `deleteLater`-t ugyanazon az objektumon. Készült rá
        javítás (a kibocsátás átütemezése a válasz saját szálára), de a
        CI-ben ezután egy MÁSIK tesztfájl kezdett összeomlani, miközben a
        főág ott zöld volt — és a bukást helyben, terhelés alatt, nyolc
        körben sem sikerült reprodukálni. Bizonyítatlan gyanúval időzítést
        változtató módosítást nem viszünk be; a jegy nyitva marad.

        Ez az őr azért van, hogy a következő olvasó **ne higgye
        megoldottnak**: ha valaki az átütemezést visszahozza, ez a teszt
        buktatja, és ezzel odavezeti a jegyhez, a méréseivel együtt."""
        import threading

        from picasapy.app.thumbnail_provider import _ThumbResponse

        response = _ThumbResponse()
        kibocsato: list[int] = []
        # ⚠️ KÖZVETLEN kapcsolat: enélkül a kötést a főszálon hoztuk
        # létre, tehát a Qt oda SOROLNÁ a szeletet, és a mérés a
        # kézbesítés szálát adná — nem a KIBOCSÁTÁSÉT. Az őr első
        # változata pontosan ezen csúszott el, és fogatlan volt.
        response.finished.connect(
            lambda: kibocsato.append(threading.get_ident()),
            Qt.ConnectionType.DirectConnection,
        )

        dolgozo_azonosito: list[int] = []

        def dolgozo() -> None:
            dolgozo_azonosito.append(threading.get_ident())
            response._finish(QImage(8, 8, QImage.Format.Format_RGB32))

        szal = threading.Thread(target=dolgozo)
        szal.start()
        szal.join(5.0)
        qt_app.processEvents()

        assert kibocsato == dolgozo_azonosito, (
            "a `finished` már NEM a pool-szálról megy ki. Ha ez szándékos "
            "javítás, olvasd el a #1457-et: az átütemezés egyszer már "
            "bekerült, és a CI-ben egy másik tesztfájl kezdett tőle "
            "összeomlani. Mérd le, mielőtt visszahozod."
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


class TestAKepMezoAllapotaKonzisztens:
    """A `cancel` és a befejezés ÁLLAPOTA konzisztens marad.

    ⚠️ **Helyesbítés.** Ez az osztály korábban azt állította, hogy a zár a
    `QImage` hivatkozásszámlálójának sérülése ellen véd. Független átnézés
    kimutatta, hogy ez **túl erős állítás**: a Qt implicit megosztásának
    számlálója atomikus, külön `QImage`-példányok szálak közötti másolása
    támogatott. Amit a zár ténylegesen véd, az az ÁLLAPOT: lemondott
    válaszba ne írjunk képet, és a `_done` jelző a képpel együtt álljon be.

    Az eredeti szöveg (megőrizve, hogy a tévedés nyoma megmaradjon):

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

    def test_mindketto_UGYANUGY_bocsatja_ki_a_jelzest(self):
        """A két szolgáltató NE csússzon szét ezen a ponton sem.

        ⚠️ A jelzés ma MINDKETTŐBEN a pool-szálról megy ki, és ez a #1457
        NYITOTT része: a motor a saját szálán hívja a `deleteLater`-t
        ugyanazon az objektumon. Készült rá javítás (a kibocsátás
        átütemezése a válasz saját szálára), de a CI-ben ezután egy MÁSIK
        tesztfájl kezdett összeomlani, miközben a főág ott zöld volt — és
        a bukást helyben, terhelés alatt, nyolc körben sem sikerült
        reprodukálni. Bizonyítatlan gyanúval időzítést változtató
        módosítást nem viszünk be.

        Amit ez az őr véd: ha valaki a KÉT szolgáltató közül csak az
        egyiket írja át, a másik ne maradjon le csendben — a #1457 első
        köre pontosan ezen bukott el."""
        import inspect

        alakok = {
            nev: ("invokeMethod" in inspect.getsource(osztaly))
            for nev, osztaly in self._valasz_osztalyok().items()
        }
        assert len(set(alakok.values())) == 1, (
            "a két bélyegkép-szolgáltató MÁSHOGY bocsátja ki a `finished` "
            f"jelzést: {alakok}. Az egyik javítása a másikat is kell hogy "
            "kövesse — különben a hiba megmarad abban, amelyik lemaradt."
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


class TestALebontasAValaszLANCOTIsBevarja:
    """A pool VÉGE nem a lánc vége (#1457/#999).

    Ezt egy független átnézés mutatta ki, és ez a nap legerősebb új
    nyoma: a `wait_for_done` csak azt garantálja, hogy a pool-feladatok
    lefutottak. A Qt viszont ezután még a saját image-reader szálán
    dolgozza fel a `finished` jelzést, hívja a `textureFactory()`-t, majd
    a `deleteLater()`-t. Amíg ez nem futott le, a válasz-objektumok
    ÉLNEK — és ha közben a teszt elengedi a vezérlőket és a motort, a lánc
    félig lebontott világban folytatódik.
    """

    def test_a_bevaras_LATHATOVA_teszi_a_maradekot(self, qt_app, tmp_path):
        """A bevárás nem buktat rá, de MEGNEVEZI, mi maradt életben.

        ⚠️ Motor NÉLKÜL létrehozott válaszokat senki nem semmisít meg —
        nincs, aki a tulajdonjogot átvegye —, tehát a számláló jogosan
        nem ürül ki. Az első változatom emiatt HÁROM meglévő tesztet
        buktatott: minden ilyen teardown végigvárta volna a teljes
        időkorlátot, majd elhasal. A lépés ezért csak esélyt ad a láncnak,
        és az eredményt láthatóvá teszi.

        Aki VALÓDI motorral dolgozik, az állítson az ürességre — ott a
        maradék tényleg hiba."""
        from picasapy.app.worker_thread import (
            elo_valaszok,
            wait_for_all_background_workers,
        )

        provider = _provider(tmp_path)
        for i in range(6):
            provider.requestImageResponse(f"{90000 + i}", None)

        assert wait_for_all_background_workers(30.0), (
            "a háttérmunka bevárása nem futott ki"
        )
        maradek = elo_valaszok()
        assert any("ThumbnailProvider" in sor for sor in maradek), (
            "a jelentésnek meg kell neveznie a szolgáltatót, amelynél élő "
            f"válasz maradt; kapott: {maradek}"
        )

    def test_a_bevaras_JELENTI_is_mi_maradt(self, qt_app, tmp_path):
        """A néma bukás itt a legrosszabb: a hibaüzenet nevezze meg, mi él."""
        import inspect

        from picasapy.app import worker_thread

        forras = inspect.getsource(worker_thread._valaszlanc_kiurult)
        assert "DeferredDelete" in forras, (
            "a halasztott törléseket kifejezetten ki kell hajtani, különben a "
            "`deleteLater` a következő eseményhurok-fordulóig vár"
        )
        assert callable(worker_thread.elo_valaszok), (
            "a hívónak meg kell tudnia nevezni, MELYIK szolgáltatónál maradt "
            "élő válasz; a puszta „nem sikerült” itt semmit nem ér"
        )

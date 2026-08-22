"""A bélyegkép-URL kövesse a fájl változását (#1186).

## A tulajdonos jelentése (v0.8.29)

> „Kollázskép vázlatot szerkesztésre megnyitottam, lementettem
> kollázsként, … de nem frissült az indexkép, maradt rajta a »Piszkozat«
> felirat. A kollázs megnyitva már nem piszkozat."

## A mérés

A bélyegkép-gyorstár (`thumbs/cache.py`) és a szolgáltató memója is a
(útvonal, `mtime_ns`, méret) hármasra kulcsol, tehát felülírt fájlhoz
ÚJ bélyegkép készül. A rács viszont sosem kéri el: a QML `Image.source`

```
image://thumbs/<id>?r=<rotate_steps>&f=<filters-crc>
```

alakú, és felülíráskor MINDHÁROM összetevő változatlan (ugyanaz a sor,
ugyanaz a forgatás, ugyanaz a szerkesztéslánc). A Qt a képet URL szerint
gyorstárazza, ezért a régi képpontok maradnak a képernyőn.

Ez nem kollázs-specifikus: bármely külső felülírás (szerkesztés más
programban, csere, visszaállítás) ugyanígy néma.
"""

from picasapy.app.models import PhotoGridModel
from picasapy.index import PhotoRecord


def _rekord(**modosit) -> PhotoRecord:
    mezok = dict(
        id=1,
        folder_path="/k",
        name="a.jpg",
        kind="image",
        size=1000,
        mtime_ns=1_000_000_000,
        star=False,
        caption=None,
        keywords=(),
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=100,
        height=100,
        hidden=False,
    )
    mezok.update(modosit)
    return PhotoRecord(**mezok)


def _url(record) -> str:
    modell = PhotoGridModel()
    modell.set_photos((record,))
    return modell.thumbUrlAt(0)


class TestBelyegkepUrl:
    def test_a_fajl_felulirasa_uj_URL_t_ad(self, qt_app):
        """⚠️ A jegy magja: eddig a felülírt fájl URL-je változatlan volt,
        ezért a Qt a RÉGI képpontokat mutatta tovább."""
        regi = _url(_rekord())
        uj = _url(_rekord(mtime_ns=2_000_000_000, size=1234))
        assert regi != uj, (
            "a felülírt fájl bélyegkép-URL-je nem változott — a Qt "
            "gyorstára a régi képet mutatja tovább"
        )

    def test_valtozatlan_fajlhoz_valtozatlan_URL(self, qt_app):
        """Megőrző: azonos fájlhoz ne készüljön új URL, különben minden
        újraolvasás feleslegesen újrarajzoltatná az egész rácsot."""
        assert _url(_rekord()) == _url(_rekord())

    def test_a_forgatas_es_a_lanc_tovabbra_is_szamit(self, qt_app):
        """Megőrző (#59): a forgatás és a szerkesztéslánc eddig is
        cache-busterként szolgált."""
        alap = _url(_rekord())
        assert _url(_rekord(rotate_steps=1)) != alap
        assert _url(_rekord(filters=" fokuszalas=1,0,0,0;")) != alap


class TestVegponttolVegpontig:
    """A tulajdonos esete: a fájl a lemezen kicserélődik (a kollázs
    véglegesítése felülírja a PISZKOZAT-feliratos helykitöltőt), és a
    rácsnak új képet kell kérnie."""

    def test_a_felulirt_fajl_utan_uj_URL_all_a_racson(
        self, qt_app, tmp_path
    ):
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache
        from PySide6.QtCore import QSettings
        from support.jpeg_factory import make_jpeg

        lib = tmp_path / "kepek"
        lib.mkdir()
        cel = lib / "kollazs.jpg"
        make_jpeg(cel, size=(64, 48))
        db = tmp_path / "index.db"
        beallitasok = QSettings(
            str(tmp_path / "s.ini"), QSettings.Format.IniFormat
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32))
        controller = AppController(db, (str(lib),), provider, settings=beallitasok)
        controller.rescan()
        for _ in range(200):
            qt_app.processEvents()
            if controller.waitForBackgroundWorkers(0.05):
                break
        qt_app.processEvents()
        assert controller.photos.rowCount() == 1
        elotte = controller.photos.thumbUrlAt(0)

        # a véglegesítés felülírja a fájlt — MÁS tartalom, más méret
        make_jpeg(cel, size=(200, 150))
        controller.resyncFolder(str(lib))
        for _ in range(200):
            qt_app.processEvents()
            if controller.waitForBackgroundWorkers(0.05):
                break
        qt_app.processEvents()

        utana = controller.photos.thumbUrlAt(0)
        assert utana and utana != elotte, (
            "a felülírás után is ugyanaz a bélyegkép-URL — a rács a régi "
            f"(PISZKOZAT-feliratos) képet mutatná: {elotte!r}"
        )

"""Az „Exportált képek" csomópont tartósan üres rácsot nyit (#1565).

## A mért kiindulás

Valódi `AppController`, produkciós időzítők, valódi fájlok; az export célja
a figyelt gyökereken **kívül** van (`<Képek>/Picasa/Exports/nyar` alakú út —
ez az export ALAPÉRTELMEZETT helye):

| eset | lemezen | látszik | idő | a csomópont listázza |
|---|---:|---:|---|---|
| watcher BE, lekérdezés BE | 3 | **0** | nem 25 s alatt | igen |
| watcher KI, lekérdezés BE | 3 | **0** | nem 25 s alatt | igen |
| watcher KI, lekérdezés KI | 3 | **0** | nem 25 s alatt | igen |

Az ELSŐ sor a lelet, és ez különbözteti meg a #1522/#1538/#1539
családtól: ott a figyelő bekapcsolva egy másodperc alatt behozta a
kimenetet, itt **a figyelővel együtt sem jön be soha**. Nem időzítés:
a mappának egyáltalán nincs helye az indexben, a `selectFolder` pedig
kizárólag az indexből olvas. A bal hasáb sora közben ott áll (a
nyilvántartás a beállításokban él, a létezést a fájlrendszerből
ellenőrizzük) — a felület tehát olyat kínál, amit a program nem tud
megmutatni.

## A választott út és az indoka

**Indexeljük az exportcélt, saját gyökérként** — nem a csomópontot
vesszük el. Az indok BIZONYÍTÉK, nem ízlés:

* `IDS_EXPORTED_CATEGORY` = „Exported Pictures" / „Exportált képek"
  (`referencia/stringres-en-hu.tsv` 1558. sor);
* a dekompilátumban ez a sztring abban a **kategória-táblában** áll, amely
  a `"Folders on Disk"` / `IDS_FOLDERS`, a `"Projects (internal)"` /
  `IDS_PROJECTS` és az `"Other Stuff"` / `IDS_DEFAULTCAT` párokat is
  felsorolja (`FUN_004a1560`) — vagyis az „Exported Pictures" a Picasánál
  ugyanolyan **könyvtár-kategória** (`P2category` érték), mint a lemezen
  álló mappáké, nem külön, fájlrendszerből listázó nézet;
* a 859 valódi `.picasa.ini`-t tartalmazó korpuszban **három** mappa
  hordozza a `P2category=Exported Pictures` értéket
  (`src/picasapy/ini/folder_category.py`).

Az eredetiben tehát az exportált mappa a KÖNYVTÁR RÉSZE. A csomópont
elvétele ezzel szemben menne, és a felhasználótól venne el funkciót.

## A kétszeres indexelés — MÉRVE

A #1539 mérése kimondta, hogy a webexport kicsinyített példányainak
indexelése ártana. Az exportcélra a „kétszer" tényszerűen igaz, és meg is
mértük: három kép exportja után a rácson **6 sor** áll, képenként kettő
(`forras` + `nyar`). Ez itt mégsem hiba — az eredeti Picasa is a könyvtár
részévé teszi az exportált mappát, a figyelt gyökér ALÁ exportált kép pedig
a #1539 óta nálunk is bejön a másolatával együtt. A mai állapot tehát nem
„egyszeres", hanem következetlen: ugyanaz az export a cél HELYÉTŐL függően
viselkedik másképp. A webexport `thumbnail/`/`image/` mappája ezzel szemben
gépi segédanyag egy HTML-oldalhoz — az továbbra sem indexelődik.

## Amit ez az út NEM tesz

**Nem lesz belőle figyelt gyökér.** A `WatchedFolders.txt` a könyvtár
horgonya (#1542/#1560); egy exportcél miatt nem bővítjük. Az exportcélok
külön kategória: a saját nyilvántartásukból (`exported_folders.py`,
korlátos, létezésre szűrt lista) indexeljük őket, saját gyökérként —
pontosan a `collage_save._index_saved_collage` gépezete.
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
def egyseg(qt_app, tmp_path):
    """Valódi vezérlő, figyelő és #1275 lekérdezés NÉLKÜL.

    A figyelő kikapcsolása itt nem a mérés élesítése (a #1565-nél a
    figyelő sem segít), hanem az, hogy a teszt egy magon se legyen
    időzítés-függő."""
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "konyvtar"
    (library / "forras").mkdir(parents=True)
    for i in range(1, 4):
        make_jpeg(library / "forras" / f"IMG_{i:04d}.jpg")
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
    _var(qt_app, lambda: not ctl._sync_running)
    if ctl._watcher is not None:
        ctl._watcher.stop()
        ctl._watcher = None
    if ctl._folder_poll_timer is not None:
        ctl._folder_poll_timer.stop()
    _var(qt_app, lambda: not ctl._sync_running)
    ctl.selectFolder(str(library / "forras"))
    assert _var(qt_app, lambda: ctl.photos.rowCount() == 3)
    yield ctl, library, tmp_path
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _kivul_all(ctl, cel) -> None:
    """A mérés ELŐFELTÉTELE, kimondva: a cél a figyelt gyökereken KÍVÜL áll.

    ⚠️ #1626: ez korábban hallgatólagos volt, és a windows-lábon NEM
    teljesült. A könyvtár `kepek`, az exportcél `Kepek/Picasa/Exports/…`
    nevet kapott — Linuxon két külön mappa, Windowson viszont UGYANAZ (a
    fájlrendszer nem kis-nagybetűérzékeny). Az exportcél így a figyelt
    gyökér ALÁ került, a `_root_for_folder` kapuja kilépett, és a fájl négy
    tesztje elbukott — nem termékhiba miatt, hanem mert a mérés mást mért,
    mint amit állít.

    A `_root_for_folder` `Path.resolve()`-ot használ, tehát ez az
    ellenőrzés mindkét platformon a VALÓDI helyzetet nézi: a névütközés
    visszatérése itt csattan, nem négy homályos állításban."""
    assert ctl._root_for_folder(str(cel)) is None, (
        f"az exportcél ({cel}) a figyelt gyökér ALATT van — ez a fájl a "
        "gyökereken KÍVÜLI célt méri, tehát így üresen zöld vagy hamisan "
        "piros lenne (#1626)"
    )


def _exportalj(ctl, qt_app, cel) -> None:
    kesz = []
    ctl.exportFinished.connect(lambda *a: kesz.append(a))
    ctl.exportRows([0, 1, 2], str(cel), 0, 85, False, "", False, False)
    assert _var(qt_app, lambda: kesz, 60.0), "az export nem futott le"
    assert len(list(cel.glob("*.jpg"))) == 3, f"az export nem írt fájlt: {kesz}"
    _kivul_all(ctl, cel)


def _latszik(ctl, cel) -> int:
    """Hány kép látszik a rácson a `cel` mappából.

    ⚠️ #1626: `path_key`-jel, nem nyers sztringgel. Az indexben a
    `normalize_path` FELOLDOTT alakja áll, a teszt viszont a maga építette
    utat ismeri — Windowson a kettő írásmódja eltérhet (a lemezről visszaadott
    kis-nagybetű), és a hasonlítás akkor is 0-t adna, ha a képek ott vannak.
    A `path_key` a projekt saját „ugyanaz a mappa" kulcsa."""
    from picasapy.paths import path_key

    cel_kulcs = path_key(str(cel))
    return sum(
        1 for p in ctl.photos.photos if path_key(p.folder_path) == cel_kulcs
    )


class TestAzExportaltKepekCsomopontNemUresRacsotNyit:
    """A jegy tényleges helyzete, végponttól végpontig."""

    def test_a_kivulre_exportalt_kepek_megjelennek(self, egyseg, qt_app):
        """A mért kiindulás: 3 kép a lemezen, 0 a rácson — tartósan."""
        ctl, _library, tmp_path = egyseg
        cel = tmp_path / "Kepek" / "Picasa" / "Exports" / "nyar"

        _exportalj(ctl, qt_app, cel)
        # a felhasználó rákattint az „Exportált képek" sorára
        ctl.selectFolder(str(cel))

        assert _var(qt_app, lambda: _latszik(ctl, cel) == 3), (
            "a figyelt gyökereken KÍVÜLRE exportált három kép közül "
            f"{_latszik(ctl, cel)} látszik — az Exportált képek "
            "csomópontja tartósan üres rácsot nyit (#1565)"
        )

    def test_az_exportcel_nem_lesz_figyelt_gyoker(self, egyseg, qt_app):
        """A `WatchedFolders.txt` szemantikája nem sérülhet (#1542/#1560).

        Az exportcél KÜLÖN kategória: indexeljük, de a felhasználó figyelt
        mappáihoz nem adjuk hozzá."""
        ctl, library, tmp_path = egyseg
        cel = tmp_path / "Kepek" / "Picasa" / "Exports" / "nyar"

        _exportalj(ctl, qt_app, cel)
        ctl.selectFolder(str(cel))
        assert _var(qt_app, lambda: _latszik(ctl, cel) == 3)

        assert list(ctl.watchedFolders) == [str(library)], (
            "az exportcél némán figyelt gyökérré vált — a figyelt mappák "
            "listája a könyvtár horgonya, nem bővíthető a felhasználó "
            "megkérdezése nélkül (#1542/#1560)"
        )
        watched_file = tmp_path / "WatchedFolders.txt"
        if watched_file.exists():
            assert str(cel) not in watched_file.read_text(encoding="utf-8")

    def test_a_nyilvantartason_kivuli_kimenet_tovabbra_sem_indexelodik(
        self, egyseg, qt_app
    ):
        """A #1539 határa MEGMARAD: nem minden kívülre írt kimenet jön be.

        Csak az Exportált képek nyilvántartásába felvett célmappa —
        a figyelt körön kívülre mentett kollázs továbbra sem."""
        ctl, _library, tmp_path = egyseg
        kivul = tmp_path / "kivul"
        kivul.mkdir()
        kesz = []
        ctl.collageFinished.connect(lambda *a: kesz.append(a))
        ctl.collageFailed.connect(lambda m: kesz.append(("HIBA", m)))

        ctl.makeCollage([0, 1], "picturegrid", str(kivul / "kollazs.jpg"))

        assert _var(qt_app, lambda: kesz), "a kollázs nem készült el"
        assert kesz[0][0] != "HIBA", kesz
        assert (kivul / "kollazs.jpg").exists()
        ctl.selectFolder(str(kivul))
        assert not _var(qt_app, lambda: _latszik(ctl, kivul) != 0, 3.0), (
            "a figyelt körön kívülre mentett kollázs is beindexelődött — "
            "a #1565 csak a NYILVÁNTARTOTT exportcélokra szól"
        )


    def test_a_figyelt_gyoker_alatti_exportcel_nem_indexelodik_ketszer(
        self, egyseg, qt_app
    ):
        """A korai kilépés FOGA (a #1539 azonos szerkezete).

        Ha az exportcél a figyelt gyökér ALATT van, azt már a #1539
        célzott újraolvasása elviszi — a saját gyökeres ágnak ott el sem
        szabad indulnia, különben minden ilyen export fölöslegesen nyitna
        egy második index-kapcsolatot és olvasná be ugyanazt a mappát.

        A mérés szinkron: az `indexExportedFolder` a `syncFinished`-et a
        munka VÉGÉN, még a híváson belül bocsátja ki, a #1539 ága viszont
        háttérszálon dolgozik — `processEvents()` nélkül tehát csak az itteni
        ág számlálhat. Enélkül az állítás nélkül a kapu némán eltávolítható
        volt (mutációval mérve: mind az öt teszt zöld maradt)."""
        from picasapy.app.exported_folders import EXPORTED_FOLDERS_SETTINGS_KEY

        ctl, library, _tmp_path = egyseg
        belul = library / "export_ide"
        belul.mkdir()
        make_jpeg(belul / "IMG_0001.jpg")
        # a nyilvántartásban BENNE van, de figyelt gyökér alatt áll
        ctl._get_settings().setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [str(belul)])
        jelzesek = []
        ctl.syncFinished.connect(lambda: jelzesek.append(1))

        ctl.indexExportedFolder(str(belul / "IMG_0001.jpg"))

        assert jelzesek == [], (
            "a figyelt gyökér alatti exportcélra is elindult a saját "
            "gyökeres indexelés — fölösleges második index-megnyitás "
            "minden ilyen exportnál"
        )

    def test_a_kivuli_exportcelra_viszont_elindul(self, egyseg, qt_app):
        """A korai kilépés ellenpróbája: kívül IGENIS dolgozik.

        Enélkül a fenti állítást egy „soha ne csinálj semmit" mutáció is
        kielégítené."""
        from picasapy.app.exported_folders import EXPORTED_FOLDERS_SETTINGS_KEY

        ctl, _library, tmp_path = egyseg
        kivul = tmp_path / "Kepek" / "Picasa" / "Exports" / "tel"
        kivul.mkdir(parents=True)
        make_jpeg(kivul / "IMG_0001.jpg")
        _kivul_all(ctl, kivul)
        ctl._get_settings().setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [str(kivul)])
        jelzesek = []
        ctl.syncFinished.connect(lambda: jelzesek.append(1))

        ctl.indexExportedFolder(str(kivul / "IMG_0001.jpg"))

        assert jelzesek == [1]


class TestAzExportcelTuleliAzIndulasiTakaritast:
    """A `prune_foreign_folders` (#58) minden figyelt gyökéren kívüli
    mappát töröl INDULÁSKOR. Enélkül az exportcél a következő indításig
    élne, és a hiba visszatérne — a kollázsnál ezt a
    `_onjavito_kollazsmappa` (#1075) oldja meg.

    #1667: a túlélést azóta NEM a takarítás utáni visszaépítés adja, hanem
    az, hogy a takarítás a nyilvántartott exportcélokat VÉDETT gyökérként
    kapja meg (`_takaritas_gyokerei`). A régi szerkezet minden induláskor
    kidobta és nulláról olvasta vissza az exportált képeket — a tulajdonos
    gépén 8,4 másodpercért."""

    def test_ujraindulas_utan_is_latszik(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app.application import (
            _takaritas_gyokerei,
            _ujraindexelt_exportcelok,
        )
        from picasapy.app.exported_folders import EXPORTED_FOLDERS_SETTINGS_KEY
        from picasapy.index import open_index, prune_foreign_folders, sync_folder

        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(library / "IMG_0001.jpg")
        cel = tmp_path / "Kepek" / "Picasa" / "Exports" / "nyar"
        cel.mkdir(parents=True)
        make_jpeg(cel / "IMG_0001.jpg")
        # #1626: itt nincs vezérlő, tehát a `_kivul_all` helyett kézzel —
        # ugyanaz az előfeltétel, ugyanazzal a `resolve()`-os összevetéssel
        assert not cel.resolve().is_relative_to(library.resolve()), (
            f"az exportcél ({cel}) a figyelt gyökér ALATT van — a "
            "`prune_foreign_folders` ki sem dobná, tehát a teszt üresen "
            "zöld lenne (#1626)"
        )

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel)])

        with open_index(tmp_path / "index.db") as conn:
            sync_folder(conn, library, library)
            sync_folder(conn, cel, cel)
            # így indul a program: a takarítás a VÉDETT gyökereket kapja
            # (#1667), a visszavétel pedig az első képkocka után fut
            prune_foreign_folders(
                conn, _takaritas_gyokerei((str(library),), settings)
            )
            _ujraindexelt_exportcelok(conn, settings)
            maradt = [
                row["path"] for row in conn.execute("SELECT path FROM folders")
            ]
            kepek = conn.execute(
                "SELECT COUNT(*) FROM photos p JOIN folders f"
                " ON f.id = p.folder_id WHERE f.path = ?",
                (str(cel.resolve()),),
            ).fetchone()[0]

        assert str(cel.resolve()) in maradt, (
            "az indulási takarítás után az exportcél kiesett az indexből — "
            "az Exportált képek csomópontja a következő indítástól ismét "
            "üres rácsot nyitna (#1565)"
        )
        assert kepek == 1, (
            "az exportcél mappasora megmaradt, de a KÉPEI nem — az "
            "Exportált képek csomópontja üres rácsot nyitna (#1565/#1667)"
        )

    def test_az_indexbe_meg_be_nem_kerult_exportcel_indulaskor_bekerul(
        self, qt_app, tmp_path
    ):
        """A visszavétel ÖNJAVÍTÓ szerepe — ezt a védelem nem pótolja.

        MÉRVE (#1667 mutációs próba): a fenti
        `test_ujraindulas_utan_is_latszik` a `_ujraindexelt_exportcelok`
        kiürítésével is ZÖLD maradt, mert azt a helyzetet a #1667 óta a
        takarítás-védelem tartja. A funkciónak viszont maradt egy olyan
        fele, amit CSAK a visszavétel tud:

        * a felhasználó a program KIKAPCSOLT állapotában (vagy egy másik
          gépről, NAS-on) tett képet az exportmappába;
        * az index egy régebbi verzióval készült, amely a célt még
          kitakarította;
        * az exportcél sosem került be, mert az exportot végző munkamenet
          összeomlott.

        Mindháromban a mappa a lemezen ott van, az indexben nincs. Ha a
        visszavétel nem fut le, az „Exportált képek" üres rácsot nyit —
        pontosan a #1565 eredeti hibája."""
        from PySide6.QtCore import QSettings

        from picasapy.app.application import (
            _takaritas_gyokerei,
            _ujraindexelt_exportcelok,
        )
        from picasapy.app.exported_folders import EXPORTED_FOLDERS_SETTINGS_KEY
        from picasapy.index import open_index, prune_foreign_folders, sync_folder

        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(library / "IMG_0001.jpg")
        cel = tmp_path / "Kepek" / "Picasa" / "Exports" / "tel"
        cel.mkdir(parents=True)
        make_jpeg(cel / "IMG_0007.jpg")

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(EXPORTED_FOLDERS_SETTINGS_KEY, [str(cel)])

        with open_index(tmp_path / "index.db") as conn:
            # SZÁNDÉKOSAN csak a könyvtár kerül be: az exportcél az
            # indexben MÉG NINCS BENNE
            sync_folder(conn, library, library)
            elozetes = [
                row["path"] for row in conn.execute("SELECT path FROM folders")
            ]
            assert str(cel.resolve()) not in elozetes, (
                "a próba előfeltétele, hogy az exportcél még ne legyen az "
                "indexben — különben a teszt üresen zöld"
            )

            prune_foreign_folders(
                conn, _takaritas_gyokerei((str(library),), settings)
            )
            _ujraindexelt_exportcelok(conn, settings)

            kepek = [
                row["name"]
                for row in conn.execute(
                    "SELECT p.name FROM photos p JOIN folders f"
                    " ON f.id = p.folder_id WHERE f.path = ?",
                    (str(cel.resolve()),),
                )
            ]

        assert kepek == ["IMG_0007.jpg"], (
            "az indexben addig nem szereplő exportcél az indulás után sem "
            "került be — az Exportált képek csomópont üres rácsot nyit "
            f"(#1565). Az indexben talált képek: {kepek}"
        )

    def test_az_indulasi_ag_hivja_is(self):
        """A LÁNC, nem a végpont: az induláskor tényleg meg kell hívni.

        A törzs önmagában semmit nem ér, ha a `run()` nem hívja — ez az a
        csapda, amit a projekt már megjárt („mérd a bekötés LÁNCÁT, ne a
        végpontokat").

        #1667 óta KÉT állítás tartja a funkciót, és a sorrend-állítás
        helyébe a védelem lépett:

        1. a takarítás a VÉDETT gyökereket kapja (`_takaritas_gyokerei`),
           tehát ki sem dobja az exportcélt;
        2. a visszavétel (az önjavító ág) továbbra is elindul valahonnan.

        Hogy a 2. pont HOL fut, azt a #1667 elhelyezés-őre állítja
        (`tests/perf/test_exportcelok_indulas_1667.py`).

        #1716 óta a takarítás HÍVÁSA a `run()`-ból egy külön wrapperbe
        (`_ottragadt_mappak_takaritasa`) költözött — az első képkocka
        utánra (ld. `tests/perf/test_takaritas_utrol_1716.py`). A
        `run()` forrása ezért már a wrappert hívja, nem közvetlenül a
        `prune_foreign_folders`-t; a védett-gyökér-állítást a wrapper
        SAJÁT forrásában ellenőrizzük."""
        import inspect

        from picasapy.app import application

        forras = inspect.getsource(application.run)

        assert "_ottragadt_mappak_takaritasa(" in forras, (
            "a `run()` egyáltalán nem takarít induláskor (#58) — a #1716 "
            "óta a `_ottragadt_mappak_takaritasa` wrapperen át kellene "
            "hívnia"
        )
        takaritas_forras = inspect.getsource(
            application._ottragadt_mappak_takaritasa
        )
        assert "_takaritas_gyokerei(roots" in takaritas_forras, (
            "a `prune_foreign_folders` NEM a védett gyökereket kapja — a "
            "takarítás minden induláskor kidobja a nyilvántartott "
            "exportcélokat, és a visszaépítés újraolvassa az összes "
            "exportált képet (#1667)"
        )
        assert "_exportcelok_visszavetele(" in forras, (
            "a `run()` nem hívja az exportcélok visszavételét — a "
            "mechanizmus megvan, csak senki nem indítja el (#1565)"
        )

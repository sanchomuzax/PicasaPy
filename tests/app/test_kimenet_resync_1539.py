"""A dedup, a kollázs, a filmexport és a „Mentés másként" célmappája is
célzott újraolvasást kap (#1539).

## A mért kiindulás

Valódi `AppController`, produkciós `FOLDER_POLL_MS`, valódi fájlok; a
kimenet MINDEN esetben a figyelt gyökér alatti, **még nem indexelt**
mappába megy (a `Duplikátumok` almappát maga a dedup hozza létre):

| út | watcher BE, lekérdezés BE | watcher KI, lekérdezés BE | watcher KI, lekérdezés KI |
|---|---|---|---|
| dedup → `Duplikátumok` | 1,06 s | **nem 25 s alatt** | **nem 25 s alatt** |
| kollázs → ÚJ mappa | 1,03 s | **nem 25 s alatt** | **nem 25 s alatt** |
| filmexport → ÚJ mappa | 1,03 s | **nem 25 s alatt** | **nem 25 s alatt** |
| „Mentés másként" → ÚJ mappa | 1,02 s | **nem 25 s alatt** | **nem 25 s alatt** |
| kontroll: „Másolat mentése" HELYBEN | — | 0,02 s | 0,02 s |

A második oszlop a lelet, és ROSSZABB, mint a #1522-é: ott a tízmásodperces
#1275 lekérdezés a LÁTOTT mappát legalább behozta. Itt a kimenet egy MÁSIK
mappába megy, mint amit a felhasználó néz, ezért a lekérdezés rá sem néz —
a kép az ötperces rescanig sehol nincs meg.

## A kontroll-sor mondja meg, MI a hiba

A „Másolat mentése" 0,02 s alatt megjelenik, mert a `_ensure_save_progress`
már ma is köt egy újraolvasást a `saveCopyFinished`-re — csakhogy azt a
**LÁTOTT** mappára (`_poll_current_folder`), nem a TÉNYLEGES célmappára. Amíg
a másolat ugyanabba a mappába megy, ez véletlenül helyes; amint a
felhasználó a „Mentés másként…" fájlválasztójában máshova mutat, a program a
rossz mappát olvassa újra. Ez ugyanaz a hibaalak, mint a #1538 `.parent`-
csapdája: a mechanizmus megvan, csak nem arra a mappára néz, amelyik
tényleg megváltozott.

## Miért nem elég azt mondani, hogy „majd a watcher"

Ugyanaz, mint a #1522-nél: a `LibraryWatcher.start` csak az INDULÁSKOR
létező gyökereket veszi fel, és az inotify figyelőkerete
(`max_user_watches`) nagy gyűjteménynél elfogyhat. Mindkét esetben némán
nem szól — az első oszlop tehát nem garancia, hanem szerencse.
"""

from __future__ import annotations

import time

import pytest

from support.jpeg_factory import make_jpeg

PICTUREGRID = "picturegrid"


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


class _StubController:
    """A `wire_dedup` szerződése: ennyit használ a vezérlőből."""

    def __init__(self, roots):
        self.watchedFolders = list(roots)
        self._roots = list(roots)
        self.resynced: list[str] = []

    def resyncOutputFolder(self, path):
        from pathlib import Path

        mappa = Path(path).parent
        for root in self._roots:
            if mappa == Path(root) or mappa.is_relative_to(root):
                self.resynced.append(str(mappa))
                return


class TestADedupBekotese:
    """A bekötés szintje: a VEZÉRLŐ slotját hívjuk, valódi fájlokkal."""

    @pytest.fixture
    def wired(self, qt_app, tmp_path):
        from picasapy.app import application
        from picasapy.app.dedup_controller import DedupController

        root = tmp_path / "kepek"
        (root / "forras").mkdir(parents=True)
        make_jpeg(root / "forras" / "IMG_0001.jpg")
        make_jpeg(root / "forras" / "IMG_0002.jpg")
        stub = _StubController([str(root)])
        dedup = DedupController(tmp_path / "index.db", None)
        application.wire_dedup(dedup, stub)
        return dedup, stub, root

    def test_a_duplikatumok_mappa_ujraolvasast_kap(self, wired):
        """A `moveOthersToDuplicatesFolder` slot — nem a jelzés kézi
        kibocsátása."""
        dedup, stub, root = wired
        a = str(root / "forras" / "IMG_0001.jpg")
        b = str(root / "forras" / "IMG_0002.jpg")

        dedup.moveOthersToDuplicatesFolder([a, b], a)

        assert str(root / "forras" / "Duplikátumok") in stub.resynced, (
            "a dedup nem kért újraolvasást a FRISSEN LÉTREHOZOTT "
            "Duplikátumok mappára — a képek az ötperces rescanig eltűnnek"
        )

    def test_a_forrasmappa_is_ujraolvasast_kap(self, wired):
        """A forrásból ELTŰNT a kép: annak a sorát is le kell venni."""
        dedup, stub, root = wired
        a = str(root / "forras" / "IMG_0001.jpg")
        b = str(root / "forras" / "IMG_0002.jpg")

        dedup.moveOthersToDuplicatesFolder([a, b], a)

        assert str(root / "forras") in stub.resynced, (
            "a forrásmappa nem kapott újraolvasást — az elmozdított kép "
            "sora ottragad a rácson"
        )

    def test_a_kukazas_a_forrasmappat_ujraolvastatja(self, wired):
        """A `deleteOthers` is a forrásmappát változtatja meg."""
        dedup, stub, root = wired
        a = str(root / "forras" / "IMG_0001.jpg")
        b = str(root / "forras" / "IMG_0002.jpg")

        dedup.deleteOthers([a, b], a)

        assert str(root / "forras") in stub.resynced

    def test_a_sikertelen_muvelet_nem_ker_resyncet(self, wired):
        """Nem létező forrás: ne kérjünk fölösleges újraolvasást."""
        dedup, stub, root = wired
        a = str(root / "forras" / "IMG_0001.jpg")
        nincs = str(root / "forras" / "NINCS_ILYEN.jpg")

        dedup.moveOthersToDuplicatesFolder([a, nincs], a)

        assert stub.resynced == []


class TestAKimenetMegjelenikAFigyeloNelkul:
    """A jegy tényleges helyzete, végponttól végpontig.

    A figyelő ÉS a #1275 lekérdezés is le van állítva — így egyedül a
    célzott resync maradhat, ami a kimenetet behozza. Ez a foga: a javítás
    nélkül a kimenet csak az ötperces rescannel jönne be.
    """

    @pytest.fixture
    def egyseg(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        library = tmp_path / "kepek"
        (library / "forras").mkdir(parents=True)
        make_jpeg(library / "forras" / "IMG_0001.jpg")
        make_jpeg(library / "forras" / "IMG_0002.jpg")
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
        _var(qt_app, lambda: not ctl._sync_running)
        # a figyelő és a lekérdezés is LE: csak a célzott resync maradhat
        if ctl._watcher is not None:
            ctl._watcher.stop()
            ctl._watcher = None
        if ctl._folder_poll_timer is not None:
            ctl._folder_poll_timer.stop()
        _var(qt_app, lambda: not ctl._sync_running)
        ctl.selectFolder(str(library / "forras"))
        assert _var(qt_app, lambda: ctl.photos.rowCount() == 2)
        yield ctl, library
        ctl.shutdown()
        assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"

    def test_a_duplikatumok_mappaba_mozgatott_kep_megjelenik(self, egyseg, qt_app):
        from picasapy.app import application
        from picasapy.app.dedup_controller import DedupController

        ctl, library = egyseg
        dedup = DedupController(ctl._db_path, None)
        application.wire_dedup(dedup, ctl)
        a = str(library / "forras" / "IMG_0001.jpg")
        b = str(library / "forras" / "IMG_0002.jpg")

        dedup.moveOthersToDuplicatesFolder([a, b], a)

        assert _var(
            qt_app,
            lambda: any(
                "Duplikátumok" in str(p.folder_path) for p in ctl.photos.photos
            ),
        ), (
            "a Duplikátumok mappába mozgatott kép nem jelent meg — figyelő "
            "és #1275 lekérdezés nélkül csak a célzott resync hozhatja be"
        )

    def test_az_uj_mappaba_mentett_kollazs_megjelenik(self, egyseg, qt_app):
        ctl, library = egyseg
        uj = library / "ujmappa"
        uj.mkdir()
        kesz = []
        ctl.collageFinished.connect(lambda *a: kesz.append(a))
        ctl.collageFailed.connect(lambda m: kesz.append(("HIBA", m)))

        ctl.makeCollage([0, 1], PICTUREGRID, str(uj / "kollazs.jpg"))

        assert _var(qt_app, lambda: kesz), "a kollázs nem készült el"
        assert kesz[0][0] != "HIBA", kesz
        assert _var(qt_app, lambda: ctl.photos.rowCount() == 3), (
            "az ÚJ mappába mentett kollázs nem jelent meg a rácson"
        )

    def test_az_uj_mappaba_exportalt_film_megjelenik(self, egyseg, qt_app):
        ctl, library = egyseg
        uj = library / "ujmappa"
        uj.mkdir()
        kesz = []
        ctl.movieFinished.connect(lambda *a: kesz.append(a))
        ctl.movieFailed.connect(lambda m: kesz.append(("HIBA", m)))

        ctl.exportMovie([0, 1], str(uj / "film.mp4"), 720, 1.0)

        assert _var(qt_app, lambda: kesz, 60.0), "a film nem készült el"
        assert kesz[0][0] != "HIBA", kesz
        assert _var(qt_app, lambda: ctl.photos.rowCount() == 3), (
            "az ÚJ mappába exportált film nem jelent meg a rácson — az "
            ".mp4 INDEXELT médiatípus, tehát a rácsra való"
        )

    def test_az_uj_mappaba_mentett_masolat_megjelenik(self, egyseg, qt_app):
        """„Mentés másként…" — a mai kód a LÁTOTT mappát olvassa újra."""
        from PySide6.QtCore import QUrl

        ctl, library = egyseg
        uj = library / "ujmappa"
        uj.mkdir()
        kesz = []
        ctl.saveCopyFinished.connect(lambda *a: kesz.append(a))

        ctl.saveRowAs(0, QUrl.fromLocalFile(str(uj / "masolat.jpg")).toString())

        assert _var(qt_app, lambda: kesz), "a mentés másként nem futott le"
        assert (uj / "masolat.jpg").exists(), kesz
        assert _var(qt_app, lambda: ctl.photos.rowCount() == 3), (
            "a MÁS mappába mentett másolat nem jelent meg — a mai kód a "
            "látott mappát olvassa újra, nem a tényleges célt"
        )

    def test_a_helyben_mentett_masolat_tovabbra_is_megjelenik(self, egyseg, qt_app):
        """Kontroll: a „Másolat mentése" ma is működik, ne rontsuk el."""
        ctl, library = egyseg
        kesz = []
        ctl.saveCopyFinished.connect(lambda *a: kesz.append(a))

        ctl.saveCopyRows([0])

        assert _var(qt_app, lambda: kesz), "a másolat mentése nem futott le"
        assert _var(qt_app, lambda: ctl.photos.rowCount() == 3)

    def test_a_figyelt_koron_kivuli_cel_nem_kerul_az_indexbe(
        self, egyseg, qt_app, tmp_path
    ):
        """A figyelt gyökereken KÍVÜLRE mentett kollázs nem indexelődik.

        Ez SZÁNDÉKOS határ (a #1522 azonos állítása): a felhasználó
        figyelt köréhez nem adunk hozzá mappát egy exportcél miatt."""
        ctl, library = egyseg
        kivul = tmp_path / "kivul"
        kivul.mkdir()
        kesz = []
        ctl.collageFinished.connect(lambda *a: kesz.append(a))
        ctl.collageFailed.connect(lambda m: kesz.append(("HIBA", m)))

        ctl.makeCollage([0, 1], PICTUREGRID, str(kivul / "kollazs.jpg"))

        assert _var(qt_app, lambda: kesz), "a kollázs nem készült el"
        assert kesz[0][0] != "HIBA", kesz
        assert (kivul / "kollazs.jpg").exists()
        # a rács változatlan: a kimenet a figyelt körön kívülre ment
        assert not _var(qt_app, lambda: ctl.photos.rowCount() != 2, 3.0)

    def test_a_figyelt_gyoker_ala_exportalt_kep_megjelenik(self, egyseg, qt_app):
        """Az export a jegy 5. pontja — a figyelt körön BELÜLI cél.

        A figyelt körön KÍVÜLI (alapértelmezett) exportcélra ez a
        mechanizmus szándékosan nem hat; ld. az `exportRows` kommentjét."""
        ctl, library = egyseg
        cel = library / "export_ide"  # figyelt gyökér ALATT, indexeletlen
        kesz = []
        ctl.exportFinished.connect(lambda *a: kesz.append(a))

        ctl.exportRows([0], str(cel), 0, 85, False, "", False, False)

        assert _var(qt_app, lambda: kesz, 60.0), "az export nem futott le"
        assert list(cel.glob("*.jpg")), f"az export nem írt fájlt: {kesz}"
        assert _var(qt_app, lambda: ctl.photos.rowCount() == 3), (
            "a figyelt gyökér alá exportált kép nem jelent meg a rácson"
        )

    def test_a_kivulre_irt_kimenet_nem_utemez_munkat(self, egyseg, tmp_path):
        """A korai kilépés FOGA: kívülre írt kimenetre EL SEM INDUL a
        célzott szinkron.

        A nyilvántartás helyességét enélkül is a `_on_folders_dirty`
        gyökér-próbája őrzi — a `resyncOutputFolder` kapuja tehát nem a
        helyességért van, hanem hogy ne ütemezzünk háttérszálat és
        index-megnyitást olyan mappára, amit úgysem szinkronizálunk. Épp
        ez a GYAKORI eset: az export alapértelmezett célja a figyelt
        gyökereken kívülre mutat. Enélkül az állítás nélkül a kapu
        némán eltávolítható volna (mutációval mérve)."""
        ctl, _library = egyseg
        kivul = tmp_path / "kivul"
        kivul.mkdir()
        hivasok = []
        ctl.resyncFolder = lambda mappa: hivasok.append(mappa)

        ctl.resyncOutputFolder(str(kivul / "barmi.jpg"))

        assert hivasok == [], (
            "a figyelt körön kívüli célra is elindult a célzott szinkron — "
            "fölösleges háttérszál és index-megnyitás minden exportnál"
        )

    def test_a_belulre_irt_kimenet_utemez_munkat(self, egyseg):
        """A korai kilépés ellenpróbája: figyelt kör ALATT igenis indul.

        Enélkül a fenti állítást egy „soha ne csinálj semmit" mutáció is
        kielégítené."""
        ctl, library = egyseg
        hivasok = []
        ctl.resyncFolder = lambda mappa: hivasok.append(mappa)

        ctl.resyncOutputFolder(str(library / "ujmappa" / "barmi.jpg"))

        assert hivasok == [str(library / "ujmappa")]

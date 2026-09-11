"""A Picasa PROJEKT-mappáit körönként megnézzük (#1123).

## A jelentés

> „Létrehoztam egy kollázst a Picasa 3 segítségével, miközben fut a
> PicasaPy, és a PicasaPy alatt nem jelent meg a kollázs futás közben.
> Visszafelé ez azonnal működik."

Majd a tulajdonos mérése (2026-09-05): **másfél perc után sem** jelent
meg, a gyűjtemény CIFS-mounton van, és „a kollázs mappát látja a
PicasaPy". Ez a két adat együtt zárja ki a jegy eredeti magyarázatát (a
mappa a figyelt gyökereken kívül volna).

## Miért nem hozza be a mai kód

Három út létezik ma, és MINDHÁROM kimarad ebben a helyzetben:

1. **inotify** (`scanner/watcher.py`): CIFS-mounton távoli írásról
   egyáltalán nem érkezik esemény — ez a `docs/benchmarks/`-ban 2026-07-16
   óta mért tény, nem feltevés.
2. **a tízmásodperces célzott lekérdezés** (#1275/#1435): a KIVÁLASZTOTT
   mappát és a rács feedjében LÁTSZÓ mappákat nézi. A feed a betöltött
   fotó-rekordokból épül (`controller._update_feed_groups`), tehát amíg a
   felhasználó egy nyaralás-mappát néz, a Kollázsok mappa NINCS benne.
   Ha benne is van egy nagy gyűjteményben, a körbeforgó adag
   (`SWEEP_FOLDERS_PER_TICK = 8`) miatt egy adott mappa csak
   `ceil(N/8) · 10` másodpercenként kerül sorra — 500 mappánál ez tíz
   perc, vagyis a tulajdonos másfél perce alatt biztosan nem.
3. **az ötperces teljes rescan**: ez hozza be — a tulajdonos szava
   szerint „használhatatlanul lassú".

A #1539 a MI kimenetünkre már megoldotta ezt (`noteOutputWritten`), de
az IDEGEN program írására nincs bejelentőnk: ott csak lekérdezés van.

## Amit ez a fájl mér

A projekt-kimeneti mappák (Kollázsok, Filmek) állandó, KORLÁTOS és
PRIORITÁSOS tagjai a tízmásodperces pecsét-körnek — nem a feedtől és nem
a körbeforgó kurzortól függenek.
"""

from __future__ import annotations

import time

import pytest

from support.figyelo import allitsd_le_a_figyelot
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
    """Figyelt gyökér: egy nyaralás-mappa és a Picasa projekt-mappái.

    A `Picasa/Kollázsok` a gyökér ALATT van (a #1088 óta a rendszer
    képmappája a figyelt gyökér), tehát a jegy eredeti gyanúja — hogy
    kívül esne — itt szándékosan NEM áll fenn."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    # ⚠️ A projekt-mappák ÜRESEK, és ez szándékos: a rács feedje a
    # BETÖLTÖTT fotó-rekordokból épül, tehát egy fotó nélküli mappa nem is
    # kerülhet a feed adagjába. Pontosan ez az „első kollázs" helyzete.
    (root / "Picasa" / "Kollázsok").mkdir(parents=True)
    (root / "Picasa" / "Filmek").mkdir(parents=True)
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library, monkeypatch):
    """Élő vezérlő, rövid lekérdezési időközzel, LEÁLLÍTOTT figyelővel.

    A figyelő leállítása a NAS-helyzet hű mása: ott sem érkezik esemény a
    másik gép írásáról."""
    from PySide6.QtCore import QSettings

    from picasapy.app import collage_prefs, library_controller, movie_output
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    monkeypatch.setattr(library_controller, "FOLDER_POLL_MS", 150)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    # A célmappák BEÁLLÍTOTTAK: enélkül a próbák a valódi `~/Képek`-be
    # néznének (a `collage_output.output_dir` alapértelmezése).
    settings.setValue(collage_prefs.OUTPUT_DIR_KEY, str(library / "Picasa" / "Kollázsok"))
    settings.setValue(movie_output.OUTPUT_DIR_KEY, str(library / "Picasa" / "Filmek"))
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl.start()
    assert _var(qt_app, lambda: not ctl._sync_running, 20.0), (
        "a kezdő szinkron nem állt le 20 s alatt"
    )
    if ctl._watcher is not None:
        allitsd_le_a_figyelot(ctl)
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _indexelt_nevek(db_path, mappa) -> set[str]:
    """A mappa indexelt fotóinak neve — a rács feedjétől FÜGGETLENÜL."""
    from picasapy.index import open_index

    with open_index(db_path) as conn:
        sorok = conn.execute(
            "SELECT p.name FROM photos p JOIN folders f ON p.folder_id = f.id "
            "WHERE f.path = ?",
            (str(mappa),),
        ).fetchall()
    return {sor[0] for sor in sorok}


class TestAKiindulas:
    """A lelet: a feed NEM tartalmazza a Kollázsok mappát."""

    def test_a_feed_adagja_nem_latja_a_kollazs_mappat(
        self, controller, library, qt_app
    ):
        nyaralas = str(library / "nyaralas")
        controller.selectFolder(nyaralas)
        assert _var(qt_app, lambda: controller.photos.rowCount() == 2)

        feed = controller._sweep_candidates(nyaralas)

        assert str(library / "Picasa" / "Kollázsok") not in feed, (
            "ha a feed magától látná a Kollázsok mappát, a jegynek nem "
            "volna tárgya — akkor ez a próba a rossz dolgot méri"
        )


class TestAzIdegenKollazsMegjelenik:
    """A jegy zárófeltétele: a Picasával készült kollázs magától jön."""

    def test_a_kollazs_mappa_uj_kepe_bekerul_az_indexbe(
        self, controller, library, qt_app, tmp_path
    ):
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 2)
        kollazsok = library / "Picasa" / "Kollázsok"

        # a windowsos Picasa 3 ír a mappába, miközben mi máshol vagyunk
        make_jpeg(kollazsok / "uj_kollazs.jpg")

        assert _var(
            qt_app,
            lambda: "uj_kollazs.jpg" in _indexelt_nevek(
                tmp_path / "index.db", kollazsok
            ),
        ), (
            "az idegen program által írt kollázs a tízmásodperces körben "
            "NEM jelent meg — a felhasználónak az ötperces rescanre kell "
            "várnia (a jegy pontosan ezt jelenti be)"
        )

    def test_a_film_mappa_is_bekerul(self, controller, library, qt_app, tmp_path):
        """A mechanizmus nem kollázs-specifikus: a Filmek mappa ugyanaz."""
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 2)
        filmek = library / "Picasa" / "Filmek"

        make_jpeg(filmek / "kockaqkep.jpg")

        assert _var(
            qt_app,
            lambda: "kockaqkep.jpg" in _indexelt_nevek(
                tmp_path / "index.db", filmek
            ),
        )


class TestANASTerheles:
    """A jegy kemény feltétele: ne terheljük feleslegesen a megosztást."""

    def test_a_projekt_mappak_koltsege_haromnal_kevesebb_muvelet(
        self, controller, library, qt_app, monkeypatch
    ):
        """Projekt-mappánként legfeljebb HÁROM pecsét-művelet körönként."""
        import os as os_modul

        # ⚠️ Előbb INDEXELTETNI kell a két mappát: a `stale_folders` a
        # tárolt pecsét nélküli mappát pecsét-művelet NÉLKÜL minősíti
        # elavultnak (szándékos rövidzár), tehát az üres állapotban a
        # költség-mérés nullát adna, és semmit nem bizonyítana.
        controller.selectFolder(str(library / "nyaralas"))
        make_jpeg(library / "Picasa" / "Kollázsok" / "k.jpg")
        make_jpeg(library / "Picasa" / "Filmek" / "f.jpg")
        assert _var(
            qt_app,
            lambda: not controller._stale_feed_folders(
                controller._projekt_kimeneti_mappak()
            ),
        ), "a két projekt-mappa nem konvergált indexelt állapotra"

        mappak = controller._projekt_kimeneti_mappak()
        assert len(mappak) == 2, (
            f"a két projekt-mappát kellene visszaadnia, ez jött: {mappak}"
        )

        hivasok = []
        eredeti = os_modul.stat

        def szamlalo(*args, **kwargs):
            hivasok.append(args[0] if args else None)
            return eredeti(*args, **kwargs)

        monkeypatch.setattr("picasapy.app.folder_freshness._stat", szamlalo)
        controller._stale_feed_folders(mappak)

        assert hivasok, (
            "egyetlen pecsét-művelet sem futott — a mérés így semmit nem "
            "bizonyít (megkerüli valami a `_stat` fogantyút?)"
        )
        assert len(hivasok) <= 3 * len(mappak), (
            f"{len(hivasok)} művelet {len(mappak)} mappára — a pecsét "
            "keretét (mappánként három) túllépi"
        )

    def test_a_gyokeren_kivuli_celmappa_kimarad(
        self, controller, library, qt_app, tmp_path
    ):
        """Ami a figyelt gyökéren KÍVÜL van, arra ne is nézzünk rá.

        A `stale_folders` a tárolt pecsét nélküli mappát elavultnak
        minősíti, a `_on_folders_dirty` viszont a gyökéren kívülit
        kihagyja — a kettő együtt azt adná, hogy minden körben elindul egy
        szinkron-szál, ami semmit nem tesz. Ezért a szűrés ITT történik."""
        from picasapy.app import collage_prefs

        kulso = tmp_path / "kulso-kollazsok"
        kulso.mkdir()
        controller._get_settings().setValue(collage_prefs.OUTPUT_DIR_KEY, str(kulso))
        controller._projekt_kimenet_cache = None

        assert str(kulso) not in controller._projekt_kimeneti_mappak()

    def test_a_nem_letezo_celmappa_kimarad(self, controller, library, tmp_path):
        """A még LÉTRE SEM HOZOTT célmappa se kerüljön a körbe."""
        from picasapy.app import collage_prefs

        nincs = library / "Picasa" / "MegNincsMeg"
        controller._get_settings().setValue(collage_prefs.OUTPUT_DIR_KEY, str(nincs))
        controller._projekt_kimenet_cache = None

        assert str(nincs) not in controller._projekt_kimeneti_mappak()


class TestMindenKorbenSorraKerul:
    """A projekt-mappák NEM a körbeforgó kurzoron múlnak.

    A feed adagja `SWEEP_FOLDERS_PER_TICK` mappát visz körönként, tehát egy
    adott mappa `ceil(N/8)` körönként kerül sorra. A projekt-mappáknak
    ehelyett MINDEN körben benne kell lenniük — a kollázs megjelenése nem
    függhet attól, hány mappát mutat épp a rács."""

    def test_a_kollazs_mappa_harom_egymast_koveto_korben_is_benne_van(
        self, controller, library, qt_app, monkeypatch
    ):
        controller.selectFolder(str(library / "nyaralas"))
        assert _var(qt_app, lambda: controller.photos.rowCount() == 2)
        kollazsok = str(library / "Picasa" / "Kollázsok")

        adagok: list[tuple[str, ...]] = []
        monkeypatch.setattr(
            controller,
            "_stale_feed_folders",
            lambda batch: (adagok.append(tuple(batch)), ())[1],
        )
        for _ in range(3):
            controller._sweep_running = False
            controller._poll_current_folder()
            assert _var(qt_app, lambda: len(adagok) > 0 and not controller._sweep_running)

        assert len(adagok) == 3, f"három körnek kellett volna lefutnia: {adagok}"
        assert all(kollazsok in adag for adag in adagok), (
            f"a Kollázsok mappa nem volt benne minden körben: {adagok}"
        )

"""A FIGYELT GYÖKÉR áthelyezését is követni kell (#1542).

## Mit mértünk a javítás ELŐTT

Valódi `AppController`, produkciós időzítők (`FOLDER_POLL_MS`), kétszintű
könyvtár (`kepek/` + `kepek/album/` + `kepek/album/alalbum/`, három kép).
A felhasználó MAGÁT a figyelt gyökeret helyezi át (`kepek` → `mashol/kepek`):

| eset | `_roots` / `WatchedFolders.txt` | bal hasáb | index (mappa/fotó) |
|---|---|---|---|
| watcher KI, lekérdezés KI | a RÉGI helyre mutat | a RÉGI, már nem létező utak | 3 / 3, a régi utakon |
| watcher KI, lekérdezés **BE** | a RÉGI helyre mutat | **üres** | **0 / 0** |
| watcher **BE**, lekérdezés **BE** | a RÉGI helyre mutat | **üres** | **0 / 0** |

Ugyanez a javítás UTÁN, mindhárom beállításban azonosan: a `_roots` és a
`WatchedFolders.txt` az ÚJ helyre mutat, a bal hasáb az új utakat mutatja, az
index 3 mappa / 3 fotó az új utakon — az új hely **0,03–0,05 s** alatt jelenik
meg (figyelő és lekérdezés nélkül is, mert a `folderMoved` fogyasztója hozza).

⚠️ A jegy leírása szerint „nem vész el index" — a MÉRÉS EZT MEGCÁFOLTA. A
#1538 gyökér-védelme csak a saját ágát (`resyncMovedFolder`) fogja vissza;
a #1275 lekérdezés (és a #1435 sweep) FÜGGETLENÜL nézi a látott mappákat,
és mivel azok a lemezen tényleg eltűntek (`folder_looks_offline` → hamis,
mert a mappa nem elérhetetlen, hanem NINCS), a `sync_folder` kiveszi őket.
Két kör alatt így az EGÉSZ könyvtár kiürül az indexből — miközben a képek
sértetlenül ott vannak az új helyen. Ez a produkciós alapbeállítás, tehát
ez az, amit a felhasználó lát.

## Amit a javítás tesz

A `resyncMovedFolder` felismeri, hogy az áthelyezett mappa MAGA a figyelt
gyökér, és KÖVETI a mozgást: az index részfáját ÁTÍRJA az új útra (sort
nem töröl és nem hoz létre — `index.move_folder_tree`), a `_roots`-ot és a
`WatchedFolders.txt`-t az új helyre állítja, a figyelőt újraindítja.

## „Mi legyen, ha a régi hely helyén MÁS mappa áll ugyanazon a néven?"

NEM követjük a gyökeret. A gyökér az egész könyvtár horgonya: ha a régi
néven ÚJRA van egy létező mappa, akkor a figyelt út egy VALÓDI helyet
nevez meg — átállítani annyi volna, mint némán abbahagyni egy létező mappa
figyelését, ráadásul a régi mappa indexsorait egy MÁSIK fizikai mappára
akasztani (útvonal szerint a kettő megkülönböztethetetlen). Ilyenkor
inkább nem írunk: a `_roots` és a `WatchedFolders.txt` érintetlen marad, az
index átírása kimarad, és marad a #1538 védelme (a régi oldal takarítása
kimarad) — csak naplózunk.
"""

from __future__ import annotations

import time
from pathlib import Path

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


def _mappa_utak(ctl) -> set[str]:
    """A BAL HASÁB mappái — a modellből, ahogy a felület látja."""
    from picasapy.app.models import FolderListModel

    model = ctl.folders
    return {
        model.data(model.index(sor, 0), FolderListModel.PathRole)
        for sor in range(model.rowCount())
        if model.data(model.index(sor, 0), FolderListModel.KindRole) == "folder"
    }


def _index_allapot(db) -> tuple[tuple[str, ...], int]:
    """(mappa-útvonalak, fotók száma) — az indexből közvetlenül."""
    from picasapy.index import open_index

    with open_index(db) as conn:
        mappak = tuple(
            sor["path"]
            for sor in conn.execute("SELECT path FROM folders ORDER BY path")
        )
        fotok = conn.execute("SELECT count(*) AS n FROM photos").fetchone()["n"]
    return mappak, fotok


def _konyvtarat_epit(tmp_path):
    """Kétszintű könyvtár három képpel + a figyelt mappák fájlja."""
    from picasapy.index import open_index, sync_tree
    from picasapy.scanner import write_watched_folders

    library = tmp_path / "kepek"
    (library / "album" / "alalbum").mkdir(parents=True)
    (tmp_path / "mashol").mkdir()
    make_jpeg(library / "IMG_GYOKER.jpg")
    make_jpeg(library / "album" / "IMG_0001.jpg")
    make_jpeg(library / "album" / "alalbum" / "SUB_0001.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    # a valódi telepítésen a fájl LÉTEZIK — enélkül a teszt nem látná, hogy
    # a horgony elavult-e
    write_watched_folders(tmp_path / "WatchedFolders.txt", (str(library),))
    return library


def _vezerlot_epit(qt_app, tmp_path, library, *, watcher: bool, lekerdezes: bool):
    from PySide6.QtCore import QSettings

    from picasapy.app import application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.fileops_controller import FileOpsController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

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
    # #1457: a nem kért figyelőt/időzítőt AZONNAL leállítjuk, még az első
    # várakozás ELŐTT. Korábban a sorrend fordított volt, és a CI-n
    # háromszor omlott össze itt a folyamat (`exit -11`) — a
    # `faulthandler`-verem szerint épp ebben a `_var`-ciklusban, miközben
    # KÉT `watchdog`-szál (`dispatch_events`, `queue_events`) futott. A
    # figyelő tehát eseményeket küldött a Qt-objektumgráfba, amíg a
    # `processEvents` pörgött. A teszt amúgy sem kéri a figyelőt
    # (`watcher=False`): ez csak azt a néhány tized másodpercet szünteti
    # meg, amíg fölöslegesen élt.
    if not watcher and ctl._watcher is not None:
        ctl._watcher.stop()
        ctl._watcher = None
    if not lekerdezes and ctl._folder_poll_timer is not None:
        ctl._folder_poll_timer.stop()
    _var(qt_app, lambda: not ctl._sync_running)
    fileops = FileOpsController()
    app_module.wire_fileops(fileops, ctl)
    return ctl, fileops


class TestAzIndexReszfaAtirasa:
    """`move_folder_tree` — a részfa útvonalainak ÁTÍRÁSA, törlés nélkül."""

    def test_atirja_a_reszfat_a_testverek_nelkul(self, tmp_path):
        """A testvér-előtag csapdája: a „…/kep" átírása nem foghatja meg a
        „…/kepek" alatti sorokat."""
        from picasapy.index import move_folder_tree, open_index, sync_tree

        gyoker = tmp_path / "gyoker"
        (gyoker / "kep" / "mely").mkdir(parents=True)
        (gyoker / "kepek").mkdir()
        make_jpeg(gyoker / "kep" / "A.jpg")
        make_jpeg(gyoker / "kep" / "mely" / "B.jpg")
        make_jpeg(gyoker / "kepek" / "C.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, gyoker)
            elotte = conn.execute("SELECT count(*) AS n FROM photos").fetchone()["n"]

            mozgatott = move_folder_tree(conn, gyoker / "kep", tmp_path / "uj")

            assert mozgatott == 2
            utak = tuple(
                sor["path"]
                for sor in conn.execute("SELECT path FROM folders ORDER BY path")
            )
            # a `gyoker` maga nem kap sort: közvetlenül nincs benne média
            assert utak == (
                str(gyoker / "kepek"),
                str(tmp_path / "uj"),
                str(tmp_path / "uj" / "mely"),
            )
            utana = conn.execute("SELECT count(*) AS n FROM photos").fetchone()["n"]
            assert utana == elotte, "az átírás fotósort veszített"

    def test_utkozesnel_nem_ir(self, tmp_path):
        """Ha az ÚJ út alatt már van indexsor, az átírás nem tippel: hibát
        jelez, és semmit nem módosít."""
        from picasapy.index import move_folder_tree, open_index, sync_tree

        gyoker = tmp_path / "gyoker"
        (gyoker / "regi").mkdir(parents=True)
        (gyoker / "uj").mkdir()
        make_jpeg(gyoker / "regi" / "A.jpg")
        make_jpeg(gyoker / "uj" / "B.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, gyoker)
            elotte = tuple(
                sor["path"] for sor in conn.execute("SELECT path FROM folders")
            )

            with pytest.raises(ValueError):
                move_folder_tree(conn, gyoker / "regi", gyoker / "uj")

            utana = tuple(
                sor["path"] for sor in conn.execute("SELECT path FROM folders")
            )
            assert utana == elotte


class TestAGyokerKovetese:
    """A figyelő és a #1275 lekérdezés is LE — így egyedül a `folderMoved`
    fogyasztója hozhatja rendbe az állapotot. Ez a foga."""

    @pytest.fixture
    def egyseg(self, qt_app, tmp_path):
        library = _konyvtarat_epit(tmp_path)
        ctl, fileops = _vezerlot_epit(
            qt_app, tmp_path, library, watcher=False, lekerdezes=False
        )
        yield ctl, fileops, library, tmp_path
        ctl.shutdown()
        assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"

    def test_a_roots_az_uj_helyre_mutat(self, egyseg, qt_app):
        ctl, fileops, library, tmp_path = egyseg
        uj = tmp_path / "mashol" / "kepek"

        fileops.moveFolder(str(library), str(tmp_path / "mashol"))

        assert list(ctl.watchedFolders) == [str(uj)], (
            "a figyelt gyökér az áthelyezés után is a RÉGI, már nem létező "
            "helyre mutat"
        )

    def test_a_watchedfolders_txt_az_uj_helyre_mutat(self, egyseg, qt_app):
        """A horgony a LEMEZEN is átíródik — enélkül a következő indítás
        ismét a régi helyet keresné."""
        ctl, fileops, library, tmp_path = egyseg
        uj = tmp_path / "mashol" / "kepek"

        fileops.moveFolder(str(library), str(tmp_path / "mashol"))

        sorok = (tmp_path / "WatchedFolders.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        assert sorok == [str(uj)], (
            "a WatchedFolders.txt a régi helyre mutat — újraindítás után a "
            "program nem találná meg a gyűjteményt"
        )

    def test_az_index_nem_veszit_sort(self, egyseg, qt_app):
        ctl, fileops, library, tmp_path = egyseg
        uj = tmp_path / "mashol" / "kepek"
        _mappak_elotte, fotok_elotte = _index_allapot(tmp_path / "index.db")
        kesz: list[int] = []
        ctl.syncFinished.connect(lambda: kesz.append(1))

        fileops.moveFolder(str(library), str(tmp_path / "mashol"))

        assert _var(qt_app, lambda: bool(kesz), 15.0), "nem futott célzott szinkron"
        _var(qt_app, lambda: False, 0.5)
        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert mappak == (
            str(uj),
            str(uj / "album"),
            str(uj / "album" / "alalbum"),
        )
        assert fotok == fotok_elotte == 3, "az index fotósort veszített"

    def test_a_bal_hasab_az_uj_helyet_mutatja(self, egyseg, qt_app):
        ctl, fileops, library, tmp_path = egyseg
        uj = tmp_path / "mashol" / "kepek"

        fileops.moveFolder(str(library), str(tmp_path / "mashol"))

        assert _var(
            qt_app,
            lambda: {str(uj), str(uj / "album"), str(uj / "album" / "alalbum")}
            <= _mappa_utak(ctl),
        ), "az áthelyezett gyökér nem jelent meg az új helyén a bal hasábban"
        assert not {p for p in _mappa_utak(ctl) if p.startswith(str(library))}, (
            "a régi, már nem létező utak ottmaradtak a bal hasábban"
        )

    def test_a_valasztott_mappa_is_atkerul(self, egyseg, qt_app):
        """A felhasználó épp a mozgatott mappát nézte: a rács ne ürüljön ki."""
        ctl, fileops, library, tmp_path = egyseg
        ctl.selectFolder(str(library / "album"))
        assert _var(
            qt_app,
            lambda: any(
                kep.folder_path == str(library / "album") for kep in ctl.photos.photos
            ),
        )
        uj_album = tmp_path / "mashol" / "kepek" / "album"

        fileops.moveFolder(str(library), str(tmp_path / "mashol"))

        assert _var(qt_app, lambda: ctl.currentFolder == str(uj_album)), (
            "a kiválasztott mappa a régi úton maradt — a rács üresen áll"
        )


class TestProdukciosIdozitokkel:
    """A MÉRT alapállapot őre: a #1275 lekérdezés és a figyelő MŰKÖDIK.

    A javítás előtt ez a beállítás ürítette ki az egész indexet (0 mappa,
    0 fotó) — ez a jegy legsúlyosabb következménye."""

    @pytest.fixture
    def egyseg(self, qt_app, tmp_path):
        library = _konyvtarat_epit(tmp_path)
        ctl, fileops = _vezerlot_epit(
            qt_app, tmp_path, library, watcher=True, lekerdezes=True
        )
        yield ctl, fileops, library, tmp_path
        ctl.shutdown()
        assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"

    def test_a_konyvtar_nem_urul_ki(self, egyseg, qt_app):
        ctl, fileops, library, tmp_path = egyseg
        uj = tmp_path / "mashol" / "kepek"
        ctl.selectFolder(str(library))

        fileops.moveFolder(str(library), str(tmp_path / "mashol"))

        # két teljes lekérdezési kör (2 × FOLDER_POLL_MS) + ráhagyás
        _var(qt_app, lambda: False, 25.0)
        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert fotok == 3, (
            f"a lekérdezési kör kiürítette az indexet (fotók: {fotok}) — a "
            f"felhasználó képei sértetlenül ott vannak {uj} alatt"
        )
        assert mappak == (
            str(uj),
            str(uj / "album"),
            str(uj / "album" / "alalbum"),
        )
        assert list(ctl.watchedFolders) == [str(uj)]


class TestHaMasMappaAllARegiHelyen:
    """Döntés: ilyenkor NEM követjük a gyökeret (ld. a modul-docstringet)."""

    @pytest.fixture
    def egyseg(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app import application as app_module
        from picasapy.app.controller import AppController
        from picasapy.app.fileops_controller import FileOpsController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        library = _konyvtarat_epit(tmp_path)
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
        if ctl._watcher is not None:
            ctl._watcher.stop()
            ctl._watcher = None
        if ctl._folder_poll_timer is not None:
            ctl._folder_poll_timer.stop()
        _var(qt_app, lambda: not ctl._sync_running)
        fileops = FileOpsController()
        # ⚠️ A SORREND a lényeg: ez a feliratkozó a `wire_fileops` ELŐTT
        # kötődik be, tehát ELŐBB fut — mire a vezérlő megkapja a jelzést, a
        # régi néven már áll egy másik mappa. Így a fájlkezelővel dolgozó
        # felhasználó esete a VALÓDI sloton át mérhető.
        fileops.folderMoved.connect(lambda regi, _uj: Path(regi).mkdir())
        app_module.wire_fileops(fileops, ctl)
        yield ctl, fileops, library, tmp_path
        ctl.shutdown()
        assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"

    def test_nem_irjuk_at_a_horgonyt(self, egyseg, qt_app):
        ctl, fileops, library, tmp_path = egyseg

        fileops.moveFolder(str(library), str(tmp_path / "mashol"))

        _var(qt_app, lambda: False, 1.0)
        assert list(ctl.watchedFolders) == [str(library)], (
            "a régi néven ÁLLÓ, létező mappa mellett is átírtuk a horgonyt"
        )
        sorok = (tmp_path / "WatchedFolders.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        assert sorok == [str(library)]

    def test_a_regi_oldal_indexsorai_megmaradnak(self, egyseg, qt_app):
        """A #1538 védelme: követés nélkül a régi oldal takarítása kimarad."""
        ctl, fileops, library, tmp_path = egyseg
        kesz: list[int] = []
        ctl.syncFinished.connect(lambda: kesz.append(1))

        fileops.moveFolder(str(library), str(tmp_path / "mashol"))

        assert _var(qt_app, lambda: bool(kesz), 15.0)
        _var(qt_app, lambda: False, 0.5)
        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert str(library / "album") in mappak, (
            "a könyvtár némán kiürült, pedig nem tudtuk követni a gyökeret"
        )
        assert fotok == 3

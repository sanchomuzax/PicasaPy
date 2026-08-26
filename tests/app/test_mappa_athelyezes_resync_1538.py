"""A MAPPA áthelyezése is indítson célzott resyncet — MINDKÉT végén (#1538).

## Mit mértünk, és miért lett ebből javítás

A `folderMoved` jelzésnek nulla fogyasztója volt (`dead_signals_baseline.txt`,
#1003). A mérés (valódi `AppController`, valódi időzítők, produkciós
`FOLDER_POLL_MS`, kétszintű mappa: `album/` + `album/alalbum/`):

| eset | ÚJ hely megjelenik | RÉGI hely eltűnik |
|---|---|---|
| watcher BE, lekérdezés BE | 1,10 s → **0,06 s** | 1,10 s → 0,06 s |
| watcher KI, lekérdezés BE | **nem 25 s alatt** → **0,05 s** | **4,70 s** → 0,10 s |
| watcher KI, lekérdezés KI | nem 25 s alatt → **0,06 s** | nem 25 s alatt → 0,06 s |
| kontroll: ugyanez EGY KÉPPEL (watcher és lekérdezés KI) | 0,11 s | 0,05 s |

(A nyíl előtt a javítás előtti, utána a javítás utáni mérés; az almappa
minden esetben a mappával együtt, ugyanabban a körben került a helyére.)

A második sor a lelet, és rosszabb, mint amit a #1522-nél láttunk: ott egy
ÚJ másolat maradt láthatatlan, itt a felhasználó MEGLÉVŐ képei tűnnek el a
könyvtárból. A #1275 lekérdezés ugyanis a KIVÁLASZTOTT (tehát a régi)
mappát nézi, észreveszi, hogy eltűnt, és kiszedi az indexből — az új helyet
viszont senki nem olvassa be. A mappa tartalma így az ötperces rescanig
sehol nincs meg. Ugyanez EGY KÉPPEL 0,11 s (a `photoMoved` célzott
resyncje, #15).

## A `.parent`-buktató

A `_watched_folder_of` a kapott út SZÜLŐJÉT adja vissza (fájlra van
szabva). Ha a `folderMoved`-et változtatás nélkül a `refresh()`-re kötnénk,
a `celszulo/album` helyett a `celszulo` mappát olvasnánk újra — az pedig
NEM-REKURZÍV (`sync_folder`), tehát az áthelyezett mappa sora létre sem
jönne. A `test_az_uj_hely_bekerul_az_indexbe` pontosan ezt a mutációt öli
meg.

## Miért kell a részfa, és miért nem `sync_tree`-vel

A `sync_folder` egyetlen mappát olvas: az almappák sorai a RÉGI út alatt
maradnának (nem létező fájlokra mutatva), az új út alattiak pedig létre sem
jönnének. A RÉGI oldalra a `sync_tree` NEM használható: eltűnt gyökérre az
üres scan-eredmény miatt a #132 védelme kihagyja a takarítást (nem tudja
megkülönböztetni a lecsatolt NAS-mounttól). Ezért mindkét oldal
mappánként, a `sync_folder` saját `folder_looks_offline` próbáján át megy —
így elérhetetlen mappa sora nem esik ki, csak a bizonyítottan eltűnté.
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


class TestAzIndexReszfaLekerdezes:
    """`folder_paths_under` — a régi oldal forrása (a lemezen már nincs meg).

    A testvér-előtag csapdája: a „…/kep" mappa NEM foghatja meg a
    „…/kepek" alatti sorokat, különben egy áthelyezés a szomszéd mappa
    sorait is kitakarítaná."""

    def test_a_reszfat_adja_a_testverek_nelkul(self, tmp_path):
        from picasapy.index import folder_paths_under, open_index, sync_tree

        gyoker = tmp_path / "kepek"
        (gyoker / "kep" / "mely").mkdir(parents=True)
        (gyoker / "kepek").mkdir()
        make_jpeg(gyoker / "kep" / "A.jpg")
        make_jpeg(gyoker / "kep" / "mely" / "B.jpg")
        make_jpeg(gyoker / "kepek" / "C.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, gyoker)

            assert folder_paths_under(conn, gyoker / "kep") == (
                str(gyoker / "kep"),
                str(gyoker / "kep" / "mely"),
            )


class TestABekotes:
    """A bekötés szintje: a VEZÉRLŐ slotját hívjuk, valódi mappákkal."""

    class _StubController:
        def __init__(self, roots):
            self.watchedFolders = list(roots)
            self.resynced = []
            self.athelyezve = []

        def resyncFolder(self, folder):
            self.resynced.append(folder)

        def resyncMovedFolder(self, regi, uj):
            self.athelyezve.append((regi, uj))

    @pytest.fixture
    def wired(self, qt_app, tmp_path):
        from picasapy.app import application
        from picasapy.app.fileops_controller import FileOpsController

        root = tmp_path / "kepek"
        (root / "album").mkdir(parents=True)
        (root / "celszulo").mkdir()
        make_jpeg(root / "album" / "IMG_0001.jpg")
        stub = self._StubController([str(root)])
        fileops = FileOpsController()
        application.wire_fileops(fileops, stub)
        return fileops, stub, root

    def test_a_moveFolder_mindket_veget_ujraolvastatja(self, wired):
        """A `moveFolder` slot — nem a jelzés kézi kibocsátása."""
        fileops, stub, root = wired

        fileops.moveFolder(str(root / "album"), str(root / "celszulo"))

        assert stub.athelyezve == [
            (str(root / "album"), str(root / "celszulo" / "album"))
        ], (
            "a mappa áthelyezése nem kért célzott újraolvasást — a tartalma "
            "az ötperces rescanig sehol nem látszik"
        )

    def test_a_sikertelen_athelyezes_nem_ker_resyncet(self, wired, tmp_path):
        """Nem létező célszülő: ne kérjünk fölösleges újraolvasást."""
        fileops, stub, root = wired
        hibak = []
        fileops.operationFailed.connect(lambda muvelet, ok: hibak.append(muvelet))

        fileops.moveFolder(str(root / "album"), str(tmp_path / "NINCS_ILYEN"))

        assert hibak == ["move_folder"]
        assert stub.athelyezve == []

    def test_a_jelzes_lokalis_utat_ad_url_bemenetre(self, wired):
        """A QML `FolderDialog` `file://` URL-t is adhat: a jelzésnek akkor
        is LOKÁLIS útvonalat kell adnia, különben a fogyasztó egy
        `file:///…` alakú „mappát" próbálna újraolvasni."""
        fileops, stub, root = wired

        fileops.moveFolder(
            (root / "album").as_uri(), (root / "celszulo").as_uri()
        )

        assert stub.athelyezve == [
            (str(root / "album"), str(root / "celszulo" / "album"))
        ]


class TestAzAthelyezettMappaAzUjHelyenLatszik:
    """A jegy tényleges helyzete, végponttól végpontig.

    A figyelő ÉS a #1275 lekérdezés is le van állítva — így egyedül a
    célzott resync maradhat, ami a mappát az új helyen behozza. Ez a foga:
    a javítás nélkül a tartalom az ötperces rescanig sehol nem látszik.
    """

    @pytest.fixture
    def egyseg(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app import application as app_module
        from picasapy.app.controller import AppController
        from picasapy.app.fileops_controller import FileOpsController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        library = tmp_path / "kepek"
        (library / "album" / "alalbum").mkdir(parents=True)
        (library / "celszulo").mkdir()
        make_jpeg(library / "album" / "IMG_0001.jpg")
        make_jpeg(library / "album" / "alalbum" / "SUB_0001.jpg")
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
        fileops = FileOpsController()
        app_module.wire_fileops(fileops, ctl)
        yield ctl, fileops, library, tmp_path
        ctl.shutdown()
        assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"

    @staticmethod
    def _mappa_utak(ctl) -> set[str]:
        """A BAL HASÁB mappái — a modellből, ahogy a felület látja."""
        from picasapy.app.models import FolderListModel

        model = ctl.folders
        return {
            model.data(model.index(sor, 0), FolderListModel.PathRole)
            for sor in range(model.rowCount())
            if model.data(model.index(sor, 0), FolderListModel.KindRole) == "folder"
        }

    def test_az_uj_hely_bekerul_az_indexbe(self, egyseg, qt_app):
        """A `.parent`-buktató őre: a SZÜLŐ (`celszulo`) újraolvasása
        nem-rekurzív, tehát az `celszulo/album` sora attól nem jönne
        létre."""
        ctl, fileops, library, _ = egyseg
        ctl.selectFolder(str(library / "album"))
        assert _var(
            qt_app,
            lambda: any(
                kep.folder_path == str(library / "album")
                for kep in ctl.photos.photos
            ),
        )
        uj = library / "celszulo" / "album"

        fileops.moveFolder(str(library / "album"), str(library / "celszulo"))

        assert _var(qt_app, lambda: str(uj) in self._mappa_utak(ctl)), (
            "az áthelyezett mappa nem jelent meg az új helyén — figyelő és "
            "#1275 lekérdezés nélkül csak a célzott resync hozhatja be"
        )
        ctl.selectFolder(str(uj))
        assert _var(
            qt_app,
            lambda: [kep.name for kep in ctl.photos.photos if kep.folder_path == str(uj)]
            == ["IMG_0001.jpg"],
        ), "az áthelyezett mappa KÉPE nem jött be az új helyen"

    def test_az_alalbum_is_atkerul(self, egyseg, qt_app):
        """A `sync_folder` NEM rekurzív: az almappa csak akkor kerül át, ha
        a resync a részfát is bejárja."""
        ctl, fileops, library, _ = egyseg
        uj_alalbum = library / "celszulo" / "album" / "alalbum"

        fileops.moveFolder(str(library / "album"), str(library / "celszulo"))

        assert _var(qt_app, lambda: str(uj_alalbum) in self._mappa_utak(ctl)), (
            "az áthelyezett mappa ALMAPPÁJA nem került át — a képei a régi, "
            "már nem létező út alatt ragadtak"
        )

    def test_a_regi_hely_eltunik_az_almappaval_egyutt(self, egyseg, qt_app):
        ctl, fileops, library, _ = egyseg
        regi = library / "album"

        fileops.moveFolder(str(regi), str(library / "celszulo"))

        assert _var(
            qt_app,
            lambda: not {str(regi), str(regi / "alalbum")}
            & self._mappa_utak(ctl),
        ), "a régi hely (vagy az almappája) ottmaradt a bal hasábban"

    def test_a_figyelt_gyoker_athelyezese_nem_uriti_ki_az_indexet(
        self, egyseg, qt_app, tmp_path
    ):
        """Adatbiztonsági korlát: ha MAGÁT a figyelt gyökeret helyezik át,
        a régi oldal takarítása KIMARAD.

        A gyökér útvonala a figyelt mappák közt (és a
        `WatchedFolders.txt`-ben) ilyenkor a régi helyre mutat — a
        könyvtár teljes tartalmát azon az alapon törölni, hogy a program
        saját nyilvántartása szerint ott KELL lennie, kockázatosabb, mint
        egy ideig elavult sorokat mutatni. A gyökér követése külön jegy."""
        ctl, fileops, library, _ = egyseg
        kivul = tmp_path / "mashol"
        kivul.mkdir()
        # a modellt a `syncFinished` tölti újra: enélkül a „még nem
        # frissült" állapotot néznénk sikernek (foga vesztett teszt)
        kesz: list[int] = []
        ctl.syncFinished.connect(lambda: kesz.append(1))

        fileops.moveFolder(str(library), str(kivul))

        assert _var(qt_app, lambda: bool(kesz), 15.0), "nem futott célzott szinkron"
        _var(qt_app, lambda: False, 0.5)  # a modellfrissítés köre
        assert str(library / "album") in self._mappa_utak(ctl), (
            "a figyelt gyökér áthelyezésekor a könyvtár némán kiürült"
        )

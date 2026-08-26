"""Az ELTŰNT figyelt gyökér nem üríthető ki az indexből (#1560).

## Mit mértünk a javítás ELŐTT

Valódi `AppController`, produkciós `FOLDER_POLL_MS` (10 s), kétszintű
könyvtár (`kepek/` + `kepek/album/` + `kepek/album/alalbum/`, három kép).
A felhasználó a figyelt fő képmappát a programon KÍVÜL, fájlkezelővel
helyezi át (`shutil.move`) — tehát NINCS `folderMoved` jelzés, a #1542
követése el sem indul:

| eset | index (mappa/fotó) | mikor ürült ki | `_roots` / `WatchedFolders.txt` | bal hasáb |
|---|---|---|---|---|
| watcher KI, lekérdezés KI | 3 / 3 (a régi utakon) | — | a RÉGI helyre mutat | 3 sor |
| watcher KI, lekérdezés **BE** | **0 / 0** | **9,34 s** | a RÉGI helyre mutat | **üres** |
| watcher **BE**, lekérdezés **BE** | **0 / 0** | **9,19 s** | a RÉGI helyre mutat | **üres** |

A második és a harmadik sor a produkciós alapbeállítás: a felhasználó
teljes könyvtára eltűnik a nyilvántartásból ~9 másodperc alatt, egyetlen
lekérdezési körből. A képek a lemezen sértetlenek, de az újraépítés nagy
gyűjteménynél sokáig tart, és a stabil rekord-id-k elvesznek.

## Miért csúszik át a meglévő védelmeken

Az ötperces `rescan()`-t a **#132** megfogja (üres scan + nem üres index →
a takarítás kimarad). A tízmásodperces **#1275** lekérdezést nem: az a
LÁTOTT mappát (és a #1435 sweep a feedben látszó többit) nézi, azok a
lemezen tényleg NINCSENEK — nem elérhetetlenek —, ezért a
`folder_looks_offline` hamis, és a `sync_folder` kiveszi a sorokat.

## A javítás: a GYÖKÉR a bizonyíték

`index.watched_root_missing`: ha MAGA a figyelt gyökér tűnt el a lemezről,
a `sync_folder` alatta SEMMIT nem töröl. Az elhatárolás mércéje szándékosan
a gyökér, nem a mappa:

* **a gyökér megvan** → a tároló olvasható, tehát egy hiányzó ALMAPPA
  tényleg hiányzik: a takarítás futhat (a #1538/#1542 viselkedése
  változatlan);
* **a gyökér nincs meg** (`ENOENT`/`ENOTDIR`, vagy már nem könyvtár) → a
  horgony maga tűnt el; ilyenkor nem tudjuk, hogy a fa törlődött-e vagy
  csak elmozdult, tehát nem törlünk;
* **a gyökér elérhetetlen** (bármely más `OSError`: lecsatolt NAS, `ESTALE`,
  elvett jog) → NEM „eltűnt": ott a meglévő `folder_looks_offline` ág
  dolgozik tovább, változatlanul.

A védelem tehát szigorúan HOZZÁAD: egyetlen olyan ág sincs, ahol miatta
törlődne sor, ami eddig megmaradt volna.

## Amit a felhasználó lát — DÖNTÉS

**Nem néma várakozás, de nem is új felületi elem: a meglévő #459/5
„jelenleg nem elérhető" jelölést kapják a mappák.** A bal hasábon a sor
halvány és dőlt lesz (`FolderPane.qml`), a súgószöveg elmondja, hogy a
sorok az adatbázisban maradnak, és a mappára lépve a borostyán
tájékoztató sáv is kiírja ugyanezt (`folderUnavailable` → `Main.qml`).

Bizonyítékot kerestünk arra, mit tesz ilyenkor az eredeti Picasa: a
`stringres-en-hu.tsv` és a `.tre` szövegforrások **nem tartalmaznak**
egyetlen olyan üzenetet sem, amely egy figyelt mappa eltűnéséről szólna
(a `not found`/`no longer`/`missing`/`unavailable` találatok mind
importra, kollázsra, feltöltésre vagy online albumra vonatkoznak). Ez
tehát DÖNTÉS, nem másolás. Ami a binárisból mégis alátámasztja: a Picasa
figyelt mappát SOHA nem szüntet meg magától — az eltávolítás explicit és
megerősítést kér (`IDS_HOTFOLDER_CONFIRM`, „Remove from Picasa…"), tehát
a némán kiürülő könyvtár az eredetitől is idegen volna.

A `_roots`-hoz és a `WatchedFolders.txt`-hez SZÁNDÉKOSAN nem nyúlunk: az
új hely automatikus megkeresése nem ennek a jegynek a dolga (a #1542
`move_folder_tree`-je készen áll rá), itt a veszteség megelőzése a cél.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg

_ROOTKENT_FUT = hasattr(os, "geteuid") and os.geteuid() == 0


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


def _pumpal(qt_app, masodperc: float) -> None:
    """Valós idő pörgetése a Qt eseményhurokkal — a produkciós időzítők
    (`FOLDER_POLL_MS`) csak így sülnek el."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        time.sleep(0.02)


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
    write_watched_folders(tmp_path / "WatchedFolders.txt", (str(library),))
    return library


def _vezerlot_epit(qt_app, tmp_path, library, *, watcher: bool):
    """Valódi `AppController`, produkciós `FOLDER_POLL_MS`-sel."""
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
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
    _var(qt_app, lambda: not ctl._sync_running)
    if not watcher and ctl._watcher is not None:
        ctl._watcher.stop()
        ctl._watcher = None
    _var(qt_app, lambda: not ctl._sync_running)
    return ctl


class TestAGyokerEltunesenekFelismerese:
    """`watched_root_missing` — az „eltűnt" és az „elérhetetlen" elhatárolása.

    Ez a jegy egyetlen új döntési pontja; a többi ág erre épül."""

    def test_a_letezo_gyoker_nem_eltunt(self, tmp_path):
        from picasapy.index import watched_root_missing

        assert watched_root_missing(tmp_path) is False

    def test_a_nem_letezo_gyoker_eltunt(self, tmp_path):
        from picasapy.index import watched_root_missing

        assert watched_root_missing(tmp_path / "nincs-ilyen") is True

    def test_a_mappa_helyen_allo_fajl_is_eltunt_gyoker(self, tmp_path):
        """A horgony már nem könyvtár — figyelt gyökérként eltűntnek számít."""
        from picasapy.index import watched_root_missing

        fajl = tmp_path / "gyoker"
        fajl.write_text("nem mappa")
        assert watched_root_missing(fajl) is True

    def test_a_LECSATOLT_MOUNT_NEM_eltunt(self, tmp_path):
        """⚠️ A jegy határesete. A lecsatolt NAS csatolási pontja ÜRES
        KÖNYVTÁRKÉNT marad ott: LÉTEZIK, tehát nem „eltűnt" — az
        elérhetetlenségét a meglévő `folder_looks_offline` mondja ki."""
        from picasapy.index import folder_looks_offline, watched_root_missing

        mount = tmp_path / "mnt" / "photo"
        mount.mkdir(parents=True)
        assert watched_root_missing(mount) is False, (
            "a lecsatolt csatolási pontot eltűntnek minősítettük"
        )
        assert folder_looks_offline(mount) is True

    @pytest.mark.skipif(_ROOTKENT_FUT, reason="rootként a jogosultság nem korlátoz")
    def test_az_ELERHETETLEN_gyoker_NEM_eltunt(self, tmp_path):
        """⚠️ A másik elérhetetlen alak: a `stat` MAGA hasal el (`EACCES`,
        `ESTALE`, `ENOTCONN`). Ezt csak úgy lehet valósághűen előállítani,
        ha a gyökér SZÜLŐJE bejárhatatlan — a `stat` ugyanis a szülő
        bejárhatóságán múlik, nem a mappáén.

        Ez a teszt öli meg azt a mutációt, amelyik az `except OSError` ágon
        `True`-t adna: az „elérhetetlen"-t „eltűnt"-nek minősítve a program
        némán más ágon menne tovább, mint amit a #459/5 kimért."""
        from picasapy.index import watched_root_missing

        zart = tmp_path / "zart"
        gyoker = zart / "nas"
        gyoker.mkdir(parents=True)
        zart.chmod(0o000)
        try:
            with pytest.raises(PermissionError):
                os.stat(gyoker)  # a mérés alapja: a stat tényleg elhasal
            assert watched_root_missing(gyoker) is False, (
                "az elérhetetlen gyökeret eltűntnek minősítettük"
            )
        finally:
            zart.chmod(0o755)


class TestASyncFolderNemTorolEltuntGyokerAlatt:
    """A `sync_folder` takarítási ága — mappa-szinten, gyorsan."""

    @pytest.fixture
    def konyvtar(self, tmp_path):
        from picasapy.index import open_index, sync_tree

        library = tmp_path / "kepek"
        (library / "album").mkdir(parents=True)
        make_jpeg(library / "IMG_GYOKER.jpg")
        make_jpeg(library / "album" / "IMG_0001.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        return library

    def test_az_eltunt_gyoker_sorai_megmaradnak(self, tmp_path, konyvtar):
        from picasapy.index import open_index, sync_folder

        shutil.move(str(konyvtar), str(tmp_path / "mashol"))
        with open_index(tmp_path / "index.db") as conn:
            sync_folder(conn, konyvtar, konyvtar)

        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert len(mappak) == 2 and fotok == 2, (
            "az eltűnt figyelt gyökér sorait a célzott szinkron kivette az "
            f"indexből: {len(mappak)} mappa / {fotok} fotó"
        )

    def test_az_eltunt_gyoker_ALMAPPAJANAK_sorai_is_megmaradnak(
        self, tmp_path, konyvtar
    ):
        """A #1275 lekérdezés a LÁTOTT mappát nézi — tipikusan egy almappát."""
        from picasapy.index import open_index, sync_folder

        shutil.move(str(konyvtar), str(tmp_path / "mashol"))
        with open_index(tmp_path / "index.db") as conn:
            sync_folder(conn, konyvtar, konyvtar / "album")

        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert len(mappak) == 2 and fotok == 2, (
            "az eltűnt gyökér alatti almappa sorai eltűntek: "
            f"{len(mappak)} mappa / {fotok} fotó"
        )

    def test_a_megmaradt_sorok_offline_jelolest_kapnak(self, tmp_path, konyvtar):
        """DÖNTÉS: nem néma várakozás — a meglévő #459/5 jelölés (halvány,
        dőlt sor + súgószöveg + tájékoztató sáv) mondja el a helyzetet."""
        from picasapy.index import open_index, sync_folder

        shutil.move(str(konyvtar), str(tmp_path / "mashol"))
        with open_index(tmp_path / "index.db") as conn:
            sync_folder(conn, konyvtar, konyvtar / "album")
            offline = conn.execute(
                "SELECT offline FROM folders WHERE path = ?",
                (str(konyvtar / "album"),),
            ).fetchone()["offline"]

        assert offline == 1, (
            "az eltűnt gyökér alatti mappa a felületen semmivel nem jelzi, "
            "hogy nem érhető el"
        )

    def test_LETEZO_gyoker_alatt_a_takaritas_TOVABBRA_IS_fut(
        self, tmp_path, konyvtar
    ):
        """⚠️ Ez a védelem foga a másik irányba: a gyökér megléte bizonyítja,
        hogy a tároló olvasható, tehát a hiányzó ALMAPPA tényleg hiányzik.
        Ha ez az ág is elnémulna, a #1538/#1542 takarítása szűnne meg."""
        from picasapy.index import open_index, sync_folder

        shutil.rmtree(konyvtar / "album")
        with open_index(tmp_path / "index.db") as conn:
            sync_folder(conn, konyvtar, konyvtar / "album")

        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert mappak == (str(konyvtar),) and fotok == 1, (
            "a valóban törölt almappa sora bennragadt az indexben: "
            f"{mappak} / {fotok} fotó"
        )

    @pytest.mark.skipif(_ROOTKENT_FUT, reason="rootként a jogosultság nem korlátoz")
    def test_az_ELERHETETLEN_gyoker_alatt_is_megmaradnak_a_sorok(
        self, tmp_path, konyvtar
    ):
        """Az elvett jogú gyökér ága VÁLTOZATLAN (#459/5, #1538): a sorok
        megmaradnak, offline jelöléssel — ezt a jegy nem ronthatja el."""
        from picasapy.index import open_index, sync_folder

        konyvtar.chmod(0o000)
        try:
            with open_index(tmp_path / "index.db") as conn:
                sync_folder(conn, konyvtar, konyvtar / "album")
        finally:
            konyvtar.chmod(0o755)

        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert len(mappak) == 2 and fotok == 2, (
            "az elérhetetlen gyökér alatti mappa sorai eltűntek: "
            f"{len(mappak)} mappa / {fotok} fotó"
        )


class TestALecsatoltNasAlmappai:
    """⚠️ A #1560 mérése közben talált MÁSODIK veszteség — ugyanaz az ág.

    A lecsatolt NAS csatolási pontja ÜRES KÖNYVTÁRKÉNT marad ott, tehát a
    gyökér LÉTEZIK; az almappái viszont nincsenek meg. A `sync_folder` a
    mappa-szintű `folder_looks_offline`-t kérdezi, az az almappára
    `FileNotFoundError`-t kap → „nem offline, takarítható", és **kiveszi a
    sorokat**. Mérve a javítás előtt (csatolási pont = figyelt gyökér,
    egy almappa egy képpel):

    | lépés | index |
    |---|---|
    | kiindulás | `photo`, `photo/2019` — 2 fotó |
    | lecsatolás + a LÁTOTT almappa szinkronja | **csak `photo`** — 1 fotó |

    A gyökér sora megmaradt (üres mappa → offline), az almappáé és a képéé
    NEM. Egy nagy, NAS-on tartott gyűjteménynél tehát egyetlen lecsatolás
    elviszi a teljes nyilvántartást, a gyökér sorát leszámítva — ez a jegy
    kifejezett elvárása („egy lecsatolt NAS-nál is meg kell maradnia az
    indexnek").

    A javítás ugyanaz a horgony-elv: a takarítás bizonyítéka a GYÖKÉR. Ha a
    gyökér nem tudja bizonyítani, hogy a tároló ott van — mert eltűnt
    (#1560) VAGY mert elérhetetlennek látszik (#459/5, üres csatolási pont)
    —, alatta nem törlünk. Ugyanez a szabály él a `sync_tree`-ben (#132) is;
    a `sync_folder` eddig egyszerűen nem követte."""

    @pytest.fixture
    def csatolasi_pont(self, tmp_path):
        """A figyelt gyökér MAGA a csatolási pont — ez a NAS tipikus alakja."""
        from picasapy.index import open_index, sync_tree

        mount = tmp_path / "mnt" / "photo"
        (mount / "2019").mkdir(parents=True)
        make_jpeg(mount / "IMG_GYOKER.jpg")
        make_jpeg(mount / "2019" / "a.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, mount)
        return mount

    def _lecsatol(self, mount: Path) -> None:
        """A lecsatolás alakja: a csatolási pont ÜRES könyvtárként marad."""
        shutil.rmtree(mount)
        mount.mkdir()

    def test_a_lecsatolt_nas_almappaja_megmarad(self, tmp_path, csatolasi_pont):
        from picasapy.index import open_index, sync_folder

        self._lecsatol(csatolasi_pont)
        with open_index(tmp_path / "index.db") as conn:
            sync_folder(conn, csatolasi_pont, csatolasi_pont / "2019")

        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert len(mappak) == 2 and fotok == 2, (
            "a lecsatolt NAS almappájának sorai eltűntek az indexből: "
            f"{mappak} / {fotok} fotó"
        )

    def test_a_TELJESEN_kiurult_gyoker_alatt_sem_takaritunk(
        self, tmp_path, csatolasi_pont
    ):
        """A védelem ÁRA, kimondva. Ha a felhasználó a programon kívül
        tényleg kitörli a teljes könyvtárat, a gyökér üres lesz — az pedig
        megkülönböztethetetlen a lecsatolt mounttól, tehát a sorok
        bennmaradnak, amíg a gyökérnek ismét lesz tartalma.

        Ez nem új kompromisszum: a `sync_tree` (#132) MÁR ÍGY VISELKEDIK
        ugyanebben a helyzetben — mérve, a #1560 előtt is megtartotta a
        sorokat. A #1560 annyit tesz, hogy a célzott szinkron sem mond mást,
        mint az ötperces rescan. A végleges eltávolítás továbbra is
        explicit: Mappakezelő → „Eltávolítás a Picasából"."""
        from picasapy.index import open_index, sync_folder

        for elem in csatolasi_pont.iterdir():
            if elem.is_dir():
                shutil.rmtree(elem)
            else:
                elem.unlink()

        with open_index(tmp_path / "index.db") as conn:
            sync_folder(conn, csatolasi_pont, csatolasi_pont / "2019")

        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert len(mappak) == 2 and fotok == 2, (
            f"a kiürült gyökér alatt takarítottunk: {mappak} / {fotok} fotó"
        )

    def test_a_visszateres_utan_a_takaritas_ismet_fut(self, tmp_path, csatolasi_pont):
        """⚠️ A védelem foga: a mount VISSZATÉRÉSE után a valóban törölt
        almappa sora ismét kikerül — a védelem nem fagyasztja be az indexet
        örökre."""
        from picasapy.index import open_index, sync_folder

        shutil.rmtree(csatolasi_pont / "2019")  # a mount megvan, a mappa nincs

        with open_index(tmp_path / "index.db") as conn:
            sync_folder(conn, csatolasi_pont, csatolasi_pont / "2019")

        mappak, fotok = _index_allapot(tmp_path / "index.db")
        assert mappak == (str(csatolasi_pont),) and fotok == 1, (
            f"a visszatért mounton a takarítás nem futott: {mappak} / {fotok} fotó"
        )


class TestAFajlkezelovelAthelyezettGyoker:
    """A jegy végponti mérése: valódi vezérlő, produkciós `FOLDER_POLL_MS`.

    Az áthelyezés `shutil.move`-val megy — a fájlkezelő sem küld
    `folderMoved` jelzést, tehát a #1542 követése el sem indul. A mérés
    szerint a javítás nélkül az index 9,2–9,3 s alatt kiürült, ezért a
    tesztek 15 s valós időt pörgetnek: két lekérdezési kör bőven belefér."""

    def _mero(self, qt_app, tmp_path, *, watcher: bool):
        library = _konyvtarat_epit(tmp_path)
        ctl = _vezerlot_epit(qt_app, tmp_path, library, watcher=watcher)
        try:
            ctl.selectFolder(str(library / "album"))
            _var(qt_app, lambda: not ctl._sync_running)
            elotte = _index_allapot(tmp_path / "index.db")
            assert elotte == (
                (
                    str(library),
                    str(library / "album"),
                    str(library / "album" / "alalbum"),
                ),
                3,
            ), f"a kiindulás nem 3 mappa / 3 fotó: {elotte}"

            # a felhasználó FÁJLKEZELŐVEL helyezi át — nincs `folderMoved`
            shutil.move(str(library), str(tmp_path / "mashol" / "kepek"))
            _pumpal(qt_app, 15.0)
            _var(qt_app, lambda: not ctl._dirty_running, 10.0)

            return ctl, library, _index_allapot(tmp_path / "index.db")
        finally:
            ctl.shutdown()
            assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"

    def test_az_index_nem_urul_ki_figyelovel(self, qt_app, tmp_path):
        _ctl, library, (mappak, fotok) = self._mero(qt_app, tmp_path, watcher=True)

        assert (mappak, fotok) == (
            (
                str(library),
                str(library / "album"),
                str(library / "album" / "alalbum"),
            ),
            3,
        ), (
            "a fájlkezelővel áthelyezett figyelt gyökér kiürítette az "
            f"indexet: {len(mappak)} mappa / {fotok} fotó"
        )

    def test_az_index_nem_urul_ki_figyelo_nelkul(self, qt_app, tmp_path):
        """Figyelő nélkül egyedül a #1275 lekérdezés dolgozik — a mérés
        szerint ez volt az, amelyik kiürítette az indexet."""
        _ctl, library, (mappak, fotok) = self._mero(qt_app, tmp_path, watcher=False)

        assert len(mappak) == 3 and fotok == 3, (
            "a #1275 lekérdezés kiürítette az indexet: "
            f"{len(mappak)} mappa / {fotok} fotó"
        )

    def test_a_bal_hasab_es_a_horgony_megmarad(self, qt_app, tmp_path):
        """A felhasználó felé: a bal hasáb nem ürül ki, és a figyelt mappák
        fájlja sem lesz üres vagy hiányos (a horgony átállítása — az új hely
        megkeresése — SZÁNDÉKOSAN nem ennek a jegynek a dolga)."""
        ctl, library, _allapot = self._mero(qt_app, tmp_path, watcher=True)

        assert len(_mappa_utak(ctl)) == 3, (
            f"a bal hasáb kiürült: {sorted(_mappa_utak(ctl))}"
        )
        assert list(ctl.watchedFolders) == [str(library)]
        assert (tmp_path / "WatchedFolders.txt").read_text().split() == [str(library)]

    def test_a_mappak_offline_jelolest_kapnak(self, qt_app, tmp_path):
        """DÖNTÉS (ld. a modul docstringjét): a felhasználó nem néma
        várakozást kap — a sorok a meglévő #459/5 jelölést viselik."""
        _ctl, library, _allapot = self._mero(qt_app, tmp_path, watcher=True)

        from picasapy.index import open_index

        with open_index(Path(tmp_path) / "index.db") as conn:
            offline = {
                sor["path"]
                for sor in conn.execute("SELECT path FROM folders WHERE offline = 1")
            }
        assert str(library / "album") in offline, (
            f'a látott mappa nem kapott „nem elérhető” jelölést: {offline}'
        )

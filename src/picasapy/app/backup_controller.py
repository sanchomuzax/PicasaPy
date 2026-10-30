"""A mentés-készletek felületi hídja (#440).

A magot a `picasapy.backup` és a `picasapy.index.backup_sets` adja; ez a
modul köti a QML-hez: készlet-lista, létrehozás/módosítás/törlés, a
következő futás TERVE (darab + méret), és a futtatás.

## Miért van külön „terv" lépés

Az eredeti a futtatás előtt megmutatja, mennyi fájl megy át, és hány
maradt ki, mert már el van mentve (*„Picasa is now showing the files you
have not previously backed up"*). A terv semmit nem ír — a felület ebből
tud darabszámot és becsült méretet mutatni, mielőtt a felhasználó
elindítja a másolást.

## A jelöltek forrása

A figyelt gyökerek alatti fájlok. A szűrést a készlet fájlszűrője végzi
(`backup.szuro`), tehát itt a teljes fájllistát adjuk át — a nem-média
fájlt a szűrő úgyis kihagyja.

## Mappánkénti választás (#3594)

Az eredeti mentés-üzemmódja csak a még el nem mentett fájlokat mutatja,
mappánként pipával (`backuptext2`, `backuptext3`). A `mentetlenMappak` ezt
a nézetet adja, a `terv` és a két futtatás pedig a bepipált mappák
listáját is elfogadja. Lista nélkül minden mappa megy (a régi út), üres
listával semmi.

A lista HÁTTÉRSZÁLON készül (`mentetlenMappakLekerese` →
`mentetlenMappakKeszek`): a gyökerek bejárása, a fájlonkénti `stat()` és a
fényképezőgép-szűrő EXIF-olvasása nagy gyűjteménynél percekig tart, és a
GUI-szálon megfagyasztaná az ablakot — a #3009 ugyanezt szüntette meg a
futásnál. Minden lekérdezés sorszámot kap; csak a legutóbbi válasza megy
ki, tehát egy lassú, régebbi válasz nem írja felül az újabbat.
"""

# ruff: noqa: F401 -- a régi importútvonal nyilvános neveit exportálja.
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, Signal, Slot

from picasapy.backup import futtasd, mappankent, tervezd_meg, visszaallit
from picasapy.backup.lemezkep import LemezkepTetel, lemezkepekbe
from picasapy.burn import CD, DVD, hasznalhato_kapacitas, lemezek_szama
from picasapy.index import open_index
from picasapy.paths import flat_key, normalize_path
from .worker_thread import BackgroundWorkerMixin
from picasapy.index.backup_sets import (
    SZUROK,
    TIPUS_CD_DVD,
    TIPUS_LEMEZ,
    TIPUSOK,
    jegyezd_fel_a_futast,
    jegyezd_fel_az_elmentettet,
    keszlet_letrehozasa,
    keszlet_modositasa,
    keszlet_torlese,
    keszletek,
)
from .backup_controller_sets import _BackupControllerSetsMixin
from .backup_controller_runs import _BackupControllerRunsMixin

_log = logging.getLogger(__name__)

#: #2074: a névleges lemezek szektorszáma. A 700 MB-os CD 360 000, a
#: 4,7 GB-os egyrétegű DVD 2 295 104 szektor — ezekből a MÉRT képlet adja
#: a ténylegesen használható méretet.
_CD_SZEKTOR = 360_000
_DVD_SZEKTOR = 2_295_104

#: #3594: mappánként legfeljebb ennyi fájlnév megy a felületre — a sor úgyis
#: levágja, a darabszám pedig külön mező. Egy ezerfájlos mappa teljes
#: névlistája csak a QML-átadást terhelné.
_FAJLNEV_KORLAT = 20


def _kepek_mappaja() -> str:
    """A felhasználó Képek mappája — MODULSZINTŰ fogantyú: a teszt ezt
    cseréli, hogy a lemezkép ne a fejlesztő valódi Képek mappájába
    kerüljön. Üres rendszerválasznál a saját mappa (relatív út nem lehet)."""
    return (
        QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        or str(Path.home())
    )


class BackupController(
    _BackupControllerSetsMixin,
    _BackupControllerRunsMixin,
    BackgroundWorkerMixin,
    QObject,
):
    """Az `Eszközök ▸ Képek biztonsági mentése…` háttér-hídja."""

    #: emberi nyelvű hibaszöveg a felületnek (hibasáv / párbeszéd)
    hibatJelez = Signal(str)
    #: a készlet-lista megváltozott (létrehozás, módosítás, törlés, futás)
    keszletekValtoztak = Signal()
    #: (átmásolt darab, átmásolt bájt)
    futasKesz = Signal(int, int)
    #: #2074: (hány lemezkép, hány fájl) — a lemezkép-kimenet vége
    lemezkepekKeszek = Signal(int, int)
    #: #4614: (visszaállított fájlok, már létező fájlok)
    visszaallitasKesz = Signal(int, int)
    #: #3009: (hányadik, hány) — az eredeti is végig beszél
    #: („Copying (%d/%d) files"). A felület ebből tud haladást mutatni.
    haladas = Signal(int, int)
    #: #3009: elindult a másolás (a felület ilyenkor mutatja a
    #: haladás-sávot és a Megszakítás gombot)
    futasIndult = Signal(int)
    #: #3594: (lekérdezés sorszáma, készlet-azonosító, mappa-sorok) — a
    #: `mentetlenMappakLekerese` háttérben számolt eredménye
    mentetlenMappakKeszek = Signal(int, int, "QVariantList")
    #: #3645: (lekérdezés sorszáma, készlet-azonosító, terv, kért média) — a
    #: `tervezdHattereben` háttérben számolt eredménye
    tervKeszult = Signal(int, int, "QVariantMap", str)

    def __init__(self, db_path: Path, gyokerek: tuple[str, ...]) -> None:
        super().__init__()
        self._db_path = Path(db_path)
        self._gyokerek = tuple(str(gy) for gy in gyokerek)
        #: #3009: a megszakítás jelzője. Szálak között olvassuk/írjuk,
        #: ezért `Event` — a `bool` mezőre nincs memória-garancia.
        self._megszakitas = threading.Event()
        #: #3594: a legutóbbi mappa-lekérdezés sorszáma. A GUI-szál írja, a
        #: háttérszál olvassa; a zár a „megnézem, aztán küldöm" párt védi.
        #: `RLock`: egy közvetlenül bekötött fogadó a jelzésből újra kérhet.
        self._mappa_keres = 0
        self._mappa_zar = threading.RLock()
        #: #3645: a legutóbbi terv-lekérdezés sorszáma — ugyanaz a minta,
        #: mint a mappa-lekérdezésnél, külön számlálóval.
        self._terv_keres = 0
        self._terv_zar = threading.RLock()

    @Slot(result=str)
    def lemezkepAlapHely(self) -> str:  # noqa: N802 — QML-slot-stílus
        """#3593: a CD/DVD-típusú készlet lemezképeinek helye.

        Az eredetiben ennek a típusnak nincs célmappája (a lemezre ír, a
        „Choose…" csak a lemez-lemez típusnál él). Nálunk a lemezkép fájl,
        tehát kell egy hely: a Képek mappában a honosított
        `il_BurnPanel::DefBkFolder` („Picasa biztonsági másolat") alatti
        `il_BurnPanel::ISOFolder` („ISO-k")."""
        return str(
            Path(_kepek_mappaja()) / self.tr("Picasa Backup") / self.tr("ISOs")
        )

    def _tervezd(self, conn, keszlet, mappak):
        """A készlet terve a figyelt gyökerekből, a pipákra szűkítve.

        #3776 [KRITIKUS javítás]: a `gyokerek` itt FELOLDVA megy tovább —
        a `_jeloltek()` a fájlokat `normalize_path`-dal feloldott gyökerek
        alól gyűjti (symlink, Windows 8.3-rövidnév, eltérő betűzés
        feloldva), tehát a `_relativ_ut` (`backup/futtatas.py`) csak akkor
        találja meg az egyező előtagot, ha a hozzá kapott gyökér UGYANÚGY
        fel van oldva. Feloldatlan gyökérnél a `relative_to` mindig
        `ValueError`-t dob, és a terv a `Path(fajl.parent.name) / fajl.name`
        eséstartalékra esik — ez ELVESZTI a mappaszerkezetet, és két,
        eltérő gyökér alatti, azonos nevű almappa (pl. `2023/nyaralas/` és
        `2024/nyaralas/`) fájljai UGYANARRA a célútra másolódnak, egymást
        felülírva."""
        return tervezd_meg(
            conn, keszlet, self._jeloltek(),
            gyokerek=tuple(normalize_path(gy) for gy in self._gyokerek),
            mappak=None if mappak is None else [str(m) for m in mappak],
        )


    def _lemezkepek_hattereben(
        self, keszlet_id: int, media: str, mappak=None
    ) -> None:
        """A lemezkép-írás törzse — háttérszálon fut.

        ⚠️ A nyilvántartás (a mentési készlet `BKTag`-je) a képek kiírása
        UTÁN frissül, ahogy az eredetiben is: a `WriteProgress::13`
        („Mentési készlet frissítése") az írás VÉGÉN fut. Ha a képírás
        elszáll, a következő futás ugyanazt viszi újra — nem hazudunk kész
        mentést.
        """
        szektor = _DVD_SZEKTOR if media == DVD else _CD_SZEKTOR
        try:
            with open_index(self._db_path) as conn:
                keszlet = self._keszlet(conn, keszlet_id)
                if keszlet is None:
                    self.hibatJelez.emit(self.tr("There is no such backup set."))
                    return
                terv = self._tervezd(conn, keszlet, mappak)
                if not terv.fajlok:
                    self.lemezkepekKeszek.emit(0, 0)
                    return
                self.futasIndult.emit(len(terv.fajlok))
                eredmeny = lemezkepekbe(
                    (
                        LemezkepTetel(
                            relativ=tetel.relativ,
                            forras=tetel.forras,
                            meret=tetel.meret,
                        )
                        for tetel in terv.fajlok
                    ),
                    Path(keszlet.cel),
                    media=media,
                    szektorszam=szektor,
                    haladas=lambda par: self.haladas.emit(par[0], par[1]),
                )
                # csak a kiírás UTÁN — `WriteProgress::13`
                jegyezd_fel_az_elmentettet(
                    conn,
                    keszlet.id,
                    [
                        (str(tetel.forras), tetel.meret, tetel.mtime_ns)
                        for tetel in terv.fajlok
                    ],
                )
                jegyezd_fel_a_futast(
                    conn,
                    keszlet.id,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                )
                conn.commit()
        except OSError as hiba:
            _log.warning("a lemezkép-írás elszállt: %s", hiba)
            self.hibatJelez.emit(
                self.tr("The backup did not finish: %1").replace("%1", str(hiba))
            )
            return
        if eredmeny.tulcsordulo:
            self.hibatJelez.emit(
                self.tr("%1 file(s) do not fit on a single disc.").replace(
                    "%1", str(len(eredmeny.tulcsordulo))
                )
            )
        self.keszletekValtoztak.emit()
        self.lemezkepekKeszek.emit(len(eredmeny.kepek), sum(eredmeny.darabok))

    def _futtatas_hattereben(self, keszlet_id: int, mappak=None) -> None:
        """A másolás törzse — háttérszálon fut."""
        try:
            with open_index(self._db_path) as conn:
                keszlet = self._keszlet(conn, keszlet_id)
                if keszlet is None:
                    self.hibatJelez.emit(self.tr("There is no such backup set."))
                    return
                terv = self._tervezd(conn, keszlet, mappak)
                self.futasIndult.emit(len(terv.fajlok))
                masoltak = futtasd(
                    conn,
                    keszlet,
                    terv,
                    haladas=lambda par: self.haladas.emit(par[0], par[1]),
                    megszakitva=self._megszakitas.is_set,
                )
                conn.commit()
        except OSError as hiba:
            _log.warning("a mentés elszállt: %s", hiba)
            self.hibatJelez.emit(
                self.tr("The backup did not finish: %1").replace(
                    "%1", str(hiba)
                )
            )
            return
        bajtok = sum(
            tetel.meret
            for tetel in terv.fajlok
            if (Path(keszlet.cel) / tetel.relativ) in set(masoltak)
        )
        self.keszletekValtoztak.emit()
        self.futasKesz.emit(len(masoltak), bajtok)

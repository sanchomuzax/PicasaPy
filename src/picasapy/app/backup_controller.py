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
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, Signal, Slot

from picasapy.backup import futtasd, mappankent, tervezd_meg
from picasapy.backup.lemezkep import LemezkepTetel, lemezkepekbe
from picasapy.burn import CD, DVD, hasznalhato_kapacitas, lemezek_szama
from picasapy.index import open_index
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

_log = logging.getLogger(__name__)

#: #2074: a névleges lemezek szektorszáma. A 700 MB-os CD 360 000, a
#: 4,7 GB-os egyrétegű DVD 2 295 104 szektor — ezekből a MÉRT képlet adja
#: a ténylegesen használható méretet.
_CD_SZEKTOR = 360_000
_DVD_SZEKTOR = 2_295_104


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


class BackupController(BackgroundWorkerMixin, QObject):
    """Az `Eszközök ▸ Képek biztonsági mentése…` háttér-hídja."""

    #: emberi nyelvű hibaszöveg a felületnek (hibasáv / párbeszéd)
    hibatJelez = Signal(str)
    #: a készlet-lista megváltozott (létrehozás, módosítás, törlés, futás)
    keszletekValtoztak = Signal()
    #: (átmásolt darab, átmásolt bájt)
    futasKesz = Signal(int, int)
    #: #2074: (hány lemezkép, hány fájl) — a lemezkép-kimenet vége
    lemezkepekKeszek = Signal(int, int)
    #: #3009: (hányadik, hány) — az eredeti is végig beszél
    #: („Copying (%d/%d) files"). A felület ebből tud haladást mutatni.
    haladas = Signal(int, int)
    #: #3009: elindult a másolás (a felület ilyenkor mutatja a
    #: haladás-sávot és a Megszakítás gombot)
    futasIndult = Signal(int)

    def __init__(self, db_path: Path, gyokerek: tuple[str, ...]) -> None:
        super().__init__()
        self._db_path = Path(db_path)
        self._gyokerek = tuple(str(gy) for gy in gyokerek)
        #: #3009: a megszakítás jelzője. Szálak között olvassuk/írjuk,
        #: ezért `Event` — a `bool` mezőre nincs memória-garancia.
        self._megszakitas = threading.Event()

    # -- készletek --------------------------------------------------------

    @Slot(result="QVariantList")
    def keszletek(self) -> list[dict]:
        """A készletek QML-alakban, név szerint."""
        with open_index(self._db_path) as conn:
            return [
                {
                    "id": k.id,
                    "nev": k.nev,
                    "cel": k.cel,
                    "szuro": k.szuro,
                    "tipus": k.tipus,
                    "utolsoFutas": k.utolso_futas or "",
                }
                for k in keszletek(conn)
            ]

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

    @Slot(str, str, str, result=bool)
    @Slot(str, str, str, str, result=bool)
    def ujKeszlet(  # noqa: N802
        self, nev: str, cel: str, szuro: str, tipus: str = TIPUS_LEMEZ
    ) -> bool:
        """Új készlet; `False`, ha nem jött létre (a hibát jelezzük).

        #3593: a `tipus` a `newbackupset.fen` két rádiója; a CD/DVD-típus
        üres célnál a `lemezkepAlapHely`-re ír."""
        if not str(nev).strip():
            self.hibatJelez.emit(
                self.tr("Give the backup set a name.")
            )
            return False
        if tipus not in TIPUSOK:
            self.hibatJelez.emit(self.tr("Unknown backup type."))
            return False
        if tipus == TIPUS_CD_DVD:
            # a CD/DVD-típusnak nincs választható helye (a `.fen` szerint a
            # „Choose…" tiltott) — a felület az alaphelyet mutatja, tehát
            # az is kerül a készletbe, akármit hozott az űrlap
            cel = self.lemezkepAlapHely()
        if not str(cel).strip():
            self.hibatJelez.emit(
                self.tr("Choose where to save the backup.")
            )
            return False
        if szuro not in SZUROK:
            self.hibatJelez.emit(self.tr("Unknown file filter."))
            return False
        try:
            with open_index(self._db_path) as conn:
                keszlet_letrehozasa(conn, nev, cel, szuro, tipus=tipus)
                conn.commit()
        except Exception as hiba:  # noqa: BLE001 — a felületre megy
            # a leggyakoribb eset az ütköző név (egyedi kulcs)
            _log.warning("a mentés-készlet nem jött létre: %s", hiba)
            self.hibatJelez.emit(
                self.tr("A backup set with this name already exists.")
            )
            return False
        self.keszletekValtoztak.emit()
        return True

    @Slot(int, str, str, str, result=bool)
    @Slot(int, str, str, str, str, result=bool)
    def modositsdAKeszletet(  # noqa: N802 — QML-slot-stílus
        self, keszlet_id: int, nev: str, cel: str, szuro: str,
        tipus: str = "",
    ) -> bool:
        """Az „Edit Set" művelete — a nyilvántartás MEGMARAD, tehát a
        mentés nem kezdődik elölről. Üres `tipus` = nem változik (#3593)."""
        if tipus and tipus not in TIPUSOK:
            self.hibatJelez.emit(self.tr("Unknown backup type."))
            return False
        if tipus == TIPUS_CD_DVD:
            cel = self.lemezkepAlapHely()
        try:
            with open_index(self._db_path) as conn:
                keszlet_modositasa(
                    conn, int(keszlet_id), nev=nev or None,
                    cel=cel or None, szuro=szuro or None,
                    tipus=tipus or None,
                )
                conn.commit()
        except Exception as hiba:  # noqa: BLE001
            _log.warning("a mentés-készlet módosítása elszállt: %s", hiba)
            self.hibatJelez.emit(self.tr("The backup set could not be changed."))
            return False
        self.keszletekValtoztak.emit()
        return True

    @Slot(int)
    def torisdAKeszletet(self, keszlet_id: int) -> None:  # noqa: N802
        """A készlet ÉS a nyilvántartása törlése.

        ⚠️ Az eredeti megerősítést kér — az a párbeszéd dolga. Azért külön
        művelet, hogy a felület ne hívhassa mellékesen."""
        with open_index(self._db_path) as conn:
            keszlet_torlese(conn, int(keszlet_id))
            conn.commit()
        self.keszletekValtoztak.emit()

    # -- terv és futtatás -------------------------------------------------

    def _keszlet(self, conn, keszlet_id: int):
        for keszlet in keszletek(conn):
            if keszlet.id == int(keszlet_id):
                return keszlet
        return None

    def _tervezd(self, conn, keszlet, mappak):
        """A készlet terve a figyelt gyökerekből, a pipákra szűkítve."""
        return tervezd_meg(
            conn, keszlet, self._jeloltek(), gyokerek=self._gyokerek,
            mappak=None if mappak is None else [str(m) for m in mappak],
        )

    def _jeloltek(self) -> list[Path]:
        fajlok: list[Path] = []
        for gyoker in self._gyokerek:
            ut = Path(gyoker)
            if not ut.is_dir():
                continue
            fajlok.extend(sorted(p for p in ut.rglob("*") if p.is_file()))
        return fajlok

    @Slot(int, result="QVariantList")
    def mentetlenMappak(self, keszlet_id: int) -> list[dict]:  # noqa: N802
        """#3594: a készlet még el nem mentett fájljai, mappánként.

        `backuptext2`: „A Picasa most azokat a fájlokat jeleníti meg,
        amelyekről korábban nem készült biztonsági másolat." A teljesen
        elmentett mappa nem kerül a listába. ÍRÁS NÉLKÜL."""
        with open_index(self._db_path) as conn:
            keszlet = self._keszlet(conn, keszlet_id)
            if keszlet is None:
                return []
            terv = self._tervezd(conn, keszlet, None)
        return [
            {
                "mappa": str(mappa),
                "nev": mappa.name,
                "fajlok": [tetel.forras.name for tetel in tetelek],
                "darab": len(tetelek),
                "bajt": sum(tetel.meret for tetel in tetelek),
            }
            for mappa, tetelek in mappankent(terv).items()
        ]

    @Slot(int, result="QVariantMap")
    @Slot(int, "QVariantList", result="QVariantMap")
    def terv(self, keszlet_id: int, mappak=None) -> dict:
        """Mit vinne át a következő futás — ÍRÁS NÉLKÜL.

        #3594: a `mappak` a bepipált mappák; nélküle minden mappa."""
        with open_index(self._db_path) as conn:
            keszlet = self._keszlet(conn, keszlet_id)
            if keszlet is None:
                self.hibatJelez.emit(self.tr("There is no such backup set."))
                return {"darab": 0, "bajt": 0, "kihagyott": 0}
            terv = self._tervezd(conn, keszlet, mappak)
        #: #2074: hány lemezre férne — az eredeti is megmutatja
        #: („Est. %d CDs or %d DVDs"). A kapacitás a MÉRT képletből jön
        #: (`szektor × 2048 − tartalék`, `0x0066be90`); a szektorszámok a
        #: névleges 700 MB-os CD-é és 4,7 GB-os DVD-é.
        return {
            "darab": len(terv.fajlok),
            "bajt": terv.osszes_bajt,
            "kihagyott": terv.kihagyott,
            "cd": lemezek_szama(
                terv.osszes_bajt,
                hasznalhato_kapacitas(CD, szektorszam=_CD_SZEKTOR),
            ),
            "dvd": lemezek_szama(
                terv.osszes_bajt,
                hasznalhato_kapacitas(DVD, szektorszam=_DVD_SZEKTOR),
            ),
        }

    @staticmethod
    def _mappalista(mappak):
        """A QML-ből jött lista szálbiztos másolata (`None` = minden)."""
        return None if mappak is None else tuple(str(m) for m in mappak)

    @Slot(int)
    @Slot(int, "QVariantList")
    def futtasdMost(self, keszlet_id: int, mappak=None) -> None:  # noqa: N802
        """A készlet futtatása HÁTTÉRSZÁLON (#3009).

        A másolás a hívó szálon futott, tehát nagy gyűjteménynél az ablak a
        művelet idejére megállt. Az adatbázis-kapcsolat a szálon belül
        nyílik: az `sqlite3` objektumok nem adhatók át szálak között.

        #3594: a `mappak` a bepipált mappák; nélküle minden mappa."""
        self._megszakitas.clear()
        self._start_background(
            self._futtatas_hattereben,
            args=(int(keszlet_id), self._mappalista(mappak)),
            name="backup-run",
        )

    @Slot(int, str)
    @Slot(int, str, "QVariantList")
    def futtasdLemezkepbe(  # noqa: N802
        self, keszlet_id: int, media: str, mappak=None
    ) -> None:
        """A készlet mentése sorszámozott ISO-lemezképekbe (#2074).

        A tulajdonos 2026-09-18-án ezt az ágat kérte („a gyűjtemény mentése
        több lemezképre"). A kapacitás a MÉRT képletből jön; a `media` a
        felületen választott lemezfajta (`cd` vagy `dvd`).

        #3594: a `mappak` a bepipált mappák; nélküle minden mappa.
        """
        self._megszakitas.clear()
        self._start_background(
            self._lemezkepek_hattereben,
            args=(int(keszlet_id), str(media), self._mappalista(mappak)),
            name="backup-iso",
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

    @Slot()
    def szakitsdMeg(self) -> None:  # noqa: N802
        """A futó mentés megszakítása (#3009).

        A már átmásolt fájlok a nyilvántartásba kerülnek, tehát a következő
        futás pontosan a hiányzókat viszi — a megszakítás nem veszít el
        munkát, csak elhalasztja."""
        self._megszakitas.set()

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

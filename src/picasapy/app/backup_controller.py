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
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.backup import futtasd, tervezd_meg
from picasapy.index import open_index
from .worker_thread import BackgroundWorkerMixin
from picasapy.index.backup_sets import (
    SZUROK,
    keszlet_letrehozasa,
    keszlet_modositasa,
    keszlet_torlese,
    keszletek,
)

_log = logging.getLogger(__name__)


class BackupController(BackgroundWorkerMixin, QObject):
    """Az `Eszközök ▸ Képek biztonsági mentése…` háttér-hídja."""

    #: emberi nyelvű hibaszöveg a felületnek (hibasáv / párbeszéd)
    hibatJelez = Signal(str)
    #: a készlet-lista megváltozott (létrehozás, módosítás, törlés, futás)
    keszletekValtoztak = Signal()
    #: (átmásolt darab, átmásolt bájt)
    futasKesz = Signal(int, int)
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
                    "utolsoFutas": k.utolso_futas or "",
                }
                for k in keszletek(conn)
            ]

    @Slot(str, str, str, result=bool)
    def ujKeszlet(self, nev: str, cel: str, szuro: str) -> bool:  # noqa: N802
        """Új készlet; `False`, ha nem jött létre (a hibát jelezzük)."""
        if not str(nev).strip():
            self.hibatJelez.emit(
                self.tr("Give the backup set a name.")
            )
            return False
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
                keszlet_letrehozasa(conn, nev, cel, szuro)
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
    def modositsdAKeszletet(  # noqa: N802 — QML-slot-stílus
        self, keszlet_id: int, nev: str, cel: str, szuro: str
    ) -> bool:
        """Az „Edit Set" művelete — a nyilvántartás MEGMARAD, tehát a
        mentés nem kezdődik elölről."""
        try:
            with open_index(self._db_path) as conn:
                keszlet_modositasa(
                    conn, int(keszlet_id), nev=nev or None,
                    cel=cel or None, szuro=szuro or None,
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

    def _jeloltek(self) -> list[Path]:
        fajlok: list[Path] = []
        for gyoker in self._gyokerek:
            ut = Path(gyoker)
            if not ut.is_dir():
                continue
            fajlok.extend(sorted(p for p in ut.rglob("*") if p.is_file()))
        return fajlok

    @Slot(int, result="QVariantMap")
    def terv(self, keszlet_id: int) -> dict:
        """Mit vinne át a következő futás — ÍRÁS NÉLKÜL."""
        with open_index(self._db_path) as conn:
            keszlet = self._keszlet(conn, keszlet_id)
            if keszlet is None:
                self.hibatJelez.emit(self.tr("There is no such backup set."))
                return {"darab": 0, "bajt": 0, "kihagyott": 0}
            terv = tervezd_meg(
                conn, keszlet, self._jeloltek(), gyokerek=self._gyokerek
            )
        return {
            "darab": len(terv.fajlok),
            "bajt": terv.osszes_bajt,
            "kihagyott": terv.kihagyott,
        }

    @Slot(int)
    def futtasdMost(self, keszlet_id: int) -> None:  # noqa: N802
        """A készlet futtatása HÁTTÉRSZÁLON (#3009).

        A másolás a hívó szálon futott, tehát nagy gyűjteménynél az ablak a
        művelet idejére megállt. Az adatbázis-kapcsolat a szálon belül
        nyílik: az `sqlite3` objektumok nem adhatók át szálak között."""
        self._megszakitas.clear()
        self._start_background(
            self._futtatas_hattereben, args=(int(keszlet_id),),
            name="backup-run",
        )

    @Slot()
    def szakitsdMeg(self) -> None:  # noqa: N802
        """A futó mentés megszakítása (#3009).

        A már átmásolt fájlok a nyilvántartásba kerülnek, tehát a következő
        futás pontosan a hiányzókat viszi — a megszakítás nem veszít el
        munkát, csak elhalasztja."""
        self._megszakitas.set()

    def _futtatas_hattereben(self, keszlet_id: int) -> None:
        """A másolás törzse — háttérszálon fut."""
        try:
            with open_index(self._db_path) as conn:
                keszlet = self._keszlet(conn, keszlet_id)
                if keszlet is None:
                    self.hibatJelez.emit(self.tr("There is no such backup set."))
                    return
                terv = tervezd_meg(
                    conn, keszlet, self._jeloltek(), gyokerek=self._gyokerek
                )
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

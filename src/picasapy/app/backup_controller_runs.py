"""A biztonsági mentés tervezési, futtatási és visszaállítási mixinje (#6271)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.burn import CD, DVD, hasznalhato_kapacitas, lemezek_szama
from picasapy.index import open_index
from picasapy.backup import visszaallit

_log = logging.getLogger("picasapy.app.backup_controller")
_CD_SZEKTOR = 360_000
_DVD_SZEKTOR = 2_295_104


# `pyside6-lupdate` uses the enclosing class as the `self.tr` context.
# Keep that source name while exposing the runtime class only as a mixin.
class BackupController:
    """Tervkészítés, mentésindítás, megszakítás és visszaállítás."""

    def terv(self, keszlet_id: int, mappak=None) -> dict:
        """Mit vinne át a következő futás — ÍRÁS NÉLKÜL.

        #3594: a `mappak` a bepipált mappák; nélküle minden mappa.

        ⚠️ #3645 átnézés [KÖZEPES]: eltűnt készletnél a `hiba` jelzőt is
        beállítja — a `_terv_hattereben` ezt adja tovább a `tervKeszult`
        jelzésen, hogy a QML meg tudja különböztetni a valódi „nincs mit
        menteni" (`darab == 0`) esettől, és NE indítsa el a futtatást."""
        with open_index(self._db_path) as conn:
            keszlet = self._keszlet(conn, keszlet_id)
            if keszlet is None:
                self.hibatJelez.emit(self.tr("There is no such backup set."))
                return {"darab": 0, "bajt": 0, "kihagyott": 0, "hiba": True}
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

    @Slot(int, "QVariantList", str, result=int)
    def tervezdHattereben(  # noqa: N802 — QML-slot-stílus
        self, keszlet_id: int, mappak, media: str
    ) -> int:
        """A terv kiszámítása HÁTTÉRSZÁLON (#3645).

        A `terv` maga a gyökerek bejárását végzi (fájlonkénti `stat`,
        fényképezőgép-szűrőnél EXIF-olvasás), ami nagy, NAS-on lévő
        gyűjteménynél percekig tarthat — a mentés-gomb kattintása ettől
        fagyott meg a GUI-szálon, a tényleges futás háttérszála (#3009)
        ellenére. Azonnal visszatér a lekérdezés sorszámával; az eredmény a
        `tervKeszult` jelzésen érkezik, és csak akkor, ha közben nem
        indult újabb lekérdezés."""
        with self._terv_zar:
            self._terv_keres += 1
            keres = self._terv_keres
        self._start_background(
            self._terv_hattereben,
            args=(keres, int(keszlet_id), self._mappalista(mappak), str(media)),
            name="backup-plan",
        )
        return keres

    def _terv_hattereben(
        self, keres: int, keszlet_id: int, mappak, media: str
    ) -> None:
        """A terv törzse — háttérszálon fut."""
        try:
            eredmeny = self.terv(keszlet_id, mappak)
        except Exception as hiba:  # noqa: BLE001 — a felület ne várjon örökké
            # a gomb a válaszra zárja a „Számítás…" állapotot — hiba esetén
            # is kell válasz, különben a panel beragad
            #
            # #3645 átnézés [KÖZEPES]: korábban ide egyszerű `{"darab": 0}`
            # ment ki, amit a QML a "nincs mit menteni" esettel azonosan
            # kezelt — hamis "Backup Complete" ÉS a futtatás mégis
            # elindult volna egy sikertelen terv felett. A `hiba` jelző (és
            # a hangos `hibatJelez`) különbözteti meg a két esetet.
            _log.warning("a mentés terve elszállt: %s", hiba)
            self.hibatJelez.emit(
                self.tr("The backup plan could not be prepared: %1").replace(
                    "%1", str(hiba)
                )
            )
            eredmeny = {"darab": 0, "bajt": 0, "kihagyott": 0, "hiba": True}
        with self._terv_zar:
            if keres != self._terv_keres:
                return  # közben újabb lekérdezés indult — ez elavult
            self.tervKeszult.emit(keres, int(keszlet_id), eredmeny, media)

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

    @Slot()
    def szakitsdMeg(self) -> None:  # noqa: N802
        """A futó mentés megszakítása (#3009), ÉS a folyamatban lévő
        tervkérés érvénytelenítése (#3645 átnézés [MAGAS]).

        A már átmásolt fájlok a nyilvántartásba kerülnek, tehát a következő
        futás pontosan a hiányzókat viszi — a megszakítás nem veszít el
        munkát, csak elhalasztja.

        ⚠️ A TERVEZÉS maga nem néz a `_megszakitas`-ra (csak a másolás
        `futtasd()`-ciklusa) — enélkül a Stop/Mégse tervezés KÖZBENI
        kattintása nem állítana meg semmit: a terv elkészülte után a QML
        `fogadjATervet` úgyis elindítaná a futtatást, és a `futtasdMost`
        elején a `_megszakitas.clear()` a jelzést is törölné. A
        `_terv_keres` növelése a `mentetlenMappakLekerese` mintáját
        követi: a KÉSVE érkező terv-válasz a sorszám-eltérés miatt a
        `_terv_hattereben`-ben némán elmarad — a `tervKeszult` ilyenkor
        nem is emitál, tehát a QML soha nem kapja meg és nem indítja el a
        futtatást."""
        self._megszakitas.set()
        with self._terv_zar:
            self._terv_keres += 1

    @Slot(str, str)
    def visszaallitastFuttat(self, forras: str, cel: str) -> None:  # noqa: N802
        """A kiválasztott mentési mappát vagy ISO-készletet visszaállítja."""
        self._start_background(
            self._visszaallitas_hattereben,
            args=(str(forras), str(cel)),
            name="backup-restore",
        )

    def _visszaallitas_hattereben(self, forras: str, cel: str) -> None:
        try:
            eredmeny = visszaallit(Path(forras), Path(cel))
        except Exception as hiba:  # noqa: BLE001 — a QML hibasávjára megy
            _log.warning("a mentés visszaállítása elszállt: %s", hiba)
            self.hibatJelez.emit(
                self.tr("The backup could not be restored: %1").replace(
                    "%1", str(hiba)
                )
            )
            return
        self.visszaallitasKesz.emit(
            eredmeny.visszaallitott, eredmeny.kihagyott
        )


# The Python mixin name is private at runtime; lupdate still sees the old
# `BackupController` context above.
_BackupControllerRunsMixin = BackupController
_BackupControllerRunsMixin.__name__ = "_BackupControllerRunsMixin"
_BackupControllerRunsMixin.__qualname__ = "_BackupControllerRunsMixin"
del BackupController

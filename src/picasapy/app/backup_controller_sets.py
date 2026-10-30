"""A biztonsági mentés készleteinek és mappalistájának mixinje (#6271)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.backup import mappankent
from picasapy.index import open_index
from picasapy.index.backup_sets import (
    SZUROK,
    TIPUS_CD_DVD,
    TIPUS_LEMEZ,
    TIPUSOK,
    keszlet_letrehozasa,
    keszlet_modositasa,
    keszlet_torlese,
    keszletek,
)
from picasapy.paths import flat_key, normalize_path

_log = logging.getLogger("picasapy.app.backup_controller")
_FAJLNEV_KORLAT = 20


# `pyside6-lupdate` uses the enclosing class as the `self.tr` context.
# Keep that source name while exposing the runtime class only as a mixin.
class BackupController:
    """Készlet-karbantartás és a még el nem mentett mappák lekérdezése."""

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

    def _keszlet(self, conn, keszlet_id: int):
        for keszlet in keszletek(conn):
            if keszlet.id == int(keszlet_id):
                return keszlet
        return None

    def _jeloltek(self) -> list[Path]:
        """#3776: a gyökér FELOLDVA — a szkenner (`scanner/walker.py`)
        ugyanígy `normalize_path`-dal jár el. Feloldás nélkül egy
        symlinkes, Windows 8.3-rövidnevű vagy eltérő betűzésű gyökér alatti
        fájl útja eltérne az index kulcsától, és a mentetlen mappa a lapos
        listában (`FolderPane.mentesTerkep`) nem találna rá."""
        fajlok: list[Path] = []
        for gyoker in self._gyokerek:
            ut = Path(normalize_path(gyoker))
            if not ut.is_dir():
                continue
            fajlok.extend(sorted(p for p in ut.rglob("*") if p.is_file()))
        return fajlok

    def _mentetlen_sorok(self, keszlet_id: int) -> list[dict]:
        """#3594: a készlet még el nem mentett fájljai, mappánként.

        `backuptext2`: „A Picasa most azokat a fájlokat jeleníti meg,
        amelyekről korábban nem készült biztonsági másolat." A teljesen
        elmentett mappa nem kerül a listába. ÍRÁS NÉLKÜL. A `fajlok` az első
        `_FAJLNEV_KORLAT` név; a teljes szám a `darab`.

        #3751: az `utak` a mappa ÖSSZES mentetlen fájljának teljes útvonala,
        csonkítás nélkül — ebből szűkül a jobb oldali képrács fájl szerint
        (`AppController.setBackupFilter`)."""
        with open_index(self._db_path) as conn:
            keszlet = self._keszlet(conn, keszlet_id)
            if keszlet is None:
                return []
            terv = self._tervezd(conn, keszlet, None)
        return [
            {
                "mappa": str(mappa),
                "nev": mappa.name,
                "fajlok": [
                    tetel.forras.name for tetel in tetelek[:_FAJLNEV_KORLAT]
                ],
                "utak": [str(tetel.forras) for tetel in tetelek],
                "darab": len(tetelek),
                "bajt": sum(tetel.meret for tetel in tetelek),
            }
            for mappa, tetelek in mappankent(terv).items()
        ]

    @Slot(str, result=str)
    def mentesKulcs(self, path: str) -> str:  # noqa: N802 — QML-slot-stílus
        """#3776: a lapos mappalista (`FolderPane.mentesTerkep`,
        `FolderListModel.rowOfPath`) összehasonlító kulcsa — ugyanaz a
        tiszta függvény mindkét oldalon, hogy egy eltérő betűzésű
        Windows-gyökér se okozzon pontos-egyezés-hibát."""
        return flat_key(str(path))

    @Slot(int, result=int)
    def mentetlenMappakLekerese(self, keszlet_id: int) -> int:  # noqa: N802
        """A mentetlen mappák kiszámítása HÁTTÉRSZÁLON (#3594).

        Azonnal visszatér a lekérdezés sorszámával; az eredmény a
        `mentetlenMappakKeszek` jelzésen érkezik, és csak akkor, ha közben
        nem indult újabb lekérdezés."""
        with self._mappa_zar:
            self._mappa_keres += 1
            keres = self._mappa_keres
        self._start_background(
            self._mentetlen_hattereben,
            args=(keres, int(keszlet_id)),
            name="backup-folders",
        )
        return keres

    def _mentetlen_hattereben(self, keres: int, keszlet_id: int) -> None:
        """A mappa-lista törzse — háttérszálon fut."""
        try:
            sorok = self._mentetlen_sorok(keszlet_id)
        except Exception as hiba:  # noqa: BLE001 — a felület ne várjon örökké
            # a felület a válaszra zárja a „Számítás…" állapotot — hiba
            # esetén is kell válasz, különben a párbeszéd beragad
            _log.warning("a mentetlen mappák listája elszállt: %s", hiba)
            sorok = []
        with self._mappa_zar:
            if keres != self._mappa_keres:
                return  # közben újabb lekérdezés indult — ez elavult
            self.mentetlenMappakKeszek.emit(keres, keszlet_id, sorok)

    @staticmethod
    def _mappalista(mappak):
        """A QML-ből jött lista szálbiztos másolata (`None` = minden)."""
        return None if mappak is None else tuple(str(m) for m in mappak)


# The Python mixin name is private at runtime; lupdate still sees the old
# `BackupController` context above.
_BackupControllerSetsMixin = BackupController
_BackupControllerSetsMixin.__name__ = "_BackupControllerSetsMixin"
_BackupControllerSetsMixin.__qualname__ = "_BackupControllerSetsMixin"
del BackupController

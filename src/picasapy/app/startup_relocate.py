"""A függőben lévő adatbázis-költözés elvégzése INDULÁSKOR (#3214).

## Miért itt, és nem a párbeszédben

A mért eredetiben a „Move Database" párbeszéd gombja csak **szándékot**
rögzít (`Preferences\\AppLocalDataPathCopy`, író `0x007d1936`), a tényleges
költözést pedig a **következő indulás** végzi el, a `moving_database.fen`
haladásjelzőjével (olvasó `0x00404d97`, burkoló `0x00404c30`). Ennek két
látható következménye van, és mindkettő a felhasználónak jó:

* a másolás nem fut olyankor, amikor a program még a RÉGI helyet használja;
* utána a program már az ÚJ helyről indul — nincs külön „indítsd újra".

Ezért fut ez a modul a tárhely-előkészítés (zár + útvonalak) **előtt**: mire
a bootstrap kiszámolja az útvonalakat, a felülbírálás már az új helyre
mutat.

## Saját döntés — kimondva

A szándék sorsát **sikertelen** költözés után a kutatás nem adta meg. Mi
mindkét kimenetnél töröljük: egy elérhetetlenné vált cél (lecsatolt lemez,
időközben megtelt mappa) különben MINDEN indulást megfogna, és a
felhasználó a saját gépén nem tudná megkerülni. A hiba nem vész el — a
hívó jelzi ki, és a program a RÉGI helyről indul tovább.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal

from picasapy.index.relocate import (
    ProgressCallback,
    RelocationProgress,
    RelocationCancelled,
    RelocationError,
    relocate_data_root,
)

from .data_location import clear_pending_root, read_pending_root, write_data_root
from .relocate_cel import (
    AKADALY_FORRASON_BELUL,
    AKADALY_HALOZATI,
    AKADALY_NEM_MAPPA,
    AKADALY_NEM_URES,
    cel_akadalya,
)

#: az indulásnál még NINCS felület, ezért a szöveg itt nem fordítható — a
#: hívó az indítóképernyőn/hibanaplóban jeleníti meg
_AKADALY_SZOVEG = {
    AKADALY_NEM_MAPPA: "a megadott hely nem mappa",
    AKADALY_NEM_URES: "a megadott mappa nem üres",
    AKADALY_HALOZATI: "a megadott hely hálózati meghajtó",
    AKADALY_FORRASON_BELUL: "a megadott hely a mostani adatok mappáján belül van",
}

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class KoltozesEredmeny:
    """`uj_gyoker`: az új, egyesített adatgyökér, ha a költözés megtörtént;
    `hiba`: emberi nyelvű hibaszöveg, ha volt szándék, de nem sikerült. Ha
    nem volt szándék, mindkettő `None`."""

    uj_gyoker: Path | None = None
    hiba: str | None = None


def lomtarba(ut: Path) -> None:
    """A régi példány a Lomtárba (#1402) — véglegesen semmit nem törlünk.

    Ha nincs elérhető lomtár (írásvédett vagy hálózati kötet), a takarítás
    KIMARAD, és a mag ezt hibaszövegként jelzi: a másolat a régi helyén
    marad (hely fogy, adat nem vész).
    """
    from picasapy.fileops.trash import TrashUnavailableError, delete_to_trash

    try:
        delete_to_trash(ut)
    except TrashUnavailableError as error:
        raise OSError(
            f"A régi példány ({ut}) nem került a Lomtárba, ezért a helyén "
            f"maradt: {error}"
        ) from error


def fuggo_koltozes(
    config_dir: Path,
    index_db: Path,
    cache_dir: Path,
    *,
    haladas: ProgressCallback | None = None,
) -> KoltozesEredmeny:
    """A rögzített szándék elvégzése, ha van.

    `index_db`/`cache_dir`: a MOSTANI (költözés előtti) útvonalak.
    `haladas`: a `relocate_data_root` haladás-visszahívása — az indulásnál
    ez írja ki az indítóképernyőre, hol tart a másolás.

    A forrás minden hibaágon érintetlen marad (a `picasapy.index.relocate`
    invariánsa); szándék nélkül a modul semmihez nem nyúl — a `config_dir`
    létre sem jön.
    """
    cel = read_pending_root(config_dir)
    if cel is None:
        return KoltozesEredmeny()

    # A szándék rögzítése óta eltelhetett idő: a cél megtelhetett vagy
    # lecsatolódhatott. Ugyanazt kérdezzük, amit a párbeszéd kérdezett.
    akadaly = cel_akadalya(cel, (Path(index_db).parent, Path(cache_dir)))
    if akadaly is not None:
        szoveg = (
            f"Az adatbázis nem költözött a(z) {cel} helyre: "
            f"{_AKADALY_SZOVEG[akadaly]}."
        )
        _log.warning("%s", szoveg)
        clear_pending_root(config_dir)
        return KoltozesEredmeny(hiba=szoveg)

    try:
        eredmeny = relocate_data_root(
            Path(index_db),
            Path(cache_dir),
            cel,
            progress=haladas,
            on_verified=lambda gyoker: write_data_root(config_dir, gyoker),
            delete_old=lomtarba,
        )
    except (RelocationError, RelocationCancelled, OSError) as error:
        _log.warning("a függőben lévő adatbázis-költözés nem sikerült: %s", error)
        clear_pending_root(config_dir)
        return KoltozesEredmeny(hiba=str(error))

    clear_pending_root(config_dir)
    if eredmeny.old_cleanup_error:
        # a költözés maga sikeres: az új hely ellenőrizve él, a felülbírálás
        # átíródott — csak a régi példány takarítása maradt félbe
        _log.warning(
            "a régi adatbázis-hely takarítása részben sikertelen: %s",
            eredmeny.old_cleanup_error,
        )
    return KoltozesEredmeny(uj_gyoker=eredmeny.new_root)


class KoltozesHid(QObject):
    """A `StartupRelocateWindow.qml` haladásjelzőjének HÍDJA (#3214).

    Szándékosan szűk: a QML pontosan ezt a négy tagot olvassa, semmi mást.
    (A `kepesseg_or.py` a kontextus-objektum MINDEN tagját számon kéri —
    egy teljes vezérlő átadása 100+ kötetlen tagot jelentene.)
    """

    valtozott = Signal()

    def __init__(self, cel: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cel = str(cel)
        self._fazis = ""
        self._kesz = 0
        self._osszes = 0

    @Property(str, notify=valtozott)
    def cel(self) -> str:
        """A cél mappa — a felhasználó lássa, hova költözik."""
        return self._cel

    @Property(str, notify=valtozott)
    def fazis(self) -> str:
        """`database` / `cache` / `done` — a mag fázisneve."""
        return self._fazis

    @Property(float, notify=valtozott)
    def arany(self) -> float:
        """A haladás 0…1 között; 0, ha még nincs mit jelenteni."""
        if self._osszes <= 0:
            return 0.0
        return min(1.0, self._kesz / self._osszes)

    def jelentsd(self, haladas: RelocationProgress) -> None:
        """A `relocate_data_root` haladás-visszahívása — HÁTTÉRSZÁLRÓL hívva.

        A `valtozott` jelzés a fő szálra sorolódik be (queued), tehát a QML
        kötések a helyes szálon frissülnek.
        """
        self._fazis = haladas.phase
        self._kesz = haladas.done
        self._osszes = haladas.total
        self.valtozott.emit()

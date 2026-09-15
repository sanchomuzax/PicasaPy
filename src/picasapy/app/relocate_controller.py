"""RelocateController: a "Move Database" dialógus (`MoveDatabaseDialog.qml`
+ `MovingDatabaseDialog.qml`, #368, `move_database.fen`/`moving_database.fen`)
QML-hídja a `picasapy.index.relocate` mag fölött.

Önálló QObject — a `DedupController`/`ImportSourceController` mintáját
követve NEM az `AppController` mixinje, hogy a `controller.py`/`Main.qml`
(forró fájlok, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést
kapja.

Az áthelyezés HÁTTÉRSZÁLON fut, haladás-jelzéssel (`relocateProgress`) és
megszakítható (`cancelRelocate`) — a `dedup_controller.py` `stop_event`
mintáját követi. Sikeres áthelyezés az ÚJ helyet írja a
`data_location.py` felülbírálásába: ez a Picasa "Move on next restart"
viselkedésének felel meg — a FUTÓ példány útvonalai nem változnak, a
felhasználónak újra kell indítania a PicasaPy-t, hogy az új helyről
induljon (`relocateFinished(True, ...)` jelzi ezt a QML-nek)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from picasapy.index.relocate import (
    RelocationCancelled,
    RelocationError,
    relocate_data_root,
)

from .data_location import write_data_root
from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)


def _lomtarba(ut: Path) -> None:
    """A régi adatbázis/gyorsítótár a Lomtárba (#1402).

    Ha nincs elérhető lomtár (írásvédett hálózati kötet, `TrashUnavailable`),
    a takarítás **kimarad**, és a mag hibaszövegként jelzi — véglegesen NEM
    törlünk a felhasználó háta mögött. Az adatbázis másolata ilyenkor a
    régi helyén marad: hely fogy, de semmi nem veszik el, és a felület a
    `old_cleanup_error`-on át ezt meg is mondja.
    """
    from picasapy.fileops.trash import TrashUnavailableError, delete_to_trash

    try:
        delete_to_trash(ut)
    except TrashUnavailableError as error:
        raise OSError(
            f"A régi példány ({ut}) nem került a Lomtárba, ezért a helyén "
            f"maradt: {error}"
        ) from error


class RelocateController(BackgroundWorkerMixin, QObject):
    """A `MoveDatabaseDialog.qml`/`MovingDatabaseDialog.qml` háttér-hídja:
    cél-választás, háttérszálas áthelyezés haladás-jelzéssel, hiba/
    megszakítás-kezelés."""

    relocateStarted = Signal()
    # (fázis: "database"/"cache"/"done", kész bájt, összes bájt)
    relocateProgress = Signal(str, int, int)
    relocateCancelled = Signal()
    relocateFailed = Signal(str)  # emberi nyelvű hibaüzenet — a forrás érintetlen
    # (új hely szövegesen) — sikeres áthelyezés, ÚJRAINDÍTÁS szükséges
    relocateFinished = Signal(str)

    def __init__(
        self,
        old_index_db: str | Path,
        old_cache_dir: str | Path,
        config_dir: str | Path,
        parent: QObject | None = None,
    ) -> None:
        """`old_index_db`/`old_cache_dir`: a jelenleg érvényes útvonalak
        (`application.py` `_data_dir()/"index.db"` és
        `_cache_dir()/"thumbs"`); `config_dir`: ahova az áthelyezés utáni
        útvonal-felülbírálás kerül (`application.py` `_config_dir()`)."""
        super().__init__(parent)
        self._old_index_db = Path(old_index_db)
        self._old_cache_dir = Path(old_cache_dir)
        self._config_dir = Path(config_dir)
        self._stop_event: threading.Event | None = None

    # #377: Qt-Property kell (nem sima @property) — a QML a sima Python-
    # property-t nem látja, és induláskor "Unable to assign [undefined] to
    # QString" figyelmeztetést adott. Az érték konstans (az áthelyezés
    # újraindítás után érvényesül), ezért constant=True.
    @Property(str, constant=True)
    def currentLocation(self) -> str:  # noqa: N802 — QML-property-stílus
        """A jelenlegi (egyesített) adatgyökér — a `pathbox
        name="current_location"` mezőnek. Az index és a cache külön XDG-
        mappában is élhet (első áthelyezés előtt) — ilyenkor az index
        mappáját mutatjuk, mert az a "fő" adat (a cache újraépíthető)."""
        return str(self._old_index_db.parent)

    @Slot(str)
    def startRelocate(self, new_location: str) -> None:
        """Az áthelyezés indítása HÁTTÉRSZÁLON. `new_location` `file://`
        URL is lehet (a QML `FolderDialog` mintája, ld. `to_local_path`)."""
        target_text = to_local_path(new_location)
        if not target_text:
            self.relocateFailed.emit(
                self.tr("Choose a new database location first.")
            )
            return
        new_root = Path(target_text)

        # #1402: a mért eredeti a műveletet MEGELŐZŐEN ellenőriz, és
        # elutasításnál semmihez nem nyúl („No changes will be made").
        # Két feltétel van, mindkettő a binárisból: a cél írható HELYI
        # merevlemez (`MoveDatabase::LocalDriveOnly`), és ÜRES
        # (`MoveDatabase::Failure` — „make sure the destination is empty").
        hiba = self._elutasitas_oka(new_root)
        if hiba:
            self.relocateFailed.emit(hiba)
            return

        stop_event = threading.Event()
        self._stop_event = stop_event
        self.relocateStarted.emit()
        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a `_stop_event` a megszakítási jelző marad, ez csak a szál
        # bevárhatóságát adja hozzá.
        self._start_background(
            self._run_relocate, args=(new_root, stop_event), name="picasapy-relocate"
        )

    @Slot()
    def cancelRelocate(self) -> None:
        """A folyamatban lévő áthelyezés megszakítása. A worker a
        legközelebbi ellenőrzési ponton tisztán leáll — a forrás
        MINDIG érintetlen marad, a célon keletkezett félkész másolat
        eltűnik (ld. `picasapy.index.relocate` invariánsa)."""
        if self._stop_event is not None:
            self._stop_event.set()

    def _elutasitas_oka(self, new_root: Path) -> str:
        """Miért nem alkalmas a cél — üres szöveg, ha alkalmas (#1402).

        A NEM létező mappa rendben van: azt a mag létrehozza. A meglévő,
        de nem üres mappa viszont nem: az eredeti is ezt kéri
        („make sure the destination is empty"), és ott a régi tartalom
        némán összekeveredhetne az áthelyezettel.
        """
        from picasapy.perf.tesztuzem import TAROLO_HALOZATI, tarolo_tipusa

        if new_root.exists() and not new_root.is_dir():
            return self.tr("The chosen destination is not a folder.")
        if new_root.is_dir() and any(new_root.iterdir()):
            return self.tr(
                "The destination folder is not empty. Choose an empty folder "
                "and try again."
            )
        # A típust a LÉTEZŐ legközelebbi szülőre kérdezzük: egy még
        # létre nem hozott mappának nincs mountja.
        letezo = new_root
        while not letezo.exists() and letezo.parent != letezo:
            letezo = letezo.parent
        # ⚠️ SZŰKÍTVE, szándékosan: az eredeti „írható HELYI merevlemez"-t
        # kér, mi viszont csak azt utasítjuk el, amit POZITÍVAN hálózati
        # meghajtóként ismerünk fel. Ok: a `tarolo_tipusa` bármilyen hibára
        # „ismeretlen"-t ad, és egy téves elutasítás rosszabb, mint egy
        # átengedett cserélhető lemez — a felhasználó a saját gépén nem tud
        # megkerülni egy magabiztosan hibás tiltást. A hálózati eset az,
        # amitől a mérés szerint tényleg óvni kell (lassú, és a
        # zárolás-kezelése más).
        if tarolo_tipusa(letezo) == TAROLO_HALOZATI:
            return self.tr(
                "The database cannot be moved to a network drive. Nothing "
                "has been changed."
            )
        return ""

    def _run_relocate(self, new_root: Path, stop_event: threading.Event) -> None:
        try:
            result = relocate_data_root(
                self._old_index_db,
                self._old_cache_dir,
                new_root,
                progress=lambda p: self.relocateProgress.emit(
                    p.phase, p.done, p.total
                ),
                should_cancel=stop_event.is_set,
                on_verified=lambda root: write_data_root(self._config_dir, root),
                # #1402: a régi példány a LOMTÁRBA megy, nem törlődik — ezt a
                # mért eredeti is így teszi. A lomtár a `fileops/` sávban él,
                # az `index/` szándékosan nem ismeri, ezért ITT adjuk át.
                delete_old=_lomtarba,
            )
        except RelocationCancelled:
            self.relocateCancelled.emit()
            return
        except RelocationError as error:
            _log.warning("adatbázis-áthelyezés sikertelen: %s", error)
            self.relocateFailed.emit(str(error))
            return
        finally:
            if self._stop_event is stop_event:
                self._stop_event = None

        if result.old_cleanup_error:
            # az áthelyezés maga sikeres (az új hely él és ellenőrzött) —
            # a régi adatok maradék törlési hibája csak figyelmeztetés
            _log.warning(
                "a régi adatbázis-hely takarítása részben sikertelen: %s",
                result.old_cleanup_error,
            )
        self.relocateFinished.emit(str(result.new_root))

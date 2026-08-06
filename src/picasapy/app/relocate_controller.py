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

_log = logging.getLogger(__name__)


class RelocateController(QObject):
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

        stop_event = threading.Event()
        self._stop_event = stop_event
        self.relocateStarted.emit()
        threading.Thread(
            target=self._run_relocate, args=(new_root, stop_event), daemon=True
        ).start()

    @Slot()
    def cancelRelocate(self) -> None:
        """A folyamatban lévő áthelyezés megszakítása. A worker a
        legközelebbi ellenőrzési ponton tisztán leáll — a forrás
        MINDIG érintetlen marad, a célon keletkezett félkész másolat
        eltűnik (ld. `picasapy.index.relocate` invariánsa)."""
        if self._stop_event is not None:
            self._stop_event.set()

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

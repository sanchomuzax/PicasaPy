"""CompactController: az adatbázis-tömörítés QML-hídja (#449,
`compacting.fen`).

Önálló QObject — a `RelocateController` (#368) mintáját követve, hogy a
`controller.py` (forró fájl) ne hízzon tovább.

A tömörítés HÁTTÉRSZÁLON fut, „szívverés"-jelzéssel (`compactProgress`) és
megszakíthatóan (`cancelCompact`) — az eredeti `compacting.fen` egyetlen
gombja is a **Mégse** volt.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from picasapy.index.compact import (
    DEFAULT_COMPACT_PERCENT,
    CompactionCancelled,
    CompactionError,
    compact_database,
    wasted_percent,
)

from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)


class CompactController(BackgroundWorkerMixin, QObject):
    """A `CompactDatabaseDialog.qml` háttér-hídja."""

    compactStarted = Signal()
    compactProgress = Signal(int)  # szívverés-számláló (nem százalék!)
    compactCancelled = Signal()
    compactFailed = Signal(str)
    # (megtakarított bájt) — sikeres tömörítés
    compactFinished = Signal(int)
    runningChanged = Signal()

    def __init__(self, index_db: str | Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._index_db = Path(index_db)
        self._stop_event: threading.Event | None = None
        self._running = False

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        """Fut-e éppen tömörítés (a Mégse gomb és a státusz-sor köti)."""
        return self._running

    @Slot(result=bool)
    def isWorthCompacting(self) -> bool:  # noqa: N802 — QML-slot-stílus
        """Érdemes-e most tömöríteni — a dialógus ezzel írja ki, hogy
        „nincs mit tömöríteni", ahelyett hogy percekre elindulna."""
        return wasted_percent(self._index_db) >= DEFAULT_COMPACT_PERCENT

    @Slot()
    def startCompact(self) -> None:  # noqa: N802 — QML-slot-stílus
        if self._running:
            return
        stop_event = threading.Event()
        self._stop_event = stop_event
        self._running = True
        self.runningChanged.emit()
        self.compactStarted.emit()
        self._start_background(
            self._run_compact, args=(stop_event,), name="picasapy-compact"
        )

    @Slot()
    def cancelCompact(self) -> None:  # noqa: N802 — QML-slot-stílus
        """Megszakítás — az adatbázis MINDIG érintetlen marad (a `VACUUM`
        ideiglenes fájlba dolgozik, és csak a végén cserél)."""
        if self._stop_event is not None:
            self._stop_event.set()

    def _run_compact(self, stop_event: threading.Event) -> None:
        try:
            result = compact_database(
                self._index_db,
                progress=self.compactProgress.emit,
                should_cancel=stop_event.is_set,
            )
        except CompactionCancelled:
            self.compactCancelled.emit()
            return
        except CompactionError as error:
            _log.warning("adatbázis-tömörítés sikertelen: %s", error)
            self.compactFailed.emit(str(error))
            return
        finally:
            if self._stop_event is stop_event:
                self._stop_event = None
            self._running = False
            self.runningChanged.emit()
        self.compactFinished.emit(result.saved_bytes)


__all__ = ["CompactController"]

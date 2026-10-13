"""Induláskori, fájlrendszert érintő karbantartás háttérszálon (#4687)."""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot

from .startup_diagnostics import StartupProgressLog
from .worker_thread import BackgroundWorkerMixin


@dataclass(frozen=True)
class StartupMaintenanceStep:
    """Egy sorban futó indulási feladat és a splash felirata."""

    key: str
    name: str
    status_text: str | None
    work: Callable[[], object]


class StartupMaintenance(BackgroundWorkerMixin, QObject):
    """Soros háttérmunka, időbélyeges indulási naplóval.

    A munkafüggvények Qt-objektumot nem módosíthatnak. A lépés eredménye a
    `stepFinished` jelzésen jut vissza a fő szálra; a takarítás és a
    könyvtárszinkron sorrendjét a `batchFinished` jelzés zárja.
    """

    statusChanged = Signal(str)
    stepFinished = Signal(str, object, str)
    batchFinished = Signal(str)

    def __init__(
        self, progress_log: StartupProgressLog, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._progress_log = progress_log
        self._lock = threading.Lock()
        self._batches: deque[tuple[str, tuple[StartupMaintenanceStep, ...]]] = deque()
        self._running = False
        self._cancelled = threading.Event()
        self._refresh_handler: Callable[[], None] | None = None

    def set_refresh_handler(self, handler: Callable[[], None]) -> None:
        """A szinkronjelzés főszálas fogadója, ami új mappafa-munkát sorol."""
        self._refresh_handler = handler

    @Slot()
    def request_refresh(self) -> None:
        """A szinkronjelzést biztonságosan a Qt főszálán dolgozza fel."""
        if self._refresh_handler is not None:
            self._refresh_handler()

    def enqueue(
        self, batch_key: str, steps: tuple[StartupMaintenanceStep, ...]
    ) -> None:
        """Feladatcsoport hozzáfűzése az egyetlen indulási munkasorhoz."""
        if not steps or self._cancelled.is_set():
            return
        with self._lock:
            self._batches.append((batch_key, tuple(steps)))
            if self._running:
                return
            self._running = True
        self._start_background(self._run_queue, name="picasapy-startup-maintenance")

    def cancel(self) -> None:
        """Kilépéskor ne induljon új lépés vagy Qt-jelzés."""
        self._cancelled.set()

    def _run_queue(self) -> None:
        while True:
            if self._cancelled.is_set():
                self._drop_pending_batches()
                return
            with self._lock:
                if not self._batches:
                    self._running = False
                    return
                batch_key, steps = self._batches.popleft()

            for step in steps:
                if self._cancelled.is_set():
                    self._drop_pending_batches()
                    return
                if step.status_text:
                    self.statusChanged.emit(step.status_text)
                self._progress_log.mark(f"{step.name} elkezdődött")
                try:
                    result = step.work()
                except Exception as error:  # noqa: BLE001 — az indulás menjen tovább
                    error_type = type(error).__name__
                    self._progress_log.mark(
                        f"{step.name} hibára futott ({error_type})"
                    )
                    result = None
                else:
                    error_type = ""
                    self._progress_log.mark(f"{step.name} befejeződött")

                if self._cancelled.is_set():
                    self._drop_pending_batches()
                    return
                self.stepFinished.emit(step.key, result, error_type)

            if not self._cancelled.is_set():
                self.batchFinished.emit(batch_key)

    def _drop_pending_batches(self) -> None:
        with self._lock:
            self._batches.clear()
            self._running = False


__all__ = ["StartupMaintenance", "StartupMaintenanceStep"]

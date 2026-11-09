"""A háttér-arckeresést fékező felhasználói aktivitás figyelése."""

from __future__ import annotations

import threading
from time import monotonic

from PySide6.QtCore import QEvent, QObject, QTimer


_USER_INPUT_EVENTS = frozenset(
    {
        QEvent.Type.KeyPress,
        QEvent.Type.KeyRelease,
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonRelease,
        QEvent.Type.MouseButtonDblClick,
        QEvent.Type.MouseMove,
        QEvent.Type.Wheel,
        QEvent.Type.TouchBegin,
        QEvent.Type.TouchUpdate,
        QEvent.Type.TouchEnd,
        QEvent.Type.TabletPress,
        QEvent.Type.TabletMove,
        QEvent.Type.TabletRelease,
        QEvent.Type.NativeGesture,
    }
)


class FaceScanActivityMonitor(QObject):
    """GUI-szálon figyeli a bevitelt és a QML néző/szerkesztő állapotát.

    A háttérszál csak a `should_pause()` szálbiztos, olcsó eredményét kéri;
    QML-objektumot sosem olvas közvetlenül a workerből.
    """

    IDLE_SECONDS = 30.0

    def __init__(self, application, engine, *, clock=monotonic):
        super().__init__(application)
        self._application = application
        self._engine = engine
        self._clock = clock
        self._lock = threading.Lock()
        self._last_input = self._clock() - self.IDLE_SECONDS
        self._viewer_open = False
        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._refresh_viewer_open)
        application.installEventFilter(self)
        self._refresh_viewer_open()
        self._timer.start()

    def eventFilter(self, _watched, event) -> bool:  # noqa: N802 — Qt-név
        if event.type() in _USER_INPUT_EVENTS:
            with self._lock:
                self._last_input = self._clock()
        return False

    def _refresh_viewer_open(self) -> None:
        try:
            roots = self._engine.rootObjects()
            viewer_open = any(
                bool(root.property("viewerOpen")) for root in roots if root
            )
        except RuntimeError:
            viewer_open = False
        with self._lock:
            self._viewer_open = viewer_open

    def should_pause(self) -> bool:
        with self._lock:
            return self._viewer_open or (
                self._clock() - self._last_input < self.IDLE_SECONDS
            )

    def stop(self) -> None:
        self._timer.stop()
        try:
            self._application.removeEventFilter(self)
        except RuntimeError:
            pass

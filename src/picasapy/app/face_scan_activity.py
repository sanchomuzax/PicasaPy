"""A háttér-arckeresést fékező felhasználói aktivitás figyelése."""

from __future__ import annotations

import threading
from time import monotonic

import shiboken6
from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtGui import QGuiApplication

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
        # #7086: a szűrő CSAK a felső szintű ablakokon ül, nem az egész
        # alkalmazáson. Az alkalmazás-szintű Python-szűrő minden Qt-eseménynél
        # (időzítő, metahívás, képválasz) a GIL-re várt; görgetéskor mérve
        # másodpercenként 1300-1700 hívás, és amíg a bélyegkép-szálak
        # dolgoztak, a felület lefagyott. A bevitel mindig az ablakhoz érkezik.
        self._figyelt_ablakok: list = []
        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._refresh_viewer_open)
        self._timer.timeout.connect(self._ablakok_figyelese)
        self._ablakok_figyelese()
        self._refresh_viewer_open()
        self._timer.start()

    def _ablakok_figyelese(self) -> None:
        """Az új felső szintű ablakokra is felteszi a szűrőt (a párbeszéd-
        ablakok később nyílnak, ezért az időzítő is hívja)."""
        try:
            ablakok = QGuiApplication.topLevelWindows()
        except RuntimeError:
            return
        # a bezárt (C++-oldalon megszűnt) ablakok kikerülnek a listából
        self._figyelt_ablakok = [a for a in self._figyelt_ablakok if shiboken6.isValid(a)]
        for ablak in ablakok:
            if not any(ablak is figyelt for figyelt in self._figyelt_ablakok):
                ablak.installEventFilter(self)
                self._figyelt_ablakok.append(ablak)

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
        for ablak in self._figyelt_ablakok:
            try:
                ablak.removeEventFilter(self)
            except RuntimeError:
                pass
        self._figyelt_ablakok = []

"""Az alsó állapotsáv „min dolgozik a program” kapcsolója (#6440).

Súgó ▸ „Háttérmunka az állapotsávon”: pipás, tartós (`QSettings`), és
alapból BE van. Kikapcsolva az állapotsáv pontosan a mostani: a háttérmunka
csak a kék csíkot és a jelzőt mozgatja, a szöveget nem írja felül.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QSettings, Signal, Slot

from .busy_activity import aktivitas_szoveg
from .busy_registry import get_app_busy_registry

#: A tartós kapcsoló `QSettings`-kulcsa.
ACTIVITY_STATUS_KEY = "view/showBackgroundActivity"


def activity_status_enabled_from(settings: QSettings | Any) -> bool:
    """A tartós beállítás olvasata. Hiányzó vagy érthetetlen érték = BE."""
    ertek = settings.value(ACTIVITY_STATUS_KEY)
    if ertek is None or ertek == "":
        return True
    if isinstance(ertek, bool):
        return ertek
    return str(ertek).strip().casefold() not in ("false", "0", "no", "off")


class ActivityStatusMixin:
    """`statusActivityEnabled` kapcsoló és az állapotsáv munkaszövege."""

    statusActivityChanged = Signal()

    def _init_activity_status(self) -> None:
        """Az AppController.__init__ hívja (a mixinek nem definiálnak saját
        `__init__`-et, ez a konvenció a repóban)."""
        self._status_activity_on = activity_status_enabled_from(self._get_settings())
        registry = get_app_busy_registry()
        registry.visibleChanged.connect(self.statusActivityChanged)
        registry.activityChanged.connect(self.statusActivityChanged)

    # -- QML-nek kitett állapot ---------------------------------------------

    @Property(bool, notify=statusActivityChanged)
    def statusActivityEnabled(self) -> bool:
        """Be van-e kapcsolva a háttérmunka kijelzése az állapotsávon."""
        return self._status_activity_on

    @Property(str, notify=statusActivityChanged)
    def statusActivityText(self) -> str:
        """Az állapotsáv munkaszövege; üres, ha nincs mit mutatni: kikapcsolva,
        vagy a munka a küszöb alatt van / már nincs látható."""
        if not self._status_activity_on:
            return ""
        registry = get_app_busy_registry()
        if not registry.visible:
            return ""
        return aktivitas_szoveg(registry.aktiv_munkak())

    # -- kapcsoló -------------------------------------------------------------

    @Slot()
    def toggleStatusActivity(self) -> None:
        self.setStatusActivityEnabled(not self._status_activity_on)

    @Slot(bool)
    def setStatusActivityEnabled(self, enabled: bool) -> None:
        """A kapcsoló átállítása, TARTÓSAN (a `sync()` a kilépés előtt is megmarad)."""
        enabled = bool(enabled)
        if enabled == self._status_activity_on:
            return
        self._status_activity_on = enabled
        settings = self._get_settings()
        settings.setValue(ACTIVITY_STATUS_KEY, enabled)
        settings.sync()
        self.statusActivityChanged.emit()

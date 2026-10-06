"""A Fotónéző következő megnyitásának ablakmódja (#4432)."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

# Az eredeti Preferences-kulcsot használjuk a saját QSettings-tárunkban is.
VIEWER_FULLSCREEN_STARTUP_KEY = "ViewerFullscreenStartup"


def coerce_viewer_fullscreen_startup(value) -> bool:
    """A mentett 0/1 értéket bool-lá alakítja; hiányzó kulcsnál igaz."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("0", "false", "no", "off", ""):
            return False
        if normalized in ("1", "true", "yes", "on"):
            return True
    return True


class ViewerStartupMixin:
    """A Fotónéző indításkori teljes képernyős beállítása."""

    viewerFullscreenStartupChanged = Signal()

    def _init_viewer_startup(self) -> None:
        self._viewer_fullscreen_startup = coerce_viewer_fullscreen_startup(
            self._get_settings().value(VIEWER_FULLSCREEN_STARTUP_KEY, 1)
        )

    @Property(bool, notify=viewerFullscreenStartupChanged)
    def viewerFullscreenStartup(self) -> bool:  # noqa: N802 — QML API
        return self._viewer_fullscreen_startup

    def setViewerFullscreenStartup(self, enabled: bool) -> None:  # noqa: N802
        enabled = bool(enabled)
        if enabled == self._viewer_fullscreen_startup:
            return
        self._viewer_fullscreen_startup = enabled
        self._get_settings().setValue(
            VIEWER_FULLSCREEN_STARTUP_KEY, 1 if enabled else 0
        )
        self.viewerFullscreenStartupChanged.emit()

    @Slot()
    def toggleViewerFullscreenStartup(self) -> None:  # noqa: N802
        self.setViewerFullscreenStartup(not self._viewer_fullscreen_startup)

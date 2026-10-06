"""A szerkesztő kezelősávjának tartós láthatósági kapcsolója (#4336)."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

EDITOR_CONTROLS_KEY = "view/editorControlsVisible"
_TRUE_VALUES = ("true", "1")
_FALSE_VALUES = ("false", "0")


def coerce_editor_controls_flag(value, default: bool = True) -> bool:
    """A QSettings bool/string értékét bool-lá alakítja; hibás érték = alap."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _TRUE_VALUES:
            return True
        if normalized in _FALSE_VALUES:
            return False
    return default


class EditorControlsMixin:
    """Az editor kezelősáv állapota, QSettings-ből visszatöltve."""

    editorControlsVisibleChanged = Signal()

    def _init_editor_controls(self) -> None:
        self._editor_controls_visible = coerce_editor_controls_flag(
            self._get_settings().value(EDITOR_CONTROLS_KEY, True)
        )

    @Property(bool, notify=editorControlsVisibleChanged)
    def editorControlsVisible(self) -> bool:
        return self._editor_controls_visible

    @Slot(bool)
    def setEditorControlsVisible(self, visible: bool) -> None:
        visible = bool(visible)
        if visible == self._editor_controls_visible:
            return
        self._editor_controls_visible = visible
        self._get_settings().setValue(
            EDITOR_CONTROLS_KEY, "true" if visible else "false"
        )
        self.editorControlsVisibleChanged.emit()

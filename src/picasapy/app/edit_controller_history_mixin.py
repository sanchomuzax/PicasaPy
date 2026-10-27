"""A szerkesztő globális Visszavonás/Újra verem és feliratai."""

from __future__ import annotations

from .edit_controller_shared import (
    EditSession,
    Property,
    Slot,
    _action_key,
    redo_label,
    undo_label,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

class EditControllerHistoryMixin:
    """A szerkesztő globális Visszavonás/Újra verem és feliratai."""

    @Property(bool, notify=_Signals.toolsChanged)
    def canUndo(self) -> bool:
        return bool(self._undo_stack)


    @Property(bool, notify=_Signals.toolsChanged)
    def canRedo(self) -> bool:
        return bool(self._redo_stack)


    @Property(str, notify=_Signals.toolsChanged)
    def undoAction(self) -> str:
        """A visszavonható művelet kulcsa (crop/tilt/redeye/…) — a gomb
        feliratához (#59)."""
        return self._undo_stack[-1][1] if self._undo_stack else ""


    @Property(str, notify=_Signals.toolsChanged)
    def redoAction(self) -> str:
        return self._redo_stack[-1][1] if self._redo_stack else ""


    @Property(str, notify=_Signals.toolsChanged)
    def undoLabel(self) -> str:
        """A Visszavonás gomb KÉSZ felirata (#465).

        Két állapota van, az eredeti `CFilterStackUI` szövegei szerint: üres
        veremnél a puszta „Visszavonás", egyébként „Visszavonás: <lépés>" —
        a felhasználó látja, mit fog visszavonni. A nevet az
        `edit_action_names` névtára adja, tehát a lánc MINDEN eleme néven
        nevezhető, nem csak egy kézzel gondozott tucat."""
        return undo_label(self.undoAction)


    @Property(str, notify=_Signals.toolsChanged)
    def redoLabel(self) -> str:
        """Az Újra gomb kész felirata — az `undoLabel` párja (#465)."""
        return redo_label(self.redoAction)


    @Slot()
    def undo(self) -> None:
        """Az utolsó művelet visszavonása (a művelet ELŐTTI lánc áll vissza)."""
        if not self._undo_stack:
            return
        self._require_active()
        previous_value, action = self._undo_stack.pop()
        self._redo_stack.append((self._session.to_value(), action))
        self._session = EditSession.from_value(previous_value)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot()
    def redo(self) -> None:
        """A visszavont művelet ismételt alkalmazása."""
        if not self._redo_stack:
            return
        self._require_active()
        redo_value, action = self._redo_stack.pop()
        self._undo_stack.append((self._session.to_value(), action))
        self._session = EditSession.from_value(redo_value)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    @staticmethod
    def _seed_undo_from_chain(session: EditSession) -> list[tuple[str, str]]:
        """A mentett filters-láncból épített undo-verem: az i. lépés
        visszavonása az első i elemű láncot állítja vissza. Az ismeretlen
        (pl. valódi Picasa által írt) szűrők is rétegként vonhatók vissza —
        a Visszavonásig a round-trip elv szerint érintetlenek maradnak."""
        entries: list[tuple[str, str]] = []
        for index, op in enumerate(session.ops):
            previous_value = EditSession(ops=session.ops[:index]).to_value()
            entries.append((previous_value, _action_key(op.name)))
        return entries


    def _push_undo(self, action: str) -> None:
        self._undo_stack.append((self._session.to_value(), action))
        self._redo_stack.clear()


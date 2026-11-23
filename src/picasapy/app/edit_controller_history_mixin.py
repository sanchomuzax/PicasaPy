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

#: #7391: azok a műveletek, amelyek megerősített visszavonása nem kerül az Újra-
#: verembe (az eredetin az Undo után az Újra tiltott, csupasz „Redo"). Csak a
#: retusálás: a Vörösszem eredeti viselkedése nincs mérve (7327-10), ezért az
#: a megszokott módon az Újra-verembe kerül.
_REDO_NELKULI_MUVELETEK = frozenset({"retouch"})


class EditControllerHistoryMixin:
    """A szerkesztő globális Visszavonás/Újra verem és feliratai."""

    @Property(bool, notify=_Signals.canUndoChanged)
    def canUndo(self) -> bool:
        return bool(self._undo_stack)


    @Property(bool, notify=_Signals.canRedoChanged)
    def canRedo(self) -> bool:
        return bool(self._redo_stack)


    @Property(str, notify=_Signals.undoActionChanged)
    def undoAction(self) -> str:
        """A visszavonható művelet kulcsa (crop/tilt/redeye/…) — a gomb
        feliratához (#59)."""
        return self._undo_stack[-1][1] if self._undo_stack else ""


    @Property(str, notify=_Signals.redoActionChanged)
    def redoAction(self) -> str:
        return self._redo_stack[-1][1] if self._redo_stack else ""


    @Property(str, notify=_Signals.undoLabelChanged)
    def undoLabel(self) -> str:
        """A Visszavonás gomb KÉSZ felirata (#465).

        Két állapota van, az eredeti `CFilterStackUI` szövegei szerint: üres
        veremnél a puszta „Visszavonás", egyébként „Visszavonás: <lépés>" —
        a felhasználó látja, mit fog visszavonni. A nevet az
        `edit_action_names` névtára adja, tehát a lánc MINDEN eleme néven
        nevezhető, nem csak egy kézzel gondozott tucat."""
        return undo_label(self.undoAction)


    @Property(str, notify=_Signals.redoLabelChanged)
    def redoLabel(self) -> str:
        """Az Újra gomb kész felirata — az `undoLabel` párja (#465)."""
        return redo_label(self.redoAction)


    @Slot()
    def undo(self) -> None:
        """Az utolsó művelet visszavonása (a művelet ELŐTTI lánc áll vissza).

        #7391: a retusálás megerősített visszavonása után az Újra tiltott és a
        felirata csupasz (job-907 `__24`): a visszavont retusálás nem kerül az
        Újra-verembe, és a verem ki is ürül, különben egy korábban visszavont
        későbbi lépés (a Crop utáni állapot, benne a retusálással) Újrája a
        retusálást is visszahozná, holott az üzenet szerint nem hozható vissza.
        Mérve csak az üres Újra-veremmel indított eset; a nem üres veremé a
        „nem hozható vissza" üzenetből következő döntés."""
        if not self._undo_stack:
            return
        self._require_active()
        previous_value, action = self._undo_stack.pop()
        if action in _REDO_NELKULI_MUVELETEK:
            self._redo_stack.clear()
        else:
            self._redo_stack.append((self._session.to_value(), action))
        self._session = EditSession.from_value(previous_value)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()
        self._end_finetune_visit()


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
        self._end_finetune_visit()


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
        if self._finetune_visit_open():
            self._end_finetune_visit()   # #7383: a másik lépés lezárja a látogatást
        self._undo_stack.append((self._session.to_value(), action))
        self._redo_stack.clear()


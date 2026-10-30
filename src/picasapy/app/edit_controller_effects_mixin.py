"""Az egygombos javítások, effektek, csúszkák és színpipetták.

A #6267 bontás után a témák az `edit_controller_effects_*_mixin.py` modulokban
élnek. Ez a homlokzat tartja a régi importútvonalat (a nyilvános nevek a
`__all__`-ban vannak), és az `applyEffect` marad itt, mert a #5957-es felosztás
teszt ezt a helyet rögzíti.
"""

from __future__ import annotations

from .edit_controller_effects_color_mixin import EditControllerEffectsColorMixin
from .edit_controller_effects_finetune_mixin import EditControllerEffectsFinetuneMixin
from .edit_controller_effects_params_mixin import EditControllerEffectsParamsMixin
from .edit_controller_effects_shift_mixin import EditControllerEffectsShiftMixin
from .edit_controller_effects_state_mixin import EditControllerEffectsStateMixin
from .edit_controller_shared import (
    _APPLICABLE_EFFECTS,
    _EFFECT_INI_NAMES,
    _EFFECT_PARAMS,
    DEAD_LEGACY_OPS,
    LEGACY_EFFECTS,
    LEGACY_EFFECT_KEYS,
    EditSession,
    Property,
    QCoreApplication,
    QGuiApplication,
    Slot,
    build_finetune2_lut,
    can_offer_filter_control,
    estimate_neutral_color,
    format_param_values,
    gyors_elonezet,
    has_params,
    np,
    one_click_keys,
    parse_neutral_argb,
    resolve_effect_params,
)

__all__ = [
    "DEAD_LEGACY_OPS",
    "EditControllerEffectsMixin",
    "EditSession",
    "LEGACY_EFFECTS",
    "LEGACY_EFFECT_KEYS",
    "Property",
    "QCoreApplication",
    "QGuiApplication",
    "Slot",
    "build_finetune2_lut",
    "can_offer_filter_control",
    "estimate_neutral_color",
    "format_param_values",
    "gyors_elonezet",
    "has_params",
    "np",
    "one_click_keys",
    "parse_neutral_argb",
    "resolve_effect_params",
]


class EditControllerEffectsMixin(
    EditControllerEffectsStateMixin,
    EditControllerEffectsFinetuneMixin,
    EditControllerEffectsParamsMixin,
    EditControllerEffectsColorMixin,
    EditControllerEffectsShiftMixin,
):
    """Az egygombos javítások, effektek, csúszkák és színpipetták."""

    @Slot(str)
    def applyEffect(self, name: str) -> None:
        """Effekt réteg a lánc végére (#20): append-only, undo-lépéssel.

        Az ismeretlen név ValueError; a paramétert igénylő effektek (pl. sat)
        dokumentált alapértékkel kerülnek be (`_EFFECT_PARAMS`)."""
        self._require_active()
        key = name.casefold()
        if key not in _APPLICABLE_EFFECTS:
            raise ValueError(f"Érvénytelen effekt: {name!r}")
        self._push_undo(key)
        self._session = self._session.append_effect(
            _EFFECT_INI_NAMES.get(key, key), _EFFECT_PARAMS.get(key, ("1",))
        )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

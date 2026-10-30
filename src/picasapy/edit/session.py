"""EditSession — immutábilis szerkesztési-lánc (filters=) állapotkezelő."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from picasapy.ini.filters import (
    FilterOp,
    canonicalize_op,
    parse_filters,
    serialize_filters,
    validate_op_for_write,
)
from picasapy.ini.rect64 import Rect64, decode_rect64, encode_rect64
from picasapy.ini.redeye import (
    EyeCircle64,
    REDEYE_FILTER_NAME,
    build_redeye_op,
    parse_redeye_regions,
)
from picasapy.ini.retouch import (
    RETOUCH_FILTER_NAME,
    RetouchPatch,
    build_retouch_op,
    build_retouch_patches_op,
    parse_retouch_patches,
    parse_retouch_regions,
)
from . import session_core as _session_core
from . import session_effects as _session_effects
from . import session_regions as _session_regions
from .session_core import (
    FinetuneValues,
    _FINETUNE_CANONICAL,
    _FINETUNE_NAMES,
    _NEUTRAL_DEFAULT,
    _SessionCoreMixin,
    _new_op,
)
from .session_effects import _SessionEffectsMixin, _finetune_float
from .session_regions import _SessionRegionsMixin


@dataclass(frozen=True)
class EditSession(_SessionCoreMixin, _SessionEffectsMixin, _SessionRegionsMixin):
    """Immutábilis szerkesztési-lánc; a filters= érték objektum-reprezentációja.

    Minden metódus új EditSession-t ad vissza — mutáció tilos.
    """

    ops: tuple[FilterOp, ...] = ()


# A régi importútvonal marad a nyilvános adat-osztály és a metódusok gazdája.
FinetuneValues.__module__ = __name__
_session_core.EditSession = EditSession
_session_effects.EditSession = EditSession
_session_regions.EditSession = EditSession

# Ezek a nevek korábban közvetlenül a session modul importjai voltak.
_API_COMPAT = (
    Callable,
    dataclass,
    FilterOp,
    canonicalize_op,
    parse_filters,
    serialize_filters,
    validate_op_for_write,
    Rect64,
    decode_rect64,
    encode_rect64,
    EyeCircle64,
    REDEYE_FILTER_NAME,
    build_redeye_op,
    parse_redeye_regions,
    RETOUCH_FILTER_NAME,
    RetouchPatch,
    build_retouch_op,
    build_retouch_patches_op,
    parse_retouch_patches,
    parse_retouch_regions,
    _FINETUNE_CANONICAL,
    _FINETUNE_NAMES,
    _NEUTRAL_DEFAULT,
    _new_op,
    _finetune_float,
)

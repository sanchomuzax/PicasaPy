"""rect64 kódolás: 16 hex karakter = 4×16 bit (left, top, right, bottom).

Spec: docs/specs/picasa-ini-format.md — a Picasa elhagyja a vezető nullákat,
ezért dekódolás előtt kötelező a zfill(16).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SCALE = 65536
_WRAPPED = re.compile(r"^rect64\((.*)\)$")
_HEX = re.compile(r"^[0-9a-fA-F]{1,16}$")


@dataclass(frozen=True)
class Rect64:
    """Relatív [0.0..1.0] koordinátájú téglalap (crop, arc-régió)."""

    left: float
    top: float
    right: float
    bottom: float


def decode_rect64(value: str) -> Rect64:
    """`3f84...` vagy `rect64(3f84...)` alak dekódolása."""
    inner = value.strip()
    wrapped = _WRAPPED.match(inner)
    if wrapped:
        inner = wrapped.group(1)
    if not _HEX.match(inner):
        raise ValueError(f"Érvénytelen rect64 érték: {value!r}")
    padded = inner.zfill(16)
    left, top, right, bottom = (
        int(padded[i : i + 4], 16) / _SCALE for i in range(0, 16, 4)
    )
    return Rect64(left, top, right, bottom)


def encode_rect64(rect: Rect64) -> str:
    """16 hex jegyű érték, vezető nullákkal — bitre pontos visszaírhatóság."""
    coords = (rect.left, rect.top, rect.right, rect.bottom)
    for coord in coords:
        if not 0.0 <= coord <= 1.0:
            raise ValueError(f"rect64 koordináta a [0..1] tartományon kívül: {coord}")
    return "".join(f"{min(round(c * _SCALE), _SCALE - 1):04x}" for c in coords)

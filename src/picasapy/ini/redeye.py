"""Vörösszem-régiók a `filters=` láncban (#445) — PicasaPy-SAJÁT kiterjesztés.

SAJÁT FUNKCIÓ (#445): a lenti `rect64(...)` paraméterezés a mi kódolásunk,
nem igazolt bináris-formátum — a bináris-egyezés erre a paraméterezésre nem
vonatkozik (lista: docs/decisions/vedett-sajat-funkciok.md).

Az eredeti Picasa `redeye=1;` alakot ír: hogy a kézzel megjelölt szemek
koordinátái nála milyen bájtformában élnek, **nem derült ki** a binárisból
(nincs `redeye64(`-szerű formátum-string) — ez a #371 nyitott kérdése.

Amit viszont a bináris kimondott (#445): a vörösszem-eszköz
**automatikus ÉS kézi** — az automatika lefut, a felhasználó pedig utólag
pótolja, amit a gép kihagyott: *„You can also draw a square around any red
eye that Picasa may have missed."*

Ezért itt a `retouch=` v1 alakjának bevált mintáját követjük (ld.
`picasapy.ini.retouch`): `redeye=1[,rect64(...)…]` — az első paraméter az
engedélyező `1` flag, a továbbiak a kézzel megjelölt szemek téglalapjai
`rect64`-ben. Paraméter nélkül a bejegyzés bájtra ugyanaz, mint a valódi
Picasáé (`redeye=1;`), tehát a kétirányú kompatibilitás sértetlen: ha a
felhasználó nem jelöl kézzel semmit, a Picasa a sajátjaként olvassa vissza.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import Rect64, decode_rect64, encode_rect64

REDEYE_FILTER_NAME = "redeye"
_SCALE = 65536
_EYE64 = re.compile(r"^eye64\(([0-9a-fA-F]{12})\)$")
_AUTO_FULL_IMAGE = "autofull64()"


@dataclass(frozen=True)
class EyeCircle64:
    """Normalizált szemkör: x/w, y/h, sugár/min(w,h), mind [0..1]."""

    x: float
    y: float
    radius: float


def encode_eye64(circle: EyeCircle64) -> str:
    """Saját `eye64` kódolás három 16 bites normalizált koordinátával."""
    coords = (circle.x, circle.y, circle.radius)
    for coord in coords:
        if not 0.0 <= coord <= 1.0:
            raise ValueError(f"eye64 koordináta a [0..1] tartományon kívül: {coord}")
    values = (min(round(coord * _SCALE), _SCALE - 1) for coord in coords)
    return f"eye64({''.join(f'{value:04x}' for value in values)})"


def decode_eye64(value: str) -> EyeCircle64:
    """`eye64(xxxxxxxxxxxx)` alak dekódolása normalizált szemkörré."""
    match = _EYE64.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"Érvénytelen eye64 érték: {value!r}")
    digits = match.group(1)
    x, y, radius = (
        int(digits[index : index + 4], 16) / _SCALE
        for index in range(0, 12, 4)
    )
    return EyeCircle64(x, y, radius)


def _extra_params(op: FilterOp) -> tuple[str, ...]:
    if not op.matches(REDEYE_FILTER_NAME):
        raise ValueError(f"Nem redeye bejegyzés: {op.name!r}")
    params = op.params[1:]
    for param in params:
        if param.startswith("eye64("):
            decode_eye64(param)
        elif param == _AUTO_FULL_IMAGE:
            continue
        else:
            decode_rect64(param)
    return params


def parse_redeye_regions(op: FilterOp) -> tuple[Rect64, ...]:
    """A kézzel megjelölt szemek téglalapjai (paraméter nélkül üres tuple).

    Érvénytelen `rect64`-nél `ValueError` — a hívó (`render.chain`) a
    #301-elv szerint az EGÉSZ bejegyzést hagyja ki, nem a teljes láncot.
    """
    return tuple(
        decode_rect64(param)
        for param in _extra_params(op)
        if not param.startswith("eye64(") and param != _AUTO_FULL_IMAGE
    )


def parse_redeye_eye_circles(
    op: FilterOp, width: int, height: int
) -> tuple[tuple[float, float, float], ...]:
    """A tárolt normalizált szemkörök pixelkoordinátákká alakítva."""
    if width <= 0 or height <= 0:
        raise ValueError("A redeye szemkörökhöz pozitív képméret kell")
    circles = (
        decode_eye64(param)
        for param in _extra_params(op)
        if param.startswith("eye64(")
    )
    return tuple(
        (circle.x * width, circle.y * height, circle.radius * min(width, height))
        for circle in circles
    )


def has_redeye_eye_circles(op: FilterOp) -> bool:
    return any(param.startswith("eye64(") for param in _extra_params(op))


def redeye_uses_full_image_fallback(op: FilterOp) -> bool:
    return _AUTO_FULL_IMAGE in _extra_params(op)


def build_redeye_op(
    regions: tuple[Rect64, ...],
    *,
    eye_circles: tuple[EyeCircle64, ...] = (),
    full_image_fallback: bool = False,
) -> FilterOp:
    """`FilterOp` a vörösszem-bejegyzéshez.

    Régió NÉLKÜL a bejegyzés `redeye=1` — bájtra a valódi Picasa alakja.
    """
    params = ["1", *(encode_rect64(region) for region in regions)]
    params.extend(encode_eye64(circle) for circle in eye_circles)
    if full_image_fallback:
        params.append(_AUTO_FULL_IMAGE)
    return FilterOp(REDEYE_FILTER_NAME, tuple(params))

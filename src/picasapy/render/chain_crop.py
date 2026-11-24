"""A képszekció `crop=` értéke és a lánc `crop64` elemeinek összehangolása.

A `chain.py`-ból kiemelve (a render-lánc moduljainak 800 soros plafonja miatt);
a `picasapy.render.chain.normalize_crop_ops` név továbbra is él.
"""

from __future__ import annotations

import logging
import threading

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64

# a naplózó neve marad a régi, hogy a meglévő naplószűrők ne változzanak
_log = logging.getLogger("picasapy.render.chain")
_CROP_WARNING_LOCK = threading.Lock()
_CROP_WARNINGS: set[tuple[str, str]] = set()


def normalize_crop_ops(
    ops: tuple[FilterOp, ...],
    crop: str | None,
    *,
    crop_ini_readable: bool = True,
    warning_key: str | None = None,
) -> tuple[FilterOp, ...]:
    """A képszekció `crop=` értékéhez igazítja a `crop64` előzményeket.

    A szabály a #4008 óta exportban használt viselkedés: olvasható ini és
    hiányzó `crop=` mellett minden láncbeli `crop64` kimarad; érvényes kulcs
    mellett az utolsó `crop64` a helyén a kulcs értékére áll. A lánc többi
    tagja és eredeti sorrendje változatlan. Hibás kulcs vagy olvashatatlan
    ini esetén a teljes lánc marad meg; az ini-olvasó naplóz, ha szükséges.
    Hibás crop= esetén képenként legfeljebb egyszer figyelmeztetünk.

    Ez csak a lánc előkészítése; a renderelés továbbra is az
    `apply_filters(..., mert_sorrend=True)` mért sorrendjében fut.
    """
    if not crop_ini_readable:
        return ops

    crop_indices = [index for index, op in enumerate(ops) if op.name == "crop64"]
    if crop is None:
        return tuple(op for op in ops if op.name != "crop64")

    try:
        current_rect = decode_rect64(crop)
    except ValueError:
        fallback = (
            "a lánc utolsó crop64 elemére esünk vissza"
            if crop_indices
            else "nem alkalmazunk kivágást"
        )
        warning = ("invalid-crop", warning_key or "<unknown>")
        with _CROP_WARNING_LOCK:
            first_warning = warning not in _CROP_WARNINGS
            _CROP_WARNINGS.add(warning)
        if first_warning:
            _log.warning("Érvénytelen crop= érték (%r); %s", crop, fallback)
        return ops

    if not crop_indices:
        return ops

    last_index = crop_indices[-1]
    last_crop = ops[last_index]
    try:
        last_rect = decode_rect64(last_crop.params[1])
    except (IndexError, ValueError):
        last_rect = None
    if last_rect == current_rect:
        return ops

    params = list(last_crop.params)
    if len(params) < 2:
        params = ["1", crop]
    else:
        params[1] = crop
    updated = list(ops)
    updated[last_index] = FilterOp(last_crop.name, tuple(params))
    return tuple(updated)

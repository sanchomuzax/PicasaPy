"""#4899: a QuantizePalette mintasor-határa float32 szerint, natív byte-goldenekkel."""

from __future__ import annotations

import base64
import math
import random
import zlib

import numpy as np
import pytest

from picasapy.render import quantize_palette as qp


# A /tmp/claude-1000/kd-r626q/verify_full.py determinisztikus forrásaihoz
# tartozó modellkimenetek RGB-sorrendben; mind a 18 eset natív futással
# bájtra egyezett a specifikáció mérési jegyzete szerint.
_NATIVE_CASES = (
    (6, 5, 2), (6, 5, 8), (6, 5, 30),
    (7, 4, 8), (7, 4, 16),
    (5, 11, 8), (13, 9, 8), (17, 5, 30), (21, 8, 2),
    (30, 40, 16), (11, 7, 8), (85, 4, 8), (121, 3, 16), (20, 2, 8),
    (5, 5, 8), (3, 3, 8), (10, 10, 8), (51, 49, 8),
)
_NATIVE_GOLDEN_B64 = (
    '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'
    'kvV/ARVjfIU='
)
_NATIVE_GOLDEN = zlib.decompress(base64.b64decode(_NATIVE_GOLDEN_B64))


def _forras_rgb(width: int, height: int) -> np.ndarray:
    rng = random.Random(626)
    bgr = np.array(
        [tuple(rng.randrange(256) for _ in range(3)) for _ in range(width * height)],
        dtype=np.uint8,
    ).reshape(height, width, 3)
    return bgr[..., ::-1].copy()


def _y1(width: int, height: int) -> int:
    lepes = np.float32(width / 50.0)
    reciprok = np.float32(np.float32(1.0) / lepes)
    return min(50, math.floor(float(np.float32(height) * reciprok)))


@pytest.mark.parametrize(
    ("width", "height"),
    tuple(dict.fromkeys((width, height) for width, height, _ in _NATIVE_CASES)),
    ids=lambda value: str(value),
)
def test_mintakep_a_float32_sorhatarig_mintazik(width: int, height: int) -> None:
    kep = _forras_rgb(width, height)
    lepes = np.float32(width / 50.0)
    hatar = _y1(width, height)

    minta = qp.mintakep(kep)
    racs = qp.pontminta_racs(kep, 50, 50, float(lepes), float(lepes))

    np.testing.assert_array_equal(minta[:hatar], racs[:hatar])
    assert not minta[hatar:].any(), f"a {hatar}. sor után a natív minta fekete"


@pytest.mark.parametrize(
    ("width", "height", "steps"),
    _NATIVE_CASES,
    ids=lambda value: str(value),
)
def test_kvantal_byteegyezik_a_natív_kimenettel(width: int, height: int, steps: int) -> None:
    kep = _forras_rgb(width, height)
    index = _NATIVE_CASES.index((width, height, steps))
    kezdet = sum(w * h * 3 for w, h, _ in _NATIVE_CASES[:index])
    veg = kezdet + width * height * 3
    vart = np.frombuffer(_NATIVE_GOLDEN[kezdet:veg], dtype=np.uint8).reshape(height, width, 3)

    np.testing.assert_array_equal(qp.kvantal(kep, steps), vart)

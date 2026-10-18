"""#5299: a láncban utoljára írt alfa a Polaroid belső képterületét vezérli."""

# rontás-kontroll: picasapy.render.chain._ALPHA_TRANSPARENT = 255 → 1 failed.

from __future__ import annotations

import numpy as np

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.glimmer_frame_ops import drop_shadow_padding


HATTER = (0xE2, 0xE2, 0xE2)


def _kep() -> np.ndarray:
    y, x = np.indices((64, 64))
    return np.stack(
        (40 + x * 2, 30 + y * 3, 180 + (x + y) % 60), axis=-1
    ).astype(np.uint8)


def _foto_kozepe(kep: np.ndarray) -> tuple[int, int]:
    """A 0°-os Polaroidban a fotó belsejének egy szöveg/keret nélküli pontja."""
    height, width = kep.shape[:2]
    side = min(height, width)
    border = round(side * 0.0645)
    top_border = round(side * 0.0968)
    _, _, (pad_left, pad_top, _, _) = drop_shadow_padding(3, 90.0, 8)
    return (
        pad_top + top_border + side // 2,
        pad_left + border + side // 2,
    )


def test_dir_sat_utan_a_polaroid_atlatszo_fotot_hatterre_kompozital() -> None:
    source = _kep()
    chain = parse_filters(
        "dir_sat=1,0.35,-0.2;Polaroid=1,0.000000,00e2e2e2;"
    )

    rendered, skipped = apply_filters(source, chain)

    assert skipped == ()
    y, x = _foto_kozepe(source)
    np.testing.assert_array_equal(rendered[y, x], HATTER)


def test_colortemp_utan_a_polaroid_megtartja_a_fotot() -> None:
    source = _kep()
    chain = parse_filters(
        "colortemp=1,0.125,0;Polaroid=1,0.000000,00e2e2e2;"
    )
    filtered, _ = apply_filters(source, chain[:-1])
    expected_photo = filtered[source.shape[0] // 2, source.shape[1] // 2]

    rendered, skipped = apply_filters(source, chain)

    assert skipped == ()
    y, x = _foto_kozepe(source)
    np.testing.assert_array_equal(rendered[y, x], expected_photo)

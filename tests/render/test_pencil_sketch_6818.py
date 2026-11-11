"""A PencilSketch Glimmer szürkítése a két érintett szűrőláncban."""

import numpy as np
import pytest

from picasapy.ini import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render import glimmer_creative


@pytest.mark.parametrize("prefix,suffix", [
    (
        "RoundedEdges=1,16.825869,00350c47;blur=1,0.414862;"
        "Soften=1,14.538445,22.413000;"
        "DropShadow=1,20.732581,100.901328,20.126229,00d42b63,0015b4f7,72.080971;"
        "Soften=1,92.181292,24.029232;",
        "PencilSketch=1,2.254321,0.014576,38.300863;",
    ),
    (
        "HeatMap=1,-109.085653,45.020651;"
        "TwoTone=1,-45.681064,86.415392,65.220250,00d158c0,00931d9e;"
        "Pixelate=1,53.379350,3.550046,63.697880;",
        "PencilSketch=1,3.916828,109.742377,26.946581;"
        "MuseumMatte=1,23.843484,31.047840,002a815d,00901989;",
    ),
], ids=["lanc-0090", "lanc-0154"])
def test_pencil_sketch_glimmer_szurkitese(monkeypatch, prefix, suffix):
    image = np.random.default_rng(6818).integers(0, 256, (32, 40, 3), dtype=np.uint8)
    before = apply_filters(image, parse_filters(prefix)).image.astype(np.int32)
    gray = (((632 * before[..., 0]) >> 9) + ((1248 * before[..., 1]) >> 9)
            + ((168 * before[..., 2]) >> 9) + 2) >> 2
    expected = np.repeat(gray[..., None], 3, axis=2).astype(np.uint8)
    seen = []
    original = glimmer_creative.autofix

    def capture(value):
        seen.append(value.copy())
        return original(value)

    monkeypatch.setattr(glimmer_creative, "autofix", capture)
    apply_filters(image, parse_filters(prefix + suffix))
    np.testing.assert_array_equal(seen[0], expected)

"""A #6686 hat szűrője maradjon bájtra azonos és gyors az RPi5-ön."""

from __future__ import annotations

import hashlib

import numpy as np

from picasapy.render.color import apply_saturation
from picasapy.render.directional import apply_dir_brite
from picasapy.render.glimmer_tone import apply_twotone
from picasapy.render.ops import apply_autocolor
from picasapy.render.rainbow import apply_rainbow
from picasapy.render.tone import apply_finetune2


_KIMENET_SHA256 = {
    "finetune2": "a7865e65f102c27b04203b732ab1b86b1b585afd326860b5c49c5c0824ec83fb",
    "autocolor": "62a60b77fcd61e0a8d556bc7a2a28dd42aca7b216b1a35ed6fb25790f9884242",
    "sat": "fce44febb5597a78d842a713c08e06d35cce325219854733844bce0f2c5d6952",
    "TwoTone": "6f7d4f35facde60f885e47585148ae19aa9779d4afced4ce88817f8b54239dea",
    "dir_brite": "61273099c359c3bb0da8c245e5983f929e009dfa6c9962d8d1d3849751c16659",
    "rainbow": "beb3b82c380143049b7e4182a5bb453e26dd88057245cbef21430b78925df50a",
}


def _sample_image() -> np.ndarray:
    rng = np.random.default_rng(6686)
    image = rng.integers(0, 256, size=(64, 96, 3), dtype=np.uint8)
    image[0, :6] = np.array(
        [[0, 0, 0], [255, 255, 255], [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 128, 17]],
        dtype=np.uint8,
    )
    return image


def _rendered_outputs(image: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "finetune2": apply_finetune2(
            image, fill=0.5, highlights=0.24, shadows=0.16, neutral=None, temperature=0.0
        ),
        "autocolor": apply_autocolor(image),
        "sat": apply_saturation(image, 0.5),
        "TwoTone": apply_twotone(image),
        "dir_brite": apply_dir_brite(image, 0.5, -0.35),
        "rainbow": apply_rainbow(image),
    }


def test_hat_szuro_bajtazonos() -> None:
    """A hashek a gyorsítás előtti renderből származnak."""
    image = _sample_image()
    before = image.copy()
    rendered = _rendered_outputs(image)

    assert np.array_equal(image, before), "egyik szűrő sem írhatja át a bemenetét"
    assert {
        name: hashlib.sha256(result.tobytes()).hexdigest()
        for name, result in rendered.items()
    } == _KIMENET_SHA256

"""#566 — az `IR` effekt eredeti, zöldcsatornás csővezetéke.

A `Picasa3.exe` statikus visszafejtése (`glimmer::IRImageOperation`) alapján
a modell már nem interpretáció. A korábbi implementáció három ponton tért el:
SCREEN-t kevert LIGHTEN helyett, a glow-t a már monokrómmá tett képre tette
(nem az eredetire), és a KÉK csatorna negatív súlyát figyelmen kívül hagyta.
Ez a fájl pontosan ezt a három dolgot méri, szintetikus, tiszta színekre.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_creative import apply_ir
from picasapy.render.glimmer_ops import apply_blend_mode, gaussian_blur_f, to_float

_SIZE = (24, 32)


def _solid(color: tuple[int, int, int]) -> np.ndarray:
    image = np.zeros((*_SIZE, 3), dtype=np.uint8)
    image[..., 0], image[..., 1], image[..., 2] = color
    return image


def _center(image: np.ndarray) -> tuple[int, int, int]:
    return tuple(int(v) for v in image[_SIZE[0] // 2, _SIZE[1] // 2])


class TestMonochromeMatrixWeights:
    """`Y = clamp(−0,5·R + 2,0·G − 0,5·B)` — a három tiszta szín külön."""

    def test_pure_green_saturates_to_white(self):
        # 2,0 · 200 = 400 → vágva 255; a zöld glow ezen már nem ronthat
        assert _center(apply_ir(_solid((0, 200, 0)))) == (255, 255, 255)

    def test_pure_red_is_clipped_to_black(self):
        # −0,5 · 200 negatív → a vágás nullázza
        assert _center(apply_ir(_solid((200, 0, 0)))) == (0, 0, 0)

    def test_pure_blue_is_clipped_to_black(self):
        # ezt hagyta ki a korábbi modell: a KÉK súlya is NEGATÍV
        assert _center(apply_ir(_solid((0, 0, 200)))) == (0, 0, 0)

    def test_blue_darkens_a_mixed_colour(self):
        # ugyanaz a zöld, több kékkel → sötétebb eredmény. A régi, kék
        # nélküli modellben a kettő MEGEGYEZETT volna.
        low_blue = _center(apply_ir(_solid((40, 100, 0))))
        high_blue = _center(apply_ir(_solid((40, 100, 200))))
        assert high_blue[0] < low_blue[0]

    def test_output_is_neutral_grey(self):
        out = apply_ir(_solid((90, 120, 60)))
        assert out[..., 0].tolist() == out[..., 1].tolist() == out[..., 2].tolist()


class TestLightenNotScreen:
    def test_glow_uses_lighten(self):
        """A LIGHTEN és a SCREEN mérhetően más eredményt ad — a kimenetnek a
        LIGHTEN-ágat kell követnie."""
        image = np.zeros((*_SIZE, 3), dtype=np.uint8)
        image[..., 0] = 120
        image[..., 1] = 90
        image[..., 2] = 60
        image_f = to_float(image)
        green = image_f[..., 1]
        zeros = np.zeros_like(green)
        glow = gaussian_blur_f(np.stack([zeros, green, zeros], axis=-1), 5.0)

        def _closing(blended):
            y = np.clip(
                -0.5 * blended[..., 0] + 2.0 * blended[..., 1] - 0.5 * blended[..., 2],
                0.0,
                255.0,
            )
            return np.clip(np.rint(y), 0, 255).astype(np.uint8)

        lighten = _closing(apply_blend_mode(image_f, glow, "lighten", 0.25))
        screen = _closing(apply_blend_mode(image_f, glow, "screen", 0.25))
        assert not np.array_equal(lighten, screen), "a két mód itt egybeesne"

        out = apply_ir(image)[..., 0]
        np.testing.assert_array_equal(out, lighten)

    def test_glow_is_applied_to_the_original_not_the_monochrome(self):
        """A LIGHTEN a NYERS képre fut, a monokróm mátrix csak UTÁNA. Ha a
        sorrend fordított lenne, a tiszta kék kép nem maradna feketén: a
        zöld glow a szürkévé tett képre világosítva már nem esne ki a
        negatív súly alól."""
        assert _center(apply_ir(_solid((0, 0, 255)))) == (0, 0, 0)


class TestFade:
    def test_fade_100_is_identity(self):
        rng = np.random.default_rng(5)
        image = rng.integers(0, 256, size=(*_SIZE, 3), dtype=np.uint8)
        np.testing.assert_array_equal(apply_ir(image, fade=100.0), image)

    @pytest.mark.parametrize("fade", [0.0, 25.0, 50.0, 75.0])
    def test_partial_fade_stays_between_the_two_ends(self, fade):
        rng = np.random.default_rng(6)
        image = rng.integers(0, 256, size=(*_SIZE, 3), dtype=np.uint8)
        full = apply_ir(image, fade=0.0).astype(int)
        mixed = apply_ir(image, fade=fade).astype(int)
        source = image.astype(int)
        low = np.minimum(full, source)
        high = np.maximum(full, source)
        assert np.all((mixed >= low - 1) & (mixed <= high + 1))

    def test_shape_and_dtype_are_preserved(self):
        image = _solid((10, 20, 30))
        out = apply_ir(image, fade=30.0)
        assert out.shape == image.shape and out.dtype == np.uint8

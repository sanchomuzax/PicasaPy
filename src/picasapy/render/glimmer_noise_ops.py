"""A Glimmer zajrétegének előállítása és keverése."""

from __future__ import annotations

from picasapy.render import nativ_noise
from picasapy.render.curves import validate_image
from picasapy.render.glimmer_blend_ops import (
    BlendMode,
    apply_blend_mode,
    to_float,
    to_uint8,
)
from picasapy.render.nativ_noise import ALAP_CSATORNAK
import numpy as np



# --- Zaj (Noise) ---------------------------------------------------------


def noise_layer(
    height: int,
    width: int,
    seed: int,
    low: float,
    high: float,
    grayscale: bool,
    channel_options: int = ALAP_CSATORNAK,
) -> np.ndarray:
    """`Noise`: a `NoiseImageOperation` natív zajrétege float32 [0,255] —
    MT19937 a Picasa 1664525-ös magvetésével, képpontonként egy húzás
    (#3736, ld. `nativ_noise.noise_layer`). Adott `seed` → a Picasáéval
    képpontra azonos zajminta.
    """
    return nativ_noise.noise_layer(height, width, seed, low, high, grayscale, channel_options)



def _blend_noise(
    image: np.ndarray, noise: np.ndarray, blend_alpha: float, blend_mode: BlendMode | int
) -> np.ndarray:
    return to_uint8(apply_blend_mode(to_float(image), noise, blend_mode, blend_alpha))



def apply_noise(
    image: np.ndarray,
    seed: int,
    low: float,
    high: float,
    grayscale: bool,
    blend_alpha: float,
    blend_mode: BlendMode | int,
) -> np.ndarray:
    """A natív zajréteg generálása és `blend_mode`/`blend_alpha` szerinti
    keverése (a lánc `NoiseImageOperation`-je, #3736). A `blend_mode` név
    vagy a natív módtábla sorszáma (`BLEND_MODE_BY_INDEX`)."""
    validate_image(image)
    height, width = image.shape[:2]
    noise = noise_layer(height, width, seed, low, high, grayscale)
    return _blend_noise(image, noise, blend_alpha, blend_mode)

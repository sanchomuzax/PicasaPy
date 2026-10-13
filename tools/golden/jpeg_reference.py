"""Referenciával egyező JPEG-kódolás a mérőszett összevetéséhez (#4940).

A Picasa-export tömörített JPEG, a mi renderünk nyers RGB. A nyers ΔE a JPEG-zajt
eltérésnek látja, ezért a mi képünket a referencia mintavételezésével és
kvantálótábláival kódoljuk, és a dekódolt eredményt hasonlítjuk össze.
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image, JpegImagePlugin


def reference_jpeg_settings(reference: Path) -> dict | None:
    """A referencia JPEG mintavételezése és kvantálótáblái; nem JPEG-nél None."""
    try:
        with Image.open(reference) as img:
            if img.format != "JPEG":
                return None
            return {
                "subsampling": JpegImagePlugin.get_sampling(img),
                "qtables": {key: list(table) for key, table in img.quantization.items()},
            }
    except OSError:
        return None


def jpeg_encode_like(rgb: np.ndarray, settings: dict) -> bytes:
    """A nyers RGB-t a megadott mintavételezéssel és kvantálótáblákkal kódolja."""
    buffer = io.BytesIO()
    Image.fromarray(rgb).save(
        buffer,
        "JPEG",
        subsampling=settings["subsampling"],
        qtables=settings["qtables"],
    )
    return buffer.getvalue()


def encode_like_reference(rgb: np.ndarray, reference: Path) -> np.ndarray:
    """A képet a referencia JPEG-kódolásával dekódolva adja vissza.

    Nem JPEG referenciánál a bemenet változatlanul jön vissza.
    """
    settings = reference_jpeg_settings(reference)
    if settings is None:
        return rgb
    decoded = Image.open(io.BytesIO(jpeg_encode_like(rgb, settings)))
    return np.asarray(decoded.convert("RGB"))

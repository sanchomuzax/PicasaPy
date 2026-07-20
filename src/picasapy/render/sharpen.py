"""Élesítés: unsharp / unsharp2.

Mért modell (`docs/specs/filters-decoded.md`, golden 4. kör): Gauss-alapú
unsharp mask, σ≈1,0 px, erősítés ≈1,21·s; az `unsharp=1` (v1) bitre azonos
az `unsharp2=1,0.600000`-val. A kernel pontos alakjának finomítása nyitott.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.render.curves import validate_image

_UNSHARP_SIGMA = 1.0
_UNSHARP_AMOUNT_PER_STRENGTH = 1.21

#: A paraméter nélküli (v1) unsharp mért egyenértékese: unsharp2 s=0,6.
UNSHARP_V1_STRENGTH = 0.6


def apply_unsharp(
    image: np.ndarray, strength: float = UNSHARP_V1_STRENGTH
) -> np.ndarray:
    """Unsharp mask: `ki = be + 1,21·s·(be − gauss(be, σ=1))`, klippel."""
    validate_image(image)
    if strength < 0:
        raise ValueError(f"Az élesítés erőssége nem lehet negatív: {strength}")
    if strength == 0:
        return image.copy()
    blurred = cv2.GaussianBlur(image, (0, 0), _UNSHARP_SIGMA)
    amount = _UNSHARP_AMOUNT_PER_STRENGTH * strength
    # float32 munkatér (#140): a 8 bites kimenethez elegendő pontosság,
    # fele akkora memóriaforgalommal, mint a float64
    image_f = image.astype(np.float32)
    sharpened = image_f + np.float32(amount) * (image_f - blurred.astype(np.float32))
    return np.clip(np.rint(sharpened), 0, 255).astype(np.uint8)

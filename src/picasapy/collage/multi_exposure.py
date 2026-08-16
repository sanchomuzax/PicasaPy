"""A Többszörös exponálás (`multiexp`) — a legegyszerűbb elrendezés (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.4 (`0x00841860`,
`0x00409ea0`).

Nincs pozíciószámítás: **minden kép a teljes lapra kerül**, oldalarányhoz
igazítva, és egymásra keveredik. A magyar leírása az eredetiben: „Képek
egymás tetejére helyezése."

> ⚠️ **Egy pont, ahol a dekompilált kód olvasata nem egyértelmű.** A keverő
> hívás súlyai `1.0f, 1.0f`. Puszta összeadásként értelmezve néhány kép
> után minden kifehéredne, ami se a funkció nevével, se a felület
> előrehaladás-jelzésével („Képek egymásra helyezése — %d / %d feldolgozva")
> nem fér össze. Ezért **egyenlő súlyú keverést** valósítunk meg: minden kép
> ugyanakkora súllyal (`1/N`) szerepel a végeredményben — ez adja a
> többszörös exponálás jellegzetes, áttetsző hatását. Ha egyszer előkerül
> egy valódi `multiexp` minta, ez egyetlen sorban javítható.
"""

from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

from .fitting import fit_inside


def multi_exposure_size(
    src_width: int, src_height: int, page_width: int, page_height: int
) -> tuple[int, int]:
    """A kép mérete a lapra igazítva — a közös illesztővel (1.9.1)."""
    return fit_inside(src_width, src_height, page_width, page_height)


def _centered(
    image: np.ndarray, page_width: int, page_height: int
) -> tuple[np.ndarray, int, int]:
    """A lapra igazított kép + a bal felső sarka a lapon (középre igazítva)."""
    source_height, source_width = image.shape[:2]
    width, height = multi_exposure_size(
        source_width, source_height, page_width, page_height
    )
    interpolation = (
        cv2.INTER_AREA if width < source_width else cv2.INTER_LINEAR
    )
    resized = cv2.resize(image, (width, height), interpolation=interpolation)
    return (resized, (page_width - width) // 2, (page_height - height) // 2)


def blend_multi_exposure(
    images: Sequence[np.ndarray],
    page_width: int,
    page_height: int,
    background: tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    """A képek egymásra keverése egyenlő súllyal; ÚJ tömböt ad vissza.

    A lapra nem érő szélek a háttérszínt kapják — így egy álló és egy fekvő
    kép keveréke is a teljes lapot kitölti."""
    if not images:
        raise ValueError("A többszörös exponáláshoz legalább egy kép kell.")
    if page_width < 1 or page_height < 1:
        raise ValueError(f"Érvénytelen lapméret: {page_width}×{page_height}")

    accumulator = np.zeros((page_height, page_width, 3), dtype=np.float64)
    for image in images:
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("A keveréshez háromcsatornás képek kellenek.")
        layer = np.full(
            (page_height, page_width, 3),
            np.array(background, dtype=np.float64),
            dtype=np.float64,
        )
        resized, x, y = _centered(image, page_width, page_height)
        layer[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
        accumulator += layer

    averaged = accumulator / len(images)
    return np.clip(averaged + 0.5, 0.0, 255.0).astype(np.uint8)


__all__ = ["blend_multi_exposure", "multi_exposure_size"]

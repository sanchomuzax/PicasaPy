"""A Picasa `filters=` lánc gyakori-javítás műveletei numpy/OpenCV képeken.

Minden függvény TISZTA: RGB `uint8` numpy tömböt (H, W, 3 alakú) kap, és
ÚJ tömböt ad vissza — a bemenetet sosem mutálja (immutabilitás).

Az `enhance`/`autolight`/`autocolor` pontos Picasa-algoritmusa nem publikus
(ld. `docs/specs/picasa-ini-format.md`), ezért itt dokumentált,
pixelhű-validálásra még nem alkalmas MVP-közelítéseket implementálunk.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.ini.rect64 import Rect64

_AUTOLIGHT_LOW_PERCENTILE = 0.5
_AUTOLIGHT_HIGH_PERCENTILE = 99.5
_AUTOCOLOR_WHITE_PERCENTILE = 99.0
_REDEYE_DOMINANCE_RATIO = 1.4
_REDEYE_MIN_RED = 60


def _validate_image(image: np.ndarray) -> None:
    """RGB uint8 (H, W, 3) alak-ellenőrzés — hibás bemenetnél ValueError."""
    if not isinstance(image, np.ndarray):
        raise ValueError(f"A kép numpy.ndarray kell legyen, nem {type(image)!r}")
    if image.dtype != np.uint8:
        raise ValueError(f"A kép dtype-ja uint8 kell legyen, nem {image.dtype}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"A kép alakja (H, W, 3) kell legyen, nem {image.shape}")


def _rect_to_pixels(rect: Rect64, width: int, height: int) -> tuple[int, int, int, int]:
    """Relatív [0..1] Rect64 → pixel-koordináták (left, top, right, bottom)."""
    left = round(rect.left * width)
    top = round(rect.top * height)
    right = round(rect.right * width)
    bottom = round(rect.bottom * height)
    return left, top, right, bottom


def apply_crop(image: np.ndarray, rect: Rect64) -> np.ndarray:
    """Kivágás a relatív [0..1] `rect` koordináták alapján, pixelre pontosan.

    Üres (nulla szélességű/magasságú) kivágásnál ValueError.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    left, top, right, bottom = _rect_to_pixels(rect, width, height)
    if right <= left or bottom <= top:
        raise ValueError(
            f"Üres kivágás: rect={rect} -> pixel=({left}, {top}, {right}, {bottom})"
        )
    return image[top:bottom, left:right].copy()


def apply_tilt(image: np.ndarray, angle: float, scale: float) -> np.ndarray:
    """Döntés (forgatás) a kép közepe körül + skálázás, bilineáris mintavétellel.

    `angle` radiánban értendő (a hívó felelőssége a Picasa nyers
    szög-paraméterének radiánra váltása). A kimenet mérete megegyezik a
    bemenetével (levágás/kitöltés a warpAffine perem-viselkedése szerint).
    """
    _validate_image(image)
    if scale <= 0:
        raise ValueError(f"A skála pozitív kell legyen, nem {scale}")
    height, width = image.shape[:2]
    center = (width / 2.0, height / 2.0)
    angle_deg = np.degrees(angle)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, scale)
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def apply_autolight(image: np.ndarray) -> np.ndarray:
    """Auto kontraszt: hisztogram-széthúzás a luminancia 0.5-99.5 percentilisén,
    a színcsatornák arányos (közös) skálázásával."""
    _validate_image(image)
    luminance = (
        0.299 * image[..., 0].astype(np.float64)
        + 0.587 * image[..., 1].astype(np.float64)
        + 0.114 * image[..., 2].astype(np.float64)
    )
    low = np.percentile(luminance, _AUTOLIGHT_LOW_PERCENTILE)
    high = np.percentile(luminance, _AUTOLIGHT_HIGH_PERCENTILE)
    if high <= low:
        return image.copy()
    scale = 255.0 / (high - low)
    stretched = (image.astype(np.float64) - low) * scale
    return np.clip(stretched, 0, 255).astype(np.uint8)


def apply_autocolor(image: np.ndarray) -> np.ndarray:
    """Auto fehéregyensúly: csatornánkénti 99. percentilis fehérpontra skálázás,
    clip 0..255 tartományra."""
    _validate_image(image)
    result = image.astype(np.float64)
    for channel in range(3):
        white_point = np.percentile(image[..., channel], _AUTOCOLOR_WHITE_PERCENTILE)
        if white_point <= 0:
            continue
        factor = 255.0 / white_point
        result[..., channel] = result[..., channel] * factor
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_enhance(image: np.ndarray) -> np.ndarray:
    """„Jó napom van" (I'm Feeling Lucky): autolight + autocolor egymás után.

    A Picasa pontos enhance-algoritmusa nem publikus (ld. spec); ez a
    dokumentált MVP-közelítés, nem pixelhű reprodukció.
    """
    _validate_image(image)
    return apply_autocolor(apply_autolight(image))


def apply_redeye(
    image: np.ndarray, regions: tuple[Rect64, ...] = ()
) -> np.ndarray:
    """Vörösszem-eltávolítás a megadott régiókban (üres esetén az egész képen).

    Konzervatív színküszöb: a pixel akkor "vörösszem", ha a piros csatorna
    dominál a zöld és a kék felett (`R > _REDEYE_DOMINANCE_RATIO * G` és
    `R > _REDEYE_DOMINANCE_RATIO * B`) és `R >= _REDEYE_MIN_RED` — ez a
    küszöb a normál bőrtónusokat (ahol R, G, B közel esik egymáshoz)
    szándékosan nem érinti. A találati pixeleknél a piros csatornát a
    zöld/kék átlagára csillapítjuk.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    result = image.copy()

    if regions:
        mask = np.zeros((height, width), dtype=bool)
        for rect in regions:
            left, top, right, bottom = _rect_to_pixels(rect, width, height)
            mask[max(top, 0) : max(bottom, 0), max(left, 0) : max(right, 0)] = True
    else:
        mask = np.ones((height, width), dtype=bool)

    red = image[..., 0].astype(np.int32)
    green = image[..., 1].astype(np.int32)
    blue = image[..., 2].astype(np.int32)
    red_eye_mask = (
        mask
        & (red >= _REDEYE_MIN_RED)
        & (red > _REDEYE_DOMINANCE_RATIO * green)
        & (red > _REDEYE_DOMINANCE_RATIO * blue)
    )

    average_green_blue = ((green + blue) / 2).astype(np.uint8)
    result[..., 0] = np.where(red_eye_mask, average_green_blue, result[..., 0])
    return result

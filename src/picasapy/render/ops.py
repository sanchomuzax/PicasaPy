"""A Picasa `filters=` lánc gyakori-javítás műveletei numpy/OpenCV képeken.

Minden függvény TISZTA: RGB `uint8` numpy tömböt (H, W, 3 alakú) kap, és
ÚJ tömböt ad vissza — a bemenetet sosem mutálja (immutabilitás).

Az autolight/enhance a golden-elemzésben megfejtett algoritmus
(`docs/specs/filters-decoded.md`, 3. kör); az autocolor csillapítási
szabálya még nyitott, ott dokumentált közelítést használunk.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.ini.rect64 import Rect64
from picasapy.render.curves import (
    apply_channel_luts,
    apply_lut,
    lut_ramp,
    validate_image,
)

_REDEYE_DOMINANCE_RATIO = 1.4
_REDEYE_MIN_RED = 60

# Autocolor: a mért gainek a teljes szürkevilág-korrekció ~60–90%-a
# (golden 3–4. kör); a pontos csillapítási szabály még nyitott kérdés.
_AUTOCOLOR_DAMPING = 0.75

# „Jó napom van" / AutoFix vágási arányok — a valódi Picasa a hisztogramban
# DARABSZÁM-küszöbbel keresi a fekete/fehér pontot (#535), nem fix
# percentilissel; ez a két konstans egy MÉRÉSSEL igazolt közelítés (12
# referencia-képpáron: átlagos csatorna-eltérés 5,47/5,48 — ld.
# `sanchomuzax/picasapy-agent` privát repó `referencia/imfeellucky/`).
_ENHANCE_LOW_FRACTION = 0.005
_ENHANCE_HIGH_FRACTION = 0.002

_validate_image = validate_image


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
    """Auto kontraszt — megfejtett algoritmus (golden 3. kör).

    Globális min–max lineáris széthúzás, minden csatornára KÖZÖS
    transzformációval (a színegyensúly megmarad):
    `ki = clip((be − gmin)·255/(gmax − gmin))`.
    """
    _validate_image(image)
    global_min = int(image.min())
    global_max = int(image.max())
    if global_max <= global_min:
        return image.copy()
    scale = 255.0 / (global_max - global_min)
    # pontonkénti lineáris széthúzás → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, (lut_ramp() - global_min) * scale)


def apply_autocolor(image: np.ndarray) -> np.ndarray:
    """Auto fehéregyensúly — csillapított szürkevilág-korrekció.

    Mérés szerint (golden 3–4. kör) a csatornákat a szürke felé húzza, de
    nem teljesen; semleges bemeneten no-op. A csillapítás pontos szabálya
    még nyitott — itt `_AUTOCOLOR_DAMPING` arányú lineáris korrekció fut.
    """
    _validate_image(image)
    means = image.reshape(-1, 3).mean(axis=0)
    gray = float(means.mean())
    # csatornánkénti gain → csatornánkénti LUT (#140): képméret-független
    ramp = lut_ramp()
    luts = []
    for channel in range(3):
        channel_mean = float(means[channel])
        if channel_mean <= 0.0:
            luts.append(ramp)
            continue
        gain = 1.0 + _AUTOCOLOR_DAMPING * (gray / channel_mean - 1.0)
        luts.append(ramp * gain)
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


def _channel_black_white_points(
    image: np.ndarray, low_fraction: float, high_fraction: float
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Csatornánkénti fekete-/fehérpont a hisztogram DARABSZÁMA alapján.

    Csatornánként: a fekete pont az a legkisebb érték, aminél a kumulált
    darabszám már eléri a `low_fraction`·(össz-képpont) küszöböt; a
    fehérpont ugyanígy, felülről számolva `high_fraction`-nel. Ha ez üres
    (nem lenne érdemi tartomány), a csatorna azonosság marad (`(0, 255)`).
    """
    height, width = image.shape[:2]
    total_pixels = height * width
    low_count = total_pixels * low_fraction
    high_count = total_pixels * high_fraction
    points = []
    for channel in range(3):
        histogram, _ = np.histogram(image[..., channel], bins=256, range=(0, 256))
        cumulative_low = np.cumsum(histogram)
        low = int(np.searchsorted(cumulative_low, low_count))
        cumulative_high = np.cumsum(histogram[::-1])
        high_from_top = int(np.searchsorted(cumulative_high, high_count))
        high = 255 - high_from_top
        if high <= low:
            low, high = 0, 255
        points.append((low, high))
    return points[0], points[1], points[2]


def apply_channel_levels_stretch(
    image: np.ndarray,
    low_fraction: float = _ENHANCE_LOW_FRACTION,
    high_fraction: float = _ENHANCE_HIGH_FRACTION,
) -> np.ndarray:
    """Csatornánként KÜLÖN lineáris szinthúzás: `ki = (be − lo)·255/(hi − lo)`.

    Ez a „Jó napom van" (I'm Feeling Lucky) és az `AutoFix` megfejtett
    modellje (#535, 12 referencia-képpáron R² = 0,9995–1,0000 illesztéssel
    igazolva). **Azonosság-eset:** ha egy csatorna `lo`/`hi`-je már `0`/`255`
    (a csatorna kihasználja a teljes tartományt), azt a csatornát a Picasa
    NEM módosítja — itt sem változik semmi (bájtra azonos marad).
    """
    _validate_image(image)
    points = _channel_black_white_points(image, low_fraction, high_fraction)
    ramp = lut_ramp()
    luts = []
    for low, high in points:
        if low == 0 and high == 255:
            luts.append(ramp)
        else:
            luts.append((ramp - low) * 255.0 / (high - low))
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


def apply_enhance(image: np.ndarray) -> np.ndarray:
    """„Jó napom van" (I'm Feeling Lucky) — megfejtett modell (#535):

    csatornánként KÜLÖN, hisztogram-darabszám alapú lineáris szinthúzás
    (`apply_channel_levels_stretch`) — nincs benne gamma, S-görbe, helyi
    kontraszt vagy külön árnyék-/csúcsfény-emelés (ld. az adott függvény
    docstringjét a bizonyítékért).
    """
    _validate_image(image)
    return apply_channel_levels_stretch(image)


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

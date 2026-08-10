"""A Picasa `filters=` lánc gyakori-javítás műveletei numpy/OpenCV képeken.

Minden függvény TISZTA: RGB `uint8` numpy tömböt (H, W, 3 alakú) kap, és
ÚJ tömböt ad vissza — a bemenetet sosem mutálja (immutabilitás).

Az `autolight` (Auto Contrast), `autocolor` (Auto Colour) és `enhance` (Jó
napom van) mindhárom a #535/#540 mérésekben megfejtett, hisztogram-
darabszám alapú lineáris szinthúzás egy-egy változata — de HÁROM KÜLÖN
modell (#540, 12-12 referencia-képpáron mérve):

- `autolight`: KÖZÖS (mindhárom csatornán azonos) vágás — nincs
  fehéregyensúly-hatása.
- `autocolor`: csatornánként KÜLÖN vágás, de a csatornák egy KÖZÖS
  (a csatornánkénti vágópontok átlagából számolt) kimeneti tartományra
  simulnak — nem nyújtja mindegyiket önállóan 0..255-re (az a modell
  a mérésen jóval rosszabbul illeszkedett, ld. #540).
- `enhance` ("Jó napom van"): csatornánként KÜLÖN vágás, ÉS mindegyik
  önállóan a teljes 0..255 tartományra nyúlik (#535).
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

# Vágási arányok az autolight/autocolor/enhance hisztogram-darabszám alapú
# szinthúzásához — a valódi Picasa a hisztogramban DARABSZÁM-küszöbbel
# keresi a fekete/fehér pontot (#535), nem fix percentilissel; ez a két
# konstans egy MÉRÉSSEL igazolt közelítés, és a #540 szerint MINDHÁROM
# művelet ugyanezt használja (az összemérhetőség kedvéért — a pontos
# küszöbérték finomítása a #539 dolga). Ld. `sanchomuzax/picasapy-agent`
# privát repó `referencia/imfeellucky/`, `referencia/autocontrast/`,
# `referencia/autocolor/`.
_LEVELS_LOW_FRACTION = 0.005
_LEVELS_HIGH_FRACTION = 0.002

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


def _common_black_white_point(
    image: np.ndarray, low_fraction: float, high_fraction: float
) -> tuple[int, int]:
    """KÖZÖS (mindhárom csatornára egyenlő) fekete-/fehérpont a hisztogram
    DARABSZÁMA alapján — a három csatorna képpontjait EGY közös
    hisztogramba összeöntve (#540: az Auto Contrast mind a 12 referencia-
    képen azonos meredekséget adott mindhárom csatornán, szórás 0,001).
    Ha nem lenne érdemi tartomány, `(0, 255)` (azonosság-eset).
    """
    total_values = image.size
    low_count = total_values * low_fraction
    high_count = total_values * high_fraction
    histogram, _ = np.histogram(image, bins=256, range=(0, 256))
    cumulative_low = np.cumsum(histogram)
    low = int(np.searchsorted(cumulative_low, low_count))
    cumulative_high = np.cumsum(histogram[::-1])
    high_from_top = int(np.searchsorted(cumulative_high, high_count))
    high = 255 - high_from_top
    if high <= low:
        low, high = 0, 255
    return low, high


def apply_autolight(image: np.ndarray) -> np.ndarray:
    """Auto Contrast — megfejtett algoritmus (#540).

    KÖZÖS (mindhárom csatornára azonos) lineáris szinthúzás, a fekete-/
    fehérpontot a hisztogram DARABSZÁMA alapján keresve (ugyanaz a
    közelítés, mint a #535 „Jó napom van"-nál, `_LEVELS_LOW_FRACTION`/
    `_LEVELS_HIGH_FRACTION` küszöbbel): `ki = (be − lo)·255/(hi − lo)`,
    egyetlen `lo`/`hi` az egész képre. **Azonosság-eset:** ha a kép már
    kihasználja a teljes tartományt (`lo == 0` és `hi == 255`), a kimenet
    bájtra azonos a bemenettel.
    """
    _validate_image(image)
    low, high = _common_black_white_point(
        image, _LEVELS_LOW_FRACTION, _LEVELS_HIGH_FRACTION
    )
    if low == 0 and high == 255:
        return image.copy()
    scale = 255.0 / (high - low)
    # pontonkénti lineáris széthúzás → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, (lut_ramp() - low) * scale)


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


def apply_autocolor(image: np.ndarray) -> np.ndarray:
    """Auto Colour — **MUNKAHIPOTÉZIS, NEM megfejtett algoritmus** (#540).

    ⚠️ **Őszinte állapot:** ez a modell a referenciakészleten **rosszabb,
    mint ha meg sem csinálnánk az effektet.** Mért átlagos csatorna-
    eltérés a valódi Picasa-kimenettől (12 kép, `referencia/autocolor/`):

        az ÉRINTETLEN kép ...................... 5,29   ← a viszonyítás
        a régi (szürkevilág) közelítés ......... 7,82
        ez a változat .......................... 7,45

    Vagyis a mostani a réginél kevéssel jobb, de **mindkettő rosszabb az
    azonosságnál** — a valódi modell tehát NINCS megfejtve. Amit a mérés
    kizárt: a csatornánként önállóan 0..255-re nyújtó (enhance-szerű)
    modell **16,5**-öt ad, tehát az Auto Colour biztosan NEM fekete-/
    fehérpontra vágó szinthúzás. Az illesztett meredekségek 1,0 közeliek
    (0,78–1,47), és az illesztett `lo`/`hi` gyakran a [0,255] tartományon
    KÍVÜLRE esik — ez finom, csatornánkénti erősítés/eltolás felé mutat,
    nem vágásra. A megfejtés a #541 tárgya.

    Ami itt fut: csatornánként KÜLÖN fekete-/fehérpont (hisztogram-
    darabszám alapján, ugyanazokkal a küszöbökkel, mint az autolight/
    enhance), de a három csatorna egy KÖZÖS kimeneti tartományra (a
    vágópontok ÁTLAGÁRA) simul — ez tartja 7,45-nél a hibát.

    **Azonosság-eset:** semleges (R=G=B mindenütt) vagy már teljes
    tartományú bemeneten a három csatorna vágópontja (és így a célsáv is)
    megegyezik → a kimenet bájtra azonos a bemenettel.
    """
    _validate_image(image)
    points = _channel_black_white_points(
        image, _LEVELS_LOW_FRACTION, _LEVELS_HIGH_FRACTION
    )
    target_low = sum(point[0] for point in points) / 3.0
    target_high = sum(point[1] for point in points) / 3.0
    ramp = lut_ramp()
    luts = []
    for low, high in points:
        if high <= low or (low == target_low and high == target_high):
            luts.append(ramp)
        else:
            luts.append((ramp - low) * (target_high - target_low) / (high - low) + target_low)
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


def apply_channel_levels_stretch(
    image: np.ndarray,
    low_fraction: float = _LEVELS_LOW_FRACTION,
    high_fraction: float = _LEVELS_HIGH_FRACTION,
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

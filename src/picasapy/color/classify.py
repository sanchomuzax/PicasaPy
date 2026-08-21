"""Átlagszín → Picasa-féle 10 színnév besorolás (#383).

A Picasa `Picasa3.exe` string-táblájából előkerült 10 keresőtoken:

    color:red  color:orange  color:yellow  color:green  color:blue
    color:purple  color:pink  color:black  color:white  color:gray

A program mellette egy `avgcolor` mezőt is tárolt (a kép átlagszíne), és a
`color:kék`-féle keresés erre szűrt. A PONTOS Picasa-besorolási szabály
(a HSV-sávhatárok, a fekete/szürke/fehér és a "pink" különválasztásának
küszöbei) **nincs dokumentálva és nem mérhető** — a Picasa 2016 óta nem
elérhető. Az alábbi küszöbök ezért a **mi józan döntésünk**, nem
rekonstruált Picasa-viselkedés (ld. `docs/specs/picasa-ini-format.md`,
„Színkereső tokenek" — a disclaimer ott is szerepel).

Az osztályozás menete:
1. RGB → HSV.
2. Ha a telítettség (S) alacsony: akromatikus ág — `black`/`gray`/`white`
   a világosság (V) szerint.
3. Egyébként a "pink" külön eset: a bíbor-vörös átmeneti hue-sávban, de
   csak KÖZEPES telítettség és MAGAS világosság mellett (a Picasa "pink"-je
   a magas világosságú, visszafogott telítettségű rózsaszín, nem a tiszta
   bíbor/vörös).
4. Egyébként hue-sáv szerinti besorolás (`red`/`orange`/`yellow`/`green`/
   `blue`/`purple`).
"""

from __future__ import annotations

import colorsys
from collections.abc import Sequence

import numpy as np

# A Picasa 10 színtokenje, angolul (ez a kanonikus, tárolt alak).
COLOR_TOKENS: tuple[str, ...] = (
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
    "black",
    "white",
    "gray",
)

# Magyar alakok a kereséshez (`szín:kék`) — SAJÁT fordítás, a hivatalos
# Picasa-magyar terminológiában (docs/specs/picasa-hu-terminology.md) ez a
# 10 szó nem szerepel, mert a `color:` funkció eddig ismeretlen volt.
_HU_NAMES: dict[str, str] = {
    "piros": "red",
    "vörös": "red",
    "narancs": "orange",
    "narancssárga": "orange",
    "sárga": "yellow",
    "zöld": "green",
    "kék": "blue",
    "lila": "purple",
    "bíbor": "purple",
    "rózsaszín": "pink",
    "fekete": "black",
    "fehér": "white",
    "szürke": "gray",
}

# token → kanonikus (angol) token; az angol nevek önmagukra képeznek.
TOKEN_ALIASES: dict[str, str] = {name: name for name in COLOR_TOKENS} | _HU_NAMES


def resolve_color_alias(word: str) -> str | None:
    """Egy kereső-szó (angol vagy magyar színnév) → kanonikus token, vagy
    `None`, ha nem egy ismert színnév (casefold-os összehasonlítás)."""
    return TOKEN_ALIASES.get(word.strip().casefold())


# --- HSV küszöbök (a mi döntésünk, ld. a modul-docstringet) -------------

# Akromatikus ág: ez alatti telítettségnél a hue zajos/értelmetlen.
_ACHROMATIC_SAT_MAX = 0.12
_BLACK_VAL_MAX = 0.20
_WHITE_VAL_MIN = 0.85

# "pink": a bíbor→vörös átmeneti hue-ív (fokban), amelyben — ha a
# telítettség közepes és a világosság magas — rózsaszínnek számít a kép
# (pl. #ffc0cb ≈ 349,5°, S≈0,25, V=1,0).
_PINK_HUE_LO = 330.0
_PINK_HUE_HI = 355.0
_PINK_SAT_MIN = 0.12
_PINK_SAT_MAX = 0.55
_PINK_VAL_MIN = 0.55

# Hue-sávhatárok (fokban) a fennmaradó 6 kromatikus névre. A `red` a 0°
# köré csavarodik (a [345°, 360°) és a [0°, 15°) tartomány is piros).
_HUE_ORANGE_MAX = 45.0
_HUE_YELLOW_MAX = 70.0
_HUE_GREEN_MAX = 170.0
_HUE_BLUE_MAX = 255.0
_HUE_PURPLE_MAX = 345.0
_HUE_RED_MIN = 345.0
_HUE_RED_MAX = 15.0


def classify_color(r: int, g: int, b: int) -> str:
    """Egy RGB (0-255) szín → a 10 Picasa-token egyike."""
    hue, sat, val = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    hue_deg = hue * 360.0

    if sat < _ACHROMATIC_SAT_MAX:
        if val < _BLACK_VAL_MAX:
            return "black"
        if val > _WHITE_VAL_MIN:
            return "white"
        return "gray"

    if (
        _PINK_HUE_LO <= hue_deg < _PINK_HUE_HI
        and _PINK_SAT_MIN <= sat < _PINK_SAT_MAX
        and val >= _PINK_VAL_MIN
    ):
        return "pink"

    return _hue_band(hue_deg)


def _hue_band(hue_deg: float) -> str:
    if hue_deg >= _HUE_RED_MIN or hue_deg < _HUE_RED_MAX:
        return "red"
    if hue_deg < _HUE_ORANGE_MAX:
        return "orange"
    if hue_deg < _HUE_YELLOW_MAX:
        return "yellow"
    if hue_deg < _HUE_GREEN_MAX:
        return "green"
    if hue_deg < _HUE_BLUE_MAX:
        return "blue"
    if hue_deg < _HUE_PURPLE_MAX:
        return "purple"
    return "red"  # 345°-ig bezárólag már a piros ág fedi; ez csak védőháló


def average_color(
    image: np.ndarray | Sequence[Sequence[Sequence[int]]], *, order: str = "rgb"
) -> tuple[int, int, int, int] | None:
    """Egy dekódolt kép Picasa-kompatibilis RGBA-átlaga.

    A Picasa a négy BGRA-bájt csatornánkénti összegét a képpontok számával
    egész osztással csonkolja. Háromcsatornás bemenetet átlátszatlannak
    (alfa=255) tekintünk, mert az OpenCV színes dekódolója ilyen tömböt ad.
    `order`: "rgb" (alap) vagy "bgr". A 2×2-nél kisebb képre a Picasa sem
    számol átlagot, ezért a visszatérési érték `None`. Üres/hibás alakú
    bemenetre `ValueError`."""
    array = np.asarray(image)
    if array.ndim != 3 or array.shape[2] < 3 or array.size == 0:
        raise ValueError("average_color: H×W×3(+) alakú kép szükséges")
    if order not in {"rgb", "bgr"}:
        raise ValueError(f"Ismeretlen csatorna-sorrend: {order!r}")
    if array.shape[0] < 2 or array.shape[1] < 2:
        return None

    pixel_count = array.shape[0] * array.shape[1]
    rgb = (array[:, :, :3].astype(np.int64).sum(axis=(0, 1)) // pixel_count).tolist()
    if order == "bgr":
        rgb.reverse()
    alpha = (
        int(array[:, :, 3].astype(np.int64).sum() // pixel_count)
        if array.shape[2] >= 4
        else 255
    )
    r, g, b = (min(255, max(0, int(value))) for value in rgb)
    return (r, g, b, min(255, max(0, alpha)))


def rgb_to_avgcolor(r: int, g: int, b: int, a: int = 255) -> int:
    """RGBA → Picasa `avgcolor` egész: `0xAARRGGBB`."""
    return ((a & 0xFF) << 24) | ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF)


def avgcolor_to_rgb(value: int) -> tuple[int, int, int]:
    """`avgcolor` (0xAARRGGBB) → RGB hármas; az alfa nem része a besorolásnak."""
    return ((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)

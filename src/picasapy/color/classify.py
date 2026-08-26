"""Picasa-féle színkeresés (`color:kék`) — a MÉRT osztályozó (#383, #1480).

A Picasa NEM az átlagszínt sorolja be. Egy **telítettséggel súlyozott
hue-hisztogramot** épít a kép EGÉSZ raszteréről, **hét vödörrel**, és a
**legnagyobb vödör nyer**. Az `avgcolor` ini-/PMP-mezőnek semmi köze
hozzá: ugyanabban a kezelőfüggvényben készül, de külön ágon.

⚠️ A modul korábbi docstringje azt állította, hogy a pontos szabály „nincs
dokumentálva és **nem mérhető**". **Ez téves volt, és megdőlt** (#1480):
az algoritmus egyetlen 752 bájtos függvényben áll a `Picasa3.exe`-ben
(`0x009dbd10`), konstansostul, és 2026-08-26-án ki lett mérve. A teljes
bizonyítéklánc: `docs/specs/picasa-szinkereses.md`. Az alábbi konstansok
tehát MÉRT Picasa-viselkedés, nem a mi döntésünk — ha valamelyik
„gyanúsan rossznak" tűnik (pl. a hue-kör tetején lévő rés), az az eredeti
viselkedése, és a hozzá tartozó teszt szándékosan őrzi.

Képpontonként (`0x009dbd98`–`0x009dbf53`), 8 bites csatornákkal, végig
EGÉSZ aritmetikával:

    MAX = max(R,G,B)      MIN = min(R,G,B)      Δ = MAX − MIN
    ha MAX == 0                   → a képpont KIMARAD
    S = Δ·255 / MAX                                        (0…255)
    H1530 = (G−B)·255/Δ              , ha R a maximum
          = (B−R)·255/Δ + 510        , ha G a maximum
          = (R−G)·255/Δ + 1020       , egyébként
    ha H1530 < 0 → H1530 += 1530
    H = H1530 / 6                                          (0…254)
    ha S <= 50                    → a képpont KIMARAD
    vödör[ b = H/10 ] += S         ⇐ a SÚLY a telítettség, nem 1

Az osztás mindenütt a C nullához csonkoló egészosztása (`idiv`), nem a
Python lefelé kerekítő `//`-ja — a hue számlálója negatív is lehet.

A döntés (`0x009dbf7d`–`0x009dbfc4`): nyolc vödör közül a legnagyobb nyer,
**döntetlennél a magasabb index**. A nyolcadik vödörbe soha nem ír senki,
így a végig üres hisztogramot ő nyeri — ez a névtábla `−1` indexe, ami
egyszerre HÁROM tokent ad: `black`, `white`, `gray`. Az eredeti tehát a
fekete/fehér/szürke között nem tesz különbséget.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

# A hét hue-vödör tokenje, a mért névtábla (`0x00424c20`) sorrendjében:
# 0=red, 1=orange, 2=yellow, 3=green, 4=blue, 5=purple, 6=pink.
HUE_BUCKET_TOKENS: tuple[str, ...] = (
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
)

# A névtábla `−1` indexe EGYETLEN sztringben adja mindhármat
# ("color:black color:white color:gray") — az akromatikus kép tehát
# mindhárom tokenre illeszkedik, nem választunk közülük.
ACHROMATIC_TOKENS: tuple[str, ...] = ("black", "white", "gray")

# A 10 Picasa-színtoken (a keresés szótára), angolul.
COLOR_TOKENS: tuple[str, ...] = HUE_BUCKET_TOKENS + ACHROMATIC_TOKENS

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


# --- MÉRT konstansok (Picasa3.exe 3.9.141.259, ld. a modul-docstringet) ---

#: `cmp ebp, 0x32` + `jle` (`0x009dbe8e`): az ennél nem telítettebb
#: képpont kimarad. 50/255 ≈ 19,6 %.
SATURATION_MIN = 50

#: A hue-kör egysége a binárisban: 1530 = 6 × 255 (a két mért eltolás,
#: 510,0 és 1020,0 ennek a harmada, illetve kétharmada).
_HUE_CIRCLE = 1530

#: hue-tized (`b = H/10`) → vödör, a switch-ágak (`0x009dbea8`–
#: `0x009dbf47`) szerint. A `-1` a MÉRT rés: a `b == 25` képpont (H
#: 250–254, kb. 353,0–358,8°) egyetlen vödörbe sem kerül. Ez az eredeti
#: viselkedése; a `tests/color/test_classify.py` szándékosan őrzi, hogy egy
#: későbbi „javítás" ne tüntesse el némán.
_BUCKET_OF_HUE_DECADE: tuple[int, ...] = (
    0,  # b=0    piros (a kör alja)
    1,
    1,
    1,  # b=1-3  narancs
    2,  # b=4    sárga
    3,
    3,
    3,
    3,
    3,
    3,
    3,  # b=5-11 zöld
    4,
    4,
    4,
    4,
    4,
    4,  # b=12-17 kék
    5,
    5,
    5,
    5,  # b=18-21 lila
    6,
    6,  # b=22-23 rózsaszín
    0,  # b=24   piros (a kör átfordul)
    -1,  # b=25  a MÉRT rés — kimarad
)


def _channels(image: np.ndarray, order: str) -> tuple[np.ndarray, ...]:
    """A bemenet ellenőrzése + (R, G, B) csatornák `int32`-ként.

    `order`: "rgb" (alap) vagy "bgr" — az OpenCV dekódolója BGR-t ad, és
    az eredeti raszter is BGRA volt. Az alfa-csatorna nem játszik."""
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("H×W×3(+) alakú kép szükséges")
    if order not in {"rgb", "bgr"}:
        raise ValueError(f"Ismeretlen csatorna-sorrend: {order!r}")
    planes = image[:, :, :3].astype(np.int32)
    first, second, third = planes[..., 0], planes[..., 1], planes[..., 2]
    return (third, second, first) if order == "bgr" else (first, second, third)


def _truncating_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """A C `idiv`-je: NULLÁHOZ csonkoló egészosztás (a Python `//`-ja
    lefelé kerekít, ami a negatív hue-számlálónál mást adna)."""
    quotient = np.abs(numerator) // denominator
    return np.where(numerator < 0, -quotient, quotient)


def _saturation(
    red: np.ndarray, green: np.ndarray, blue: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(MAX, Δ, S) képpontonként. `MAX == 0` (fekete képpont) esetén Δ is
    0, tehát S = 0 — a hívó telítettség-szűrője úgyis kidobja, külön ág
    nem kell hozzá."""
    maximum = np.maximum(np.maximum(red, green), blue)
    minimum = np.minimum(np.minimum(red, green), blue)
    delta = maximum - minimum
    safe_max = np.where(maximum == 0, 1, maximum)
    return maximum, delta, delta * 255 // safe_max


def _hue(
    red: np.ndarray,
    green: np.ndarray,
    blue: np.ndarray,
    maximum: np.ndarray,
    delta: np.ndarray,
) -> np.ndarray:
    """H (0…254) a MEGTARTOTT képpontokra — Δ > 0 a hívó felelőssége.

    A három ágat maszkonként, egymás után számoljuk (nem `np.where`-rel
    az egész tömbön): így minden képpontra csak a rá vonatkozó ág fut le,
    ami nagy rasztereknél mérhetően olcsóbb. Az ágválasztás sorrendje
    mért: előbb R, aztán G, egyébként B."""
    hue1530 = np.empty(red.shape, dtype=np.int32)
    red_is_max = red == maximum
    green_is_max = ~red_is_max & (green == maximum)
    blue_is_max = ~red_is_max & ~green_is_max
    for mask, first, second, offset in (
        (red_is_max, green, blue, 0),
        (green_is_max, blue, red, 510),
        (blue_is_max, red, green, 1020),
    ):
        hue1530[mask] = (
            _truncating_divide((first[mask] - second[mask]) * 255, delta[mask]) + offset
        )
    np.add(hue1530, _HUE_CIRCLE, out=hue1530, where=hue1530 < 0)
    return hue1530 // 6


def pixel_bucket(red: int, green: int, blue: int) -> int | None:
    """Egyetlen RGB képpont vödre (0…6), vagy `None`, ha a képpont kimarad
    (fekete, `S <= 50`, vagy a mért résbe esik).

    Elsősorban a határesetek tesztelhetőségéért van külön — a hisztogram
    ugyanezt a matekot vektorizálva végzi."""
    channels = tuple(np.array([value], dtype=np.int32) for value in (red, green, blue))
    maximum, delta, saturation = _saturation(*channels)
    if int(saturation[0]) <= SATURATION_MIN:
        return None
    hue = _hue(*channels, maximum, delta)
    bucket = _BUCKET_OF_HUE_DECADE[int(hue[0]) // 10]
    return None if bucket < 0 else bucket


def hue_histogram(
    image: np.ndarray | Sequence[Sequence[Sequence[int]]], *, order: str = "rgb"
) -> tuple[int, ...]:
    """A hét vödör telítettség-összege a kép EGÉSZ raszteréről.

    A visszaadott hetes a `HUE_BUCKET_TOKENS` sorrendjét követi. Üres
    raszterre (és ha minden képpont kimarad) csupa nulla."""
    array = np.asarray(image)
    red, green, blue = _channels(array, order)
    if array.size == 0:
        return (0,) * len(HUE_BUCKET_TOKENS)

    maximum, delta, saturation = _saturation(red, green, blue)
    # A hue-t CSAK a megmaradó képpontokra számoljuk ki — a kidobottakon
    # (fekete, fakó) semmi dolgunk, és ez a raszter felét-harmadát is
    # jelentheti.
    keep = saturation > SATURATION_MIN
    kept_saturation = saturation[keep].astype(np.int64)
    if kept_saturation.size == 0:
        return (0,) * len(HUE_BUCKET_TOKENS)
    hue = _hue(red[keep], green[keep], blue[keep], maximum[keep], delta[keep])

    buckets = np.asarray(_BUCKET_OF_HUE_DECADE, dtype=np.int64)[hue // 10]
    # A résbe eső (−1) képpontokat itt dobjuk el — a `bincount` nem tűrné.
    # A `weights` miatt a `bincount` float64-et ad, de az összeg felső
    # korlátja 255 × képpontszám, ami messze a float64 egész-pontos
    # tartományán belül van — a végén tehát veszteség nélkül egészítünk.
    inside = buckets >= 0
    totals = np.bincount(
        buckets[inside],
        weights=kept_saturation[inside],
        minlength=len(HUE_BUCKET_TOKENS),
    )
    return tuple(int(value) for value in totals)


def classify_image(
    image: np.ndarray | Sequence[Sequence[Sequence[int]]], *, order: str = "rgb"
) -> tuple[str, ...]:
    """Egy dekódolt kép Picasa-színtokenjei.

    Színes képre EGY token (a legnagyobb vödöré, döntetlennél a magasabb
    indexűé — mért viselkedés). Ha egyetlen vödör sem kapott súlyt (a kép
    akromatikus, vagy minden telített képpontja a mért résbe esett), az
    eredmény a névtábla `−1` ága: MINDHÁROM akromatikus token."""
    totals = hue_histogram(image, order=order)
    winner = max(range(len(totals)), key=lambda index: (totals[index], index))
    if totals[winner] == 0:
        return ACHROMATIC_TOKENS
    return (HUE_BUCKET_TOKENS[winner],)


def average_color(
    image: np.ndarray | Sequence[Sequence[Sequence[int]]], *, order: str = "rgb"
) -> tuple[int, int, int, int] | None:
    """Egy dekódolt kép Picasa-kompatibilis RGBA-átlaga (`avgcolor`).

    ⚠️ Ez NEM a színkeresés bemenete (#1480) — a Picasa is külön ágon
    számolja. Az `avgcolor` önálló kép-metaadat.

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
    """`avgcolor` (0xAARRGGBB) → RGB hármas."""
    return ((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)

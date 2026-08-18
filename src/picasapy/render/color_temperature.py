"""A `finetune2` színhőmérséklete — FEKETETEST-tábla + az `autocolor` mátrixa (#879).

## Miért nem csatorna-szorzók

A hőmérséklet-csúszka **nem** három csatorna-erősítést állít (ez volt a
korábbi modellünk), hanem **kiválaszt egy megvilágítás-színt** egy
feketetest-táblából, és a képet azzal a színnel **semlegesíti** — pontosan
úgy, ahogy az `autocolor` a becsült megvilágítást.

A natív ág (`0x0090e9d0`, 54 bájt):

```c
i = (int)(temp * 37.0 + 55.0);   // 0xcf47e0 = 37,0 · 0xcf4610 = 55,0
k = TABLA[i];                     // 0x00c7cf98, csomagolt 0x00RRGGBB
0x0090eda0(dst, src, k);          // ← AZ AUTOCOLOR ALKALMAZÓJA (#759)
```

Ez magyarázza a #685 mérésének SSIM 0,478-át: a kettő **szerkezetileg**
más modell, nem paraméter-hangolás kérdése.

## A csúszka jelentése

`Kelvin = 1000 + 100·i`, tehát:

```
Kelvin = 6500 + 3700 · temp        temp ∈ [−1 … 1]  →  2800 K … 10200 K
```

⚠️ **A `temp = 0` NEM azonosság:** az 55. bejegyzés (255, 249, 253)
minimálisan meleg, tehát a mátrix egy hajszálnyit hűt. A korábbi kódunk
`temperature == 0`-nál a bemenetet adta vissza — apró, de rendszeres hiba.

## ⚠️ A tábla SZÁRMAZTATOTT, nem a binárisból olvasott

A `docs/specs/filters-decoded.md` a 120 elemű táblából **hat** bejegyzést
közöl. A többit **Planck-sugárzásból + CIE 1931 színillesztésből**
számoltam, sRGB-be konvertálva és a legnagyobb csatornára normálva, majd
befagyasztottam ide (determinizmus: a számított tábla numpy-verzióval
sodródhatna).

A hat ismert horgonyon az eltérés:

| index | Kelvin | spec | számított | eltérés |
|---:|---:|---|---|---|
| 0 | 1000 K | (255, 56, 0) | (255, 47, 0) | **−9 a zöldön** |
| 18 | 2800 K | (255, 173, 94) | (255, 178, 96) | +5, +2 |
| 36 | 4600 K | (255, 221, 190) | (255, 224, 192) | +3, +2 |
| 55 | 6500 K | (255, 249, 253) | (255, 249, 254) | +1 a kéken |
| 70 | 8000 K | (227, 233, 255) | (227, 231, 255) | −2 a zöldön |
| 92 | 10200 K | (202, 218, 255) | (203, 216, 255) | +1, −2 |

A csúszka a **18…92** indexet éri el; ott az eltérés legfeljebb 5 szint, és
a mátrix ezt tovább tompítja (a megvilágítás-szín kis hibája a kimeneten
még kisebb eltérést ad). **A modellt a golden párokon mértem** — ld. a
`tests/render/test_finetune2_homerseklet_879.py` méréseit.

Ha valaha előkerül a bináris tábla pontos tartalma, ez a hat horgony az
ellenőrző pont: a `test_a_hat_horgony_a_spec_szerint` őr mutatja meg,
mennyit mozdul.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.autocolor_matrix import apply_autocolor_matrix, autocolor_matrix_16_16

#: A csúszka középpontja a táblában (`0xcf4610 = 55,0`) és a szorzó
#: (`0xcf47e0 = 37,0`) — a natív `i = (int)(temp·37 + 55)`.
TEMPERATURE_CENTER = 55
TEMPERATURE_SPAN = 37

#: Feketetest-RGB, `Kelvin = 1000 + 100·index`. Származtatott — ld. a
#: modul-docstring figyelmeztetését.
BLACKBODY_TABLE: tuple[tuple[int, int, int], ...] = (
    (255, 47, 0),  # 1000 K
    (255, 63, 0),  # 1100 K
    (255, 76, 0),  # 1200 K
    (255, 88, 0),  # 1300 K
    (255, 98, 0),  # 1400 K
    (255, 106, 0),  # 1500 K
    (255, 114, 0),  # 1600 K
    (255, 122, 0),  # 1700 K
    (255, 129, 0),  # 1800 K
    (255, 135, 0),  # 1900 K
    (255, 141, 21),  # 2000 K
    (255, 147, 36),  # 2100 K
    (255, 152, 47),  # 2200 K
    (255, 157, 56),  # 2300 K
    (255, 161, 65),  # 2400 K
    (255, 166, 74),  # 2500 K
    (255, 170, 81),  # 2600 K
    (255, 174, 89),  # 2700 K
    (255, 178, 96),  # 2800 K
    (255, 181, 103),  # 2900 K
    (255, 185, 110),  # 3000 K
    (255, 188, 116),  # 3100 K
    (255, 191, 122),  # 3200 K
    (255, 194, 128),  # 3300 K
    (255, 197, 134),  # 3400 K
    (255, 200, 140),  # 3500 K
    (255, 203, 145),  # 3600 K
    (255, 205, 150),  # 3700 K
    (255, 207, 156),  # 3800 K
    (255, 210, 161),  # 3900 K
    (255, 212, 166),  # 4000 K
    (255, 214, 170),  # 4100 K
    (255, 216, 175),  # 4200 K
    (255, 218, 179),  # 4300 K
    (255, 220, 184),  # 4400 K
    (255, 222, 188),  # 4500 K
    (255, 224, 192),  # 4600 K
    (255, 226, 196),  # 4700 K
    (255, 227, 200),  # 4800 K
    (255, 229, 204),  # 4900 K
    (255, 231, 208),  # 5000 K
    (255, 232, 212),  # 5100 K
    (255, 233, 215),  # 5200 K
    (255, 235, 219),  # 5300 K
    (255, 236, 222),  # 5400 K
    (255, 238, 225),  # 5500 K
    (255, 239, 228),  # 5600 K
    (255, 240, 232),  # 5700 K
    (255, 241, 235),  # 5800 K
    (255, 242, 238),  # 5900 K
    (255, 244, 241),  # 6000 K
    (255, 245, 243),  # 6100 K
    (255, 246, 246),  # 6200 K
    (255, 247, 249),  # 6300 K
    (255, 248, 252),  # 6400 K
    (255, 249, 254),  # 6500 K
    (253, 248, 255),  # 6600 K
    (251, 246, 255),  # 6700 K
    (249, 245, 255),  # 6800 K
    (246, 244, 255),  # 6900 K
    (244, 242, 255),  # 7000 K
    (242, 241, 255),  # 7100 K
    (240, 240, 255),  # 7200 K
    (238, 239, 255),  # 7300 K
    (236, 237, 255),  # 7400 K
    (235, 236, 255),  # 7500 K
    (233, 235, 255),  # 7600 K
    (231, 234, 255),  # 7700 K
    (230, 233, 255),  # 7800 K
    (228, 232, 255),  # 7900 K
    (227, 231, 255),  # 8000 K
    (225, 230, 255),  # 8100 K
    (224, 230, 255),  # 8200 K
    (223, 229, 255),  # 8300 K
    (221, 228, 255),  # 8400 K
    (220, 227, 255),  # 8500 K
    (219, 226, 255),  # 8600 K
    (218, 225, 255),  # 8700 K
    (216, 225, 255),  # 8800 K
    (215, 224, 255),  # 8900 K
    (214, 223, 255),  # 9000 K
    (213, 223, 255),  # 9100 K
    (212, 222, 255),  # 9200 K
    (211, 221, 255),  # 9300 K
    (210, 221, 255),  # 9400 K
    (209, 220, 255),  # 9500 K
    (208, 219, 255),  # 9600 K
    (207, 219, 255),  # 9700 K
    (207, 218, 255),  # 9800 K
    (206, 218, 255),  # 9900 K
    (205, 217, 255),  # 10000 K
    (204, 217, 255),  # 10100 K
    (203, 216, 255),  # 10200 K
    (203, 216, 255),  # 10300 K
    (202, 215, 255),  # 10400 K
    (201, 215, 255),  # 10500 K
    (200, 214, 255),  # 10600 K
    (200, 214, 255),  # 10700 K
    (199, 213, 255),  # 10800 K
    (198, 213, 255),  # 10900 K
    (198, 212, 255),  # 11000 K
    (197, 212, 255),  # 11100 K
    (197, 212, 255),  # 11200 K
    (196, 211, 255),  # 11300 K
    (195, 211, 255),  # 11400 K
    (195, 210, 255),  # 11500 K
    (194, 210, 255),  # 11600 K
    (194, 210, 255),  # 11700 K
    (193, 209, 255),  # 11800 K
    (193, 209, 255),  # 11900 K
    (192, 209, 255),  # 12000 K
    (192, 208, 255),  # 12100 K
    (191, 208, 255),  # 12200 K
    (191, 208, 255),  # 12300 K
    (190, 207, 255),  # 12400 K
    (190, 207, 255),  # 12500 K
    (189, 207, 255),  # 12600 K
    (189, 206, 255),  # 12700 K
    (189, 206, 255),  # 12800 K
    (188, 206, 255),  # 12900 K
)


def temperature_index(temperature: float) -> int:
    """A csúszkaállás → tábla-index, a natív `(int)` CSONKÍTÁSSAL.

    A C `(int)` nulla felé csonkol; a csúszka `[−1…1]` tartományán az
    eredmény mindig pozitív (18…92), de a képlet így hű marad.
    """
    raw = temperature * float(TEMPERATURE_SPAN) + float(TEMPERATURE_CENTER)
    index = int(raw)  # a C `(int)` cast: nulla felé csonkít
    return max(0, min(len(BLACKBODY_TABLE) - 1, index))


def temperature_illuminant(temperature: float) -> tuple[int, int, int]:
    """A csúszkaálláshoz tartozó megvilágítás-szín a feketetest-táblából."""
    return BLACKBODY_TABLE[temperature_index(temperature)]


def temperature_kelvin(temperature: float) -> int:
    """A csúszkaállás Kelvinben — `1000 + 100·index`."""
    return 1000 + 100 * temperature_index(temperature)


def neutralize_illuminant(image: np.ndarray, illuminant: tuple[int, int, int]) -> np.ndarray:
    """A megadott megvilágítás-szín semlegesítése az `autocolor` mátrixával.

    Ugyanaz a `0x0090eda0`, amit a #759 teljesen visszafejtett — csak a `k`
    forrása más (ott becslés, itt a feketetest-tábla, illetve a pipetta).
    """
    red, green, blue = illuminant
    matrix = autocolor_matrix_16_16(int(red), int(green), int(blue))
    return apply_autocolor_matrix(image, matrix)


__all__ = [
    "BLACKBODY_TABLE",
    "TEMPERATURE_CENTER",
    "TEMPERATURE_SPAN",
    "neutralize_illuminant",
    "temperature_illuminant",
    "temperature_index",
    "temperature_kelvin",
]

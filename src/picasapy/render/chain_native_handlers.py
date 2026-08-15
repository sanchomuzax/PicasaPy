"""A #687-ben bekötött natív szűrők lánc-kezelői.

A `chain.py` a 800 soros fájlkorlát közelében jár, ezért az új kezelők
TÖRZSE itt él; ott csak a `_HANDLERS`-be kötés marad.

**A paraméter-leképezés forrása mindenütt a dekompilált BURKOLÓ**
(`referencia/dekompilalt/natív-szűrők.c`, a privát agent-repóban; a hívási
térkép a `docs/specs/picasa-native-filter-workers.md`-ben). A burkolók
vékonyak: kiolvassák a csúszkákat a paraméterblokkból (`+0x28`, `+0x2c`,
`+0x30`) és egy közös munkafüggvényt hívnak — a lényeg tehát az, MELYIK
csúszka MELYIK munkafüggvény-argumentumba megy. Ezt rögzítik az itteni
függvények.
"""

from __future__ import annotations

import numpy as np

from picasapy.ini.filters import FilterOp
from picasapy.render.native_colortemp import apply_native_colortemp
from picasapy.render.native_tone import (
    apply_gamma,
    apply_native_contrast,
    apply_native_levels,
)
from picasapy.render.ops import apply_autocontrast
from picasapy.render.shadow_highlight import apply_shadow_highlight
from picasapy.render.tone import apply_fill

#: A `triple2` Fehérpont csúszkájának alapértéke a `filterdesc.xml` szerint.
#: Hiányzó paraméternél ezzel futunk — így a `triple2=1;` azonosság, ahogy a
#: natív „nincs teendő" ág is (fill = 0, fekete = 0, fehér = 1).
_TRIPLE2_DEFAULT_WHITE = 1.0

#: A natív nullaosztás-védés a `triple2`/`triple3` fehérpontján
#: (`if (w <= 0.001) w = 0.001;` — mindkét burkolóban betű szerint ott áll).
_MIN_WHITE_POINT = 0.001


def _slider(op: FilterOp, index: int, default: float = 0.0) -> float:
    """A flag utáni `index`-edik csúszka számként, hiányzónál `default`.

    POZÍCIÓ szerint konvertál (a `chain._effect_float` mintájára): ha az adott
    helyen értelmezhetetlen érték áll, a kivétel FELSZÁLL, és a lánc ezt az
    egy bejegyzést hagyja ki (#301).
    """
    absolute = index + 1  # a 0. paraméter az engedélyező „1" flag
    if len(op.params) <= absolute:
        return default
    return float(op.params[absolute])


def apply_contrast_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`contrast=1,Kontraszt` — `0x008f8a20`.

    A burkoló a fényerőnek 0-t, a gammának 1,0-t ad:
    `FUN_0090c2c0(kép, csúszka0, 0, 1.0f)`.
    """
    return apply_native_contrast(image, contrast=_slider(op, 0))


def apply_gamma_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`gamma=1,Szint` — `0x008f8e30` (a burkoló `exp(szint)`-et ad tovább)."""
    return apply_gamma(image, level=_slider(op, 0))


def apply_colortemp_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`colortemp=1,HidegMeleg,Fehérváltás` — `0x008f8ea0`.

    `FUN_0090ea10(cél, forrás, csúszka0, csúszka1)`: az első csúszka a
    hideg↔meleg tengely, a második a fehérváltás (ld. a `colorfix` burkolóját,
    ami ugyanezt a magot a színhő-csúszkával és 0 fehérváltással hívja).
    """
    return apply_native_colortemp(
        image, cool_to_warm=_slider(op, 0), white_shift=_slider(op, 1)
    )


def apply_backlight_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`backlight=1,Mennyiség` — `0x008f8970`, a Derítőfény magja.

    `FUN_0090ac20(cél, forrás, csúszka0, 1.0f)` — bájtra ugyanaz a hívás,
    mint a `fill`-é; az `autobacklight` ugyanezt fix 0,25-tel futtatja. Egy
    implementáció, három belépési pont.
    """
    return apply_fill(image, _slider(op, 0))


def apply_shadow_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`shadow=1,Sugár,Árnyék%,Kiemelés%` — `0x008f8ee0`.

    `FUN_0090d3e0(csúszka0, csúszka1, csúszka2)`, vagyis a három csúszka a
    regiszterbeli sorrendjében megy át. A Sugár leképezése KÖZELÍTÉS — ld.
    `shadow_highlight.apply_shadow_highlight` docstringjét.
    """
    return apply_shadow_highlight(
        image,
        radius=_slider(op, 0),
        shadow=_slider(op, 1),
        highlight=_slider(op, 2),
    )


def apply_autocontrast_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`autocontrast=1;` — `0x008f89d0`, csatornánkénti automatikus szinthúzás."""
    del op  # nincs szabad paramétere
    return apply_autocontrast(image)


def apply_triple_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`triple=1,Fényerő,Kontraszt,Derítőfény` — `0x008f8a60`.

    A burkoló két lépése: Derítőfény (`0x0090ac20`), majd kontraszt
    (`0x0090c2c0`, illetve helyben a `0x0090c340`) — a kontraszt-magba a
    MÁSODIK csúszka megy kontrasztként és az ELSŐ fényerőként. Mindkét lépés
    kimarad, ha a hozzá tartozó csúszka nulla.

    **A #685 mérőszettje ezt NEM validálta:** az egyetlen mérőesetben a lánc
    paraméter nélkül állt (`triple=1,`), tehát mindhárom csúszka nulla volt,
    és a Picasa is, mi is változatlanul hagytuk a képet. A paraméter-leképezés
    forrása ezért kizárólag a dekompilált burkoló — mérésre vár.
    """
    brightness = _slider(op, 0)
    contrast = _slider(op, 1)
    fill = _slider(op, 2)
    result = apply_fill(image, fill) if fill != 0.0 else image
    if contrast == 0.0 and brightness == 0.0:
        return result.copy() if result is image else result
    return apply_native_contrast(result, contrast=contrast, brightness=brightness)


def _apply_fill_then_levels(
    image: np.ndarray, fill: float, black: float, white: float
) -> np.ndarray:
    """A `triple2`/`triple3` közös váza: Derítőfény, majd szinthúzás.

    A natív burkolók mindkét lépést kihagyják, ha a saját csúszkájuk
    semleges: a Derítőfényt 0-nál, a szinthúzást a `fehér == 1 és fekete == 0`
    párnál.
    """
    white = max(white, _MIN_WHITE_POINT)
    result = apply_fill(image, fill) if fill != 0.0 else image
    if white == 1.0 and black == 0.0:
        return result.copy() if result is image else result
    return apply_native_levels(result, black=black, white=white)


def apply_triple2_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`triple2=1,Derítőfény,Feketepont,Fehérpont` — `0x008f8b90`."""
    return _apply_fill_then_levels(
        image,
        fill=_slider(op, 0),
        black=_slider(op, 1),
        white=_slider(op, 2, _TRIPLE2_DEFAULT_WHITE),
    )


def apply_triple3_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`triple3=1,Derítőfény,Kiemelések,Árnyékok` — `0x008f8ce0`.

    A burkoló a Kiemeléseket FEHÉRPONTTÁ fordítja (`fehér = 1 − Kiemelések`),
    az Árnyékokat pedig változatlanul adja feketepontnak — vagyis a
    „Kiemelések/Árnyékok" pár ugyanaz a szinthúzás, mint a `finetune`-é
    (#551), csak itt egyetlen LUT-ban.
    """
    return _apply_fill_then_levels(
        image,
        fill=_slider(op, 0),
        black=_slider(op, 2),
        white=1.0 - _slider(op, 1),
    )


__all__ = [
    "apply_autocontrast_op",
    "apply_backlight_op",
    "apply_colortemp_op",
    "apply_contrast_op",
    "apply_gamma_op",
    "apply_shadow_op",
    "apply_triple2_op",
    "apply_triple3_op",
    "apply_triple_op",
]

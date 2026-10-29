"""Auto Colour, Auto Contrast és szinthúzó renderműveletek."""

from __future__ import annotations

import numpy as np

from picasapy.render.autocolor_matrix import (
    apply_autocolor_matrix,
    autocolor_matrix_16_16,
    estimate_illuminant,
)
from picasapy.render.curves import (
    apply_channel_luts,
    apply_lut,
    validate_image as _validate_image,
)
from picasapy.render.ops_levels_analysis import (
    _blend_clip_points,
    _channel_black_white_points,
    _native_levels_lut,
    _union_black_white_point,
)

_ENHANCE_BLEND = 0.30

_AUTOCONTRAST_BLEND = 1.0

_CAREFUL_MAX_OUT = 252

def apply_autolight(image: np.ndarray) -> np.ndarray:
    """Auto Contrast — KÖZÖS (mindhárom csatornára azonos) lineáris
    szinthúzás (#540), a natív vágópontokkal (#539).

    A közös `lo`/`hi` a csatornánkénti, darabszám-küszöbös vágópontok
    UNIÓJA (`_union_black_white_point`), a leképezés pedig a natív
    fixpontos átvitel. Mivel egyetlen `lo`/`hi` fut mindhárom csatornán,
    a műveletnek nincs fehéregyensúly-hatása — ez különbözteti meg a
    csatornánként vágó Auto Colourtól.

    **Azonosság-eset:** ha a kép már kihasználja a teljes tartományt
    (`lo == 0` és `hi == 255`), a kimenet bájtra azonos a bemenettel.

    Mért átlagos eltérés a valódi Picasa-kimenettől a `referencia/
    autocontrast/` 12 képpárján: **0,41** (a korábbi, összeöntött
    hisztogramú közelítés 0,62; az érintetlen kép 7,49).
    """
    _validate_image(image)
    low, high = _union_black_white_point(image)
    if high <= low or (low == 0 and high == 255):
        return image.copy()
    # pontonkénti lineáris széthúzás → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, _native_levels_lut(low, high))

def apply_autocolor(image: np.ndarray) -> np.ndarray:
    """Auto Colour — `M · diag(g) · M⁻¹` SZÍNMÁTRIX (#759).

    **A #541-es, csatornánkénti modell le lett váltva.** A natív alkalmazó
    (`0x0090eda0`) egy 3×3-as mátrixszal szoroz 16.16 fixpontban, amibe a
    becsült erősítések a mátrix TERÉBEN épülnek be — ezért nem ment 2,35
    alá semmilyen csatornánkénti közelítés: hiányoztak a kereszt-tagok.

    A részletek, a mérés és a két csapda (float32; a csonkoló egész-osztás)
    a `picasapy.render.autocolor_matrix` modul-docstringjében. Mért átlagos
    csatorna-eltérés a 12 golden páron:

        érintetlen kép ............................ 5,287
        a korábbi modellünk (#541) ................ 2,352
        EZ a modell ............................... 0,614

    A 0,614 a JPEG-újratömörítés zajszintje (~0,69) ALATT van.

    **Azonosság-eset:** semleges becslésnél (`kR = kB = 128`) a mátrix
    pontosan az egységmátrix, tehát a kimenet bájtra a bemenet. A korábbi
    modell ezt NEM tudta: egy semleges mérőképen 0,812-nyit elmozdított,
    pedig a Picasa hozzá sem nyúlt.
    """
    _validate_image(image)
    red_gain, blue_gain = estimate_illuminant(image)
    matrix = autocolor_matrix_16_16(red_gain, 128, blue_gain)
    if np.array_equal(matrix, np.diag([65536, 65536, 65536])):
        return image.copy()
    return apply_autocolor_matrix(image, matrix)

def apply_channel_levels_stretch(
    image: np.ndarray,
    blend: float = _ENHANCE_BLEND,
    careful: bool = False,
) -> np.ndarray:
    """Lineáris szinthúzás a natív `0x009db610` szerint — KEVERT vágóponttal.

    A vágópontok csatornánként készülnek (`_channel_black_white_points`), de
    a függvény nem itt áll meg: a `blend` arányban a KÖZÖS `[loMin, hiMax]`
    tartomány felé húzza őket (`_blend_clip_points`, #721). A hívó adja meg
    az arányt — az `enhance` 0,30-at, az `autocontrast` 1,0-et. A leképezés a
    natív fixpontos átvitel (`_native_levels_lut`).

    A `careful` a `CarefulEnhance` beállítás ága: felezett feketepontok a
    közös minimum képzése előtt, és 252-es kimeneti korlát. A valódi
    Picasa-exportunk NEM ezzel készült (a 12 páron 2,366 kontra 0,572),
    ezért az alapértelmezés `False` — a beállítás a felhasználó gépén él,
    nem az ini-ben.

    **Azonosság-eset:** ha egy csatorna kevert `lo`/`hi`-je `0`/`255`, a
    natív fixpontos átvitel pontosan 65536-os gaint ad, tehát a kimenet
    bájtra azonos a bemenettel.

    Mért átlagos csatorna-eltérés a `referencia/imfeellucky/` 12 valódi
    Picasa-képpárján: **0,572** — a #721 előtti kód (keverés nélkül, de a
    `_MIN_STRETCH_SPAN = 58` korláttal) 2,480, az érintetlen kép 10,346.
    A 0,30 MÉRT optimum is: 0,25-nél 0,795, 0,30-nál 0,572, 0,35-nél
    0,884 — vagyis a visszafejtett konstanst a mérés önállóan megerősíti.

    #721: a korábbi `_MIN_STRETCH_SPAN = 58` korlát ITT SZŰNT MEG. Az az
    58 nem a natív kód korlátja volt, hanem épp ennek a keverésnek a
    lenyomata: a „Utopic Unicorn" két szűk csatornáján a kevert tartomány
    **58,7** és **58,7** (a Picasából mért 58,1 és 59,2), a zöld kevert
    pontjai `18,0…76,7` (mérve `18,2…76,3`). A keveréssel a korlát a 12
    páron EGYETLEN csatornán sem lépne működésbe (visszatéve mind a 12 kép
    kimenete bájtra azonos), a kiugró képé pedig 13,035-ről 0,521-re esik.
    """
    _validate_image(image)
    points = _blend_clip_points(_channel_black_white_points(image), blend, careful)
    max_out = _CAREFUL_MAX_OUT if careful else 255
    luts = [_native_levels_lut(low, high, max_out) for low, high in points]
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))

def apply_enhance(image: np.ndarray) -> np.ndarray:
    """„Jó napom van" (I'm Feeling Lucky) — `0x008f8840` → `0x009db610`.

    Hisztogram-darabszám alapú lineáris szinthúzás, a vágópontokat **30%-ban
    a közös érték felé keverve** (#721): a hívó a `-1,0` jelzőt adja át,
    amire a natív függvény a `0,30`-as alapértéket használja. Nincs benne
    gamma, S-görbe, helyi kontraszt vagy külön árnyék-/csúcsfény-emelés
    (#535).

    A `CarefulEnhance` bool ágat itt nem kapcsoljuk be — a beállítás a
    felhasználó gépén él, nem az ini-ben, és a referencia-exportunk is a
    kikapcsolt ággal készült (ld. `apply_channel_levels_stretch`).
    """
    _validate_image(image)
    return apply_channel_levels_stretch(image, _ENHANCE_BLEND)

def apply_autocontrast(image: np.ndarray) -> np.ndarray:
    """`autocontrast` („Automatikus kontraszt") — `0x008f89d0` → `0x009db610`.

    Ugyanaz a natív szinthúzó, mint az `enhance`-é, de a hívó **`1,0`**
    keverést ad át (`fld1`, `0x008f89fd`) és fixen 0 boolt (`push 0`,
    `0x008f8a03`). A vágópont tehát TELJESEN közös (`[loMin, hiMax]`),
    vagyis — az `enhance`-szel ellentétben — a művelet **nem mozdítja el a
    fehéregyensúlyt**, csak a kontrasztot húzza szét (#721).

    A két szűrő a #685 szürke rámpáján azonos kimenetet adott — ott
    `lo_ch = loMin` és `hi_ch = hiMax`, tehát a keverés elvileg sem
    látszhat. Színes képen viszont eltérnek.
    """
    _validate_image(image)
    return apply_channel_levels_stretch(image, _AUTOCONTRAST_BLEND)

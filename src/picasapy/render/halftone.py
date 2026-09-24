"""Nyomdai féltónusos (halftone) raszter — a `Comicize` alapprimitívje (#569).

A Picasa `Comicize` effektje **nem** élkiemelő képregényszűrő: két, egymáshoz
képest fél csempével eltolt, csempézett pontmaszkból épített **nyomdai
raszter**. A maszk-primitívet a `filterdesc.xml` `TiledImageMask` művelete
írja le (`tileWidth tileHeight offsetX offsetY alphaMin width height`), a
csempeméretet pedig a natív `glimmer::TiledImageMask` kód:

    dotSize = round(imageWidth / 70) + 1

Bemenet/kimenet: float32 [0,1] maszk, (H, W). A modul TISZTA: új tömböt ad
vissza, semmit nem mutál.
"""

from __future__ import annotations

import numpy as np

#: A csempeméret képlete a natív kódból (#569). A képSZÉLESSÉG (nem a
#: rövidebb oldal!) osztója — vagyis álló és fekvő képen ugyanaz a szélesség
#: ad ugyanakkora pontot.
_DOT_SIZE_DIVISOR = 70

#: A pont TELJES kiterjedése a csempén belül — a `TiledImageMask`
#: `scaleWidth`/`scaleHeight` mezője, MÉRT alapérték: **0,8** (#2476).
#:
#: A natív művelet a `+0x10`/`+0x14` mezőt a tengely méretével szorozza, és a
#: konstruktor (`FUN_00bb7a10`) mindkettőt `0,8`-ra állítja; a szállított
#: `filterdesc.xml` két `TiledImageMask` példánya egyiken sem adja meg, tehát
#: mindkettő az alapértéket használja. A pont átmérője így `0,8 · csempe`,
#: azaz a sugara a BEÍRT kör `0,8`-a — a rámpa egységében épp `0,8`.
#:
#: ⚠️ Ez az a szám, ami a raszterünk amplitúdó-hibáját magyarázza: a festékes
#: terület a sugár NÉGYZETÉVEL nő, és `1 / 0,8² = 1,5625` — pontosan az a
#: ~1,5-szeres túl-erősség, amit a `research/comicize-sweep/` 15 exportján
#: mértünk (5,70 vs. a referencia 3,77).
DOT_SCALE = 0.8

#: A maszk KÖZÉPPONTI értéke — a `TiledImageMask` `alphaMax` mezője, MÉRT
#: alapérték: **1,0** (#2476). A konstruktor (`0x00bba250`) a `fld1`-gyel írja
#: be, az `alphaMin`-t `fldz`-vel, a négy `padding` mezőt nullával; a szállított
#: `filterdesc.xml` egyik `TiledImageMask` példánya sem adja meg őket.
#: ⇒ a maszk a csempe közepén 1,0-ról a `DOT_SCALE`-szeres peremén 0,0-ra futó
#: LINEÁRIS rámpa (a rajzoló két megállót ad át: `0x00bbacba: push 2`).
DOT_ALPHA_MAX = 1.0


def dot_size_for(width: int) -> int:
    """A raszter csempemérete a kép szélességéből: `round(W / 70) + 1` (#569).

    A `+ 1` a natív képletben is ott van — ettől a legkisebb csempe 1 px, és
    a raszter sosem fajul el nulla méretűre.
    """
    if width <= 0:
        raise ValueError(f"Érvénytelen képszélesség: {width}")
    return int(round(width / _DOT_SIZE_DIVISOR)) + 1


def tiled_dot_ramp(
    height: int,
    width: int,
    tile: int,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> np.ndarray:
    """A csempézett pontrács SUGÁR-rámpája: 0 a csempe közepén, 1 a csempe
    BEÍRT körének peremén — a sarkokban 1 fölé megy (√2-ig).

    Ez a féltónus KÜSZÖB-mátrixa: egy képpont akkor lesz festékes, ha a
    tónusa sötétebb, mint az itteni küszöb — így a pont a sötét területeken
    NAGYRA nő, a világosokon elfogy. A `tiled_dot_mask` (a `TiledImageMask`
    művelet közvetlen megfelelője) ugyanebből a rámpából áll elő.
    """
    if tile < 1:
        raise ValueError(f"Érvénytelen csempeméret: {tile}")
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    tile_f = np.float32(tile)
    center = tile_f / np.float32(2.0)
    local_x = np.mod(xs + np.float32(0.5) - np.float32(offset_x), tile_f) - center
    local_y = np.mod(ys + np.float32(0.5) - np.float32(offset_y), tile_f) - center
    return (np.hypot(local_x, local_y) / center).astype(np.float32)


def native_dot_mask(
    height: int, width: int, tile: int, offset_x: float = 0.0, offset_y: float = 0.0
) -> np.ndarray:
    """A `TiledImageMask` natív pontmaszkja, 0..255 (#3390, #3522).

    A csemperajzoló (`0x00bbaa90`) két megállóval hívja a közös rácsolót
    (`0x008f3840` → `0x008f3970`): a kétmegállós LUT a két alfa-végpontból
    `[255, 254, …, 1, 0]` (`0x008f3700`, csonkolt lineáris keverés). A
    rácsoló a képpont sugarát 8.8-as fixpontra CSONKOLJA: a felső bájt a
    LUT-rekesz, az alsó a tört súlya, és a kimenet
    `(next · frac + current · (256 − frac)) >> 8`. Felülmintavételezés és
    külön peremlágyítás NINCS.

    A sugár a `DOT_SCALE`-lel (0,8) normált rámpa: 0 a pont közepén, 1 a
    pont peremén; azon túl a maszk 0.
    """
    rampa = tiled_dot_ramp(height, width, tile, offset_x, offset_y) / np.float32(DOT_SCALE)
    fix = np.floor(np.clip(rampa, 0.0, 1.0) * np.float32(255.0 * 256.0)).astype(np.int64)
    fix = np.minimum(fix, 255 * 256)
    rekesz, tort = fix >> 8, fix & 255
    lut = 255 - np.arange(256, dtype=np.int64)
    aktualis = lut[rekesz]
    kovetkezo = lut[np.minimum(rekesz + 1, 255)]
    return ((kovetkezo * tort + aktualis * (256 - tort)) >> 8).astype(np.float32)


def tiled_dot_mask(
    height: int,
    width: int,
    tile: int,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    alpha_min: float = 0.0,
    alpha_max: float = DOT_ALPHA_MAX,
    scale: float = DOT_SCALE,
) -> np.ndarray:
    """Csempézett pontmaszk — a `TiledImageMask` MÉRT alakja (#569, #2476).

    Minden `tile` × `tile` csempe közepén `alpha_max` áll, és onnan a csempe
    `scale`-szeres beírt körének peremén `alpha_min`-ig fut **lineárisan**; a
    peremen kívül `alpha_min`. Ez nem „kemény korong antialiasolt peremmel",
    hanem kétmegállós radiális rámpa — a rajzoló (`0x00bbaa90`) ugyanazt a
    megálló-kiértékelőt hívja, mint a `CircularGradientImageMask`, mindkettő
    **két** megállóval (`0x00bbacba: push 2`).

    Az `offset_x`/`offset_y` a csempe-rács eltolása — a `Comicize` második ága
    ezt `tile / 2`-re állítja, ettől lesz a raszter sakktábla-szerűen sűrű,
    ahogy a nyomdai féltónusnál.

    ⭐ **A maszk ÁLLANDÓ** (#2476): a tónus nem a maszkból jön, hanem a
    láncból (`PartialMask` a fehér fölé, majd küszöbgörbe — ld.
    `effects_artistic.apply_comicize`). A lánc a 8 bites, natív keverésű
    változatot használja (`native_dot_mask`); ez a lebegőpontos alak a maszk
    geometriájának őre.

    A visszaadott maszk float32 [0,1], (H, W).
    """
    for nev, ertek in (("alphaMin", alpha_min), ("alphaMax", alpha_max)):
        if not 0.0 <= ertek <= 1.0:
            raise ValueError(f"A(z) {nev} [0,1] közé esik: {ertek}")
    if scale <= 0.0:
        raise ValueError(f"A pontskála pozitív: {scale}")
    ramp = tiled_dot_ramp(height, width, tile, offset_x, offset_y)
    hely = np.clip(ramp / np.float32(scale), 0.0, 1.0)
    return (np.float32(alpha_max) + (np.float32(alpha_min) - np.float32(alpha_max)) * hely).astype(
        np.float32
    )


__all__ = [
    "DOT_ALPHA_MAX",
    "DOT_SCALE",
    "dot_size_for",
    "native_dot_mask",
    "tiled_dot_mask",
    "tiled_dot_ramp",
]

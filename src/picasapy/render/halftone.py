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

#: A pont peremének lágyítása pixelben. A natív maszk antialiasingjának
#: PONTOS alakja (és a perem kerekítése) az egyetlen nyitott részlet a
#: #569-ben — golden-összevetés tisztázhatja. Egy pixelnyi lineáris átmenet
#: a szokásos, és a raszter jellegét nem befolyásolja.
_EDGE_SOFTNESS_PX = 1.0


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


def halftone_branch(
    ink: np.ndarray, tile: int, offset_x: float = 0.0, offset_y: float = 0.0
) -> np.ndarray:
    """Egy raszter-ág: a `ink` (0..255 tónus) féltónusos pontrácsa.

    A pont sugara a tónussal nő: sötét képpontnál a csempe majdnem teljesen
    fekete, világosnál egy szemcse marad, 255-nél semmi. A perem
    antialiasolt — ennek PONTOS alakja a #569 egyetlen nyitott részlete.

    A visszatérés float32 [0,255]: 0 a festékes, 255 a festéktelen rész.
    """
    height, width = ink.shape[:2]
    ramp = tiled_dot_ramp(height, width, tile, offset_x, offset_y)
    tone = np.clip(ink / np.float32(255.0), 0.0, 1.0)
    # a pont sugara (a beírt körhöz mérve): fekete tónusnál 1, fehérnél 0
    radius = 1.0 - tone
    # a perem lágyítása a csempeméretéhez mérve — a `_EDGE_SOFTNESS_PX` a
    # pixelben mért átmenet, a rámpa viszont a beírt sugárral normált
    softness = np.float32(max(_EDGE_SOFTNESS_PX / max(tile / 2.0, 1e-6), 1e-6))
    ink_amount = np.clip((radius - ramp) / softness + np.float32(0.5), 0.0, 1.0)
    # a második tényező zárja ki, hogy a NULLA sugarú pont (tiszta fehér)
    # a lágyítás miatt mégis kapjon egy fél fedettségű szemcsét a csempe
    # közepén — fehéren nincs festék
    ink_amount = ink_amount * np.clip(radius / softness, 0.0, 1.0)
    return ((1.0 - ink_amount) * np.float32(255.0)).astype(np.float32)


def tiled_dot_mask(
    height: int,
    width: int,
    tile: int,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    alpha_min: float = 0.0,
) -> np.ndarray:
    """Csempézett, antialiasolt pontmaszk — `TiledImageMask` (#569).

    Minden `tile` × `tile` csempe közepén egy kör áll, `tile / 2` sugárral;
    a körön belül a maszk 1, kívül `alpha_min`, a perem `_EDGE_SOFTNESS_PX`
    szélességben lineárisan megy át. Az `offset_x`/`offset_y` a csempe-rács
    eltolása — a `Comicize` második ága ezt `tile / 2`-re állítja, ettől lesz
    a raszter sakktábla-szerűen sűrű, ahogy a nyomdai féltónusnál.

    A visszaadott maszk float32 [0,1], (H, W).
    """
    if not 0.0 <= alpha_min <= 1.0:
        raise ValueError(f"Az alphaMin [0,1] közé esik: {alpha_min}")
    ramp = np.clip(tiled_dot_ramp(height, width, tile, offset_x, offset_y), 0.0, 1.0)
    center = max(tile / 2.0, 1e-6)
    softness = np.float32(max(_EDGE_SOFTNESS_PX / center, 1e-6))
    # 1 a beírt körön belül, 0 kívül, lineáris átmenettel a peremen
    inside = np.clip((1.0 - ramp) / softness + np.float32(0.5), 0.0, 1.0)
    return (np.float32(alpha_min) + (1.0 - np.float32(alpha_min)) * inside).astype(
        np.float32
    )


__all__ = ["dot_size_for", "halftone_branch", "tiled_dot_mask", "tiled_dot_ramp"]

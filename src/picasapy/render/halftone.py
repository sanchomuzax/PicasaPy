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


def tiled_mask_origin(
    width: int,
    height: int,
    tile: int | tuple[int, int],
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> tuple[int, int]:
    """A `TiledImageMask` rácsának origója képpontban (#3876, #3878).

    A rács `⌈W/t⌉·t × ⌈H/t⌉·t` méretű (`0x00bbb070`), és KÖZÉPRE igazított:
    az origó `(W − rácsszélesség)/2`, **nulla felé csonkoló** egész osztással
    (`cdq` / `sub` / `sar 1`, `0x00bba7b7`–`0x00bba7ca`), plusz a szintén
    csonkolt eltolás (`or 0xc00` + `fistp`, `0x00bba7a5`–`0x00bba7dc`);
    függőlegesen ugyanígy. 960 × 640-en, `t = 15`-tel `(0, −2)`, fél csempés
    (7,5-ös) eltolással `(7, 5)`.

    A csempe közepe az origótól `t/2`-re van, és a rácsoló a képpont
    INDEXÉBŐL mér (`0x008f3b61` `fldz`): a `tiled_dot_ramp` ezt
    `offset = origó + 0,5`-tel adja vissza.
    """
    if isinstance(tile, tuple):
        if len(tile) != 2:
            raise ValueError(f"Érvénytelen csempeméret: {tile}")
        tile_width, tile_height = tile
    else:
        tile_width = tile_height = tile
    if tile_width < 1 or tile_height < 1:
        raise ValueError(f"Érvénytelen csempeméret: {tile}")

    def _tengely(meret: int, csempe: int, eltolas: float) -> int:
        racs = int(np.ceil(np.float32(meret) / np.float32(csempe))) * csempe
        return int((meret - racs) / 2) + int(eltolas)

    return (
        _tengely(width, tile_width, offset_x),
        _tengely(height, tile_height, offset_y),
    )


def _repeat_tile_at_origin(
    tile_mask: np.ndarray,
    height: int,
    width: int,
    origin_x: int,
    origin_y: int,
) -> np.ndarray:
    """Csempét ismétel az origótól induló, képszélre klippelt rácsban."""
    tile_height, tile_width = tile_mask.shape
    result = np.zeros((height, width), dtype=tile_mask.dtype)

    for row in range(height // tile_height + 1):
        y = origin_y + row * tile_height
        dst_y0 = max(y, 0)
        dst_y1 = min(y + tile_height, height)
        if dst_y0 >= dst_y1:
            continue
        src_y0 = dst_y0 - y
        src_y1 = src_y0 + dst_y1 - dst_y0

        for column in range(width // tile_width + 1):
            x = origin_x + column * tile_width
            dst_x0 = max(x, 0)
            dst_x1 = min(x + tile_width, width)
            if dst_x0 >= dst_x1:
                continue
            src_x0 = dst_x0 - x
            src_x1 = src_x0 + dst_x1 - dst_x0
            result[dst_y0:dst_y1, dst_x0:dst_x1] = tile_mask[
                src_y0:src_y1, src_x0:src_x1
            ]

    return result


def tiled_mask_grid(
    tile_mask: np.ndarray,
    height: int,
    width: int,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> np.ndarray:
    """A `TiledImageMask` csempéjét a natív, középre tett rácson rajzolja ki.

    A csempe mindkét irányban `floor(képméret/csempeméret)+1` alkalommal
    kerül kirajzolásra. A csonkolt eltolás a középre igazított rácsorigóhoz
    adódik, a képkereten kívüli részeket pedig a kimenet klippeli (#4338).
    """
    tile = np.asarray(tile_mask)
    if tile.ndim != 2 or tile.shape[0] < 1 or tile.shape[1] < 1:
        raise ValueError("A Tiled maszkcsempéje nem üres, kétdimenziós tömb legyen")
    if height < 1 or width < 1:
        raise ValueError(f"Érvénytelen kimenetméret: {width}×{height}")

    tile_height, tile_width = tile.shape
    origin_x, origin_y = tiled_mask_origin(
        width, height, (tile_width, tile_height), offset_x, offset_y
    )
    return _repeat_tile_at_origin(tile, height, width, origin_x, origin_y)


def tiled_dot_ramp(
    height: int,
    width: int,
    tile: int,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> np.ndarray:
    """Folytonos sugárrámpa, a képpontok közepén mintázva.

    A `native_dot_mask` ettől külön térbeli fázist követ: az eredeti worker
    egész képpontindexből képezi a float32 sugarat, majd Q8.8-ra kerekít
    (#4326). Ez a rámpa a középpontból mintázott, folytonos geometriai
    segédmodell marad.
    """
    if tile < 1:
        raise ValueError(f"Érvénytelen csempeméret: {tile}")
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    tile_f = np.float32(tile)
    center = tile_f / np.float32(2.0)
    local_x = np.mod(xs + np.float32(0.5) - np.float32(offset_x), tile_f) - center
    local_y = np.mod(ys + np.float32(0.5) - np.float32(offset_y), tile_f) - center
    return (np.hypot(local_x, local_y) / center).astype(np.float32)


def _native_dot_radius_q8_8(tile: int) -> np.ndarray:
    """A Tiled worker nyers, nearest-even Q8.8 sugárértékei csempénként (#4326).

    A 7×7-es mérésben ez a mátrix a `CVTPS2DQ` előtti float32 sugár
    kerekítéséből származik. A `0xff00`-ra vágás külön történik, közvetlenül
    a LUT-indexelés előtt.
    """
    if tile < 1:
        raise ValueError(f"Érvénytelen csempeméret: {tile}")

    def _transzformacio(csempe: int) -> tuple[np.float32, np.float32]:
        csempe_f = np.float32(csempe)
        meretezett = np.float32(csempe_f * np.float32(DOT_SCALE))
        kezdet = np.float32(-np.float32(meretezett - csempe_f) * np.float32(0.5))
        kozep = np.float32(kezdet + np.float32(meretezett * np.float32(0.5)))
        skala = np.float32(meretezett / np.float32(1638.4))
        inverz = np.float32(np.float32(1.0) / skala)
        eltolas = np.float32(-kozep / skala)
        return (
            np.float32(float(inverz) * 79.6875),
            np.float32(float(eltolas) * 79.6875),
        )

    step_x, translation_x = _transzformacio(tile)
    step_y, translation_y = _transzformacio(tile)
    x = np.arange(tile, dtype=np.float32)
    y = np.arange(tile, dtype=np.float32)
    tx = np.float32(x * step_x + translation_x)
    ty = np.float32(y * step_y + translation_y)
    sugar_negyzet = np.float32(tx[np.newaxis, :] ** 2 + ty[:, np.newaxis] ** 2)
    sugar = np.sqrt(sugar_negyzet, dtype=np.float32)
    return np.rint(sugar).astype(np.int32)


def _native_dot_alpha_lut() -> np.ndarray:
    """Az eredeti `Tiled` két stopja által kiértékelt 256 alfa-bájt (#4326)."""
    stop = np.arange(256, dtype=np.float32) / np.float32(255.0)
    return np.trunc(255.0 - stop.astype(np.float64) * 255.0).astype(np.uint8)


def native_dot_mask(
    height: int, width: int, tile: int, offset_x: float = 0.0, offset_y: float = 0.0
) -> np.ndarray:
    """A `TiledImageMask` natív pontmaszkja, 0..255 (#3390, #3522).

    A kétmegállós LUT az eredeti float32 `i/255` értékből és x87-es
    csonkolásból áll elő: `[255, 253, 252, 251, …, 2, 1, 0, 0]`.
    A transzformált sugár 8.8-as fixpontos értékét a SIMD ág
    `CVTPS2DQ`-val (kerekítés a legközelebbi egészre) alakítja, majd
    `q >> 8` választ LUT-rekeszt, `q & 255` pedig tört súlyt. A kimenet
    `(next · frac + current · (256 − frac)) >> 8`. Felülmintavételezés és
    külön peremlágyítás NINCS.

    A teljes csemperács és a szélek klippelése a `tiled_mask_grid`-en fut
    (#4338). Az eltolás a wrapper által csonkolt rácseltolás.
    """
    if tile < 1:
        raise ValueError(f"Érvénytelen csempeméret: {tile}")
    if height < 1 or width < 1:
        raise ValueError(f"Érvénytelen kimenetméret: {width}×{height}")

    q = np.minimum(_native_dot_radius_q8_8(tile), 255 * 256).astype(np.int64)
    rekesz, tort = q >> 8, q & 255

    lut = _native_dot_alpha_lut().astype(np.int64)
    aktualis = lut[rekesz]
    kovetkezo = lut[np.minimum(rekesz + 1, 255)]
    tile_mask = ((kovetkezo * tort + aktualis * (256 - tort)) >> 8).astype(np.uint8)
    return tiled_mask_grid(tile_mask, height, width, offset_x, offset_y).astype(np.float32)


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
    """Folytonos, pixelközépen mintázott pontmaszk-geometria (#569, #2476).

    Minden `tile` × `tile` csempe közepén `alpha_max` áll, és onnan a csempe
    `scale`-szeres beírt körének peremén `alpha_min`-ig fut **lineárisan**; a
    peremen kívül `alpha_min`. Ez nem „kemény korong antialiasolt peremmel",
    hanem kétmegállós radiális rámpa — a rajzoló (`0x00bbaa90`) ugyanazt a
    megálló-kiértékelőt hívja, mint a `CircularGradientImageMask`, mindkettő
    **két** megállóval (`0x00bbacba: push 2`).

    Az `offset_x`/`offset_y` a csempe-rács eltolása — a `Comicize` második ága
    ezt `tile / 2`-re állítja, ettől lesz a raszter sakktábla-szerűen sűrű,
    ahogy a nyomdai féltónusnál.

    Ez a segédmodell képpontközépből mintáz; az eredeti natív effekt
    képpontindexből számított, Q8.8-as bájtmaszkját a `native_dot_mask`
    adja (#4326). A Comicize lánc ezt a natív változatot használja.

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
    "tiled_mask_grid",
    "tiled_mask_origin",
]

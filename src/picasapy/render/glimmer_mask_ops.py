"""Körkörös alfaátmenet- és színezőmaszk-műveletek."""

from __future__ import annotations

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_blend_ops import apply_blend_mode, to_float, to_uint8
import numpy as np



# --- Térbeli maszkok -------------------------------------------------------


def circular_gradient_mask(
    height: int,
    width: int,
    inner_radius: float,
    outer_radius: float,
    center: tuple[float, float] | None = None,
    inner_alpha: float = 0.0,
    outer_alpha: float = 1.0,
    aspect_ratio: float = 1.0,
) -> np.ndarray:
    """`CircularGradient`: (H, W) float32 [0,1] maszk — `inner_alpha` az
    `inner_radius`-on belül (védett, „éles" zóna), `outer_alpha` az
    `outer_radius`-on túl, lineárisan a kettő között. `center` alapból a kép
    közepe, pixel-egységben.

    #3958/#4905: a 16 bites pozíció az eredeti egész befoglaló dobozából és
    az aspect-függő skálából számolódik; a kimenet egész alfa-bájtokból
    (`alfa / 255`) áll. A méret és a bal/felső él külön, nearest-even
    kerekítést kap, ahogy a natív x87 FISTP.

    #788: a két alfa a natív `CircularGradientImageMask`
    `innerAlpha`/`outerAlpha` attribútuma; az alapértékek a KIOLVASOTT
    tartalékok (`0,0` → `1,0`), tehát az alapeset változatlan. A natív olvasó
    mindkettőt `[0,1]`-re vágja (`0x00bd0391`, `0x00bd03e1`).

    `aspect_ratio` a natív `aspectRatio` mezője; a meglévő hívók változatlanul
    körmaszkot kérnek az alapértelmezett `1.0` értékkel. Nem pozitív értéknél
    `ValueError` (a natív viselkedés nincs kimérve, a csendes maszk hibás lenne).
    """
    if aspect_ratio <= 0:
        raise ValueError(f"Az aspectRatio pozitívnak kell lennie: {aspect_ratio}")
    cx, cy = center if center is not None else (width / 2.0, height / 2.0)
    belso = float(np.clip(inner_alpha, 0.0, 1.0))
    kulso = float(np.clip(outer_alpha, 0.0, 1.0))
    if outer_radius <= inner_radius:
        # A spec képlete erre is érvényes, de `inner = outer = 0` mellett az
        # új út `R = 0`-val osztana: ezért marad a korábbi kemény lépcső (a
        # hívók, `Lomo` és `Holga`, ide sosem jutnak).
        ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
        dist = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy)
        arany = (dist >= inner_radius).astype(np.float32)
        return (np.float32(belso) + arany * np.float32(kulso - belso)).astype(np.float32)
    tabla = _kormaszk_megallo_tabla(inner_radius, outer_radius, belso, kulso)
    pozicio = _kormaszk_doboz_pozicio(
        height,
        width,
        cx,
        cy,
        inner_radius,
        outer_radius,
        aspect_ratio,
    )
    rekesz = pozicio >> 8
    tort = pozicio & 0xFF
    alfa = (tabla[rekesz + 1] * tort + tabla[rekesz] * (256 - tort)) >> 8
    return (alfa.astype(np.float32) / np.float32(255.0)).astype(np.float32)



#: A körmaszk pozíciójának teljes skálája (`0xff00`, 16 bites; a Flash
#: színátmenet 255 rekesze × 256).
_KORMASZK_POZICIO_MAX = 0xFF00



def _kormaszk_megallo_tabla(
    inner_radius: float, outer_radius: float, inner_alpha: float, outer_alpha: float
) -> np.ndarray:
    """A `CircularGradientImageMask` 257 elemű megálló-táblája (`0x008f3700`,
    #3957): `p₁ = csonk(255·inner/R)`, `T[i] = csonk(a₀ + (a₁−a₀)·f32((i−p₁)/
    (255−p₁)))` a `p₁ ≤ i < 255` rekeszekre, `a₀` előtte, `a₁` 255-től 256-ig.
    """
    sugar = max(inner_radius, outer_radius)
    a0 = int(np.trunc(255.0 * inner_alpha))
    a1 = int(np.trunc(255.0 * outer_alpha))
    p1 = int(np.trunc(255.0 * inner_radius / sugar))
    tabla = np.full(257, a0, dtype=np.int64)
    if p1 < 255:
        i = np.arange(p1, 255)
        arany = ((i - p1).astype(np.float32) / np.float32(255 - p1)).astype(np.float64)
        tabla[p1:255] = np.trunc(a0 + (a1 - a0) * arany).astype(np.int64)
    tabla[255:] = a1
    return tabla



def _kormaszk_doboz_pozicio(
    height: int,
    width: int,
    cx: float,
    cy: float,
    inner_radius: float,
    outer_radius: float,
    aspect_ratio: float,
) -> np.ndarray:
    """A tört paraméterek natív dobozából számolt SSE2 pozíció (#4905).

    A `0x00bd05f0` a méretet és a bal/felső élt külön x87 `FISTP`-vel,
    nearest-even módon egészíti ki. A pixelút a lekerekített, még nem
    klippelt doboz közepét és méretét használja (`0x00cf47f0` és
    `0x00cf48f0` konstansokkal), majd az SSE2 `sqrtps`/`cvtps2dq` ága adja a
    16 bites pozíciót.
    """
    f32 = np.float32
    radius = max(f32(inner_radius), f32(outer_radius))
    height_f = f32(f32(2.0) * radius)
    width_f = f32(f32(aspect_ratio) * height_f)

    box_width = int(np.rint(width_f))
    box_height = int(np.rint(height_f))
    if box_width < 1 or box_height < 1:
        # A 0-s méret osztást (inf/NaN maszk) adna: hibát dobunk helyette.
        raise ValueError(
            f"A körmaszk doboza nullára kerekedne (aspectRatio={aspect_ratio}, "
            f"sugár={float(radius)})"
        )
    left = int(np.rint(f32(f32(cx) - f32(width_f * f32(0.5)))))
    top = int(np.rint(f32(f32(cy) - f32(height_f * f32(0.5)))))
    box_center_x = f32(left + f32(box_width * f32(0.5)))
    box_center_y = f32(top + f32(box_height * f32(0.5)))

    flash_scale = f32(1638.4000244140625)
    inverse_affine_scale = f32(79.6875)
    scale_x = f32(f32(flash_scale / f32(box_width)) * inverse_affine_scale)
    scale_y = f32(f32(flash_scale / f32(box_height)) * inverse_affine_scale)
    u = (np.arange(width, dtype=np.float32) - box_center_x) * scale_x
    v = (np.arange(height, dtype=np.float32) - box_center_y) * scale_y
    distance = np.sqrt(
        v[:, np.newaxis] * v[:, np.newaxis] + u[np.newaxis, :] * u[np.newaxis, :]
    )
    return np.minimum(np.rint(distance), _KORMASZK_POZICIO_MAX).astype(np.int64)



def tint_multiply(image: np.ndarray, color: tuple[int, int, int], alpha: float) -> np.ndarray:
    """`Tint(Color=..., BlendMode=multiply)`: szorzó-színezés `alpha` súllyal.

    `color` csatornasorrendje **ugyanaz, mint a `image` tömbé** — ez a
    modul (és a teljes `render/chain.py` csővezeték, ld. a modul-docstring
    tetejét) **RGB**-terű, NEM BGR: `color[0]` = R, `color[1]` = G,
    `color[2]` = B. A `filterdesc.xml` hex színeit (`0xRRGGBB`) ezért
    közvetlenül, csere nélkül `(R, G, B)` sorrendben kell megadni. A
    BGR/RGB keveredés (#510) csak a modulhatárokon (pl. `cv2.imread`
    kimenete, `export/exporter.py::_apply_filter_chain`) számít, ahol a
    hívó `cv2.cvtColor(..., COLOR_BGR2RGB/RGB2BGR)`-rel konvertál.
    """
    validate_image(image)
    image_f = to_float(image)
    color_layer = np.empty_like(image_f)
    color_layer[..., 0] = color[0]
    color_layer[..., 1] = color[1]
    color_layer[..., 2] = color[2]
    return to_uint8(apply_blend_mode(image_f, color_layer, "multiply", alpha))

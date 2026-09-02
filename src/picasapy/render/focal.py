"""Fókusz-effektek: `FocalZoom` és `PicnikFocalPixelate` (#570).

A #381 az XML-csővezetéket rögzítette; a natív
`glimmer::RadialBlurImageOperation` visszafejtése (vtable `0xcf07fc`,
wrapper `0xbc24e0`, mag `0xbcf4b0`) adta hozzá a hiányzó, implementáció-
kritikus részleteket:

- a **paramétersorrend** `x, y, Impact, Radius, Hardness, Fade` — a
  fókuszpont UTÁN az `Impact` jön, a `Radius` NEM a harmadik numerikus mező
  (a korábbi kód innen olvasta, ezért a két csúszka hatása fel volt
  cserélve);
- a két effekt **KÖZÖS körmaszkot** használ;
- a `FocalZoom` mintaszáma és zoomtartománya rögzített képlet, nem tetszőleges
  lépésszám.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import validate_image

#: A `Hardness` osztója a natív képletben. A 101 (nem 100!) szándékos: a
#: `Hardness = 100` mellett is marad egy hajszálnyi átmenet, sosem lesz a
#: belső és a külső sugár azonos.
_HARDNESS_DIVISOR = 101.0

#: A `FocalZoom` mintaszáma: `min(trunc(Impact) + 5, 30)`.
_ZOOM_SAMPLE_BASE = 5
_ZOOM_SAMPLE_MAX = 30

#: A maximális zoomeltolás osztója: `floor(width * Impact / 200)`.
_ZOOM_OFFSET_DIVISOR = 200.0


def focal_mask(
    height: int,
    width: int,
    x: float,
    y: float,
    radius: float,
    hardness: float,
    scale: float = 1.0,
) -> np.ndarray:
    """A két fókusz-effekt KÖZÖS körmaszkja (#570) — float32 [0,1], (H, W).

    A natív képlet, teljes felbontásra visszaskálázott sugárral:

        inner = Radius · (imageWidth / fullResWidth) · Hardness/101
        outer = Radius · (imageWidth / fullResWidth) · (2 − Hardness/101)

    A maszk a belső sugáron belül **0** (a hatás nem éri el: itt marad éles a
    kép), a külsőn túl **1** (teljes hatás), közte lineáris.

    A `scale` az `imageWidth / fullResWidth` arány. A PicasaPy renderelője a
    kapott felbontáson dolgozik; ha a hívó kicsinyített előnézetet renderel,
    ezzel az aránnyal tudja a sugarat arányosan visszaskálázni. Alapértéke
    1,0 — a teljes felbontású render esete.
    """
    hard = float(np.clip(hardness, 0.0, 100.0)) / _HARDNESS_DIVISOR
    base = max(float(radius), 0.0) * max(float(scale), 0.0)
    inner = base * hard
    outer = base * (2.0 - hard)
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    dist = np.hypot(
        xs + np.float32(0.5) - np.float32(x * width),
        ys + np.float32(0.5) - np.float32(y * height),
    )
    if outer <= inner:
        return (dist >= np.float32(inner)).astype(np.float32)
    return np.clip(
        (dist - np.float32(inner)) / np.float32(outer - inner), 0.0, 1.0
    ).astype(np.float32)


def zoom_sample_count(impact: float) -> int:
    """`N = min(trunc(Impact) + 5, 30)` — a zoomminták száma (#570)."""
    return min(int(max(impact, 0.0)) + _ZOOM_SAMPLE_BASE, _ZOOM_SAMPLE_MAX)


def zoom_max_offset(width: int, impact: float) -> int:
    """`floor(width · Impact / 200)` — a legnagyobb zoomeltolás pixelben."""
    return int(np.floor(width * max(impact, 0.0) / _ZOOM_OFFSET_DIVISOR))


def apply_focal_zoom(
    image: np.ndarray,
    x: float = 0.5,
    y: float = 0.5,
    impact: float = 50.0,
    radius: float = 10.0,
    hardness: float = 50.0,
    fade: float = 0.0,
    scale: float = 1.0,
) -> np.ndarray:
    """`FocalZoom=1,x,y,Impact,Radius,Hardness,Fade` — sugárirányú (zoom)
    elmosás a fókuszpont körül (#570).

    A natív mag szerint `N = min(trunc(Impact) + 5, 30)` zoommintát átlagol,
    a legnagyobb zoomeltolás `floor(width · Impact / 200)` pixel. A minták a
    fókuszpont körül egyre nagyobb léptékben újramintavételezett képek; a
    kész elmosás a **körmaszk** szerint keveredik az élesen maradó
    középpontra, végül a `Fade` a szokásos `1 − Fade/100` súllyal zár.
    """
    validate_image(image)
    if not 0.0 <= x <= 1.0 or not 0.0 <= y <= 1.0:
        raise ValueError(f"Az (x, y) fókuszpont 0..1 közé esik: ({x}, {y})")
    for name, value in (
        ("Impact", impact),
        ("Radius", radius),
        ("Hardness", hardness),
        ("Fade", fade),
    ):
        if value < 0:
            raise ValueError(f"A(z) {name} nem lehet negatív: {value}")

    height, width = image.shape[:2]
    samples = zoom_sample_count(impact)
    max_offset = zoom_max_offset(width, impact)
    image_f = image.astype(np.float32)
    if max_offset <= 0 or samples <= 1:
        blurred = image_f
    else:
        # a legnagyobb minta ennyivel nagyobb a képnél — pixelben megadott
        # eltolásból léptékarány
        max_scale = 1.0 + max_offset / max(width, 1)
        center = (x * width, y * height)
        accum = np.zeros_like(image_f)
        for step in range(samples):
            zoom = 1.0 + (max_scale - 1.0) * step / (samples - 1)
            matrix = cv2.getRotationMatrix2D(center, 0.0, zoom)
            accum += cv2.warpAffine(
                image,
                matrix,
                (width, height),
                flags=cv2.INTER_LINEAR,
                # ⚠️ #1351: MÉRETLEN FELTEVÉS, nem adat. A `Comicize`
                # peremszabálya kiderült a szállított `filterdesc.xml`-ből
                # (nulla padding, képméretre feszített rács), a `FocalZoom`
                # halmozásáé NEM: az a NATÍV magban van (`0xbcf4b0`), ami
                # nincs visszafejtve, és golden-párunk sincs rá.
                #
                # A `BORDER_REPLICATE` a mi választásunk — józan, de nem
                # igazolt. Aki méréssel eldönti, cserélje ki, és vegye ki
                # ezt a megjegyzést; addig NE hivatkozzon rá úgy, mintha
                # az eredeti viselkedése volna.
                borderMode=cv2.BORDER_REPLICATE,
            ).astype(np.float32)
        blurred = accum / np.float32(samples)

    mask = focal_mask(height, width, x, y, radius, hardness, scale)[..., np.newaxis]
    focused = image_f + mask * (blurred - image_f)
    weight = np.float32(np.clip(1.0 - fade / 100.0, 0.0, 1.0))
    return _to_uint8(image_f + weight * (focused - image_f))


def apply_focal_pixelate(
    image: np.ndarray,
    x: float = 0.5,
    y: float = 0.5,
    impact: float = 20.0,
    radius: float = 10.0,
    hardness: float = 50.0,
    fade: float = 0.0,
    scale: float = 1.0,
) -> np.ndarray:
    """`PicnikFocalPixelate=1,x,y,Impact,Radius,Hardness,Fade` (#570).

    A natív recept: lekicsinyítés `W/Impact × H/Impact` méretre, majd
    visszanagyítás `W × H`-ra **`smoothing = false`** módban — vagyis
    legközelebbi-szomszéd, nem interpoláció (ettől lesznek éles blokkjai, nem
    elmosódott foltjai). Ugyanaz a körmaszk és `Fade`, mint a `FocalZoom`-nál.
    """
    validate_image(image)
    if not 0.0 <= x <= 1.0 or not 0.0 <= y <= 1.0:
        raise ValueError(f"Az (x, y) fókuszpont 0..1 közé esik: ({x}, {y})")
    for name, value in (
        ("Impact", impact),
        ("Radius", radius),
        ("Hardness", hardness),
        ("Fade", fade),
    ):
        if value < 0:
            raise ValueError(f"A(z) {name} nem lehet negatív: {value}")

    height, width = image.shape[:2]
    image_f = image.astype(np.float32)
    factor = max(float(impact), 1.0)
    small_w = max(1, int(width / factor))
    small_h = max(1, int(height / factor))
    small = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_AREA)
    # smoothing=false → NEAREST: a blokkok élei élesek maradnak
    pixelated = cv2.resize(
        small, (width, height), interpolation=cv2.INTER_NEAREST
    ).astype(np.float32)

    mask = focal_mask(height, width, x, y, radius, hardness, scale)[..., np.newaxis]
    focused = image_f + mask * (pixelated - image_f)
    weight = np.float32(np.clip(1.0 - fade / 100.0, 0.0, 1.0))
    return _to_uint8(image_f + weight * (focused - image_f))


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


__all__ = [
    "apply_focal_pixelate",
    "apply_focal_zoom",
    "focal_mask",
    "zoom_max_offset",
    "zoom_sample_count",
]

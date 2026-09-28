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

import numpy as np

from picasapy.lazy_cv2 import cv2
from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import masked_blend, resize_image

#: A `Hardness` osztója a natív képletben. A 101 (nem 100!) szándékos: a
#: `Hardness = 100` mellett is marad egy hajszálnyi átmenet, sosem lesz a
#: belső és a külső sugár azonos.
_HARDNESS_DIVISOR = 101.0

#: A `FocalZoom` mintaszáma: `min(trunc(Impact) + 5, 30)`.
_ZOOM_SAMPLE_BASE = 5
_ZOOM_SAMPLE_MAX = 30

#: A maximális zoomeltolás osztója: `floor(width * Impact / 200)`.
_ZOOM_OFFSET_DIVISOR = 200.0

#: A keverés súlyai a Picasa SSE2-ágában (`0x00bcf0f9`–`0x00bcf0fe`, #3883):
#: `acc = (38·minta + 217·acc) >> 8` — összegük 255, az osztó 256.
_ZOOM_SAMPLE_WEIGHT = 38
_ZOOM_ACC_WEIGHT = 217

#: Ennyi soronként dolgozik a `zoom_blur` (gyorsítótár-méret, nem natív adat).
_ZOOM_BAND_ROWS = 64

#: A `cv2.remap` egész (`CV_16SC2`) indextérképének felső határa.
_REMAP_MAX_SIZE = 32767


def focal_mask(
    height: int,
    width: int,
    x: float,
    y: float,
    radius: float,
    hardness: float,
    scale: float = 1.0,
    inner_alpha: float = 0.0,
    outer_alpha: float = 1.0,
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

    #788: az `inner_alpha`/`outer_alpha` a natív `CircularGradientImageMask`
    `innerAlpha`/`outerAlpha` attribútuma. Az alapértékek a KIOLVASOTT
    tartalékok (`0,0` → `1,0`), tehát az alapeset változatlan; a natív olvasó
    mindkettőt `[0,1]`-re vágja (`0x00bd0391`, `0x00bd03e1`), ezért itt is
    vágunk. Ez adja a `PicnikFocalPixelate` „Fordított" jelölőjét: a
    `filterdesc.xml` ott pontosan a két alfát cseréli.
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
    belso = np.float32(np.clip(inner_alpha, 0.0, 1.0))
    kulso = np.float32(np.clip(outer_alpha, 0.0, 1.0))
    if outer <= inner:
        arany = (dist >= np.float32(inner)).astype(np.float32)
    else:
        arany = np.clip(
            (dist - np.float32(inner)) / np.float32(outer - inner), 0.0, 1.0
        ).astype(np.float32)
    return (belso + arany * (kulso - belso)).astype(np.float32)


def zoom_sample_count(impact: float) -> int:
    """`N = min(trunc(Impact) + 5, 30)` — a zoomminták száma (#570)."""
    return min(int(max(impact, 0.0)) + _ZOOM_SAMPLE_BASE, _ZOOM_SAMPLE_MAX)


def zoom_max_offset(width: int, impact: float) -> int:
    """`floor(width · Impact / 200)` — a legnagyobb zoomeltolás pixelben."""
    return int(np.floor(width * max(impact, 0.0) / _ZOOM_OFFSET_DIVISOR))


def zoom_offsets(samples: int, max_offset: int) -> tuple[int, ...]:
    """A minták eltolása a natív sorrendben (#3883): `k = N … 1`,
    `off = ⌊k·D / N⌋` — a legnagyobb eltolás jön ELŐSZÖR (`0x00bcf58e`,
    `0x00bcf93e`)."""
    if samples <= 0:
        return ()
    return tuple((k * max_offset) // samples for k in range(samples, 0, -1))


def zoom_sample_indices(length: int, offset: int, focus_px: float) -> np.ndarray:
    """Egy tengely legközelebbi-szomszéd forrásindexei (#3883), `int64`.

    A cél → forrás mátrix egy tengelyre `u = (X + 0,5)·L/(L+off) + off·f/L`
    (`f` a fókusz képpontban), float32-ben; az index `⌊65536·u⌋ >> 16` — a
    natív 16.16 fixpont, interpoláció nélkül. A mátrix fix pontja
    `f·(L+off)/L`, nem pontosan `f`.

    A képlet a képen belül marad, amíg `f < L²/(L+off)` — a középfókusz
    (a golden-készlet minden esete) mindig ilyen. Ennél szélsőbb fókusznál a
    sor vége a képen túl mintázna; ott a szélső képpontot vesszük (vágás).
    Ezt a peremesetet golden-pár nem méri.
    """
    scale = np.float32(length / (length + offset))
    shift = np.float32(offset * focus_px / length)
    pos = np.arange(length, dtype=np.float32) + np.float32(0.5)
    u = pos * scale + shift
    fixed = np.floor(u * np.float32(65536.0)).astype(np.int64)
    return np.clip(fixed >> 16, 0, length - 1)


def zoom_blend_step(acc: np.ndarray, sample: np.ndarray) -> np.ndarray:
    """Egy minta ráfeszítése az akkumulátorra (#3883), `uint8` → `uint8`.

    `acc = (38·minta + 217·acc) >> 8` — a Picasa SSE2-ágának súlya
    (`0x00bcf0f9`), egészben. **A sávhibával együtt:** a négysávos ciklus
    csak a csoport első két képpontját bontja ki (`0x00bcf345`,
    `0x00bcf349`), ezért soronként a négyes csoportok 2. és 3. képpontja a
    0. és az 1. képpont (előző) akkumulátorával kever. A sor végi ≤ 3
    képpontos maradék (`0x00bcf444`) a sajátjával. A Picasa kimenete ezt a
    négyes periódusú mintát hordozza, tehát nekünk is kell.
    """
    full = (acc.shape[1] // 4) * 4
    weighted_acc = acc.astype(np.uint16)
    weighted_acc *= np.uint16(_ZOOM_ACC_WEIGHT)
    weighted_acc[:, 2:full:4] = weighted_acc[:, 0:full:4]
    weighted_acc[:, 3:full:4] = weighted_acc[:, 1:full:4]
    mixed = sample.astype(np.uint16)
    mixed *= np.uint16(_ZOOM_SAMPLE_WEIGHT)
    mixed += weighted_acc  # legfeljebb 255·255 — elfér uint16-ban
    mixed >>= 8
    return mixed.astype(np.uint8)


def zoom_blur(
    image: np.ndarray, x: float, y: float, impact: float, *, gyors: bool = False
) -> np.ndarray:
    """A `RadialBlurImageOperation` magja (`0x00bcf4b0`, #3883) — `uint8`.

    Az akkumulátor a forrás másolata; `zoom_offsets` sorrendjében minden
    eltoláshoz a forrásból legközelebbi szomszéddal vett minta
    (`zoom_sample_indices`, a két tengely külön — a mátrix átlós) keveredik
    rá (`zoom_blend_step`). A függőleges eltoláshoz is a `W`-ből számolt
    `D` tartozik, de a léptékarány tengelyenként más: `H/(H+off)`.

    `gyors=True`: CSAK a csúszka-húzás közbeni élő előnézetnek (a
    `gyors_elonezet` blokk, #3846 mintájára). Ugyanazok a mintaindexek, de
    OpenCV-vel (`remap` + `addWeighted`): kerekítve, sávhiba nélkül. A natív
    út 2560 px-en ~1,7× lassabb a régi, átlagoló OpenCV-útnál; a gyors út
    ennél is gyorsabb, és szemre ugyanazt a zoomot adja.
    """
    height, width = image.shape[:2]
    offsets = zoom_offsets(zoom_sample_count(impact), zoom_max_offset(width, impact))
    focus_x = float(x) * width
    focus_y = float(y) * height
    steps = [
        (
            zoom_sample_indices(height, off, focus_y),
            zoom_sample_indices(width, off, focus_x),
        )
        for off in offsets
    ]
    if gyors and max(height, width) <= _REMAP_MAX_SIZE:
        return _zoom_blur_gyors(image, steps)
    return _zoom_blur_nativ(image, steps)


def _zoom_blur_gyors(
    image: np.ndarray, steps: list[tuple[np.ndarray, np.ndarray]]
) -> np.ndarray:
    """Az élő előnézet útja: `remap` egész indextérképpel (pontosan a natív
    minta), `addWeighted` 38/256 · 217/256 súllyal (sávhiba nélkül)."""
    height, width = image.shape[:2]
    index_map = np.empty((height, width, 2), dtype=np.int16)
    acc = image
    for rows, cols in steps:
        index_map[..., 0] = cols[np.newaxis, :]
        index_map[..., 1] = rows[:, np.newaxis]
        sample = cv2.remap(image, index_map, None, cv2.INTER_NEAREST)
        # a −0,5 a natív `>> 8` csonkítását közelíti (a kerekítés helyett)
        acc = cv2.addWeighted(
            sample, _ZOOM_SAMPLE_WEIGHT / 256.0, acc, _ZOOM_ACC_WEIGHT / 256.0, -0.5
        )
    return acc.copy() if acc is image else acc


def _zoom_blur_nativ(
    image: np.ndarray, steps: list[tuple[np.ndarray, np.ndarray]]
) -> np.ndarray:
    """A natív út: `zoom_blend_step` egészben, a sávhibával."""
    height = image.shape[0]
    # A sorok egymástól függetlenek (a minta a FORRÁSBÓL jön, a keverés
    # soron belüli), ezért sávonként végigvihető minden lépés: a sáv a
    # gyorsítótárban marad, és nem kell teljes képméretű köztes tömb.
    out = np.empty_like(image)
    for top in range(0, height, _ZOOM_BAND_ROWS):
        bottom = min(top + _ZOOM_BAND_ROWS, height)
        acc = image[top:bottom].copy()
        for rows, cols in steps:
            sample = np.take(np.take(image, rows[top:bottom], axis=0), cols, axis=1)
            acc = zoom_blend_step(acc, sample)
        out[top:bottom] = acc
    return out


def apply_focal_zoom(
    image: np.ndarray,
    x: float = 0.5,
    y: float = 0.5,
    impact: float = 50.0,
    radius: float = 10.0,
    hardness: float = 50.0,
    fade: float = 0.0,
    scale: float = 1.0,
    *,
    gyors: bool = False,
) -> np.ndarray:
    """`FocalZoom=1,x,y,Impact,Radius,Hardness,Fade` — sugárirányú (zoom)
    elmosás a fókuszpont körül (#570).

    A natív mag (`zoom_blur`, #3883) `N = min(trunc(Impact) + 5, 30)`
    legközelebbi-szomszéd mintát kever egymás után az akkumulátorra
    (38/217-es súllyal, a Picasa sávhibájával); a legnagyobb zoomeltolás
    `floor(width · Impact / 200)` pixel. A kész elmosás a **körmaszk**
    szerint, a `MaskInstruction` egész képletével keveredik az élesen maradó
    középpontra, végül a `Fade` a szokásos `1 − Fade/100` súllyal zár.

    `D = 0` mellett (keskeny kép vagy `Impact = 0`) a kép változatlan.
    A `gyors` a húzás közbeni élő előnézet útja (`zoom_blur`).
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
    if zoom_max_offset(width, impact) <= 0:
        blurred = image
    else:
        blurred = zoom_blur(image, x, y, impact, gyors=gyors)

    # a körmaszk a `MaskInstruction` egész képletével keveri a kernelt az
    # élesen maradó középpontra (`masked_blend`, #3442)
    mask = focal_mask(height, width, x, y, radius, hardness, scale)
    image_f = image.astype(np.float32)
    focused = masked_blend(image_f, blurred.astype(np.float32), mask)
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
    reverse: bool = False,
) -> np.ndarray:
    """`PicnikFocalPixelate=1,x,y,Impact,Radius,Hardness,Fade` (#570).

    A natív recept: lekicsinyítés `W/Impact × H/Impact` méretre a közös
    `Resize`-zal (`resize_image`, fixpontos doboz, #3805), majd
    visszanagyítás `W × H`-ra **`smoothing = false`** módban — vagyis
    legközelebbi-szomszéd, nem interpoláció (ettől lesznek éles blokkjai, nem
    elmosódott foltjai). Ugyanaz a körmaszk és `Fade`, mint a `FocalZoom`-nál.

    #788: a `reverse` a felület ötödik vezérlője (`_chkReverse`, alapból ki).
    A `filterdesc.xml` ezt **a körmaszk két alfájának cseréjével** valósítja
    meg (`outerAlpha = Reverse ? 0 : 1`, `innerAlpha = Reverse ? 1 : 0`), nem
    külön ággal — ezért itt sincs külön ág. Alaphelyzetben a kör KÖZEPE marad
    éles, fordítva épp az lesz pixeles.
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
    # a közös `Resize` (#3805): kicsinyítéskor a `ytResampler` fixpontos
    # doboza, visszafelé `smoothing=false` → legközelebbi szomszéd
    small = resize_image(image, small_w, small_h, smoothing=True)
    pixelated = resize_image(small, width, height, smoothing=False).astype(np.float32)

    mask = focal_mask(
        height,
        width,
        x,
        y,
        radius,
        hardness,
        scale,
        inner_alpha=1.0 if reverse else 0.0,
        outer_alpha=0.0 if reverse else 1.0,
    )[..., np.newaxis]
    focused = image_f + mask * (pixelated - image_f)
    weight = np.float32(np.clip(1.0 - fade / 100.0, 0.0, 1.0))
    return _to_uint8(image_f + weight * (focused - image_f))


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


__all__ = [
    "apply_focal_pixelate",
    "apply_focal_zoom",
    "focal_mask",
    "zoom_blend_step",
    "zoom_blur",
    "zoom_max_offset",
    "zoom_offsets",
    "zoom_sample_count",
    "zoom_sample_indices",
]

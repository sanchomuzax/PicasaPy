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

from typing import NamedTuple

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


class _ZoomStep(NamedTuple):
    """Egy natív SSE2-lépés levágott célterülete és 16.16-os forrásindexei."""

    x_start: int
    y_start: int
    x_indices: np.ndarray
    y_indices: np.ndarray
    valid_rows: np.ndarray


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
    """`⌊width · trunc(Impact) / 200⌋` — a legnagyobb zoomeltolás pixelben.

    A mag az egésszé csonkolt `amount`-ot kapja, és egészben szoroz
    (`0x00bcf4d7 mul edx`), tehát kézzel írt tört Impactnél is csonkolunk."""
    return (width * int(max(impact, 0.0))) // _ZOOM_OFFSET_DIVISOR


def zoom_offsets(samples: int, max_offset: int) -> tuple[int, ...]:
    """A minták eltolása a natív sorrendben (#3883): `k = N … 1`,
    `off = ⌊k·D / N⌋` — a legnagyobb eltolás jön ELŐSZÖR (`0x00bcf58e`,
    `0x00bcf93e`)."""
    if samples <= 0:
        return ()
    return tuple((k * max_offset) // samples for k in range(samples, 0, -1))


def zoom_sample_indices(length: int, offset: int, focus_px: float) -> np.ndarray:
    """Az ideális egytengelyes leképezés legközelebbi-szomszéd indexei (#3883).

    Ez a képlet-segéd külön-külön számolja ki a pixeleket. A natív
    `zoom_blur` SSE2-útja ehelyett az affine mátrixból épített, egész
    16.16-os léptetőtáblát és levágott ROI-t használja; azt a
    `_zoom_native_steps` valósítja meg. A segéd képen belüli clampje ezért
    nem a natív peremkezelés modellje.

    A cél → forrás mátrix egy tengelyre `u = (X + 0,5)·L/(L+off) + off·f/L`
    (`f` a fókusz képpontban), float32-ben; az index `⌊65536·u⌋ >> 16` — a
    natív 16.16 fixpont, interpoláció nélkül. A mátrix fix pontja
    `f·(L+off)/L`, nem pontosan `f`.

    A képlet a képen belül marad, amíg `f < L²/(L+off)` — a középfókusz
    (a golden-készlet minden esete) mindig ilyen. Mivel a függőleges eltolás
    is a szélességből jön, fekvő képen a függőleges tengely már közepes
    fókusznál túllép (2560×1707, Impact 100: `y = 0,6`-tól). Ott a szélső
    képpontot vesszük (vágás) — ez a MI feltevésünk, a Picasa viselkedése
    nincs kiolvasva (#3893), és golden-pár sem méri.
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
    kevert_acc = acc.copy()
    kevert_acc[:, 2:full:4] = acc[:, 0:full:4]
    kevert_acc[:, 3:full:4] = acc[:, 1:full:4]
    weighted_acc = np.multiply(kevert_acc, _ZOOM_ACC_WEIGHT, dtype=np.uint16)
    mixed = np.multiply(sample, _ZOOM_SAMPLE_WEIGHT, dtype=np.uint16)
    mixed += weighted_acc  # legfeljebb 255·255 — elfér uint16-ban
    mixed >>= 8
    return mixed.astype(np.uint8)


def zoom_blur(
    image: np.ndarray, x: float, y: float, impact: float, *, gyors: bool = False
) -> np.ndarray:
    """A `RadialBlurImageOperation` magja (`0x00bcf4b0`, #3883) — `uint8`.

    A `zoom_offsets` sorrendjében a natív SSE2-út a célterületet az affine
    mátrix inverzével levágja, majd soronként 16.16-os koordinátatáblát épít.
    Az első lane kezdőértéke a leképezett pixelközép; a lane-lépés a
    float32 mátrixelem `65536`-tal szorozva, nullához csonkolva. A következő
    lane-ek és négyes csoportok egész összeadással készülnek. A képen kívüli
    célpixelek kimaradnak, nem a szélső forráspixelre szorulnak.

    `gyors=True`: CSAK a csúszka-húzás közbeni élő előnézetnek (a
    `gyors_elonezet` blokk, #3846 mintájára). Ugyanezt a natív léptetőtáblát
    használja, OpenCV-vel (`remap` + `addWeighted`): kerekítve, sávhiba nélkül.
    """
    height, width = image.shape[:2]
    if not width or not height:
        return image.copy()
    focus_x = np.float32(float(x) * width)
    focus_y = np.float32(float(y) * height)
    steps = _zoom_native_steps(height, width, focus_x, focus_y, impact)
    if gyors and max(height, width) <= _REMAP_MAX_SIZE:
        return _zoom_blur_gyors(image, steps)
    return _zoom_blur_nativ(image, steps)


def _zoom_native_steps(
    height: int, width: int, focus_x: np.float32, focus_y: np.float32, impact: float
) -> list[_ZoomStep]:
    """A Picasa SSE2-út 16.16-os léptetőtáblája és levágott cél-ROI-ja.

    A magban (`0x00bcf4cb`–`0x00bcf58e`) minden lépés egész `off` értéke
    saját affine mátrixot épít. A transform (`0x00bcefb0`) a float32
    mátrixelemekből egyszer csonkolt 16.16-os lépést készít, majd négyes
    lane-ekkel halad; nem értékeli újra lebegőpontos képlettel minden célpixel
    koordinátáját. A `0xa4a140`/`0xa4a240` a forrástéglalapot a célba
    vetíti, a `0x9aaae0` metszi a kimenettel. A peremsor jobb végét a mag
    `0xbcf2a2`–`0xbcf2e9` ellenőrzi a 16.16-os forrásindex alapján.
    """
    steps: list[_ZoomStep] = []
    offsets = zoom_offsets(zoom_sample_count(impact), zoom_max_offset(width, impact))
    for off in offsets:
        # A mag `D`-t szélességből számolja, de a függőleges skála magasságú.
        # Az x87 elsőként float32-be írja az osztást, majd annak reciprokát
        # is float32-ként tárolja (`0x00bcf61e`–`0x00bcf628`, `0x00bcf642`–`0x00bcf64a`).
        scale_x_ratio = np.float32((width + off) / width)
        scale_y_ratio = np.float32((height + off) / height)
        scale_x = np.float32(1.0 / float(scale_x_ratio))
        scale_y = np.float32(1.0 / float(scale_y_ratio))

        # A bináris a fókusz komplementerét (`W-x`, `H-y`) szorozza az
        # eltolással, elosztja a dimenzióval, majd ezt vonja le az offból.
        # A köztes hányados float32-be kerül a kivonás előtt.
        tx_remainder = np.float32(off * (width - float(focus_x)) / width)
        ty_remainder = np.float32(off * (height - float(focus_y)) / height)
        shift_x = np.float32(off - float(tx_remainder))
        shift_y = np.float32(off - float(ty_remainder))

        # `a4a140`/`a4a240`: a forrás-téglalap inverz leképezése. A helper a
        # határból 0,499-et von le, majd az x87 FISTP nearest-even módjával
        # egész célhatárt készít. Python round ugyanezt a ties-to-even szabályt
        # használja; a végén a téglalap a célkép határaival metsződik.
        x_start = max(0, round((0.0 - float(shift_x)) / float(scale_x) - 0.499))
        x_stop = min(
            width,
            round((width - float(shift_x)) / float(scale_x) - 0.499),
        )
        y_start = max(0, round((0.0 - float(shift_y)) / float(scale_y) - 0.499))
        y_stop = min(
            height,
            round((height - float(shift_y)) / float(scale_y) - 0.499),
        )
        if x_stop <= x_start or y_stop <= y_start:
            continue

        # A target->source koordinátát float32-ben tárolja az x87 út, utána
        # a `0xc0b1e0`/`0xc29990` konverzió nullához csonkol 16.16-ra.
        # Az x tengely `m00` lépése a négylane-es táblába kerül; a radial
        # mátrix `m10=0`, ezért a soron belüli y-lane-ek azonosak.
        base_x = np.float32(float(scale_x) * (x_start + 0.5) + float(shift_x))
        fixed_x_start = int(float(base_x) * 65536.0)
        fixed_x_step = int(float(scale_x) * 65536.0)
        x_fixed = fixed_x_start + np.arange(x_stop - x_start, dtype=np.int64) * fixed_x_step
        x_indices = x_fixed >> 16

        # A SSE2-sor végén a mintán kívüli célpixelek kimaradnak. Zoomnál a
        # vízszintes leképezés monoton, ezért a jobb szélt elég visszavágni.
        x_count = len(x_indices)
        while x_count and (x_indices[x_count - 1] < 0 or x_indices[x_count - 1] >= width):
            x_count -= 1
        x_indices = x_indices[:x_count]
        if not x_count:
            continue

        rows = np.arange(y_start, y_stop, dtype=np.float64)
        base_y = np.float32(shift_y)  # m10=0 a RadialBlur diagonális mátrixában.
        y_mapped = np.asarray(
            np.float32(scale_y) * (rows + 0.5) + base_y, dtype=np.float32
        )
        y_fixed = (y_mapped.astype(np.float64) * 65536.0).astype(np.int64)
        y_indices = y_fixed >> 16
        valid_rows = (y_indices >= 0) & (y_indices < height)
        steps.append(_ZoomStep(x_start, y_start, x_indices, y_indices, valid_rows))
    return steps


def _zoom_blur_gyors(
    image: np.ndarray, steps: list[_ZoomStep]
) -> np.ndarray:
    """Az élő előnézet útja: natív léptetőtábla, OpenCV-keverés, sávhiba nélkül."""
    height, width = image.shape[:2]
    index_map = np.empty((height, width, 2), dtype=np.int16)
    out = image.copy()
    for step in steps:
        x_end = step.x_start + len(step.x_indices)
        y_end = step.y_start + len(step.y_indices)
        index_map.fill(0)
        index_map[step.y_start:y_end, step.x_start:x_end, 0] = step.x_indices[
            np.newaxis, :
        ]
        index_map[step.y_start:y_end, step.x_start:x_end, 1] = np.clip(
            step.y_indices, 0, height - 1
        )[:, np.newaxis]
        sample = cv2.remap(image, index_map, None, cv2.INTER_NEAREST)
        # a −0,5 a natív `>> 8` csonkítását közelíti (a kerekítés helyett)
        mixed = cv2.addWeighted(
            sample, _ZOOM_SAMPLE_WEIGHT / 256.0, out, _ZOOM_ACC_WEIGHT / 256.0, -0.5
        )
        region = out[step.y_start:y_end, step.x_start:x_end]
        mixed_region = mixed[step.y_start:y_end, step.x_start:x_end]
        region[step.valid_rows] = mixed_region[step.valid_rows]
    return out


def _zoom_blur_nativ(
    image: np.ndarray, steps: list[_ZoomStep]
) -> np.ndarray:
    """A natív út: `zoom_blend_step` egészben, a sávhibával."""
    height = image.shape[0]
    out = image.copy()
    for step in steps:
        x_end = step.x_start + len(step.x_indices)
        y_end = step.y_start + len(step.y_indices)
        for top in range(step.y_start, y_end, _ZOOM_BAND_ROWS):
            bottom = min(top + _ZOOM_BAND_ROWS, y_end)
            row_start = top - step.y_start
            row_end = bottom - step.y_start
            valid = step.valid_rows[row_start:row_end]
            if not valid.any():
                continue
            rows = np.clip(step.y_indices[row_start:row_end], 0, height - 1)
            sample = image[rows[:, np.newaxis], step.x_indices[np.newaxis, :]]
            region = out[top:bottom, step.x_start:x_end]
            mixed = zoom_blend_step(region, sample)
            region[valid] = mixed[valid]
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
    `⌊width · trunc(Impact) / 200⌋` pixel. A kész elmosás a **körmaszk**
    szerint, a `MaskInstruction` egész képletével keveredik az élesen maradó
    középpontra, végül a `Fade` a szokásos `1 − Fade/100` súllyal zár.

    `D = 0` mellett is lefut a natív mintaciklus: az `N` darab null-eltolású
    minta a 38/217-es képlettel ismételten az akkumulátorra keveredik.
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

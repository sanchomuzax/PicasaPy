"""Keret-/árnyék-primitívek a Glimmer-effektekhez (#381) — a `glimmer_ops.py`
testvérmodulja, KÜLÖN fájlban, hogy egyik se lépje át a 800 soros korlátot.

`BorderImageOperation`, `DropShadow` és `Rotate(padBorder)` közös építőkövei:
szegélygyűrű, sarok-lekerekítés, felirat-sáv, vetett árnyék, kibővített
vászonra forgatás. Ezeket használja a `Border`, `RoundedEdges`,
`MuseumMatte`, `Sixties` (sarok-lekerekítés), `DropShadow` és `Polaroid`
csővezetéke (`glimmer_frames.py`).
"""

from __future__ import annotations

import math

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.fixpontos_mintavevo import fixpontos_bilinearis
from picasapy.render.glimmer_ops import fade_alpha
from picasapy.render.nativ_blur import nativ_blur_csatorna

_BORDER_Q_X_SLOPE = 240


def add_ring(image: np.ndarray, thickness: float, color: tuple[int, int, int]) -> np.ndarray:
    """Egyetlen egyenletes szegélygyűrű hozzáadása — a vastagság PIXELBEN.

    #317: korábban a vastagságot a rövidebb oldal SZÁZALÉKÁNAK vettük, ezért
    egy 2560×1702-es fotón az alapértelmezett Museum Matte 1447 px-es (!)
    keretet rakott 65 helyett — a kimenet 5454×4596-ra hízott. A
    `referencia/museummatte/` hét exportja pixelre eldöntötte a kérdést: a
    hozzáadott keret oldalanként PONTOSAN `Outer + Inner` pixel
    (0/50/100-as külső és 0/100-as belső állásokon egyaránt).
    """
    validate_image(image)
    px = max(0, int(round(thickness)))
    if px == 0:
        return image.copy()
    return cv2.copyMakeBorder(image, px, px, px, px, cv2.BORDER_CONSTANT, value=color)


def add_border_sides(
    image: np.ndarray, left: int, right: int, top: int, bottom: int, color: tuple[int, int, int]
) -> np.ndarray:
    """Aszimmetrikus (oldalanként eltérő vastagságú) szegély, pixelben megadva."""
    validate_image(image)
    left, right, top, bottom = (max(0, int(round(v))) for v in (left, right, top, bottom))
    if left == right == top == bottom == 0:
        return image.copy()
    return cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)


def round_corners(
    image: np.ndarray, corner_radius_px: float, fill_color: tuple[int, int, int]
) -> np.ndarray:
    """A kép sarkainak lekerekítése: a levágott sarok-háromszögeket
    `fill_color`-ral tölti ki (nincs alfa-csatornánk, ezért a kivágott
    sarok a HÁTTÉRSZÍNNEL — jellemzően a keret külső színével — látszik).
    """
    validate_image(image)
    radius = int(round(corner_radius_px))
    if radius <= 0:
        return image.copy()
    height, width = image.shape[:2]
    radius = min(radius, height // 2, width // 2)
    if radius <= 0:
        return image.copy()
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.rectangle(mask, (radius, 0), (width - radius, height), 1, -1)
    cv2.rectangle(mask, (0, radius), (width, height - radius), 1, -1)
    for corner_x, corner_y in (
        (radius, radius),
        (width - radius, radius),
        (radius, height - radius),
        (width - radius, height - radius),
    ):
        cv2.circle(mask, (corner_x, corner_y), radius, 1, -1)
    color_arr = np.array(fill_color, dtype=image.dtype)
    filled = np.empty_like(image)
    filled[:] = color_arr
    return np.where(mask[..., np.newaxis] == 1, image, filled)


def _sarok_fedes(
    q: np.ndarray,
    belso_negyzetes_tav: float,
    kulso_negyzetes_tav: float,
) -> np.ndarray:
    """A natív 16.16-os `0x00aa1840` fedési súlyai, 0…256 tartományban.

    A távolságokat és a kerekítési sorrendet a `docs/specs/filterdesc-registry.md`
    Border I. szakasza rögzíti. A belső körön a súly 256, a külsőn kívül 0;
    csak a köztes gyűrűn fut a natív egészszorzás.
    """
    if kulso_negyzetes_tav <= belso_negyzetes_tav:
        raise ValueError("a külső négyzetes távolságnak nagyobbnak kell lennie")

    q = np.asarray(q, dtype=np.int64)
    skala = (2**24) // int(kulso_negyzetes_tav - belso_negyzetes_tav)
    fedes = np.zeros(q.shape, dtype=np.uint16)
    fedes[q <= belso_negyzetes_tav] = 256
    reszleges = (q > belso_negyzetes_tav) & (q < kulso_negyzetes_tav)
    fedes[reszleges] = (
        ((kulso_negyzetes_tav - q[reszleges]) * skala) >> 16
    ).astype(np.uint16)
    return fedes


def _border_q_racs(sugar: int) -> np.ndarray:
    """A Border natív `2*sugar` négyzetes q-rácsa (`aa1840`, I.4)."""
    koordinata = np.arange(2 * sugar, dtype=np.int64)
    x = koordinata[np.newaxis, :]
    y = koordinata[:, np.newaxis]
    dx = x - sugar + 1
    dy = y - sugar + 1
    return 256 * (dx * dx + dy * dy) - _BORDER_Q_X_SLOPE * x


def _fedett_forras_alfa(forras_alfa: int, fedes: int) -> int:
    """A forrás alfája a görbe fedésével súlyozva (`(A·C)>>8`)."""
    return (forras_alfa * fedes) >> 8


def _kompozit_alfa(cel_alfa: int, forras_alfa: int) -> int:
    """A `0x009ab410` alfa-képlete egy opaque cél fölött is megőrzi az ff-et."""
    return ((cel_alfa * (256 - forras_alfa)) >> 8) + forras_alfa


def _kever_reszleges_argb(cel: int, forras: int, fedes: int) -> int:
    """A natív packed ARGB-keverés egy pixelre, az eredeti shift-sorrenddel."""
    if fedes <= 0:
        return cel

    cel_csatornak = [(cel >> shift) & 0xFF for shift in (24, 16, 8, 0)]
    forras_csatornak = [(forras >> shift) & 0xFF for shift in (24, 16, 8, 0)]
    alfa = forras_csatornak[0]

    if fedes >= 256:
        # A teljes fedésű ág a skálázott cél-dwordhoz egyetlen dwordként adja
        # hozzá a forrást; az átvitel is a natív része ennek az útnak.
        vissza = 256 - alfa
        cel_dword = sum(
            ((csatorna * vissza) >> 8) << shift
            for csatorna, shift in zip(cel_csatornak, (24, 16, 8, 0), strict=True)
        )
        return (cel_dword + forras) & 0xFFFFFFFF

    alfa_resz = _fedett_forras_alfa(alfa, fedes)
    inverz = 255 - alfa_resz
    eredmeny = 0
    for index, shift in enumerate((24, 16, 8, 0)):
        cel_cs = cel_csatornak[index]
        forras_cs = forras_csatornak[index]
        if shift in (16, 0):  # R/B: az összeg a shift előtt készül.
            csatorna = (cel_cs * inverz + forras_cs * fedes) >> 8
        else:  # G/alfa: a két tag külön shiftelődik.
            csatorna = ((cel_cs * inverz) >> 8) + ((forras_cs * fedes) >> 8)
        eredmeny |= (csatorna & 0xFF) << shift
    return eredmeny


def _raszterez_kor(
    q: np.ndarray,
    *,
    belso_negyzetes_tav: float,
    kulso_negyzetes_tav: float,
    forras_argb: int,
    cel_argb: int,
) -> np.ndarray:
    """Fedett kör natív ARGB-raszterezése és opaque cél fölötti kompozitja."""
    fedesek = _sarok_fedes(q, belso_negyzetes_tav, kulso_negyzetes_tav)
    eredmeny = np.empty(fedesek.shape, dtype=np.uint32)
    cel_alfa = (cel_argb >> 24) & 0xFF
    for index in np.ndindex(fedesek.shape):
        koztes = _kever_reszleges_argb(cel_argb, forras_argb, int(fedesek[index]))
        alfa = _kompozit_alfa(cel_alfa, (koztes >> 24) & 0xFF)
        eredmeny[index] = (koztes & 0x00FFFFFF) | (alfa << 24)
    return eredmeny


def _kever_rgb_fedessel(cel: np.ndarray, forras: np.ndarray, fedes: np.ndarray) -> np.ndarray:
    """RGB színek keverése a natív fedési súlyok csatornasorrendjével."""
    cel_u32 = np.asarray(cel, dtype=np.uint32)
    forras_u32 = np.asarray(forras, dtype=np.uint32)
    fedes_u32 = np.asarray(fedes, dtype=np.uint32)[..., np.newaxis]
    alfa_resz = (255 * fedes_u32) >> 8
    inverz = 255 - alfa_resz
    reszleges_rb = (cel_u32 * inverz + forras_u32 * fedes_u32) >> 8
    reszleges_g = ((cel_u32[..., 1:2] * inverz) >> 8) + (
        (forras_u32[..., 1:2] * fedes_u32) >> 8
    )
    reszleges = np.concatenate(
        (reszleges_rb[..., 0:1], reszleges_g, reszleges_rb[..., 2:3]), axis=-1
    )
    reszleges = np.clip(reszleges, 0, 255).astype(np.uint8)
    return np.where(
        fedes_u32 == 0,
        cel_u32.astype(np.uint8),
        np.where(fedes_u32 == 256, forras_u32.astype(np.uint8), reszleges),
    )


def _kompozital_forrassarok(
    cel: np.ndarray, forras: np.ndarray, fedes: np.ndarray
) -> np.ndarray:
    """A Border forrássarkának `9ab360` maszkalfája és `/255` kompozitja."""
    cel_u32 = np.asarray(cel, dtype=np.uint32)
    forras_u32 = np.asarray(forras, dtype=np.uint32)
    alfa = (255 * np.asarray(fedes, dtype=np.uint32)) >> 8
    alfa = alfa[..., np.newaxis]
    return (
        (cel_u32 * (255 - alfa) + forras_u32 * alfa) // 255
    ).astype(np.uint8)


def draw_border(
    image: np.ndarray,
    outer_color: tuple[int, int, int],
    inner_color: tuple[int, int, int],
    outer_thickness: float,
    inner_thickness: float,
    corner_radius_px: float = 0.0,
    caption_height_px: float = 0.0,
) -> np.ndarray:
    """`BorderImageOperation` a natív külön külső- és forrássarok-ráccsal.

    A két élsimított ív a `docs/specs/filterdesc-registry.md` I.4 képleteit
    követi. A keretsáv q-rácsa külön a kép sarkainál fut; a forrás q-rácsa
    csak a négy forrássarok-pixelblokkot kompozitálja. A feliratsáv magassága
    továbbra is csonkított egész (`0x008eea90`).
    """
    validate_image(image)
    height, width = image.shape[:2]
    belso = max(0, int(round(inner_thickness)))
    kulso = max(0, int(round(outer_thickness)))
    felirat = max(0, int(caption_height_px))
    sugar = max(0, min(int(round(corner_radius_px)), height // 2, width // 2))
    keret = kulso + belso
    vaszon = np.empty((height + 2 * keret + felirat, width + 2 * keret, 3), dtype=image.dtype)
    vaszon[:] = np.asarray(outer_color, dtype=image.dtype)
    vaszon[kulso : kulso + height + 2 * belso, kulso : kulso + width + 2 * belso] = np.asarray(
        inner_color, dtype=image.dtype
    )
    vaszon[keret : keret + height, keret : keret + width] = image
    if sugar == 0:
        return vaszon

    n = sugar + belso
    kulso_sugar = min(
        int(np.float32(n) + np.float32(1.0)),
        (width + 2 * belso) // 2,
        (height + 2 * belso) // 2,
    )
    if kulso_sugar > 0:
        kulso_q = _border_q_racs(kulso_sugar)
        kulso_ri2 = 256 * kulso_sugar**2 - 256 * kulso_sugar + 64
        kulso_ro2 = 256 * kulso_sugar**2 + 256 * kulso_sugar + 64
        kulso_fedes = _sarok_fedes(kulso_q, kulso_ri2, kulso_ro2)
        kulso_folt = _kever_rgb_fedessel(
            np.asarray(outer_color, dtype=np.uint8),
            np.asarray(inner_color, dtype=np.uint8),
            kulso_fedes,
        )
        for also, y_racs in (
            (kulso, slice(0, kulso_sugar)),
            (kulso + height + 2 * belso - kulso_sugar, slice(kulso_sugar, 2 * kulso_sugar)),
        ):
            for bal, x_racs in (
                (kulso, slice(0, kulso_sugar)),
                (kulso + width + 2 * belso - kulso_sugar, slice(kulso_sugar, 2 * kulso_sugar)),
            ):
                vaszon[
                    also : also + kulso_sugar,
                    bal : bal + kulso_sugar,
                ] = kulso_folt[y_racs, x_racs]

    source_q = _border_q_racs(sugar)
    source_ri2 = 256 * (sugar - 1) ** 2
    source_ro2 = 256 * sugar**2
    source_fedes = _sarok_fedes(source_q, source_ri2, source_ro2)
    bel = np.asarray(inner_color, dtype=np.uint8)
    for y_canvas, y_source, y_racs in (
        (keret, slice(0, sugar), slice(0, sugar)),
        (keret + height - sugar, slice(height - sugar, height), slice(sugar, 2 * sugar)),
    ):
        for x_canvas, x_source, x_racs in (
            (keret, slice(0, sugar), slice(0, sugar)),
            (keret + width - sugar, slice(width - sugar, width), slice(sugar, 2 * sugar)),
        ):
            cel = np.broadcast_to(bel, (sugar, sugar, 3))
            kep_sarok = image[y_source, x_source]
            vaszon[
                y_canvas : y_canvas + sugar,
                x_canvas : x_canvas + sugar,
            ] = _kompozital_forrassarok(cel, kep_sarok, source_fedes[y_racs, x_racs])
    return vaszon


#: #649/#626/#3809: a `DropShadowImageOperation` árnyék-eltolása
#: (`0x00bcdea0`):
#:
#:     dx = floor( (cos(szög·π/180) + 6,7e−06) · távolság + 0,001825 )
#:     dy = floor( (sin(szög·π/180) + 6,7e−06) · távolság + 0,001825 )
#:
#: A két apró szám NEM paraméter, hanem lebegőpontos védelem: a 2,9999…
#: alakban kijövő, valójában egész szorzatot emeli az egész fölé, mielőtt a
#: `floor` lecsípné (`docs/specs/filterdesc-registry.md`, „A Polaroid
#: geometriája”).
_SHADOW_TIE_SLOPE = 6.7e-06
_SHADOW_TIE_OFFSET = 0.001825


def shadow_offset(distance_px: float, angle: float) -> tuple[int, int]:
    """Az árnyék (dx, dy) eltolása a natív képlettel (#649, #3809).

    A kerekítés `floor` (`0x00bcdece` `call 0x00c0b1e0`), nem C-`round`: a
    (távolság 0–30, szög 0–359°) párok 71%-ánál a kettő eltér — például az
    alapértelmezett 4 / 45°-nál `(2, 2)` a natív, nem `(3, 3)`. Tengelyirányú
    szögnél (0°, 90°, 180°, 270°) a kettő egybeesik.
    """
    radian = math.radians(angle)
    return (
        math.floor(
            (math.cos(radian) + _SHADOW_TIE_SLOPE) * distance_px
            + _SHADOW_TIE_OFFSET
        ),
        math.floor(
            (math.sin(radian) + _SHADOW_TIE_SLOPE) * distance_px
            + _SHADOW_TIE_OFFSET
        ),
    )


#: A `DropShadow` határoló-doboz kiterjesztőjének (`0x00bcd760`) szorzója a
#: leíró `quality="{BitmapFilterQuality.HIGH}"` (= 3) fokozatán, `0x00cf4368`.
_DROPSHADOW_HIGH_FAKTOR = 1.3501
#: `quality="{BitmapFilterQuality.HIGH}"` (`filterdesc.xml`) = 3: a natív
#: elmosás 3 vízszintes + 3 függőleges menete (#3474, `0x00bc7540`/`0x00bc77b0`).
_DROPSHADOW_QUALITY = 3
#: A paraméter-vágó (`0x00bcd640`) a `blurX`/`blurY`-t erre a tartományra szorítja.
_DROPSHADOW_BLUR_MIN = 1.0
_DROPSHADOW_BLUR_MAX = 255.0


def drop_shadow_padding(
    distance: float, angle: float, blur: float
) -> tuple[float, tuple[int, int], tuple[int, int, int, int]]:
    """A `DropShadow` vásznának oldalankénti bővítése (#3419).

    A `0x00bcd760` a képet oldalanként `ceil(blur · 1,3501)` képponttal
    tágítja; a `blur` KÉPPONT, `clamp(1, 255)`. A kitágított dobozt az
    árnyék `(dx, dy)` eltolja, és a kimenet a kettő UNIÓJA az eredeti
    képpel — ha az eltolás nagyobb a margónál, a vászon aszimmetrikus.

    Vissza: `(blur_px, (dx, dy), (bal, fent, jobb, lent))`.
    """
    blur_px = min(max(float(blur), _DROPSHADOW_BLUR_MIN), _DROPSHADOW_BLUR_MAX)
    margo = math.ceil(blur_px * _DROPSHADOW_HIGH_FAKTOR)
    dx, dy = shadow_offset(int(round(distance)), angle)
    return (
        blur_px,
        (dx, dy),
        (max(0, margo - dx), max(0, margo - dy), max(0, margo + dx), max(0, margo + dy)),
    )


def teglalap_alfa(shadow_alpha: float) -> int:
    """Az árnyék-téglalap alfa-bájtja (#3498).

    A konstruktor a `shadowAlpha`-t `[0, 1]`-re vágja, és float32-ként tárolja
    (`0x00bcd654`–`0x00bcd68c`); a rajzoló 255-tel szoroz, majd a `fistp`
    ELŐTT a kerekítési módot nulla felé állítja (`0x00bcda7a`: `or 0xc00`).
    Az eredmény tehát CSONKOLT, nem kerekített érték.
    """
    vagott = float(np.float32(min(max(float(shadow_alpha), 0.0), 1.0)))
    return math.trunc(vagott * 255.0)


def compose_drop_shadow(
    image: np.ndarray,
    shadow_color: tuple[int, int, int],
    background_color: tuple[int, int, int],
    distance_px: int,
    angle: float,
    blur_px: float,
    margin: int,
    fade: float = 0.0,
    pads: tuple[int, int, int, int] | None = None,
) -> np.ndarray:
    """A `DropShadow` kompozitálása MÁR KISZÁMOLT pixel-paraméterekkel
    (elmosás-sugár, eltolás, vászon-margó) — az önálló `draw_drop_shadow`
    és a Polaroid rögzített (pixelben megadott) árnyék-receptje közös magja
    (#1144). A hívó felel a `margin` helyes levezetéséért; a `pads`
    (bal, fent, jobb, lent) megadásakor a vászon aszimmetrikus, és a
    `margin` figyelmen kívül marad.
    """
    validate_image(image)
    height, width = image.shape[:2]
    bal, fent, jobb, lent = pads if pads is not None else (margin,) * 4
    canvas_h, canvas_w = height + fent + lent, width + bal + jobb

    # #3474: a natív út (`0x00bcd940`). Az árnyékréteg egyenes BGRA: a teljes
    # vászon `árnyékszín | alfa 0`, a téglalap `TRUNC(shadowAlpha · 255)`
    # alfával (#3498, `teglalap_alfa`). Az elmosás (`0x00bc5680`, quality=3: 3 vízszintes + 3
    # függőleges egész menet) az állandó RGB-t nem változtatja, tehát
    # gyakorlatilag csak az alfát mossa — ezért elég az alfa-csatorna.
    offset_x, offset_y = shadow_offset(distance_px, angle)
    top = fent + offset_y
    left = bal + offset_x
    alfa = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    alfa[top : top + height, left : left + width] = teglalap_alfa(fade_alpha(fade))
    alfa = nativ_blur_csatorna(alfa, blur_px, blur_px, _DROPSHADOW_QUALITY).astype(np.uint32)

    # a keverés (`0x008f48b0`) egész: `(S·α + D·(255 − α)) // 255`
    hatter = np.array(background_color, dtype=np.uint32)
    arnyek = np.array(shadow_color, dtype=np.uint32)
    canvas = (arnyek * alfa[..., np.newaxis] + hatter * (255 - alfa[..., np.newaxis])) // 255
    canvas = canvas.astype(np.uint8)

    canvas[fent : fent + height, bal : bal + width] = image
    return canvas


def draw_drop_shadow(
    image: np.ndarray,
    shadow_color: tuple[int, int, int],
    background_color: tuple[int, int, int],
    distance: float,
    angle: float,
    blur: float,
    fade: float = 0.0,
) -> np.ndarray:
    """`DropShadow`: a kép vetett árnyéka a `background_color` vászonra,
    `distance`/`angle` szerint eltolva, `blur` KÉPPONTNYI elmosással,
    `shadowAlpha = fade_alpha(fade)` átlátszósággal.

    A vászon mérete a bináris kiterjesztőjét követi (`drop_shadow_padding`,
    #3419): a 684-es golden mindhárom állásában képpontra egyezik a valódi
    Picasa-exporttal. A korábbi modell (a `blur` a rövidebb oldal százaléka,
    margó `2·blur + distance`) a `0x00bcd760` szerint mindkét pontján téves
    volt.

    Az elmosás a natív `quality=3` út (#3474, `render/nativ_blur.py`): az
    emulátorban futtatott eredeti kóddal bitre azonos.
    """
    validate_image(image)
    blur_px, _, pads = drop_shadow_padding(distance, angle, blur)
    return compose_drop_shadow(
        image,
        shadow_color,
        background_color,
        int(round(distance)),
        angle,
        blur_px,
        0,
        fade,
        pads=pads,
    )


def rotate_with_pad(
    image: np.ndarray,
    angle_deg: float,
    border_color: tuple[int, int, int],
    *,
    gyors: bool = False,
) -> np.ndarray:
    """`Rotate(..., padBorder, borderColor=...)`: elforgatás a forgatott
    téglalap befoglaló méretű vásznára; az üresen maradó sarkokat
    `border_color` tölti ki.

    #3420: a szög a Picasa `RotateImageOperation degAngle`-je, és POZITÍV
    értéknél az óramutató JÁRÁSA szerint forgat (a 684-es Polaroid-exporton
    `Rotate = 5`-nél a keret felső éle jobbra lejt).

    #1144: a befoglaló méret `csonk(|W·cos θ| + |H·sin θ|)` ×
    `csonk(|W·sin θ| + |H·cos θ|)` (`0x00bc7ca0`) — a Polaroid `818×950`/
    `887×1004` mért kimenete csak így egyezik.

    #3809: a cél → forrás mátrix `T(sW/2, sH/2) · R · T(−dW/2, −dH/2)`
    (`0x00bc8060`), a képpont KÖZEPÉT vetíti vissza, tehát a forrás közepe
    pontosan a cél közepére esik. A mintavétel a natív 8 bites fixpontos
    bilineáris (`fixpontos_mintavevo.fixpontos_bilinearis`). A korábbi út (a kép `//2`-vel a
    vászonra, majd OpenCV-sarok-konvenciós `warpAffine`) fél képpontokat
    tolt el, és a peremen a kitöltő színnel mosott össze.

    `gyors=True` (#3862): CSAK a Polaroid effekt-csúszkájának húzása közbeni
    élő előnézetnek — ugyanaz a képpontközepes mátrix, de `cv2.INTER_LINEAR`
    a mintavevő (az `ops.apply_tilt` `gyors` ágának mintájára, #3846). A
    kilógó sarkokat itt `border_color` tölti ki (nem `BORDER_REPLICATE`,
    mint a Kiegyenesítésnél), mert a Polaroid vásznán VALÓDI, kitöltendő
    sarkok vannak, nem csak a fixpontos mintavevő kerekítési maradéka.
    """
    validate_image(image)
    src_h, src_w = image.shape[:2]
    radian = math.radians(angle_deg)
    cos_a, sin_a = math.cos(radian), math.sin(radian)
    cel_w = int(math.floor(src_w * abs(cos_a) + src_h * abs(sin_a)))
    cel_h = int(math.floor(src_w * abs(sin_a) + src_h * abs(cos_a)))
    # cél → forrás: az óramutató szerinti forgatás inverze
    matrix = (
        cos_a, sin_a, src_w / 2.0 - cos_a * cel_w / 2.0 - sin_a * cel_h / 2.0,
        -sin_a, cos_a, src_h / 2.0 + sin_a * cel_w / 2.0 - cos_a * cel_h / 2.0,
    )
    if gyors:
        m0, m1, m2, m3, m4, m5 = matrix
        # képpontközepes → képpont-index: G = T(−0,5) · M · T(0,5)
        index_matrix = np.array(
            [[m0, m1, m2 + 0.5 * (m0 + m1) - 0.5], [m3, m4, m5 + 0.5 * (m3 + m4) - 0.5]]
        )
        return cv2.warpAffine(
            image,
            index_matrix,
            (cel_w, cel_h),
            flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=border_color,
        )
    return fixpontos_bilinearis(image, matrix, cel_w, cel_h, border_color)


__all__ = [
    "add_ring",
    "add_border_sides",
    "round_corners",
    "draw_border",
    "compose_drop_shadow",
    "teglalap_alfa",
    "shadow_offset",
    "drop_shadow_padding",
    "draw_drop_shadow",
    "rotate_with_pad",
]

"""A Glimmer-effektek (#381) `FilterOp` → egzakt csővezeték adapterei.

A `chain.py` `_HANDLERS`-be kötött függvényei: a `filters=` lánc pozíció
szerinti paramétereit (a `filterdesc-registry.md` 4.1 ini-sorrend-szabálya
szerint: numerikusok max 3 → színek → maradék numerikus → jelölők) a
`glimmer_tone`/`glimmer_creative`/`glimmer_artistic`/`glimmer_frames`/
`glimmer_focal` egzakt csővezetékeinek kwarg-jaira fordítják.

A pozíciók minden effektnél a `docs/specs/filterdesc-registry.md` 4.1–4.2
fejezete alapján SZÁMOLTAK (nem találgatottak) — ahol van valós ini-minta
(`filters-decoded.md` 5. kör), a levezetett sorrend egyezik vele.
"""

from __future__ import annotations

from picasapy.ini.filters import FilterOp
from picasapy.render import glimmer_artistic as artistic
from picasapy.render import glimmer_creative as creative
from picasapy.render import glimmer_focal as focal
from picasapy.render import glimmer_frames as frames
from picasapy.render import glimmer_tone as tone
from picasapy.render.tinting import parse_rgb_hex


def _float_at(op: FilterOp, index: int, default: float) -> float:
    """A flag utáni `index`-edik paraméter számként, hiányzónál `default`
    (a `chain._effect_float`-tal azonos, POZÍCIÓ szerinti olvasás — a
    szám/szín keveredés miatt a teljes lista konvertálása elszállna)."""
    absolute = index + 1
    if len(op.params) <= absolute:
        return default
    return float(op.params[absolute])


def _color_at(op: FilterOp, index: int, default: tuple[int, int, int]) -> tuple[int, int, int]:
    absolute = index + 1
    if len(op.params) <= absolute:
        return default
    return parse_rgb_hex(op.params[absolute])


def _bool_at(op: FilterOp, index: int, default: bool) -> bool:
    """A jelölőnégyzet-paraméterek egész számként (`0`/`1`) szerializálódnak."""
    absolute = index + 1
    if len(op.params) <= absolute:
        return default
    try:
        return float(op.params[absolute]) != 0.0
    except ValueError:
        return default


# --- Vignette / Matte / HDR / LocalContrast ---------------------------------


def apply_vignette_op(image, op: FilterOp):
    return tone.apply_vignette(
        image,
        blur=_float_at(op, 0, 35.0),
        strength=_float_at(op, 1, 1.4),
        fade=_float_at(op, 2, 0.0),
        color=_color_at(op, 3, (0, 0, 0)),
    )


def apply_matte_op(image, op: FilterOp):
    return tone.apply_matte(
        image,
        blur=_float_at(op, 0, 40.0),
        strength=_float_at(op, 1, 1.2),
        fade=_float_at(op, 2, 0.0),
        color=_color_at(op, 3, (255, 255, 255)),
    )


def apply_hdr_op(image, op: FilterOp):
    return tone.apply_hdr(
        image,
        radius=max(1.3, _float_at(op, 0, 20.0)),
        strength=_float_at(op, 1, 3.0),
        fade=_float_at(op, 2, 0.0),
    )


def apply_local_contrast_op(image, op: FilterOp):
    return tone.apply_local_contrast(
        image, radius=max(1.3, _float_at(op, 0, 15.0)), strength=_float_at(op, 1, 1.5)
    )


def apply_crossprocess_op(image, op: FilterOp):
    return tone.apply_crossprocess(image, fade=_float_at(op, 0, 0.0))


def apply_sixties_op(image, op: FilterOp, seed: int | None = None):
    return tone.apply_sixties(
        image,
        fade=_float_at(op, 0, 20.0),
        color=_color_at(op, 1, (255, 255, 255)),
        rounded=_bool_at(op, 2, True),
        seed=seed,
    )


def apply_heatmap_op(image, op: FilterOp):
    return tone.apply_heatmap(image, hue=_float_at(op, 0, 0.0), fade=_float_at(op, 1, 0.0))


def apply_nightvision_op(image, op: FilterOp, seed: int | None = None):
    return tone.apply_nightvision(
        image,
        brightness=_float_at(op, 0, 0.0),
        contrast=_float_at(op, 1, 0.0),
        fade=_float_at(op, 2, 0.0),
        seed=seed,
    )


def apply_twotone_op(image, op: FilterOp):
    return tone.apply_twotone(
        image,
        brightness=_float_at(op, 0, 0.0),
        contrast=_float_at(op, 1, 20.0),
        fade=_float_at(op, 2, 0.0),
        black_color=_color_at(op, 3, (0x00, 0x44, 0x88)),
        white_color=_color_at(op, 4, (0xFF, 0xFF, 0x00)),
    )


def apply_quantizepalette_op(image, op: FilterOp):
    return tone.apply_quantizepalette(
        image, steps=_float_at(op, 0, 8.0), smoothing=_float_at(op, 1, 80.0), fade=_float_at(op, 2, 0.0)
    )


# --- Creative ---------------------------------------------------------------


def apply_cinemascope_op(image, op: FilterOp, seed: int | None = None):
    # A jelölő polaritása NYITOTT (docs/specs/filters-decoded.md, „Nyitva"):
    # a filterdesc alapértéke „true", a mért minta mégis Cinemascope=1,0 —
    # itt az ini-értéket egyenes leképezéssel vesszük át (0=ki, 1=be).
    return creative.apply_cinemascope(image, letterbox=_bool_at(op, 0, True), seed=seed)


def apply_orton_op(image, op: FilterOp):
    return creative.apply_orton(
        image, bloom=_float_at(op, 0, 25.0), brightness=_float_at(op, 1, 50.0), fade=_float_at(op, 2, 0.0)
    )


def apply_pencil_sketch_op(image, op: FilterOp):
    return creative.apply_pencil_sketch(
        image,
        radius=max(1.3, _float_at(op, 0, 2.0)),
        contrast=_float_at(op, 1, 100.0),
        fade=_float_at(op, 2, 0.0),
    )


def apply_holga_op(image, op: FilterOp, seed: int | None = None):
    return creative.apply_holga(
        image,
        blur=_float_at(op, 0, 70.0),
        grain=_float_at(op, 1, 30.0),
        fade=_float_at(op, 2, 0.0),
        seed=seed,
    )


def apply_lomo_op(image, op: FilterOp):
    return creative.apply_lomo(image, blur=_float_at(op, 0, 50.0), fade=_float_at(op, 1, 0.0))


def apply_ir_op(image, op: FilterOp):
    return creative.apply_ir(image, fade=_float_at(op, 0, 0.0))


def apply_neon_op(image, op: FilterOp):
    return creative.apply_neon(image, fade=_float_at(op, 0, 0.0), color=_color_at(op, 1, (255, 0, 0)))


# --- Artistic ---------------------------------------------------------------


def apply_boost_op(image, op: FilterOp):
    return artistic.apply_boost(image, impact=_float_at(op, 0, 50.0))


def apply_soften_op(image, op: FilterOp):
    return artistic.apply_soften(image, impact=_float_at(op, 0, 50.0), fade=_float_at(op, 1, 50.0))


def apply_pixelate_op(image, op: FilterOp):
    return artistic.apply_pixelate(image, impact=max(2.0, _float_at(op, 0, 20.0)), fade=_float_at(op, 2, 0.0))


def apply_picnik_grain_op(image, op: FilterOp, seed: int | None = None):
    return artistic.apply_picnik_grain(
        image, grain=_float_at(op, 0, 10.0), lighten=_bool_at(op, 1, False), seed=seed
    )


# --- Frames (MÉRETNÖVELŐ) ----------------------------------------------------


def apply_border_op(image, op: FilterOp):
    return frames.apply_border(
        image,
        outer_thickness=_float_at(op, 0, 20.0),
        inner_thickness=_float_at(op, 1, 5.0),
        corner_radius=_float_at(op, 2, 0.0),
        outer_color=_color_at(op, 3, (0, 0, 0)),
        inner_color=_color_at(op, 4, (255, 255, 255)),
        caption_height=_float_at(op, 5, 0.0),
    )


def apply_rounded_edges_op(image, op: FilterOp):
    height, width = image.shape[:2]
    return frames.apply_rounded_edges(
        image,
        corner_radius=_float_at(op, 0, min(height, width) / 10.0),
        outer_color=_color_at(op, 1, (255, 255, 255)),
    )


def apply_drop_shadow_op(image, op: FilterOp):
    return frames.apply_drop_shadow(
        image,
        distance=_float_at(op, 0, 4.0),
        angle=_float_at(op, 1, 90.0),
        blur=_float_at(op, 2, 10.0),
        shadow_color=_color_at(op, 3, (0, 0, 0)),
        background_color=_color_at(op, 4, (255, 255, 255)),
        fade=_float_at(op, 5, 30.0),
    )


def apply_museum_matte_op(image, op: FilterOp):
    return frames.apply_museum_matte(
        image,
        outer_thickness=_float_at(op, 0, 25.0),
        inner_thickness=_float_at(op, 1, 40.0),
        outer_color=_color_at(op, 2, (0x1A, 0x0E, 0x03)),
        inner_color=_color_at(op, 3, (0xF0, 0xEA, 0xE4)),
    )


def apply_polaroid_op(image, op: FilterOp):
    return frames.apply_polaroid(
        image, rotate=_float_at(op, 0, 5.0), color=_color_at(op, 1, (0xE2, 0xE2, 0xE2))
    )


# --- Festhető maszkos effektek (#381, #688) --------------------------------


def apply_picnik_tint_op(image, op: FilterOp):
    return focal.apply_picnik_tint(image, fade=_float_at(op, 0, 0.0), color=_color_at(op, 1, (0x80, 0xCF, 0xFF)))


def apply_reanimated_eye_color_op(image, op: FilterOp):
    # #688: maszk nélkül AZONOSSÁG — a lánc nem tud ecset-maszkot adni, és
    # az eredeti Picasa is érintetlenül hagyja a be nem festett képet.
    return focal.apply_reanimated_eye_color(image, blur=_float_at(op, 0, 6.0), fade=_float_at(op, 1, 20.0))


#: Festhető (ecset-)maszkos effektek — a `chain.py` `apply_filters`-e
#: ezekhez külön magyar figyelmeztetést fűz.
PAINTABLE_MASK_OPS = frozenset({"picniktint", "reanimatedeyecolor"})

#: #688: azok a festhető-maszkos effektek, amelyek ÜRES maszkkal indulnak —
#: befestés nélkül az eredeti Picasa sem változtat a képen. A #685
#: mérőszettjének exportja szerint a `ReanimatedEyeColor` ilyen (Picasa
#: ΔE 0,18 = JPEG-zaj), a `PicnikTint` (ΔE 36,9) és a `Soften` (ΔE 5,5)
#: viszont NEM: azok befestés nélkül is a teljes képre futnak.
EMPTY_MASK_DEFAULT_OPS = frozenset({"reanimatedeyecolor"})

PAINTABLE_MASK_WARNING_TEMPLATE = (
    "{name}: a Picasa ecsettel kijelölt területre hatna, a PicasaPy-nak "
    "még nincs ecset-eszköze — a hatás egyelőre a TELJES KÉPRE fut (#381)."
)

EMPTY_MASK_WARNING_TEMPLATE = (
    "{name}: a Picasa csak az ecsettel BEFESTETT területre viszi fel, és "
    "befestés nélkül semmit nem változtat — a PicasaPy-nak még nincs "
    "ecset-eszköze, ezért a kép változatlan marad (#688)."
)


def paintable_mask_warning(name: str) -> str:
    """A festhető-maszkos effekt figyelmeztetése — attól függ, hogy az
    effekt ÜRES vagy teljes maszkkal indul-e (#688)."""
    template = (
        EMPTY_MASK_WARNING_TEMPLATE
        if name.casefold() in EMPTY_MASK_DEFAULT_OPS
        else PAINTABLE_MASK_WARNING_TEMPLATE
    )
    return template.format(name=name)


__all__ = [
    "apply_vignette_op",
    "apply_matte_op",
    "apply_hdr_op",
    "apply_local_contrast_op",
    "apply_crossprocess_op",
    "apply_sixties_op",
    "apply_heatmap_op",
    "apply_nightvision_op",
    "apply_twotone_op",
    "apply_quantizepalette_op",
    "apply_cinemascope_op",
    "apply_orton_op",
    "apply_pencil_sketch_op",
    "apply_holga_op",
    "apply_lomo_op",
    "apply_ir_op",
    "apply_neon_op",
    "apply_boost_op",
    "apply_soften_op",
    "apply_pixelate_op",
    "apply_picnik_grain_op",
    "apply_border_op",
    "apply_rounded_edges_op",
    "apply_drop_shadow_op",
    "apply_museum_matte_op",
    "apply_polaroid_op",
    "apply_picnik_tint_op",
    "apply_reanimated_eye_color_op",
    "PAINTABLE_MASK_OPS",
    "PAINTABLE_MASK_WARNING_TEMPLATE",
    "EMPTY_MASK_DEFAULT_OPS",
    "EMPTY_MASK_WARNING_TEMPLATE",
    "paintable_mask_warning",
]

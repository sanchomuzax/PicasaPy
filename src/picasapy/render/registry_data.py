"""A `filterdesc.xml` (Picasa 3.9.141.259) 84 szűrőjének NYERS adattáblája.

**Igazságforrás:** `docs/specs/filterdesc-registry.md` 2. és 4.2 fejezete
(#382). A fájl a `research/` alatti gitignore-olt `filterdesc.xml`-ből lett
KÉZZEL kigyűjtve — futásidőben az eredeti XML nem érhető el, ezért ez a
modul a tényleges, kódba fagyasztott igazságforrás.

Ez a fájl csak ADATOT tartalmaz (a `registry.py` építi belőle a tipizált
`FilterSpec`/`SliderSpec` objektumokat) — szándékosan nem importál semmit
a `registry.py`-ból, hogy a két modul közötti függés egyirányú maradjon.

## Korlátok (őszintén)

- A csúszkák `default`-ja `None`, ahol a doksi táblázata nem közöl explicit
  `d=` értéket (a Picasa ilyenkor feltehetően 0-val indul, de ez nincs
  bizonyítva minden sorra — inkább `None`, mint kitalált szám).
- A Glimmer-effektek (`Boost`…`Vignette`, ld. a doksi 4.2 pontja) néhány
  csúszkájának felső határa a KÉPMÉRETTŐL függ (pl. `CornerRadius` ≤
  `min(W,H)/2`) — ezeket `math.inf` felső korláttal vesszük fel: a statikus
  regiszter nem ismerheti a képméretet, a tényleges korlátot a renderelő
  alkalmazza majd (ez az #382 hatókörén kívül eső, jövőbeli finomítás).
- A Glimmer-effektek SZÍN- és jelölőnégyzet-vezérlői (pl. `Border` két
  színe, `Sixties` „Rounded" jelölője) nincsenek `SliderSpec`-ként felvéve —
  a dataclass csak numerikus csúszkákat modellez (ld. `registry.py`
  `SliderSpec`); a színek/jelölők a `color_kind`/jövőbeli mezőkkel
  bővíthetők, ha a szerkesztő UI (5. pont) igényli.
- A `RoundedEdges` `resizes` jelzője a doksi 2. táblázatában „—", de a
  #382-es issue kifejezetten a méretváltó szűrők közé sorolja (az eredeti
  Picasa a lekerekítést a vágott képre "égeti be", ami issue-szinten
  méretváltásnak számít) — itt az issue-t követjük, nem a táblázat-sort.
"""

from __future__ import annotations

import math

#: Egy csúszka nyers leírása: (index, label, minimum, maximum, default, log_base, hidden)
SliderRaw = tuple[int, str, float, float, float | None, float | None, bool]

#: Egy szűrő nyers leírása:
#: (key, label, mode, full_res, slow, resizes, rotates, persists_region,
#:  sliders, color_kind, has_puck)
FilterRaw = tuple[
    str, str, str, bool, bool, bool, bool, bool,
    tuple[SliderRaw, ...], str, bool,
]

_INF = math.inf


def _s(
    index: int,
    label: str,
    minimum: float,
    maximum: float,
    default: float | None = None,
    log_base: float | None = None,
    hidden: bool = False,
) -> SliderRaw:
    return (index, label, minimum, maximum, default, log_base, hidden)


# --- 1. natív szűrők (a filterdesc.xml <filter> elemei, Glimmer nélkül) ----

RAW_FILTERS: tuple[FilterRaw, ...] = (
    ("save", "Save", "history", False, False, False, False, False, (), "none", False),
    ("crop64", "Crop", "history", False, False, False, False, False, (), "none", False),
    ("crop", "Crop", "history", False, False, False, False, False, (), "none", False),
    ("redeye", "Red Eye", "history", False, False, False, False, True, (), "none", False),
    ("retouch", "Retouches", "history", False, False, False, False, True, (), "none", False),
    ("picnik", "Creative Kit", "history", False, False, False, False, True, (), "none", False),
    ("rot", "Rotate", "history", False, False, False, False, False, (), "none", False),
    (
        "debug", "Debug", "effect", False, False, False, False, False,
        (_s(0, "Size", 0.0, 100.0),), "none", True,
    ),
    (
        "triple", "Lighting Fixes", "soft", False, False, False, False, False,
        (
            _s(0, "Brightness", -1.0, 1.0),
            _s(1, "Contrast", -0.5, 0.5),
            _s(2, "Fill Light", 0.0, 1.0),
        ),
        "none", False,
    ),
    (
        "triple2", "Lighting Fixes", "soft", False, False, False, False, False,
        (
            _s(0, "Fill Light", 0.0, 1.0),
            _s(1, "Black Point", 0.0, 1.0),
            _s(2, "White Point", 0.0, 1.0, default=1.0),
        ),
        "none", False,
    ),
    (
        "triple3", "Lighting Fixes", "soft", False, False, False, False, False,
        (
            _s(0, "Fill Light", 0.0, 1.0),
            _s(1, "Highlights", 0.0, 0.48),
            _s(2, "Shadows", 0.0, 0.48),
        ),
        "none", False,
    ),
    (
        "finetune", "Tuning", "soft", False, False, False, False, False,
        (
            _s(0, "Fill Light", 0.0, 1.0),
            _s(1, "Highlights", 0.0, 0.48),
            _s(2, "Shadows", 0.0, 0.48),
            _s(3, "Color Temperature", -0.5, 0.5),
        ),
        "circle", True,
    ),
    (
        "finetune2", "Tuning", "soft", False, False, False, False, False,
        (
            _s(0, "Fill Light", 0.0, 1.0),
            _s(1, "Highlights", 0.0, 0.48),
            _s(2, "Shadows", 0.0, 0.48),
            _s(3, "Color Temperature", -1.0, 1.0),
        ),
        "circle", True,
    ),
    (
        "colorfix", "Color Fixes", "soft", False, False, False, False, False,
        (
            _s(0, "Choose White Point", 0.0, 0.0, hidden=True),
            _s(1, "Color Temperature", -0.5, 0.5),
        ),
        "circle", True,
    ),
    ("autobacklight", "Fill Light", "oneclick", False, False, False, False, False, (), "none", False),
    ("autolight", "Auto Contrast", "oneclick", False, False, False, False, False, (), "none", False),
    ("autocolor", "Auto Color", "oneclick", False, False, False, False, False, (), "none", False),
    ("bw", "B&W", "oneclick", False, False, False, False, False, (), "none", False),
    ("enhance", "I'm Feeling Lucky", "oneclick", False, False, False, False, False, (), "none", False),
    ("warm", "Warmify", "oneclick", False, False, False, False, False, (), "none", False),
    ("grain", "Film Grain (Old)", "oneclick", False, False, False, False, False, (), "none", False),
    ("grain2", "Film Grain", "oneclick", True, True, False, False, False, (), "none", False),
    ("sepia", "Sepia", "oneclick", False, False, False, False, False, (), "none", False),
    (
        "unsharp", "Sharpen (Old)", "effect", False, False, False, False, False,
        (_s(0, "Amount", 0.0, 1.0, default=0.6),), "none", False,
    ),
    (
        "unsharp2", "Sharpen", "effect", True, True, False, False, False,
        (_s(0, "Amount", 0.0, 3.0, default=0.6),), "none", False,
    ),
    ("autocontrast", "Auto Contrast", "oneclick", False, False, False, False, False, (), "none", False),
    (
        "tilt", "Straighten", "tool", False, False, False, False, False,
        (
            _s(0, "Angle", -1.0, 1.0, default=0.0, hidden=True),
            _s(1, "Scale (v1-kompat)", 0.0, 0.0, hidden=True),
        ),
        "none", False,
    ),
    (
        "rainbow", "Rainbow", "tool", False, False, False, False, False,
        (_s(0, "Position", 0.0, 256.0, default=0.0),), "none", False,
    ),
    (
        "radblur", "Soft Focus", "effect", False, False, False, False, False,
        (_s(0, "Size", -1.0, 1.0), _s(1, "Amount", -1.0, 1.0)), "none", True,
    ),
    (
        "radsat", "Focal B&W", "effect", False, False, False, False, False,
        (_s(0, "Size", -1.0, 1.0), _s(1, "Sharpness", 0.0, 1.0)), "none", True,
    ),
    (
        "linblur", "Linear Blur", "effect", False, False, False, False, False,
        (_s(0, "Amount", 0.0, 10.0, default=2.0),), "none", True,
    ),
    ("ansel", "Filtered B&W", "effect", False, False, False, False, False, (), "wheel_v1", False),
    (
        "tint", "Tint (Old)", "effect", False, False, False, False, False,
        (_s(0, "Color Preservation", -1.0, 255.0),), "wheel_v0", False,
    ),
    (
        "dir_tint", "Graduated Tint", "effect", False, False, False, True, False,
        (
            _s(0, "Feather", 0.0, 1.0, default=0.25),
            _s(1, "Shade", 0.0, 1.0, default=0.25),
        ),
        "wheel_v0", True,
    ),
    (
        "radtint", "Radial Tint", "effect", False, False, False, False, False,
        (_s(0, "Feather", 0.0, 1.0, default=0.25),), "wheel_v0", True,
    ),
    (
        "glow", "Glow (Old)", "effect", False, False, False, False, False,
        (
            _s(0, "Intensity", 0.0, 1.0, default=0.65),
            _s(1, "Radius", 0.0, 1.0, default=3.0, log_base=250.0),
        ),
        "none", False,
    ),
    (
        "glow2", "Glow", "effect", True, True, False, False, False,
        (
            _s(0, "Intensity", 0.0, 1.0, default=0.65),
            _s(1, "Radius", 0.0, 1.0, default=3.0, log_base=250.0),
        ),
        "none", False,
    ),
    (
        "sat", "Saturation", "effect", False, False, False, False, False,
        (_s(0, "Amount", -1.0, 1.0, default=0.1618),), "none", False,
    ),
    (
        "colortemp", "Color Temperature", "effect", False, False, False, False, False,
        (
            _s(0, "Cool to Warm", -0.5, 0.5, default=0.125),
            _s(1, "White Shift", 0.0, 1.0),
        ),
        "none", False,
    ),
    (
        "shadow", "Shadow & Highlight", "effect", False, False, False, False, False,
        (
            _s(0, "Radius", 0.0, 1.0, log_base=250.0),
            _s(1, "Shadow %", 0.0, 1.0),
            _s(2, "Highlight %", 0.0, 1.0),
        ),
        "none", False,
    ),
    (
        "blur", "Blur", "effect", False, False, False, False, False,
        (_s(0, "Threshold", -0.5, 0.5, default=0.1),), "none", False,
    ),
    (
        "contrast", "Contrast", "effect", False, False, False, False, False,
        (_s(0, "Contrast", -0.5, 0.5, default=0.1),), "none", False,
    ),
    (
        "gamma", "Gamma Correct", "effect", False, False, False, False, False,
        (_s(0, "Level", -1.0, 1.0, default=0.1618),), "none", False,
    ),
    (
        "backlight", "Backlight Fix", "effect", False, False, False, False, False,
        (_s(0, "Amount", 0.0, 1.0, default=0.25),), "none", False,
    ),
    (
        "fill", "Fill Light", "soft", False, False, False, False, False,
        (_s(0, "Fill Light", 0.0, 1.0, default=0.0, hidden=True),), "none", False,
    ),
    (
        "whitept", "Whitepoint", "effect", False, False, False, False, False,
        (_s(0, "Choose Whitepoint Color", 0.0, 0.0, hidden=True),), "circle", True,
    ),
    (
        "dir_sat", "Directional Saturation", "effect", False, False, False, False, False,
        (
            _s(0, "Left to Right", -1.0, 1.0),
            _s(1, "Top to Bottom", -1.0, 1.0),
        ),
        "none", True,
    ),
    (
        "dir_brite", "Directional Brightness", "effect", False, False, False, False, False,
        (
            _s(0, "Left to Right", -1.0, 1.0),
            _s(1, "Top to Bottom", -1.0, 1.0),
        ),
        "none", True,
    ),
    (
        "dir_sharp", "Directional Sharpen", "effect", False, False, False, False, False,
        (
            _s(0, "Left to Right", -1.0, 1.0),
            _s(1, "Top to Bottom", -1.0, 1.0),
        ),
        "none", True,
    ),
    (
        "focalpixelate", "Focal Pixelate", "effect", False, False, False, False, False,
        (
            _s(0, "Pixel Size", 0.0, 100.0, default=15.0),
            _s(1, "Focal Size", 0.0, 2.0, default=1.0),
            _s(2, "Edge Hardness", 0.0, 0.95, default=0.25),
            _s(3, "Fade", 0.0, 1.0, default=0.0),
        ),
        "none", True,
    ),
    # --- 2. Glimmer (Picnik-örökös) effektek — a doksi 4.2 pontja ----------
    (
        "boost", "Boost", "effect", False, False, False, False, False,
        (_s(0, "Impact", 0.0, 100.0, default=50.0),), "none", False,
    ),
    (
        "border", "Border", "effect", False, False, True, False, False,
        (
            _s(0, "OuterThickness", 0.0, 100.0, default=20.0),
            _s(1, "InnerThickness", 0.0, 100.0, default=5.0),
            _s(2, "CornerRadius", 0.0, _INF, default=0.0),
            _s(3, "CaptionHeight", 0.0, _INF, default=0.0),
        ),
        "none", False,
    ),
    ("cinemascope", "Cinemascope", "effect", True, False, True, False, False, (), "none", False),
    (
        "comicize", "Comic Book", "effect", True, True, False, False, False,
        (
            _s(0, "BlurXY", 0.0, 100.0, default=20.0),
            _s(1, "DotContrast", 0.0, 100.0, default=50.0),
            _s(2, "DotFade", 0.0, 100.0, default=50.0),
        ),
        "none", False,
    ),
    (
        "crossprocess", "Cross Process", "effect", True, False, False, False, False,
        (_s(0, "Fade", 0.0, 100.0, default=0.0),), "none", False,
    ),
    (
        "dropshadow", "Drop Shadow", "effect", True, True, True, False, False,
        (
            _s(0, "Distance", 0.0, 30.0, default=4.0),
            _s(1, "Angle", 0.0, 360.0, default=90.0),
            _s(2, "Blur", 0.0, 100.0, default=10.0),
            _s(3, "Fade", 0.0, 100.0, default=30.0),
        ),
        "none", False,
    ),
    (
        "picnikfocalpixelate", "Focal Pixelate", "effect", True, False, False, False, False,
        (
            _s(0, "Impact", 2.0, 100.0, default=20.0),
            _s(1, "Radius", 10.0, _INF),
            _s(2, "Hardness", 0.0, 100.0, default=50.0),
            _s(3, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", True,
    ),
    (
        "focalzoom", "Focal Zoom", "effect", True, False, False, False, False,
        (
            _s(0, "Impact", 1.0, 100.0, default=50.0),
            _s(1, "Radius", 10.0, _INF),
            _s(2, "Hardness", 0.0, 100.0, default=50.0),
            _s(3, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", True,
    ),
    (
        "picnikgrain", "Film Grain", "effect", True, True, False, False, False,
        (_s(0, "Grain", 0.0, 50.0, default=10.0),), "none", False,
    ),
    (
        "hdr", "HDR-ish", "effect", True, True, False, False, False,
        (
            _s(0, "Radius", 1.3, 80.0, default=20.0),
            _s(1, "Contrast", 1.0, 7.0, default=3.0),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "heatmap", "Heat Map", "effect", True, False, False, False, False,
        (
            _s(0, "Hue", -180.0, 180.0, default=0.0),
            _s(1, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "holga", "Holga-ish", "effect", True, True, False, False, False,
        (
            _s(0, "Blur", 0.0, 100.0, default=70.0),
            _s(1, "Grain", 0.0, 100.0, default=30.0),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    ("invert", "Invert Colors", "effect", False, False, False, False, False, (), "none", False),
    (
        "ir", "Infrared Film", "effect", False, False, False, False, False,
        (_s(0, "Fade", 0.0, 100.0, default=0.0),), "none", False,
    ),
    (
        "localcontrast", "Local Contrast", "effect", False, False, False, False, False,
        (
            _s(0, "Radius", 1.3, 40.0, default=15.0),
            _s(1, "Contrast", 1.0, 3.0, default=1.5),
        ),
        "none", False,
    ),
    (
        "lomo", "Lomo-ish", "effect", True, True, False, False, False,
        (
            _s(0, "Blur", 0.0, 100.0, default=50.0),
            _s(1, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "matte", "Matte", "effect", False, False, False, False, False,
        (
            _s(0, "Blur", 0.0, 50.0, default=40.0),
            _s(1, "Strength", 1.0, 2.0, default=1.2),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "museummatte", "Museum Matte", "effect", False, False, True, False, False,
        (
            _s(0, "OuterThickness", 0.0, 100.0, default=25.0),
            _s(1, "InnerThickness", 0.0, 100.0, default=40.0),
        ),
        "none", False,
    ),
    (
        "neon", "Neon", "effect", True, True, False, False, False,
        (_s(0, "Fade", 0.0, 100.0, default=0.0),), "none", False,
    ),
    (
        "nightvision", "Night Vision", "effect", False, False, False, False, False,
        (
            _s(0, "Brightness", -50.0, 50.0, default=0.0),
            _s(1, "Contrast", -50.0, 50.0, default=0.0),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "orton", "Orton-ish", "effect", True, True, False, False, False,
        (
            _s(0, "Bloom", 0.0, 50.0, default=25.0),
            _s(1, "Brightness", 0.0, 100.0, default=50.0),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "pencilsketch", "Pencil Sketch", "effect", True, True, False, False, False,
        (
            _s(0, "Radius", 1.3, 5.0, default=2.0),
            _s(1, "Contrast", 0.0, 200.0, default=100.0),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "pixelate", "Pixelate", "effect", True, False, False, False, False,
        (
            _s(0, "Impact", 2.0, 150.0, default=20.0),
            _s(1, "BlendMode", 0.0, 9.0, default=9.0),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "polaroid", "Polaroid", "effect", False, False, True, False, False,
        (_s(0, "Rotate", -10.0, 10.0, default=5.0),), "none", False,
    ),
    (
        "quantizepalette", "Posterize", "effect", True, True, False, False, False,
        (
            _s(0, "Steps", 2.0, 30.0, default=8.0),
            _s(1, "Smoothing", 0.0, 100.0, default=80.0),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "reanimatedeyecolor", "Ghoul Eye", "effect", False, False, False, False, False,
        (
            _s(0, "Blur", 0.0, 30.0, default=6.0),
            _s(1, "Fade", 0.0, 100.0, default=20.0),
        ),
        "none", False,
    ),
    (
        "roundededges", "Rounded Edges", "effect", False, False, True, False, False,
        (_s(0, "CornerRadius", 0.0, _INF),), "none", False,
    ),
    (
        "sixties", "1960's", "effect", False, False, False, False, False,
        (_s(0, "Fade", 0.0, 100.0, default=20.0),), "none", False,
    ),
    (
        "soften", "Soften", "effect", False, False, False, False, False,
        (
            _s(0, "Impact", 0.0, 100.0, default=50.0),
            _s(1, "Fade", 0.0, 100.0, default=50.0),
        ),
        "none", False,
    ),
    (
        "picniktint", "Tint", "effect", False, False, False, False, False,
        (_s(0, "Fade", 0.0, 100.0, default=0.0),), "none", False,
    ),
    (
        "twotone", "Duo-Tone", "effect", False, False, False, False, False,
        (
            _s(0, "Brightness", -95.0, 95.0, default=0.0),
            _s(1, "Contrast", 0.0, 100.0, default=20.0),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    (
        "vignette", "Vignette", "effect", False, False, False, False, False,
        (
            _s(0, "Blur", 0.0, 50.0, default=35.0),
            _s(1, "Strength", 1.0, 2.0, default=1.4),
            _s(2, "Fade", 0.0, 100.0, default=0.0),
        ),
        "none", False,
    ),
    ("moviestart", "Start Point", "oneclick", False, False, False, False, False, (), "none", False),
    ("movieend", "End Point", "oneclick", False, False, False, False, False, (), "none", False),
)

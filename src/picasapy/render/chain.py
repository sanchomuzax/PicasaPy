"""A `filters=` lánc alkalmazása numpy képekre: `apply_filters` sorban futtatja
a támogatott műveleteket. Kihagyja mind az ISMERETLEN NEVŰ, mind az ismert
nevű, de HIBÁS PARAMÉTERŰ bejegyzéseket (részleges előnézet), és a kihagyott
nevek listáját is visszaadja — a lánc egyetlen hibás tagja sem dobja el a
teljes renderelést (#301).
"""

from __future__ import annotations

import logging
import math

import numpy as np

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64
from picasapy.ini.retouch import parse_retouch_regions
from picasapy.render.color import (
    apply_bw,
    apply_grain,
    apply_saturation,
    apply_sepia,
    apply_warm,
)
from picasapy.render.effects import (
    GLOW_V1_INTENSITY,
    GLOW_V1_RADIUS,
    apply_glow,
    apply_radblur,
    apply_radsat,
    apply_vignette,
)
from picasapy.render.effects_artistic import (
    apply_boost,
    apply_comicize,
    apply_focal_zoom,
    apply_neon,
    apply_pencil_sketch,
    apply_pixelate,
    apply_soften,
)
from picasapy.render.effects_creative import (
    apply_cinemascope,
    apply_holga,
    apply_ir,
    apply_lomo,
    apply_orton,
    apply_sixties,
)
from picasapy.render.effects_frames import (
    apply_border,
    apply_drop_shadow,
    apply_museum_matte,
    apply_polaroid,
)
from picasapy.render.effects_creative_tone import (
    apply_crossprocess,
    apply_hdr,
    apply_heatmap,
    apply_invert,
    apply_quantizepalette,
    apply_twotone,
)
from picasapy.render.ops import (
    apply_autocolor,
    apply_autolight,
    apply_crop,
    apply_enhance,
    apply_redeye,
    apply_tilt,
)
from picasapy.render.chain_report import ChainReport, validate_and_clamp_op
from picasapy.render.registry import FILTER_REGISTRY, chain_flags
from picasapy.render.retouch import apply_retouch
from picasapy.render.sharpen import UNSHARP_V1_STRENGTH, apply_unsharp
from picasapy.render.tinting import (
    apply_ansel,
    apply_dir_tint,
    apply_tint,
    parse_rgb_hex,
)
from picasapy.render.tone import apply_fill, apply_finetune2, parse_neutral_argb

_log = logging.getLogger(__name__)

# Megfejtve (golden 4. kör): a tilt szöge θ = p·0,2 radián (= p·11,459°).
_TILT_RADIANS_PER_UNIT = 0.2

#: Az exe-string-bányászat (`docs/specs/picasa-exe-strings.md`, #347) által
#: AZONOSÍTOTT, de golden-méréssel MÉG NEM KALIBRÁLT `filters=` nevek. A lánc
#: FELISMERI őket — parse/round-trip rendben megy, és az `apply_filters`
#: kihagyott-listájában (`skipped`) szerepelnek, tehát az összesített
#: "nem renderelhető" jelentésbe számítanak —, de VIZUÁLIS MODELLT nem
#: futtatunk rájuk: kitalált implementáció helyett a kalibráció a #347
#: utódjegyében (golden-kör) készül el. A `RECOGNIZED_BUT_UNRENDERED`
#: elnevezés szándékos: megkülönbözteti őket a TELJESEN ismeretlen
#: (soha nem dokumentált) nevektől, amik ugyanabba a `skipped` listába
#: kerülnek, de nincs mögöttük exe-forrás.
KNOWN_UNRENDERED_OPS = frozenset(
    {
        "grain",  # v1 — a grain2-nek van implementációja, a bare v1-nek nincs
        "radtint",  # feltehetően a dir_tint radiális testvére (rad- előtag)
        "roundededges",
        "matte",
        "nightvision",
        # --- a filterdesc-regiszter (#382) által azonosított 21 további,
        # eddig sehol nem dokumentált szűrőnév — a filterdesc.xml-ben
        # léteznek, tehát régi könyvtárak `filters=` láncában előfordulhatnak.
        # A regiszterben (`registry.py`) megvan a leírásuk, de vizuális
        # modellt (golden-mérés híján) még nem futtatunk rájuk.
        "triple",
        "triple2",
        "triple3",
        "colorfix",
        "autobacklight",
        "autocontrast",
        "rainbow",
        "linblur",
        "colortemp",
        "shadow",
        "blur",
        "contrast",
        "gamma",
        "backlight",
        "whitept",
        "dir_sat",
        "dir_brite",
        "dir_sharp",
        "focalpixelate",
        "debug",
    }
)

#: Boolean jelző-tokenek a láncban (`<név>=1;`, param nélkül), amik NEM
#: effektet írnak le, hanem egy másik bejegyzés melletti METAADATOT — mint a
#: már ismert `redeye=1;`/`retouch=1;`. A `picnik=1;` (exe-string-bányászat,
#: #347) feltehetően azt jelzi, hogy a lánc valamelyik tagja Creative
#: Kit ("Picnik") eredetű effekt volt. Ezeket a lánc ÉRVÉNYES no-op-ként
#: nyeli el: nem effekt, ezért nem is kerül a "nem renderelhető" kihagyott-
#: listába — az ini-round-trip a `picasapy.ini.filters` generikus
#: parse/serialize rétegén keresztül változatlanul megőrzi.
#: A #382-es filterdesc-regiszter öt `mode="history"`/mozi-jelölő szűrője:
#: nem képi művelet (csak szerkesztési előzmény vagy mozi-vágás-marker),
#: ezért ugyanúgy no-op-ként nyelendők el, mint a `picnik=1;`.
_NOOP_MARKERS = frozenset({"picnik", "save", "rot", "crop", "moviestart", "movieend"})


def tilt_cover_scale(width: int, height: int, angle: float) -> float:
    """A forgatás utáni levágás elkerüléséhez szükséges minimális skála.

    `angle` radiánban. Az elforgatott téglalapot úgy skálázzuk, hogy a
    forgatott kép mindenütt lefedje az eredeti (width, height) vásznat:
    `s = max(cos|a| + (w/h)*sin|a|, cos|a| + (h/w)*sin|a|)`.
    (Fekvő képen ez a mérten igazolt `cos θ + (W/H)·sin θ` képlet.)
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"A méretek pozitívak kell legyenek: {width}x{height}")
    cos_a = abs(math.cos(angle))
    sin_a = abs(math.sin(angle))
    width_ratio = width / height
    height_ratio = height / width
    return max(cos_a + width_ratio * sin_a, cos_a + height_ratio * sin_a)


def _apply_tilt_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    params = op.float_params()
    if not params:
        raise ValueError(f"A tilt szűrőnek legalább egy paramétere kell legyen: {op}")
    angle = params[0] * _TILT_RADIANS_PER_UNIT
    if len(params) >= 2 and params[1] > 0:
        scale = params[1]
    else:
        # A Picasa 3.x a skála-mezőbe jellemzően 0.000000-t ír (#73): a 0
        # vagy hiányzó érték jelentése „számold ki a kitöltő skálát".
        height, width = image.shape[:2]
        scale = tilt_cover_scale(width, height, angle)
    return apply_tilt(image, angle=angle, scale=scale)


def _apply_crop_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    if len(op.params) < 2:
        raise ValueError(f"A crop64 szűrőnek rect64 paraméter kell: {op}")
    rect = decode_rect64(op.params[1])
    return apply_crop(image, rect)


def _apply_fill_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    params = op.float_params()
    if not params:
        raise ValueError(f"A fill szűrőnek erősség-paraméter kell: {op}")
    return apply_fill(image, params[0])


def _apply_sat_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    params = op.float_params()
    if not params:
        raise ValueError(f"A sat szűrőnek erősség-paraméter kell: {op}")
    return apply_saturation(image, params[0])


def _apply_unsharp_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    params = op.float_params()
    strength = params[0] if params else UNSHARP_V1_STRENGTH
    return apply_unsharp(image, strength)


def _finetune_float(op: FilterOp, index: int) -> float:
    return float(op.params[index]) if len(op.params) > index else 0.0


def _apply_finetune_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """finetune/finetune2 — a hiányzó paraméterek semlegesek.

    (A v1 p1/fill-je mérten azonos a v2-ével; a v1 színhő-skálája eltér,
    ott a v2 modellje közelítésként fut.)
    """
    neutral = parse_neutral_argb(op.params[4]) if len(op.params) > 4 else None
    return apply_finetune2(
        image,
        fill=_finetune_float(op, 1),
        highlights=_finetune_float(op, 2),
        shadows=_finetune_float(op, 3),
        neutral=neutral,
        temperature=_finetune_float(op, 5),
    )


def _apply_grain_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # A grain2 sztochasztikus (véletlen mag); az élő előnézetben viszont
    # rögzített maggal futtatjuk (seed=0), hogy egy változatlan lánc újra-
    # renderelésekor a szemcse ne "villogjon" — a spec elfogadási teszthez
    # (statisztikai) ez nem szükséges, csak az UI-élmény miatt választott mag.
    return apply_grain(image, seed=0)


def _effect_float(op: FilterOp, index: int, default: float) -> float:
    """A flag utáni `index`-edik paraméter számként, hiányzónál `default`.

    POZÍCIÓ szerint konvertál, nem az egész listát (#332): az effekt-opok egy
    részében szám és `00RRGGBB` szín KEVEREDIK (`Polaroid=1,5.0,00e2e2e2`),
    és a teljes lista konvertálása egy betűt tartalmazó színen elszállt volna
    — magával rántva az egyébként hibátlan szám-paramétereket is.

    Ha az adott pozíción értelmezhetetlen érték áll, a kivétel FELSZÁLL: a
    hívó lánc ilyenkor kihagyja ezt az egy bejegyzést, a többi lefut (#301).
    """
    absolute = index + 1  # a 0. paraméter az engedélyező "1" flag
    if len(op.params) <= absolute:
        return default
    return float(op.params[absolute])


def _apply_vignette_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Vignette=1,belső%,erősség,?,szín — a 3-4. paraméter szerepe méretlen
    return apply_vignette(
        image,
        inner=_effect_float(op, 0, 35.0),
        strength=_effect_float(op, 1, 1.4),
    )


def _apply_glow_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # glow (v1) és glow2 azonos paraméter-alakkal: 1,intenzitás,sugár;
    # paraméter nélkül a v1 golden-kitben mért alapértékei futnak
    return apply_glow(
        image,
        intensity=_effect_float(op, 0, GLOW_V1_INTENSITY),
        radius=_effect_float(op, 1, GLOW_V1_RADIUS),
    )


#: A szín-paraméter nélküli tint/ansel/dir_tint alakok alapértéke (#357).
#: Éles `.picasa.ini`-kben (élő NAS-os állomány, 2026-08-05) a Picasa
#: ELHAGYJA a szín-paramétert, ha a felhasználó az alapértelmezett színnel
#: mentett — a színválasztó alapállapota a fehér, ezért hiányzó szín esetén
#: ezzel futunk. KÖZELÍTÉS: golden-méréssel még nem validált (az érintett
#: effektek amúgy is a MÉRT-DE-ELTÉR kategóriában vannak, ld.
#: `docs/specs/filters-decoded.md`).
_DEFAULT_TINT_COLOR = (255, 255, 255)


def _apply_tint_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Élő alak: `tint=1,preserve[,szín]` — a szín opcionális (#357).
    if len(op.params) < 2:
        raise ValueError(f"A tint szűrőnek preserve paraméter kell: {op}")
    color = parse_rgb_hex(op.params[2]) if len(op.params) > 2 else _DEFAULT_TINT_COLOR
    return apply_tint(image, preserve=float(op.params[1]), color=color)


def _apply_ansel_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Élő alak: `ansel=1[,szín]` — a szín opcionális (#357); nélküle tiszta B/W.
    color = parse_rgb_hex(op.params[1]) if len(op.params) > 1 else _DEFAULT_TINT_COLOR
    return apply_ansel(image, color=color)


def _apply_radblur_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    return apply_radblur(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        size=_effect_float(op, 2, 0.0),
        amount=_effect_float(op, 3, 0.0),
    )


def _apply_radsat_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    return apply_radsat(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        radius=_effect_float(op, 2, 0.5),
        sharpness=_effect_float(op, 3, 0.5),
    )


def _apply_dir_tint_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Élő alak: `dir_tint=1,x,y,gradiens,árnyalás[,szín]` — a szín
    # opcionális (#357), hiányában az alapértelmezett színnel futunk.
    if len(op.params) < 5:
        raise ValueError(f"A dir_tint szűrőnek x,y,gradiens,árnyalás kell: {op}")
    color = parse_rgb_hex(op.params[5]) if len(op.params) > 5 else _DEFAULT_TINT_COLOR
    return apply_dir_tint(
        image,
        x=float(op.params[1]),
        y=float(op.params[2]),
        gradient=float(op.params[3]),
        shade=float(op.params[4]),
        color=color,
    )


# --- az 5. fül effektjeinek paraméter-leképezése (#332) --------------------
# A pozíciók a `docs/specs/filters-decoded.md` 5. körében MÉRT ini-mintákból
# jönnek (a felhasználó valódi Picasa-exportjaiból), nem találgatásból: az
# implementált szignatúrák alapértékei rendre egybeesnek a mért mintákkal.
# A 4. fül effektjeinél ez az egyezés NINCS meg (a pontos PICASA-skála a
# #317-es golden-kör híján ismeretlen) — ott ezért a paramétereket a
# `_effect_ratio` biztonságos, 0..1-re vetített arányként veszi át (ld. a
# 4. fül handlerei fölötti megjegyzést), nem az (esetleg más skálájú) mért
# minta szerint — de legalább TÉNYLEG eljutnak a rendererhez, és
# paraméter nélkül a jól hangolt implementált alapértékkel futnak.
# A szín-paramétereket a projekt bevált `parse_rgb_hex`-e olvassa.


def _effect_color(op: FilterOp, index: int, default: tuple[int, int, int]):
    """A flag utáni `index`-edik paraméter színként, hiányzónál `default`."""
    absolute = index + 1
    if len(op.params) <= absolute:
        return default
    return parse_rgb_hex(op.params[absolute])


def _effect_ratio(op: FilterOp, index: int, default: float) -> float:
    """A flag utáni `index`-edik paraméter 0..1 arányként, hiányzónál `default`.

    A 4. fül effektjeinél (#332) a paraméterek PONTOS skálája nem mért
    (#317 golden-kör még nyitva) — de a projekt többi mért csúszkája
    (Boost, Soften, Vignette belső sugara stb.) következetesen 0..100-as
    skálát használ. Ezt a konvenciót vetítjük 0..1 tartományba azoknál a
    kwarg-oknál, amik szigorúan [0,1]-re vannak korlátozva (pl. `strength`,
    `blend`, `softness`) — így egy valódi (akár a mértnél nagyobb) ini-érték
    sem tud kivételt dobni, csak a felső korláton szaturál."""
    absolute = index + 1
    if len(op.params) <= absolute:
        return default
    raw = float(op.params[absolute])
    return min(1.0, max(0.0, raw / 100.0))


def _apply_boost_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Boost=1,erősség
    return apply_boost(image, strength=_effect_float(op, 0, 50.0))


def _apply_soften_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Soften=1,mérték,sugár
    return apply_soften(
        image,
        amount=_effect_float(op, 0, 50.0),
        radius=_effect_float(op, 1, 50.0),
    )


def _apply_pixelate_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Pixelate=1,blokkméret,?,? — a 2-3. paraméter szerepe méretlen
    return apply_pixelate(image, block_size=_effect_float(op, 0, 20.0))


def _apply_focal_zoom_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # FocalZoom=1,x,y,sugár,erősség,?,?
    return apply_focal_zoom(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        radius=_effect_float(op, 2, 50.0),
        strength=_effect_float(op, 3, 50.0),
    )


def _apply_pencil_sketch_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # PencilSketch=1,elmosás,fényerő,szín-keverés
    return apply_pencil_sketch(
        image,
        blur_radius=_effect_float(op, 0, 2.0),
        brightness=_effect_float(op, 1, 100.0),
        color_mix=_effect_float(op, 2, 0.0),
    )


def _apply_neon_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Neon=1,intenzitás,#szín
    return apply_neon(
        image,
        intensity=_effect_float(op, 0, 50.0),
        color=_effect_color(op, 1, (0, 255, 170)),
    )


def _apply_comicize_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Comicize=1,élerősség,poszterizálás,simítás
    return apply_comicize(
        image,
        edge_strength=_effect_float(op, 0, 20.0),
        posterize=_effect_float(op, 1, 50.0),
        smoothness=_effect_float(op, 2, 50.0),
    )


def _apply_border_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Border=1,szélesség,?,?,#szín1,#keretszín,? — a keret színe az 5. (a mért
    # mintában 00ffffff = fehér, ami az implementált alapérték is)
    return apply_border(
        image,
        width=_effect_float(op, 0, 20.0),
        color=_effect_color(op, 4, (255, 255, 255)),
    )


def _apply_drop_shadow_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # DropShadow=1,keret,szög,elmosás,#árnyékszín,#keretszín,átlátszatlanság
    return apply_drop_shadow(
        image,
        border_width=_effect_float(op, 0, 4.0),
        angle=_effect_float(op, 1, 90.0),
        blur=_effect_float(op, 2, 10.0),
        shadow_color=_effect_color(op, 3, (0, 0, 0)),
        border_color=_effect_color(op, 4, (255, 255, 255)),
        opacity=_effect_float(op, 5, 30.0),
    )


def _apply_museum_matte_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # MuseumMatte=1,szélesség,vonalpozíció,#vonalszín,#paszpartuszín
    return apply_museum_matte(
        image,
        width=_effect_float(op, 0, 25.0),
        line_position=_effect_float(op, 1, 40.0),
        line_color=_effect_color(op, 2, (3, 14, 26)),
        mat_color=_effect_color(op, 3, (228, 234, 240)),
    )


def _apply_retouch_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`retouch=1[,rect64...];` — a régiók PicasaPy-saját kiterjesztéssel
    érkeznek (ld. `picasapy.ini.retouch` docsztring); régió nélkül no-op."""
    regions = parse_retouch_regions(op)
    return apply_retouch(image, regions)


def _apply_polaroid_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Polaroid=1,keretszélesség,#szín
    return apply_polaroid(
        image,
        border_width=_effect_float(op, 0, 5.0),
        color=_effect_color(op, 1, (226, 226, 226)),
    )


# --- a 4. fül kreatív effektjeinek paraméter-leképezése (#332) --------------
# A pozíciók a `docs/specs/filters-decoded.md` 5. körében mért ini-mintákból
# jönnek, de — szemben az 5. füllel — itt az implementált szignatúrák
# alapértékei NEM esnek egybe a mért mintákkal (pl. `IR=1,0.000000;` vs. az
# implementált `strength=1.0`): a golden-mérés (#317) még nyitva van, a
# pontos PICASA-skála ismeretlen. Amíg paraméter NINCS a láncban, a handler
# a jól hangolt implementált alapértékkel fut (nincs viselkedésváltozás a
# gombbal alkalmazott, paraméter nélküli esetben) — de ha VAN paraméter (pl.
# egy valódi Picasa-ból importált `.picasa.ini`-ben), azt tényleg felhasználja,
# a #301 hibatűrő mintája szerint (rossz paraméter → az az egy op kimarad).


def _apply_ir_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # IR=1,erősség
    return apply_ir(image, strength=_effect_float(op, 0, 1.0))


def _apply_lomo_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Lomo=1,telítettség,kontraszt,?
    return apply_lomo(
        image,
        saturation=_effect_float(op, 0, 1.6),
        contrast=_effect_float(op, 1, 1.3),
    )


def _apply_holga_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Holga=1,lágyítás,?,vignetta — a lágyítás [0,1]-re kötött, ezért arányos
    # (0..100→0..1) leképezéssel; a vignetta erőssége korlátlan, közvetlenül.
    return apply_holga(
        image,
        softness=_effect_ratio(op, 0, 0.4),
        vignette_strength=_effect_float(op, 2, 2.0),
    )


def _apply_hdr_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # HDR=1,clip,csempeméret,erősség — a clip/csempe legalább a minimumon
    # marad, ha az ini 0-t (vagy annál kisebbet) írna.
    return apply_hdr(
        image,
        clip_limit=max(0.1, _effect_float(op, 0, 2.0)),
        tile_grid_size=max(1, int(_effect_float(op, 1, 8))),
        strength=_effect_ratio(op, 2, 1.0),
    )


def _apply_cinemascope_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Cinemascope=1,árnyalás — a mért egyetlen paraméter (jellemzően 0) a
    # hűvös árnyalás erősségeként fut; a képarány az alapértéken marad.
    return apply_cinemascope(image, tint_strength=_effect_ratio(op, 0, 0.15))


def _apply_orton_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Orton=1,fényesítés,elmosás,keverés
    return apply_orton(
        image,
        brightness=max(0.01, _effect_float(op, 0, 1.4)),
        blur_sigma=max(0.01, _effect_float(op, 1, 8.0)),
        blend=_effect_ratio(op, 2, 0.5),
    )


def _apply_sixties_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Sixties=1,fakítás,#szín,? — a színparamétert a modell (fix meleg
    # csatornaeltolás) nem használja, csak a fakítást vesszük át.
    return apply_sixties(image, fade=_effect_ratio(op, 0, 0.35))


def _apply_heatmap_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # HeatMap=1,keverés,?
    return apply_heatmap(image, blend=_effect_ratio(op, 0, 1.0))


def _apply_crossprocess_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # CrossProcess=1,erősség
    return apply_crossprocess(image, strength=_effect_ratio(op, 0, 1.0))


def _apply_quantizepalette_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # QuantizePalette=1,szintszám,?,? — a szintszám egész, [2,256]-ra kötve
    levels = int(_effect_float(op, 0, 4.0))
    return apply_quantizepalette(image, levels=max(2, min(256, levels)))


def _apply_twotone_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # TwoTone=1,?,?,?,#árnyékszín,#fényszín — a két szín egyértelmű formátumú
    # (00RRGGBB), ezért ezeket a `parse_rgb_hex`-szel biztonsággal átvesszük.
    return apply_twotone(
        image,
        shadow_color=_effect_color(op, 3, (10, 10, 40)),
        highlight_color=_effect_color(op, 4, (255, 225, 140)),
    )


_HANDLERS = {
    "tilt": _apply_tilt_op,
    "redeye": lambda image, op: apply_redeye(image),
    "retouch": _apply_retouch_op,
    "enhance": lambda image, op: apply_enhance(image),
    "autolight": lambda image, op: apply_autolight(image),
    "autocolor": lambda image, op: apply_autocolor(image),
    "fill": _apply_fill_op,
    "finetune": _apply_finetune_op,
    "finetune2": _apply_finetune_op,
    "bw": lambda image, op: apply_bw(image),
    "sepia": lambda image, op: apply_sepia(image),
    "warm": lambda image, op: apply_warm(image),
    "sat": _apply_sat_op,
    "unsharp": _apply_unsharp_op,
    "unsharp2": _apply_unsharp_op,
    "grain2": _apply_grain_op,
    "vignette": _apply_vignette_op,  # az ini-ben nagybetűs: Vignette
    "glow": _apply_glow_op,
    "glow2": _apply_glow_op,
    "tint": _apply_tint_op,
    "ansel": _apply_ansel_op,
    "radblur": _apply_radblur_op,
    "radsat": _apply_radsat_op,
    "dir_tint": _apply_dir_tint_op,
    # --- a 4. fül kreatív effektjei (#329, paraméterekkel: #332) -----------
    # A Picasa PONTOS paraméterezése ezeknél nem mért (golden-mérés: #317),
    # a modellek közelítők — de a láncban ott álló paramétereket mostantól
    # tényleg felhasználjuk (ld. a handlerek fölötti megjegyzést), nem
    # dobjuk el csendben.
    "ir": _apply_ir_op,
    "lomo": _apply_lomo_op,
    "holga": _apply_holga_op,
    "hdr": _apply_hdr_op,
    "cinemascope": _apply_cinemascope_op,
    "orton": _apply_orton_op,
    "sixties": _apply_sixties_op,
    "invert": lambda image, op: apply_invert(image),
    "heatmap": _apply_heatmap_op,
    "crossprocess": _apply_crossprocess_op,
    "quantizepalette": _apply_quantizepalette_op,
    "twotone": _apply_twotone_op,
    # --- az 5. fül művészi effektjei (#330, paraméterekkel: #332) ----------
    "boost": _apply_boost_op,
    "soften": _apply_soften_op,
    "pixelate": _apply_pixelate_op,
    "focalzoom": _apply_focal_zoom_op,
    "pencilsketch": _apply_pencil_sketch_op,
    "neon": _apply_neon_op,
    "comicize": _apply_comicize_op,
    # keretes effektek — MEGNÖVELIK a képet, ezért a vágás UTÁN futnak
    # (ld. _FRAME_EFFECTS és az apply_filters sorrendje)
    "border": _apply_border_op,
    "dropshadow": _apply_drop_shadow_op,
    "museummatte": _apply_museum_matte_op,
    "polaroid": _apply_polaroid_op,
}

#: Keretet rajzoló, tehát MÉRETNÖVELŐ effektek (#330/#382). A vágás
#: koordinátái az EREDETI képre vonatkoznak, ezért ezeket a crop UTÁN kell
#: alkalmazni — különben a keret vastagságával csúszna el a kivágás. A
#: halmazt mostantól a filterdesc-regiszter `resizes` jelzője adja (a
#: korábbi kézzel karbantartott lista helyett, #382 3. pont): minden
#: `resizes=True` szűrő, aminek TÉNYLEG van bekötött handlere. A
#: `RoundedEdges` a regiszterben `resizes=True`, de nincs `_HANDLERS`
#: bejegyzése (`KNOWN_UNRENDERED_OPS` tagja) — ezért a metszetből
#: automatikusan kimarad, amíg implementálatlan.
_FRAME_EFFECTS = frozenset(
    key for key, spec in FILTER_REGISTRY.items() if spec.resizes
) & _HANDLERS.keys()

def apply_filters(
    image: np.ndarray, ops: tuple[FilterOp, ...]
) -> ChainReport:
    """Sorban alkalmazza a támogatott szűrőket (crop64, tilt, redeye, retouch,
    enhance, autolight, autocolor, fill, finetune/finetune2, bw, sepia, warm,
    sat, unsharp/unsharp2, grain2, Vignette, glow/glow2, tint, ansel, radblur,
    radsat, dir_tint).

    A `retouch` régió-adata PicasaPy-saját kiterjesztés (ld.
    `picasapy.ini.retouch` docsztring) — valódi Picasa-eredetű, régió nélküli
    `retouch=1;` bejegyzésnél no-op.

    A `grain2` rögzített maggal (seed=0) renderel (#20): a Picasa szemcséje
    véletlen magos, pixelhűen nem reprodukálható — a determinisztikus mag az
    előnézet-villogást kerüli el, statisztikailag a spec szerinti a kimenet.

    A nem támogatott (ismeretlen nevű) szűrőket szándékosan némán kihagyja
    (részleges előnézet). Ismert nevű, de hibás/hiányos paraméterű bejegyzés
    (pl. `tilt=1;` paraméter nélkül, `crop64=1,zzz;` érvénytelen hexszel)
    ESETÉN sem áll meg a teljes lánc — a hibás op kimarad, a kivétel a logba
    kerül, a lánc TÖBBI TAGJA lefut (#301). A kihagyott nevek sorrendhelyes
    listáját mindkét esetben visszaadja: `(kép, kihagyott_nevek)`. A
    `KNOWN_UNRENDERED_OPS` (#347) tagjai ugyanide, a kihagyott-listába
    kerülnek — FELISMERT, de kalibráció híján még vizuális modell nélküli
    nevek; a `_NOOP_MARKERS` (pl. `picnik=1;`) viszont NEM effekt, ezért
    nem is jelenik meg a kihagyott-listában, csendben elnyelődik.

    A `crop64` a láncban csak szerkesztési TÖRTÉNET — önmagában NEM vág
    (spec: `docs/specs/filters-decoded.md`). A tényleges vágást a képszekció
    külön `crop=` kulcsa adja, ami a lánc EFFEKTÍV (utolsó) crop64-ével egyezik.
    Ezt egyetlenegyszer, a teljes képre futó effektusok UTÁN alkalmazzuk, az
    EREDETI képméretre vonatkozó koordinátákkal (a tilt méret-tartó). Így a
    több crop64-et tartalmazó valódi Picasa-láncok sem kaszkádolnak (#130).

    **Tartomány-validáció (#382):** néhány ismert szűrőnél (`sat`, `tilt`,
    `finetune`/`finetune2`, `unsharp`/`unsharp2`) a paraméter a `registry`
    modul `[minimum, maximum]` tartományára VÁGVA fut le, ha az ini-beli
    érték kilóg belőle — a kivágott figyelmeztetést a visszaadott
    `ChainReport.range_warnings` hordozza. A `.picasa.ini` maga NEM
    módosul (a parszer szintjén nincs szigorítás, a round-trip elv szent).

    **Sáv-jelzők (#382):** a visszaadott `ChainReport.full_res`/`.slow`/
    `.resizes` jelzi, hogy a lánc tartalmaz-e olyan szűrőt, ami csak teljes
    felbontáson helyes, ami drága (aszinkron út kell), illetve ami
    megváltoztatja a kimeneti képméretet — a regiszterből számolva, a
    LÁNCBAN SZEREPLŐ (nemcsak a ténylegesen renderelt) nevek alapján.
    """
    result = image
    skipped: list[str] = []
    range_warnings: list[str] = []
    crop_op: FilterOp | None = None
    frame_ops: list[FilterOp] = []
    for op in ops:
        key = op.name.casefold()
        if key == "crop64":
            crop_op = op  # csak az effektív (utolsó) crop64 számít
            continue
        if key in _FRAME_EFFECTS:
            # a keret a vágás UTÁN kerül a képre (#330) — a lánc szerinti
            # sorrendjüket egymás közt megtartva
            frame_ops.append(op)
            continue
        if key in _NOOP_MARKERS:
            # boolean jelző-token (#347/#382), nem effekt — érvényes no-op,
            # nem kerül a kihagyott-listába
            continue
        handler = _HANDLERS.get(key)
        if handler is None:
            skipped.append(op.name)
            continue
        op, op_warnings = validate_and_clamp_op(op)
        range_warnings.extend(op_warnings)
        try:
            result = handler(result, op)
        except Exception:
            # Ismert nevű, de hibás paraméterű bejegyzés: a lánc többi tagja
            # ettől még lefusson (#301) — a hiba nem tűnik el nyomtalanul.
            _log.exception("Filter-bejegyzés kihagyva (hibás paraméter): %s", op)
            skipped.append(op.name)
    if crop_op is not None:
        try:
            result = _apply_crop_op(result, crop_op)
        except Exception:
            _log.exception(
                "Filter-bejegyzés kihagyva (hibás paraméter): %s", crop_op
            )
            skipped.append(crop_op.name)
    # keretek legvégül, a már kivágott képre (#330)
    for op in frame_ops:
        handler = _HANDLERS[op.name.casefold()]
        op, op_warnings = validate_and_clamp_op(op)
        range_warnings.extend(op_warnings)
        try:
            result = handler(result, op)
        except Exception:
            _log.exception("Filter-bejegyzés kihagyva (hibás paraméter): %s", op)
            skipped.append(op.name)
    all_keys = [op.name for op in ops]
    full_res, slow, resizes = chain_flags(all_keys)
    return ChainReport(
        result,
        tuple(skipped),
        full_res=full_res,
        slow=slow,
        resizes=resizes,
        range_warnings=tuple(range_warnings),
    )

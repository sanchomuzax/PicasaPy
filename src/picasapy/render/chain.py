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
from picasapy.ini.redeye import parse_redeye_regions
from picasapy.ini.retouch import parse_retouch_patches, parse_retouch_regions
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
)
from picasapy.render.effects_artistic import apply_comicize
from picasapy.render.focal import apply_focal_pixelate, apply_focal_zoom
from picasapy.render.effects_creative_tone import apply_invert
from picasapy.render import chain_glimmer_handlers as glimmer
from picasapy.render import chain_native_handlers as native
from picasapy.render.ops import (
    apply_autocolor,
    apply_autolight,
    apply_crop,
    apply_enhance,
    apply_redeye,
    apply_tilt,
)
from picasapy.render.chain_report import ChainReport, validate_and_clamp_op
from picasapy.render.directional import (
    apply_dir_brite,
    apply_dir_sat,
    apply_dir_sharp,
)
from picasapy.render.linear_blur import apply_linblur
from picasapy.render.registry import FILTER_REGISTRY, chain_flags
from picasapy.render.retouch import apply_retouch, apply_retouch_patches
from picasapy.render.sharpen import UNSHARP_V1_STRENGTH, apply_unsharp
from picasapy.render.tinting import (
    apply_ansel,
    apply_dir_tint,
    apply_radtint,
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
        # `grain` (v1) a #347 lezáró auditban (2026-08-06) KIKERÜLT innen:
        # a `filterdesc-registry.md` szerint a `grain2`-vel MEGEGYEZŐ,
        # paraméter nélküli "Film Grain" oneclick család régi tagja, ezért
        # a `grain2` golden-mért modelljét (`_apply_grain_op`) használja
        # (ld. lent a `_HANDLERS`-ben).
        # `radtint` a #565-ben KIKERÜLT innen: a natív regisztráció
        # (0x8f8730), a feldolgozó mag (0x90b370) és a maszk-LUT (0x90aeb0)
        # visszafejtésével az algoritmuscsalád és a pixelművelet (radiális
        # szorzó-tint, köbös smoothstep maszk) rögzített — egyedül a Feather
        # csúszka affin leképezése maradt feltételezés (ld. apply_radtint).
        # --- a filterdesc-regiszter (#382) által azonosított 21 további,
        # eddig sehol nem dokumentált szűrőnév — a filterdesc.xml-ben
        # léteznek, tehát régi könyvtárak `filters=` láncában előfordulhatnak.
        # A regiszterben (`registry.py`) megvan a leírásuk, de vizuális
        # modellt (golden-mérés híján) még nem futtatunk rájuk.
        # `triple`, `triple2`, `triple3`, `autocontrast`, `colortemp`,
        # `contrast`, `gamma`, `backlight`, `shadow` a #687-ben KIKERÜLT innen: a
        # dekompilált burkolóikból (`natív-szűrők.c`) a csúszka →
        # munkafüggvény-argumentum leképezés egyértelmű, a munkafüggvények
        # pedig már megvoltak. A #685 mérőszettje mindegyiket igazolta
        # (ld. a `chain_native_handlers` docstringjeit) — a `triple`
        # kivételével, aminek az egyetlen mérőesete paraméter nélküli
        # (tehát azonosság) volt.
        "colorfix",
        "rainbow",
        # `linblur` és `dir_sharp` a #623-ban KIKERÜLT innen: a natív magok
        # (`0x0090de10`, `0x0090d600`), a burkolóik és a közös elmosó
        # (`0x009dd0d0`) visszafejtésével a hatás jellege és a
        # pixel-matematika rögzített. A `linblur` sugár-leképezése és a
        # `dir_sharp` rámpa-horgonya KÖZELÍTÉS — ld. a két `apply_*`
        # docstringjét; a kalibráció a #317-ben fut.
        "blur",
        "whitept",
        "debug",
    }
)

#: #567 — HALOTT (legacy) szűrőnevek: a `filterdesc.xml`-ben még ott állnak,
#: de a 3.9.141.259 build natív regisztrációs táblájában NINCS hozzájuk sem
#: render-callback, sem névregisztráció. Ezek tehát nem „még nem
#: implementált" effektek: maga a Picasa sem futtatta már őket, konfigurációs
#: maradványok. A lánc kihagyja őket (a `skipped`-ben megjelennek), és a
#: `ChainReport.legacy_warnings` külön, egyértelműen kimondja, hogy halott
#: bejegyzésről van szó.
#:
#: A kisbetűs `focalpixelate` NEM azonos az élő `PicnikFocalPixelate`
#: Glimmer-effekttel: az utóbbi saját néven, saját callbackkel regisztrált,
#: és a saját handlerén fut. A kettőt szándékosan nem vezetjük egy kulcsra.
DEAD_LEGACY_OPS = frozenset({"focalpixelate"})

#: #687 — MÉRTEN TÉTLEN szűrőnevek: a #685 mérőszettjében (178 kép, egyetlen
#: valódi Picasa-export) maga a Picasa sem változtatott rajtuk (átlagos
#: ΔE ≤ 1,0, ami a JPEG-újratömörítés szintje), holott a lánc a
#: `filterdesc.xml` szerinti alap-, felső és alsó csúszkaállásokat is
#: tartalmazta.
#:
#: **Ez NEM azonos a `DEAD_LEGACY_OPS`-szal.** Ezeknek a natív regiszterben
#: VAN feldolgozójuk (a `blur` magja `0x0090cf60`, a `colorfix`/`whitept`
#: a `0x0090eda0` fehérpont-magot hívja) — csak a mérésben nem hatottak.
#: Két magyarázat áll nyitva, és a mérés egyik mellett sem dönt:
#: vagy tényleg tétlenek a 3.9.141.259-ben, vagy a mérőszett által
#: generált paraméter-alak nem az, amit a Picasa olvas (a `colorfix` és a
#: `whitept` PIPETTA-színt vár, amit a szett a lánc végére írt). Ezért a
#: bejegyzés célja pusztán annyi, hogy a következő mérés ne HIÁNYNAK
#: olvassa őket: a felhasználó a lánc kihagyásakor megkapja az okot is.
MEASURED_IDLE_OPS = frozenset({"blur", "colorfix", "whitept"})

#: A mérten tétlen bejegyzésre adott, felhasználónak szóló magyar üzenet.
MEASURED_IDLE_WARNING_TEMPLATE = (
    "{name}: a mérésben (#685) maga a Picasa sem változtatott vele a képen, "
    "ezért nem futtatunk rá modellt — a kép változatlan marad."
)

#: A halott bejegyzésre adott, felhasználónak szóló magyar üzenet (#567).
#: #567: az `autobacklight` fix derítőfény-erőssége a natív hívás
#: argumentumából (0,25) — nem csúszka, nem képfüggő.
_AUTOBACKLIGHT_FILL = 0.25

DEAD_LEGACY_WARNING_TEMPLATE = (
    "{name}: halott (legacy) szűrőnév — a Picasa 3.9 natív regiszterében "
    "sincs hozzá feldolgozó, ezért a kép változatlan marad."
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
    #
    # Ugyanez a handler szolgálja ki a `grain` (v1) bejegyzést is (#347
    # lezáró audit, 2026-08-06): a filterdesc-regiszter szerint a `grain`
    # ("Film Grain (Old)") és a `grain2` ("Film Grain") egyaránt paraméter
    # nélküli oneclick — nincs se csúszka, se szín, ami megkülönböztetné
    # őket, csak a `fullres+slow` sávjelző. A `grain` v1-re önmagára nincs
    # külön golden-mérés, ezért ez KÖZELÍTÉS (a már mért grain2-modell
    # újrahasznosítása) — ugyanaz a minta, mint a glow/glow2,
    # unsharp/unsharp2, finetune/finetune2 v1/v2 párosításoknál.
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


def _apply_autobacklight_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`autobacklight=1;` — FIX 25%-os derítőfény (#567).

    A natív regiszter szerint a render callback (`0x8f7cc0`) ugyanazt a
    feldolgozó magot (`0x90ac20`) hívja, mint a `backlight`/`fill`, fix
    `0.25` és `1.0` argumentumokkal. Vagyis ez NEM adaptív képelemzés — a
    kikommentezett UI-súgó is ezt mondja: „Increases ambient lighting by
    25%." Nincs benne hisztogram- vagy fényesség-vizsgálat, a paraméterei
    nem is olvasottak.
    """
    del op  # nincs szabad paramétere — a 25% fix
    return apply_fill(image, _AUTOBACKLIGHT_FILL)


def _apply_radtint_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Élő alak: `radtint=1,x,y,feather[,szín]` — a filterdesc szerint EGY
    # csúszkája van (Feather), mellette puck (fókuszpont) és színkerék; a
    # szín a #357 mintája szerint opcionális.
    color = parse_rgb_hex(op.params[4]) if len(op.params) > 4 else _DEFAULT_TINT_COLOR
    return apply_radtint(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        feather=_effect_float(op, 2, 0.25),
        color=color,
    )


def _apply_dir_sat_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Élő alak: `dir_sat=1,balról-jobbra,felülről-lefelé` — a natív burkoló
    # (`0x008f8fb0`) a két csúszkát KÖZVETLENÜL adja tovább, a korong
    # (`puck`) csak beállítja őket, külön paraméterként nem jelenik meg.
    return apply_dir_sat(
        image,
        horizontal=_effect_float(op, 0, 0.0),
        vertical=_effect_float(op, 1, 0.0),
    )


def _apply_dir_brite_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Ugyanaz a paraméter-alak, mint a `dir_sat`-nál (`0x008f9050`).
    return apply_dir_brite(
        image,
        horizontal=_effect_float(op, 0, 0.0),
        vertical=_effect_float(op, 1, 0.0),
    )


def _apply_dir_sharp_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Ugyanaz a paraméter-alak, mint a `dir_sat`-nál (`0x008f9090`).
    return apply_dir_sharp(
        image,
        horizontal=_effect_float(op, 0, 0.0),
        vertical=_effect_float(op, 1, 0.0),
    )


def _apply_linblur_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`linblur=1,x,y,Mennyiség` — a korong itt VALÓDI pozíció.

    A `dir_*` családdal ellentétben a `linblur` burkolója (`0x008f99c0`) a
    korong koordinátáját olvassa (a közös `0x008f9bf0` visszahíváson át),
    ezért a puck-os szűrők általános ini-sorrendje érvényes: `x, y` elöl,
    utána a csúszka (`docs/specs/filterdesc-registry.md` 3. pont). Az
    alapértékek a `filterdesc.xml`-ből: a korong a kép közepén, a
    „Mennyiség" 2,0 — a középre tett korong azonosság.
    """
    return apply_linblur(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        amount=_effect_float(op, 2, 2.0),
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


# --- a KÖZELÍTŐ maradt effektek (#381: FocalZoom, Comicize) --------------
# A Glimmer-effektek nagy része #381-ben átállt a `filterdesc.xml` egzakt
# csővezetékeire (`chain_glimmer_handlers.py`) — ez a két handler a régi,
# `_effect_float`-tal pozíció szerint olvasó KÖZELÍTŐ modellen maradt.


def _apply_focal_zoom_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`FocalZoom=1,x,y,Impact,Radius,Hardness,Fade` (#570).

    A paramétersorrendet a natív `glimmer::RadialBlurImageOperation`
    visszafejtése adta meg: a fókuszpont UTÁN az `Impact` jön — a korábbi
    kód a harmadik mezőt Radius-ként olvasta, ezért a két csúszka hatása
    fel volt cserélve.
    """
    return apply_focal_zoom(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        impact=_effect_float(op, 2, 50.0),
        radius=_effect_float(op, 3, 10.0),
        hardness=_effect_float(op, 4, 50.0),
        fade=_effect_float(op, 5, 0.0),
    )


def _apply_focal_pixelate_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`PicnikFocalPixelate=1,x,y,Impact,Radius,Hardness,Fade` (#570).

    Ugyanaz a paraméter-sorrend és ugyanaz a körmaszk, mint a
    `FocalZoom`-nál; a hatás lekicsinyítés + legközelebbi-szomszéd
    visszanagyítás (`smoothing = false`).
    """
    return apply_focal_pixelate(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        impact=_effect_float(op, 2, 20.0),
        radius=_effect_float(op, 3, 10.0),
        hardness=_effect_float(op, 4, 50.0),
        fade=_effect_float(op, 5, 0.0),
    )


def _apply_comicize_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # #569: `Comicize=1,BlurXY,DotContrast,DotFade` — a filterdesc szerinti
    # HÁROM csúszka (a korábbi „élerősség/poszterizálás/simítás" elnevezés a
    # Canny-közelítés maradványa volt, ld. apply_comicize docstringjét)
    return apply_comicize(
        image,
        blur_xy=_effect_float(op, 0, 20.0),
        dot_contrast=_effect_float(op, 1, 50.0),
        dot_fade=_effect_float(op, 2, 50.0),
    )


def _apply_retouch_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`retouch=1[,rect64...];` (v1) vagy `retouch=2[,patch...];` (v2, #445)
    — mindkét adat-alak PicasaPy-saját kiterjesztés (ld.
    `picasapy.ini.retouch` docsztring); adat nélkül no-op.

    A két alak kölcsönösen kizárja egymást a verzió-jelző (`params[0]`)
    alapján, ezért elég mindkét parsert megpróbálni és az eredményt
    összefésülni — pontosan az egyik ad nem-üres eredményt."""
    patches = parse_retouch_patches(op)
    if patches:
        return apply_retouch_patches(image, patches)
    regions = parse_retouch_regions(op)
    return apply_retouch(image, regions)


_HANDLERS = {
    "tilt": _apply_tilt_op,
    "redeye": lambda image, op: apply_redeye(image, parse_redeye_regions(op)),
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
    "grain": _apply_grain_op,  # v1 — közelítés, ld. _apply_grain_op docsztringje
    "grain2": _apply_grain_op,
    "glow": _apply_glow_op,
    "glow2": _apply_glow_op,
    "tint": _apply_tint_op,
    "ansel": _apply_ansel_op,
    "radblur": _apply_radblur_op,
    "radsat": _apply_radsat_op,
    "dir_tint": _apply_dir_tint_op,
    "dir_sat": _apply_dir_sat_op,
    "dir_brite": _apply_dir_brite_op,
    "dir_sharp": _apply_dir_sharp_op,
    "linblur": _apply_linblur_op,
    "radtint": _apply_radtint_op,
    "autobacklight": _apply_autobacklight_op,
    # --- a #687-ben bekötött natív szűrők (törzsük:
    # `chain_native_handlers.py`, a magok a `native_tone`/`native_colortemp`/
    # `ops` modulokban). A paraméter-leképezés a dekompilált burkolókból,
    # a hitelesítés a #685 mérőszettjéből.
    "contrast": native.apply_contrast_op,
    "gamma": native.apply_gamma_op,
    "colortemp": native.apply_colortemp_op,
    "backlight": native.apply_backlight_op,
    "shadow": native.apply_shadow_op,
    "autocontrast": native.apply_autocontrast_op,
    "triple": native.apply_triple_op,
    "triple2": native.apply_triple2_op,
    "triple3": native.apply_triple3_op,
    # --- Glimmer-effektek: EGZAKT csővezetékek a filterdesc.xml szerint
    # (#381, `chain_glimmer_handlers.py` + `glimmer_*` modulok). Az `IR`
    # kivétel: a `IRImageOperation` belső kernele a filterdesc.xml-ben sem
    # publikus, ott a modell dokumentáltan INTERPRETÁCIÓ (ld.
    # `glimmer_creative.apply_ir` docstringjét). `FocalZoom`/
    # A `Comicize` a #569-ben, a `FocalZoom`/`PicnikFocalPixelate` pedig a
    # #570-ben megkapta a natív visszafejtésből származó csővezetékét.
    "vignette": glimmer.apply_vignette_op,  # az ini-ben nagybetűs: Vignette
    "matte": glimmer.apply_matte_op,
    "hdr": glimmer.apply_hdr_op,
    "localcontrast": glimmer.apply_local_contrast_op,
    "ir": glimmer.apply_ir_op,
    "lomo": glimmer.apply_lomo_op,
    "holga": glimmer.apply_holga_op,
    "cinemascope": glimmer.apply_cinemascope_op,
    "orton": glimmer.apply_orton_op,
    "sixties": glimmer.apply_sixties_op,
    "invert": lambda image, op: apply_invert(image),
    "heatmap": glimmer.apply_heatmap_op,
    "nightvision": glimmer.apply_nightvision_op,
    "crossprocess": glimmer.apply_crossprocess_op,
    "quantizepalette": glimmer.apply_quantizepalette_op,
    "twotone": glimmer.apply_twotone_op,
    "boost": glimmer.apply_boost_op,
    "soften": glimmer.apply_soften_op,
    "pixelate": glimmer.apply_pixelate_op,
    "picnikgrain": glimmer.apply_picnik_grain_op,
    # #570: mindkét fókusz-effekt a natív paraméter-sorrendet és a közös
    # körmaszkot használja (render/focal.py)
    "focalzoom": _apply_focal_zoom_op,
    "picnikfocalpixelate": _apply_focal_pixelate_op,
    "pencilsketch": glimmer.apply_pencil_sketch_op,
    "neon": glimmer.apply_neon_op,
    "comicize": _apply_comicize_op,  # KÖZELÍTŐ maradt (ld. fent)
    "picniktint": glimmer.apply_picnik_tint_op,
    "reanimatedeyecolor": glimmer.apply_reanimated_eye_color_op,
    "roundededges": glimmer.apply_rounded_edges_op,
    # keretes effektek — MEGNÖVELIK a képet, ezért a vágás UTÁN futnak
    # (ld. _FRAME_EFFECTS és az apply_filters sorrendje)
    "border": glimmer.apply_border_op,
    "dropshadow": glimmer.apply_drop_shadow_op,
    "museummatte": glimmer.apply_museum_matte_op,
    "polaroid": glimmer.apply_polaroid_op,
}

#: Keretet rajzoló, tehát MÉRETNÖVELŐ effektek (#330/#382). A vágás
#: koordinátái az EREDETI képre vonatkoznak, ezért ezeket a crop UTÁN kell
#: alkalmazni — különben a keret vastagságával csúszna el a kivágás. A
#: halmazt mostantól a filterdesc-regiszter `resizes` jelzője adja (a
#: korábbi kézzel karbantartott lista helyett, #382 3. pont): minden
#: `resizes=True` szűrő, aminek TÉNYLEG van bekötött handlere. A
#: `RoundedEdges` a #381-ben MEGKAPTA a `_HANDLERS` bejegyzését
#: (`glimmer.apply_rounded_edges_op`) — a metszetben szerepel, nem marad ki
#: (a korábbi, "implementálatlan" állapotot leíró megjegyzés elavult volt).
_FRAME_EFFECTS = frozenset(
    key for key, spec in FILTER_REGISTRY.items() if spec.resizes
) & _HANDLERS.keys()

def can_render_filter(name: str) -> bool:
    """Van-e a `name` szűrőnévhez VALÓDI vizuális modellünk (#571)?

    Az igazságforrás maga a renderelő: a kereten (`_FRAME_EFFECTS`) és a
    vágáson kívül a `_HANDLERS` regiszter dönt. A no-op jelzők (`picnik`,
    `redeye`…) NEM effektek, ezért hamisat adnak — a felületen nincs is
    gombjuk.
    """
    key = name.casefold()
    return key in _HANDLERS or key in _FRAME_EFFECTS or key == "crop64"


def apply_filters(
    image: np.ndarray, ops: tuple[FilterOp, ...]
) -> ChainReport:
    """Sorban alkalmazza a támogatott szűrőket (crop64, tilt, redeye, retouch,
    enhance, autolight, autocolor, autocontrast, fill, backlight,
    finetune/finetune2, triple/triple2/triple3, contrast, gamma, colortemp,
    bw, sepia, warm, sat, unsharp/unsharp2, grain2, Vignette, glow/glow2,
    tint, ansel, radblur, radsat, dir_tint, radtint).

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
    nem is jelenik meg a kihagyott-listában, csendben elnyelődik. Ahol a
    kihagyás OKA ismert — halott legacy név (#567) vagy mérten tétlen
    bejegyzés (#687) —, ott a `ChainReport.legacy_warnings` ki is mondja.

    A `crop64` a láncban csak szerkesztési TÖRTÉNET — önmagában NEM vág
    (spec: `docs/specs/filters-decoded.md`). A tényleges vágást a képszekció
    külön `crop=` kulcsa adja, ami a lánc EFFEKTÍV (utolsó) crop64-ével egyezik.
    Ezt egyetlenegyszer, a teljes képre futó effektusok UTÁN alkalmazzuk, az
    EREDETI képméretre vonatkozó koordinátákkal (a tilt méret-tartó). Így a
    több crop64-et tartalmazó valódi Picasa-láncok sem kaszkádolnak (#130).

    **Tartomány-validáció (#382, #669):** néhány ismert szűrőnél (`sat`,
    `tilt`, `finetune`/`finetune2`, `unsharp`/`unsharp2`, az irányított
    család — `dir_sat`/`dir_brite`/`dir_sharp`/`dir_tint`, `linblur`,
    `radblur`, `radsat`, `radtint`, `glow`/`glow2`, `tint`, `fill`, valamint
    a #687-ben bekötött `contrast`/`gamma`/`colortemp`/`backlight`/
    `triple`/`triple2`/`triple3`) a
    paraméter a `registry` modul `[minimum, maximum]` tartományára VÁGVA
    fut le, ha az ini-beli érték kilóg belőle — a kivágott figyelmeztetést
    a visszaadott `ChainReport.range_warnings` hordozza. A `.picasa.ini`
    maga NEM módosul (a parszer szintjén nincs szigorítás, a round-trip
    elv szent). A teljes lista a `chain_report._RANGE_VALIDATED_PARAM_POSITIONS`
    táblában van.

    **Sáv-jelzők (#382):** a visszaadott `ChainReport.full_res`/`.slow`/
    `.resizes` jelzi, hogy a lánc tartalmaz-e olyan szűrőt, ami csak teljes
    felbontáson helyes, ami drága (aszinkron út kell), illetve ami
    megváltoztatja a kimeneti képméretet — a regiszterből számolva, a
    LÁNCBAN SZEREPLŐ (nemcsak a ténylegesen renderelt) nevek alapján.
    """
    result = image
    skipped: list[str] = []
    range_warnings: list[str] = []
    legacy_warnings: list[str] = []
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
            if key in DEAD_LEGACY_OPS:
                # #567: nem „még nincs modellünk", hanem a Picasa maga sem
                # futtatta már — ezt ki is mondjuk, nem csak kihagyjuk
                legacy_warnings.append(
                    DEAD_LEGACY_WARNING_TEMPLATE.format(name=op.name)
                )
            elif key in MEASURED_IDLE_OPS:
                # #687: van natív feldolgozója, de a mérésben nem hatott —
                # a két ok külön üzenetet kap (ld. MEASURED_IDLE_OPS)
                legacy_warnings.append(
                    MEASURED_IDLE_WARNING_TEMPLATE.format(name=op.name)
                )
            skipped.append(op.name)
            continue
        if key in glimmer.PAINTABLE_MASK_OPS:
            # #381: PicnikTint/ReanimatedEyeColor ecset-maszkja hiányzik —
            # a hatás a TELJES KÉPRE fut, ezt jelezni kell.
            range_warnings.append(glimmer.PAINTABLE_MASK_WARNING_TEMPLATE.format(name=op.name))
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
        legacy_warnings=tuple(legacy_warnings),
    )

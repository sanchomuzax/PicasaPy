"""A `filters=` renderlánc egyedi műveletkezelői."""

from __future__ import annotations

import numpy as np

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64
from picasapy.ini.redeye import (
    has_redeye_eye_circles,
    parse_redeye_eye_circles,
    parse_redeye_regions,
    redeye_uses_full_image_fallback,
)
from picasapy.ini.retouch import parse_retouch_patches, parse_retouch_regions
from picasapy.render.blur import apply_blur
from picasapy.render.chain_geometry import (
    Matrix,
)
from picasapy.render.chain_policy import _AUTOBACKLIGHT_FILL
from picasapy.render.color import apply_grain, apply_saturation
from picasapy.render.dir_tint import DIR_TINT_DEFAULT_ALPHA, apply_dir_tint
from picasapy.render.directional import apply_dir_brite, apply_dir_sat, apply_dir_sharp
from picasapy.render.effects import (
    GLOW_V1_INTENSITY,
    GLOW_V1_RADIUS,
    apply_glow,
    apply_radblur,
    apply_radsat,
)
from picasapy.render.effects_artistic import apply_comicize
from picasapy.render.linear_blur import apply_linblur
from picasapy.render.native_colortemp import apply_native_colortemp
from picasapy.render.native_grain import grain_seed
from picasapy.render.ops import apply_crop, apply_redeye
from picasapy.render.rainbow import apply_rainbow
from picasapy.render.sharpen import UNSHARP_V1_STRENGTH, apply_unsharp
from picasapy.render.tinting import apply_ansel, apply_radtint, apply_tint, parse_alpha_hex, parse_rgb_hex
from picasapy.render.tone import apply_fill, apply_finetune2, parse_neutral_argb
from picasapy.render.retouch import apply_retouch, apply_retouch_patches

def _apply_crop_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    if len(op.params) < 2:
        raise ValueError(f"A crop64 szűrőnek rect64 paraméter kell: {op}")
    rect = decode_rect64(op.params[1])
    return apply_crop(image, rect)


def _apply_crop_op_lekepezve(
    image: np.ndarray,
    op: FilterOp,
    eredeti_w: int,
    eredeti_h: int,
    matrix: "Matrix",
) -> np.ndarray:
    """A `crop64` a MÉRT sorrendben: a téglalap az EREDETI képre vonatkozik.

    A #330 mérése szerint a `crop64` koordinátái az eredeti (szerkesztés
    előtti) képre értendők. A mai, halasztott ág ezt úgy teljesíti, hogy a
    vágást a méret-tartó effektek UTÁN, de a keretek ELŐTT futtatja. A mért
    sorrendben viszont a vágás ott fut, ahol áll — tehát a téglalapot át kell
    számolni az addig felgyűlt leképezéssel (`matrix`: eredeti → jelenlegi).
    Pontosan ezt teszi az eredeti is: a `+0x84` rekesz a mátrixot ÉS az
    inverzét adja át minden opnak.
    """
    if len(op.params) < 2:
        raise ValueError(f"A crop64 szűrőnek rect64 paraméter kell: {op}")
    rect = decode_rect64(op.params[1])
    (a, b, c), (d, e, f) = matrix
    sarkok = [
        (
            a * (rect.left * eredeti_w) + b * (rect.top * eredeti_h) + c,
            d * (rect.left * eredeti_w) + e * (rect.top * eredeti_h) + f,
        ),
        (
            a * (rect.right * eredeti_w) + b * (rect.bottom * eredeti_h) + c,
            d * (rect.right * eredeti_w) + e * (rect.bottom * eredeti_h) + f,
        ),
    ]
    magassag, szelesseg = image.shape[:2]
    bal = max(0, min(round(min(x for x, _ in sarkok)), szelesseg))
    jobb = max(0, min(round(max(x for x, _ in sarkok)), szelesseg))
    fent = max(0, min(round(min(y for _, y in sarkok)), magassag))
    lent = max(0, min(round(max(y for _, y in sarkok)), magassag))
    if jobb <= bal or lent <= fent:
        raise ValueError(
            f"Üres kivágás a leképezés után: rect={rect} -> ({bal}, {fent}, {jobb}, {lent})"
        )
    return image[fent:lent, bal:jobb].copy()


def _apply_redeye_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """A render csak a tárolt régiókat használja; arcmodellt nem tölt.

    A csupasz, Picasából jövő `redeye=1` azonosság (#720). Az automatikus
    app-találatokat `eye64` körök kódolják; a modell nélküli régi teljes
    képes út kifejezett `autofull64()` jelölést kap.
    """
    regions = parse_redeye_regions(op)
    if redeye_uses_full_image_fallback(op):
        return apply_redeye(image)
    if has_redeye_eye_circles(op):
        height, width = image.shape[:2]
        return apply_redeye(
            image,
            regions,
            eye_circles=parse_redeye_eye_circles(op, width, height),
        )
    if regions:
        return apply_redeye(image, regions)
    return image.copy()


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

    A Derítőfény/Csúcsfények/Árnyékok ág a két változatban AZONOS (#879:
    mindkettő ugyanazt a `0x0090c1e0` szinthúzót hívja). A KÜLÖNBSÉG a
    színhőmérséklet: két külön natív függvény szolgálja ki.

    | | natív worker | gépezet |
    |---|---|---|
    | `finetune2` (v2) | `0x0090e9d0` | feketetest-tábla + 3×3-as mátrix (#956) |
    | `finetune` (v1) | **`0x0090ea10`** | középtónus-parabolás worker (ugyanaz, mint a `colortemp`-é) |

    ⛔ A „a v1 ugyanaz a görbe kétszeres skálán" hipotézis MEGDŐLT (#958,
    `filters-decoded.md`): a golden-eltérés 15,82 lett volna ~0 helyett, és
    az irány is ellentmondott — a v1 a saját maximumán 3–5-ször erősebben hat.

    ⭐ A v1 színága **KÉT KÜLÖN KÉPPONTMENET** (`0x008f7e4e`: `push esi;
    push esi` — ugyanaz a puffer forrás és cél): előbb a semlegesítő, aztán
    a hőmérséklet. A kettő között megmarad a 8 bites kvantálás, tehát nem
    vonhatók össze egyetlen lebegőpontos menetté. A worker fehérváltás-
    argumentuma mindkét ágon **0,0** (`fldz`, `0x008f7e3e`, `0x008f7e67`).
    """
    neutral = parse_neutral_argb(op.params[4]) if len(op.params) > 4 else None
    temperature = _finetune_float(op, 5)
    if op.name.casefold() != "finetune":
        return apply_finetune2(
            image,
            fill=_finetune_float(op, 1),
            highlights=_finetune_float(op, 2),
            shadows=_finetune_float(op, 3),
            neutral=neutral,
            temperature=temperature,
        )
    # v1: a közös ág hőmérséklet NÉLKÜL, majd a saját natív worker.
    kozbenso = apply_finetune2(
        image,
        fill=_finetune_float(op, 1),
        highlights=_finetune_float(op, 2),
        shadows=_finetune_float(op, 3),
        neutral=neutral,
        temperature=0.0,
    )
    if temperature == 0.0:
        return kozbenso
    return apply_native_colortemp(kozbenso, temperature, 0.0)


def _apply_grain_op(image: np.ndarray, op: FilterOp, ordinal: int) -> np.ndarray:
    # A Picasa CRT rand()-folyamából származó magot a renderlánc helyi
    # sorszáma adja. Nincs globális számláló: ugyanaz a lánc így ismételten
    # ugyanazt a determinisztikus képet adja.
    #
    # Ugyanez a handler szolgálja ki a `grain` (v1) bejegyzést is (#347
    # lezáró audit, 2026-08-06, megerősítve #3927-ben): a natív callback
    # (`0x008f88e0`) mindkét tokenre UGYANAZ — nincs se csúszka, se szín,
    # ami megkülönböztetné őket, csak a `fullres+slow` sávjelző. Ez tehát
    # NEM közelítés: a `grain` (v1) és a `grain2` egyaránt ugyanazt a
    # kiolvasott, nyolc lépéses natív algoritmust futtatja
    # (`native_grain.apply_native_grain`, #3928).
    return apply_grain(image, seed=grain_seed(ordinal))


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


def _apply_rainbow_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Élő alak: `rainbow=1,színmegőrzés`; a natív callback intre csonkol.
    preserve = int(float(op.params[1])) if len(op.params) > 1 else 0
    return apply_rainbow(image, preserve=preserve)


def _apply_ansel_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Élő alak: `ansel=1[,szín]` — a szín opcionális (#357); nélküle tiszta B/W.
    color = parse_rgb_hex(op.params[1]) if len(op.params) > 1 else _DEFAULT_TINT_COLOR
    return apply_ansel(image, color=color)


def _apply_desat_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`desat=<jelző>,r,g,b` — az `ansel` (Filtered B&W) örökölt ini-kulcsa
    (#711).

    A natív dekompiláció (konstruktor `0x0050bd70`, vtable-hívás
    `0x0050ce70`) szerint a `CDesaturateFilter` a `0x0090e680` munkafüggvényt
    hívja — UGYANAZT, amit az `ansel` callbackje (`0x008f8410`) is. A
    különbség kizárólag a szín útjában van: az `ansel` pakolt hexet bont
    `/255.0` osztással három floattá, a `desat` a három floatot KÖZVETLENÜL
    kapja (0..1 tartomány). Az átváltás egzakt (ld.
    `docs/specs/picasa-ini-format.md`, „A `desat`" szakasz):

        desat(r, g, b) == ansel( round(r*255)<<16 | round(g*255)<<8 | round(b*255) )

    Hiányzó paraméterre a natív konstruktor alapértéke fut (mindhárom
    csatorna `0,333` — semleges szürke).
    """
    channels = tuple(_effect_float(op, index, 1.0 / 3.0) for index in range(3))
    color = tuple(max(0, min(255, round(channel * 255.0))) for channel in channels)
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


def _apply_blur_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`blur=1[,Küszöbérték]` — élmegőrző, küszöbvezérelt simítás (#1142, #3493).

    Az egyetlen csúszka a KÜSZÖB, nem a sugár: azt dönti el, hol áll fal,
    azaz hol NEM simít a kiolvasott natív lánc (ld. `render/blur.py`).
    Az alapérték a `filterdesc.xml`-ből 0,1.

    ⚠️ A paraméter szándékosan NINCS a `chain_report` tartományvágó
    táblájában: a mérten futó `blur=1,2.000000;` alak kilóg a
    csúszkatartományból, a vágás tehát épp azt az esetet ölné meg, amit az
    eredeti lefuttat.
    """
    return apply_blur(image, threshold=_effect_float(op, 0, 0.1))


def _apply_dir_tint_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Élő alak: `dir_tint=1,x,y,gradiens,árnyalás[,szín]` — a szín
    # opcionális (#357), hiányában az alapértelmezett színnel futunk.
    if len(op.params) < 5:
        raise ValueError(f"A dir_tint szűrőnek x,y,gradiens,árnyalás kell: {op}")
    # A fehér-kihagyás a TELJES színdwordon múlik (#3902), ezért az alfa is
    # átmegy; szín nélkül a natív konstruktor `0xFFFFFFFF`-e fut.
    has_color = len(op.params) > 5
    color = parse_rgb_hex(op.params[5]) if has_color else _DEFAULT_TINT_COLOR
    alpha = parse_alpha_hex(op.params[5]) if has_color else DIR_TINT_DEFAULT_ALPHA
    return apply_dir_tint(
        image,
        x=float(op.params[1]),
        y=float(op.params[2]),
        gradient=float(op.params[3]),
        shade=float(op.params[4]),
        color=color,
        alpha=alpha,
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

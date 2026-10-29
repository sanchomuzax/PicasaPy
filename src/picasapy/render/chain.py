"""A `filters=` lánc alkalmazása numpy képekre: `apply_filters` sorban futtatja
a támogatott műveleteket. Kihagyja mind az ISMERETLEN NEVŰ, mind az ismert
nevű, de HIBÁS PARAMÉTERŰ bejegyzéseket (részleges előnézet), és a kihagyott
nevek listáját is visszaadja — a lánc egyetlen hibás tagja sem dobja el a
teljes renderelést (#301).
"""

from __future__ import annotations

import logging
import threading

import numpy as np

from picasapy.ini.filter_registry import (
    effective_param_count,
    is_exact_filter_name,
    max_param_count,
)
from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64
from picasapy.render import chain_glimmer_handlers as glimmer
from picasapy.render import chain_native_handlers as native
from picasapy.render.chain_geometry import (
    AZONOSSAG,
    Matrix,
    keret_geometria,
    tartalom_elhelyezes,
    _szorzat,
)
from picasapy.render.chain_ops import (
    _apply_ansel_op,
    _apply_autobacklight_op,
    _apply_blur_op,
    _apply_comicize_op,
    _apply_crop_op,
    _apply_crop_op_lekepezve,
    _apply_desat_op,
    _apply_dir_brite_op,
    _apply_dir_sat_op,
    _apply_dir_sharp_op,
    _apply_dir_tint_op,
    _apply_fill_op,
    _apply_finetune_op,
    _apply_glow_op,
    _apply_grain_op,
    _apply_linblur_op,
    _apply_radblur_op,
    _apply_radsat_op,
    _apply_radtint_op,
    _apply_rainbow_op,
    _apply_redeye_op,
    _apply_retouch_op,
    _apply_sat_op,
    _apply_tint_op,
    _apply_unsharp_op,
    _effect_float,
    _finetune_float as _finetune_float,
    _DEFAULT_TINT_COLOR as _DEFAULT_TINT_COLOR,
)
from picasapy.render.chain_policy import (
    DEAD_LEGACY_OPS,
    DEAD_LEGACY_WARNING_TEMPLATE,
    EXCESS_PARAM_WARNING_TEMPLATE,
    KNOWN_UNRENDERED_OPS as KNOWN_UNRENDERED_OPS,
    MEASURED_IDLE_OPS,
    MEASURED_IDLE_WARNING_TEMPLATE,
    MEASURED_NOT_RUNNING_OPS,
    MEASURED_NOT_RUNNING_WARNING_TEMPLATE,
    _AUTOBACKLIGHT_FILL as _AUTOBACKLIGHT_FILL,
    _NOOP_MARKERS,
)
from picasapy.render.chain_report import ChainReport, validate_and_clamp_op
from picasapy.render.dinamikus_csuszka import dinamikus_csuszka_ertek, fel_rovidebb_el
from picasapy.render.elonezeti_arany import (
    gyors_elonezet_aktiv,
    jelenlegi_arany,
)
from picasapy.render.effects_creative_tone import apply_invert
from picasapy.render.focal import apply_focal_pixelate, apply_focal_zoom
from picasapy.render.op_geometry import LancHelyzet, OpGeometria, op_geometria
from picasapy.render.ops import apply_autocolor, apply_autolight, apply_enhance, apply_tilt
from picasapy.render.registry import FILTER_REGISTRY, chain_flags
from picasapy.render.color import apply_bw, apply_sepia, apply_warm

_log = logging.getLogger(__name__)
_CROP_WARNING_LOCK = threading.Lock()
_CROP_WARNINGS: set[tuple[str, str]] = set()
_ALPHA_TRANSPARENT = 0

def normalize_crop_ops(
    ops: tuple[FilterOp, ...],
    crop: str | None,
    *,
    crop_ini_readable: bool = True,
    warning_key: str | None = None,
) -> tuple[FilterOp, ...]:
    """A képszekció `crop=` értékéhez igazítja a `crop64` előzményeket.

    A szabály a #4008 óta exportban használt viselkedés: olvasható ini és
    hiányzó `crop=` mellett minden láncbeli `crop64` kimarad; érvényes kulcs
    mellett az utolsó `crop64` a helyén a kulcs értékére áll. A lánc többi
    tagja és eredeti sorrendje változatlan. Hibás kulcs vagy olvashatatlan
    ini esetén a teljes lánc marad meg; az ini-olvasó naplóz, ha szükséges.
    Hibás crop= esetén képenként legfeljebb egyszer figyelmeztetünk.

    Ez csak a lánc előkészítése; a renderelés továbbra is az
    `apply_filters(..., mert_sorrend=True)` mért sorrendjében fut.
    """
    if not crop_ini_readable:
        return ops

    crop_indices = [index for index, op in enumerate(ops) if op.name == "crop64"]
    if crop is None:
        return tuple(op for op in ops if op.name != "crop64")

    try:
        current_rect = decode_rect64(crop)
    except ValueError:
        fallback = (
            "a lánc utolsó crop64 elemére esünk vissza"
            if crop_indices
            else "nem alkalmazunk kivágást"
        )
        warning = ("invalid-crop", warning_key or "<unknown>")
        with _CROP_WARNING_LOCK:
            first_warning = warning not in _CROP_WARNINGS
            _CROP_WARNINGS.add(warning)
        if first_warning:
            _log.warning("Érvénytelen crop= érték (%r); %s", crop, fallback)
        return ops

    if not crop_indices:
        return ops

    last_index = crop_indices[-1]
    last_crop = ops[last_index]
    try:
        last_rect = decode_rect64(last_crop.params[1])
    except (IndexError, ValueError):
        last_rect = None
    if last_rect == current_rect:
        return ops

    params = list(last_crop.params)
    if len(params) < 2:
        params = ["1", crop]
    else:
        params[1] = crop
    updated = list(ops)
    updated[last_index] = FilterOp(last_crop.name, tuple(params))
    return tuple(updated)

# Megfejtve (golden 4. kör): a tilt szöge θ = p·0,2 radián (= p·11,459°).
_TILT_RADIANS_PER_UNIT = 0.2

def _apply_tilt_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`tilt=1,p,<2. mező>` — a Kiegyenesítés.

    #3846: a natív visszahívás (`0x008f8810`) CSAK a szöget (`p`) adja
    tovább; a 2. mezőt (a Picasa 3.x jellemzően `0.000000`-t ír bele, #73)
    a natív út nem olvassa, ezért mi sem. A skálát az `apply_tilt` maga
    számolja (`ops.tilt_scale`). A csúszka húzása közben (`gyors_elonezet`
    blokk) a gyors mintavevővel fut, minden más esetben a natívval.
    """
    params = op.float_params()
    if not params:
        raise ValueError(f"A tilt szűrőnek legalább egy paramétere kell legyen: {op}")
    return apply_tilt(
        image, angle=params[0] * _TILT_RADIANS_PER_UNIT, gyors=gyors_elonezet_aktiv()
    )

# --- a KÖZELÍTŐ maradt effektek (#381: FocalZoom, Comicize) --------------
# A Glimmer-effektek nagy része #381-ben átállt a `filterdesc.xml` egzakt
# csővezetékeire (`chain_glimmer_handlers.py`) — ez a két handler a régi,
# `_effect_float`-tal pozíció szerint olvasó KÖZELÍTŐ modellen maradt.

#: #3596: a két fókuszos `Radius` tartományának alsó vége (képpont) és az
#: alapértéke — a leíró „a tartomány közepe", azaz 50 %.
_FOKUSZSUGAR_MIN = 10.0
_FOKUSZSUGAR_ALAP_SZAZALEK = 50.0

def _apply_focal_zoom_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`FocalZoom=1,x,y,Impact,Radius,Hardness,Fade` (#570).

    A paramétersorrendet a natív `glimmer::RadialBlurImageOperation`
    visszafejtése adta meg: a fókuszpont UTÁN az `Impact` jön — a korábbi
    kód a harmadik mezőt Radius-ként olvasta, ezért a két csúszka hatása
    fel volt cserélve.

    #3596: a `Radius` SZÁZALÉK (`DynamicRangeSlider`), a tartománya
    `10 … min(fullResImageWidth, fullResImageHeight)/2`. A teljes felbontás
    az előnézeti arányból jön vissza; a kész sugarat a maszk a natív
    `scale`-lel (`imageWidth / fullResImageWidth`) vetíti az előnézetre.

    #3884: a csúszka húzása közben (`gyors_elonezet` blokk) a zoom-kernel
    gyors OpenCV-úton fut, minden más esetben (mentés, export, bélyegkép,
    elengedés) a natívon.
    """
    arany = jelenlegi_arany()
    height, width = image.shape[:2]
    return apply_focal_zoom(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        impact=_effect_float(op, 2, 50.0),
        radius=dinamikus_csuszka_ertek(
            _effect_float(op, 3, _FOKUSZSUGAR_ALAP_SZAZALEK),
            _FOKUSZSUGAR_MIN,
            fel_rovidebb_el(height / arany, width / arany),
        ),
        hardness=_effect_float(op, 4, 50.0),
        fade=_effect_float(op, 5, 0.0),
        scale=arany,
        gyors=gyors_elonezet_aktiv(),
    )

def _apply_focal_pixelate_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """`PicnikFocalPixelate=1,x,y,Impact,Radius,Hardness,Fade,Reverse` (#3315).

    A mezősorrendet a natív lánc-ÍRÓ adja (`0x008fac40`): engedélyezés →
    puck x,y → az első három csúszka → (szín, ha volna) → a NEGYEDIK
    csúszka → a jelölőnégyzet `,%d`-ként. A leíró
    (`runtime/filterdesc.xml:859`) puckot, négy csúszkát (Impact, Radius,
    Hardness, Fade) és egy `_chkReverse` jelölőt ad.

    #3596: a `Radius` SZÁZALÉK, tartománya `10 … min(W, H)/2` (az
    `Impact` statikus csúszka, az nyers érték marad).
    """
    # #4941: a hiányos lánc (pl. `PicnikFocalPixelate=1,20.000000;`): a Picasa csendben kihagyja, nem alapértékkel fut.
    if len(op.params) < 8:
        return image
    height, width = image.shape[:2]
    return apply_focal_pixelate(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        impact=_effect_float(op, 2, 20.0),
        radius=dinamikus_csuszka_ertek(
            _effect_float(op, 3, _FOKUSZSUGAR_ALAP_SZAZALEK),
            _FOKUSZSUGAR_MIN,
            fel_rovidebb_el(height, width),
        ),
        hardness=_effect_float(op, 4, 50.0),
        fade=_effect_float(op, 5, 0.0),
        reverse=_effect_float(op, 6, 0.0) != 0.0,
    )

_HANDLERS = {
    "tilt": _apply_tilt_op,
    "redeye": _apply_redeye_op,
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
    "grain": _apply_grain_op,  # v1 — a grain2-vel EGYEZŐ, kiolvasott algoritmus, ld. _apply_grain_op docsztringje
    "grain2": _apply_grain_op,
    "glow": _apply_glow_op,
    "glow2": _apply_glow_op,
    "tint": _apply_tint_op,
    "ansel": _apply_ansel_op,
    "desat": _apply_desat_op,  # #711: az ansel örökölt ini-kulcsa
    "radblur": _apply_radblur_op,
    "radsat": _apply_radsat_op,
    "dir_tint": _apply_dir_tint_op,
    "dir_sat": _apply_dir_sat_op,
    "dir_brite": _apply_dir_brite_op,
    "dir_sharp": _apply_dir_sharp_op,
    "linblur": _apply_linblur_op,
    # #1142: a `blur` mérten LEFUT a csúszkatartomány fölött
    "blur": _apply_blur_op,
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
    "rainbow": _apply_rainbow_op,
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
    # #3315: visszakerült — a #1142 mérése rossz aritású sorra készült
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
_FRAME_EFFECTS = (
    frozenset(key for key, spec in FILTER_REGISTRY.items() if spec.resizes) & _HANDLERS.keys()
)

def can_render_filter(name: str) -> bool:
    """Van-e a `name` szűrőnévhez VALÓDI vizuális modellünk (#571)?

    Az igazságforrás maga a renderelő: a kereten (`_FRAME_EFFECTS`) és a
    vágáson kívül a `_HANDLERS` regiszter dönt. A no-op jelzők (`picnik`,
    `redeye`…) NEM effektek, ezért hamisat adnak — a felületen nincs is
    gombjuk.
    """
    # #1141: az ELFOGADÁS pontos (az eredeti kis-nagybetű-érzékeny), a
    # regiszter-keresés viszont a meglévő kisbetűs kulcsokon megy
    if not (is_exact_filter_name(name) or name == "crop64"):
        return False
    key = name.casefold()
    return key in _HANDLERS or key in _FRAME_EFFECTS or key == "crop64"

#: #1142 — VAN modellünk, de a felületen mégsem kínálunk hozzá vezérlőt.
#:
#: ⚠️ #3493: a korábbi indok („a csúszkatartományban tétlen") MEGDŐLT — a
#: kiolvasott natív lánc valódi, zajos tartalmon a csúszka tartományában
#: is simít; a mért tétlenség a kétszínű 762-es ábra sajátja volt. A
#: `blur`-nek viszont az eredetiben SINCS felületi belépési pontja (#3485):
#: a lánc idegen vagy régi `.picasa.ini`-ből kapja, ezért a LÁNC rendereli,
#: de gombot nem adunk rá — az eredeti sem ad.
UI_INERT_RANGE_OPS = frozenset({"blur"})

def can_offer_filter_control(name: str) -> bool:
    """Kínálhatjuk-e a szűrőt a felületen ÁLLÍTHATÓ vezérlőként (#1142)?

    Szigorúbb, mint a `can_render_filter`: azt is megköveteli, hogy a
    csúszkatartományon belül LEGYEN látható hatása (ld.
    `UI_INERT_RANGE_OPS`).
    """
    return can_render_filter(name) and name.casefold() not in UI_INERT_RANGE_OPS

def apply_filters(
    image: np.ndarray,
    ops: tuple[FilterOp, ...],
    *,
    paint_mask: np.ndarray | None = None,
    mert_sorrend: bool = True,
    bejovo: LancHelyzet | None = None,
    input_alpha: int = 255,
) -> ChainReport:
    """Sorban alkalmazza a támogatott szűrőket (crop64, tilt, redeye, retouch,
    enhance, autolight, autocolor, autocontrast, rainbow, fill, backlight,
    finetune/finetune2, triple/triple2/triple3, contrast, gamma, colortemp,
    bw, sepia, warm, sat, unsharp/unsharp2, grain2, Vignette, glow/glow2,
    tint, ansel, desat, radblur, radsat, dir_tint, radtint).

    A `retouch` régió-adata PicasaPy-saját kiterjesztés (ld.
    `picasapy.ini.retouch` docsztring) — valódi Picasa-eredetű, régió nélküli
    `retouch=1;` bejegyzésnél no-op.

    A `grain`/`grain2` a Picasa CRT `rand()`-folyamából kapja a magját,
    három értéket fogyasztva műveletenként. A sorszám renderenként nulláról
    indul, így a lánc determinisztikus, az ismételt előnézet nem villog.

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

    **`mert_sorrend` — MA EZ AZ ALAPÉRTELMEZÉS (#3229 3. lépés):** a lánc az
    ops EREDETI sorrendjében fut — nincs vágás- és keret-halasztás —, a
    `crop64` téglalapját pedig az addig felgyűlt leképezéssel számoljuk át (a
    #330 mérése így is teljesül: a koordináták az EREDETI képre vonatkoznak).
    Ez az, amit az eredeti tesz: a `CGenericFilter` `+0x84` rekesze minden
    opnak átadja a leképezést ÉS az inverzét (`docs/specs/filterdesc-registry.md`
    12., `render/op_geometry.py`).

    **Amit ez eldöntött (2026-09-19, a tulajdonos exportja).** A
    `3229-lanc-sorrend` készlet `01-keret-utan-szepia.jpg` képén az eredeti
    Picasa kimenetén a keret **barnás** (átlagos RGB 46, 37, 28), tehát a
    szépia a KERETRE is ráment; a kontroll-képen (`sepia;Border`) a keret
    fekete marad. A mi két águnk ugyanazon a képen: a halasztott 0, 0, 0
    (átlagos ΔE 4,481), a mért sorrend **46, 37, 29** (ΔE **2,278**). Ezért
    fordult meg az alapértelmezés. Őr:
    `tests/render/test_lanc_sorrend_elesben_3229.py`.

    `mert_sorrend=False` a RÉGI, halasztó ág — csak kontroll-mérésre való.

    **`bejovo` — a KETTÉVÁGOTT lánc folytatása (#3229).** Aki a láncot két
    hívásban futtatja (a szerkesztő lánc-prefix gyorsítótára), az első hívás
    `ChainReport.helyzet`-ét adja ide. Enélkül a második hívás a kapott képet
    hiszi az eredetinek, és a `crop64` koordinátái meg a `content_placement`
    elcsúsznak. `None` esetén a lánc a saját bemenetét tekinti eredetinek.

    **Sáv-jelzők (#382):** a visszaadott `ChainReport.full_res`/`.slow`/
    `.resizes` jelzi, hogy a lánc tartalmaz-e olyan szűrőt, ami csak teljes
    felbontáson helyes, ami drága (aszinkron út kell), illetve ami
    megváltoztatja a kimeneti képméretet — a regiszterből számolva, a
    LÁNCBAN SZEREPLŐ (nemcsak a ténylegesen renderelt) nevek alapján.
    """
    if input_alpha not in (0, 255):
        raise ValueError(f"A lánc alfaállapota csak 0 vagy 255 lehet: {input_alpha}")
    result = image
    grain_ordinal = 0
    alpha_state = input_alpha
    # #3229: a MÉRT sorrend ága követi, hova került a forrás — `hely_matrix` a
    # (vágás utáni) forrásból a jelenlegi képbe, `eredeti_*` pedig az eredeti
    # méret, amire a `crop64` koordinátái vonatkoznak (#330).
    if bejovo is not None:
        eredeti_w, eredeti_h = bejovo.eredeti_szelesseg, bejovo.eredeti_magassag
        ered_matrix: Matrix = bejovo.eredeti_matrix  # eredeti -> jelenlegi
        hely_matrix: Matrix = bejovo.hely_matrix  # a vágott forrás -> jelenlegi
        hely_w, hely_h = bejovo.hely_szelesseg, bejovo.hely_magassag
    else:
        eredeti_h, eredeti_w = image.shape[:2] if image is not None else (0, 0)
        ered_matrix = AZONOSSAG
        hely_matrix = AZONOSSAG
        hely_w, hely_h = eredeti_w, eredeti_h
    utolso_crop = None
    if mert_sorrend:
        for _op in ops:
            if _op.name == "crop64":
                utolso_crop = _op
    skipped: list[str] = []
    range_warnings: list[str] = []
    legacy_warnings: list[str] = []
    crop_op: FilterOp | None = None
    frame_ops: list[FilterOp] = []
    for op in ops:
        # #1141: a nem kanonikus írásmódú tag ISMERETLEN — a lánc
        # bejárója ilyenkor az eredetiben megáll (#1140), ezért itt is
        # kihagyjuk (a vágást a `parse_filters_prefix` végzi)
        if not (is_exact_filter_name(op.name) or op.name == "crop64"):
            skipped.append(op.name)
            continue
        # #910: fölös paraméterű tag — az eredeti lánc-bejárója elejti.
        # A korlát forrása ugyanaz a `MAX_PARAM_COUNTS`, amit az ÍRÁS
        # oldala már használ (`ini/filter_guard.py`); ISMERETLEN névre a
        # `max_param_count` None-t ad, tehát arra nem validálunk — a
        # round-trip elv nem sérül. A ZÁRÓ ÜRES mező (`grain=1,;`) mérten
        # tolerált, ezt az `effective_param_count` intézi.
        limit = max_param_count(op.name)
        if limit is not None:
            count = effective_param_count(op.params)
            if count > limit:
                legacy_warnings.append(
                    EXCESS_PARAM_WARNING_TEMPLATE.format(name=op.name, count=count, limit=limit)
                )
                skipped.append(op.name)
                continue
        key = op.name.casefold()
        if key == "crop64":
            crop_op = op  # csak az effektív (utolsó) crop64 számít
            if mert_sorrend and op is utolso_crop:
                # a MÉRT sorrendben a vágás OTT fut, ahol áll — a téglalapot
                # az addig felgyűlt leképezéssel számoljuk át
                try:
                    result = _apply_crop_op_lekepezve(result, op, eredeti_w, eredeti_h, ered_matrix)
                except Exception:
                    _log.exception("Filter-bejegyzés kihagyva (hibás paraméter): %s", op)
                    skipped.append(op.name)
                    # a záró ág se próbálja újra: akkor KÉTSZER kerülne a
                    # kihagyott-listára ugyanaz a bejegyzés (#301 őre)
                    crop_op = None
                else:
                    crop_op = None  # már alkalmazva, a záró ág ne fussa újra
                    # a placement innentől a VÁGOTT forrásból indul
                    hely_h, hely_w = result.shape[:2]
                    hely_matrix = AZONOSSAG
                    lepes = op_geometria(op, eredeti_w, eredeti_h)
                    ered_matrix = _szorzat(lepes.matrix, ered_matrix)
            continue
        if key in _FRAME_EFFECTS and not mert_sorrend:
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
                legacy_warnings.append(DEAD_LEGACY_WARNING_TEMPLATE.format(name=op.name))
            elif key in MEASURED_IDLE_OPS:
                # #687: van natív feldolgozója, de a mérésben nem hatott —
                # a két ok külön üzenetet kap (ld. MEASURED_IDLE_OPS)
                legacy_warnings.append(MEASURED_IDLE_WARNING_TEMPLATE.format(name=op.name))
            elif key in MEASURED_NOT_RUNNING_OPS:
                # #1142: a mérés szerint az eredeti nem futtatja — nálunk
                # volt rá renderer, ezért a mi kimenetünk tért el
                legacy_warnings.append(MEASURED_NOT_RUNNING_WARNING_TEMPLATE.format(name=op.name))
            skipped.append(op.name)
            continue
        if key in glimmer.PAINTABLE_MASK_OPS and paint_mask is not None:
            # #3541: a festhető effekt itt a Vámpírszem; a meglévő ecsetmaszk
            # közvetlenül az effektnek jut el.
            op, op_warnings = validate_and_clamp_op(op)
            range_warnings.extend(op_warnings)
            try:
                result = glimmer.alkalmazd_maszkkal(key, result, op, paint_mask)
            except Exception:
                _log.exception("Filter-bejegyzés kihagyva (hibás paraméter): %s", op)
                skipped.append(op.name)
            continue
        if key in glimmer.PAINTABLE_MASK_OPS:
            # #3541: a Vámpírszem ecsetmaszk nélkül változatlan marad; a másik
            # négy effekt a saját ágán, az egész képen fut.
            warning = glimmer.paintable_mask_warning(op.name)
            if warning:
                range_warnings.append(warning)
        op, op_warnings = validate_and_clamp_op(op)
        range_warnings.extend(op_warnings)
        elotte_h, elotte_w = result.shape[:2]
        try:
            if key in {"grain", "grain2"}:
                result = handler(result, op, grain_ordinal)
            elif key == "polaroid":
                result = handler(result, op, alpha=alpha_state)
            else:
                result = handler(result, op)
        except Exception:
            # Ismert nevű, de hibás paraméterű bejegyzés: a lánc többi tagja
            # ettől még lefusson (#301) — a hiba nem tűnik el nyomtalanul.
            _log.exception("Filter-bejegyzés kihagyva (hibás paraméter): %s", op)
            skipped.append(op.name)
        else:
            # #5299: a Picasa pixel-worker egyes kimeneteinek alfáját nem írja
            # át. Csak a kutatási specben megnevezett írókat követjük; a többi
            # effekt mai, háromcsatornás viselkedése változatlan.
            if key in {"dir_sat", "blur"}:
                alpha_state = _ALPHA_TRANSPARENT
            elif key == "colortemp" or key == "polaroid":
                alpha_state = 255
            if key in {"grain", "grain2"}:
                grain_ordinal += 1
            if mert_sorrend:
                # #3229: a TÉNYLEGESEN lefutott op leképezését fűzzük a
                # lánchoz — a hibára futott (kihagyott) op nem mozdít semmit
                lepes = op_geometria(op, elotte_w, elotte_h)
                ered_matrix = _szorzat(lepes.matrix, ered_matrix)
                hely_matrix = _szorzat(lepes.matrix, hely_matrix)
    if crop_op is not None:
        try:
            result = _apply_crop_op(result, crop_op)
        except Exception:
            _log.exception("Filter-bejegyzés kihagyva (hibás paraméter): %s", crop_op)
            skipped.append(crop_op.name)
    # keretek legvégül, a már kivágott képre (#330)
    #
    # #3166: itt még a VÁGOTT, keret nélküli méret áll — a szerkesztő átfedő
    # rétegei (vágás-téglalap, arckeretek) pontosan ehhez a téglalaphoz
    # tartoznak, a keretezett kimenetben viszont már nem ez a teljes kép.
    # Ezért a keret-ág ELŐTT jegyezzük meg a méretet, és a TÉNYLEGESEN
    # alkalmazott (csonkolt paraméterű, hibára nem futott) keret-opokból
    # számoljuk a helyet.
    elokeret_h, elokeret_w = result.shape[:2] if result is not None else (0, 0)
    alkalmazott_keretek: list[FilterOp] = []
    for op in frame_ops:
        handler = _HANDLERS[op.name.casefold()]
        op, op_warnings = validate_and_clamp_op(op)
        range_warnings.extend(op_warnings)
        try:
            if op.name.casefold() == "polaroid":
                result = handler(result, op, alpha=alpha_state)
            else:
                result = handler(result, op)
        except Exception:
            _log.exception("Filter-bejegyzés kihagyva (hibás paraméter): %s", op)
            skipped.append(op.name)
            continue
        if op.name.casefold() == "polaroid":
            alpha_state = 255
        alkalmazott_keretek.append(op)
    content_placement = None
    if mert_sorrend:
        # #3229: a mért sorrendben a keretek NEM a lánc végén futnak, tehát a
        # „keret-ág előtti méret" mint horgony nem létezik. A placement a
        # VÁGOTT forrásból a végső kimenetbe vezető leképezésből jön — ez az,
        # amit a szerkesztő átfedő rétegei (vágás-téglalap, arckeretek) kérnek.
        if hely_matrix != AZONOSSAG and hely_w and hely_h and result is not None:
            vegso_h, vegso_w = result.shape[:2]
            content_placement = tartalom_elhelyezes(
                OpGeometria(vegso_w, vegso_h, hely_matrix), hely_w, hely_h
            )
    elif alkalmazott_keretek and elokeret_w and elokeret_h:
        content_placement = tartalom_elhelyezes(
            keret_geometria(tuple(alkalmazott_keretek), elokeret_w, elokeret_h),
            elokeret_w,
            elokeret_h,
        )
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
        content_placement=content_placement,
        helyzet=LancHelyzet(eredeti_w, eredeti_h, ered_matrix, hely_matrix, hely_w, hely_h),
        alpha=alpha_state,
    )

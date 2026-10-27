# ruff: noqa: F401 -- a régi modul import-szimbólumait is megőrizzük.
"""Az EditController mixinjeinek közös állandói és segédei."""

from __future__ import annotations

from dataclasses import dataclass, replace
import itertools
import re

import logging
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError
from PySide6.QtCore import (
    Property,
    QCoreApplication,
    QEvent,
    QLocale,
    QObject,
    QSettings,
    Signal,
    Slot,
)
from PySide6.QtCore import Qt as QtNamespace
from PySide6.QtGui import QGuiApplication

from picasapy.app.effect_params import (
    format_param_values,
    has_params,
    resolve_effect_params,
)
from picasapy.edit.session import EditSession
from picasapy.fileops import is_folder_writable
from picasapy.ini import (
    FilterOp,
    FilterWriteError,
    IniConflictError,
    IniSaveError,
    PhotoCropReader,
    load_or_empty,
    parse_faces,
    update_document,
    with_backuphash,
)
from picasapy.ini.rect64 import Rect64, encode_rect64
from picasapy.ini.redeye import EyeCircle64
from picasapy.ini.retouch import RetouchPatch

from .paint_mask_controller import PaintMaskMixin
from picasapy.ini.text_overlay import (
    BETUMERETEK,
    meret_taroltbol,
    tarolt_meret,
    TextBlock,
    TextGeometry,
    TextOverlay,
    TextStyle,
    alignment_code,
    alignment_name,
    fill_mode_from,
    parse_text,
    parse_text_active,
    serialize_text,
    serialize_text_active,
)
from picasapy.metadata import read_exif_details
from picasapy.render.chain import (
    DEAD_LEGACY_OPS,
    can_offer_filter_control,
    normalize_crop_ops,
)
from picasapy.render.chain_geometry import AZONOSSAG, Matrix
from picasapy.render.op_geometry import invertal
from picasapy.render.legacy_effects import LEGACY_EFFECT_KEYS, LEGACY_EFFECTS
from picasapy.render.registry import chain_flags
from picasapy.render.registry import one_click_keys
from picasapy.render.elonezeti_arany import gyors_elonezet
from picasapy.render.crop_suggest import suggest_crops
from picasapy.render.gpu_point_pipeline import build_finetune2_lut
from picasapy.render.text_fonts import default_family, family_labels
from picasapy.render.tone import estimate_neutral_color, parse_neutral_argb
from picasapy.scanner import PICASA_INI_NAME

from . import formatting
from .edit_action_names import redo_label, undo_label
from .edit_preview import EditPreviewProvider, TextOverlaySpec
from .histogram_helper import EMPTY_HISTOGRAM
from .worker_thread import BackgroundWorkerMixin

#: #3819: a `?rev=` cache-buster FOLYAMATSZINTŰ számlálókból jön, nem
#: példányonként 0-ról. A Qt kép-gyorstára folyamatszintű, kulcsa az URL és a
#: kért méret; ha egy újabb vezérlő-példány ugyanarra a fotóra ugyanazt a
#: számot adná, a Qt a RÉGI képet adná vissza a szolgáltató megkérdezése
#: nélkül (mérve: a megjelenítési mód váltása így nem jutott a képernyőre).
_REVIZIO = itertools.count(1)
_GPU_REVIZIO = itertools.count(1)
# #4283: az eredeti `picker::mru_%d` tükrözése a saját QSettingsben.
_PICKER_MRU_SETTINGS_KEYS = tuple(f"picker/mru_{index}" for index in range(5))
_PICKER_COLOR_PATTERN = re.compile(r"#[0-9a-fA-F]{6}\Z")

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class _RedeyeBufferState:
    """A vörösszem-panel egy régiónként visszaállítható állapota."""

    regions: tuple[Rect64, ...]
    eye_circles: tuple[tuple[float, float, float], ...]
    eye_image_size: tuple[int, int] | None
    eye_overlay_size: tuple[int, int] | None
    eye_to_overlay: Matrix
    full_image_fallback: bool
    found: int
    can_reapply_auto: bool
    reset_message: bool

# #459: a csillag/album-írás mintája (photo_ops_controller.py) — a tartós
# ütközés/lemezhiba is kezelt hiba, nem néma adatvesztés/kivétel.
# #643: a round-trip őr visszautasítása is ide tartozik. A `_save()` KÜLÖN
# ágon kezeli (`editChainRejected`), mert az `editSaveFailed` párbeszéde a
# „lemezhiba, a lemez tele lehet" mondattal keretezi az üzenetet — ez itt
# félrevezető lenne. A tuple attól még tartalmazza, hogy az őr semelyik
# másik mentési útvonalon se szökhessen ki nyers kivételként.
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError, FilterWriteError)

# redeye: a réteg LEVÉTELE (#116) — a felvitel/kézi régiók a #445-ös
# Vörösszem eszközön át mennek (enterRedeyeTool/applyRedeye).
_TOGGLE_NAMES = ("redeye",)
# egygombos javítások: append-only rétegezés, levétel csak Visszavonással
_ONE_SHOT_NAMES = ("enhance", "autolight", "autocolor")
# Effektek (#20): append-only rétegek. A render-op nélküli effektek is a
# láncba kerülnek (round-trip), az előnézeten csak kimaradnak. A paramétert
# igénylők (pl. sat) dokumentált alapértékkel indulnak — a finomhangolt
# csúszkázás követő feladat.
_EFFECT_PARAMS: dict[str, tuple[str, ...]] = {
    "sat": ("1", "0.500000"),
    # --- „Régi effektek" fül (#571, #582) ---------------------------------
    # A `fill` renderelője KÖTELEZŐ erősség-paramétert vár (`chain.
    # _apply_fill_op`), paraméter nélkül kivételt dobna. Az alapérték a
    # natív `autobacklight` fix 25%-a (#567: a render callback ugyanazt a
    # magot hívja `0.25`-tel) — ez a Picasából származó szám, nem tipp.
    "fill": ("1", "0.250000"),
    # A `radtint` alakja `radtint=1,x,y,feather[,szín]` (#565): középre tett
    # fókuszpont + a filterdesc.xml Feather-alapértéke (0.25). A szín
    # elhagyható — a renderelő ilyenkor a dokumentált alapszínt használja.
    "radtint": ("1", "0.500000", "0.500000", "0.250000"),
}

#: A „Régi effektek" fül gombjai közül azok, amelyeket ALKALMAZNI is lehet
#: (#582). A fülön minden örökölt név látszik, de csak ezekhez van valódi
#: renderelőnk; a többi gombja letiltva jelenik meg, és ide sem juthat el.
#: Az igazságforrás itt is a renderelő (`can_offer_filter_control`), nem
#: kézzel karbantartott lista — így a fül soha nem kínálhat olyan effektet,
#: amelyik utána kivételbe futna, sem olyat, aminek a csúszkatartományán
#: belül mérten nincs hatása (#1142).
_LEGACY_EFFECT_NAMES = tuple(
    sorted(key for key in LEGACY_EFFECT_KEYS if can_offer_filter_control(key))
)
_EFFECT_NAMES = (
    # #2141: az 1. effekt-fül első hat csempéje az EREDETI elsődlegesét
    # hívja (a `0x00c7e5a0` csempe-tábla szerint). Az `unsharp`, `grain`
    # és `tint` a SHIFTes másodlagos — a #2141 idején nem volt felületi
    # belépési pontjuk, ezért kimaradtak innen.
    #
    # #2146: a Shift-ág MEGÉPÜLT, tehát a másodlagosok visszakerülnek —
    # enélkül a Shifttel megnyomott csempe `ValueError`-t adna (a
    # `test_effect_names.py` őre pontosan ezt fogta meg).
    #
    # #3315: a `picnikfocalpixelate` is bekerült — a kezelője megvan, és a
    # Shift-ág a `pixelate` csempén megépült (a kilencedik pár).
    "unsharp",
    "grain",
    "tint",
    "glow",
    "radtint",
    "unsharp2",
    "sepia",
    "bw",
    "warm",
    "picnikgrain",
    "picniktint",
    "sat",
    "radblur",
    "glow2",
    "ansel",
    "radsat",
    "dir_tint",
    "vignette",
    # 4. fül — kreatív effektek (#329)
    "ir",
    "lomo",
    "holga",
    "hdr",
    "cinemascope",
    "orton",
    "sixties",
    "invert",
    "heatmap",
    "crossprocess",
    "quantizepalette",
    "twotone",
    "matte",
    "nightvision",
    "localcontrast",
    # 5. fül — művészi effektek (#330)
    "boost",
    "soften",
    "pixelate",
    # #3315: a `pixelate` Shift-párja (a kilencedik)
    "picnikfocalpixelate",
    "focalzoom",
    "pencilsketch",
    "neon",
    "comicize",
    "border",
    "dropshadow",
    "museummatte",
    "polaroid",
    "roundededges",
    # #2141: a `picnikgrain` FÖLJEBB került, az 1. fül 5. csempéjéhez —
    # itt duplikátum volna.
)

#: Amit a szerkesztő ténylegesen a láncra tehet: a felület fülein szereplő
#: effektek ÉS a „Régi effektek" fül alkalmazható gombjai (#582).
_APPLICABLE_EFFECTS = frozenset(_EFFECT_NAMES) | frozenset(_LEGACY_EFFECT_NAMES)

#: A `.picasa.ini`-be írandó betűzés, ahol az eltér a belső kulcstól. A
#: Picasa a vignette-et NAGYBETŰVEL írja (`Vignette=1,...`); a round-trip
#: elv (CLAUDE.md 1. döntés) szerint mi is úgy írjuk, hogy a párhuzamosan
#: futó eredeti Picasa is felismerje. Beolvasásnál mindkét alak jó — a
#: renderelő kis-nagybetű-tűrő.
_EFFECT_INI_NAMES: dict[str, str] = {
    "vignette": "Vignette",
    # a 4-5. fül effektjeit a Picasa nagy kezdőbetűvel (több szónál
    # CamelCase-szel) írja — a `filters=` így marad kölcsönösen olvasható
    "ir": "IR",
    "lomo": "Lomo",
    "holga": "Holga",
    "hdr": "HDR",
    "cinemascope": "Cinemascope",
    "orton": "Orton",
    "sixties": "Sixties",
    "invert": "Invert",
    "heatmap": "HeatMap",
    "crossprocess": "CrossProcess",
    "quantizepalette": "QuantizePalette",
    "twotone": "TwoTone",
    "matte": "Matte",
    "nightvision": "NightVision",
    "localcontrast": "LocalContrast",
    "roundededges": "RoundedEdges",
    "picnikfocalpixelate": "PicnikFocalPixelate",
    "picnikgrain": "PicnikGrain",
    "picniktint": "PicnikTint",
    "boost": "Boost",
    "soften": "Soften",
    "pixelate": "Pixelate",
    "focalzoom": "FocalZoom",
    "pencilsketch": "PencilSketch",
    "neon": "Neon",
    "comicize": "Comicize",
    "border": "Border",
    "dropshadow": "DropShadow",
    "museummatte": "MuseumMatte",
    "polaroid": "Polaroid",
}

#: A retusálás-eszköz (#445) kör alakú ecsetének mérete-csúszkája [1..100]
#: egész egységben ("Brush Size", ld. `EditorPanel.qml`) — a valódi Picasa
#: ecsetméret-egysége nem ismert (ld. `picasapy.ini.retouch` docsztring),
#: ezért ez egy PicasaPy-saját, dokumentált leképezés: a csúszka-érték a
#: `_BRUSH_SIZE_TO_RELATIVE_DIVISOR`-ral osztva adja a relatív [0..1]
#: sugarat (a kép rövidebb oldalára vonatkoztatva, ld.
#: `picasapy.render.retouch.apply_retouch_patches`) — a felső határnál
#: (100) ez 0.1, azaz a kép rövidebb oldalának 10%-a, ami a legnagyobb
#: gyakorlati foltnak is elég, anélkül, hogy a fél képet lefedné.
_BRUSH_SIZE_MIN = 1
_BRUSH_SIZE_MAX = 100
_DEFAULT_BRUSH_SIZE = 20
_BRUSH_SIZE_TO_RELATIVE_DIVISOR = 1000.0

#: #450 (2. lépcső): tipográfia — a rajzoló (`render.text_fonts`) családja,
#: méret-szorzója és stílusai. A családnevet a rendszer betűtípus-adatbázisa
#: adja; a választott család a `text=` ini-mezőbe kerül.
#: #2287: a betűméret az eredeti 16 elemű listájából (`BETUMERETEK`),
#: alapértéke **12** (a panel `+0x2cc` mezőjének kezdő értéke).
_DEFAULT_TEXT_SIZE_PT = 12
_DEFAULT_TEXT_BOLD = False
_DEFAULT_TEXT_ITALIC = False
_DEFAULT_TEXT_UNDERLINE = False
_DEFAULT_TEXT_ALIGN = "left"

# A felirat pozíciója a `text=` kulcs GEOMETRIA mezőjében él, a képre
# normalizált [0..1] értékként (#371-ben megfejtve) — ugyanabban az
# egységben, amit a szerkesztő és az előnézet is használ, ezért nincs
# szükség átszámításra, és nem kell hozzá saját skálázó konstans sem. A
# 0.8.88-ig írt, PicasaPy-saját egész-kódolást az
# `picasapy.ini.text_overlay` olvasó oldala migrálja.

#: A szöveg-eszköz stílus-beállításai (#450). A `text=` stílusblokkjából ma
#: NÉGY beállítás megy oda-vissza: a kitöltés és a körvonal színe (#371), a
#: vízszintes igazítás és a kitöltés/körvonal mód (#2108, a 8. mező 8–15.
#: illetve 0–7. bitje).
#:
#: ⚠️ A mód SZÁMÍTOTT, nem tárolt: `no_fill` → 1; különben a vastagság
#: pontosan 0,0 → 0; egyébként → 2 (`fill_mode_from`). Visszatöltéskor
#: ezért a mód csak a kitöltés ki/be állapotát adja vissza — a
#: körvonalvastagság pontos értéke az 5. mezőben él, azt a #2271 írja ki.
#:
#: Ami MARAD munkamenet-állapot: az átlátszóság — annak a
#: Picasa-formátumban nincs megfelelő mezője.
#: #2108: a kitöltés/körvonal mód »nincs kitöltés« értéke.
_MOD_NINCS_KITOLTES = 1
_DEFAULT_TEXT_FILL_COLOR = (255, 255, 255)
_DEFAULT_TEXT_OUTLINE_COLOR = (0, 0, 0)
_DEFAULT_TEXT_OUTLINE_THICKNESS = 0
_DEFAULT_TEXT_FILL_ENABLED = True
_DEFAULT_TEXT_OPACITY = 1.0


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"Érvénytelen szín (nem #rrggbb alakú): {value!r}")
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError as error:
        raise ValueError(f"Érvénytelen szín (nem #rrggbb alakú): {value!r}") from error


def _rgb_to_argb(rgb: tuple[int, int, int]) -> int:
    """RGB → a `text=` stílus-mezőjének `0xAARRGGBB` egésze, teljesen
    átlátszatlan alfával (a korpusz mindkét mintáján `0xFF` az alfa)."""
    r, g, b = rgb
    return 0xFF000000 | (r << 16) | (g << 8) | b


def _argb_to_rgb(argb: int) -> tuple[int, int, int]:
    """`0xAARRGGBB` → RGB; az alfát elhagyjuk (a rajzoló külön
    `opacity`-vel dolgozik)."""
    return ((argb >> 16) & 0xFF, (argb >> 8) & 0xFF, argb & 0xFF)



def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _action_key(filter_name: str) -> str:
    """Szűrő-név → művelet-kulcs a Visszavonás-felirathoz (crop64→crop)."""
    key = filter_name.casefold()
    if key == "crop64":
        return "crop"
    return key



def _controller_family_labels():
    """A betűcsalád-olvasó monkeypatch-kompatibilis hídja."""
    from . import edit_controller
    return edit_controller.family_labels()


def _controller_update_document(*args, **kwargs):
    """Az ini-író monkeypatch-kompatibilis hídja."""
    from . import edit_controller
    return edit_controller.update_document(*args, **kwargs)

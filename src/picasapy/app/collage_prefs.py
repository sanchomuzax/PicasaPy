"""A kollázs-panel megőrzött beállításai (#943) — spec 9.3.

Tiszta réteg a QSettings fölött: kulcsok egy helyen, a visszatöltés
értelmezhetetlen értéknél az ALAPÉRTELMEZÉSRE esik vissza (a
`window_geometry.py` „értelmetlen mentés = alapértelmezés" elve). Egy
kézzel átírt vagy régi verzióból maradt beállítás sosem omlaszthatja el a
panelt.

A `collage/format` a formátum KULCSÁT tárolja (`Desktop4x3`), nem a
Picasa nyers sorszámát: a szám a menü sorrendjéhez kötődne, és egy későbbi
tétel beszúrása némán elmozdítaná a jelentését.
"""

from __future__ import annotations

from dataclasses import dataclass

from picasapy.collage.page_formats import (
    DEFAULT_FORMAT_KEY,
    ORIENTATIONS,
    is_known_format,
)
from picasapy.collage.themes import COLLAGE_THEMES, PICTUREPILE, capabilities_for

THEME_KEY = "collage/theme"
FORMAT_KEY = "collage/format"
ORIENTATION_KEY = "collage/orientation"
SHADOWS_KEY = "collage/shadows"
CAPTIONS_KEY = "collage/showcaptions"
BGCOLOR_KEY = "collage/bgcolor"
#: A legutóbb kiírt piszkozat útvonala (spec 9.3 hetedik kulcsa). Nem a
#: piszkozat TARTALMA — az `autosave.cxf`-ben él —, hanem az, hogy hol
#: keressük: a felhasználó a Kollázsok album helyét átállíthatja, és egy
#: összeomlás után a régi helyen álló piszkozatot is meg kell találnunk.
AUTOSAVE_KEY = "collage/autosave"

#: A piszkozat HELYKITÖLTŐ képének útvonala (#1125). Enélkül a
#: véglegesítés nem tudja, melyik JPEG a sajátja: a „nincs `.cxf` párja"
#: IGAZ egy idegen képre is, amit a felhasználó tett a mappába.
PLACEHOLDER_KEY = "collage/draftPlaceholder"
#: A kimeneti mappa („Kollázsok" album). Kulcsként tartjuk, hogy a teszt és
#: a későbbi beállítás-panel ugyanazt az egy helyet írja.
OUTPUT_DIR_KEY = "collage/outputDir"

#: A háttérszín alapértéke — a `.cxf` `DEFAULT_BACKGROUND_COLOR`-jával egyező
#: átlátszatlan fekete (`0x008342b0`).
DEFAULT_BACKGROUND = "#000000"

#: Az alapértelmezett tájolás: a `.tre`-ben a **fekvő** gomb az előre
#: lenyomott (`Property setpressed 1`).
DEFAULT_ORIENTATION = "landscape"


def flag(value, default: bool) -> bool:
    """QSettings-érték bool-lá; hiányzó vagy értelmezhetetlen = alapérték.

    A `QSettings` platformonként bool-t vagy szöveget ad vissza ugyanarra az
    írásra — az `appearance_controller.coerce_dark_flag` mintája."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("true", "1"):
            return True
        if text in ("false", "0"):
            return False
    return default


@dataclass(frozen=True)
class CollagePrefs:
    """A visszatöltött beállítások.

    `shadows_explicit` azt őrzi, hogy a felhasználó hozzányúlt-e már az
    árnyék-jelölőhöz: amíg nem, a TÉMA dönt (a maszk 14. bitje), tehát a
    téma-váltás az árnyékot is átállítja — utána viszont a felhasználó
    döntése marad érvényben."""

    theme: str = PICTUREPILE
    format_key: str = DEFAULT_FORMAT_KEY
    orientation: str = DEFAULT_ORIENTATION
    captions: bool = True
    shadows: bool = True
    shadows_explicit: bool = False
    background_color: str = DEFAULT_BACKGROUND


def load_prefs(settings) -> CollagePrefs:
    """A panel indulóállapota a QSettings-ből, hibatűrően."""
    theme = settings.value(THEME_KEY, PICTUREPILE)
    theme = theme if theme in COLLAGE_THEMES else PICTUREPILE

    format_key = settings.value(FORMAT_KEY, DEFAULT_FORMAT_KEY)
    if not isinstance(format_key, str) or not is_known_format(format_key):
        format_key = DEFAULT_FORMAT_KEY

    orientation = settings.value(ORIENTATION_KEY, DEFAULT_ORIENTATION)
    if orientation not in ORIENTATIONS:
        orientation = DEFAULT_ORIENTATION

    stored_shadow = settings.value(SHADOWS_KEY)
    color = settings.value(BGCOLOR_KEY, DEFAULT_BACKGROUND)
    return CollagePrefs(
        theme=theme,
        format_key=format_key,
        orientation=orientation,
        captions=flag(settings.value(CAPTIONS_KEY), True),
        shadows=flag(stored_shadow, capabilities_for(theme).shadow_default),
        shadows_explicit=stored_shadow is not None,
        background_color=str(color) if color else DEFAULT_BACKGROUND,
    )


__all__ = [
    "AUTOSAVE_KEY",
    "PLACEHOLDER_KEY",
    "BGCOLOR_KEY",
    "CAPTIONS_KEY",
    "DEFAULT_BACKGROUND",
    "DEFAULT_ORIENTATION",
    "FORMAT_KEY",
    "ORIENTATION_KEY",
    "OUTPUT_DIR_KEY",
    "SHADOWS_KEY",
    "THEME_KEY",
    "CollagePrefs",
    "flag",
    "load_prefs",
]

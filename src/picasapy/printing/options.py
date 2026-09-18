"""A Picasa-nyomat szegély- és felirat-beállításai (#1780).

A binárisan igazolt `Preferences\\printoptions::*` kulcsok PicasaPy-ben
QSettings-kulcsokként, a `printoptions/` névtér alatt élnek. A réteg
szándékosan Qt-rajzolás nélküli: a beállítások betöltése, mentése és
érvényesítése önállóan tesztelhető, a `PrintController` csak ezt fogyasztja.

A szegélyvastagság tárolt értéke **0..1024**, nem a QML Slider 0..1 értéke.
A színek az eredeti `0xAARRGGBB` dword alakját őrzik.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from PySide6.QtGui import QColor

TEXT_SIZE_VALUES: tuple[int, ...] = (
    8,
    10,
    12,
    14,
    16,
    18,
    20,
    22,
    26,
    30,
    36,
    48,
    60,
    72,
    84,
    96,
)

TEXT_SOURCE_MAX = 3
TEXT_PLACEMENT_MAX = 2
BORDER_SIZE_MAX = 1024


@dataclass(frozen=True)
class PrintOptions:
    """A nyomtatási kinézet 11 tartós beállítása."""

    textSource: int = 0
    textPlacement: int = 0
    textFont: str = "Arial"
    textSize: int = 12
    textColor: int = 0
    wrap: bool = False
    border: bool = False
    borderSize: int = 10
    borderColor: int = 0
    borderEdge: bool = False
    evenBorder: bool = True

    def as_mapping(self) -> dict[str, Any]:
        return {mezo.name: getattr(self, mezo.name) for mezo in fields(self)}


#: A kulcsok külön névtere biztosítja, hogy egy QSettings-backend se írja
#: felül a nyomtató vagy a nyomatméret más beállítását.
_OPTION_KEYS = {
    "textSource": "printoptions/text",
    "textPlacement": "printoptions/textplacement",
    "textFont": "printoptions/textfont",
    "textSize": "printoptions/textsize",
    "textColor": "printoptions/textcolor",
    "wrap": "printoptions/wrap",
    "border": "printoptions/border",
    "borderSize": "printoptions/bordersize",
    "borderColor": "printoptions/bordercolor",
    "borderEdge": "printoptions/borderedge",
    "evenBorder": "printoptions/evenborder",
}


def _bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.strip().lower() in {"true", "1", "yes", "on"}:
            return True
        if value.strip().lower() in {"false", "0", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def _color(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number & 0xFFFFFFFF


def load_print_options(settings) -> PrintOptions:
    """A beállítások hibatűrő betöltése QSettings-ből."""
    alap = PrintOptions()
    values: dict[str, Any] = {}
    for mezo in fields(alap):
        kulcs = _OPTION_KEYS[mezo.name]
        nyers = settings.value(kulcs, getattr(alap, mezo.name))
        if mezo.name == "textSource":
            values[mezo.name] = _int(nyers, alap.textSource, 0, TEXT_SOURCE_MAX)
        elif mezo.name == "textPlacement":
            values[mezo.name] = _int(
                nyers, alap.textPlacement, 0, TEXT_PLACEMENT_MAX
            )
        elif mezo.name == "textFont":
            values[mezo.name] = str(nyers or alap.textFont)
        elif mezo.name == "textSize":
            try:
                meret = int(nyers)
            except (TypeError, ValueError):
                meret = alap.textSize
            values[mezo.name] = (
                meret if meret in TEXT_SIZE_VALUES else alap.textSize
            )
        elif mezo.name in {"textColor", "borderColor"}:
            values[mezo.name] = _color(nyers, getattr(alap, mezo.name))
        elif mezo.name in {"wrap", "border", "borderEdge", "evenBorder"}:
            values[mezo.name] = _bool(nyers, getattr(alap, mezo.name))
        elif mezo.name == "borderSize":
            values[mezo.name] = _int(nyers, alap.borderSize, 0, BORDER_SIZE_MAX)
    return PrintOptions(**values)


def save_print_options(settings, options: PrintOptions) -> None:
    """Mind a 11 kulcs explicit mentése; a QSettings-backend szinkronizál."""
    for mezo in fields(options):
        settings.setValue(_OPTION_KEYS[mezo.name], getattr(options, mezo.name))
    settings.sync()


def update_print_option(options: PrintOptions, name: str, value: Any) -> PrintOptions:
    """Egy QML-ből érkező mező érvényesítése új, immutábilis állapottá."""
    if name not in _OPTION_KEYS:
        return options
    values = options.as_mapping()
    if name == "textSource":
        values[name] = _int(value, options.textSource, 0, TEXT_SOURCE_MAX)
    elif name == "textPlacement":
        values[name] = _int(value, options.textPlacement, 0, TEXT_PLACEMENT_MAX)
    elif name == "textFont":
        text = str(value or "").strip()
        values[name] = text or options.textFont
    elif name == "textSize":
        try:
            meret = int(value)
        except (TypeError, ValueError):
            meret = options.textSize
        values[name] = meret if meret in TEXT_SIZE_VALUES else options.textSize
    elif name in {"textColor", "borderColor"}:
        values[name] = _color(value, getattr(options, name))
    elif name in {"wrap", "border", "borderEdge", "evenBorder"}:
        values[name] = _bool(value, getattr(options, name))
    elif name == "borderSize":
        values[name] = _int(value, options.borderSize, 0, BORDER_SIZE_MAX)
    return PrintOptions(**values)


def argb_to_qcolor(value: int) -> QColor:
    """`0xAARRGGBB` → Qt QColor, csatorna-átrendezés nélkül."""
    number = int(value) & 0xFFFFFFFF
    return QColor(
        (number >> 16) & 0xFF,
        (number >> 8) & 0xFF,
        number & 0xFF,
        (number >> 24) & 0xFF,
    )


def qcolor_to_argb(color: QColor) -> int:
    """Qt QColor → az eredeti `0xAARRGGBB` egész alak."""
    return (
        (color.alpha() << 24)
        | (color.red() << 16)
        | (color.green() << 8)
        | color.blue()
    )


def has_render_effects(options: PrintOptions) -> bool:
    """Igényel-e a nyomat extra rajzolást az alap kép fölött/alatt."""
    return options.textSource != 0 or (options.border and options.borderSize > 0)


__all__ = [
    "BORDER_SIZE_MAX",
    "PrintOptions",
    "TEXT_SIZE_VALUES",
    "argb_to_qcolor",
    "has_render_effects",
    "load_print_options",
    "qcolor_to_argb",
    "save_print_options",
    "update_print_option",
]

"""A weboldal-export méretei (#4610) — az eredeti `webexport.fen` és a
sablonok szabálya szerint (spec: `docs/specs/picasa-menu-parancsok-viselkedes.md`
6.1).

- A párbeszédnek EGY méretválasztója van (`popup name="sizeradio"`), és az
  a NAGY kép méretét adja. Bélyegkép-méret választó nincs.
- A bélyegkép méretét a sablon `define thumbnailWidth/thumbnailHeight`-je
  adja; ha a sablon nem adja meg, 144 képpont (`0x0086c125 push 0x90`).
- A sablon `define imageWidth/imageHeight`-je felülírja a választást.

A képek a `.tpl` futtatása ELŐTT készülnek (`images.py`), ezért a sablon
méret-`define`-jait itt, előre olvassuk ki az `index.tpl` saját soraiból."""

from __future__ import annotations

import dataclasses
import logging
from pathlib import Path

from .context import WebExportSettings
from .tpl_lang import DefineCommand, TplSyntaxError, parse_tpl

logger = logging.getLogger(__name__)

#: A `sizeradio` öt eleme a `webexport.fen` sorrendjében (4–8. sor):
#: Original Size · 1024 · 800 · 640 · 320. A 0 az eredeti méret.
SIZE_CHOICES: tuple[int, ...] = (0, 1024, 800, 640, 320)

#: `Preferences\WebExportSize` alapértéke 3 (`0x007f5310`) → 3. index, 640.
DEFAULT_SIZE_INDEX = 3

#: A bélyegkép mérete, ha a sablon nem adja meg (`0x0086c125`, `0x0086c136`).
DEFAULT_THUMBNAIL_SIZE = 144

_THUMB_KEYS = ("thumbnailWidth", "thumbnailHeight")
_IMAGE_KEYS = ("imageWidth", "imageHeight")


def image_size_for_index(index: int) -> int:
    """A választó indexéhez tartozó képpont (0 = eredeti méret). A táblán
    kívüli index az eredeti méretet adja — az eredeti is a 0. elemre ejti
    az ismeretlen tárolt értéket (`0x7f5bf0`)."""
    if 0 <= index < len(SIZE_CHOICES):
        return SIZE_CHOICES[index]
    return SIZE_CHOICES[0]


def settings_for_template(
    template_dir: Path, image_choice: int, base: WebExportSettings
) -> WebExportSettings:
    """A `base` beállítás új példánya a sablonhoz igazított képméretekkel:
    a nagy kép a választás (`image_choice`, 0 = eredeti), hacsak a sablon
    `define imageWidth`-je mást nem mond; a bélyegkép a sablon
    `define thumbnailWidth`-je, hiányában 144."""
    defines = _index_defines(Path(template_dir))
    thumb = _box(defines, _THUMB_KEYS, DEFAULT_THUMBNAIL_SIZE)
    image = _box(defines, _IMAGE_KEYS, image_choice)
    return dataclasses.replace(
        base,
        thumbnail_max_dimension=thumb or None,
        image_max_dimension=image or None,
    )


def _index_defines(template_dir: Path) -> dict[str, str]:
    """Az `index.tpl` saját `define` sorai (az utolsó nyer). Olvashatatlan
    vagy hibás sablonnál üres — a futtatás úgyis hangosan bukik rajta."""
    try:
        text = (template_dir / "index.tpl").read_text(encoding="utf-8")
        commands = parse_tpl(text)
    except (OSError, TplSyntaxError) as error:
        logger.warning("A sablon méretei nem olvashatók (%s): %s", template_dir, error)
        return {}
    return {c.name: c.value for c in commands if isinstance(c, DefineCommand)}


def _box(defines: dict[str, str], keys: tuple[str, str], default: int) -> int:
    """Szélesség/magasság párból a leghosszabb oldal korlátja. Az `ExportSettings`
    egyetlen méretet ismer: eltérő párnál a kisebbik nem-nulla érték fér a
    dobozba. Hiányzó vagy nem szám érték a `default`-ra esik."""
    values = [_int_or(defines.get(key), default) for key in keys]
    nonzero = [v for v in values if v > 0]
    return min(nonzero) if nonzero else 0


def _int_or(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return max(0, int(value.strip()))
    except ValueError:
        return default

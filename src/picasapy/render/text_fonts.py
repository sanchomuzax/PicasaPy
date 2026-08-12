"""TrueType-betűtípusok a szöveg-eszközhöz (#450).

**Miért kellett:** a szöveg-overlay eddig az OpenCV **Hershey**-készletével
rajzolt. Abban nincs betűcsalád, nincs félkövér/dőlt, nincs aláhúzás, és a
betűkép sem hasonlít a Picasa TrueType-betűire — vagyis a jegy hátralévő
vezérlői (betűtípus · méret · B/I/U · igazítás) egyszerűen nem voltak
megvalósíthatók. A Pillow (már függőség) FreeType-rajzolója mindezt tudja.

**A családok leképezése.** A Picasa a Windows rendszer-betűit kínálta
(Arial, Times New Roman, Courier New…). Linuxon ezek jellemzően nincsenek
meg, viszont a **Liberation**-készlet METRIKUSAN kompatibilis velük
(ugyanaz a betűszélesség, ezért a tördelés is egyezik) — ezt használjuk
helyettesítőnek. A keresés fájlnév-jelöltek listáján megy, nem
fontconfig-on: így determinisztikus, és a tesztek is ellenőrizhetik.

**Ha egyetlen TrueType sem található**, a hívó a régi Hershey-úton rajzol
tovább (ld. `render.text_overlay`) — a szöveg-eszköz sosem eshet ki, csak a
tipográfia lesz szegényebb.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

from PIL import ImageFont

#: Ahol TrueType-fájlokat keresünk. A sorrend számít: a rendszer saját
#: mappái előbb, mert ott állnak az eredeti (Arial, Times) betűk, ha
#: egyáltalán telepítve vannak.
_FONT_DIRS: tuple[str, ...] = (
    "C:/Windows/Fonts",
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/Library/Fonts",
    "/System/Library/Fonts",
    str(Path.home() / ".fonts"),
    str(Path.home() / ".local/share/fonts"),
)


class FontFamily(NamedTuple):
    """Egy felkínált betűcsalád és a hozzá tartozó fájlnév-jelöltek.

    A `regular`/`bold`/`italic`/`bold_italic` mezők fájlnév-listák: az első
    létező nyer. A Picasa saját (windowsos) neve áll elöl, utána a
    metrikusan kompatibilis Liberation-változat, végül a DejaVu — az utóbbi
    nem metrikus párja egyiknek sem, de szinte minden Linuxon ott van.
    """

    key: str
    label: str
    regular: tuple[str, ...]
    bold: tuple[str, ...]
    italic: tuple[str, ...]
    bold_italic: tuple[str, ...]


#: A felkínált családok. Szándékosan RÖVID lista: a Picasa is a rendszer
#: betűit sorolta, de a hűség szempontjából az számít, hogy a három
#: klasszikus osztály (talpatlan · talpas · írógép) elérhető legyen, és
#: hogy a leképezés metrikusan pontos maradjon.
FONT_FAMILIES: tuple[FontFamily, ...] = (
    FontFamily(
        "arial", "Arial",
        ("arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"),
        ("arialbd.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"),
        ("ariali.ttf", "LiberationSans-Italic.ttf", "DejaVuSans-Oblique.ttf"),
        ("arialbi.ttf", "LiberationSans-BoldItalic.ttf",
         "DejaVuSans-BoldOblique.ttf"),
    ),
    FontFamily(
        "times", "Times New Roman",
        ("times.ttf", "LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"),
        ("timesbd.ttf", "LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"),
        ("timesi.ttf", "LiberationSerif-Italic.ttf", "DejaVuSerif-Italic.ttf"),
        ("timesbi.ttf", "LiberationSerif-BoldItalic.ttf",
         "DejaVuSerif-BoldItalic.ttf"),
    ),
    FontFamily(
        "courier", "Courier New",
        ("cour.ttf", "LiberationMono-Regular.ttf", "DejaVuSansMono.ttf"),
        ("courbd.ttf", "LiberationMono-Bold.ttf", "DejaVuSansMono-Bold.ttf"),
        ("couri.ttf", "LiberationMono-Italic.ttf", "DejaVuSansMono-Oblique.ttf"),
        ("courbi.ttf", "LiberationMono-BoldItalic.ttf",
         "DejaVuSansMono-BoldOblique.ttf"),
    ),
)

#: Az alapértelmezett család kulcsa — a Picasa szöveg-eszköze is
#: talpatlan betűvel indult.
DEFAULT_FAMILY = "arial"

_FAMILY_BY_KEY = {family.key: family for family in FONT_FAMILIES}


def family_labels() -> list[dict[str, str]]:
    """A felület lenyílójának adata: `key` + megjelenő `label`."""
    return [{"key": f.key, "label": f.label} for f in FONT_FAMILIES]


def _candidate_files(family: FontFamily, bold: bool, italic: bool) -> tuple[str, ...]:
    if bold and italic:
        return family.bold_italic
    if bold:
        return family.bold
    if italic:
        return family.italic
    return family.regular


def _find_file(names: Iterable[str]) -> Path | None:
    """Az első létező fájl a jelöltek közül, a `_FONT_DIRS` alatt.

    A keresés rekurzív (a Linux-disztribúciók almappákba rendezik a
    készleteket), és kis-nagybetű-tűrő, mert a Windows-fájlnevek írásmódja
    gépenként eltérhet.
    """
    wanted = {name.casefold(): index for index, name in enumerate(names)}
    best: tuple[int, Path] | None = None
    for directory in _FONT_DIRS:
        root = Path(directory)
        if not root.is_dir():
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for filename in filenames:
                index = wanted.get(filename.casefold())
                if index is not None and (best is None or index < best[0]):
                    best = (index, Path(dirpath) / filename)
                    if index == 0:
                        return best[1]
    return best[1] if best else None


def font_path_for(
    family_key: str, *, bold: bool = False, italic: bool = False
) -> Path | None:
    """A kért stílushoz tartozó TrueType-fájl, vagy `None`.

    Ha a kért stílus (pl. dőlt) fájlja nincs meg, a NORMÁL változatra
    esünk vissza — jobb a szöveget a helyes családdal, dőlés nélkül
    kirajzolni, mint egy egészen más betűvel.
    """
    family = _FAMILY_BY_KEY.get(family_key) or _FAMILY_BY_KEY[DEFAULT_FAMILY]
    path = _find_file(_candidate_files(family, bold, italic))
    if path is None and (bold or italic):
        path = _find_file(family.regular)
    return path


def load_font(
    family_key: str, size_px: int, *, bold: bool = False, italic: bool = False
):
    """Betöltött Pillow-betű a kért stílusban, vagy `None`, ha nincs
    használható TrueType a gépen (a hívó ilyenkor a Hershey-útra esik)."""
    if size_px <= 0:
        raise ValueError(f"A betűméret pozitív kell legyen: {size_px}")
    path = font_path_for(family_key, bold=bold, italic=italic)
    if path is None:
        return None
    try:
        return ImageFont.truetype(str(path), size_px)
    except OSError:
        # sérült vagy nem támogatott fájl — a hívó a Hershey-útra esik
        return None


__all__ = [
    "DEFAULT_FAMILY",
    "FONT_FAMILIES",
    "FontFamily",
    "family_labels",
    "font_path_for",
    "load_font",
]

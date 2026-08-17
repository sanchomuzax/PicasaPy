"""A kollázs kilenc téma-kulcsa — a Picasa `.exe` string-táblájából (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.1 és 1.6/b. A kilenc kulcs
egyetlen összefüggő tömbben áll a binárisban; az első három a **keret**, a
maradék hat a **kollázs-típus**. A `.cxf` fájl szó szerint ezeket írja ki,
tehát egy betű eltérés is olvashatatlanná tenné a fájlt az eredetinek.

⚠️ **A csapda:** a felületi „Mozaik" kulcsa `picturegrid`, a „Rács"-é viszont
`regulargrid` — a „grid" szó NEM ott van, ahol a magyar (vagy angol) névből
gondolná az ember. Aki a UI-névből következtet, két típust ír rosszul a
fájlba.
"""

from __future__ import annotations

from typing import NamedTuple

# --- Kollázs-típusok (a `.cxf` gyökér `theme` attribútuma) -------------------

PICTUREPILE = "picturepile"  # Képkupac — szétszórt képek
PICTUREGRID = "picturegrid"  # Mozaik — automatikus illesztés az oldalra
FRAMEGRID = "framegrid"  # Képkockamozaik — hangsúlyos központi kép
REGULARGRID = "regulargrid"  # Rács — szabályos sorok és oszlopok
CONTACTSHEET = "contactsheet"  # Indexkép — tájékoztató fejléccel
MULTIEXP = "multiexp"  # Többszörös exponálás — egymásra vetítés

COLLAGE_THEMES = (
    PICTUREPILE,
    PICTUREGRID,
    FRAMEGRID,
    REGULARGRID,
    CONTACTSHEET,
    MULTIEXP,
)
"""A hat típus a FELÜLETI sorrendben (a bináris tömbjének sorrendje más)."""

# --- Képkeretek (a `.cxf` csomóponton belüli `<theme>`) ---------------------

NOBORDER = "noborder"  # Egyik sem — csak a kép
WHITEBORDER = "whiteborder"  # Fehér szegély
POLAROID = "polaroid"  # Polaroid fényképezőgép — ITT jelenik meg a felirat

BORDER_THEMES = (NOBORDER, WHITEBORDER, POLAROID)

# A háttérként használt kép „tompított" módja (`DimmedBitmapTheme`).
DIMMED = "dimmed"

# A Picasa C++ osztályneve témánként (RTTI-ből) — a dekompilált kód és a
# specifikáció összekötéséhez, hibakereséskor hasznos.
THEME_CLASS_NAMES = {
    PICTUREPILE: "CPileTheme",
    PICTUREGRID: "CGridTheme",
    FRAMEGRID: "CFrameGridTheme",
    REGULARGRID: "CRegularGridTheme",
    CONTACTSHEET: "CContactSheetTheme",
    MULTIEXP: "CMultiExposureTheme",
    NOBORDER: "NoBorderTheme",
    WHITEBORDER: "WhiteBorderTheme",
    POLAROID: "PolaroidBitmapTheme",
    DIMMED: "DimmedBitmapTheme",
}

# --- A témák KÉPESSÉG-MASZKJA (#923) ---------------------------------------
#
# A Picasában nem minden beállítás értelmes minden kollázs-típusnál, és ezt
# NEM témánkénti felületi kód dönti el, hanem egy konstans bitmaszk, amit
# minden téma-osztály 7. vtable-slotja ad vissza. A panel (`0x00831750`)
# ebből mutatja, rejti és tiltja a vezérlőit.
#
# | téma | maszk | cím |
# |---|---|---|
# | `picturepile` | `0x1EBBF` | `0x00829c70` |
# | `picturegrid` | `0x1C55` | `0x00829c90` |
# | `framegrid` | `0x1C55` | `0x00829c90` |
# | `regulargrid` | `0x0C55` | `0x00829ce0` |
# | `contactsheet` | `0x4B11` | `0x00829d40` |
# | `multiexp` | `0x0100` | `0x00829d00` |
#
# A megfejtett bitek:
#
# | bit | jelentés | cím |
# |---|---|---|
# | 4 | a kijelölés engedélyezett | `0x008318ed` |
# | 9 | a három keretgomb látszik | `0x008317f5` |
# | 10 | a térköz-csúszka látszik | `0x00831860` |
# | 11 | az árnyék-jelölő engedélyezett | `0x00831818` |
# | 14 | a `collage::shadows` ALAPÉRTÉKE | (kutatás, 2026-08-18) |
#
# ⚠️ A keretsor (13, 122) 266×89 és a térköz-csoport (19, 123) 250×81
# UGYANAZT a helyet foglalja a panelen — ez önmagában bizonyítja, hogy a
# kettő sosem látszik együtt.
#
# A 15. és 16. bitnek NINCS fogyasztója a `.text`-ben (halott bitek), a
# 12. bit „képesség-hirdetés" (a téma megvalósítja a 9. vtable-slotot: csak
# a `CGridTheme` és a `CFrameGridTheme`), a 6. bit jelentése NYITOTT.

#: A hat téma nyers maszkja — a forrás a fenti tábla.
THEME_MASKS = {
    PICTUREPILE: 0x1EBBF,
    PICTUREGRID: 0x1C55,
    FRAMEGRID: 0x1C55,
    REGULARGRID: 0x0C55,
    CONTACTSHEET: 0x4B11,
    MULTIEXP: 0x0100,
}

_BIT_SELECTION = 4
_BIT_BORDERS = 9
_BIT_SPACING = 10
_BIT_SHADOW = 11
_BIT_SHADOW_DEFAULT = 14


class ThemeCapabilities(NamedTuple):
    """Egy téma engedélyezett beállításai — a maszkból származtatva.

    `shadow_default` a `collage::shadows` alapértéke (14. bit): árnyék
    alapból BE a Képkupacnál és az Indexképnél, KI a másik négynél.
    """

    borders: bool
    spacing: bool
    shadow: bool
    selection: bool
    shadow_default: bool


def capabilities_for(theme: str) -> ThemeCapabilities:
    """A téma képességei. Ismeretlen téma = hiba (nem néma alapértelmezés)."""
    if theme not in THEME_MASKS:
        raise ValueError(f"Ismeretlen kollázs-téma: {theme!r}")
    mask = THEME_MASKS[theme]
    return ThemeCapabilities(
        borders=bool(mask & (1 << _BIT_BORDERS)),
        spacing=bool(mask & (1 << _BIT_SPACING)),
        shadow=bool(mask & (1 << _BIT_SHADOW)),
        selection=bool(mask & (1 << _BIT_SELECTION)),
        shadow_default=bool(mask & (1 << _BIT_SHADOW_DEFAULT)),
    )


#: Előszámolt tábla — a `capabilities_for` gyorsítója és egyben olvasható
#: dokumentáció arról, mi látszik melyik témánál.
THEME_CAPABILITIES = {theme: capabilities_for(theme) for theme in COLLAGE_THEMES}

__all__ = [
    "BORDER_THEMES",
    "COLLAGE_THEMES",
    "CONTACTSHEET",
    "DIMMED",
    "FRAMEGRID",
    "MULTIEXP",
    "NOBORDER",
    "PICTUREGRID",
    "PICTUREPILE",
    "POLAROID",
    "REGULARGRID",
    "THEME_CLASS_NAMES",
    "WHITEBORDER",
]

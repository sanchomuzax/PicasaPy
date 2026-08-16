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

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
# | 6 | a CSOPORT-CSOMÓPONT külön overlay-ágba kerül | `0x00860470` |
# | 9 | a három keretgomb látszik | `0x008317f5` |
# | 10 | a térköz-csúszka látszik | `0x00831860` |
# | 11 | az árnyék-jelölő engedélyezett | `0x00831818` |
# | 14 | a `collage::shadows` ALAPÉRTÉKE | (kutatás, 2026-08-18) |
#
# ⚠️ A keretsor (13, 122) 266×89 és a térköz-csoport (19, 123) 250×81
# UGYANAZT a helyet foglalja a panelen — ez önmagában bizonyítja, hogy a
# kettő sosem látszik együtt.
#
# ⚠️ BIZONYÍTOTTSÁGI FOK — bitenként ELTÉRŐ, ne kezeld egyformán:
#
# | bit | mi támasztja alá |
# |---|---|
# | 9 (keret) | a fogyasztó kód + a felhasználó képernyőképe — de CSAK a Képkupacra |
# | 10 (térköz) | ugyanaz, szintén csak a Képkupacra |
# | 14 (árnyék alapérték) | ugyanaz, szintén csak a Képkupacra |
# | 4 (kijelölés) | **KIZÁRÓLAG a fogyasztó kód olvasata** — nincs külső megerősítés |
# | 11 (árnyék engedélyezve) | **KIZÁRÓLAG a fogyasztó kód olvasata** — nincs külső megerősítés |
# | 6 (csoport-overlay) | **megerősített mechanizmus** — utasításszinten végigkövetve (#1170) |
#
# A maszkértékek ÉS a bit→jelentés hozzárendelés UGYANABBÓL az egy forrásból
# származik (a `0x00831750` / `0x0082c4e0` visszafejtése). A `capabilities_for`
# származtatása ezért NEM független megerősítés: azt igazolja, hogy a maszkok
# és a belőlük közölt tábla között nincs átírási/számolási hiba — a bitek
# JELENTÉSÉT nem.
#
# A legolcsóbb valódi ellenőrzés: a **Többszörös exponálás** az eredetiben.
# A jóslat szerint ott sem kijelölés, sem háttér-beállítás, sem árnyék nincs —
# egyetlen képernyőkép NÉGY bitet dönt el egyszerre.
#
# A 15. és 16. bitnek NINCS fogyasztója a `.text`-ben (halott bitek), a
# 12. bit „képesség-hirdetés" (a téma megvalósítja a 9. vtable-slotot: csak
# a `CGridTheme` és a `CFrameGridTheme`).
#
# --- A 6. BIT — MEGFEJTVE (#1170, kutatás 2026-08-21) -----------------------
#
# A bit a kollázs **csoport-csomópontját** (`collagepanel/groupnode`) teszi
# **külön, a szülőtől független feldolgozási ágba** — overlay-rétegbe —, a
# szokásos, szülőhöz kötött jelenetgráf-bejárás helyett. NEM szövegelrendezési
# kapcsoló: az a 2016 előtti feltevés volt, és megdőlt.
#
# A kapu maga (`CollageNodeHandler` vtable 5. rekesze, `0x008603c0`):
#
#     0x0086046e  call edx        ; a téma képesség-maszkja (vt[0x1c])
#     0x00860470  shr  eax, 6
#     0x00860473  test al, 1      ; << a 6. BIT
#     0x00860475  je   0x86054f   ; nincs -> kihagyja
#     0x00860488  mov  byte ptr [edi + 0x219], 1   ; a jelző, amit a bejáró néz
#
# A `+0x219` jelzőt a jelenetgráf-bejáró (`0x009e2aa5`) olvassa: a csomópont
# rekordja KÜLÖN verembe kerül, és a rutin azonnal kilép — a normál ág
# (piszkos jelzők, geometria-összevetés) nem fut le rá. A `.text` teljes
# pásztázása szerint a jelzőnek kilenc beállítója van, és mind lebegő,
# szülő fölé kilógó, kódból épülő gyerekcsoportot rak össze (az arcpanel
# kiegészítői, a vágókeret, a színpaletta) — innen az „overlay" olvasat.
#
# A csomópont RAJZA is ki van mérve (`docs/specs/picasa-kollazs-felulet.md`
# **2/b**): `#F85E0F` színű, 2 képpont vastag, élsimított KÖRVONALAS
# téglalap — a felületi megvalósítása a `CollageGroupNode.qml`.

#: A hat téma nyers maszkja — a forrás a fenti tábla.
THEME_MASKS = {
    PICTUREPILE: 0x1EBBF,
    PICTUREGRID: 0x1C55,
    FRAMEGRID: 0x1C55,
    REGULARGRID: 0x0C55,
    CONTACTSHEET: 0x4B11,
    MULTIEXP: 0x0100,
}

# #943: a panel a MARADÉK öt bitet is használja — a `collageCapabilities`
# térkép mind a kilenc képességet továbbadja a QML-nek, hogy témánkénti `if`
# sehol ne szülessen (`kollazs-panel-ui-spec.md` 5.).
#
# | bit | jelentés | mi támasztja alá |
# |---|---|---|
# | 0 | a háttér-beállítások látszanak | a panelkód olvasata (`0x00831750`) |
# | 2 | „Képek összekeverése" engedélyezve (≥ 2 kép) | `0x0082fa0f` |
# | 3 | „Véletlenszerű kollázs" engedélyezve (≥ 1 kép) | `0x0082fa60` |
# | 7 | szabad elforgatás | spec 15.: **erős** |
#
# ⚠️ A **gyűrű** (5. bit) a leggyengébb láncszem: a spec 5. mátrixa szerint a
# gyűrű CSAK a Képkupacnál van, és az 5. bit pontosan ott áll — de a 7. bit
# is, tehát a kettő szétosztása (5 = gyűrű, 7 = forgatás) a maszkokból
# önmagában NEM eldönthető. A 7 = forgatás a specből jön, az 5 = gyűrű az
# ebből maradó következtetés. A megvalósítást nem befolyásolja: mindkét bit
# ugyanarra az egy témára áll.
_BIT_BACKGROUND = 0
_BIT_SHUFFLE = 2
_BIT_SCRAMBLE = 3
_BIT_SELECTION = 4
_BIT_RING = 5
_BIT_GROUP_OVERLAY = 6
_BIT_ROTATE = 7
_BIT_BORDERS = 9
_BIT_SPACING = 10
_BIT_SHADOW = 11
_BIT_SHADOW_DEFAULT = 14


class ThemeCapabilities(NamedTuple):
    """Egy téma engedélyezett beállításai — a maszkból származtatva.

    `shadow_default` a `collage::shadows` alapértéke (14. bit): árnyék
    alapból BE a Képkupacnál és az Indexképnél, KI a másik négynél.

    #943: az öt középső mező a panel többi vezérlőjét kapcsolja (háttér-doboz,
    a két véletlenszerűsítő gomb, a gyűrű-overlay és a szabad forgatás).

    `group_overlay` (#1170, 6. bit) a vászon CSOPORT-ELEMÉT engedélyezi: a
    három rács-témánál a többszörös kijelölés köré körvonalas keret kerül,
    külön overlay-rétegben. Nem panel-vezérlő — a vászon olvassa.

    ⚠️ Az ÚJ mezők MINDIG a sor VÉGÉN állnak, hogy a #923 óta meglévő négy
    mező helye (és a `picasa_render` olvasata) ne csússzon el.
    """

    borders: bool
    spacing: bool
    shadow: bool
    selection: bool
    shadow_default: bool
    background: bool
    shuffle: bool
    scramble: bool
    ring: bool
    rotate: bool
    group_overlay: bool


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
        background=bool(mask & (1 << _BIT_BACKGROUND)),
        shuffle=bool(mask & (1 << _BIT_SHUFFLE)),
        scramble=bool(mask & (1 << _BIT_SCRAMBLE)),
        ring=bool(mask & (1 << _BIT_RING)),
        rotate=bool(mask & (1 << _BIT_ROTATE)),
        group_overlay=bool(mask & (1 << _BIT_GROUP_OVERLAY)),
    )


#: A FELÜLETNEK átadott képesség-térkép mezői (spec 8.1). A
#: `shadow_default` szándékosan NINCS köztük: az az árnyék-jelölő
#: kezdőértéke, nem külön vezérlő — a panelen nincs mit mutatni belőle.
UI_CAPABILITY_FIELDS = (
    "borders",
    "spacing",
    "shadow",
    "selection",
    "background",
    "shuffle",
    "scramble",
    "ring",
    "rotate",
    "group_overlay",
)


def capability_map(theme: str) -> dict[str, bool]:
    """A téma képességei SZÓTÁRKÉNT — ezt adja tovább a vezérlő a QML-nek
    (`collageCapabilities`, QVariantMap). Egyetlen forrás, hogy témánkénti
    `if` se a Pythonban, se a QML-ben ne szülessen."""
    c = capabilities_for(theme)
    return {name: bool(getattr(c, name)) for name in UI_CAPABILITY_FIELDS}


#: Előszámolt tábla — a `capabilities_for` gyorsítója és egyben olvasható
#: dokumentáció arról, mi látszik melyik témánál.
THEME_CAPABILITIES = {theme: capabilities_for(theme) for theme in COLLAGE_THEMES}

__all__ = [
    "BORDER_THEMES",
    "UI_CAPABILITY_FIELDS",
    "capabilities_for",
    "capability_map",
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

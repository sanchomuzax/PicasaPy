"""A kollázs Oldalformátum-listája (#943).

Forrás: `docs/specs/picasa-kollazs-felulet.md` **7.** — a `format_menu`
ugyanazt a listaépítőt használja, mint a szerkesztő vágóeszköze
(`0x007cc990`), és mind a tizenhét számpár a kódból van kiolvasva
(bizonyítottsági fok: **megerősített**).

Két dolog, amit könnyű elrontani:

1. **A táblázat arányai HOSSZÚ : RÖVID alakban állnak** („10 x 15" →
   15 : 10), nem magasság : szélesség alakban. Melyik lesz a magasság, azt
   a **tájolás** dönti el — ezért kap a `page_ratio()` külön `orientation`
   paramétert. Aki a nyers számpárt teszi a lap magasság/szélesség
   arányába, minden fekvő lapot állóra fordít.
2. **Két A4 van, más kulccsal**: az `A4` és a kollázs saját
   `A4PageCollage` („A4-es méretű papír") tétele — ugyanaz az arány, két
   menüsor (`0x007cd488` és `0x007cdba4`).

A listában két **dinamikus** tétel van (`long is None`): a `Manual` a
jelenlegi arányt tartja meg, a `CurrentDisplay` a képernyőét veszi át.
"""

from __future__ import annotations

from typing import NamedTuple

#: A tájolás két megengedett értéke (a `.cxf` `ORIENTATIONS`-ével egyezik).
ORIENTATIONS = ("landscape", "portrait")


class PageFormat(NamedTuple):
    """Egy oldalformátum a menüből.

    `long` / `short` a lap **hosszabb és rövidebb** oldala, tetszőleges
    mértékegységben — csak az arányuk számít. Dinamikus tételnél (`Manual`,
    `CurrentDisplay`) mindkettő `None`.
    """

    key: str
    label: str
    description: str
    long: float | None
    short: float | None


#: A menü tételei a felületi SORRENDBEN. A két csoportcím
#: (`CustomAspectRatios`, `AddCustomAspectRatio`) kimarad: azok nem
#: formátumok, hanem a menü szerkezetéhez tartoznak (a QML dolga).
PAGE_FORMATS: tuple[PageFormat, ...] = (
    PageFormat("Manual", "Manual", "", None, None),
    PageFormat("5x8m", "5 x 8", "", 8, 5),
    PageFormat("9x13m", "9 x 13", "Small print", 13, 9),
    PageFormat("10x15m", "10 x 15", "Large print", 15, 10),
    PageFormat("Crop13x18m", "13 x 18", "", 18, 13),
    PageFormat("Crop20x25m", "20 x 25", "", 25, 20),
    PageFormat("A4", "A4", "Full page", 297, 210),
    PageFormat("4x6", "4 x 6", "Small print", 6, 4),
    PageFormat("5x7", "5 x 7", "Large print", 7, 5),
    PageFormat("FullPage", "8.5 x 11", "Letter paper", 22, 17),
    PageFormat("8x10", "8 x 10", "", 10, 8),
    PageFormat("A4PageCollage", "A4 paper", "", 297, 210),
    PageFormat("Square", "Square", "CD Cover", 1, 1),
    PageFormat("Desktop4x3", "4:3", "Standard screen", 4, 3),
    PageFormat("Widescreen", "16:10", "Widescreen monitor", 16, 10),
    PageFormat("HDTV16x9", "16:9", "HDTV", 16, 9),
    PageFormat("WideFrame", "5:3", "Widescreen Photo Frame", 5, 3),
    PageFormat("CurrentDisplay", "Current display", "", None, None),
)

_BY_KEY = {fmt.key: fmt for fmt in PAGE_FORMATS}

#: Az alapértelmezett formátum. A `picasa-create-features.md` 1.9.11 szerint
#: a `collage::format` alapértelmezése **4:3** — a `picasa-kollazs-felulet.md`
#: 10. szakaszának `2`-es nyers értéke ugyanennek a mentett alakja.
DEFAULT_FORMAT_KEY = "Desktop4x3"

#: A képernyő aránya (magasság / szélesség), ha nem sikerül lekérdezni.
FALLBACK_SCREEN_RATIO = 9 / 16


def format_for(key: str) -> PageFormat:
    """A kulcshoz tartozó formátum; ismeretlen kulcs = hiba (nem néma
    alapértelmezés — a `.cxf`-be írt rossz formátum észrevétlen maradna)."""
    try:
        return _BY_KEY[key]
    except KeyError:
        raise ValueError(f"Ismeretlen oldalformátum: {key!r}") from None


def format_text(key: str) -> str:
    """A `.cxf` `format` attribútuma: a formátum NEVE, `hosszú:rövid` alakban.

    A tulajdonos 11 valódi kollázsán mérve (#1089): az A4 neve `297:210` —
    **milliméterben** —, holott a képpontaránya `256:181`. A kettőnek nincs
    köze egymáshoz azon túl, hogy közelítik egymást. Aki a képpontméretből
    számol, 11-ből 6-ot elront.

    ⚠️ **Nem hozzuk legegyszerűbb alakra.** A `15:10` a `10 x 15`-ös papír
    neve, nem egy törtszám: a `gcd`-osztás `3:2`-t adna, amit az eredeti
    soha nem ír le. Ugyanez rontaná el a `297:210`-et is (`99:70`).

    A név **nem forog a tájolással** — az álló A4 is `297:210`, a tájolást
    a `.cxf` külön mezője mondja meg.

    A két DINAMIKUS tételnek (`Manual`, `CurrentDisplay`) nincs neve: ott a
    lap tényleges arányából számolunk. Hogy az eredeti pontosan mit ír
    ezekhez, nincs mintánk — a formátum-menü 18 tételéből ez a kettő
    maradt mérés nélkül."""
    fmt = format_for(key)
    if fmt.long is None or fmt.short is None:
        raise ValueError(
            f"A(z) {key!r} dinamikus formátumnak nincs neve; "
            "használd az arányból számoló ágat."
        )
    return f"{_szam(fmt.long)}:{_szam(fmt.short)}"


def _szam(ertek: float) -> str:
    """`297.0` → `297`; a nevekben nincs tizedespont."""
    egesz = int(ertek)
    return str(egesz) if float(egesz) == float(ertek) else str(ertek)


def is_known_format(key: str) -> bool:
    """Szerepel-e a kulcs a menüben — a felületi bemenet szűrésére."""
    return key in _BY_KEY


def page_ratio(
    key: str,
    orientation: str,
    *,
    screen_ratio: float = FALLBACK_SCREEN_RATIO,
    current_ratio: float = 1.0,
) -> float:
    """A lap **magasság / szélesség** aránya — ebből él a lap alakja (8.1).

    `screen_ratio` a „Jelenlegi megjelenítés" tételhez, `current_ratio` a
    `Manual`-hoz kell (az a jelenlegi arányt tartja meg).
    """
    if orientation not in ORIENTATIONS:
        raise ValueError(
            f"Ismeretlen tájolás: {orientation!r} (várt: {ORIENTATIONS})"
        )
    fmt = format_for(key)
    if fmt.key == "CurrentDisplay":
        # a képernyő arányát a tájolás NEM forgatja: ez maga a képernyő
        return float(screen_ratio)
    if fmt.long is None or fmt.short is None:
        return float(current_ratio)
    if orientation == "landscape":
        return float(fmt.short) / float(fmt.long)
    return float(fmt.long) / float(fmt.short)


__all__ = [
    "DEFAULT_FORMAT_KEY",
    "FALLBACK_SCREEN_RATIO",
    "format_text",
    "ORIENTATIONS",
    "PAGE_FORMATS",
    "PageFormat",
    "format_for",
    "is_known_format",
    "page_ratio",
]

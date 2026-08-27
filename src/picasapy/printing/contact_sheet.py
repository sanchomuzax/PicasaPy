"""Indexkép-nyomtatás geometriája (#1590) — Qt-független, determinisztikus.

A `picasapy.app.print_controller.PrintController` ezt hívja: az oldal
nyomtatható területéből (`PageGeometry`) és a képek számából kiszámolja,
hány lap kell, hol a fejléc, és hol állnak a bélyegképek.

## Mit mondott meg a mérés, és mit nem

Az eredetiben az indexkép **nyomtatási méret**, nem külön párbeszéd: a
`ytPrintSizes::eContact` a többi papírméret (4x6, 5x7, Tárcaméret,
FullPage…) mellett áll, a `ytPrintTip::eContact` szövege pedig „Képek
nyomtatása indexképként". A lap fejléce **saját**, nem a kollázsé: a
nyomtató a `ytPrinter::contactsheetalbum` („Album:") és a
`ytPrinter::contactsheetdate` („Dátum:") CÍMKÉZETT mezőket rajzolja, míg
az indexkép-KOLLÁZS fejléce a `CContactSheetTheme::subtitle_format`
(„%1$d kép, %2$s") mintát követi. A #1590 jegy „ugyanaz az elrendezés,
mint a kollázsé" előírása tehát a FEJLÉC-re nézve MEGDŐLT; a **rácsra**
viszont áll, ezért a cellákat a kollázs `contact_sheet_layout`-ja adja —
nem írunk másodszor rácsszámolót.

**Amit a mérés NEM adott meg:** az oszlopszámot és a soronkénti
lapszámot. Az eredeti nyomtatási előnézetéből ezek nem olvashatók ki, és
a `stringres`-ben sincs rájuk kulcs. Ezért **DÖNTÉS** (nem lelet): az
oszlopszám a felhasználóé (alapértéke `DEFAULT_COLUMNS`), a sorok száma
pedig a lap alakjából adódik úgy, hogy a cellák a lehető
legnégyzetesebbek legyenek — így a portré és a fekvő lap egyaránt
kihasznált marad.
"""

from __future__ import annotations

from dataclasses import dataclass

from picasapy.collage.layout import Placement, contact_sheet_layout

from .layout import PageGeometry

#: Az oszlopok alapértelmezett száma. A `collage.layout.contact_sheet_layout`
#: is ezt használja alapértéknek — egy helyen dől el, mi a „szokásos" rács.
DEFAULT_COLUMNS = 4

#: A fejléc a nyomtatható magasság ekkora hányadát kapja. Az indexkép-
#: KOLLÁZS 15 %-ot ad neki (`CONTACT_SHEET_HEADER_RATIO`); a nyomtatott lap
#: fejléce két rövid, címkézett sor („Album:", „Dátum:"), ezért kevesebb is
#: elég — a maradék a bélyegképeké. DÖNTÉS, nem mérés.
HEADER_RATIO = 0.08

#: A cellák közötti (és a szélső) hézag a nyomtatható szélesség hányadában.
SPACING_RATIO = 0.012


@dataclass(frozen=True)
class ContactSheetPage:
    """Egy nyomtatott indexkép-lap.

    A `first` és a `count` a nyomtatandó képek listájába mutat; a
    `placements` a lap bal felső sarkától mért rajzolási téglalapok
    (ugyanabban a mértékegységben, mint a `PageGeometry`).
    """

    first: int
    count: int
    placements: tuple[Placement, ...]

    def __post_init__(self) -> None:
        if self.count != len(self.placements):
            raise ValueError(
                f"{self.count} kép, de {len(self.placements)} hely a lapon"
            )


def rows_per_page(page: PageGeometry, columns: int) -> int:
    """Hány sor fér egy lapra a megadott oszlopszám mellett.

    A cél a lehető legnégyzetesebb cella: a rács oldalaránya kövesse a
    bélyegképeknek maradó területét. Legalább egy sor mindig van.
    """
    if columns < 1:
        raise ValueError(f"Érvénytelen oszlopszám: {columns}")
    body_height = page.printable_height * (1.0 - HEADER_RATIO)
    if body_height <= 0:
        raise ValueError("A fejléc nem hagyott helyet a bélyegképeknek.")
    aranyos = columns * body_height / page.printable_width
    return max(1, int(round(aranyos)))


def header_rect(page: PageGeometry) -> tuple[float, float, float, float]:
    """A fejléc téglalapja (x, y, szélesség, magasság) a lap sarkától."""
    return (
        page.margin,
        page.margin,
        page.printable_width,
        page.printable_height * HEADER_RATIO,
    )


def sheet_pages(
    count: int, page: PageGeometry, columns: int = DEFAULT_COLUMNS
) -> tuple[ContactSheetPage, ...]:
    """A képek lapokra osztva, laponként azonos cellamérettel.

    ⚠️ A cellaméret SZÁNDÉKOSAN a TELEjéből számolódik (`per_page` kép),
    még a részben teli utolsó lapon is: különben az utolsó lap néhány képe
    óriásira nőne, és a lapok nem lennének összehasonlíthatók — pontosan
    ezt várja az ember egy indexképtől.
    """
    if count < 1:
        raise ValueError("Indexkép-nyomtatáshoz legalább egy kép kell.")
    if columns < 1:
        raise ValueError(f"Érvénytelen oszlopszám: {columns}")
    sorok = rows_per_page(page, columns)
    per_page = sorok * columns

    fejlec_magassag = page.printable_height * HEADER_RATIO
    body_x = page.margin
    body_y = page.margin + fejlec_magassag
    body_w = int(page.printable_width)
    body_h = int(page.printable_height - fejlec_magassag)
    spacing = max(1, int(page.printable_width * SPACING_RATIO))

    # a rács a KOLLÁZS indexkép-elrendezéséből jön (#1590: ne írjunk
    # másodszor rácsszámolót); a teli lapra kérjük, és a részben teli
    # lapon az első `n` cellát használjuk
    teli = contact_sheet_layout(per_page, body_w, body_h, columns, spacing)

    lapok: list[ContactSheetPage] = []
    for first in range(0, count, per_page):
        ezen = min(per_page, count - first)
        lapok.append(
            ContactSheetPage(
                first=first,
                count=ezen,
                placements=tuple(
                    Placement(
                        x=int(body_x) + cell.x,
                        y=int(body_y) + cell.y,
                        width=cell.width,
                        height=cell.height,
                        fill=False,
                    )
                    for cell in teli[:ezen]
                ),
            )
        )
    return tuple(lapok)


__all__ = [
    "DEFAULT_COLUMNS",
    "HEADER_RATIO",
    "SPACING_RATIO",
    "ContactSheetPage",
    "header_rect",
    "rows_per_page",
    "sheet_pages",
]

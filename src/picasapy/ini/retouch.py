"""A `retouch` filters-lánc-bejegyzés régió-adatai (#148).

**FONTOS, ŐSZINTE ÁLLAPOT:** a valódi Picasa `retouch` régió-adatformátuma
NINCS dekódolva — a `docs/specs/filters-decoded.md` „Nyitva” listája
(5. pont) ezt kifejezetten nyitott kérdésként jelöli, és a kutatás során
(#148) sem került elő valódi `.picasa.ini`-minta retusált régió-adattal (a
`research/testdata` alatt egyetlen retouch/redeye golden sem található). A
Picasa3.exe string-táblájában a `retouch=1;` kizárólag PARAMÉTER NÉLKÜLI
jelzőként fordul elő (`docs/specs/picasa-exe-strings.md`) — ez összhangban
van azzal a lehetséggel, hogy a valódi Picasa a retusálást (a redeye-hoz
hasonlóan) rögtön a képpontokba „süti", és a `retouch=1;` csak történeti
jelző, régió-visszajátszás nélkül.

Emiatt ez a modul egy **PicasaPy-saját, dokumentált kiterjesztést** definiál:
`retouch=1,<rect64>[,<rect64>...];` — minden további rect64 paraméter egy-egy
retusálandó régió, a `crop64`/redeye-régiók mintájára (relatív [0..1]
koordináták, ld. `picasapy.ini.rect64`). Ez a formátum:

- **VISSZAFELÉ KOMPATIBILIS**: egy valódi Picasa-exportból származó puszta
  `retouch=1;` (régió nélkül) ezen a modulon keresztül is hiba nélkül
  értelmezhető — `parse_retouch_regions` ilyenkor üres tuple-t ad, a
  renderelés no-op (nem tudjuk, HOL kellene retusálni).
- **NEM garantáltan egyezik** azzal, amit egy valódi Picasa írna, ha ugyanazt
  a képet szerkesztenék — ha egyszer előkerül egy valódi golden-minta
  retusált régióval, ezt a formátumot validálni/cserélni kell (ld. jelentés).
"""

from __future__ import annotations

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import Rect64, decode_rect64, encode_rect64

RETOUCH_FILTER_NAME = "retouch"


def parse_retouch_regions(op: FilterOp) -> tuple[Rect64, ...]:
    """A `retouch` FilterOp régióinak dekódolása.

    A `params[0]` az engedélyező `1` flag; az esetleges további paraméterek
    rect64-ként dekódolandók. Érvénytelen rect64-nél `ValueError` — a hívó
    (`render.chain`) felelőssége, hogy a #301-elv szerint a teljes bejegyzést
    kihagyja, ne a teljes láncot dobja el.
    """
    if not op.matches(RETOUCH_FILTER_NAME):
        raise ValueError(f"Nem retouch bejegyzés: {op.name!r}")
    return tuple(decode_rect64(param) for param in op.params[1:])


def build_retouch_op(regions: tuple[Rect64, ...]) -> FilterOp:
    """`FilterOp` építése retusálási régiókból (íráshoz)."""
    params = ("1", *(encode_rect64(rect) for rect in regions))
    return FilterOp(RETOUCH_FILTER_NAME, params)

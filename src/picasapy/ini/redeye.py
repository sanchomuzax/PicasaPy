"""Vörösszem-régiók a `filters=` láncban (#445) — PicasaPy-SAJÁT kiterjesztés.

Az eredeti Picasa `redeye=1;` alakot ír: hogy a kézzel megjelölt szemek
koordinátái nála milyen bájtformában élnek, **nem derült ki** a binárisból
(nincs `redeye64(`-szerű formátum-string) — ez a #371 nyitott kérdése.

Amit viszont a bináris kimondott (#445): a vörösszem-eszköz
**automatikus ÉS kézi** — az automatika lefut, a felhasználó pedig utólag
pótolja, amit a gép kihagyott: *„You can also draw a square around any red
eye that Picasa may have missed."*

Ezért itt a `retouch=` v1 alakjának bevált mintáját követjük (ld.
`picasapy.ini.retouch`): `redeye=1[,rect64(...)…]` — az első paraméter az
engedélyező `1` flag, a továbbiak a kézzel megjelölt szemek téglalapjai
`rect64`-ben. Paraméter nélkül a bejegyzés bájtra ugyanaz, mint a valódi
Picasáé (`redeye=1;`), tehát a kétirányú kompatibilitás sértetlen: ha a
felhasználó nem jelöl kézzel semmit, a Picasa a sajátjaként olvassa vissza.
"""

from __future__ import annotations

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import Rect64, decode_rect64, encode_rect64

REDEYE_FILTER_NAME = "redeye"


def parse_redeye_regions(op: FilterOp) -> tuple[Rect64, ...]:
    """A kézzel megjelölt szemek téglalapjai (paraméter nélkül üres tuple).

    Érvénytelen `rect64`-nél `ValueError` — a hívó (`render.chain`) a
    #301-elv szerint az EGÉSZ bejegyzést hagyja ki, nem a teljes láncot.
    """
    if not op.matches(REDEYE_FILTER_NAME):
        raise ValueError(f"Nem redeye bejegyzés: {op.name!r}")
    return tuple(decode_rect64(param) for param in op.params[1:])


def build_redeye_op(regions: tuple[Rect64, ...]) -> FilterOp:
    """`FilterOp` a vörösszem-bejegyzéshez.

    Régió NÉLKÜL a bejegyzés `redeye=1` — bájtra a valódi Picasa alakja.
    """
    return FilterOp(
        REDEYE_FILTER_NAME, ("1", *(encode_rect64(r) for r in regions))
    )

"""A `retouch` filters-lánc-bejegyzés régió-/folt-adatai (#148, #445).

**FONTOS, ŐSZINTE ÁLLAPOT:** a valódi Picasa `retouch` régió-adatformátuma
NINCS dekódolva — a `docs/specs/filters-decoded.md` „Nyitva” listája
(5. pont) ezt kifejezetten nyitott kérdésként jelöli, és a kutatás során
(#148, #445, #371) sem került elő valódi `.picasa.ini`-minta retusált
régió-adattal (a `research/testdata` alatt egyetlen retouch/redeye golden
sem található). A Picasa3.exe string-táblájában a `retouch=1;` kizárólag
PARAMÉTER NÉLKÜLI jelzőként fordul elő (`docs/specs/picasa-exe-strings.md`)
— ez összhangban van azzal a lehetőséggel, hogy a valódi Picasa a
retusálást (a redeye-hoz hasonlóan) rögtön a képpontokba „süti", és a
`retouch=1;` csak történeti jelző, adat-visszajátszás nélkül.

Emiatt ez a modul **KÉT, EGYMÁS UTÁN SZÜLETETT, PicasaPy-saját, dokumentált
kiterjesztést** definiál — a valódi Picasa bájtformátuma egyiknek sem ismert:

1. **v1 (`retouch=1,<rect64>[,<rect64>...];`, #148)** — az eredeti,
   téglalap-régiós kiterjesztés. **Csak OLVASÁSRA tartjuk meg** (a
   `parse_retouch_regions`/`build_retouch_op` páron át) — a szerkesztő UI
   már nem ír ilyet, de a korábban PicasaPy-jal mentett `.picasa.ini`-k
   hiba nélkül betölthetők maradnak vele.
2. **v2 (`retouch=2,<patch20hex>[,<patch20hex>...];`, #445)** — a jelenlegi
   szerkesztő UI ezt írja. A Picasa saját súgószövege (
   „Click to select the area to fix. Then, move the mouse to see a preview
   of the replacement area. Click on the image again to finalize.") szerint
   a retusálás **irányított klónozás**: a felhasználó egy CÉL-foltot jelöl
   ki, majd egy FORRÁS-pontot, ahonnan a kép a célra másolódik, kör alakú,
   állítható méretű ecsettel. Ezért egy folt (`RetouchPatch`) HÁROM adatot
   hordoz: cél-pont, forrás-pont, sugár (mindhárom relatív [0..1] egység,
   a sugár a kép rövidebb oldalára vonatkoztatva — ld.
   `picasapy.render.retouch.apply_retouch_patches`). A 20 hex jegyű kódolás
   a `rect64` mintáját követi (4×4 hex jegy koordinátánként), eggyel több
   mezővel (target_x, target_y, source_x, source_y, radius).

**VISSZAFELÉ KOMPATIBILITÁS (kötelező, #445):**

- egy valódi Picasa-eredetű, adat nélküli `retouch=1;` mindkét
  olvasó-függvényen (`parse_retouch_regions`/`parse_retouch_patches`) át
  hiba nélkül üres tuple-t ad — egyik sem tudja (és nem is próbálja),
  HOL kellene retusálni;
- egy korábbi PicasaPy-verzió által írt `retouch=1,<rect64>...;` a
  `parse_retouch_regions`-szal továbbra is hiba nélkül olvasható (a
  `parse_retouch_patches` ilyenkor üres tuple-t ad, mert a verzió-jelző
  nem `2`);
- egy jelenlegi PicasaPy által írt `retouch=2,<patch>...;` a
  `parse_retouch_patches`-szal olvasható (a `parse_retouch_regions`
  ilyenkor üres tuple-t ad, mert a verzió-jelző nem `1`).

**NEM garantáltan egyezik** azzal, amit egy valódi Picasa írna, ha ugyanazt
a képet szerkesztenék — ha egyszer előkerül egy valódi golden-minta
retusált régióval/folttal, ezt a formátumot validálni/cserélni kell (ld.
jelentés).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import Rect64, decode_rect64, encode_rect64

RETOUCH_FILTER_NAME = "retouch"

_LEGACY_VERSION = "1"
_PATCH_VERSION = "2"

_PATCH_SCALE = 65536
_PATCH_HEX = re.compile(r"^[0-9a-fA-F]{1,20}$")


@dataclass(frozen=True)
class RetouchPatch(object):
    """Egyetlen retusálási folt (#445): cél-pont, forrás-pont, sugár —
    mindhárom relatív [0..1] egység (a sugár a kép rövidebb oldalára
    vonatkoztatva, ld. modul-docsztring)."""

    target_x: float
    target_y: float
    source_x: float
    source_y: float
    radius: float


def decode_patch(value: str) -> RetouchPatch:
    """20 hex jegyű `RetouchPatch`-kódolás dekódolása (a `rect64` mintája,
    eggyel több mezővel: target_x, target_y, source_x, source_y, radius)."""
    inner = value.strip()
    if not _PATCH_HEX.match(inner):
        raise ValueError(f"Érvénytelen retouch-patch érték: {value!r}")
    padded = inner.zfill(20)
    target_x, target_y, source_x, source_y, radius = (
        int(padded[i : i + 4], 16) / _PATCH_SCALE for i in range(0, 20, 4)
    )
    return RetouchPatch(
        target_x=target_x,
        target_y=target_y,
        source_x=source_x,
        source_y=source_y,
        radius=radius,
    )


def encode_patch(patch: RetouchPatch) -> str:
    """20 hex jegyű érték, vezető nullákkal — bitre pontos visszaírhatóság."""
    coords = (
        patch.target_x,
        patch.target_y,
        patch.source_x,
        patch.source_y,
        patch.radius,
    )
    for coord in coords:
        if not 0.0 <= coord <= 1.0:
            raise ValueError(f"retouch-patch koordináta a [0..1] tartományon kívül: {coord}")
    return "".join(f"{min(round(c * _PATCH_SCALE), _PATCH_SCALE - 1):04x}" for c in coords)


def parse_retouch_regions(op: FilterOp) -> tuple[Rect64, ...]:
    """A `retouch` FilterOp v1 (téglalap-régiós, #148) régióinak dekódolása.

    Csak visszamenőleges olvasáshoz (ld. modul-docsztring) — a `params[0]`
    az engedélyező `1` flag; az esetleges további paraméterek rect64-ként
    dekódolandók. Ha a bejegyzés v2 (patch-alapú, `params[0] == "2"`), üres
    tuple-t ad — nem ez a formátum illik rá.

    Érvénytelen rect64-nél `ValueError` — a hívó (`render.chain`) felelőssége,
    hogy a #301-elv szerint a teljes bejegyzést kihagyja, ne a teljes láncot
    dobja el.
    """
    if not op.matches(RETOUCH_FILTER_NAME):
        raise ValueError(f"Nem retouch bejegyzés: {op.name!r}")
    if op.params and op.params[0] == _PATCH_VERSION:
        return ()
    return tuple(decode_rect64(param) for param in op.params[1:])


def build_retouch_op(regions: tuple[Rect64, ...]) -> FilterOp:
    """`FilterOp` építése v1 (téglalap-régiós) retusálási régiókból.

    Csak visszamenőleges kompatibilitási tesztekhez/olvasáshoz maradt meg —
    a szerkesztő UI a `build_retouch_patches_op`-ot használja (#445)."""
    params = (_LEGACY_VERSION, *(encode_rect64(rect) for rect in regions))
    return FilterOp(RETOUCH_FILTER_NAME, params)


def parse_retouch_patches(op: FilterOp) -> tuple[RetouchPatch, ...]:
    """A `retouch` FilterOp v2 (folt-alapú, #445) foltjainak dekódolása.

    A `params[0]` a verzió-jelző (`"2"`); ha hiányzik vagy más (pl. a v1
    `"1"` vagy egy valódi Picasa puszta `retouch=1;`-je), üres tuple-t ad —
    nem ez a formátum illik rá.

    Érvénytelen patch-kódolásnál `ValueError` — a hívó felelőssége a
    #301-elv szerinti, bejegyzés-szintű hibatűrés.
    """
    if not op.matches(RETOUCH_FILTER_NAME):
        raise ValueError(f"Nem retouch bejegyzés: {op.name!r}")
    if not op.params or op.params[0] != _PATCH_VERSION:
        return ()
    return tuple(decode_patch(param) for param in op.params[1:])


def build_retouch_patches_op(patches: tuple[RetouchPatch, ...]) -> FilterOp:
    """`FilterOp` építése v2 (folt-alapú, #445) retusálási foltokból."""
    params = (_PATCH_VERSION, *(encode_patch(patch) for patch in patches))
    return FilterOp(RETOUCH_FILTER_NAME, params)

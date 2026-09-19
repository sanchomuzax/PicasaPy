"""Objektívnév feloldása azonosítóból — a MÉRT Picasa-táblákkal (#3121).

A nyers (RAW) fájlok és a tükörreflexes gépek JPEG-jei az objektívet
**azonosítóként** tárolják a MakerNote-ban, nem emberi névként. Az eredeti
Picasa két beépített táblából oldotta fel, és **két külön kulccsal**:

| gyártó | tábla (VA) | rekord | kulcs |
|---|---|---|---|
| Canon | `0x00c79c98` | 230 × 24 bájt | `LensType` + gyújtó/rekesz négyes |
| Nikon | `0x00c7b230` | 416 × 12 bájt | a 8 bájtos `LensID` |

A mérés — a táblák határai, a rekordkiosztás, a keresés utasításonként és az
elosztó — a `docs/specs/picasa-metaadat-tulajdonsagok.md` **9. szakaszában**
áll. A táblák tartalma az `objektiv_tabla.json`-ban, a binárisból KINYERVE
(az eszköz a privát agent-repóban: `eszkozok/meres/objektiv_tabla_kinyer.py`).

## Két részlet, ami a mérésből jön, és nem „józan ész"

1. **A Canon `LensType` ismétlődhet** — egy azonosító több objektívet takar.
   Ilyenkor a gyújtótávolság/rekesz **négyes** választ a jelöltek közül.
2. **A float-egyezés 8 ULP tűréssel megy**: az eredeti a két `float`
   BITMINTÁJÁT vonja ki egészként, és az abszolút különbséget hasonlítja
   8-hoz. Ezért a `35.0`-hoz az EXIF-ből jövő `34.999996` MÉG találat, a
   kilencedik ULP viszont már nem.

⚠️ Amit ez a modul NEM tud: hogy a `LensType`/`LensID` a MakerNote melyik
bájtjain áll. A feloldás kulcs → név; a kulcs KIOLVASÁSA a MakerNote-ból a
#3121 következő lépése, és mintafájl kell hozzá.
"""

from __future__ import annotations

import json
import struct
from functools import lru_cache
from pathlib import Path

TABLA_UT = Path(__file__).with_name("objektiv_tabla.json")

#: A MÉRT tűrés: a két float bitmintájának egész különbsége ennél kisebb
#: legyen (`0x00a35bd5`: `cmp eax, 8` / `jae <következő>`).
ULP_TURES = 8

#: A `Make` mező előtagjai — a mért elosztó ez alapján választ ágat (9.9).
_CANON_ELOTAG = "canon"
_NIKON_ELOTAG = "nikon"


@lru_cache(maxsize=1)
def _tabla() -> dict:
    return json.loads(TABLA_UT.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _canon_index() -> dict[int, tuple[dict, ...]]:
    """`lens_type` → az azonosítón OSZTOZÓ rekordok."""
    index: dict[int, list[dict]] = {}
    for rekord in _tabla()["canon"]:
        index.setdefault(rekord["lens_type"], []).append(rekord)
    return {kulcs: tuple(ertek) for kulcs, ertek in index.items()}


@lru_cache(maxsize=1)
def _nikon_index() -> dict[str, str]:
    return {r["lens_id"].upper(): r["nev"] for r in _tabla()["nikon"]}


def _bitminta(ertek: float) -> int:
    (bit,) = struct.unpack("<I", struct.pack("<f", float(ertek)))
    return bit


def _egyezik(tabla_ertek: float, mert: float | None) -> bool:
    """A MÉRT összevetés: a bitminták egész különbsége < 8 ULP.

    A hiányzó (`None`) mért érték a `0.0`-val ér fel — a táblában is `0.0f`
    jelzi a fix gyújtótávolságot és az állandó rekeszt.
    """
    return abs(_bitminta(tabla_ertek) - _bitminta(0.0 if mert is None else mert)) \
        < ULP_TURES


def canon_objektiv(
    lens_type: int,
    gyujto_min: float | None = None,
    gyujto_max: float | None = None,
    rekesz_min: float | None = None,
    rekesz_max: float | None = None,
) -> str | None:
    """A Canon-ág: `LensType`, majd a négyes dönt az ütközésnél."""
    jeloltek = _canon_index().get(int(lens_type))
    if not jeloltek:
        return None
    for rekord in jeloltek:
        if (
            _egyezik(rekord["gyujto_min"], gyujto_min)
            and _egyezik(rekord["gyujto_max"], gyujto_max)
            and _egyezik(rekord["rekesz_min"], rekesz_min)
            and _egyezik(rekord["rekesz_max"], rekesz_max)
        ):
            return rekord["nev"]
    return None


def nikon_objektiv(lens_id: bytes | str) -> str | None:
    """A Nikon-ág: a 8 bájtos `LensID` közvetlen kulcs.

    `bytes` és hexadecimális sztring egyaránt mehet; más hosszúságnál
    `ValueError` — a csendes `None` elrejtené a hívó hibáját.
    """
    if isinstance(lens_id, str):
        hexa = lens_id.strip().replace(" ", "").upper()
    else:
        hexa = bytes(lens_id).hex().upper()
    if len(hexa) != 16:
        raise ValueError(
            f"a Nikon LensID 8 bájt (16 hexa jegy), ez {len(hexa) // 2} bájt")
    return _nikon_index().get(hexa)


def objektiv_neve(
    make: str | None,
    *,
    lens_type: int | None = None,
    lens_id: bytes | str | None = None,
    gyujto_min: float | None = None,
    gyujto_max: float | None = None,
    rekesz_min: float | None = None,
    rekesz_max: float | None = None,
) -> str | None:
    """Az elosztó: a gyártót a **Make** dönti el (a mért `FUN_00a35940`).

    Ismeretlen gyártónál vagy hiányzó kulcsnál `None` — nem tippelünk.
    """
    gyarto = (make or "").strip().lower()
    if gyarto.startswith(_CANON_ELOTAG):
        if lens_type is None:
            return None
        return canon_objektiv(
            lens_type, gyujto_min, gyujto_max, rekesz_min, rekesz_max)
    if gyarto.startswith(_NIKON_ELOTAG):
        if lens_id is None:
            return None
        return nikon_objektiv(lens_id)
    return None

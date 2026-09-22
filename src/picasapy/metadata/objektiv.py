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

## A Canon-ág teljes menete (9.12)

A `canon_leiras` a `MakerNote 0x0001` tömbből ugyanazt számolja, amit a
`FUN_00a35a60`: a négy számot, a tábla-keresést, és ha az nem ad nevet, a
`0x00a36650` **tartalék-leírását** (`35-105mm f/3.5-4.5`). A tömböt a
`makernote.py` olvassa ki.

⚠️ A Nikon-ág kulcsa (a `LensData` verziói és titkosítása) még nincs
kiolvasva — az a #3495; addig a Nikon-fájl „Lens"
sora változatlan.
"""

from __future__ import annotations

import json
import math
import struct
from functools import lru_cache
from pathlib import Path
from typing import Sequence

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


#: A méret-kapu: a tömb legalább ennyi elemű (`(elemszám·2 & ~1) > 0x36`,
#: `0x00a35a8c`; a `0x009f0fd0` a méretet elemszám·2 alakban adja vissza).
_CANON_MIN_ELEM = 28
#: `lea ecx,[edi-1] / cmp ecx,0xfffd / ja` — ezen kívül nincs tábla-keresés.
_CANON_LENS_TYPE_MAX = 0xFFFE


#: A legnagyobb véges float32; fölötte az x87 `fstp dword` végtelent ír.
_F32_MAX = 3.4028234663852886e38


def _f32(ertek: float) -> float:
    """Egyszeres pontosságra kerekítés — az eredeti `fstp dword` lépése.

    A tartományon kívüli érték (sérült fájl, pl. `e26 = 0xFFFF`) végtelen
    lesz, ahogy az x87-en is — a `struct` itt kivételt dobna.
    """
    if not abs(ertek) <= _F32_MAX:
        return math.copysign(math.inf, ertek)
    return struct.unpack("<f", struct.pack("<f", ertek))[0]


def _nem_nulla(ertek: float) -> bool:
    """A tartalék-leírás „van-e érték" próbája: ugyanaz a 8 ULP, 0.0 ellen.

    ⚠️ Eltérés: a nem véges számot (a túlcsorduló sérült érték) „nincs
    értéknek" vesszük — az eredeti CRT itt olvashatatlan szöveget írna ki.
    """
    return math.isfinite(ertek) and not _egyezik(0.0, ertek)


def canon_leiras(beallitasok: Sequence[int]) -> str | None:
    """A Canon-ág (`FUN_00a35a60`): név a táblából, vagy tartalék-leírás."""
    talalat = canon_talalat(beallitasok)
    return talalat[0] if talalat else None


def canon_talalat(beallitasok: Sequence[int]) -> tuple[str, bool] | None:
    """Mint a `canon_leiras`, de megmondja, TÁBLANÉV-e (`True`) vagy a
    tartalék-leírás (`False`) — a panel a kettőt másképp rangsorolja.

    `beallitasok` a `MakerNote 0x0001` (CameraSettings) tömbje. `None`, ha a
    tömb rövid, vagy ha a számokból semmi nem írható ki.
    """
    if len(beallitasok) < _CANON_MIN_ELEM:
        return None
    e = beallitasok
    gyujto_min = gyujto_max = rekesz_min = rekesz_max = 0.0
    if e[25]:
        if e[24]:
            gyujto_min = _f32(e[24] / e[25])
        if e[23] and e[23] != e[24]:
            gyujto_max = _f32(e[23] / e[25])
    if e[26]:
        rekesz_min = _f32(2.0 ** (e[26] / 64))
    if e[27] and e[27] != e[26]:
        rekesz_max = _f32(2.0 ** (e[27] / 64))
    if 1 <= e[22] <= _CANON_LENS_TYPE_MAX:
        nev = canon_objektiv(e[22], gyujto_min, gyujto_max, rekesz_min, rekesz_max)
        if nev:
            return nev, True
    leiras = _tartalek_leiras(gyujto_min, gyujto_max, rekesz_min, rekesz_max)
    return (leiras, False) if leiras else None


def _tartalek_leiras(
    gyujto_min: float, gyujto_max: float, rekesz_min: float, rekesz_max: float
) -> str:
    """A `0x00a36650` formázója: a gyújtó CSONKOLVA (`cvttsd2si`), a rekesz
    `%.2g`-vel; a két rész közé csak akkor kerül szóköz, ha az első nem üres."""
    szoveg = ""
    if _nem_nulla(gyujto_min):
        if _nem_nulla(gyujto_max):
            szoveg = "%d-%dmm" % (int(gyujto_min), int(gyujto_max))
        else:
            szoveg = "%dmm" % int(gyujto_min)
    if _nem_nulla(rekesz_min):
        if szoveg:
            szoveg += " "
        if _nem_nulla(rekesz_max):
            szoveg += "f/%.2g-%.2g" % (rekesz_min, rekesz_max)
        else:
            szoveg += "f/%.2g" % rekesz_min
    return szoveg

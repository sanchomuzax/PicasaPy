"""Objektívnév feloldása azonosítóból — a MÉRT Picasa-táblákkal (#3121).

A nyers (RAW) fájlok és a tükörreflexes gépek JPEG-jei az objektívet
**azonosítóként** tárolják a MakerNote-ban, nem emberi névként. Az eredeti
Picasa két beépített táblából oldotta fel, és **két külön kulccsal**:

| gyártó | tábla (VA) | rekord | kulcs |
|---|---|---|---|
| Canon | `0x00c79c98` | 230 × 24 bájt | `LensType` + gyújtó/rekesz négyes |
| Nikon | `0x00c7b228` | 417 × 12 bájt | a 8 bájtos `LensID` |

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

## A Nikon-ág teljes menete (9.13, #3495)

A `nikon_leiras` a `0x00a35d80` menetét követi: a `LensData` (`0x0098`)
verziója adja a 7 bájt eltolását és azt, hogy kell-e visszafejteni; a kulcs
ez a 7 bájt + a `LensType` (`0x0083`); a keresés az **első** találatnál áll
meg (a táblában 5 kulcs ismétlődik); találat nélkül ugyanaz a
`0x00a36650` tartalék-leírás jön, mint a Canon-ágon.

⛔ A 9.2 a Nikon-rekordot `{név, kulcs}`-nak olvasta; a helyes alak
`{kulcs, név}` a `0x00c7b228`-tól (9.13 A) — a tábla ennek megfelelően
újraépítve. A visszafejtés az exiftool Nikon-`Decrypt` eljárása; valódi
titkosított mintán nincs mérve (9.13 C).
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
    """Kulcs → név, az ELSŐ előfordulás nyer (`0x00a36347`: a ciklus az első
    találatnál kilép) — a sima dict-építés az utolsót tartaná meg."""
    index: dict[str, str] = {}
    for rekord in _tabla()["nikon"]:
        index.setdefault(rekord["lens_id"].upper(), rekord["nev"])
    return index


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


# -- a Nikon-ág (9.13) ---------------------------------------------------------

#: `LensData` verzió → (a 7 bájt eltolása, titkosított-e) — 9.13 B.
_NIKON_VERZIOK = {
    b"0100": (6, False),
    b"0101": (0x0B, False),
    b"0201": (0x0B, True),
    b"0202": (0x0B, True),
    b"0203": (0x0B, True),
    b"0204": (0x0C, True),
}
_NIKON_P_HOSSZ = 7
#: `0x00a3627a`–`0x00a36292`: ezen kívül nincs tábla-keresés, csak tartalék.
_NIKON_LENS_TYPE_MAX = 0xFFFE
#: A visszafejtés a 4. bájttól indul (`0x00a364f0`); a verzió nyílt.
_NIKON_TITKOS_KEZDET = 4
#: Sorozatszám nélkül a kulcs: D50-en 0x22, máshol 0x60 (`0x00a365b0`–`d2`).
_NIKON_D50_KULCS = 0x22
_NIKON_ALAP_KULCS = 0x60

#: A helyettesítő táblák (`0x00ce3c38`) — bájtra az exiftool `Nikon.pm`
#: `@xlat` tömbje (12.76).
_NIKON_XLAT = (
    bytes.fromhex(
        "c1bf6d0d59c5139d83616b4fc77f3d3d5359e3c7e92f95a7951fdf7f2b29c70d"
        "df07ef71893d133d3b13fb0d89c1651fb30d6b29e3fbefa36b477f9535a7474f"
        "c7f1599535112961f13db32b0d4389c19d9d8965f1e9dfbf3d7f5397e5e99517"
        "1d3d8bfbc7e367a707f171a753b52989e52ba71729e94fc5656d6bef0d89492f"
        "b34353651d49a3138959ef6bef651d0b5913e34f9db329432b071d95595947fb"
        "e5e961472f357f177fef7f959571d3a30b71a3ad0b3bb5fba3bf4f831dade92f"
        "7165a3e507353d0db5e9e5473b9def35a3bfb3df53d397534971073561712f43"
        "2f11df1797fb953b7f6bd325bfadc7c5c5b58bef2fd3076b25499525496d71c7"
    ),
    bytes.fromhex(
        "a7bcc9ad91df85e5d478d517467c294c4d03e925681186b3bdf76f6122a22634"
        "2abe1e4614689d4418c240f47e5f1bad0b94b667b40be1ea959c66dce75d6c05"
        "dad5df7aeff6db1f824cc06847a1bdee3950564adddfa5f8c6daca90ca01429d"
        "8b0c7343750594de24b38034e52cdc9b3fca3345d0db5ff552c321dae222726b"
        "3ed05ba8878c065d0fdd091993d0b9fc8b0f8460331c9b45f1f0a3943a127733"
        "4d4478283c9efd655716946bfb59d0c82236dbd2639843a1048786f7a626bbd6"
        "594dbf6a2eaa2befe678b64ee02fdc7cbe5719327e2ad0b8ba29003c527da849"
        "3b2deb2549faa3aa39a7c5a7501136fbc6674af5a512657eb0dfaf4eb3617f2f"
    ),
)


def nikon_visszafejt(lens_data: bytes, sorozat_kulcs: int, zarszamlalo: int) -> bytes:
    """A `0x00a364f0`: a 4. bájttól XOR-folyam, az exiftool `Decrypt`
    szerkezetével (a zárszámláló négy bájtja XOR-olva adja a 2. kulcsot)."""
    szamlalo_kulcs = 0
    for i in range(4):
        szamlalo_kulcs ^= (zarszamlalo >> (8 * i)) & 0xFF
    ci = _NIKON_XLAT[0][sorozat_kulcs & 0xFF]
    cj = _NIKON_XLAT[1][szamlalo_kulcs]
    ck = 0x60
    ki = bytearray(lens_data)
    for i in range(_NIKON_TITKOS_KEZDET, len(ki)):
        cj = (cj + ci * ck) & 0xFF
        ck = (ck + 1) & 0xFF
        ki[i] ^= cj
    return bytes(ki)


def _nikon_sorozat_kulcs(sorozatszam: str | None, modell: str | None) -> int:
    """A számjegyes sorozatszám maga a kulcs; különben a modell dönt.

    ⚠️ Az eredeti a gyártói szótár `0x74`/`0x78` eleméből veszi (9.13 C,
    a címkéjük nincs kiolvasva); itt az exiftool `SerialKey` eljárása megy a
    `0x001d` `SerialNumber` mezőn.
    """
    szoveg = (sorozatszam or "").strip()
    if szoveg.isdigit():
        return int(szoveg)
    modell_szo = (modell or "").strip().split()
    return _NIKON_D50_KULCS if modell_szo[-1:] == ["D50"] else _NIKON_ALAP_KULCS


def nikon_leiras(
    lens_data: bytes | None,
    lens_type: int | None,
    *,
    sorozatszam: str | None = None,
    zarszamlalo: int | None = None,
    modell: str | None = None,
) -> str | None:
    """A Nikon-ág (`0x00a35d80`): név a táblából, vagy tartalék-leírás."""
    talalat = nikon_talalat(
        lens_data, lens_type,
        sorozatszam=sorozatszam, zarszamlalo=zarszamlalo, modell=modell)
    return talalat[0] if talalat else None


def nikon_talalat(
    lens_data: bytes | None,
    lens_type: int | None,
    *,
    sorozatszam: str | None = None,
    zarszamlalo: int | None = None,
    modell: str | None = None,
) -> tuple[str, bool] | None:
    """Mint a `nikon_leiras`, de megmondja, TÁBLANÉV-e (`True`) vagy a
    tartalék-leírás (`False`).

    `None`, ha a `LensData` hiányzik, ismeretlen verziójú, vagy nem hosszabb,
    mint `eltolás + 7` (`0x00a361dd`–`e6`). ⚠️ Titkosított verziónál
    zárszámláló nélkül is `None` — az eredeti ilyenkor is visszafejtene, de a
    kulcs fele hiányzik, és a szemét kulcsból jövő név rosszabb a semminél.
    """
    if not lens_data:
        return None
    verzio = _NIKON_VERZIOK.get(bytes(lens_data[:4]))
    if verzio is None:
        return None
    eltolas, titkos = verzio
    if len(lens_data) <= eltolas + _NIKON_P_HOSSZ:
        return None
    if titkos:
        if zarszamlalo is None:
            return None
        lens_data = nikon_visszafejt(
            bytes(lens_data), _nikon_sorozat_kulcs(sorozatszam, modell),
            zarszamlalo)
    p = bytes(lens_data[eltolas:eltolas + _NIKON_P_HOSSZ])
    if lens_type is not None and 1 <= lens_type <= _NIKON_LENS_TYPE_MAX:
        nev = nikon_objektiv(p + bytes([lens_type & 0xFF]))
        if nev:
            return nev, True
    leiras = _tartalek_leiras(
        5 * _nikon_g(p[2]), 5 * _nikon_g(p[3]), _nikon_g(p[4]), _nikon_g(p[5]))
    return (leiras, False) if leiras else None


def _nikon_g(bajt: int) -> float:
    """`g(b) = 2^(b/24)` (`0x00cf3ef0` = 24,0; `0x00c7d9d0` = 2,0)."""
    return 2.0 ** (bajt / 24)

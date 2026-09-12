""".pmp oszlopfájl olvasása (#1) — a Picasa központi (PMP) adatbázisa nem
relációs: minden logikai tábla minden oszlopa külön `.pmp` fájl.

Formátum keresztvalidálva (Java `PMPDB.java` ↔ Python `pmpinfo.py`,
ld. `docs/reference-repos-audit.md`): 20 bájtos little-endian fejléc, utána
a nyers rekordok egymás után, szeparátor nélkül. Csak olvasás — a PicasaPy
a PMP-adatbázist sosem írja.

A fejléc típuskódja a FÁJLÉ; hogy az adott OSZLOPNAK mi a helyes típusa, azt
a `docs/specs/picasa-imagedata-rekord.md` 44 soros táblája mondja meg (a
Picasa 3.9 regisztráló hívásaiból, PR #2520). Az innen fontos kilenc oszlop
az `OSZLOP_TIPUSOK`-ban áll; a `read_pmp_column(..., oszlop=…)` ezt kéri
számon (#2521).
"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_MAGIC = 0x3FCCCCCD
_CONST_1332 = 0x1332
_CONST_2 = 0x00000002
_HEADER = struct.Struct("<IHHIHHI")

# A típuskódok a `Picasa3.exe` RTTI-jéből, NEM adatból következtetve (#2105):
# a PMP-oszlopok `CColumn<…>` sablonpéldányok, és a sablon harmadik
# paramétere `0x13320000 + típuskód` — a C++ típusnév pedig a sablonban áll.
#
#   0x00 ytString · 0x01 unsigned long · 0x02 double · 0x03 SIGNED char
#   0x04 unsigned __int64 · 0x05 unsigned short · 0x06 char const* · 0x07 INT
#
# ⚠️ A `0x03` és a `0x07` ELŐJELES (#2106). Korábban mindkettőt előjel nélkül
# olvastuk; a tulajdonos `imagedata_edit_width.pmp`-jében (0x07) szereplő
# `0xFFFFFFAA` emiatt 4 294 967 210-ként jött vissza −86 helyett.
TYPE_STRING = frozenset({0x0, 0x6})
TYPE_UINT32 = frozenset({0x1})
TYPE_INT32 = frozenset({0x7})
TYPE_DOUBLE = frozenset({0x2})
TYPE_INT8 = frozenset({0x3})
TYPE_UINT64 = frozenset({0x4})
TYPE_UINT16 = frozenset({0x5})


#: #2521 — az OSZLOP elvárt típuskódja, a Picasa 3.9 binárisából.
#:
#: A fejléc típusmezője a FÁJLÉ; azt eddig semmi nem vetette össze azzal,
#: hogy az adott oszlopnak MI a helyes típusa. Egy sérült vagy összekevert
#: `.pmp` így némán rossz értéket adott — a #2106 pontosan ilyen volt.
#:
#: A forrás nem az adat, hanem a REGISZTRÁLÓ hívás célcíme: a nyolc
#: `CColumn<…>` konstruktor RTTI-vel azonosítva, a sablon harmadik
#: paramétere `0x13320000 + típuskód`. Mind a 44 `imagedata`-oszlop
#: táblája: `docs/specs/picasa-imagedata-rekord.md` (PR #2520).
#:
#: ⚠️ A `star` értéke SZÁNDÉKOSAN `None`: a 3.9 ezt az oszlopot **nem
#: regisztrálja**, a csillagozást a `starlist.txt`-ből olvassa (#2335).
#: Nálunk az olvasása megmarad a régebbi adatbázisok miatt — de nincs
#: mihez mérni, tehát típus-elvárást sem támasztunk rá. Egy örökölt,
#: jogos fájlt elutasítani rosszabb volna, mint nem ellenőrizni.
OSZLOP_TIPUSOK: dict[str, int | None] = {
    "caption": 0x00,
    "rotate": 0x00,
    "filters": 0x00,
    "deferredregion": 0x00,
    "tags": 0x06,
    "crop64": 0x04,
    "lat": 0x02,
    "long": 0x02,
    #: #2336: a geotag jelzője. A típus MÉRVE a tulajdonos adatmappáján
    #: (`imagedata_geoview.pmp` fejléce: `0x00`, `ytString`); a tartalma egy
    #: KML `<LookAt>` blokk — az importáló csak azt nézi, üres-e.
    "geoview": 0x00,
    "star": None,  # örökölt, ld. fent
}


class PmpFormatError(ValueError):
    """Érvénytelen vagy sérült `.pmp` fejléc/rekord."""


@dataclass(frozen=True)
class PmpColumn:
    """Egy beolvasott oszlop: a mezőtípus + a rekordok sorrendhelyes tuple-je."""

    field_type: int
    values: tuple

    def __len__(self) -> int:
        return len(self.values)


def read_pmp_column(path: Path, oszlop: str | None = None) -> PmpColumn:
    """Egy `.pmp` fájl teljes beolvasása.

    `oszlop`: az oszlop NEVE (pl. `"lat"`). Megadva a fejléc típuskódját
    összevetjük az `OSZLOP_TIPUSOK` mért elvárásával (#2521), és eltérésnél
    beszédes hibát adunk. Enélkül — és a táblában nem szereplő névre — a
    viselkedés a korábbi: nincs miről mért állításunk, tehát nem utasítunk
    el semmit.

    Raises:
        PmpFormatError: Érvénytelen magic/konstans/mezőtípus-eltérés, az
            oszlop elvárt típusától való eltérés (#2521), vagy a
            rekordadatok csonkák/hiányosak a fejlécben jelzett
            rekordszámhoz képest.
    """
    data = Path(path).read_bytes()
    if len(data) < _HEADER.size:
        raise PmpFormatError(f"A fejléc túl rövid: {path}")
    magic, type1, const_a, const2, type1_repeat, const_b, count = _HEADER.unpack_from(
        data, 0
    )
    if magic != _MAGIC:
        raise PmpFormatError(f"Érvénytelen magic ({magic:#x}): {path}")
    if type1 != type1_repeat:
        raise PmpFormatError(
            f"A mezőtípus két bejegyzése nem egyezik ({type1:#x} != "
            f"{type1_repeat:#x}): {path}"
        )
    if const_a != _CONST_1332 or const_b != _CONST_1332:
        raise PmpFormatError(f"Váratlan konstans a fejlécben: {path}")
    if const2 != _CONST_2:
        raise PmpFormatError(f"Váratlan konstans a fejlécben: {path}")

    _ellenorizd_az_oszlop_tipusat(oszlop, type1, path)

    values = _read_records(data, _HEADER.size, type1, count, path)
    return PmpColumn(field_type=type1, values=tuple(values))


def _ellenorizd_az_oszlop_tipusat(
    oszlop: str | None, talalt: int, path: Path
) -> None:
    """A fejléc típuskódja egyezzen az OSZLOP mért típusával (#2521).

    Hallgat, ha nincs oszlopnév, ha az oszlop nem szerepel a táblában, vagy
    ha a bejegyzése `None` (örökölt oszlop — ld. `OSZLOP_TIPUSOK`).
    """
    if oszlop is None:
        return
    elvart = OSZLOP_TIPUSOK.get(oszlop)
    if elvart is None or elvart == talalt:
        return
    raise PmpFormatError(
        f"A(z) „{oszlop}” oszlop típusa nem a mért: elvárt "
        f"{elvart:#04x}, "
        f"a fájl fejlécében {talalt:#04x} áll ({path}). A hiteles típust a "
        f"Picasa 3.9 regisztráló hívása adja "
        f"(docs/specs/picasa-imagedata-rekord.md)."
    )


def _read_records(
    data: bytes, offset: int, field_type: int, count: int, path: Path
) -> list:
    if field_type in TYPE_STRING:
        return _read_strings(data, offset, count, path)
    fmt, size = _FIXED_WIDTH.get(field_type, (None, None))
    if fmt is None:
        raise PmpFormatError(f"Ismeretlen mezőtípus ({field_type:#x}): {path}")
    end = offset + size * count
    if end > len(data):
        raise PmpFormatError(f"Csonka rekordadat ({count} rekord): {path}")
    return list(struct.unpack_from(f"<{count}{fmt}", data, offset))


_FIXED_WIDTH: dict[int, tuple[str, int]] = {}
for _t in TYPE_UINT32:
    _FIXED_WIDTH[_t] = ("I", 4)
for _t in TYPE_INT32:
    _FIXED_WIDTH[_t] = ("i", 4)
for _t in TYPE_DOUBLE:
    _FIXED_WIDTH[_t] = ("d", 8)
for _t in TYPE_INT8:
    _FIXED_WIDTH[_t] = ("b", 1)
for _t in TYPE_UINT64:
    _FIXED_WIDTH[_t] = ("Q", 8)
for _t in TYPE_UINT16:
    _FIXED_WIDTH[_t] = ("H", 2)


def _read_strings(data: bytes, offset: int, count: int, path: Path) -> list[str]:
    values = []
    for _ in range(count):
        end = data.find(b"\x00", offset)
        if end == -1:
            raise PmpFormatError(f"Hiányzó string-lezáró (0x00): {path}")
        values.append(_decode(data[offset:end], path))
        offset = end + 1
    return values


def _decode(raw: bytes, path: Path) -> str:
    """UTF-8 dekódolás; nem-UTF-8 bájtoknál naplózott figyelmeztetéssel
    esik vissza `errors="replace"`-re — a hibás bájtok némán ne vesszenek
    el nyomtalanul."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning(
            "Nem UTF-8 érték a(z) %s fájlban — a nem dekódolható bájtok "
            "helyettesítő karakterrel (U+FFFD) kerülnek be: %r",
            path,
            raw,
        )
        return raw.decode("utf-8", errors="replace")

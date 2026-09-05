"""Közös teszt-segéd: szintetikus `.pmp` oszlopfájl és thumbindex bájtok
előállítása a keresztvalidált formátum szerint (docs/reference-repos-audit.md)."""

import struct

THUMB_INDEX_MAGIC = 0x40466666
_NO_PARENT = 0xFFFFFFFF

MAGIC = 0x3FCCCCCD
CONST_1332 = 0x1332
CONST_2 = 0x00000002

# A típusok az RTTI-ből (#2105); a 0x03 és a 0x07 ELŐJELES (#2106).
_FIXED_FORMAT = {
    0x1: "I",  # unsigned long
    0x7: "i",  # int — ELŐJELES
    0x2: "d",  # double
    0x3: "b",  # signed char — ELŐJELES
    0x4: "Q",  # unsigned __int64
    0x5: "H",  # unsigned short
}


def build_pmp_column(field_type: int, values) -> bytes:
    """A `read_pmp_column`-nal olvasható bájtsorozat: fejléc + rekordok."""
    values = list(values)
    header = struct.pack(
        "<IHHIHHI",
        MAGIC,
        field_type,
        CONST_1332,
        CONST_2,
        field_type,
        CONST_1332,
        len(values),
    )
    if field_type in (0x0, 0x6):
        body = b"".join(value.encode("utf-8") + b"\x00" for value in values)
    else:
        fmt = _FIXED_FORMAT[field_type]
        body = struct.pack(f"<{len(values)}{fmt}", *values)
    return header + body


#: A bejegyzés farkának ELSŐ ÖT mezője: `creation`, `modified` (FILETIME),
#: `size`, `kind`, `dirty` — a `thumbindex._FAROK` (`<QQIIBBI`) eleje. A
#: `valid` (1 bájt) és a `parent_index` (4 bájt) külön megy alább, hogy a
#: hívó a `valid`-ot közvetlenül állíthassa.
_FAROK_FEJ = struct.Struct("<QQIIB")


def build_thumb_index(entries) -> bytes:
    """A `read_thumb_index`-szel olvasható bájtsorozat.

    `entries`: (név, szülőindex) párok, vagy (név, szülőindex, kind, valid)
    négyesek. A szülőindex `None` = könyvtár (0xffffffff).

    ⚠️ **A `kind`/`valid` alapértéke NEM nulla** (#2404). Korábban a gyár 26
    nullát írt, tehát minden szintetikus bejegyzés `valid=0` és `kind=0`
    lett — ami a MÉRT szabály szerint azt jelenti, hogy „a név már teljes
    útvonal". A tesztek így olyan adaton futottak, ami a valóságban nem
    fordul elő, és a szülő-összefűzést egyáltalán nem gyakorolták volna.

    Az alapértékek ezért valósághűek: `valid = 1`, a `kind` pedig könyvtárnál
    `1`, fájlnál `2` (mérve a tulajdonos katalógusán). Aki a
    típus-viselkedést vizsgálja, a négyes alakkal írja felül.
    """
    entries = list(entries)
    blob = struct.pack("<II", THUMB_INDEX_MAGIC, len(entries))
    for entry in entries:
        if len(entry) == 2:
            name, parent = entry
            kind = 1 if parent is None else 2
            valid = 1
        else:
            name, parent, kind, valid = entry
        parent_index = _NO_PARENT if parent is None else parent
        blob += (
            name.encode("utf-8")
            + b"\x00"
            + _FAROK_FEJ.pack(0, 0, 0, kind, 0)
            + bytes([valid])
            + struct.pack("<I", parent_index)
        )
    return blob

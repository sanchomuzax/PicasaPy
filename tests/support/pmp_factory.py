"""Közös teszt-segéd: szintetikus `.pmp` oszlopfájl és thumbindex bájtok
előállítása a keresztvalidált formátum szerint (docs/reference-repos-audit.md)."""

import struct

THUMB_INDEX_MAGIC = 0x40466666
_NO_PARENT = 0xFFFFFFFF

MAGIC = 0x3FCCCCCD
CONST_1332 = 0x1332
CONST_2 = 0x00000002

_FIXED_FORMAT = {
    0x1: "I",  # uint32
    0x7: "I",
    0x2: "d",  # double
    0x3: "B",  # uint8
    0x4: "Q",  # uint64
    0x5: "H",  # uint16
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


def build_thumb_index(entries) -> bytes:
    """A `read_thumb_index`-szel olvasható bájtsorozat.

    `entries`: (név, szülőindex) párok; szülőindex None = könyvtár
    (0xffffffff). A 26 ismeretlen bájtot nullákkal töltjük."""
    entries = list(entries)
    blob = struct.pack("<II", THUMB_INDEX_MAGIC, len(entries))
    for name, parent in entries:
        parent_index = _NO_PARENT if parent is None else parent
        blob += (
            name.encode("utf-8")
            + b"\x00"
            + b"\x00" * 26
            + struct.pack("<I", parent_index)
        )
    return blob

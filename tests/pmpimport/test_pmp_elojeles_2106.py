"""#2106: a PMP `0x03` és `0x07` típus ELŐJELES — mi unsignedként olvastuk.

## A bizonyíték

A `Picasa3.exe` RTTI-jében a PMP-oszlopok `CColumn<…>` sablonpéldányok, és a
sablon harmadik paramétere `0x13320000 + típuskód` — a típusnév pedig a
sablonban áll:

| típuskód | sablonpéldány | a típus |
|---|---|---|
| `0x03` | `CColumn<signed_char,1,322043907>` | **előjeles** bájt |
| `0x07` | `CColumn<int,1,322043911>` | **előjeles** 32 bites |

## Miért nem elméleti

A tulajdonos valódi Picasa-adatbázisának `imagedata_edit_width.pmp` fájlja
(típus `0x07`) tartalmazza a `0xFFFFFFAA` bájtnégyest. Előjelesen ez **−86**;
a régi olvasónk **4 294 967 210**-et adott rá vissza.
"""

from __future__ import annotations

import struct

import pytest

from picasapy.pmpimport.pmp_column import read_pmp_column

MAGIC = 0x3FCCCCCD
CONST_1332 = 0x1332
CONST_2 = 0x00000002


def _pmp(tmp_path, field_type: int, body: bytes, count: int):
    fej = struct.pack(
        "<IHHIHHI", MAGIC, field_type, CONST_1332, CONST_2, field_type, CONST_1332, count
    )
    ut = tmp_path / f"oszlop_{field_type:#x}.pmp"
    ut.write_bytes(fej + body)
    return ut


class TestElojelesTipusok:
    def test_a_0x07_MERT_esete_minusz_86(self, tmp_path):
        """A tulajdonos `imagedata_edit_width.pmp`-jében szereplő bájtnégyes."""
        ut = _pmp(tmp_path, 0x7, b"\xaa\xff\xff\xff", 1)
        assert read_pmp_column(ut).values == (-86,)

    def test_a_0x07_pozitiv_ertekei_valtozatlanok(self, tmp_path):
        ut = _pmp(tmp_path, 0x7, struct.pack("<3i", 0, 1, 2_000_000_000), 3)
        assert read_pmp_column(ut).values == (0, 1, 2_000_000_000)

    def test_a_0x03_elojeles(self, tmp_path):
        """A korpuszunkban ma nincs rá eset — a TÍPUS attól még előjeles."""
        ut = _pmp(tmp_path, 0x3, bytes([0x00, 0x01, 0x7F, 0x80, 0xFF]), 5)
        assert read_pmp_column(ut).values == (0, 1, 127, -128, -1)

    @pytest.mark.parametrize(
        ("tipus", "csomag", "vart"),
        [
            (0x1, struct.pack("<I", 0xFFFFFFFF), 0xFFFFFFFF),  # unsigned long
            (0x4, struct.pack("<Q", 0xFFFFFFFFFFFFFFFF), 0xFFFFFFFFFFFFFFFF),  # u64
            (0x5, struct.pack("<H", 0xFFFF), 0xFFFF),  # unsigned short
        ],
    )
    def test_az_ELOJEL_NELKULI_tipusok_valtozatlanok(self, tmp_path, tipus, csomag, vart):
        """Ellenkező irányú őr: a javítás ne tegye előjelessé a többit."""
        ut = _pmp(tmp_path, tipus, csomag, 1)
        assert read_pmp_column(ut).values == (vart,)

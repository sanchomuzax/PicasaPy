"""Az üres forrásból épülő TIFF-blokk little-endian (II), mint a Picasáé (#4009).

A forrás MEGLÉVŐ blokkjának bájtsorrendje marad (MM marad MM, II marad II);
csak a `tiff=None` esetén épülő új blokk lesz II.
"""

from __future__ import annotations

import struct

import pytest

from picasapy.metadata import tiff_helyben as th

_DT = th.ascii_ertek("2020:01:02 03:04:05")


def _valtozasok():
    return [th.Valtozas("0th", 0x0132, _DT)]


def _ifd0(tiff: bytes, e: str) -> dict[int, tuple[int, int, bytes]]:
    off = struct.unpack_from(e + "I", tiff, 4)[0]
    n = struct.unpack_from(e + "H", tiff, off)[0]
    ki = {}
    for i in range(n):
        tag, tipus, darab = struct.unpack_from(e + "HHI", tiff, off + 2 + 12 * i)
        ki[tag] = (tipus, darab, tiff[off + 10 + 12 * i : off + 14 + 12 * i])
    return ki


def test_ures_forras_ii_blokkot_ad():
    ki = th.frissitett_tiff(None, _valtozasok())
    assert ki[:4] == b"II*\x00"
    tagek = _ifd0(ki, "<")
    assert set(tagek) == {0x0132}
    off = struct.unpack("<I", tagek[0x0132][2])[0]
    assert ki[off : off + 20] == b"2020:01:02 03:04:05\x00"


def test_az_ures_alap_maga_is_ii():
    assert th._URES_TIFF[:4] == b"II*\x00"
    assert th.frissitett_tiff(None, [])[:2] == b"II"


@pytest.mark.parametrize("e,fej", [("<", b"II*\x00"), (">", b"MM\x00*")])
def test_a_meglevo_blokk_bajtsorrendje_marad(e, fej):
    forras = fej + struct.pack(e + "I", 8) + struct.pack(e + "H", 0) + b"\x00" * 4
    ki = th.frissitett_tiff(forras, _valtozasok())
    assert ki[:4] == fej
    assert 0x0132 in _ifd0(ki, e)


@pytest.mark.parametrize("e,fej", [("<", b"II*\x00"), (">", b"MM\x00*")])
def test_a_celkorlat_mindket_sorrendre(e, fej):
    # a meglévő 0x0132 (20 bájt) mutatója a blokkon KÍVÜLRE esik: nem írható a helyén
    forras = fej + struct.pack(e + "I", 8) + struct.pack(e + "H", 1)
    forras += struct.pack(e + "HHII", 0x0132, 2, 20, 9999) + b"\x00" * 4
    ki = th.frissitett_tiff(forras, _valtozasok())
    assert len(ki) < 200 and ki[:4] == fej
    tipus, darab, mezo = _ifd0(ki, e)[0x0132]
    off = struct.unpack(e + "I", mezo)[0]
    assert off != 9999 and ki[off : off + 20] == b"2020:01:02 03:04:05\x00"


@pytest.mark.parametrize("e,fej", [("<", b"II*\x00"), (">", b"MM\x00*")])
def test_a_ketszer_szereplo_tag_orzese_mindket_sorrendre(e, fej):
    forras = fej + struct.pack(e + "I", 8) + struct.pack(e + "H", 2)
    forras += struct.pack(e + "HHI4s", 0x0132, 1, 1, b"\x01\x00\x00\x00") * 2 + b"\x00" * 4
    with pytest.raises(th.TiffHiba):
        th.frissitett_tiff(forras, _valtozasok())


def test_ii_ures_blokk_gps_es_exif_is_epul():
    ki = th.frissitett_tiff(None, [th.Valtozas("Exif", 0x9003, _DT)])
    assert ki[:2] == b"II"
    assert 0x8769 in _ifd0(ki, "<")

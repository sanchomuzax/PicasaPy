"""A régi PMP-, thumbindex- és cache-olvasók szerkezettudatos fuzz-próbái."""
# ruff: noqa: E402

from __future__ import annotations

import struct
from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st

from picasapy.pmpimport.cacheblob import open_cache_store
from picasapy.pmpimport.pmp_column import PmpFormatError, read_pmp_column
from picasapy.pmpimport.table import read_table
from picasapy.pmpimport.thumbindex import (
    ThumbIndexFormatError,
    read_slot_index,
    read_thumb_index,
)

_PMP_MAGIC = 0x3FCCCCCD
_CONST_1332 = 0x1332
_CONST_2 = 2
_THUMB_MAGIC = 0x40466666
_KORPUSZ = Path(__file__).parent / "korpusz" / "pmp"
_PMP_KORPUSZ = bytes.fromhex(
    (_KORPUSZ / "column-header.hex").read_text(encoding="ascii").strip()
)
_THUMB_KORPUSZ = bytes.fromhex(
    (_KORPUSZ / "thumbindex-header.hex").read_text(encoding="ascii").strip()
)


def _pmp_fejlec(tipus: int, darab: int) -> bytes:
    return struct.pack(
        "<IHHIHHI",
        _PMP_MAGIC,
        tipus,
        _CONST_1332,
        _CONST_2,
        tipus,
        _CONST_1332,
        darab,
    )


def _slot_index(darab: int, ertek: int = 0) -> bytes:
    adat = bytearray(struct.pack("<f", 1.6))
    for _ in range(4):
        adat.extend(struct.pack("<I", darab))
        if darab:
            adat.extend(struct.pack(f"<{darab}I", *([ertek] * darab)))
    return bytes(adat)


@st.composite
def _pmp_eset(draw):
    tipus = draw(st.integers(min_value=0, max_value=9))
    darab = draw(st.sampled_from((0, 1, 3, 0x7FFFFFFF, 0xFFFFFFFF)))
    torzs = draw(st.binary(max_size=2048))
    fejlec = _PMP_KORPUSZ if draw(st.booleans()) else _pmp_fejlec(tipus, darab)
    return fejlec + torzs


@st.composite
def _thumb_eset(draw):
    darab = draw(st.sampled_from((0, 1, 2, 100_000, 0xFFFFFFFF)))
    torzs = draw(st.binary(max_size=2048))
    fejlec = _THUMB_KORPUSZ if draw(st.booleans()) else struct.pack(
        "<II", _THUMB_MAGIC, darab
    )
    return fejlec + torzs


@st.composite
def _slot_eset(draw):
    darab = draw(st.sampled_from((0, 1, 3, 100_000, 0xFFFFFFFF)))
    if darab <= 3:
        alap = _slot_index(darab)
    else:
        # Nagy, de hamis darabszám: a törzs szándékosan hiányzik.
        alap = struct.pack("<fI", 1.6, darab)
    torzs = draw(st.binary(max_size=128))
    return alap + torzs


@given(pmp=_pmp_eset(), thumb=_thumb_eset(), slot=_slot_eset())
def test_mutalt_pmp_fejlecek_es_darabszamok_hibas_adaton_is_gyorsak(
    pmp, thumb, slot, tmp_path, fuzz_keret
):
    fajl = tmp_path / "fuzz.pmp"
    thumb_fajl = tmp_path / "thumbindex.db"
    slot_fajl = tmp_path / "thumbs_index.db"
    db3 = tmp_path / "db3"
    db3.mkdir(exist_ok=True)
    tabla_fajl = db3 / "imagedata_caption.pmp"
    cache_data = db3 / "thumbs_0.db"
    cache_index = db3 / "thumbs_index.db"

    with fuzz_keret():
        fajl.write_bytes(pmp)
        thumb_fajl.write_bytes(thumb)
        slot_fajl.write_bytes(slot)
        tabla_fajl.write_bytes(pmp)
        cache_index.write_bytes(slot)
        cache_data.write_bytes(b"")

        try:
            read_pmp_column(fajl)
        except PmpFormatError:
            pass
        try:
            read_thumb_index(thumb_fajl)
        except ThumbIndexFormatError:
            pass
        try:
            read_slot_index(slot_fajl)
        except ThumbIndexFormatError:
            pass
        try:
            read_table(db3, "imagedata")
        except PmpFormatError:
            pass
        try:
            open_cache_store(db3, "thumbs")
        except ThumbIndexFormatError:
            pass

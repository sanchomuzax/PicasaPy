"""A `.picasa.ini` veszteségmentes parserének szerkezettudatos fuzz-próbái."""
# ruff: noqa: E402

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st

from picasapy.ini.document import parse_document
from picasapy.ini.filters import FilterOp, parse_filters, serialize_filters
from picasapy.ini.io import load_document, save_document
from picasapy.ini.rect64 import decode_rect64, encode_rect64

_ALFABET = "abcXYZ0123[]=;,#\r\n\t\x00 éőű"
_TOKENEK = ("0", "1", "-1", "nan", "inf", "-inf", "1e9", "", "0000ffff")
_INI_KORPUSZ = Path(__file__).parent / "korpusz" / "ini" / "roundtrip.ini"


@st.composite
def _ini_esetek(draw):
    szoveg = draw(st.text(alphabet=_ALFABET, max_size=2048))
    ops = draw(
        st.lists(
            st.tuples(
                st.sampled_from(("bw", "sepia", "Border", "Vignette", "unknown")),
                st.lists(st.sampled_from(_TOKENEK), min_size=0, max_size=5),
            ),
            max_size=8,
        )
    )
    rect = draw(st.text(alphabet="0123456789abcdefABCDEF", min_size=1, max_size=16))
    raw = draw(st.binary(max_size=2048))
    bom = draw(st.booleans())
    return szoveg, ops, rect, raw, bom


@given(eset=_ini_esetek())
def test_ini_parser_es_szurok_roundtripja_es_mentese_bajtazonos(
    eset, tmp_path, fuzz_keret
):
    szoveg, nyers_ops, rect, raw, bom = eset
    with TemporaryDirectory(prefix="ini-", dir=tmp_path) as temp_dir, fuzz_keret():
        mappa = Path(temp_dir)
        dokumentum = parse_document(szoveg)
        assert dokumentum.serialize() == szoveg

        ops = tuple(FilterOp(nev, tuple(parameterek)) for nev, parameterek in nyers_ops)
        kimenet = serialize_filters(ops)
        assert parse_filters(kimenet) == ops
        assert parse_filters(serialize_filters(parse_filters(kimenet))) == ops

        dekodolt = decode_rect64(rect)
        ujra = decode_rect64(encode_rect64(dekodolt))
        assert ujra == dekodolt

        cel = mappa / "fuzz.picasa.ini"
        cel.write_bytes((b"\xef\xbb\xbf" if bom else b"") + raw)
        betoltott = load_document(cel)
        mentett = mappa / "mentett.picasa.ini"
        save_document(betoltott, mentett)
        assert mentett.read_bytes() == cel.read_bytes()


@given(ertek=st.text(alphabet=_ALFABET, max_size=1024))
def test_ini_modositasakor_a_masik_szakasz_bajtjai_valtozatlanok(
    ertek, fuzz_keret
):
    eredeti = "# fejléc\r\n[Masik.jpg]\ncaption = változatlan\r\n[Harmadik.jpg]\nnyers\n"
    with fuzz_keret():
        dokumentum = parse_document(eredeti)
        modositott = dokumentum.with_value("Fuzz.jpg", "caption", ertek)
        assert modositott.sections[: len(dokumentum.sections)] == dokumentum.sections
        assert modositott.serialize().startswith(eredeti)

        eltavolitott = modositott.with_removed("Fuzz.jpg", "caption")
        assert eltavolitott.serialize() == eredeti


@given(ertek=st.text(alphabet="0123456789abcdefABCDEF", min_size=1, max_size=16))
def test_rect64_rovid_es_teljes_hex_alakja_fixpont(ertek, fuzz_keret):
    with fuzz_keret():
        egyszer = decode_rect64(ertek)
        teljes = encode_rect64(egyszer)
        assert decode_rect64(encode_rect64(decode_rect64(teljes))) == egyszer


def test_ini_korpusz_bom_crlf_nul_es_csonka_szakasz_roundtripja(fuzz_keret):
    raw = _INI_KORPUSZ.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    szoveg = raw[3:].decode("utf-8")
    with fuzz_keret():
        assert parse_document(szoveg).serialize() == szoveg


@pytest.mark.parametrize(
    ("raw", "vart_kodolas", "vart_bom"),
    (
        (b"[a]\ncaption=\xc3\xa9\n", "utf-8", False),
        (b"\xef\xbb\xbf[a]\r\ncaption=\xc3\xa9\r\n", "utf-8", True),
        (b"[a]\ncaption=\xe9\n", "latin-1", False),
        (b"[a]\ncaption=\xff\xfe\n", "latin-1", False),
    ),
)
def test_ini_bajtszintu_utf8_latin1_es_hibas_utf8_mentese(raw, vart_kodolas, vart_bom, tmp_path, fuzz_keret):
    with fuzz_keret():
        forras = tmp_path / "bemenet.picasa.ini"
        cel = tmp_path / "kimenet.picasa.ini"
        forras.write_bytes(raw)
        dokumentum = load_document(forras)
        assert dokumentum.encoding == vart_kodolas
        assert dokumentum.bom is vart_bom
        save_document(dokumentum, cel)
        assert cel.read_bytes() == raw

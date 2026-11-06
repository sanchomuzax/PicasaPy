"""CXF-, contacts.xml- és ISO-olvasók fuzz-próbái."""
# ruff: noqa: E402

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import struct

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import example, given, strategies as st

from picasapy.backup.iso_olvaso import ISOOlvaso
from picasapy.collage.cxf import CxfNode, CxfProject, dumps, loads
from picasapy.ini.contacts_xml import (
    ContactXmlEntry,
    parse_contacts_xml,
    serialize_contacts_xml,
)


def _iso_rekord(szektor: int, meret: int, jelzok: int, nev: bytes) -> bytes:
    hossz = 33 + len(nev) + (len(nev) % 2 == 0)
    adat = bytearray(hossz)
    adat[0] = hossz
    adat[2:6] = struct.pack("<I", szektor)
    adat[6:10] = struct.pack(">I", szektor)
    adat[10:14] = struct.pack("<I", meret)
    adat[14:18] = struct.pack(">I", meret)
    adat[25] = jelzok
    adat[32] = len(nev)
    adat[33 : 33 + len(nev)] = nev
    return bytes(adat)


def _iso_mag() -> bytes:
    szektor = 2048
    adat = bytearray(20 * szektor)
    pvd = memoryview(adat)[16 * szektor : 17 * szektor]
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[6] = 1
    pvd[156:190] = _iso_rekord(18, szektor, 0x02, b"\x00")
    terminator = memoryview(adat)[17 * szektor : 18 * szektor]
    terminator[0] = 255
    terminator[1:6] = b"CD001"
    terminator[6] = 1
    konyvtar = 18 * szektor
    adat[konyvtar : konyvtar + 34] = _iso_rekord(18, szektor, 0x02, b"\x00")
    adat[konyvtar + 34 : konyvtar + 68] = _iso_rekord(
        18, szektor, 0x02, b"\x01"
    )
    fajlnev = b"fuzz.txt;1"
    rekord = _iso_rekord(19, 4, 0, fajlnev)
    adat[konyvtar + 68 : konyvtar + 68 + len(rekord)] = rekord
    adat[19 * szektor : 19 * szektor + 4] = b"fuzz"
    return bytes(adat)


_XML_ALFABET = "abcXYZ0123 <>&;/'\"=\r\n"
_ISO_ALAP = _iso_mag()
_XML_KORPUSZ = Path(__file__).parent / "korpusz" / "xml"
_CXF_KORPUSZ = (_XML_KORPUSZ / "cxf.xml").read_bytes()
_CONTACTS_KORPUSZ = (_XML_KORPUSZ / "contacts.xml").read_text(encoding="utf-8")
_ISO_KORPUSZ = (_XML_KORPUSZ / "iso-seed.txt").read_bytes()
_ENTITY_BOMBA = ["<!ENTITY a '1234567890'>"]
_ELOZO_ENTITAS = "a"
for _ENTITAS_NEVE in "bcdefgh":
    _ENTITY_BOMBA.append(
        f"<!ENTITY {_ENTITAS_NEVE} '{('&' + _ELOZO_ENTITAS + ';') * 8}'>"
    )
    _ELOZO_ENTITAS = _ENTITAS_NEVE
_CONTACTS_ENTITAS_BOMBA = (
    "<!DOCTYPE contacts ["
    + "".join(_ENTITY_BOMBA)
    + "]><contacts><contact id='6582a1' name='&h;' "
    + "modified_time='2026-01-01T00:00:00+00:00' local_contact='1'/></contacts>"
)


@st.composite
def _cxf_eset(draw):
    if draw(st.booleans()):
        return _CXF_KORPUSZ
    verzio = draw(st.sampled_from((1, 2)))
    cxf = dumps(
        CxfProject(
            version=verzio,
            album_title=draw(st.text(alphabet=_XML_ALFABET, max_size=64)),
            nodes=(
                CxfNode(
                    x=0.1,
                    y=0.2,
                    w=0.3,
                    h=0.4,
                    theta=0.0,
                    scale=12.0,
                    src=draw(st.text(alphabet=_XML_ALFABET, max_size=64)),
                ),
            ),
        )
    )
    return cxf


@given(
    cxf=_cxf_eset(),
    cxf_nyers=st.binary(max_size=4096),
    contacts=st.one_of(
        st.just(_CONTACTS_KORPUSZ),
        st.text(alphabet=_XML_ALFABET, max_size=4096),
    ),
    nev=st.text(alphabet=_XML_ALFABET, max_size=128),
    azonosito=st.text(alphabet="0123456789abcdef", min_size=1, max_size=16),
    iso_offset=st.integers(min_value=0, max_value=len(_ISO_ALAP) - 1),
    iso_byte=st.integers(min_value=0, max_value=255),
    iso_hossz=st.integers(min_value=0, max_value=len(_ISO_ALAP)),
)
@example(
    cxf=b"<collage version=\"2\"><spacing value=\"0\"/></collage>",
    cxf_nyers=b"<collage><node",
    contacts=_CONTACTS_ENTITAS_BOMBA,
    nev="Fuzzer & Writer",
    azonosito="6582a1",
    iso_offset=20 * 2048 - 1,
    iso_byte=0,
    iso_hossz=20 * 2048,
)
def test_cxf_contacts_es_iso_mutalt_bemeneteken_is_korlatozott(
    cxf,
    cxf_nyers,
    contacts,
    nev,
    azonosito,
    iso_offset,
    iso_byte,
    iso_hossz,
    tmp_path,
    fuzz_keret,
):
    with fuzz_keret():
        projekt = loads(cxf)
        stabil = loads(dumps(projekt))
        assert loads(dumps(stabil)) == stabil

        try:
            betoltott = loads(cxf_nyers)
        except ValueError:
            pass
        else:
            stabil = loads(dumps(betoltott))
            assert loads(dumps(stabil)) == stabil

        try:
            parse_contacts_xml(contacts)
        except ValueError:
            pass

        bejegyzes = ContactXmlEntry(
            person_id=azonosito,
            name=nev,
            modified_time=datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
            local_contact="1",
        )
        irt_xml = serialize_contacts_xml((bejegyzes,))
        ujraolvasott = parse_contacts_xml(irt_xml)
        assert ujraolvasott == (bejegyzes,)
        assert parse_contacts_xml(serialize_contacts_xml(ujraolvasott)) == ujraolvasott

        iso = bytearray(_ISO_ALAP[:iso_hossz])
        if iso:
            hely = min(iso_offset, len(iso) - 1)
            iso[hely] = iso_byte
        for sorszam, kepbajtok in enumerate((bytes(iso), _ISO_KORPUSZ)):
            iso_path = tmp_path / f"mutalt-{sorszam}.iso"
            iso_path.write_bytes(kepbajtok)
            try:
                ISOOlvaso(iso_path)
            except ValueError:
                pass

"""#7250: új `[.album:token]` szakasznál a kulcsok sorrendje `name`, `token`, ...

Eredeti: `0x0052a810` (Ghidra-kötet 466-495, 3171-3367. sor).
"""

from __future__ import annotations

from picasapy.ini.albums import ensure_album
from picasapy.ini.document import parse_document


def _kulcsok(doc, szakasz):
    return [kulcs for kulcs, _ertek in doc.section(szakasz).items()]


def test_csak_nevvel_is_name_az_elso():
    doc = ensure_album(parse_document(""), "abc", "Nyaralás")
    assert _kulcsok(doc, ".album:abc") == ["name", "token"]


def test_minden_mezovel_az_eredeti_sorrend():
    doc = ensure_album(parse_document(""), "abc", "Nyaralás",
                       description="Leírás", location="Balaton", date="2025-07-10")
    assert _kulcsok(doc, ".album:abc") == ["name", "token", "description", "location", "date"]


def test_meglevo_szakasz_valtozatlan():
    eredeti = "[.album:abc]\ntoken=abc\nname=Régi\n"
    doc = ensure_album(parse_document(eredeti), "abc", "Új")
    assert doc.serialize() == parse_document(eredeti).serialize()

"""#7208: az album törlése után a szakasz megőrzi a token sort, az olvasó kihagyja.

A törléskor a [.album:<token>] szakaszban csak a token= sor marad meg;
a képszakaszok albums= sora kikerül, a többi kulcsuk érintetlen.
Az olvasó oldal a név nélküli, csak tokenes szakaszt nem mutatja albumként.
"""

from __future__ import annotations

from picasapy.ini.albums import albums_of, without_album_everywhere
from picasapy.ini.document import parse_document

_TOKEN = "7208" * 8
_OTHER = "b" * 32


def test_without_album_everywhere_megorzi_a_tokent_es_torli_a_tulajdonsagokat():
    tartalom = (
        f"[.album:{_TOKEN}]\n"
        f"token={_TOKEN}\n"
        "name=Nyaralás\n"
        "date=2026-01-01\n"
        "location=Balaton\n"
        "description=Szép nyár\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN},{_OTHER}\n"
        "caption=maradjon\n"
        f"[b.jpg]\n"
        f"albums={_TOKEN}\n"
        "star=yes\n"
    )
    document = parse_document(tartalom)

    eredmeny = without_album_everywhere(document, _TOKEN)

    # A [.album:<token>] szakasz megmarad, de csak a token= sorral
    szakasz = eredmeny.section(f".album:{_TOKEN}")
    assert szakasz is not None
    assert szakasz.get("token") == _TOKEN
    assert szakasz.get("name") is None
    assert szakasz.get("date") is None
    assert szakasz.get("location") is None
    assert szakasz.get("description") is None
    assert szakasz.items() == (("token", _TOKEN),)

    # A képszakaszokból kikerül a törölt token
    a = eredmeny.section("a.jpg")
    assert a is not None
    assert a.get("albums") == _OTHER
    assert a.get("caption") == "maradjon"

    b = eredmeny.section("b.jpg")
    assert b is not None
    assert b.get("albums") is None
    assert b.get("star") == "yes"

    # Az olvasó oldal a név nélküli szakaszt nem adja vissza
    assert not any(album.token == _TOKEN for album in albums_of(eredmeny))


def test_csak_tokenes_szakaszt_az_albums_of_nem_ad_vissza():
    tartalom = (
        f"[.album:{_TOKEN}]\n"
        f"token={_TOKEN}\n"
        f"[.album:{_OTHER}]\n"
        f"token={_OTHER}\n"
        "name=Érvényes album\n"
    )
    document = parse_document(tartalom)
    albumok = albums_of(document)
    assert len(albumok) == 1
    assert albumok[0].token == _OTHER
    assert albumok[0].name == "Érvényes album"

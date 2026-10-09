"""#4536: a személy-album borítója PicasaPy-metaadatként round-tripel."""

from __future__ import annotations

import pytest

from picasapy.ini import parse_document
from picasapy.ini.person_album_thumbnail import (
    clear_person_album_thumbnail,
    person_album_thumbnails,
    set_person_album_thumbnail,
)


def test_szemely_borito_mentese_es_visszaolvasasa_megoriz_minden_mas_adatot():
    eredeti = parse_document(
        "[Contacts2]\n"
        "1111111111111111=Anna;;\n"
        "[a.jpg]\n"
        "faces=rect64(1e00280045006e00),1111111111111111\n"
        "caption=megtartandó\n"
    )

    mentett = set_person_album_thumbnail(eredeti, "Anna", "a.jpg")

    assert person_album_thumbnails(mentett) == {"anna": "a.jpg"}
    assert mentett.section("PicasaPy").is_special is True
    assert [section.name for section in mentett.file_sections()] == ["a.jpg"]
    assert mentett.section("a.jpg").get("faces") == eredeti.section("a.jpg").get("faces")
    assert mentett.section("a.jpg").get("caption") == "megtartandó"
    assert "[PicasaPy]" not in eredeti.serialize()


def test_ugyanazon_szemely_boritoja_felulirhato_es_torolheto_kisbetuuggetlenul():
    mentett = set_person_album_thumbnail(
        parse_document("[a.jpg]\ncaption=marad\n"), "Anna", "a.jpg"
    )
    felulirt = set_person_album_thumbnail(mentett, "ANNA", "b.jpg")

    assert person_album_thumbnails(felulirt) == {"anna": "b.jpg"}
    torolt = clear_person_album_thumbnail(felulirt, "anna")
    assert person_album_thumbnails(torolt) == {}
    assert torolt.section("a.jpg").get("caption") == "marad"


@pytest.mark.parametrize("nev,fajl", [("", "a.jpg"), ("Anna", "../a.jpg"), ("Anna", "")])
def test_ervenytelen_szemely_vagy_nem_mappabeli_fajl_elutasitott(nev, fajl):
    with pytest.raises(ValueError):
        set_person_album_thumbnail(parse_document(""), nev, fajl)

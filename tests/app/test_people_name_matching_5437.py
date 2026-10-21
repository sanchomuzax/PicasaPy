"""#5437: a People-lista és a csempe névjavaslatának bináris egyezése."""

from __future__ import annotations

from picasapy.app.people_name_matching import (
    filter_and_sort_people,
    match_people_name,
)


def test_nevszavas_egyezes_a_nev_barmelyik_szavatol() -> None:
    assert match_people_name("ki", "Kiss Anna")
    assert match_people_name("ki", "Anna Kiss")
    assert match_people_name("anna k", "Anna Kiss")
    assert match_people_name("jean-p", "Jean-Pierre")
    assert match_people_name("john_s", "John-Smith")
    assert match_people_name("kelly:mar", "Kelly:Marie")
    assert not match_people_name("Nagykiss", "Kiss Anna")
    assert not match_people_name("kiss anna", "Anna Kiss")


def test_kisbetusites_nem_vonja_ossze_az_ekezeteket() -> None:
    assert match_people_name("Év", "Éva Kiss")
    assert not match_people_name("Ev", "Éva Kiss")
    assert match_people_name("KI", "Anna Kiss")


def test_ures_kereses_minden_nevre_egyezik() -> None:
    assert match_people_name("", "Anna Kiss")
    assert match_people_name("   ", "Anna Kiss")


def test_keresesi_sorrend_az_uj_embert_es_a_nev_prefixet_elore_hozza() -> None:
    people = [
        {"name": "Anna Kiss", "contactIds": ["1"]},
        {"name": "Kiss Anna", "contactIds": ["2"]},
        {"name": "Kira Zöld", "contactIds": ["3"]},
        {"name": "Kiwi Ádám", "contactIds": ["4"]},
        {"name": "Kiss Béla", "contactIds": [], "isNew": True},
        {"name": "Béla", "contactIds": ["5"]},
    ]

    ordered = filter_and_sort_people(people, "ki")

    assert [person["name"] for person in ordered] == [
        "Kiss Béla",
        "Kira Zöld",
        "Kiss Anna",
        "Kiwi Ádám",
        "Anna Kiss",
    ]


def test_dontetlennel_nev_szerint_es_ures_keresesnel_is_nev_szerint_rendez() -> None:
    tied = [
        {"name": "Ann Zed", "contactIds": ["1"]},
        {"name": "Ann Able", "contactIds": ["2"]},
        {"name": "Z Ann", "contactIds": ["3"]},
    ]
    assert [row["name"] for row in filter_and_sort_people(tied, "ann")] == [
        "Ann Able",
        "Ann Zed",
        "Z Ann",
    ]

    empty_search = [
        {"name": "Zed", "contactIds": [], "isNew": True},
        {"name": "amy", "contactIds": ["4"]},
    ]
    assert [row["name"] for row in filter_and_sort_people(empty_search, "")] == [
        "amy",
        "Zed",
    ]


def test_kapcsolat_nelkuli_szemely_nem_szamit_ujnak() -> None:
    # Az eredetiben csak a mentetlen (0-s azonosítójú) rekord kerül előre.
    entries = [
        {"name": "Kiss Zoltan", "contactIds": []},
        {"name": "Kiss Anna", "contactIds": ["1"]},
    ]

    result = filter_and_sort_people(entries, "kiss")

    assert [entry["name"] for entry in result] == ["Kiss Anna", "Kiss Zoltan"]

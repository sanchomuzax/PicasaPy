"""#1767 — a Személyek lista három rendezési módja.

Az eredeti Picasa a Személyek listáját **három mód** szerint rendezi, és a
választást a `Preferences\\peoplesort` kulcs őrzi:

| `peoplesort` | felirat |
|---|---|
| 0 | Sort &People by Name |
| 1 | Sort People by &Amount |
| 2 | Sort People by Top &10 |

Nálunk eddig **fix névsorrend** volt (`people.py`), és a menü három tétele
`placeholder` — látszott, kattintható volt, nem csinált semmit.

⚠️ A **Top 10 szűrés is**, nem csak rendezés: a lista tíz elemre rövidül.
"""

from __future__ import annotations

import pytest

from picasapy.index.people import (
    PEOPLE_SORT_MODES,
    PersonRecord,
    TOP_LIST_LIMIT,
    rendezd_szemelyeket,
)

_MINTA = (
    PersonRecord(name="Csilla", photo_count=3),
    PersonRecord(name="anna", photo_count=9),
    PersonRecord(name="Béla", photo_count=9),
    PersonRecord(name="Zoltán", photo_count=1),
)


class TestNevSzerint:
    def test_kis_nagybetu_turoen_rendez(self):
        eredmeny = rendezd_szemelyeket(_MINTA, "name")
        assert [p.name for p in eredmeny] == [
            "anna", "Béla", "Csilla", "Zoltán"
        ]

    def test_ez_az_ALAPERTELMEZES(self):
        """`peoplesort=0` az eredeti alapértéke is."""
        assert rendezd_szemelyeket(_MINTA, "name") == rendezd_szemelyeket(
            _MINTA, "nincs-ilyen-mod"
        )


class TestDarabszamSzerint:
    def test_a_legtobb_kepen_szereplo_all_elol(self):
        eredmeny = rendezd_szemelyeket(_MINTA, "count")
        assert [p.photo_count for p in eredmeny] == [9, 9, 3, 1]

    def test_azonos_darabszamnal_nevsor(self):
        """A `people_with` már ezt a `(-count, name.casefold())` kulcsot
        használja — ugyanazt hasznosítjuk újra."""
        eredmeny = rendezd_szemelyeket(_MINTA, "count")
        assert [p.name for p in eredmeny][:2] == ["anna", "Béla"]


class TestTopLista:
    def test_legfeljebb_tiz_elem(self):
        sokan = tuple(
            PersonRecord(name=f"sz{i:02d}", photo_count=100 - i)
            for i in range(25)
        )
        assert len(rendezd_szemelyeket(sokan, "top")) == TOP_LIST_LIMIT

    def test_a_darabszam_szerinti_elejet_adja(self):
        sokan = tuple(
            PersonRecord(name=f"sz{i:02d}", photo_count=100 - i)
            for i in range(25)
        )
        assert (
            rendezd_szemelyeket(sokan, "top")
            == rendezd_szemelyeket(sokan, "count")[:TOP_LIST_LIMIT]
        )

    def test_tiznel_kevesebbet_nem_told_fel(self):
        assert len(rendezd_szemelyeket(_MINTA, "top")) == len(_MINTA)


class TestAModok:
    def test_harom_mod_van(self):
        assert PEOPLE_SORT_MODES == ("name", "count", "top")

    @pytest.mark.parametrize("mod", PEOPLE_SORT_MODES)
    def test_egyik_sem_veszit_el_szemelyt(self, mod: str):
        """A `top` KIVÉTEL — az szándékosan szűr; a másik kettő nem."""
        eredmeny = rendezd_szemelyeket(_MINTA, mod)
        if mod == "top":
            assert len(eredmeny) <= TOP_LIST_LIMIT
        else:
            assert len(eredmeny) == len(_MINTA)

    def test_ures_listara_ures(self):
        for mod in PEOPLE_SORT_MODES:
            assert rendezd_szemelyeket((), mod) == ()

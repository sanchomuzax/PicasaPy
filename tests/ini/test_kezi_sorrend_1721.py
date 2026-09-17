"""#1721 — a kézi sorrend (`priority=`) a `.picasa.ini`-ben.

Az ADR-014 (`docs/decisions/kezi-sorrend-a-picasa-iniben.md`) döntése: a
manuális sorrend a mappa saját `.picasa.ini`-jébe megy, NEM a `db3`-ba. A
formátum onnan való:

| | |
|---|---|
| kulcs | `priority` a kép szakaszában |
| érték | tizedes szám, **pont** tizedesjellel |
| hiányzó | „nincs kézi hely" |

⚠️ A számozás szándékosan NEM egész: beszúráskor két szomszéd közé FÉL
érték kerül, így egy áthelyezés nem írja át az egész mappát.
"""

from __future__ import annotations

from picasapy.ini.document import parse_document
from picasapy.ini.priority import (
    kozteslepes,
    olvasd_a_prioritasokat,
    prioritas_nelkul,
    prioritassal,
)


class TestOlvasas:
    def test_a_kulcsot_szamkent_adja(self):
        doc = parse_document("[a.jpg]\npriority=2.5\n")

        assert olvasd_a_prioritasokat(doc) == {"a.jpg": 2.5}

    def test_a_kulcs_nelkuli_kep_kimarad(self):
        doc = parse_document("[a.jpg]\nstar=yes\n[b.jpg]\npriority=1\n")

        assert olvasd_a_prioritasokat(doc) == {"b.jpg": 1.0}

    def test_a_romlott_erteket_kihagyja(self):
        """Nem dobhat: egy kézzel elrontott sor ne vigye el a rács
        rendezését — a kép „nincs kézi helyen" állapotba esik."""
        doc = parse_document("[a.jpg]\npriority=ize\n[b.jpg]\npriority=3\n")

        assert olvasd_a_prioritasokat(doc) == {"b.jpg": 3.0}

    def test_a_vesszos_tizedesjelet_NEM_fogadja_el(self):
        """A gépi számok írásmódja a PONT (`docs/specs/tizedesjel.md`); a
        vesszős alak nem a mi formátumunk, és a `float()` sem érti."""
        doc = parse_document("[a.jpg]\npriority=2,5\n")

        assert olvasd_a_prioritasokat(doc) == {}

    def test_a_mappa_szakaszt_nem_nezi(self):
        doc = parse_document("[Picasa]\npriority=9\n[a.jpg]\npriority=1\n")

        assert olvasd_a_prioritasokat(doc) == {"a.jpg": 1.0}


class TestIras:
    def test_ponttal_ir(self):
        doc = prioritassal(parse_document("[a.jpg]\nstar=yes\n"), "a.jpg", 2.5)

        assert "priority=2.5" in doc.serialize()

    def test_az_egesz_ertek_is_pontos_alakban_megy(self):
        """A 3.0 NEM „3”: az olvasó `float`-ot vár, és a formátum egyetlen
        alakja a tizedes szám — így a fájl önmagában is elmondja, hogy
        törtérték is lehet benne."""
        doc = prioritassal(parse_document("[a.jpg]\n"), "a.jpg", 3.0)

        assert "priority=3.0" in doc.serialize()

    def test_a_tobbi_kulcsot_nem_bantja(self):
        doc = prioritassal(
            parse_document("[a.jpg]\nstar=yes\ncrop64=1234\n"), "a.jpg", 1.0
        )
        szoveg = doc.serialize()

        assert "star=yes" in szoveg
        assert "crop64=1234" in szoveg

    def test_uj_szakaszt_is_letrehoz(self):
        doc = prioritassal(parse_document("[a.jpg]\nstar=yes\n"), "b.jpg", 1.0)

        assert olvasd_a_prioritasokat(doc) == {"b.jpg": 1.0}

    def test_a_torles_csak_a_kulcsot_veszi_ki(self):
        doc = prioritas_nelkul(
            parse_document("[a.jpg]\nstar=yes\npriority=1.0\n"), "a.jpg"
        )
        szoveg = doc.serialize()

        assert "priority" not in szoveg
        assert "star=yes" in szoveg


class TestKozteslepes:
    """A beszúrás értéke — ezért nem kell az egész mappát átírni."""

    def test_ket_szomszed_koze_a_felezopont_kerul(self):
        assert kozteslepes(1.0, 2.0) == 1.5

    def test_a_lista_elejere_eggyel_kisebb(self):
        assert kozteslepes(None, 1.0) == 0.0

    def test_a_lista_vegere_eggyel_nagyobb(self):
        assert kozteslepes(3.0, None) == 4.0

    def test_ures_listaban_nulla(self):
        assert kozteslepes(None, None) == 0.0

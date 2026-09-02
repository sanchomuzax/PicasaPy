"""A `rotate=` sor MEGŐRZÉSE nullánál (#2004).

## A lelet

Forgatásnál nullánál töröltük a `rotate=` kulcsot, ezzel az indoklással:
„n=0-nál a kulcs törlődik, így a teljes kör bitre pontos round-trip".

**Az indoklás pont fordítva igaz azokra a fájlokra, amiket a VALÓDI
Picasa írt.** A Picasa a `rotate` alapértékének a `rotate(0)`-t tekinti,
nem a hiányzó kulcsot (`0x0068b535`–`0x0068b58c`: kulcs→alapérték tábla),
és ki is írja: a tulajdonos gyűjteményében **1 735** `rotate=rotate(0)`
sor van.

⇒ Egy Picasa-eredetű fájlon a négyszeri forgatás nálunk **eltávolított
egy sort**, ami eredetileg ott volt.

## A szabály: MEGŐRZÉS, nem „mindig kiírjuk"

Ha mindig kiírnánk, olyan fájlokba is bekerülne a sor, amelyekben
eredetileg nem volt — az ugyanúgy eltérés. A helyes szabály:

| a fájlban volt `rotate=` sor? | 0 lépésnél |
|---|---|
| **igen** | maradjon, `rotate(0)` értékkel |
| **nem** | ne keletkezzen |
"""

from __future__ import annotations

import pytest

from picasapy.app.photo_ops_controller import forgatas_mutacio
from picasapy.ini import parse_document


def _dok(szoveg: str):
    return parse_document(szoveg)


def _sor(document, nev: str, kulcs: str) -> str | None:
    szakasz = document.section(nev)
    return szakasz.get(kulcs) if szakasz else None


class TestAMegorzes:
    def test_VOLT_rotate_sor_marad_nullanal(self):
        """A jegy első »Kész, ha« pontja: `rotate(2)` + kétszeri forgatás
        után a sor `rotate(0)`, NEM tűnik el."""
        dok = _dok("[kep.jpg]\nrotate=rotate(2)\n")
        uj = forgatas_mutacio(dok, "kep.jpg", 0)
        assert _sor(uj, "kep.jpg", "rotate") == "rotate(0)"

    def test_NEM_VOLT_rotate_sor_nem_keletkezik(self):
        """A második pont: ahol nem volt sor, ott ne keletkezzen."""
        dok = _dok("[kep.jpg]\nstar=yes\n")
        uj = forgatas_mutacio(dok, "kep.jpg", 0)
        assert _sor(uj, "kep.jpg", "rotate") is None

    def test_ismeretlen_szakaszban_sem_keletkezik(self):
        dok = _dok("[masik.jpg]\nrotate=rotate(1)\n")
        uj = forgatas_mutacio(dok, "kep.jpg", 0)
        assert _sor(uj, "kep.jpg", "rotate") is None
        assert _sor(uj, "masik.jpg", "rotate") == "rotate(1)", (
            "a másik kép sorát nem szabad bántani"
        )

    @pytest.mark.parametrize("steps", [1, 2, 3])
    def test_nem_nulla_lepesnel_valtozatlan_a_viselkedes(self, steps):
        dok = _dok("[kep.jpg]\nstar=yes\n")
        uj = forgatas_mutacio(dok, "kep.jpg", steps)
        assert _sor(uj, "kep.jpg", "rotate") == f"rotate({steps})"

    def test_a_KIS_NAGYBETU_sem_szamit(self):
        """Az ini-olvasónk kis-nagybetű-tűrő; a megőrzés se legyen
        érzékeny rá."""
        dok = _dok("[kep.jpg]\nRotate=rotate(1)\n")
        uj = forgatas_mutacio(dok, "kep.jpg", 0)
        assert _sor(uj, "kep.jpg", "rotate") == "rotate(0)"


class TestATOBBI_SOR_ERINTETLEN:
    def test_a_szomszedos_kulcsok_megmaradnak(self):
        dok = _dok("[kep.jpg]\nstar=yes\nrotate=rotate(3)\ncaption=szia\n")
        uj = forgatas_mutacio(dok, "kep.jpg", 0)
        assert _sor(uj, "kep.jpg", "star") == "yes"
        assert _sor(uj, "kep.jpg", "caption") == "szia"


class TestAKOMMENT_SEM_HAZUDHAT:
    def test_a_felrevezeto_indoklas_eltunt(self):
        """A jegy negyedik pontja: a `_apply_rotate` docstringje ma azt
        állítja, hogy a törlés adja a bitre pontos round-tripet — épp
        fordítva igaz."""
        import inspect

        from picasapy.app.photo_ops_controller import PhotoOpsMixin

        doc = inspect.getdoc(PhotoOpsMixin._apply_rotate) or ""
        assert "kulcs törlődik, így a teljes kör bitre pontos" not in doc

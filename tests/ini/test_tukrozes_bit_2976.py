"""#2976: a `flipped(N)` bit→tengely hozzárendelése és a nulla írása.

A #2938 kimérte az eredeti ini-írójából (`0x0042d7e0`), mit jelent az `N`:

| `flipped` bit | érték | a kiváltott művelet | tengely |
|---|---:|---:|---|
| 0. | `1` | 2 | **vízszintes** |
| 1. | `2` | 1 | **függőleges** |

A mi jelzőnk eddig FORDÍTVA állt (`1` = függőleges), mert a
billentyű-ág argumentumát vette át — az viszont egy MÁSIK számtér. Amíg a
jelző csak az indexben élt, ez nem látszott; a fájlba írva a másik
tengelyt írnánk le, és az eredeti Picasa rosszul olvasná vissza.

A második mért szabály: **nulla maszknál a kulcs ÜRES értéket kap**
(`0x0042d864`), nem `flipped(0)`-t. Ezért nincs egyetlen `flipped=` sor
sem a 859 fájlos korpuszban.
"""

from __future__ import annotations

import pytest

from picasapy.app.photo_ops_controller import tukrozes_mutacio
from picasapy.ini.document import parse_document
from picasapy.render.flip import FLIP_HORIZONTAL, FLIP_MASK, FLIP_VERTICAL


class TestABitHozzarendeles:
    """A jelző értéke MAGA az ini bitmaszkja — nincs átváltás."""

    def test_a_vizszintes_az_ELSO_bit(self):
        assert FLIP_HORIZONTAL == 1

    def test_a_fuggoleges_a_MASODIK_bit(self):
        assert FLIP_VERTICAL == 2

    def test_a_ketto_egyutt_harom(self):
        assert FLIP_MASK == 3


def _dok(torzs: str):
    return parse_document(torzs)


def _ertek(dokumentum, nev="egy.jpg"):
    szakasz = dokumentum.section(nev)
    return None if szakasz is None else szakasz.get("flipped")


class TestAzIrás:
    def test_a_vizszintes_flipped_1_et_ir(self):
        uj = tukrozes_mutacio(_dok("[egy.jpg]\nstar=yes\n"), "egy.jpg",
                              FLIP_HORIZONTAL)
        assert _ertek(uj) == "flipped(1)"

    def test_a_fuggoleges_flipped_2_t_ir(self):
        uj = tukrozes_mutacio(_dok("[egy.jpg]\nstar=yes\n"), "egy.jpg",
                              FLIP_VERTICAL)
        assert _ertek(uj) == "flipped(2)"

    def test_mindketto_flipped_3_at_ir(self):
        uj = tukrozes_mutacio(_dok("[egy.jpg]\nstar=yes\n"), "egy.jpg",
                              FLIP_HORIZONTAL | FLIP_VERTICAL)
        assert _ertek(uj) == "flipped(3)"


class TestANulla:
    """A mért szabály: nulla maszknál ÜRES érték, nem `flipped(0)`."""

    def test_a_meglevo_sor_URESRE_vált(self):
        uj = tukrozes_mutacio(_dok("[egy.jpg]\nflipped=flipped(1)\n"),
                              "egy.jpg", 0)
        assert _ertek(uj) == "", "nulla maszknál üres érték jár"

    def test_NEM_ir_flipped_0_t(self):
        uj = tukrozes_mutacio(_dok("[egy.jpg]\nflipped=flipped(2)\n"),
                              "egy.jpg", 0)
        assert _ertek(uj) != "flipped(0)"

    def test_ahol_NEM_volt_sor_ott_nem_keletkezik(self):
        """A `rotate` megőrző szabálya (#2004): idegen fájlba ne írjunk
        olyan kulcsot, ami eddig nem volt benne."""
        uj = tukrozes_mutacio(_dok("[egy.jpg]\nstar=yes\n"), "egy.jpg", 0)
        assert _ertek(uj) is None


class TestARoundTrip:
    """Beolvasva és visszaírva bitre azonos — a jegy 4. pontja."""

    @pytest.mark.parametrize("maszk", [1, 2, 3])
    def test_oda_vissza_azonos(self, maszk):
        from picasapy.index.sync import flip_jelzo

        torzs = f"[egy.jpg]\nflipped=flipped({maszk})\n"
        beolvasott = flip_jelzo(_dok(torzs).section("egy.jpg").get("flipped"))
        assert beolvasott == maszk
        uj = tukrozes_mutacio(_dok(torzs), "egy.jpg", beolvasott)
        assert uj.serialize() == torzs, "a visszaírás nem bitre azonos"

    def test_az_ismeretlen_ertek_nem_dol_el(self):
        from picasapy.index.sync import flip_jelzo

        assert flip_jelzo("flipped(9)") == 1, "a fölös bitek leesnek"
        assert flip_jelzo(None) == 0
        assert flip_jelzo("") == 0

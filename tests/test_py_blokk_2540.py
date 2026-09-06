"""A Python-blokk-kivágó saját őrei (#2540).

⚠️ Ez MÉRŐESZKÖZ: több vezérlő-őr épül rá. Ha némán rosszat vág ki, azok
az őrök hallgatnak olyankor is, amikor jelezniük kellene — a hibás mérő
rosszabb, mint a hiányzó.
"""

from __future__ import annotations

import pytest

from tests.support.py_blokk import fuggveny_torzs, kommentek_nelkul


class TestKommentekNelkul:
    def test_a_hossz_valtozatlan(self):
        """A sorszámok és eltolások csak akkor maradnak érvényesek, ha a
        kivágott rész helyén szóköz áll."""
        forras = "a = 1  # megjegyzés\nb = 2\n"
        assert len(kommentek_nelkul(forras)) == len(forras)

    def test_sorkommentet_kivag(self):
        assert kommentek_nelkul("a = 1  # b = 2").rstrip() == "a = 1"

    def test_a_SZTRINGEN_beluli_kettoskereszt_MARAD(self):
        """A `"#1234"` nem komment — enélkül a kivágó levágná a sor végét,
        és az őr egy MEGLÉVŐ sort látna hiányzónak."""
        sor = 'szin = "#ff8800"  # a mért érték'
        assert kommentek_nelkul(sor).rstrip() == 'szin = "#ff8800"'

    def test_a_docstringet_kivagja(self):
        forras = 'def f():\n    """replace( itt csak leírás"""\n    return 1\n'
        assert "replace(" not in kommentek_nelkul(forras)
        assert "return 1" in kommentek_nelkul(forras)

    def test_a_modul_docstringjet_is_kivagja(self):
        forras = '"""x = 9"""\nx = 1\n'
        tiszta = kommentek_nelkul(forras)
        assert "x = 9" not in tiszta
        assert "x = 1" in tiszta

    def test_a_NEM_docstring_sztring_marad(self):
        """Csak az első utasítás docstring; egy sima sztring-konstans nem."""
        forras = 'def f():\n    a = 1\n    "ez nem docstring"\n'
        assert "ez nem docstring" in kommentek_nelkul(forras)


class TestFuggvenyTorzs:
    _FORRAS = (
        "def elso():\n"
        "    return 'A'\n"
        "\n"
        "\n"
        "def masodik():\n"
        "    # egy hosszú indoklás, ami a rögzített ablakot kicsúsztatná\n"
        "    def belso():\n"
        "        return 'belso'\n"
        "    return 'B'\n"
        "\n"
        "\n"
        "def harmadik():\n"
        "    return 'C'\n"
    )

    def test_a_horgony_sajat_fuggvenyet_adja(self):
        blokk = fuggveny_torzs(self._FORRAS, "def masodik()")
        assert "return 'B'" in blokk
        assert "return 'A'" not in blokk, "átcsúszott az ELŐZŐ függvénybe"
        assert "return 'C'" not in blokk, "átcsúszott a KÖVETKEZŐ függvénybe"

    def test_a_BEAGYAZOTT_fuggveny_bennemarad(self):
        blokk = fuggveny_torzs(self._FORRAS, "def masodik()")
        assert "return 'belso'" in blokk

    def test_a_LEGBELSO_befoglalot_adja(self):
        """Törzsön belüli horgonyra a beágyazott függvény a blokk, nem a
        külső — különben a szomszéd ág is beleszámítana."""
        blokk = fuggveny_torzs(self._FORRAS, "return 'belso'")
        assert "def belso()" in blokk
        assert "return 'B'" not in blokk

    def test_a_KOMMENT_nem_kerul_bele(self):
        blokk = fuggveny_torzs(self._FORRAS, "def masodik()")
        assert "hosszú indoklás" not in blokk

    def test_hosszu_komment_utan_is_megvan_a_mert_sor(self):
        """A #2540 mért esete: a horgony és a mért sor közé sok sornyi
        indoklás kerül. A rögzített ablakos alak itt bukott."""
        forras = (
            "def worker():\n"
            + "    # sor\n" * 80
            + "    finally_helyett = True\n"
            + "    return finally_helyett\n"
        )
        assert "return finally_helyett" in fuggveny_torzs(
            forras, "def worker()"
        )

    def test_a_metodus_torzse_is_kivaghato(self):
        forras = (
            "class A:\n"
            "    def egy(self):\n"
            "        return 1\n"
            "\n"
            "    def ketto(self):\n"
            "        return 2\n"
        )
        blokk = fuggveny_torzs(forras, "def ketto(")
        assert "return 2" in blokk
        assert "return 1" not in blokk

    def test_ismeretlen_horgonyra_BUKIK(self):
        with pytest.raises(AssertionError, match="nincs meg"):
            fuggveny_torzs(self._FORRAS, "def nincs_ilyen()")

    def test_a_CSAK_kommentben_allo_horgony_NEM_talalat(self):
        """Enélkül egy kommentbe írt hivatkozás kielégítené az őrt."""
        with pytest.raises(AssertionError, match="nincs meg"):
            fuggveny_torzs("def f():\n    # cel_hivas()\n    pass\n",
                           "cel_hivas()")

    def test_modul_szintu_horgonyra_BUKIK(self):
        with pytest.raises(AssertionError, match="nem függvényben"):
            fuggveny_torzs("x = 1\n", "x = 1")

    def test_elrontott_forrasra_BUKIK(self):
        with pytest.raises(AssertionError, match="nem elemezhető"):
            fuggveny_torzs("def f(:\n", "def f(")

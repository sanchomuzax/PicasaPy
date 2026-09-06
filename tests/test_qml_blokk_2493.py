"""A blokk-kivágó saját őrei (#2493).

⚠️ Ez MÉRŐESZKÖZ: több forrás-szintű őr épül rá. Ha némán rosszat vág ki,
azok az őrök hallgatnak olyankor is, amikor jelezniük kellene — a hibás
mérő rosszabb, mint a hiányzó.
"""

from __future__ import annotations

import pytest

from tests.support.qml_blokk import blokk_horgonyra, kommentek_nelkul


class TestKommentekNelkul:
    def test_sorkommentet_kivag(self):
        assert kommentek_nelkul('a: 1  // b: 2').strip() == "a: 1"

    def test_blokk_kommentet_kivag(self):
        assert kommentek_nelkul("a: 1 /* b: 2 */ c: 3") == "a: 1  c: 3"

    def test_az_idezojelen_beluli_ket_per_MARAD(self):
        """A `"https://…"` nem komment — enélkül a kivágó levágná a sor
        végét, és az őr egy MEGLÉVŐ sort látna hiányzónak."""
        sor = 'source: "https://pelda.hu/kep.svg"'
        assert kommentek_nelkul(sor) == sor

    def test_a_kommentbe_irt_sor_nem_szamit(self):
        assert "ToolTip.text" not in kommentek_nelkul("// ToolTip.text: x")


class TestBlokkHorgonyra:
    _FORRAS = """
    Item {
        Gomb {
            objectName: "elso"
            text: "A"
        }
        Gomb {
            objectName: "masodik"
            // egy hosszú indoklás, ami a rögzített ablakot kicsúsztatná
            Belso { melyebb: true }
            text: "B"
        }
    }
    """

    def test_a_horgony_sajat_blokkjat_adja(self):
        blokk = blokk_horgonyra(self._FORRAS, 'objectName: "masodik"')
        assert 'text: "B"' in blokk
        assert 'text: "A"' not in blokk, "átcsúszott a szomszéd blokkba"

    def test_a_BEAGYAZOTT_blokk_is_bennemarad(self):
        """A záró zárójel keresése mélységet számol — különben a belső
        blokk `}`-ja korán zárná a kivágást."""
        blokk = blokk_horgonyra(self._FORRAS, 'objectName: "masodik"')
        assert "melyebb: true" in blokk
        assert blokk.rstrip().endswith("}")

    def test_a_KOMMENT_nem_kerul_bele(self):
        blokk = blokk_horgonyra(self._FORRAS, 'objectName: "masodik"')
        assert "hosszú indoklás" not in blokk

    def test_hosszu_komment_utan_is_megvan_a_mert_sor(self):
        """A #2493 mért esete: a horgony és a mért sor közé 14 sornyi
        indoklás kerül. A rögzített ablakos alak itt bukott."""
        forras = (
            'Gomb {\n  objectName: "g"\n'
            + "  // sor\n" * 40
            + '  ToolTip.text: qsTr("x")\n}\n'
        )
        assert 'ToolTip.text: qsTr("x")' in blokk_horgonyra(
            forras, 'objectName: "g"'
        )

    def test_ismeretlen_horgonyra_BUKIK(self):
        with pytest.raises(AssertionError, match="nincs meg"):
            blokk_horgonyra(self._FORRAS, "objectName: \"nincs-ilyen\"")

    def test_zaratlan_blokkra_BUKIK(self):
        with pytest.raises(AssertionError, match="nem záródik"):
            blokk_horgonyra('Gomb {\n  objectName: "g"\n', 'objectName: "g"')

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


class TestBlokkHorgonyUtan:
    """A fejlécre horgonyzott eset (#2540): `function f() { … }`."""

    _FORRAS = """
    Item {
        Elozo { text: "elozo" }
        function lepj() {
            // egy hosszú indoklás, ami a rögzített ablakot kicsúsztatná
            if (x) { melyebb() }
            return korbe()
        }
        Kovetkezo { text: "kovetkezo" }
    }
    """

    def test_a_fejlec_UTANI_blokkot_adja(self):
        from tests.support.qml_blokk import blokk_horgony_utan

        blokk = blokk_horgony_utan(self._FORRAS, "function lepj()")
        assert "return korbe()" in blokk
        assert "elozo" not in blokk, "a BEFOGLALÓ blokkot adta vissza"
        assert "kovetkezo" not in blokk, "átcsúszott a szomszédra"

    def test_a_BEAGYAZOTT_blokk_bennemarad(self):
        from tests.support.qml_blokk import blokk_horgony_utan

        assert "melyebb()" in blokk_horgony_utan(
            self._FORRAS, "function lepj()"
        )

    def test_a_KOMMENTBE_irt_emlites_NEM_horgony(self):
        """Mérve a #2540-ben: a `test_shift_csempek_2146.py` horgonya egy
        komment-említésre esett, és a próba a valódi kezelő helyett egy
        egészen más blokkot mért — zölden, örökre."""
        from tests.support.qml_blokk import blokk_horgony_utan

        forras = (
            "// az onValtozott kezelő hátralévő része\n"
            "Item { valami: 1 }\n"
            "onValtozott: {\n    igaziHivas()\n}\n"
        )
        assert "igaziHivas()" in blokk_horgony_utan(forras, "onValtozott")

    def test_nyito_zarojel_nelkul_BUKIK(self):
        from tests.support.qml_blokk import blokk_horgony_utan

        with pytest.raises(AssertionError, match="nincs nyitó"):
            blokk_horgony_utan('text: "x"', 'text: "x"')

    def test_zaratlan_blokkra_BUKIK(self):
        from tests.support.qml_blokk import blokk_horgony_utan

        with pytest.raises(AssertionError, match="nem záródik"):
            blokk_horgony_utan("function f() {\n  a()\n", "function f()")


class TestHivasArgumentumai:
    """Az „eljut-e az érték a hívásig?" állítás határa a `( … )` (#2540)."""

    _FORRAS = """
    ctl.masikHivas(a, b, mertErtek)
    ctl.celHivas(
        elso, masodik,
        harmadik)
    ctl.harmadikHivas(mertErtek)
    """

    def test_a_TELJES_tobbsoros_argumentumlistat_adja(self):
        from tests.support.qml_blokk import hivas_argumentumai

        assert "harmadik" in hivas_argumentumai(self._FORRAS, "ctl.celHivas")

    def test_a_SZOMSZED_hivas_argumentuma_NEM_szamit(self):
        """Ez a lényeg: rögzített ablakkal egy MÁSIK hívásnak átadott érték
        is „bizonyította" volna a bekötést."""
        from tests.support.qml_blokk import hivas_argumentumai

        assert "mertErtek" not in hivas_argumentumai(
            self._FORRAS, "ctl.celHivas"
        )

    def test_a_BEAGYAZOTT_zarojel_nem_zar_koran(self):
        from tests.support.qml_blokk import hivas_argumentumai

        assert hivas_argumentumai("f(g(1), 2)", "f") == "g(1), 2"

    def test_zaratlan_zarojelre_BUKIK(self):
        from tests.support.qml_blokk import hivas_argumentumai

        with pytest.raises(AssertionError, match="nem záródik"):
            hivas_argumentumai("f(a, b", "f")


class TestASorrendKotott:
    """Előbb VÁGNI, csak utána laposítani (#2540)."""

    _FORRAS = (
        "Gomb {\n  // magyarázat: MIÉRT nincs ikonja\n"
        '  objectName: "g"\n  ToolTip.text: qsTr(\n      "x")\n}\n'
        "Masik { y: 1 }\n"
    )

    def test_a_LAPOSITOTT_forrason_a_kivago_BUKIK(self):
        """Egy sorba fűzve az első `//` a szöveg VÉGÉIG nyel el mindent —
        a kivágónak ezt hangosan kell jeleznie, nem némán rossz blokkot
        adnia. (Mérve a #2540-ben: két őr adta be neki a `" ".join(...)`
        alakot.)"""
        from tests.support.qml_blokk import blokk_horgonyra

        laposított = " ".join(self._FORRAS.split())
        with pytest.raises(AssertionError, match="nincs meg"):
            blokk_horgonyra(laposított, 'objectName: "g"')

    def test_VAGAS_utan_laposítva_helyes(self):
        from tests.support.qml_blokk import blokk_horgonyra

        blokk = " ".join(
            blokk_horgonyra(self._FORRAS, 'objectName: "g"').split()
        )
        assert 'ToolTip.text: qsTr( "x")' in blokk
        assert "y: 1" not in blokk


class TestIdezojelesKapcsosZarojel2575:
    """A sztringben álló `{` NEM zárójel — enélkül a mérő elcsúszik.

    Mérve a #2575-ben: a `blokk_horgonyra` egy `text: "{ jel"` kötésű
    elemre „a blokk nem záródik" hibát adott, pedig a forrás helyes. A
    másik irány a veszélyesebb: kiegyensúlyozott ál-zárójelekkel némán
    RÖVIDEBB blokkot vágott volna — és a rá épülő őrök egy meglévő sort
    láttak volna hiányzónak.
    """

    _FORRAS = """
Item {
    objectName: "cel"
    text: "nyito { jel"
    width: 10
}
Item {
    objectName: "masik"
    width: 20
}
"""

    def test_a_sztringbeli_nyito_zarojel_nem_szamit(self):
        from tests.support.qml_blokk import blokk_horgonyra

        blokk = blokk_horgonyra(self._FORRAS, 'objectName: "cel"')
        assert "width: 10" in blokk
        assert "masik" not in blokk

    def test_a_sztringbeli_zaro_zarojel_sem(self):
        from tests.support.qml_blokk import blokk_horgonyra

        forras = self._FORRAS.replace('"nyito { jel"', '"zaro } jel"')
        blokk = blokk_horgonyra(forras, 'objectName: "cel"')
        assert "width: 10" in blokk
        assert "masik" not in blokk

    def test_a_hivas_argumentumai_is_atugorja(self):
        from tests.support.qml_blokk import hivas_argumentumai

        forras = 'onClicked: ment(")", elem.path)\nmas: 1'
        assert "elem.path" in hivas_argumentumai(forras, "ment")


class TestElemTipusa2575:
    _FORRAS = """
PicasaMenuItem {
    objectName: "elso"
}
Rectangle {
    objectName: "masodik"
}
"""

    def test_a_tipusnevet_adja(self):
        from tests.support.qml_blokk import elem_tipusa

        assert elem_tipusa(self._FORRAS, 'objectName: "elso"') == "PicasaMenuItem"
        assert elem_tipusa(self._FORRAS, 'objectName: "masodik"') == "Rectangle"

    def test_a_SZOMSZED_tipusa_nem_szamit(self):
        """A régi alak (`forras[:kezdet][-200:]`) a szomszéd nevét is
        elfogadta — ez a próba pont azt zárja ki."""
        from tests.support.qml_blokk import elem_tipusa

        assert elem_tipusa(self._FORRAS, 'objectName: "masodik"') != "PicasaMenuItem"


class TestTulajdonsagErteke2575:
    _FORRAS = """
Item {
    ToolTip.text: offline
        ? path + qsTr("nem elérhető")
        : path
    ToolTip.visible: hovered
    width: 10
}
"""

    def test_a_tobbsoros_kotest_egyben_adja(self):
        from tests.support.qml_blokk import tulajdonsag_erteke

        ertek = tulajdonsag_erteke(self._FORRAS, "ToolTip.text")
        assert "offline" in ertek and "nem elérhető" in ertek

    def test_a_KOVETKEZO_tulajdonsagot_mar_nem(self):
        """Ha beleérne, az őr a szomszéd kötésével „bizonyítana"."""
        from tests.support.qml_blokk import tulajdonsag_erteke

        ertek = tulajdonsag_erteke(self._FORRAS, "ToolTip.text")
        assert "hovered" not in ertek
        assert "width" not in ertek


class TestElozoKomment2575:
    _FORRAS = """
// elso indoklas
Item {
    objectName: "elso"
}

// masodik indoklas
// ket soros
Item {
    objectName: "masodik"
}
"""

    def test_az_ELEM_folotti_tombot_adja(self):
        from tests.support.qml_blokk import elozo_komment

        szoveg = elozo_komment(self._FORRAS, 'objectName: "masodik"')
        assert "masodik indoklas" in szoveg and "ket soros" in szoveg

    def test_a_SZOMSZED_indoklasa_nem_szamit(self):
        """A régi alak (`forras[hely - 1400:][:2200]`) a fentebbi elem
        indoklását is elfogadta volna."""
        from tests.support.qml_blokk import elozo_komment

        assert "elso indoklas" not in elozo_komment(
            self._FORRAS, 'objectName: "masodik"'
        )

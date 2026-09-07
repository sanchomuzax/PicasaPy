"""A blokk-kivágó saját őrei (#2493).

⚠️ Ez MÉRŐESZKÖZ: több forrás-szintű őr épül rá. Ha némán rosszat vág ki,
azok az őrök hallgatnak olyankor is, amikor jelezniük kellene — a hibás
mérő rosszabb, mint a hiányzó.
"""

from __future__ import annotations

import pytest

from tests.support.qml_blokk import (
    blokk_horgonyra,
    blokk_tartomanyok,
    blokkok_tipusra,
    kommentek_nelkul,
)


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


class TestBlokkokTipusra2613:
    """A felsoroló mérő (#2613) — öt teszt saját párosítóját váltja ki.

    A #1600 mérése mutatta meg, miért nem elég a sor-alapú keresés: a
    `TrayBar` és a `PhotoViewer` `source:` kötése NÉGY soros ternárius, és
    a sor-alapú első változat épp azt a hármat nem találta meg, ami a
    tulajdonos képernyőjén a rács mellett látszik.
    """

    _FORRAS = """
Item {
    Image {
        objectName: "elso"
        source: "a.png"
    }
    Rectangle {
        Image {
            objectName: "masodik"
            text: "{ nem zarojel"
        }
    }
}
Image { objectName: "harmadik" }
"""

    def test_mindet_felsorolja(self):
        from tests.support.qml_blokk import blokkok_tipusra

        blokkok = blokkok_tipusra(self._FORRAS, "Image")
        assert len(blokkok) == 3
        nevek = [b for _, b in blokkok]
        assert any('"elso"' in b for b in nevek)
        assert any('"masodik"' in b for b in nevek)
        assert any('"harmadik"' in b for b in nevek)

    def test_a_BEAGYAZOTT_blokkot_sem_hagyja_ki(self):
        """A `masodik` egy `Rectangle`-ben ül — a naiv, felső szintre
        korlátozott felsorolás kihagyná."""
        from tests.support.qml_blokk import blokkok_tipusra

        assert any('"masodik"' in b
                   for _, b in blokkok_tipusra(self._FORRAS, "Image"))

    def test_a_sztringbeli_zarojel_nem_csusztat(self):
        from tests.support.qml_blokk import blokkok_tipusra

        masodik = next(b for _, b in blokkok_tipusra(self._FORRAS, "Image")
                       if '"masodik"' in b)
        assert masodik.rstrip().endswith("}")
        assert "harmadik" not in masodik

    def test_a_sorszam_visszakereshetove_teszi(self):
        from tests.support.qml_blokk import blokkok_tipusra

        sorszamok = [n for n, _ in blokkok_tipusra(self._FORRAS, "Image")]
        assert sorszamok == sorted(sorszamok)
        assert all(n > 0 for n in sorszamok)

    def test_MAS_tipusra_nem_illeszkedik(self):
        """A `PicasaImage` nem `Image` — a szóhatár őrzi."""
        from tests.support.qml_blokk import blokkok_tipusra

        forras = 'PicasaImage {\n    objectName: "nem ez"\n}\n'
        assert blokkok_tipusra(forras, "Image") == []


class TestBlokkTartomanyok:
    """#2613 — a felsoroló ELTOLÁS-alakja: „ezen a blokkon BELÜL van?"

    A `blokkok_tipusra` a szöveget adja vissza; az #1719 állításának
    viszont a HELY kell: egy másik találat egy `DeferredDialog { … }`
    tartományba esik-e. Az #1719 első változata 400 karakterrel nézett
    vissza, és mutációs próbán megbukott — a szomszéd blokk
    `sourceComponent`-je a látókörbe esett.
    """

    _FORRAS = """
Item {
    // ez a komment ELTOLNA, ha nem vágnánk ki
    Doboz {
        objectName: "elso"
        text: "{ nem zarojel"
        Belso { objectName: "beagyazott" }
    }
    Masik { objectName: "kivul" }
    Doboz { objectName: "masodik" }
}
"""

    def _tiszta(self) -> str:
        return kommentek_nelkul(self._FORRAS)

    def test_a_tartomanyok_a_TISZTITOTT_forrasra_illenek(self):
        """A hívó ugyanazon a szövegen keres, amin a tartományok készültek."""
        tiszta = self._tiszta()
        for kezdet, vege in blokk_tartomanyok(self._FORRAS, "Doboz"):
            assert tiszta[kezdet:].startswith("Doboz")
            assert tiszta[vege] == "}"

    def test_a_BELUL_levo_talalatot_belulnek_mondja(self):
        tiszta = self._tiszta()
        tartomanyok = blokk_tartomanyok(self._FORRAS, "Doboz")
        hely = tiszta.index('"beagyazott"')
        assert any(k < hely < v for k, v in tartomanyok)

    def test_a_KIVUL_levo_talalatot_nem_mondja_belulnek(self):
        """Ez a mutációs próba lényege: a szomszéd blokk nem szívhatja be."""
        tiszta = self._tiszta()
        tartomanyok = blokk_tartomanyok(self._FORRAS, "Doboz")
        hely = tiszta.index('"kivul"')
        assert not any(k < hely < v for k, v in tartomanyok)

    def test_a_sztringbeli_zarojel_nem_csusztat(self):
        """A `text: "{ nem zarojel"` nem nyithat új mélységet."""
        tiszta = self._tiszta()
        elso = next(iter(blokk_tartomanyok(self._FORRAS, "Doboz")))
        assert '"kivul"' not in tiszta[elso[0]:elso[1]]

    def test_mindet_megtalalja(self):
        assert len(blokk_tartomanyok(self._FORRAS, "Doboz")) == 2

    def test_ugyanazt_hatarolja_mint_a_szoveges_alak(self):
        """A két alak nem csúszhat szét — a `blokkok_tipusra` erre épül."""
        tiszta = self._tiszta()
        szoveges = [b for _, b in blokkok_tipusra(self._FORRAS, "Doboz")]
        eltolasos = [
            tiszta[tiszta.index("{", k):v + 1]
            for k, v in blokk_tartomanyok(self._FORRAS, "Doboz")
        ]
        assert szoveges == eltolasos


class TestSorszamHuseg:
    """#2613 — a felsorolás sorszáma az EREDETI forrásra hivatkozzon.

    A `kommentek_nelkul` a `/* … */` blokkot korábban NYOMTALANUL vágta ki,
    a sortöréseivel együtt. Ettől minden utána következő blokk sorszáma
    elcsúszott, és a lelet („`Main.qml:412` névtelen tétel") rossz sorra
    mutatott. A sorszám nem díszítés: az őr üzenetében ez az egyetlen
    fogódzó, amivel a fejlesztő megtalálja a hibás elemet.
    """

    _FORRAS = """Item {
    /* egy
       harom
       soros
       blokk-komment */
    Doboz { objectName: "utana" }
}
"""

    def test_a_blokk_komment_nem_csusztatja_a_sorszamot(self):
        eredeti_sor = next(
            i + 1
            for i, sor in enumerate(self._FORRAS.splitlines())
            if '"utana"' in sor
        )
        (sorszam, _blokk), = blokkok_tipusra(self._FORRAS, "Doboz")
        assert sorszam == eredeti_sor, (
            f"a sorszám {sorszam}, az eredeti forrásban {eredeti_sor} — a "
            "blokk-komment kivágása elcsúsztatta"
        )

    def test_a_komment_tartalma_tovabbra_sem_szamit(self):
        """A sortörések megtartása nem hozhatja vissza a komment SZÖVEGÉT."""
        assert "harom" not in kommentek_nelkul(self._FORRAS)

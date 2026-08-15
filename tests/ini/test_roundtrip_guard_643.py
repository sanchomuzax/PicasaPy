"""#643 — ROUND-TRIP ŐR: a Picasa által elvetett lánc nem juthat a lemezre.

A #643 kutatói szála bizonyította (dekompilációból ÉS hét valódi
Picasa-exporton mérve, ld. `docs/specs/picasa-ini-format.md` „A `filters=`
lánc bejárója az első hibás tagnál MEGÁLL"), hogy az eredeti Picasa
lánc-bejárója az első hibás tagnál megáll, és onnantól a lánc hátralévő
része **egyáltalán nem fut le**. Három hibamód viselkedik azonosan:

1. ismeretlen szűrőnév (`nincsilyen=1;bw=1;` → a `bw` sem fut le),
2. rossz (túl sok) paraméterszám (`grain2=1,0.5;bw=1;` → semmi),
3. hiányzó `=` (`sepia;bw=1;` → semmi).

Ez a teszt az ŐRT állítja: az ini-írás egyetlen kapuján (`IniDocument.
with_value`) nem mehet ki olyan lánc, amely a fentiek miatt a Picasában
némán elhalna — kivéve, ha a hibás tag MÁR OTT VOLT a kulcs előző
értékében (azt a round-trip elv szerint bitre pontosan megőrizzük, de
naplózzuk).
"""

from __future__ import annotations

import logging

import pytest

from picasapy.ini.document import parse_document
from picasapy.ini.filter_guard import (
    DefectKind,
    guard_chain_write,
    inspect_chain,
    is_chain_key,
)
from picasapy.ini.filter_registry import FilterWriteError
from picasapy.ini.io import load_document, update_document

_SECTION = "kep.jpg"


def _doc_with_chain(value: str | None = None):
    """Egyszekciós dokumentum, opcionálisan meglévő `filters=` lánccal."""
    text = f"[{_SECTION}]\nstar=yes\n"
    if value is not None:
        text += f"filters={value}\n"
    return parse_document(text)


class TestLancVizsgalat:
    """A három mért hibamód felismerése (`inspect_chain`)."""

    def test_ismeretlen_nev(self):
        defects = inspect_chain("nincsilyen=1;bw=1;")
        assert [d.kind for d in defects] == [DefectKind.UNKNOWN_NAME]
        assert defects[0].entry == "nincsilyen=1"
        assert defects[0].index == 0

    def test_tul_sok_parameter(self):
        defects = inspect_chain("grain2=1,0.500000;bw=1;")
        assert [d.kind for d in defects] == [DefectKind.TOO_MANY_PARAMS]

    def test_hianyzo_egyenlosegjel(self):
        defects = inspect_chain("sepia;bw=1;")
        assert [d.kind for d in defects] == [DefectKind.MISSING_EQUALS]

    def test_helyes_lanc_tiszta(self):
        assert inspect_chain("sepia=1;bw=1;crop64=1,45930000ba03defe;") == ()

    def test_ures_lanc_tiszta(self):
        assert inspect_chain("") == ()

    def test_a_hibas_tag_utani_tagok_is_jelolve(self):
        """A bejáró megáll, tehát a hibás tag UTÁNI tagok sem futnak le —
        ezt a hibaüzenetnek ki kell mondania (ez a #643 lényege)."""
        defects = inspect_chain("nincsilyen=1;bw=1;sepia=1;")
        assert defects[0].lost_entries == ("bw=1", "sepia=1")


class TestKulcsFelismeres:
    def test_filters_es_redo_lanc_kulcs(self):
        assert is_chain_key("filters")
        assert is_chain_key("FILTERS")
        assert is_chain_key("redo")

    def test_mas_kulcs_nem(self):
        assert not is_chain_key("caption")
        assert not is_chain_key("crop")


class TestIroKapu:
    """A `guard_chain_write` döntése: kivétel vs. naplózott megőrzés."""

    def test_ujonnan_keletkezo_hiba_kivetel(self):
        with pytest.raises(FilterWriteError) as hiba:
            guard_chain_write("filters", "nincsilyen=1;bw=1;", None)
        assert "nincsilyen=1" in str(hiba.value)

    def test_meglevo_hibas_tag_megorizheto(self, caplog):
        """A már a fájlban lévő hibás tagot NEM dobjuk el (adatvesztés lenne),
        de nem is megy ki némán: naplózzuk."""
        with caplog.at_level(logging.WARNING):
            tolerated = guard_chain_write(
                "filters", "nincsilyen=1;sepia=1;", "nincsilyen=1;"
            )
        assert [d.entry for d in tolerated] == ["nincsilyen=1"]
        assert "nincsilyen=1" in caplog.text

    def test_meglevo_tag_megvaltoztatasa_mar_kivetel(self):
        with pytest.raises(FilterWriteError):
            guard_chain_write("filters", "nincsilyen=1,2;", "nincsilyen=1;")

    def test_nem_lanc_kulcsra_nem_szol_bele(self):
        assert guard_chain_write("caption", "sepia;bw", None) == ()


class TestDokumentumKapu:
    """Az őr a KÖZÖS írási kapun ül — semmilyen hívó nem kerülheti meg."""

    @pytest.mark.parametrize(
        "chain",
        [
            "nincsilyen=1;bw=1;",  # ismeretlen név
            "grain2=1,0.500000;bw=1;",  # rossz paraméterszám
            "sepia;bw=1;",  # hiányzó `=`
        ],
    )
    def test_hibas_lanc_nem_irhato(self, chain):
        document = _doc_with_chain()
        with pytest.raises(FilterWriteError):
            document.with_value(_SECTION, "filters", chain)

    def test_hibas_redo_lanc_sem_irhato(self):
        document = _doc_with_chain()
        with pytest.raises(FilterWriteError):
            document.with_value(_SECTION, "redo", "nincsilyen=1;")

    def test_hibas_lanc_uj_szekcioba_sem_irhato(self):
        document = _doc_with_chain()
        with pytest.raises(FilterWriteError):
            document.with_value("masik.jpg", "filters", "nincsilyen=1;")

    def test_helyes_lanc_atmegy(self):
        document = _doc_with_chain().with_value(_SECTION, "filters", "sepia=1;bw=1;")
        assert document.section(_SECTION).get("filters") == "sepia=1;bw=1;"

    def test_meglevo_hibas_tag_megorzese_atmegy(self):
        """Round-trip elv: amit nem mi rontottunk el, azt nem dobjuk el."""
        document = _doc_with_chain("Ismeretlen42=1;")
        updated = document.with_value(_SECTION, "filters", "Ismeretlen42=1;sepia=1;")
        assert updated.section(_SECTION).get("filters") == "Ismeretlen42=1;sepia=1;"


class TestAtviteliCsatorna:
    """`carried=True`: a MÁSHONNAN átvitt lánc nem szerzőség (#152/#426/#644).

    A beillesztés, annak visszavonása, a mentés `redo=` átforgatása és a
    napló-visszatöltése változatlanul HORDOZ egy láncot. Az ott lévő idegen
    tag nem most keletkezik — eldobni adatvesztés, visszautasítani a
    felhasználó munkájának eldobása lenne. Az őr ilyenkor naplóz, de átenged.
    """

    def test_atvitt_lanc_atmegy(self, caplog):
        document = _doc_with_chain()
        with caplog.at_level(logging.WARNING):
            updated = document.with_value(
                "masik.jpg", "filters", "Ismeretlen42=1;sepia=1;", carried=True
            )
        assert updated.section("masik.jpg").get("filters") == "Ismeretlen42=1;sepia=1;"
        assert "Ismeretlen42=1" in caplog.text

    def test_atvitel_sem_nema(self, caplog):
        """Az átvitel NEM kapcsolja ki az őrt — a hiba naplóba kerül."""
        with caplog.at_level(logging.WARNING):
            defects = guard_chain_write("filters", "sepia;", None, carried=True)
        assert [d.kind for d in defects] == [DefectKind.MISSING_EQUALS]
        assert caplog.records

    def test_alapertelmezes_szigoru(self):
        """A `carried` nem szivároghat el: alapból minden út szigorú."""
        document = _doc_with_chain()
        with pytest.raises(FilterWriteError):
            document.with_value("masik.jpg", "filters", "Ismeretlen42=1;")


class TestLemezreNemJutKi:
    """A jegy tényleges követelménye: a hibás lánc nem éri el a FÁJLT."""

    def test_a_fajl_erintetlen_marad(self, tmp_path):
        ini_path = tmp_path / ".picasa.ini"
        # CRLF sorvégek szándékosan: a fájlnak BÁJTRA érintetlennek kell
        # maradnia, ezért az összehasonlítás is bájt-szintű (a szöveges
        # olvasás univerzális sorvég-fordítása elfedné a különbséget).
        eredeti = f"[{_SECTION}]\r\nstar=yes\r\nfilters=sepia=1;\r\n".encode()
        ini_path.write_bytes(eredeti)

        with pytest.raises(FilterWriteError):
            update_document(
                ini_path,
                lambda doc: doc.with_value(_SECTION, "filters", "nincsilyen=1;bw=1;"),
                backup=True,
            )

        assert ini_path.read_bytes() == eredeti
        assert load_document(ini_path).section(_SECTION).get("filters") == "sepia=1;"

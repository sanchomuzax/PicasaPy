"""A nyelvi ellenőrzés kivonatolójának próbasora.

A hunspellt nem igényli: a szöveg-kivonatolást és a szó-darabolást méri, mert
a kalibráláskor (2026-08-19) minden vaklárma ONNAN jött, nem a szótárból.
"""

import importlib.util
import pathlib

import pytest

_UT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "nyelvi_ellenorzes.py"
_spec = importlib.util.spec_from_file_location("nyelvi_ellenorzes", _UT)
ne = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ne)


def test_gyorsbillentyu_jelolo_nem_vagja_ketté_a_szot():
    """S&amp;zerkesztés -> 'Szerkesztés', nem 'S' + 'zerkesztés'."""
    assert "Szerkesztés" in ne._szavak(["S&amp;zerkesztés"])
    assert "zerkesztés" not in ne._szavak(["S&amp;zerkesztés"])


def test_gyorsbillentyu_nyers_jellel_is():
    assert "Megjelenítése" in ne._szavak(["M&egjelenítése"])


def test_helykitolto_nem_kerul_a_szavak_koze():
    szavak = ne._szavak(["%1 kép másolása ide: %2", "{0} elem kijelölve"])
    assert all(not s.startswith("%") and not s.startswith("{") for s in szavak)
    assert "másolása" in szavak


def test_csak_a_hozzaadott_sorok_szamitanak():
    diff = (
        "+++ b/a.qml\n"
        '+    text: "Új felirat"\n'
        '-    text: "Régi felirat"\n'
        '     text: "Változatlan felirat"\n'
    )
    szovegek = ne.magyar_szovegek(diff)
    assert "Új felirat" in szovegek
    assert "Régi felirat" not in szovegek
    assert "Változatlan felirat" not in szovegek


def test_kodkomment_nem_felirat():
    diff = '+++ b/a.py\n+    x = 1  # magyar kommentár ékezettel\n'
    assert ne.magyar_szovegek(diff) == []


def test_forditas_elemek_kivonatolodnak():
    diff = "+++ b/hu.ts\n+        <translation>Mappa megjelenítése</translation>\n"
    assert ne.magyar_szovegek(diff) == ["Mappa megjelenítése"]


def test_ekezet_nelkuli_szoveg_nem_erdekel():
    diff = '+++ b/a.qml\n+    text: "Open file"\n'
    assert ne.magyar_szovegek(diff) == []


def test_szotar_beolvasasa():
    szavak = ne._sajat_szavak()
    assert "vörösszem" in szavak  # kisbetűsítve tárolódik
    assert "# kommentsor" not in szavak


@pytest.mark.parametrize("szo", ["Többválaszás", "fülöt", "orden"])
def test_ismert_hibak_a_probaban_szerepelnek(szo):
    """Az öntesz a saját, dokumentált hibáinkat méri — ne kophasson ki."""
    assert szo in ne.PROBA_HIBAS

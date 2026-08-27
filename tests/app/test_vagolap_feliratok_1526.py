"""#1526: a vágólap-parancsok MAGYAR feliratai a HIVATALOS szövegek legyenek.

A feliratokat nem mi fogalmazzuk: a Picasa saját magyar erőforrásaiból valók.
A főmenüé a `docs/specs/picasa-menu-parancsok.csv` `eMenuEdit` sorai, a
szövegmező-helyimenüé a `stringres-en-hu.tsv` `Address` névtere (a #1526
jegyben *megerősített* fokozattal).

A QML-funkcionális teszt nem tudja ezt mérni: a fixture nem telepít
`QTranslator`-t, tehát ott a `qsTr()` az ANGOL forrássztringet adja. Ez a
fájl ezért közvetlenül a `picasapy_hu.ts`-t olvassa — a #1527 mintája.

## Miért van `&` a feliratokban

Az eredeti feliratok gyorsbillentyű-jelölővel érkeznek (`Cu&t` → `&Kivágás`),
és a Qt/QML ugyanezt az `&`-konvenciót használja: a `MenuItem` mnemonik-tudatos
címkét rajzol, tehát az ampersand aláhúzást jelöl, nem betűt (#757). A jelölő
elhagyása néma funkcióvesztés volna: a billentyűzetes navigáció szűnne meg.

## Miért csak a MAGYAR oldalon van `&` a szövegmező-menüben

A főmenü ANGOL alakja is dokumentált (`Cu&t`, `&Copy`, `&Paste`), ezért ott a
forrássztring is a hivatalos alakot követi. Az `Address` névtér angol
oszlopát viszont NEM mértük — csak a magyart. Találgatott angol mnemonikot
nem írunk a forrásba; a magyar oldal a hivatalos szöveg, és a felhasználó azt
látja.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_TS_PATH = (
    Path(__file__).resolve().parents[2]
    / "src" / "picasapy" / "app" / "i18n" / "picasapy_hu.ts"
)

#: (kontextus, forrássztring) -> a HIVATALOS magyar felirat.
HIVATALOS: dict[tuple[str, str], str] = {
    # -- eMenuEdit (docs/specs/picasa-menu-parancsok.csv)
    ("PicasaMenuBar", "Cu&t"): "&Kivágás",
    ("PicasaMenuBar", "&Copy"): "&Másolás",
    ("PicasaMenuBar", "&Paste"): "&Beillesztés",
    ("PicasaMenuBar", "Copy Text"): "Szöveg másolása",
    ("PicasaMenuBar", "Paste Text"): "Szöveg beillesztése",
    # -- Address (stringres-en-hu.tsv, a #1526 jegy táblája)
    ("TextFieldContextMenu", "Undo"): "&Visszavonás",
    ("TextFieldContextMenu", "Cut"): "&Kivágás",
    ("TextFieldContextMenu", "Copy"): "&Másolás",
    ("TextFieldContextMenu", "Paste"): "&Beillesztés",
    ("TextFieldContextMenu", "Delete"): "&Törlés",
    ("TextFieldContextMenu", "Select All"): "Az ö&sszes kijelölése",
    ("TextFieldContextMenu", "Auto-Complete"): "&Automatikus kitöltés",
}


def _forditasok() -> dict[tuple[str, str], str]:
    gyoker = ET.parse(_TS_PATH).getroot()
    talalt: dict[tuple[str, str], str] = {}
    for context in gyoker.findall("context"):
        nev = (context.findtext("name") or "").strip()
        for message in context.findall("message"):
            forras = (message.findtext("source") or "").strip()
            forditas = message.find("translation")
            talalt[(nev, forras)] = (
                forditas.text or "" if forditas is not None else ""
            )
    return talalt


@pytest.fixture(scope="module")
def forditasok():
    return _forditasok()


@pytest.mark.parametrize(("kulcs", "vart"), sorted(HIVATALOS.items()))
def test_a_hivatalos_felirat_szerepel(forditasok, kulcs, vart):
    kontextus, forras = kulcs
    assert kulcs in forditasok, (
        f"nincs fordítás: {kontextus} / {forras!r} — "
        "a menüpont angolul jelenne meg magyar nyelven"
    )
    assert forditasok[kulcs] == vart


def test_a_szovegmezo_menu_MIND_A_HET_tetelenek_van_mnemonikja(forditasok):
    """Az `Address` menü hét tétele mind gyorsbillentyű-jelölővel érkezik —
    ha egyből kimarad, a billentyűzetes navigáció ott elakad."""
    hiany = [
        forras
        for (kontextus, forras), felirat in forditasok.items()
        if kontextus == "TextFieldContextMenu" and "&" not in felirat
    ]
    assert hiany == [], f"mnemonik nélküli feliratok: {hiany}"


def test_a_regi_mnemonik_nelkuli_alakok_eltuntek(forditasok):
    """Visszavonás-őr: ha valaki „egyszerűsítésként" leszedi az
    ampersandokat, ez bukik (a #1045 tanulsága: a visszavonáshoz ellenkező
    irányú őr kell)."""
    tiltott = {
        ("PicasaMenuBar", "Cut"),
        ("PicasaMenuBar", "Copy"),
        ("PicasaMenuBar", "Paste"),
    }
    maradt = sorted(kulcs for kulcs in tiltott if kulcs in forditasok)
    assert maradt == [], (
        f"mnemonik nélküli RÉGI forrássztringek maradtak a .ts-ben: {maradt}"
    )

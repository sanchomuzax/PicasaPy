"""#1526: a vágólap-parancsok MAGYAR feliratai a HIVATALOS szövegek legyenek.

A feliratokat nem mi fogalmazzuk: a Picasa saját magyar erőforrásaiból valók.
A főmenüé a `docs/specs/picasa-menu-parancsok.csv` `eMenuEdit` sorai, a
szövegmező-helyimenüé a `stringres-en-hu.tsv` `Address` névtere (a #1526
jegyben *megerősített* fokozattal).

A QML-funkcionális teszt nem tudja ezt mérni: a fixture nem telepít
`QTranslator`-t, tehát ott a `qsTr()` az ANGOL forrássztringet adja. Ez a
fájl ezért közvetlenül a `picasapy_hu.ts`-t olvassa — a #1527 mintája.

## Miért van `&` a helyi menüben, és miért NINCS a főmenüben

Az eredeti feliratok szinte mind gyorsbillentyű-jelölővel érkeznek — a
menü-CSV 177 angol feliratából **141**, a magyarból **139** tartalmaz `&`-et.
A PicasaPy viszont ezt **eddig csak a menük CÍMÉRE** vette át: a
`PicasaMenuBar.qml` 142 `qsTr()` felirata közül a #1526 előtt kilencben volt
`&` — a nyolc menücím (`&File`, `&Edit`, …) és az `E&xit`. A tételek szintjén
tehát a projekt következetesen mnemonik NÉLKÜL dolgozik; a #1527 tegnap a
`Save As...`-t is így vette át, holott a CSV-ben `Save &As...` áll.

Emiatt a #1526 első köre TÉVEDETT, amikor a `Cut`/`Copy`/`Paste` tételekre
egyedül rátette az ampersandot: 133 tétel közül háromnak lett aláhúzása, a
menü Alt-navigációja ettől nem lett használható, csak egyenetlen. A
mnemonikok menüszintű bevezetése ÖNÁLLÓ, menü-egészre kiterjedő munka (133
felirat + minden helyi menü + a `.ts`), nem a vágólap-jegy mellékhatása.

A **szövegmező-helyimenü** más eset, és ezért marad mnemonikos: ott
MIND A HÉT tétel hivatalos magyar felirata `&`-es (a jegy tételes táblája),
tehát a menü önmagában teljes és következetes — a billentyűs navigáció
végig működik benne.

Az `Address` névtér ANGOL oszlopát nem mértük, csak a magyart; találgatott
angol mnemonikot nem írunk a forrásba.
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
    # -- eMenuEdit (docs/specs/picasa-menu-parancsok.csv), a projekt
    # tétel-szintű konvenciója szerint mnemonik NÉLKÜL (ld. a docstringet)
    ("PicasaMenuBar", "Cut"): "Kivágás",
    ("PicasaMenuBar", "Copy"): "Másolás",
    ("PicasaMenuBar", "Paste"): "Beillesztés",
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


def test_a_fomenu_tetelei_NEM_kapnak_kulon_mnemonikot(forditasok):
    """Ellenkező irányú őr (#1045 tanulsága).

    A #1526 első köre pont ezt rontotta el: három tételre rátette az
    ampersandot, amitől a menü egyenetlen lett, és a
    `test_qml_menubar_audit` mintaillesztése is elhasalt. Amíg a mnemonikok
    menü-egészre kiterjedő bevezetése meg nem történik (önálló jegy), a
    Szerkesztés menü vágólap-tételei mnemonik NÉLKÜL állnak — ez az őr
    fogja meg, ha valaki megint csak néhányat lát el vele."""
    tiltott = {
        ("PicasaMenuBar", "Cu&t"),
        ("PicasaMenuBar", "&Copy"),
        ("PicasaMenuBar", "&Paste"),
    }
    maradt = sorted(kulcs for kulcs in tiltott if kulcs in forditasok)
    assert maradt == [], (
        "a főmenü vágólap-tételei külön mnemonikot kaptak, a többi 130 tétel "
        f"viszont nem — ettől a menü egyenetlen lesz: {maradt}"
    )

"""A felület betűcsalád-tokenjei a MÉRT családra mutatnak (#3310).

## Miért

A `Theme.uiFamily` és a `Theme.condensedFamily` üres volt, és egyetlen
fogyasztójuk sem akadt: a QML-oldal nem tudott arra a családra hivatkozni,
amit az alkalmazás ténylegesen telepít (`_UI_FONT_FAMILY`, #526 — mérve tíz
felirat képpont-szélességéből). A `condensedFamily` viszont SZÁNDÉKOSAN
marad üres: a `.ytf` normalizált vektora (#2943/#3311) nem ad súlytól
független győztest, tehát keskeny családot nem vezetünk be.

## Mit mér

1. a token értéke MEGEGYEZIK az alkalmazás által telepített családdal
   (nem külön leírt, elcsúszható sztring);
2. a `condensedFamily` üres, és a kód megindokolja;
3. a tokenekre nem épül NÉMA HELYETTESÍTŐ család: a kirajzolt feliraton a
   Qt által ténylegesen FELOLDOTT család ugyanaz, mint a kért;
4. a bizonyíték egy VALÓDI, LÁTHATÓ feliraton áll (`trayInfoText`), nem a
   property értékén.

## Amit NEM mér

A betű képét: hogy a glifák tényleg az eredeti Picasa arányait adják-e —
azt a #526 mérése döntötte el, nem ez az őr. És nem méri azt sem, hogy a
felület TÖBBI felirata is ezt a családot kéri: a globális alkalmazás-betű
adja őket, külön token nélkül.
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtGui import QFontInfo

GYOKER = Path(__file__).resolve().parents[3]
THEME = GYOKER / "src/picasapy/app/qml/PicasaPy/Theme.qml"
TRAYBAR = GYOKER / "src/picasapy/app/qml/PicasaPy/TrayBar.qml"
APPLICATION = GYOKER / "src/picasapy/app/application.py"


def _token(nev: str) -> str:
    forras = THEME.read_text(encoding="utf-8")
    talalat = re.search(
        rf'readonly property string {nev}: "([^"]*)"', forras)
    assert talalat, f"nincs `{nev}` token a Theme.qml-ben"
    return talalat.group(1)


def _telepitett_csalad() -> str:
    forras = APPLICATION.read_text(encoding="utf-8")
    talalat = re.search(r'_UI_FONT_FAMILY = "([^"]+)"', forras)
    assert talalat, "nincs _UI_FONT_FAMILY az application.py-ben"
    return talalat.group(1)


def test_az_uiFamily_a_telepitett_csalad() -> None:
    """Egy forrás: a token nem csúszhat el az alkalmazás betűjétől."""
    assert _token("uiFamily") == _telepitett_csalad()


def test_a_condensedFamily_ures_es_indokolt() -> None:
    assert _token("condensedFamily") == ""
    forras = THEME.read_text(encoding="utf-8")
    kezd = forras.index("A keskeny család SZÁNDÉKOSAN üres")
    indoklas = forras[kezd:kezd + 700]
    assert "#2943" in indoklas or "#3311" in indoklas, (
        "az üresen hagyás indoklása nevezze meg a mérést")


def test_az_ures_tokenre_nem_epul_fogyaszto() -> None:
    """Üres családnévre kötött felirat NÉMÁN a Qt alapértelmezését kapná —
    ami nem ugyanaz, mint a szándékos öröklés."""
    qml_gyoker = THEME.parent.parent
    fogyasztok = [
        ut.name for ut in qml_gyoker.rglob("*.qml")
        if "Theme.condensedFamily" in ut.read_text(encoding="utf-8")
    ]
    assert not fogyasztok, (
        "a `condensedFamily` üres, mégis kötve van: " + ", ".join(fogyasztok))


def test_a_lathato_feliraton_a_MERT_csalad_jelenik_meg(qml_app) -> None:
    """A bizonyíték kirajzolt felirat, nem property-érték."""
    window, _controller, _engine = qml_app
    felirat = window.findChild(object, "trayInfoText")
    assert felirat is not None, "nincs `trayInfoText` a jelenetben"
    assert felirat.property("visible"), "a felirat nem látható"
    assert felirat.property("width") > 0, "a feliratnak nincs szélessége"

    betu = felirat.property("font")
    kert = _telepitett_csalad()
    assert betu.family() == kert, (
        f"a felirat {betu.family()!r} családot kér, nem a mért {kert!r}")
    # A NÉMA HELYETTESÍTÉS ellen: a Qt által FELOLDOTT család is ugyanaz.
    assert QFontInfo(betu).family() == kert, (
        f"a Qt {QFontInfo(betu).family()!r}-ra helyettesített — a mért "
        f"{kert!r} nincs betöltve")


def test_a_traybar_a_tokenre_hivatkozik_nem_a_nevre() -> None:
    """A felirat a tokenen át kérje a családot, ne beégetett sztringgel."""
    forras = TRAYBAR.read_text(encoding="utf-8")
    assert "font.family: Theme.uiFamily" in forras
    assert 'font.family: "Open Sans"' not in forras

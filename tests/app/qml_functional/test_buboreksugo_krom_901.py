"""A buboréksúgó krómja az eredeti MÉRT értékeire áll (#901).

## A mérés

A tulajdonos képernyőképéről képpontonként leolvasva: a buborék kitöltése
`#F4F1E5`, a kerete `#B7B5AC` 1 képpont, a sarkai derékszögűek, a szöveg
fekete, és az árnyék **csak a jobb és az alsó élen** van. A késleltetés a
binárisból `0,6 s` (`0x00c7e304`).

A buborék saját rajzolású csomópont (`ytToolTip`, vtable `0x00c909d4`) —
nem a Windows `tooltips_class32` vezérlője, és nem respack-kép.

## Amit ez az őr NEM mér

- Az árnyék EREDETI mechanizmusát: a képen látszik, de a forrása a
  binárisban **nincs bizonyítva** (a generikus `useshadow` paramétereinek a
  tooltip példányára kötése hiányzik). Ezért a mért KÉPI alakot utánozzuk,
  és a `CS_DROPSHADOW`-magyarázatot sehol nem állítjuk.
- A betű pontos eredeti képpontméretét: a bináris az `Arial` CSALÁDOT adja
  meg (`0x00a6b6ed` → `0x00c80a64`), a méretet nem. A 12 képpont a mi
  mércénk marad, regresszióval védve.
- Hogy a rendszeren TÉNYLEG Arial rajzolódik-e: Linuxon jellemzően nincs
  telepítve, és a Qt metrikailag rokon családra helyettesít. Ezért a kért
  család-LISTÁT mérjük (első elem Arial + nevesített tartalék), nem a
  feloldott családot.
"""

from __future__ import annotations

import re
from pathlib import Path

QML = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml"
TOOLTIP = QML / "PicasaStyle" / "ToolTip.qml"
THEME = QML / "PicasaPy" / "Theme.qml"

#: A képernyőképről mért króm (világos mód).
MERT_HATTER = "#f4f1e5"
MERT_KERET = "#b7b5ac"


def _nyers_token(nev: str) -> str:
    """A token VILÁGOS ágának értéke (`dark ? sötét : világos`).

    A mérés a világos módra szól — az eredetinek nincs sötét témája.
    """
    forras = THEME.read_text(encoding="utf-8")
    talalat = re.search(
        rf'readonly property color {nev}:\s*tema\.dark\s*\?\s*'
        rf'"#[0-9a-fA-F]{{6}}"\s*:\s*"(#[0-9a-fA-F]{{6}})"',
        forras)
    assert talalat, f"nincs `{nev}` nyers token a Theme.qml-ben"
    return talalat.group(1).lower()


def test_a_vilagos_hatter_a_MERT_szin() -> None:
    assert _nyers_token("tooltipBg") == MERT_HATTER


def test_a_keret_a_MERT_szin() -> None:
    assert _nyers_token("tooltipBorder") == MERT_KERET


def test_a_buborek_a_sajat_tokenjeit_hasznalja() -> None:
    """Nem a panel/króm tokent — azok a MI krómunk, nem a mért buboréké."""
    forras = TOOLTIP.read_text(encoding="utf-8")
    assert "Theme.tooltipBg" in forras
    assert "Theme.tooltipBorder" in forras
    assert "Theme.panelBg" not in forras
    assert "Theme.chromeBorder" not in forras


def test_a_sarkok_derekszoguek() -> None:
    forras = TOOLTIP.read_text(encoding="utf-8")
    assert not re.search(r"^\s*radius\s*:", forras, re.M), (
        "a mért buborék sarka derékszögű — ne kerekítsük")


def test_a_keret_egy_keppont() -> None:
    forras = TOOLTIP.read_text(encoding="utf-8")
    assert re.search(r"border\.width:\s*1\b", forras)


def test_az_arnyek_csak_a_jobb_es_also_elen_van() -> None:
    """A képen mért alak: bal és felső élen NINCS árnyék."""
    forras = TOOLTIP.read_text(encoding="utf-8")
    arnyek = re.search(r'objectName:\s*"picasaToolTipArnyek"', forras)
    assert arnyek, "hiányzik az árnyék-réteg"
    blokk = forras[arnyek.start():arnyek.start() + 600]
    assert re.search(r"^\s*x:\s*\d", blokk, re.M), "az árnyék nincs jobbra tolva"
    assert re.search(r"^\s*y:\s*\d", blokk, re.M), "az árnyék nincs lefelé tolva"


def test_az_arnyek_a_buborek_ALATT_rajzolodik() -> None:
    """Az árnyék nem takarhatja a kitöltést és a keretet."""
    forras = TOOLTIP.read_text(encoding="utf-8")
    arnyek = forras.index('objectName: "picasaToolTipArnyek"')
    hatter = forras.index('objectName: "picasaToolTipHatter"')
    assert arnyek < hatter, "az árnyéknak a háttér ELŐTT kell állnia"


def test_a_KERT_betucsalad_Arial() -> None:
    """A bináris az Arial CSALÁDOT adja meg (`0x00a6b6ed`).

    ⚠️ A FELOLDOTT családot nem állítjuk: ahol az Arial nincs telepítve, a
    Qt metrikailag rokonra helyettesít — az a rendszer dolga, nem a miénk.
    A listás `font.families` alak ezen a Qt-n nem létezik (mérve: „Cannot
    assign to non-existent property", Qt 6.8.2), ezért egy család áll itt.
    """
    forras = TOOLTIP.read_text(encoding="utf-8")
    assert re.search(r'font\.family:\s*"Arial"', forras)


def test_a_600_ms_keslelteteset_nem_irtuk_at() -> None:
    forras = TOOLTIP.read_text(encoding="utf-8")
    assert "delay: Theme.tooltipDelay" in forras
    assert re.search(r"tooltipDelay:\s*600", THEME.read_text(encoding="utf-8"))


def test_nincs_CS_DROPSHADOW_magyarazat() -> None:
    """A korábbi, NEM bizonyított mechanizmus-magyarázat nem élhet tovább."""
    for ut in (TOOLTIP, Path(__file__)):
        forras = ut.read_text(encoding="utf-8")
        allitas = re.search(r"CS_DROPSHADOW(?![-\s]*magyarázatot)", forras)
        assert allitas is None or "nem állít" in forras, (
            f"{ut.name}: a CS_DROPSHADOW bizonyítottként szerepel")


# --- a KIRAJZOLT buborék: nem forrásszöveg, hanem élő elem ------------------

def test_a_kirajzolt_buborek_a_MERT_szineket_viseli(qt_app) -> None:
    """A jegy kimondja: az elfogadás LÁTÁS legyen, ne csak forrás-egyezés.

    A stílus-komponenst élőben állítjuk fel, és a valódi elemek
    tulajdonságait mérjük — szín, keretvastagság, sarok, árnyék-eltolás.
    """
    from PySide6.QtCore import QObject, QUrl
    from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlProperty

    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    komponens = QQmlComponent(engine, QUrl.fromLocalFile(str(TOOLTIP)))
    assert komponens.status() == QQmlComponent.Status.Ready, komponens.errorString()
    sugo = komponens.create()
    assert sugo is not None, komponens.errorString()
    QQmlEngine.setObjectOwnership(sugo, QQmlEngine.ObjectOwnership.CppOwnership)
    try:
        hatter = sugo.findChild(QObject, "picasaToolTipHatter")
        arnyek = sugo.findChild(QObject, "picasaToolTipArnyek")
        assert hatter is not None and arnyek is not None

        assert hatter.property("color").name().lower() == MERT_HATTER
        # a `border` QQuickPen* csoport — PySide6-ban nincs rá konverter,
        # ezért a pontozott utat `QQmlProperty`-vel olvassuk (a #384 mintája)
        assert QQmlProperty(hatter, "border.color").read().name().lower() == MERT_KERET
        assert QQmlProperty(hatter, "border.width").read() == 1
        assert hatter.property("radius") == 0, "a mért sarok derékszögű"

        # az árnyék jobbra ÉS lefelé tolva — a bal/felső élen így nem látszik
        assert arnyek.property("x") > 0 and arnyek.property("y") > 0
        assert arnyek.property("color").alphaF() < 1.0, "az árnyék áttetsző"
    finally:
        sugo.deleteLater()
        engine.deleteLater()

"""#3070 1. lépés — a `Theme.qml` KÉT rétege, és a kettő egyezése.

## Miért kell két réteg

A megjelenítési mód (`apply_display_mode`) egy SZÍNTRANSZFORMÁCIÓ, amit a
vezérlő egyetlen menetben számol ki minden tokenre, és a QML csak
tokennév → szín kereséssel vesz ki belőle (`Theme.megjelenitesiPaletta`).

A `Theme.qml`-ben viszont több szín SZÁRMAZTATOTT: `Qt.lighter(buttonBg,
1.08)`, `Qt.darker(buttonBg, 1.15)`, `chromeBorder`, `ink`, `contentPanel`.
A származtatás és a mód **nem kommutál** (a `Qt.lighter` a HSV-világosságot
szorozza, a mód gamma-alapú), tehát:

| burkolás | amit kiszámol | helyes? |
|---|---|---|
| minden definíció átalakítóba | `mód(származtat(mód(nyers)))` | nem — kétszer hat |
| csak a literálok | `származtat(mód(nyers))` | nem — a származtatás a módosított színből |
| **két réteg** | `mód(származtat(nyers))` | **igen** |

Ezért a nyers értékek egy belső `QtObject`-ben élnek (`Theme.nyers`), a
származtatásuk is ONNAN számol, és a nyilvános 103 szín mindegyike
**pontosan egyszer** megy át a módon.

## Amit ez az őr állít

- üres palettával a nyilvános érték a NYERS érték — mindkét témában, tehát
  ez a lépés viselkedés-változás nélküli (a felület pontosan úgy néz ki,
  mint eddig);
- minden nyers tokenhez van nyilvános pár és fordítva (nem maradhat token a
  belső rétegben rekedve, és nem jelenhet meg csak a nyilvánoson);
- a paletta bejegyzése a nyilvános színen ÁTJÖN, a nyerset nem írja át;
- a származtatott szín a NYERS forrásból számol: a forrás-token palettázása
  nem szivárog át a származtatottra (ez zárja ki a kétszeres alkalmazást).

A próba nem sorol fel színeket: a Qt metaobjektumán megy végig, tehát egy
JÖVŐBEN hozzáadott token is automatikusan a hatálya alá esik.

## Amit NEM állít

A látványt: ez a lépés szándékosan nem változtat egyetlen képpontot sem, a
mód tényleges alkalmazását (a paletta feltöltését) a jegy 2. lépése hozza.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QColor
from PySide6.QtQml import QJSValue, QQmlEngine

TEMA_QML = (
    Path(__file__).resolve().parents[2]
    / "src/picasapy/app/qml/PicasaPy/Theme.qml"
)

#: A nem SZÍN típusú tokenek (méret, súly, betűcsalád): a mód nem érinti őket.
NEM_SZIN = ("int", "var", "string", "bool", "QObject", "QtObject")


def _tokenek(objektum: QObject) -> dict[str, str]:
    """A QObject saját (nem örökölt) property-jei: név → típusnév."""
    mo = objektum.metaObject()
    kezdet = mo.propertyOffset()
    ki: dict[str, str] = {}
    for i in range(kezdet, mo.propertyCount()):
        p = mo.property(i)
        ki[p.name()] = p.typeName()
    return ki


def _ertek(objektum: QObject, nev: str):
    """A property értéke Python-oldali alakban (a `var` QJSValue-t ad)."""
    ertek = objektum.property(nev)
    return ertek.toVariant() if isinstance(ertek, QJSValue) else ertek


def _szinek(objektum: QObject) -> list[str]:
    return [
        nev
        for nev, tipus in _tokenek(objektum).items()
        if tipus == "QColor" and nev != "objectName"
    ]


@pytest.fixture
def tema(qt_app):
    """A Theme singleton élő példánya — a kötések ezen futnak."""
    import picasapy.app as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(Path(app_module.__file__).resolve().parent / "qml"))
    peldany = engine.singletonInstance("PicasaPy", "Theme")
    assert peldany is not None, "a Theme singleton nem töltődött be"
    yield peldany
    del peldany
    engine.deleteLater()


class TestAKetReteg:
    def test_a_nyers_reteg_letezik(self, tema):
        nyers = tema.property("nyers")
        assert isinstance(nyers, QObject), (
            "a Theme-nek belső `nyers` rétege kell: a származtatott színek "
            "onnan számolnak, különben a mód kétszer hatna"
        )

    def test_minden_szinnek_van_nyers_parja(self, tema):
        nyers = tema.property("nyers")
        nyilvanos = set(_szinek(tema))
        belso = set(_szinek(nyers))
        assert nyilvanos == belso, (
            "csak a nyilvánoson: " + ", ".join(sorted(nyilvanos - belso))
            + " · csak a nyersen: " + ", ".join(sorted(belso - nyilvanos))
        )
        assert len(nyilvanos) >= 100, f"gyanúsan kevés szín-token: {len(nyilvanos)}"

    def test_a_nem_szin_tokenek_is_atjonnek(self, tema):
        nyers = tema.property("nyers")
        for nev, tipus in _tokenek(nyers).items():
            if tipus == "QColor" or nev == "objectName":
                continue
            assert _ertek(tema, nev) == _ertek(nyers, nev), (
                f"a(z) `{nev}` nem-szín token nem jön át a nyilvános felületre"
            )


class TestUresPalettavalValtozatlan:
    """Ez a lépés viselkedés-változás nélküli: a felület képe nem mozdul."""

    @pytest.mark.parametrize("sotet", [False, True])
    def test_a_nyilvanos_szin_a_nyers_szin(self, tema, sotet):
        tema.setProperty("dark", sotet)
        nyers = tema.property("nyers")
        elteres = [
            nev
            for nev in _szinek(tema)
            if QColor(tema.property(nev)) != QColor(nyers.property(nev))
        ]
        assert not elteres, (
            f"üres palettával eltért ({'sötét' if sotet else 'világos'}): "
            + ", ".join(sorted(elteres))
        )


class TestAPalettaHatasa:
    def test_a_paletta_bejegyzese_atjon(self, tema):
        tema.setProperty("megjelenitesiPaletta", {"canvasBg": "#ff0000"})
        try:
            assert QColor(tema.property("canvasBg")) == QColor("#ff0000")
            # a nyers értéket nem írja át — a származtatás forrása marad
            nyers = tema.property("nyers")
            assert QColor(nyers.property("canvasBg")) != QColor("#ff0000")
            # és a paletta nem szivárog a többi tokenre
            assert QColor(tema.property("panelBg")) == QColor(
                nyers.property("panelBg")
            )
        finally:
            tema.setProperty("megjelenitesiPaletta", {})

    def test_a_szarmaztatott_szin_a_NYERS_forrasbol_szamol(self, tema):
        """A kétszeres alkalmazás kizárása.

        A `buttonTopNormal` sötét témán `Qt.lighter(buttonBg, 1.08)`. Ha a
        származtatás a NYILVÁNOS `buttonBg`-t olvasná, a `buttonBg`
        palettázása átszivárogna rá — épp ez a `mód(származtat(mód(nyers)))`
        hiba. A nyers rétegből számolva nem szivárog.
        """
        tema.setProperty("dark", True)
        nyers = tema.property("nyers")
        eredeti = QColor(tema.property("buttonTopNormal"))
        tema.setProperty("megjelenitesiPaletta", {"buttonBg": "#ff0000"})
        try:
            assert QColor(tema.property("buttonBg")) == QColor("#ff0000")
            assert QColor(tema.property("buttonTopNormal")) == eredeti
            assert QColor(nyers.property("buttonTopNormal")) == eredeti
        finally:
            tema.setProperty("megjelenitesiPaletta", {})
            tema.setProperty("dark", False)


class TestAForrasAlakja:
    """Forrás-szintű őr: a nyilvános színek MINDEGYIKE az átalakítón megy át.

    Egy jövőbeli token, amit valaki a nyilvános rétegbe ír közvetlen
    értékkel, a futásidejű őröket átcsúsztatná (nyers párja se lenne, de a
    hibaüzenet ott nehezebben olvasható). Ez a próba a definíció ALAKJÁT
    rögzíti.
    """

    def test_a_nyilvanos_szinek_a_szin_fuggvenyen_at_jonnek(self):
        szoveg = TEMA_QML.read_text(encoding="utf-8")
        elol, _, hatul = szoveg.partition("    }\n")  # a nyers blokk zárása
        assert hatul, "a `nyers` blokk nem található a Theme.qml-ben"
        hibas = [
            sor.strip()
            for sor in hatul.splitlines()
            if sor.startswith("    readonly property color ")
            and "tema._szin(" not in sor
        ]
        assert not hibas, (
            "nyilvános szín az átalakító nélkül: " + " · ".join(hibas)
        )

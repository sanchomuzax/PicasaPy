"""#2187 — a fejléc KIJELÖLT hatóköre: `confirmsel` és `removesel`.

Az eredetiben a `confirmsug` („Confirm all") és a `confirmsel` („Confirm")
UGYANAZON a 88 × 27-es téglalapon váltakozik (`respack.yt`), ugyanazzal a
kezelővel (`0x00602640`, `push 1` = mind, `push 0` = a kijelöltek). A
`removesel` mért súgója „Remove selected suggestions".

Nálunk a váltás feltétele: a rács kijelölésén van-e e személyre szóló
függő javaslat (`selectedSuggestionCount`, a gazda a
`FaceScanController.personSuggestionIdsForPaths`-ból számolja).

Hivatalos magyar feliratok (`docs/specs/picasa-arcfelismeres.md` 15.):
„Jóváhagyás" · „Kijelölt javaslatok jóváhagyása" · „Kijelölt javaslatok
törlése".

Amit ez a fájl NEM mér: a gomb képi megjelenését (a felirat hossza a
88 képpontos gombban — a „Jóváhagyás" rövidebb, mint a már most is kint
lévő „Az összes jóváhagyása (N)").
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import picasapy.app.application as app_module
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

_KEEP_ALIVE: list = []

_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")
_FEED = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "LightboxFeed.qml"
).read_text(encoding="utf-8")


def _fejlec(engine, **props):
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    fejlec = comp.createWithInitialProperties(props)
    assert comp.errors() == [], comp.errors()
    assert fejlec is not None
    _KEEP_ALIVE.append(fejlec)
    return fejlec


def _gomb(fejlec, nev):
    gomb = fejlec.findChild(QObject, nev)
    assert gomb is not None, f"{nev} nem található"
    return gomb



class TestJovahagyasValtakozik:
    def test_kijeloles_nelkul_az_osszes(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3,
                         selectedSuggestionCount=0)

        felirat = _gomb(fejlec, "headerConfirmSuggestionsButton").property("text")

        assert felirat == "Confirm all (3)"

    def test_kijelolt_javaslattal_a_kijeloltek(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3,
                         selectedSuggestionCount=1)

        gomb = _gomb(fejlec, "headerConfirmSuggestionsButton")

        assert gomb.property("text") == "Confirm"
        assert gomb.property("sugoSzoveg") == "Confirm selected suggestions"

    def test_ugyanaz_a_teglalap(self, qml_app):
        """A mérés: `confirmsug` és `confirmsel` ugyanazt a helyet foglalja."""
        _, _, engine = qml_app
        mind = _gomb(_fejlec(engine, personName="Anna", suggestionCount=3,
                             selectedSuggestionCount=0),
                     "headerConfirmSuggestionsButton")
        kijelolt = _gomb(_fejlec(engine, personName="Anna", suggestionCount=3,
                                 selectedSuggestionCount=2),
                         "headerConfirmSuggestionsButton")

        for tul in ("x", "width", "height"):
            assert mind.property(tul) == kijelolt.property(tul)


class TestElvetesSugo:
    def test_kijelolt_javaslattal_a_mert_sugo(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3,
                         selectedSuggestionCount=1)

        gomb = _gomb(fejlec, "headerRemoveSuggestionsButton")

        assert gomb.property("sugoSzoveg") == "Remove selected suggestions"

    def test_kijeloles_nelkul_az_osszesrol_szol(self, qml_app):
        """Kijelölés nélkül a gomb az összesre hat — a súgó ezt mondja,
        nem a mért „selected" alakot (ne ígérjen mást, mint amit tesz)."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3,
                         selectedSuggestionCount=0)

        gomb = _gomb(fejlec, "headerRemoveSuggestionsButton")

        assert gomb.property("sugoSzoveg") == "Remove all suggestions"


class TestBekotes:
    """A gazda a kijelölt fotókból számolja az arcokat, és a műveletet
    velük hívja — forrás-szintű állítás, mert a Main.qml élő példánya
    nélkül a lánc nem járható be (a vezérlő-oldalt a
    `tests/app/test_kijelolt_javaslatok_2187.py` méri)."""

    def test_a_gazda_a_kijeloles_arcait_kerdezi(self):
        assert "personSuggestionIdsForPaths" in _MAIN

    def test_a_feed_atadja_a_kijelolt_darabszamot(self):
        assert "selectedSuggestionCount:" in _FEED

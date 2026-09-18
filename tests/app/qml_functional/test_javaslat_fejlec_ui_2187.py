"""#2187 — a személy-album fejlécének javaslat-vezérlői.

Az eredetiben a személy-album fejléce **saját panel** (`faceheaderpanel`),
és rajta ül a jóváhagyási munkafolyamat. Nálunk a személy képei UGYANABBAN
a rácsban, ugyanezzel a fejléccel jelennek meg — a vezérlők ezért ugyanide
kerülnek, a személy-album MÓDJÁBAN.

## A mért geometria (`respack.yt`, a jegy táblája)

| vezérlő | méret | hely |
|---|---|---|
| `confirmsug` / `confirmsel` | **88 × 27** | (348, 55) — **ugyanaz a téglalap** |
| `removesel` | **88 × 27** | (439, 55) |

A két jóváhagyó ugyanazon a helyen váltakozik, mert a mérés szerint
**ugyanaz a kezelő** (`0x00602640`), egyetlen logikai argumentummal:
`confirmsug` → `push 1` (mind), `confirmsel` → `push 0` (a kijelöltek).

## ⚠️ Amit ez a kör NEM visz

A **kijelölt** hatókör (`confirmsel`, `removesel` a kijelöltekre). Ahhoz a
javaslatoknak látszaniuk kell a személy-album rácsában — enélkül a
„Jóváhagyás" felirat egy üres halmazra hatna. A művelet mindkét hatókört
tudja (`test_javaslat_fejlec_2187.py`), a felület egyelőre a teljeset
hívja, és a gomb felirata ezért nem vált.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import picasapy.app.application as app_module
import pytest
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


class TestLathatosag:
    def test_mappa_fejlecen_NINCSENEK_javaslat_gombok(self, qml_app):
        """Általános album/mappa esetén a vezérlők nem látszanak — a
        jegy első „Kész, ha" pontja."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, folderName="Nyaralás", personName="")

        for nev in ("headerConfirmSuggestionsButton",
                    "headerRemoveSuggestionsButton"):
            gomb = fejlec.findChild(QObject, nev)
            assert gomb is not None, f"{nev} nem található"
            assert gomb.property("visible") is False

    def test_javaslat_nelkuli_szemely_albumon_sem(self, qml_app):
        """Nyitott személy-album, de nincs függő javaslat: nincs mit
        jóváhagyni, tehát a vezérlők sem látszanak."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=0)

        assert fejlec.findChild(
            QObject, "headerConfirmSuggestionsButton"
        ).property("visible") is False

    def test_javaslattal_latszanak(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3)

        for nev in ("headerConfirmSuggestionsButton",
                    "headerRemoveSuggestionsButton"):
            assert fejlec.findChild(QObject, nev).property("visible") is True


class TestGeometria:
    @pytest.mark.parametrize(
        "nev", ["headerConfirmSuggestionsButton", "headerRemoveSuggestionsButton"]
    )
    def test_a_mert_88x27(self, qml_app, nev):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3)

        gomb = fejlec.findChild(QObject, nev)

        assert gomb.property("width") == 88
        assert gomb.property("height") == 27


class TestFelirat:
    def test_a_jovahagyas_kiirja_a_darabszamot(self, qml_app):
        """A fejléc-gombok szám nélküli és számos alakban élnek (#1823) —
        a javaslat-gomb a FÜGGŐ javaslatok számát mutatja, nem a
        kijelölését, mert a hatóköre (ebben a körben) mindig a teljes."""
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=3)

        felirat = fejlec.findChild(
            QObject, "headerConfirmSuggestionsButton"
        ).property("text")

        assert "3" in felirat


class TestJelzesek:
    def test_a_jovahagyas_jelet_ad(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=2)
        kaptunk = []
        fejlec.confirmSuggestionsRequested.connect(lambda: kaptunk.append(1))

        fejlec.findChild(
            QObject, "headerConfirmSuggestionsButton"
        ).clicked.emit()

        assert kaptunk == [1]

    def test_az_elvetes_jelet_ad(self, qml_app):
        _, _, engine = qml_app
        fejlec = _fejlec(engine, personName="Anna", suggestionCount=2)
        kaptunk = []
        fejlec.removeSuggestionsRequested.connect(lambda: kaptunk.append(1))

        fejlec.findChild(
            QObject, "headerRemoveSuggestionsButton"
        ).clicked.emit()

        assert kaptunk == [1]


class TestBekotes:
    """A jelek a vezérlő MŰVELETÉIG jutnak — forrás-szintű állítás, mert a
    gazda (Main.qml) élő példánya nélkül a lánc nem járható be."""

    def test_a_feed_atadja_a_szemely_nevet(self):
        assert "personName:" in _FEED

    def test_a_gazda_a_vezerlo_muveletet_hivja(self):
        assert "confirmPersonSuggestions" in _MAIN
        assert "removePersonSuggestions" in _MAIN

    def test_a_gazda_a_darabszamot_a_vezerlobol_veszi(self):
        assert "personSuggestionCount" in _MAIN

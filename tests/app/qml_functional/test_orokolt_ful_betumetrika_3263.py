"""Az örökölt-effektek füle NAGYOBB betűvel is belefér a mért 277-be (#3263).

## A kiváltó eset

A main CI windows-lába piros volt: a fül ott **317** képpontot kért, Linuxon
ugyanaz **274**. A különbség a betűmetrika — a windowsos alapbetű magasabb
sort ad, a bevezető szöveg három sorba tört, és a rács gombjai is magasabbak.
A 277 viszont az EREDETI Picasa windowsos felvételéből MÉRT szám: ahol a
fülünk 317, ott tényleg 40 képponttal magasabb a mért lapnál.

## Amit ez az őr állít

Hogy a befértség **konstrukcióból** áll, nem a platform betűjének
jóindulatából: a bevezető legfeljebb két sor, a rács pedig görgethető
kereten belül él, ami a lapból maradó helyet kapja. A próba ezért
MEGNÖVELI a betűt — ahogy a windowsos futtató tenné —, és utána is a mért
277-et kéri számon.

## Amit NEM állít

A LÁTVÁNYT: hogy a görgethető rácsban hova kerülnek a csempék. A csempe-
geometriát a #741 őre méri.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

MERT_LAP_MAGASSAG = 277


def _ful(window) -> QObject:
    elem = window.findChild(QObject, "legacyEffectsColumn")
    assert elem is not None, "a legacyEffectsColumn fül nincs a jelenetben"
    return elem


class TestNagyobbBetuvelIsBefer:
    def test_a_megnovelt_bevezeto_nem_noveli_a_fulet(self, qml_app, qt_app):
        """A bevezető betűjét a WINDOWS-nál is nagyobbra állítjuk."""
        window = qml_app[0]
        qt_app.processEvents()
        ful = _ful(window)
        bevezeto = window.findChild(QObject, "legacyEffectsIntro")
        assert bevezeto is not None

        elotte = float(ful.property("implicitHeight"))
        assert elotte <= MERT_LAP_MAGASSAG

        betu = bevezeto.property("font")
        betu.setPixelSize(22)  # a mai ~11 helyett — durva windowsos túlzás
        bevezeto.setProperty("font", betu)
        qt_app.processEvents()

        utana = float(ful.property("implicitHeight"))
        assert utana <= MERT_LAP_MAGASSAG, (
            f"nagyobb betűvel a fül {utana:.0f} képpont — a mért lap 277"
        )

    def test_a_bevezeto_legfeljebb_ket_sor(self, qml_app, qt_app):
        window = qml_app[0]
        qt_app.processEvents()
        bevezeto = window.findChild(QObject, "legacyEffectsIntro")
        assert int(bevezeto.property("maximumLineCount")) == 2

    def test_a_racs_gorgetheto_kerete_letezik(self, qml_app, qt_app):
        """A tartalom nem vész el: ami nem fér ki, az elgörgethető."""
        window = qml_app[0]
        qt_app.processEvents()
        keret = window.findChild(QObject, "legacyEffectsScroll")
        assert keret is not None, "a görgethető keret nélkül a rács alja levágódna"
        assert float(keret.property("contentHeight")) >= float(keret.property("height"))

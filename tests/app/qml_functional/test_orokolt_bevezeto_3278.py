"""#3278 — az „Örökölt szűrők" fül bevezetője NAGYOBB betűvel sem vágódik le.

## A helyzet

A bevezető (`legacyEffectsIntro`) a #3263 óta `maximumLineCount: 2` +
`elide` korlátozással áll: enélkül a windowsos, magasabb sorú betűvel
három sorba tört, és a fül túlnőtt a mért `editpanel/tabpanel1` = 277
képponton. Az elidálás így a TÖRÉST hárította el, az olvashatóságot nem: a
CI mindkét lábán levágva jelentette a #656 őre.

## ⛔ Referencia NINCS — és ezt ki kell mondani

A jegy törzse szerint „a referenciát a Picasa saját füle adja". **Nem
adja:** ez a fül a mi SAJÁT kiegészítésünk (ADR-003,
`docs/decisions/legacy-effects-tab.md`), az eredetiben nem létezik. A
szöveg hossza tehát a mi döntésünk, nem egyeztetési kérdés.

A választott megoldás: a bevezető EGY rövid mondat, ami a legnagyobb
ésszerű betűvel is elfér két sorban; a bővebb magyarázat (hogy a mai
Picasa csak a régi szerkesztésekben ismeri fel őket) nem vész el, hanem a
buboréksúgóba kerül.

## Amit ez a fájl állít

- a felirat **nem levágott** (`truncated === false`) a mai betűvel;
- **nagyobb betűvel sem** — a CI-metrika és a felhasználó
  rendszerbetűje is nagyobb lehet, mint a fejlesztői gépé;
- a bővebb magyarázat **elérhető** (súgó), tehát a rövidítés nem
  információvesztés;
- a fül magassága a mért kereten belül marad.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent

_KEEP_ALIVE: list = []

#: A mért laptmagasság (`editpanel/tabpanel1`) — a #3263 hivatkozási száma.
LAP_MAGASSAG = 277


def _ful(engine):
    """Az örökölt fül önállóan, egy hamis gazda-panellel.

    A `panel` a gazda `EditorPanel`; a fülnek csak néhány jelzője kell
    belőle, ezért egy `QtObject` is elég — így a próba nem a teljes
    szerkesztőt építi fel.

    ⚠️ A betűMÉRET-et nem állítjuk: a `Theme` szingleton, a felülírása
    átszivárogna a többi próbára. A nagyobb betű hatását a SZÉLESSÉG
    szűkítése méri — a szöveg ugyanúgy több helyet kér, mint amennyi van."""
    forras = """
import QtQuick
import PicasaPy 1.0

Item {
    width: 276
    height: 400
    QtObject {
        id: hamisPanel
        property bool modeToolActive: false
        property int activeTab: 6
        property bool paramPanelActive: false
        property bool enabled: true
        property var legacyEffects: []
        function hasEffectController() { return false }
        function legacyEffectEnabled(nev) { return false }
    }
    EditorLegacyTab {
        anchors.fill: parent
        panel: hamisPanel
    }
}
"""
    comp = QQmlComponent(engine)
    comp.setData(forras.encode("utf-8"), QUrl())
    _KEEP_ALIVE.append(comp)
    gyoker = comp.create()
    assert [e.toString() for e in comp.errors()] == [], comp.errors()
    assert gyoker is not None
    _KEEP_ALIVE.append(gyoker)
    return gyoker


def _bevezeto(gyoker) -> QObject:
    elem = gyoker.findChild(QObject, "legacyEffectsIntro")
    assert elem is not None, "nincs legacyEffectsIntro"
    return elem


class TestNemVagodikLe:
    def test_a_mai_betuvel_nem_levagott(self, qml_app):
        _, _, engine = qml_app

        bevezeto = _bevezeto(_ful(engine))

        assert bevezeto.property("truncated") is False, bevezeto.property("text")

    @pytest.mark.parametrize("szelesseg", [276, 260, 240])
    def test_keskenyebb_panelen_sem(self, qml_app, szelesseg):
        """A tartalom-oszlop szélessége nem állandó (#779): a felirat a
        keskenyebb panelen is elfér két sorban.

        ⚠️ A 240 az ALSÓ határ: a #779 mérése szerint a legkeskenyebb
        panelen ennyi a tartalom-oszlop. Ennél szűkebbre nem méretezünk,
        mert olyan panel nincs."""
        _, _, engine = qml_app
        gyoker = _ful(engine)
        gyoker.setProperty("width", szelesseg)

        assert _bevezeto(gyoker).property("truncated") is False

    def test_a_ket_soros_korlat_MEGMARAD(self, qml_app):
        """A #3263 őre: a sorszám rögzítése nélkül a fül magassága a
        betűmetrikán múlna. A rövidítés ezt NEM oldja fel."""
        _, _, engine = qml_app

        assert _bevezeto(_ful(engine)).property("maximumLineCount") == 2


class TestAzInformacioNemVESZ_EL:
    def test_a_bovebb_magyarazat_a_sugoban_van(self, qml_app):
        """A rövidítés nem információvesztés: amit a mondatból kivettünk,
        az a buboréksúgóban elérhető.

        ⚠️ A CSATOLT `ToolTip.text` a próbából nem olvasható ki
        (`property("ToolTip.text")` → null, ez mérve a #1701-ben), ezért a
        fül SAJÁT tulajdonságban is tartja — ahogy a `PicasaMenuItem`
        `sajatSugo`-ja."""
        _, _, engine = qml_app

        sugo = _bevezeto(_ful(engine)).property("bovebbSugo")

        assert sugo, "nincs bővebb magyarázat"
        assert "old edits" in sugo or "régi" in sugo


class TestAFulMagassaga:
    def test_a_mert_lapon_belul_marad(self, qml_app):
        """A #3263 állítása változatlanul áll: a fül nem nőhet a mért
        `editpanel/tabpanel1` fölé."""
        _, _, engine = qml_app
        gyoker = _ful(engine)

        ful = gyoker.findChild(QObject, "legacyEffectsColumn")
        assert ful is not None
        assert ful.property("implicitHeight") <= LAP_MAGASSAG, (
            ful.property("implicitHeight")
        )

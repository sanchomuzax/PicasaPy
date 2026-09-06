"""#2494: a „Visszavonás: <effektnév>" felirat nem lóghat le a gombról.

## A tulajdonos jelentése (v0.8.293)

> „A »Visszavonás: Jó napom van« felirat betűmérete túl nagy, emiatt
> lelóg a gombról."

## MÉRVE a képernyőmentésen (`235707.jpg`, 1920 × 1200)

| | eredeti (Picasa 3) | nálunk |
|---|---|---|
| a gomb kerete (y) | 380 … 405 → **26 px** | 403 … 430 → **28 px** |
| 1. szövegsor | 384 … 393 | 414 … 424 |
| 2. szövegsor | 396 … 405 | **430 … 435** ⚠️ |
| sorköz | **12 px** | **16 px** |
| a szöveg kezdete a keret tetejétől | **4 px** | **11 px** |
| „Visszavonás: Jó napom" szélessége | 103 px | 106 px |

⇒ **NEM a betűméret a hibás**: ugyanaz a szöveg 106 kontra 103 képpont
széles, azaz a betűk gyakorlatilag azonos méretűek. A kilógást két másik
eltérés okozza: a felirat FELÜLRE volt igazítva (11 px veszteség a
tetején), és a gomb magassága rögzített 28 volt, ami két sornak kevés.

## A javítás hatóköre — és amit SZÁNDÉKOSAN nem tettünk

A gomb mostantól **megnő**, ha a felirat két sorra tör (a 28 alsó korlát
lett, nem felső), és a felirat középen ül.

A **sorközt** nem szorítottuk 12 képpontra. Rögzített képpontos
sormagasság már megharapott minket: a #422-ben a Windows CI ugyanazt a
szöveget HÁROM sorra törte, mert a sormagasság platformonként más. A
gomb növekedése platformfüggetlenül old, a 4 képpontos sorköz-eltérés
pedig nem látszik. Ez tudatos eltérés a mért 26 képponttól, nem tévedés.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

#: A leghosszabb VALÓDI magyar felirat, nem kitalált szöveg: a
#: `Visszavonás` + a leghosszabb lefordított effektnév
#: (`Auto Contrast` → „Automatikus kontraszt", 21 karakter).
LEGHOSSZABB_FELIRAT = "Visszavonás: Automatikus kontraszt"

#: A tulajdonos jelentésében szereplő, mért eset.
JELENTETT_FELIRAT = "Visszavonás: Jó napom van"


#: A tulajdonos képernyőmentésén MÉRT gombszélesség. A spec 132-t mond
#: (#741), a felvételen viszont 109 — ezen a szélességen tör két sorra a
#: jelentett felirat. A próba a MÉRT állapotot idézi elő, nem a spec
#: szerintit: a hiba ott jelentkezett.
MERT_GOMBSZELESSEG = 109


def _panel(qt_app, *, gombszelesseg: float | None = None):
    from tests.app.qml_functional.test_editor_panel_geometry_741 import _render

    panel = _render(qt_app)
    if gombszelesseg is not None:
        # a sor két egyenlő gombot és 5 px hézagot tartalmaz, a panel
        # pedig 4-4 px oldalmargót ad
        panel.setWidth(2 * gombszelesseg + 5 + 8)
        qt_app.processEvents()
    return panel


def _gomb_es_felirat(panel) -> tuple[QObject, QObject]:
    from tests.app.qml_functional.test_editor_panel_geometry_741 import _child

    return _child(panel, "editUndoButton"), _child(panel, "editUndoButtonLabel")


@pytest.mark.parametrize(
    "felirat,szelesseg",
    [
        (JELENTETT_FELIRAT, MERT_GOMBSZELESSEG),
        (JELENTETT_FELIRAT, None),
        (LEGHOSSZABB_FELIRAT, MERT_GOMBSZELESSEG),
        (LEGHOSSZABB_FELIRAT, None),
    ],
    ids=["jelentett-mert", "jelentett-spec", "leghosszabb-mert", "leghosszabb-spec"],
)
def test_a_felirat_belefer_a_gombba(qt_app, felirat, szelesseg):
    """A RAJZOLT felirat alja nem lóghat túl a gomb alján.

    A `paintedHeight`-et mérjük, nem a sorok számát: a tördelés
    platformonként más lehet (#422), a kilógás viszont ugyanaz a hiba
    mindenhol."""
    panel = _panel(qt_app, gombszelesseg=szelesseg)
    panel.setProperty("undoLabel", felirat)
    qt_app.processEvents()

    gomb, cimke = _gomb_es_felirat(panel)
    teteje = cimke.mapToItem(gomb, 0, 0).y()
    alja = teteje + cimke.property("paintedHeight")

    assert alja <= gomb.property("height") + 0.5, (
        f"a(z) {felirat!r} felirat {alja - gomb.property('height'):.1f} "
        f"képponttal lelóg a gombról (gomb {gomb.property('height'):.0f} px, "
        f"a felirat alja {alja:.1f})"
    )


def test_a_felirat_a_gomb_TETEJEROL_sem_log_ki(qt_app):
    """A középre igazítás nem tolhatja a feliratot a gomb fölé."""
    panel = _panel(qt_app, gombszelesseg=MERT_GOMBSZELESSEG)
    panel.setProperty("undoLabel", LEGHOSSZABB_FELIRAT)
    qt_app.processEvents()

    gomb, cimke = _gomb_es_felirat(panel)
    assert cimke.mapToItem(gomb, 0, 0).y() >= -0.5


@pytest.mark.parametrize(
    "felirat", ["Visszavonás", JELENTETT_FELIRAT, LEGHOSSZABB_FELIRAT]
)
def test_a_felirat_FUGGOLEGESEN_KOZEPEN_ul(qt_app, felirat):
    """A felirat fölötti és alatti rés közel egyenlő.

    ⚠️ Ezt a gomb megnövelése ÖNMAGÁBAN nem biztosítja: felülre
    horgonyozva a felirat akkor is elfér, csak a tetőhöz tapad. MÉRVE a
    `235707.jpg`-n: az eredetiben a szöveg 4 képponttal a keret alatt
    kezdődik egy 26 képpontos gombban (tehát középen), nálunk 11-gyel egy
    28 képpontosban. A mutáció (visszaállított felső igazítás) enélkül az
    őrön ÁTMENT.
    """
    panel = _panel(qt_app, gombszelesseg=MERT_GOMBSZELESSEG)
    panel.setProperty("undoLabel", felirat)
    qt_app.processEvents()

    gomb, cimke = _gomb_es_felirat(panel)
    felette = cimke.mapToItem(gomb, 0, 0).y()
    alatta = gomb.property("height") - (felette + cimke.property("paintedHeight"))

    assert abs(felette - alatta) <= 2.5, (
        f"a(z) {felirat!r} felirat nem középen ül: fölötte {felette:.1f}, "
        f"alatta {alatta:.1f} képpont"
    )


def test_egysoros_feliratnal_marad_a_MERT_28(qt_app):
    """⚠️ A 28 a #741 MÉRT gombmagasága (`filter_undo` 132 × 28) — a
    javítás csak akkor engedheti nagyobbra, ha a felirat tényleg nem fér
    el. Az alapeset geometriája nem változhat."""
    panel = _panel(qt_app)
    panel.setProperty("undoLabel", "Visszavonás")
    qt_app.processEvents()

    gomb, _cimke = _gomb_es_felirat(panel)
    assert abs(gomb.property("height") - 28) <= 1, (
        f"az egysoros gomb {gomb.property('height'):.0f} px magas a mért 28 "
        "helyett (#741 spec 1.)"
    )


def test_a_ket_gomb_egyforma_magas(qt_app):
    """#405: a Visszavonás és az Újra egyenlő pár — ha az egyik megnő, a
    másik sem maradhat le, különben a sor szétcsúszik."""
    from tests.app.qml_functional.test_editor_panel_geometry_741 import _child

    panel = _panel(qt_app, gombszelesseg=MERT_GOMBSZELESSEG)
    panel.setProperty("undoLabel", LEGHOSSZABB_FELIRAT)
    qt_app.processEvents()

    undo = _child(panel, "editUndoButton")
    redo = _child(panel, "editRedoButton")
    assert abs(undo.property("height") - redo.property("height")) <= 0.5

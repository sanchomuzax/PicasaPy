"""#2494: a „Visszavonás: <effektnév>" felirat nem lóghat le a gombról.

## A tulajdonos jelentése (v0.8.293)

> „A »Visszavonás: Jó napom van« felirat betűmérete túl nagy, emiatt
> lelóg a gombról."

## MÉRVE a képernyőmentéseken

Az első kör a `235707.jpg`-t (v0.8.293) mérte; az alábbi számok a
tulajdonos ÚJABB, 1:1-es felvételéről valók (`141421.jpg`, 1920 × 1200,
bal fél Picasa 3, jobb fél PicasaPy v0.8.302):

| | eredeti (Picasa 3) | nálunk (v0.8.302) |
|---|---|---|
| a gomb rajzolt kerete (y) | 380 … 405 → **26 px** | 403 … 440 → **38 px** |
| alapvonal-távolság (sorköz) | **10 px** | **14 px** |
| „Visszavonás: Jó napom" szélessége | 103 px | 109 px |

⇒ **NEM a betűméret a hibás**: ugyanaz a szöveg 109 kontra 103 képpont
széles, azaz a betűk gyakorlatilag azonos méretűek.

## ⚠️ HELYESBÍTÉS — az első kör indoklása TÉVES volt

Az első kör a **gombot növelte meg** (26 → 38), és a sorközt szándékosan
békén hagyta, ezzel az indokkal: „a #422-ben a Windows CI ugyanazt a
szöveget HÁROM sorra törte, mert a sormagasság platformonként más".

**Ez téves hivatkozás volt.** A #422 a gombmagasság `fontSize * 1.35`-ös
BECSLÉSÉRŐL szólt; azt pedig, hogy egy szöveg hány sorra törik, a betűk
SZÉLESSÉGE dönti el, amire a sorköznek semmi hatása nincs. A sorköz
szorítása nem hozhat vissza egy harmadik sort.

A tulajdonos ezt visszaesésként jelentette: a gomb 38 képpont magas lett a
mért 26 helyett. A valódi ok a **hiányzó sorköz-beállítás** volt — a
`PanelButton` felirat-`Text`-je a betűtípus saját, 13,64 képpontos
sormagasságával rajzolt, miközben az eredeti erőforrás (`m_buttonfontC`:
`fontsize 12`, `textwrap 1`, **`fontleading 10`**) 10-et ír elő. A javítás
azóta `Theme.lineLeading` (fix 10 képpont), és a gomb visszatért 26-ra.

## 26 vagy 28? — a #741 spec és a felvétel ELLENTMONDÁSA feloldva

A #741 a respack `filter_undo` téglalapjából **132 × 28**-at mond, a
felvételen viszont **26** mérhető. Mindkettő igaz, mert nem ugyanazt
mérik:

* a **132 × 28** a HELY, amit a gomb az elrendezésben elfoglal — ezt a
  felvétel megerősíti: a két gomb bal keretének osztásköze **137** =
  132 + 5 hézag, pontosan a respack értéke;
* a **130 × 26** a KIRAJZOLT gombkeret: a gombkép minden oldalon 1
  képponttal beljebb kezdődik a helyénél (a szélességen ugyanez a −2
  látszik: 130 a 132-ből).

Nálunk a `PanelButton` `Rectangle`-je MAGA a rajzolt keret — nincs külön
hely és külön kép —, tehát a látható 26-ot kell felvennie.

## Ez a fájl SZÁMÍTOTT geometriát mér

A képpontos párja a `test_sorkoz_renderelt_2494_2567.py`: az rajzoltatja
ki a panelt, és a FELVÉTELEN méri a sorközt és a keretet. A visszaesést
azért nem fogta meg semmi, mert csak ez a számított oldal létezett — a
kettő együtt az őr.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer

#: A leghosszabb VALÓDI magyar felirat, nem kitalált szöveg: a
#: `Visszavonás` + a leghosszabb lefordított effektnév
#: (`Auto Contrast` → „Automatikus kontraszt", 21 karakter).
LEGHOSSZABB_FELIRAT = "Visszavonás: Automatikus kontraszt"

#: A tulajdonos jelentésében szereplő, mért eset.
JELENTETT_FELIRAT = "Visszavonás: Jó napom van"


#: Szűk gomb: ezen a szélességen a jelentett felirat BIZTOSAN két sorra
#: tör, bármelyik platform betűtípusával. (A tulajdonos gépén a 132 széles
#: gombon is tört — az ottani betűkép ~5%-kal szélesebb a tesztkörnyezet
#: Nunito Sansánál —, a tördelés tehát nem hordozható próba. Ez a szám NEM
#: a gomb mért szélessége: a felvételen a KIRAJZOLT keret 130, a helye 132.)
MERT_GOMBSZELESSEG = 109


def _panel(qt_app, *, gombszelesseg: float | None = None):
    from tests.app.qml_functional.test_editor_panel_geometry_741 import _render

    panel = _render(qt_app)
    if gombszelesseg is not None:
        # a sor két egyenlő gombot és 5 px hézagot tartalmaz, a panel
        # pedig 4-4 px oldalmargót ad
        panel.setWidth(2 * gombszelesseg + 5 + 8)
        _leul(qt_app)
    return panel


def _leul(qt_app, korok: int = 3) -> None:
    """⚠️ A felirat magassága a KAPOTT szélességtől függ, a gomb magassága
    pedig a felirattól — ez az elrendezésnek két menet. Egyetlen
    `processEvents()` után a mérés még a köztes állapotot látja (mérve: a
    „belefér" és a „középen ül" próba UGYANARRA a beállításra más
    eredményt adott). Ezért várunk rendes eseményhurok-fordulókat."""
    for _ in range(korok):
        qt_app.processEvents()
        szunet = QEventLoop()
        QTimer.singleShot(10, szunet.quit)
        szunet.exec()


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
    _leul(qt_app)

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
    _leul(qt_app)

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
    _leul(qt_app)

    gomb, cimke = _gomb_es_felirat(panel)
    felette = cimke.mapToItem(gomb, 0, 0).y()
    alatta = gomb.property("height") - (felette + cimke.property("paintedHeight"))

    assert abs(felette - alatta) <= 2.5, (
        f"a(z) {felirat!r} felirat nem középen ül: fölötte {felette:.1f}, "
        f"alatta {alatta:.1f} képpont"
    )


def test_egysoros_feliratnal_marad_a_MERT_26(qt_app):
    """⚠️ A 26 a felvételen MÉRT, KIRAJZOLT gombkeret (a respack 132 × 28-as
    téglalapja a HELY — ld. a modul fejét). A javítás csak akkor engedheti
    nagyobbra, ha a felirat tényleg nem fér el."""
    panel = _panel(qt_app)
    panel.setProperty("undoLabel", "Visszavonás")
    _leul(qt_app)

    gomb, _cimke = _gomb_es_felirat(panel)
    assert abs(gomb.property("height") - 26) <= 1, (
        f"az egysoros gomb {gomb.property('height'):.0f} px magas a mért 26 "
        "helyett (#741/#2494)"
    )


def test_a_ket_gomb_egyforma_magas(qt_app):
    """#405: a Visszavonás és az Újra egyenlő pár — ha az egyik megnő, a
    másik sem maradhat le, különben a sor szétcsúszik."""
    from tests.app.qml_functional.test_editor_panel_geometry_741 import _child

    panel = _panel(qt_app, gombszelesseg=MERT_GOMBSZELESSEG)
    panel.setProperty("undoLabel", LEGHOSSZABB_FELIRAT)
    _leul(qt_app)

    undo = _child(panel, "editUndoButton")
    redo = _child(panel, "editRedoButton")
    assert abs(undo.property("height") - redo.property("height")) <= 0.5

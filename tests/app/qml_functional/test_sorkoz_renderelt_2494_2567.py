"""A többsoros feliratok sorköze a KIRAJZOLT képen — #2494 és #2567.

## Miért képpontos ez az őr, és miért nem elég a számított geometria

A #2494-et egyszer már „megjavítottuk", és **visszaesett**. Az akkori őr a
`paintedHeight`-et hasonlította a gomb magasságához — vagyis csak azt kérdezte,
hogy *elfér-e* a felirat. Elfért: a javítás a **gombot növelte meg** 26-ról
38-ra, ahelyett hogy a **sorközt** szorította volna a mértre. A számított
mérce szerint ez helyes volt; a felhasználó szemével nézve nem.

Ezért ez a fájl a panelt **kirajzoltatja** (`QQuickWindow.grabWindow()`), és a
KÉPPONTOKON méri, amit állít: a szövegsorok tinta-sávjait és a gomb keretét.
A `test_visszavonas_felirat_2494.py` számított őrei megmaradnak mellette —
kiegészítik egymást, de egyedül egyik sem elég.

## A mérce: 10 képpont, KÉT független forrásból

▶**ERŐFORRÁS.** A `fontmacros_win.tre` mindkét ide tartozó makrója ugyanazt
mondja (`docs/specs/ui-audit-editor.md` 3.3, `picasa-gomb-es-menu-rendszer.md`):

* `m_buttonfontC` — a Visszavonás/Újra és minden sima gombfelirat:
  `fontsize 12`, `textwrap 1`, **`fontleading 10`**;
* `m_fxlabel` — a csempefelirat: `fontsize 11`, `fontweight 700`,
  **`fontleading 10`**.

▶**KÉP.** A tulajdonos 1:1 felvételén (`141421.jpg`, 1920 × 1200; bal fél
Picasa 3, jobb fél PicasaPy) a Picasa alapvonal-távolsága MÉRVE:

| hely | eredeti | PicasaPy (v0.8.302) |
|---|---|---|
| „Visszavonás: Jó napom / van" | **10** | 14 |
| „Automatikus / kontraszt" csempe | **10** | 13 |

A két módszer betűre egyezik, tehát a 10 nem becslés.

## Miért FIX képpont és nem arány

A `Text.ProportionalHeight` a PLATFORM betűtípusának sormagasságát szorozza.
A tesztkörnyezet Nunito Sanst kap (sormagasság 13,64), a tulajdonos gépén futó
alkalmazás ennél ~5%-kal szélesebb betűképet rajzol — arányos sorköznél tehát
gépenként MÁS képpontszám jönne ki, és épp azt veszítenénk el, amit átveszünk.
A `Text.FixedHeight` mindenhol ugyanazt a 10-et adja; ezt az őr méri.
"""

from __future__ import annotations

import time

import numpy as np
import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

from tests.app.qml_functional.test_editor_panel_geometry_741 import (
    PANEL_SZELESSEG,
    _EditControllerStub,
    _child,
)

_KEEPALIVE: list[object] = []

#: Az eredeti `fontleading` — MÉRVE és az erőforrásból is (ld. a modul fejét).
MERT_SORKOZ = 10

#: A KIRAJZOLT gombkeret magassága a felvételen. A respack `filter_undo`
#: téglalapja 132 × 28 — az a HELY, amit a gomb elfoglal; a rajzolt keret
#: minden oldalon 1 képponttal kisebb. Bizonyíték ugyanazon a felvételen:
#: a két gomb bal keretének osztásköze 137 = 132 + 5 hézag (pontosan a
#: respack értéke), a rajzolt keret viszont 130 × 26. Nálunk a `PanelButton`
#: `Rectangle`-je MAGA a rajzolt keret, tehát a látható 26 az irányadó.
MERT_GOMBKERET = 26

#: A leghosszabb VALÓDI magyar Visszavonás-felirat. A tesztkörnyezet betűje
#: keskenyebb a tulajdonos gépén futóénál, ezért a rövidebb („Visszavonás:
#: Jó napom van") itt még EGY sorba fér — a kétsoros esetet ezzel idézzük elő
#: determinisztikusan, gépfüggő szélesség-szorongatás nélkül.
KETSOROS_FELIRAT = "Visszavonás: Automatikus kontraszt"

#: A hosszú csempefelirat, ami a felvételen is két sorra tört.
KETSOROS_CSEMPE = "Automatikus kontraszt"


def _var_a_kirajzolasra(view: QQuickView, qt_app, masodperc: float = 10.0) -> None:
    """A `test_histogram_pixels_864.py` bevált mintája: fix beállás, majd
    két egyforma felvételre várakozás. A fali óra itt PADLÓ, nem plafon."""
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)
    elozo = None
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        mostani = view.grabWindow()
        if elozo is not None and mostani == elozo:
            return
        elozo = mostani
        time.sleep(0.01)
    qt_app.processEvents()


#: A #741 mérőfájljának vázával azonos: a panel a gyökér BAL oldalán áll,
#: rögzített szélességgel. ⚠️ `anchors.fill`-lel a fülsáv rejtve maradt és a
#: gombsor a panel tetejére csúszott — a felvételen üres, fehér panel
#: látszott. A kirajzolt őrnél ez némán hamis leletet adna, ezért a
#: `test_a_ful_tartalma_egyaltalan_kirajzolodik` külön ellenőrzi.
_PANEL_QML = """
import QtQuick
import PicasaPy 1.0
Item {{
    objectName: "gyoker"
    EditorPanel {{
        objectName: "panel"
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: {szelesseg}
    }}
}}
"""


@pytest.fixture(scope="module")
def _panel_nezet(qt_app):
    """Egyetlen kirajzolt panel a fájl összes mérésére (drága erőforrás)."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    stub = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", stub)
    view.engine().rootContext().setContextProperty("controller", None)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(
        _PANEL_QML.format(szelesseg=PANEL_SZELESSEG).encode("utf-8"), QUrl()
    )
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(PANEL_SZELESSEG, 900)
    root.setWidth(PANEL_SZELESSEG)
    root.setHeight(900)
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)
    _KEEPALIVE.extend((view, root, component, stub))
    yield view, root, qt_app


def _szurkekep(view: QQuickView) -> tuple[np.ndarray, float]:
    """A kirajzolt ablak szürkeárnyalatos képe és a képpont-arány."""
    kep = view.grabWindow().convertToFormat(QImage.Format.Format_Grayscale8)
    szelesseg, magassag = kep.width(), kep.height()
    assert szelesseg > 0 and magassag > 0, "üres felvétel"
    puffer = np.frombuffer(kep.constBits(), dtype=np.uint8, count=kep.sizeInBytes())
    tomb = puffer.reshape(magassag, kep.bytesPerLine())[:, :szelesseg].astype(float)
    return tomb, szelesseg / max(1, view.width())


def _ablakdoboz(view: QQuickView, item: QQuickItem) -> tuple[int, int, int, int]:
    """Az elem (x, y, szélesség, magasság) doboza a FELVÉTEL képpontjaiban."""
    tomb, arany = _szurkekep(view)
    del tomb
    bal_felso = item.mapToScene(item.mapFromItem(item, 0, 0))
    return (
        int(round(bal_felso.x() * arany)),
        int(round(bal_felso.y() * arany)),
        int(round(item.width() * arany)),
        int(round(item.height() * arany)),
    )


def _tinta_savok(
    tomb: np.ndarray, x0: int, x1: int, y0: int, y1: int, kuszob: float = 0.18
) -> list[tuple[int, int]]:
    """A szövegsorok tinta-sávjai: (első, utolsó) képpontsor, abszolút y-ban.

    Soronként a SAJÁT mediánjához képest mérünk sötétséget — így a gomb
    függőleges színátmenete nem számít bele, csak a betűk."""
    reszlet = tomb[y0:y1, x0:x1]
    median = np.median(reszlet, axis=1, keepdims=True)
    sotetseg = np.clip(median - reszlet, 0, None).sum(axis=1)
    if sotetseg.max() <= 0:
        return []
    hatar = sotetseg.max() * kuszob
    savok: list[tuple[int, int]] = []
    aktualis: list[int] | None = None
    for eltolas, ertek in enumerate(sotetseg):
        if ertek > hatar:
            aktualis = [eltolas, eltolas] if aktualis is None else [aktualis[0], eltolas]
        elif aktualis is not None:
            savok.append((y0 + aktualis[0], y0 + aktualis[1]))
            aktualis = None
    if aktualis is not None:
        savok.append((y0 + aktualis[0], y0 + aktualis[1]))
    return savok


def _alapvonal_tavolsag(savok: list[tuple[int, int]]) -> int:
    """A két szövegsor ALJÁNAK távolsága — ez az alapvonal-távolság.

    Miért az alja és nem a teteje: a felső sor tartalmazhat felnyúló betűt
    (V, J, ékezet), az alsó nem feltétlenül — a tetők távolsága ezért
    betűfüggő. Az alja (leszálló szárak nélkül) mindkét soron az alapvonal."""
    assert len(savok) == 2, f"két szövegsort vártam, {len(savok)} sávot mértem"
    return savok[1][1] - savok[0][1]


# ==========================================================================
# 0. Önellenőrzés — a kirajzolt őr nem mérhet ÜRES képet
# ==========================================================================
def test_a_panel_tartalma_egyaltalan_kirajzolodik(_panel_nezet):
    """⚠️ Ez az őr saját maga őre.

    A fájl első változata a panelt `anchors.fill: parent`-tel építette. A
    fülsáv ettől rejtve maradt, egyetlen csempe sem rajzolódott ki, a
    gombsor a panel tetejére csúszott — a felvétel egy fehér lap volt két
    gombbal. A sorköz-állítások ettől függetlenül ZÖLDEK voltak: a mérés
    tárgya hiányzott, nem a mérés bukott.

    Ezért mielőtt bármit állítanánk a képpontokról, kimondjuk, hogy a mért
    elemek TÉNYLEG ott vannak, ahol mérünk."""
    view, _root, _qt_app = _panel_nezet
    tomb, _ = _szurkekep(view)
    for nev in ("editTabFixes", "editToolAutocolor", "editUndoButton"):
        elem = _child(_root, nev)
        x, y, szelesseg, magassag = _ablakdoboz(view, elem)
        assert szelesseg > 0 and magassag > 0, f"{nev}: nulla méretű doboz"
        reszlet = tomb[y : y + magassag, x : x + szelesseg]
        assert reszlet.size > 0, f"{nev} doboza a felvételen kívülre esik"
        assert reszlet.min() < 245, (
            f"{nev} helyén a felvétel ÜRES (legsötétebb képpont "
            f"{reszlet.min():.0f}) — nincs mit mérni"
        )


# ==========================================================================
# #2494 — a Visszavonás-gomb kétsoros felirata
# ==========================================================================
def _undo_savok(panel_nezet, felirat: str):
    view, root, qt_app = panel_nezet
    panel = _child(root, "panel")
    panel.setProperty("undoLabel", felirat)
    _var_a_kirajzolasra(view, qt_app)
    gomb = _child(root, "editUndoButton")
    x, y, szelesseg, magassag = _ablakdoboz(view, gomb)
    tomb, _ = _szurkekep(view)
    savok = _tinta_savok(tomb, x + 3, x + szelesseg - 3, y + 1, y + magassag - 1)
    return gomb, (x, y, szelesseg, magassag), savok


def test_a_visszavonas_gomb_sorkoze_a_MERT_10(_panel_nezet):
    """#2494: a kétsoros felirat alapvonal-távolsága a KIRAJZOLT képen 10.

    ⚠️ Ez az az állítás, amit a visszaesés idején senki nem tett: az akkori
    őr csak azt kérdezte, elfér-e a felirat, és a gomb megnövelését is
    helyesnek látta."""
    _gomb, _doboz, savok = _undo_savok(_panel_nezet, KETSOROS_FELIRAT)
    tavolsag = _alapvonal_tavolsag(savok)
    assert abs(tavolsag - MERT_SORKOZ) <= 1, (
        f"a kirajzolt sorköz {tavolsag} képpont a mért {MERT_SORKOZ} helyett "
        f"(tinta-sávok: {savok})"
    )


@pytest.mark.parametrize(
    "felirat", ["Visszavonás", "Visszavonás: Jó napom van", KETSOROS_FELIRAT]
)
def test_a_gomb_kerete_a_MERT_26_marad(_panel_nezet, felirat):
    """#2494 VISSZAESÉS: a kétsoros felirat nem NÖVELHETI meg a gombot.

    A visszaesés pontosan ez volt: 26 helyett 38. Egysoros feliratnál sem
    változhat — a 26 nem „legalább", hanem a mért keret."""
    _gomb, doboz, _savok = _undo_savok(_panel_nezet, felirat)
    assert doboz[3] == MERT_GOMBKERET, (
        f"a(z) {felirat!r} feliratú gomb {doboz[3]} képpont magas a mért "
        f"{MERT_GOMBKERET} helyett"
    )


def test_a_ketsoros_felirat_TINTAJA_a_gombon_belul_van(_panel_nezet):
    """A hosszú felirat KIRAJZOLVA is belefér, fölötte-alatta valódi réssel.

    A felvételen az eredeti 26 képpontos gombjában a tinta 4-4 képpontnyi
    rést hagy; nálunk legalább 2-2 kell, különben a betűk a keretre ülnek."""
    _gomb, (_x, y, _sz, magassag), savok = _undo_savok(_panel_nezet, KETSOROS_FELIRAT)
    assert len(savok) == 2, f"a felirat nem tört két sorra: {savok}"
    felette = savok[0][0] - y
    alatta = (y + magassag) - savok[-1][1]
    assert felette >= 2 and alatta >= 2, (
        f"a felirat tintája a gomb keretére ül: fölötte {felette}, alatta "
        f"{alatta} képpont (gomb y={y}..{y + magassag}, sávok {savok})"
    )


@pytest.mark.parametrize(
    "felirat", ["Visszavonás", "Visszavonás: Jó napom van", KETSOROS_FELIRAT]
)
def test_a_felirat_tintaja_a_gomb_KOZEPEN_ul(_panel_nezet, felirat):
    """A felirat FÜGGŐLEGES KÖZEPE a gomb közepére esik — kirajzolva.

    Az eredetiben ezt a `m_buttonfontC` `YConstraint 0.5, 0.5, 0`-ja írja
    elő. A számított párja (`test_visszavonas_felirat_2494.py`) a szöveg
    DOBOZÁT méri; ez a tintát — a kettő nem ugyanaz, mert a doboz alján a
    leszálló szárak üres sávja is benne van.

    ⚠️ MUTÁCIÓVAL igazolva: a régi, `… / 2 - 5` alakú igazítást
    visszatéve az egysoros felirat tintája 5 képponttal a gomb közepe FÖLÉ
    kerül (306 a 311 helyett), és ez az őr pirosra vált. A `paintedHeight`
    alapú, számított őr ugyanezt átengedte."""
    _gomb, (_x, y, _sz, magassag), savok = _undo_savok(_panel_nezet, felirat)
    assert savok, "a feliratnak nincs tintája a felvételen"
    tinta_kozep = (savok[0][0] + savok[-1][1]) / 2
    gomb_kozep = y + magassag / 2
    assert abs(tinta_kozep - gomb_kozep) <= 2.5, (
        f"a(z) {felirat!r} felirat tintájának közepe {tinta_kozep:.1f}, a "
        f"gombé {gomb_kozep:.1f} — {tinta_kozep - gomb_kozep:+.1f} képpont "
        f"eltolás (sávok: {savok})"
    )


# ==========================================================================
# #2567 — az eszközcsempék kétsoros felirata
# ==========================================================================
def test_a_csempefelirat_sorkoze_a_MERT_10(_panel_nezet):
    """#2567: ugyanaz a hiba a csempéken — MÉRVE 13 volt a 10 helyett.

    A csempe feliratát KÖZVETLENÜL állítjuk be: a tesztkörnyezet nem
    fordít, az angol „Auto Contrast" pedig egy sorba fér, tehát a hibás
    esetet nem idézné elő."""
    view, root, qt_app = _panel_nezet
    cimke = _child(root, "editToolAutocolorLabel")
    csempe = _child(root, "editToolAutocolor")
    csempe.setProperty("label", KETSOROS_CSEMPE)
    _var_a_kirajzolasra(view, qt_app)

    x, y, szelesseg, magassag = _ablakdoboz(view, cimke)
    tomb, _ = _szurkekep(view)
    savok = _tinta_savok(tomb, x, x + szelesseg, y, y + magassag + 4)
    tavolsag = _alapvonal_tavolsag(savok)
    assert abs(tavolsag - MERT_SORKOZ) <= 1, (
        f"a csempefelirat kirajzolt sorköze {tavolsag} képpont a mért "
        f"{MERT_SORKOZ} helyett (tinta-sávok: {savok})"
    )

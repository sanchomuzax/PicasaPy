"""A „Megjelenítés és szerkesztés" HATÁSA, kirajzolva — #1001.

A `collageEditRequested` jelzést a vezérlő kibocsátotta, de a teljes
`Main.qml` fában NEM volt fogadója: a gomb, a duplakattintás és a helyi
menü tétele egyaránt hatástalan maradt egy **kiadott** (0.8.1) verzióban.

## Miért nem elég a jelzést mérni

A #948 tesztje ezt állította:

```python
_kivalt(panel, "collageMenuViewAndEdit")
assert len(kertek) == 1                     # a jelzés elment
```

Ez a mai, HIBÁS kódon is zöld — pontosan ezért maradt a hiba észrevétlen.
Egy jelzés önmagában nem funkció; a felhasználó azt látja, hogy a kép
megnyílik-e a szerkesztőben. Ez a fájl ezért **soha nem a jelzésre**, hanem
mindig a következményre kérdez:

* a néző (és vele a szerkesztő bal panelje) **elöl van**, és
* **azt a képet** mutatja, amelyiket a felhasználó kiválasztotta, és
* a **kollázs lapja közben nyitva marad** (a jegy harmadik feltétele).

Mindhárom belépési pontra külön eset jut: a gomb (`CollageRandomRow`), a
duplakattintás (`CollageNode`) és a helyi menü tétele
(`CollageContextMenus`).

## Miért a VALÓDI `Main.qml`-ben mérünk

A komponens-tesztek mesterséges burokban építik fel a panelt, ahol a
`controller` kézzel kapott értéket — a hiányzó láncszem viszont éppen a
gazdában (`Main.qml`) volt. A `qml_app` fixture-rel igazi `AppController`,
igazi `Main.qml`, igazi ablak épül fel; a hiba csak így mérhető.

## Két csapda, amit ez a fájl kikerül

* a `Repeater` delegáltjait a `findChild` **nem** találja meg — a VIZUÁLIS
  fát kell bejárni (`_walk`, a #651/#985 mintájából);
* fejnélküli környezetben az elrendezés **nem** fut le egyetlen
  `processEvents()` után (#918), ezért kattintás előtt megvárjuk, hogy a
  geometria STABIL legyen — a main ubuntu-lába pontosan ezen piroslott.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

# --------------------------------------------------------------------------
# Segédek — a #985-ös fájl bevált mintája
# --------------------------------------------------------------------------


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `Repeater` elemei csak itt látszanak."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _keres(window, nev: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == nev:
            return item
    return window.findChild(QObject, nev)


def _elem(window, nev: str) -> QQuickItem:
    talalt = _keres(window, nev)
    assert talalt is not None, f"a(z) {nev} nincs a kirajzolt jelenetben"
    return talalt


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő)."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _kozeppont(item: QQuickItem) -> tuple[float, float]:
    pont = item.mapToScene(item.boundingRect().center())
    return (pont.x(), pont.y())


def _stabil_kozeppont(item: QQuickItem, qt_app) -> QPoint:
    """A kattintás helye CSAK stabil elrendezés után számolható ki.

    A `_var` a KÖVETKEZMÉNYT várja ki; ha a koordináta már eleve rossz (az
    elem még 0 méretű, vagy nem a végleges helyén áll), az esemény a
    semmibe megy, és utólag semmilyen várakozás nem javítja."""
    _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    elozo = _kozeppont(item)
    _var(qt_app, lambda: _kozeppont(item) == elozo)
    x, y = _kozeppont(item)
    return QPoint(round(x), round(y))


def _kattints(window, item: QQuickItem, qt_app) -> None:
    pont = _stabil_kozeppont(item, qt_app)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    qt_app.processEvents()
    QTest.qWait(30)
    qt_app.processEvents()


def _duplan_kattints(window, item: QQuickItem, qt_app, amig=None) -> None:
    """Valódi duplakattintás; `amig` a kattintás KÖVETKEZMÉNYE.

    #1463: korábban a kattintás után fix `QTest.qWait(30)` állt, a hívó
    pedig azonnal állított — vagyis a teszt arra fogadott, hogy 30 ms elég.
    Terhelt, négymagos gépen ez hamis pirosat ad. Az `amig` predikátummal a
    hívóhely megmondja, MIRE vár, és a várakozás azonnal továbbenged, amint
    az bekövetkezett."""
    pont = _stabil_kozeppont(item, qt_app)
    QTest.mouseDClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    qt_app.processEvents()
    if amig is None:
        # Nincs megnevezett következmény: marad a fali óra. Új hívónál ez ne
        # maradjon így — a hívóhelyre illő feltételt kell megadni.
        QTest.qWait(30)
    else:
        assert _var(qt_app, amig), "#2408: a vart allapot nem allt be idoben"
    qt_app.processEvents()


def _kivalt(window, nev: str, qt_app) -> None:
    """A `MenuItem`-nek nincs hívható `trigger()`-e — a `triggered` SIGNAL
    kiváltása futtatja az `onTriggered` kezelőt (a #948 mintája)."""
    tetel = window.findChild(QObject, nev)
    assert tetel is not None, f"a(z) {nev} menütétel nincs meg"
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _menusor(window):
    bar = window.property("menuBar")
    assert bar is not None, "nincs menüsor"
    return bar


def _kollazs_lapot_nyit(window, qt_app, sorok=(0, 1)) -> None:
    """A VALÓDI út: a Létrehozás menü jelzését sütjük el (#936 tanulsága)."""
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", int(sorok[0]))
    qt_app.processEvents()
    bar = _menusor(window)
    bar.metaObject().invokeMethod(bar, "collageRequested")
    qt_app.processEvents()


def _azonos_utvonal(egyik: str, masik: str) -> bool:
    """Útvonal-egyezés a platform elválasztójától függetlenül.

    A csomópont útvonalát a `Path` építi (Windowson `\\`), a fotómodellé
    `/`-t használ — a nyers sztring-hasonlítás a windows-lábon némán bukna
    (#190 tanulsága útvonalakra)."""
    return Path(egyik) == Path(masik)


# --------------------------------------------------------------------------
# Fixture — nyitott kollázs-lap, két képpel
# --------------------------------------------------------------------------


@pytest.fixture
def kollazs(qml_app, qt_app):
    """(window, controller) nyitott Kollázs-lappal, kirajzolt vászonnal."""
    window, controller = qml_app[0], qml_app[1]
    window.resize(1280, 800)
    qt_app.processEvents()
    _kollazs_lapot_nyit(window, qt_app)
    assert _var(qt_app, lambda: controller.property("collageOpen") is True), (
        "a Kollázs lap nem nyílt meg — a teszt előfeltétele hiányzik"
    )
    assert _var(qt_app, lambda: controller.property("collageClipCount") == 2), (
        "nem két kép került a vászonra"
    )
    assert _var(qt_app, lambda: _keres(window, "collageNode1") is not None), (
        "a csomópontok nem rajzolódtak ki"
    )
    return window, controller


def _csomopont_utvonal(controller, index: int) -> str:
    return controller.collageNodes.nodes[index].path


def _nezoben_latott_utvonal(window, controller) -> str:
    """Amit a szerkesztő TÉNYLEGESEN mutat — a néző sorindexéből."""
    nezo = _elem(window, "photoViewer")
    sor = int(nezo.property("currentIndex"))
    return str(controller.photos.filePathAt(sor))


def _kijelol(controller, qt_app, index: int) -> None:
    controller.setCollageSelection([index])
    qt_app.processEvents()


def _allitsd_hogy_a_szerkeszto_nyilt_meg(window, controller, qt_app, index: int):
    """A jegy MÉRCÉJE: a szerkesztő elöl van, a megfelelő képpel.

    Négy állítás, mert négyféleképpen lehet félig kész a bekötés: a néző
    nem nyílik ki, kinyílik de rossz képpel, kinyílik de a szerkesztő-panel
    nem látszik, vagy kinyílik és közben elveszti a kollázs lapját."""
    varva = _csomopont_utvonal(controller, index)

    assert _var(qt_app, lambda: window.property("viewerOpen") is True), (
        'a „Megjelenítés és szerkesztés" után a szerkesztő NEM nyílt meg '
        "(a `collageEditRequested` jelzésnek nincs fogadója)"
    )
    nezo = _elem(window, "photoViewer")
    assert _var(qt_app, nezo.isVisible), "a néző nem látszik a jelenetben"

    assert _var(
        qt_app,
        lambda: _azonos_utvonal(_nezoben_latott_utvonal(window, controller), varva),
    ), (
        "a szerkesztő nem a kiválasztott képet mutatja: "
        f"{_nezoben_latott_utvonal(window, controller)!r} ≠ {varva!r}"
    )

    panel = _elem(window, "viewerEditorPanel")
    assert _var(qt_app, panel.isVisible), (
        "a szerkesztő bal panelje nem látszik — a kép csak megjelenik, "
        "de nem szerkeszthető"
    )

    assert controller.property("collageOpen") is True, (
        "a szerkesztő megnyitása BEZÁRTA a kollázs lapját — a jegy "
        "kifejezetten azt kéri, hogy nyitva maradjon"
    )


# --------------------------------------------------------------------------
# 1. A gomb (`CollageRandomRow`)
# --------------------------------------------------------------------------
class TestAGomb:
    def test_a_gomb_megnyitja_a_szerkesztot_a_kijelolt_keppel(self, kollazs, qt_app):
        window, controller = kollazs
        # a MÁSODIK képet választjuk: egy „mindig a nulladik sort nyitom"
        # megvalósítás így nem csúszhat át véletlenül
        _kijelol(controller, qt_app, 1)
        gomb = _elem(window, "collageViewAndEditButton")
        assert _var(qt_app, lambda: gomb.property("enabled") is True), (
            "a gomb egyetlen kijelölt képnél sem aktív — a teszt vakon menne át"
        )

        _kattints(window, gomb, qt_app)

        _allitsd_hogy_a_szerkeszto_nyilt_meg(window, controller, qt_app, 1)


# --------------------------------------------------------------------------
# 2. A duplakattintás (`CollageNode`)
# --------------------------------------------------------------------------
class TestADuplakattintas:
    def test_a_kepre_duplan_kattintva_megnyilik_a_szerkeszto(self, kollazs, qt_app):
        window, controller = kollazs
        csomopont = _elem(window, "collageNode1")

        # #1463: a poll feltétele PONTOSAN az, amit az alábbi állítás mér —
        # a bukás így az eredeti, beszédes állításon jelentkezik (kiírja a
        # tényleges kijelölést), nem a várakozáson.
        _duplan_kattints(
            window,
            csomopont,
            qt_app,
            amig=lambda: list(controller.collageSelection) == [1],
        )

        # a lenyomás maga jelöl ki (`picasa-eger-es-kijeloles.md` 2.) —
        # ha az esemény mégis másik képre esett, azt itt tudjuk meg, nem
        # egy félrevezető útvonal-eltérésből
        assert list(controller.collageSelection) == [1], (
            "a duplakattintás nem az 1-es csomópontra esett "
            f"(kijelölés: {list(controller.collageSelection)})"
        )
        _allitsd_hogy_a_szerkeszto_nyilt_meg(window, controller, qt_app, 1)

    def test_a_gyuru_peremen_a_duplakattintas_NEM_nyit_szerkesztot(
        self, kollazs, qt_app
    ):
        """A gyűrű PEREME a forgató-méretező fogantyú (spec 7.2).

        A duplakattintás-kezelő a gyűrűn is ott van — enélkül a kijelölt
        képen néma maradna —, de csak a BELSŐ (mozgató) zónában szabad
        parancsot indítania."""
        window, controller = kollazs
        _kijelol(controller, qt_app, 1)
        gyuru = _elem(window, "collageRing1")
        assert _var(qt_app, gyuru.isVisible), "a gyűrű nem látszik"
        kozep = _stabil_kozeppont(gyuru, qt_app)
        # 48 (belső sugár) < 57 < 66 (külső sugár) — biztosan a peremen
        perem = QPoint(kozep.x() + 57, kozep.y())

        QTest.mouseDClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            perem,
        )
        qt_app.processEvents()
        QTest.qWait(50)
        qt_app.processEvents()

        assert window.property("viewerOpen") is False, (
            "a forgató-fogantyún indított duplakattintás megnyitotta a "
            "szerkesztőt — a gyűrű belseje és pereme más parancs"
        )


# --------------------------------------------------------------------------
# 3. A helyi menü tétele (`CollageContextMenus`)
# --------------------------------------------------------------------------
class TestAHelyiMenu:
    def test_a_menutetel_megnyitja_a_szerkesztot(self, kollazs, qt_app):
        window, controller = kollazs
        _kijelol(controller, qt_app, 1)

        _kivalt(window, "collageMenuViewAndEdit", qt_app)

        _allitsd_hogy_a_szerkeszto_nyilt_meg(window, controller, qt_app, 1)


# --------------------------------------------------------------------------
# 4. A visszaút — a kollázs lapja nyitva marad
# --------------------------------------------------------------------------
class TestVisszaAKollazshoz:
    """A jegy harmadik feltétele: „a kollázs lapja közben nyitva marad"."""

    def test_a_szerkesztobol_kilepve_a_kollazs_lap_megvan(self, kollazs, qt_app):
        window, controller = kollazs
        _kijelol(controller, qt_app, 0)
        _kivalt(window, "collageMenuViewAndEdit", qt_app)
        assert _var(qt_app, lambda: window.property("viewerOpen") is True)

        # „Vissza a könyvtárhoz" (`editpanel/albumview`) — a gombnak nincs
        # objectName-je, a jelzését sütjük el, ahogy a menüsornál is
        nezo = _elem(window, "photoViewer")
        nezo.metaObject().invokeMethod(nezo, "closed")
        assert _var(qt_app, lambda: window.property("viewerOpen") is False)

        sav = _elem(window, "documentTabStrip")
        assert _var(qt_app, lambda: sav.property("hasProjectTabs") is True), (
            "a kollázs lapja eltűnt a fülsávból — a szerkesztő bezárta"
        )
        assert controller.property("collageOpen") is True

    def test_van_lathato_visszaut_a_kollazshoz(self, kollazs, qt_app):
        """A felhasználónak LÁTNIA kell, hogyan jut vissza."""
        window, controller = kollazs
        _kijelol(controller, qt_app, 0)
        _kivalt(window, "collageMenuViewAndEdit", qt_app)
        assert _var(qt_app, lambda: window.property("viewerOpen") is True)
        nezo = _elem(window, "photoViewer")
        nezo.metaObject().invokeMethod(nezo, "closed")
        assert _var(qt_app, lambda: window.property("viewerOpen") is False)

        #: #1939: a visszaút az ALSÓ SÁV üzenetsávjában van
        #: (`traySingleActionReturn`), nem lebegő gombként a jobb felső
        #: sarokban. Az állítás lényege ugyanaz: a felhasználónak LÁTNIA
        #: kell, hogyan jut vissza.
        gomb = _elem(window, "traySingleActionReturn")
        assert _var(qt_app, gomb.isVisible), (
            "a szerkesztőből kilépve nincs látható visszaút a kollázshoz"
        )

        _kattints(window, gomb, qt_app)
        sav = _elem(window, "documentTabStrip")
        assert _var(qt_app, lambda: sav.property("activeTabId") == "collage"), (
            'a „Vissza a kollázshoz" gomb nem váltott vissza a lapra'
        )
        panel = _elem(window, "collagePanel")
        assert _var(qt_app, panel.isVisible), "a kollázs-panel nem jött elő"

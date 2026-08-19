"""A KÖNYVTÁR PANELJE egészben eltűnik a projekt-lapon — #1026, KIRAJZOLVA.

## Mit látott a felhasználó

Két képernyőképet tett egymás mellé (eredeti Picasa 3 vs. PicasaPy 0.8.4),
azonos beállítással, kollázs-módban. Nálunk ott maradt a felső eszközsáv
(Importálás, csillag-szűrők, keresés) és az alsó tálca-/kimeneti sáv
(kép-számláló, E-mail, Nyomtatás, Exportálás) — az eredetiben egyik sincs.

## Miért NEM „rejtsünk el két sávot"

A `panelroot.tre` szerint az eredetiben nincs ilyen elrejtő szabály; a
jelenség SZERKEZETI:

```
panelroot/mainuipanel:  root      ← a KÖNYVTÁR panelja
panelroot/collagepanel: root      ← a KOLLÁZS panelja, TESTVÉR
    YConstraint 0, 0, tabdiv      ← a felső éle a FÜLSÁV alatt
    YConstraint 1, 1, 0           ← az alsó éle az ABLAK alján
panelroot/globaltabs: panelroot/tabback   ← a fülsáv MINDKETTŐN kívül
```

A `thumbui.tre` szerint pedig a két sáv a `mainuipanel` GYEREKE
(`importbutton`, `sbutton`, `timelinebutton`, `globalmode`,
`bottombevel_base`, `#include outputlayout.tre`). Vagyis nem a sávok
rejtőznek el: a könyvtár panelja tűnik el, és a sávok abban vannak.

Ezért ez a fájl NEM sávonként állít. A `TestAKeretEgeszbenTunikEl` a keret
MINDEN darabját EGY paraméterezett esetben járja végig, és az
`AZ_ELREJTENDO_KERET` lista a szerződés: aki új darabot tesz a könyvtár
keretébe, ide is felveszi, különben a következő kör pont azt felejtené el,
amit a felhasználó megint jelezne.

## És miért mérünk magasságot, nem property-t

A jegy elfogadási feltétele terület-nyereség: „a vászon a fülsáv alatti
teljes területet kapja, az ablak aljáig". Egy `visible: false` kötés ezt
NEM bizonyítja — a sáv attól még foglalhat helyet (pl. ha az
`ApplicationWindow` nem venné vissza a `header`/`footer` területét). Ezért
a `TestAVaszonMegkapjaATeruletet` a KIRAJZOLT geometriát olvassa, és a
nyereséget képpontban is kimondja.

Beégetett képpont-küszöb sehol: a sávok magassága platformfüggő (a #985
mérte, hogy ugyanaz a szöveg Linuxon 14, Windowson 12 px). Minden állítás
az ABLAKHOZ és a szomszédokhoz viszonyít.
"""

import time

import pytest
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

# --------------------------------------------------------------------------
# Segédek (a #985 tesztfájljának bevált mintája szerint)
# --------------------------------------------------------------------------
# A KÖNYVTÁR kerete: minden darab, aminek a projekt-lapon el kell tűnnie.
# A `header` az eszközsáv (`thumbui/importbutton`+`sbutton`+`globalmode`),
# a `footer` az alsó tálca- ÉS kimeneti sáv (`bottombevel_base` +
# `outputlayout.tre`), a `mainSplit` pedig a könyvtár tartalma.
AZ_ELREJTENDO_KERET = ("header", "mainSplit", "footer")


def _walk(item: QQuickItem):
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


def _ablakban(item: QQuickItem) -> tuple[float, float, float, float]:
    """Az elem doboza az ABLAK koordinátarendszerében (x, y, szél., mag.)."""
    sarok = item.mapToScene(item.boundingRect().topLeft())
    return (sarok.x(), sarok.y(), item.width(), item.height())


def _kozeppont(item: QQuickItem) -> tuple[float, float]:
    pont = item.mapToScene(item.boundingRect().center())
    return (pont.x(), pont.y())


def _kattints(window, item: QQuickItem, qt_app) -> None:
    """VALÓDI kattintás — a helyét csak STABIL geometria után számoljuk.

    Fejnélküli környezetben az elrendezés késik (#918), és a #985 ubuntu-
    lába pontosan azon bukott, hogy a kattintás a fül mellé esett."""
    _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    kozep_x, kozep_y = _kozeppont(item)
    _var(qt_app, lambda: _kozeppont(item) == (kozep_x, kozep_y))
    kozep_x, kozep_y = _kozeppont(item)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep_x), round(kozep_y)),
    )
    qt_app.processEvents()
    QTest.qWait(30)
    qt_app.processEvents()


def _menusor(window):
    bar = window.property("menuBar")
    assert bar is not None, "nincs menüsor"
    return bar


def _keret_darab(window, nev: str) -> QQuickItem:
    """A könyvtár-keret egy darabja névről.

    A `header`/`footer` az `ApplicationWindow` saját property-je (a
    vizuális bejárás nem éri el őket, mert nem a tartalomterület gyerekei),
    a többit a jelenetből keressük."""
    if nev in ("header", "footer"):
        item = window.property(nev)
        assert item is not None, f"nincs {nev} az ablakon"
        return item
    return _elem(window, nev)


def _kollazs_lapot_nyit(window, qt_app, sorok=(0, 1)) -> None:
    """A VALÓDI út: a Létrehozás menü jelzését sütjük el (#936 tanulsága)."""
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", int(sorok[0]))
    qt_app.processEvents()
    bar = _menusor(window)
    bar.metaObject().invokeMethod(bar, "collageRequested")
    qt_app.processEvents()
    sav = _elem(window, "documentTabStrip")
    assert _var(qt_app, lambda: sav.property("activeTabId") == "collage"), (
        "a Kollázs lap nem lett aktív"
    )
    # az elrendezésnek le KELL futnia, mielőtt geometriát olvasunk
    panel = _elem(window, "collagePanel")
    assert _var(qt_app, lambda: panel.isVisible() and panel.height() > 0)


def _konyvtar_fulre(window, qt_app) -> None:
    """VALÓDI kattintás a rögzített Könyvtár fülre (nem property-írás)."""
    sav = _elem(window, "documentTabStrip")
    for _ in range(3):
        if sav.property("activeTabId") == "library":
            return
        _kattints(window, _elem(window, "documentTabLibrary"), qt_app)
        if _var(qt_app, lambda: sav.property("activeTabId") == "library", 1.0):
            return
    raise AssertionError("a Könyvtár fülre kattintás nem váltott lapot")


# --------------------------------------------------------------------------
# 1. A keret EGÉSZBEN tűnik el
# --------------------------------------------------------------------------
class TestAKeretEgeszbenTunikEl:
    """Nem sávonként: a lista MINDEN darabjára ugyanaz az állítás fut."""

    @pytest.mark.parametrize("darab", AZ_ELREJTENDO_KERET)
    def test_a_konyvtar_kerete_nem_latszik_a_kollazs_lapon(
        self, qml_app, qt_app, darab
    ):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        item = _keret_darab(window, darab)
        assert _var(qt_app, lambda: item.isVisible() is False), (
            f"a könyvtár keretének „{darab}” darabja a kollázs-lapon is "
            "látszik — az eredetiben a KÖNYVTÁR PANELJE tűnik el egészben, "
            "és ez a darab abban van (`thumbui.tre`: a `mainuipanel` gyereke)"
        )

    def test_a_konyvtar_kerete_helyet_sem_foglal(self, qml_app, qt_app):
        """A `visible: false` kevés: a sáv attól még elvehetné a helyet.

        Az `ApplicationWindow` csak akkor adja vissza a `header`/`footer`
        területét a tartalomnak, ha az elem tényleg láthatatlan — ezt a
        tartalomterület TETEJE és ALJA mutatja meg."""
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        panel = _elem(window, "collagePanel")
        tartalom = panel.parentItem()
        _, tartalom_y, _, tartalom_h = _ablakban(tartalom)
        menu_h = _menusor(window).property("height")
        assert round(tartalom_y) == round(menu_h), (
            f"a tartalomterület {tartalom_y:.0f} px-nél kezdődik, a menüsor "
            f"alja viszont {menu_h:.0f} — valami sáv még helyet foglal fölötte"
        )
        assert round(tartalom_y + tartalom_h) == round(window.height()), (
            f"a tartalomterület alja {tartalom_y + tartalom_h:.0f} px, az "
            f"ablaké {window.height()} — valami sáv még helyet foglal alatta"
        )

    def test_a_keresojavaslatok_sem_lognak_at_a_lapra(self, qml_app, qt_app):
        """A keresődoboz a keret része — a javaslat-buborék se úszhat rá.

        A felhasználó gépel a keresőbe, majd megnyitja a Kollázs lapot: a
        `toolbar.searchText` megmarad, tehát a buborék kötése önmagában
        igazat adna."""
        window = qml_app[0]
        buborek = _elem(window, "searchSuggestions")
        # a keresőmező szövege hajtja a buborék kötését (`searchText` alias)
        _elem(window, "searchField").setProperty("text", "ke")
        buborek.setProperty(
            "suggestions",
            [{"kind": "folder", "name": "kepek", "count": 2, "param": "/kepek"}],
        )
        assert _var(qt_app, buborek.isVisible), (
            "a buborék a KÖNYVTÁR lapján sem jelent meg — az őrnek nincs foga"
        )
        _kollazs_lapot_nyit(window, qt_app)
        assert _var(qt_app, lambda: buborek.isVisible() is False), (
            "a kereső javaslat-buboréka a kollázs-lapra úszott"
        )


# --------------------------------------------------------------------------
# 2. A menüsor és a fülsáv MARAD
# --------------------------------------------------------------------------
class TestAMenusorEsAFulsavMarad:
    """A fülsáv az eredetiben MINDKÉT panelen kívül van (`panelroot`)."""

    def test_a_menusor_latszik(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        bar = _menusor(window)
        assert _var(qt_app, lambda: bar.property("visible") is True), (
            "a menüsor eltűnt a kollázs-lapon — az a panelen KÍVÜL van"
        )
        assert bar.property("height") > 0

    def test_a_fulsav_latszik_es_magassaga_megmarad(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        sav = _elem(window, "documentTabStrip")
        vart = sav.property("savMagassag")
        assert _var(qt_app, lambda: sav.isVisible() and sav.height() == vart), (
            f"a fülsáv {sav.height()} px magas (várt: {vart})"
        )

    def test_a_fulsav_kozvetlenul_a_menusor_alatt_van(self, qml_app, qt_app):
        """Eltűnt eszközsávnál a fülsáv feljebb csúszik — pont a menüsor alá.

        Ez az eredeti `panelroot/globaltabs` helye: a menüsor alatt, és a
        panelek FÖLÖTT."""
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        sav = _elem(window, "documentTabStrip")
        _, sav_y, _, _ = _ablakban(sav)
        menu_h = _menusor(window).property("height")
        assert round(sav_y) == round(menu_h), (
            f"a fülsáv {sav_y:.0f} px-nél kezdődik, a menüsor alja "
            f"{menu_h:.0f} — maradt közöttük egy sáv"
        )


# --------------------------------------------------------------------------
# 3. A vászon megkapja a felszabaduló területet — MÉRVE
# --------------------------------------------------------------------------
class TestAVaszonMegkapjaATeruletet:
    @pytest.mark.parametrize("meret", [(1024, 700), (1280, 800), (1600, 900)])
    def test_a_lap_magassaga_az_ablak_minusz_menusor_minusz_fulsav(
        self, qml_app, qt_app, meret
    ):
        """A jegy elfogadási feltétele, szó szerint."""
        window = qml_app[0]
        window.resize(*meret)
        _kollazs_lapot_nyit(window, qt_app)
        panel = _elem(window, "collagePanel")
        sav = _elem(window, "documentTabStrip")
        menu_h = _menusor(window).property("height")
        vart = window.height() - menu_h - sav.height()
        assert _var(qt_app, lambda: abs(panel.height() - vart) <= 2), (
            f"a kollázs-panel {panel.height():.0f} px magas, az ablak "
            f"({window.height()}) − menüsor ({menu_h:.0f}) − fülsáv "
            f"({sav.height():.0f}) = {vart:.0f} px-nek kellene lennie"
        )

    def test_a_panel_alja_az_ablak_alja(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        panel = _elem(window, "collagePanel")
        _, panel_y, _, panel_h = _ablakban(panel)
        assert round(panel_y + panel_h) == round(window.height()), (
            f"a kollázs-panel alja {panel_y + panel_h:.0f} px, az ablaké "
            f"{window.height()} — az alsó sáv még elveszi a helyet"
        )

    def test_a_panel_teteje_a_fulsav_alja(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        panel = _elem(window, "collagePanel")
        sav = _elem(window, "documentTabStrip")
        _, sav_y, _, sav_h = _ablakban(sav)
        _, panel_y, _, _ = _ablakban(panel)
        assert round(panel_y) == round(sav_y + sav_h), (
            "a kollázs-panel nem közvetlenül a fülsáv alatt kezdődik"
        )

    def test_a_nyereseg_pont_a_ket_sav_magassaga(self, qml_app, qt_app):
        """A MÉRT szám: mennyivel nő a vászon területe.

        A könyvtár tartalma (`mainSplit`) és a kollázs panelje ugyanazt a
        tartalomterületet kapja, csak a kollázsé a két sáv magasságával
        nagyobb — és a fülsáv magasságával kisebb (a fülsáv üres
        könyvtárban 0 magas, nyitott lapon nem)."""
        window = qml_app[0]
        oszto = _elem(window, "mainSplit")
        assert _var(qt_app, lambda: oszto.height() > 0)
        konyvtar_h = oszto.height()
        eszkozsav_h = window.property("header").property("height")
        talcasav_h = window.property("footer").property("height")

        _kollazs_lapot_nyit(window, qt_app)
        panel = _elem(window, "collagePanel")
        sav = _elem(window, "documentTabStrip")
        nyereseg = eszkozsav_h + talcasav_h - sav.height()
        vart = konyvtar_h + nyereseg
        assert _var(qt_app, lambda: abs(panel.height() - vart) <= 2), (
            f"a vászon {panel.height():.0f} px magas; a könyvtár tartalma "
            f"{konyvtar_h:.0f} volt, az eszközsáv {eszkozsav_h:.0f}, az alsó "
            f"sáv {talcasav_h:.0f}, a fülsáv {sav.height():.0f} → "
            f"{vart:.0f} px-nek kellene lennie"
        )
        assert nyereseg > 0, "a javítás nem hozott területet a vászonnak"


# --------------------------------------------------------------------------
# 4. Visszaváltva MINDEN visszajön
# --------------------------------------------------------------------------
class TestVisszavaltvaMindenVisszajon:
    @pytest.mark.parametrize("darab", AZ_ELREJTENDO_KERET)
    def test_a_keret_darabja_visszajon(self, qml_app, qt_app, darab):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        _konyvtar_fulre(window, qt_app)
        item = _keret_darab(window, darab)
        assert _var(qt_app, lambda: item.isVisible() is True), (
            f"a könyvtár keretének „{darab}” darabja nem jött vissza a "
            "Könyvtár fülre visszaváltva"
        )

    def test_a_konyvtar_tartalma_ugyanaz_az_objektum_marad(self, qml_app, qt_app):
        """A #944 kimérte: `visible`-lel kell kapcsolni, NEM `Loader.active`-kal.

        Az utóbbi megsemmisítené a feedet, és vele a görgetési pozíciót meg a
        kijelölést."""
        window = qml_app[0]
        elotte = _elem(window, "mainSplit")
        _kollazs_lapot_nyit(window, qt_app)
        _konyvtar_fulre(window, qt_app)
        utana = _elem(window, "mainSplit")
        assert elotte is utana, (
            "a könyvtár tartalma újraépült a lapváltás során — a rejtés "
            "megsemmisítette (`Loader.active`?), így elveszne a görgetés"
        )

    def test_a_kijeloles_tulel(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app, sorok=(0, 1))
        _konyvtar_fulre(window, qt_app)
        assert list(window.property("selectedIndexes")) == [0, 1], (
            "a kijelölés nem élte túl a lapváltást"
        )

    def test_a_tartalomterulet_visszakapja_a_savokat(self, qml_app, qt_app):
        """Visszaváltva a `mainSplit` ismét a két sáv KÖZÖTT áll."""
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        _konyvtar_fulre(window, qt_app)
        oszto = _elem(window, "mainSplit")
        assert _var(qt_app, lambda: oszto.isVisible() and oszto.height() > 0)
        _, oszto_y, _, oszto_h = _ablakban(oszto)
        menu_h = _menusor(window).property("height")
        eszkozsav_h = window.property("header").property("height")
        talcasav_h = window.property("footer").property("height")
        sav = _elem(window, "documentTabStrip")
        assert round(oszto_y) == round(menu_h + eszkozsav_h + sav.height()), (
            "a könyvtár tartalma nem a fülsáv alá került vissza"
        )
        assert round(oszto_y + oszto_h) == round(window.height() - talcasav_h), (
            "a könyvtár tartalma nem az alsó sávig ér vissza"
        )

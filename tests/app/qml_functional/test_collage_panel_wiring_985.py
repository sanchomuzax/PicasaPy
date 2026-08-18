"""A Kollázs-panel BEKÖTÉSE az alkalmazásba, KIRAJZOLVA — #985.

Ez a #920-as sorozat zárófájlja. A nyolc rész (#942–#949) mind elkészült, de
a felhasználó egyiket sem érte el: az `AppController` nem örökölte a
`CollageMixin`-t, a `Main.qml` pedig nem ismerte sem a `DocumentTabStrip`-et,
sem a `CollagePanel`-t. A hiányzó két kötést ez a fájl őrzi.

## Miért a VALÓDI `Main.qml`-ben mérünk

A nyolc rész saját tesztje mind **mesterséges burokban** építette fel a
panelt (`support/collage_canvas_harness._panel()`): ott a `controller`
property kézzel kapott értéket, és a panel az ablak teljes területét kapta.
A felhasználó viszont a `Main.qml` ős-láncát látja — menüsor, eszköztár,
fülsáv, `SplitView` —, és pontosan az a láncszem hiányzott, amit egyetlen
komponens-teszt sem érintett. Ezért itt a `qml_app` fixture-t töltjük be:
igazi `AppController`, igazi `Main.qml`, igazi ablak.

## A jegy elfogadási feltétele — és hogyan bizonyítjuk

> A felhasználó megnyitja a Kollázs lapot, elrendezést és keretet vált,
> megfog egy képet, elhúzza, elforgatja, és a **mentett kép PONTOSAN azt
> mutatja, amit a vásznon látott**.

A `TestAMentettKepAzAmitLatott` osztály ezt a teljes láncot végigviszi
valódi kattintásokkal és valódi egérhúzással, majd **két független lábon**
állítja a záró egyenlőséget:

1. **képpont-láb** — a KIRAJZOLT vászonról leolvassuk, hova került az
   elhúzott kép a lapon (arányban), és a mentett JPEG **ugyanazon a helyen**
   annak a képnek a színét mutatja. Nem SHA/MD5: a beégetett képpont-hash a
   platformot is szerződésbe foglalná (a Windows-láb némán bukna rajta) —
   itt a *tartalom* van állítva, nem a bájtsorozat.
2. **geometria-láb** — a JPEG mellé írt `.cxf` csomópont-geometriája
   (középpont arányban, szög radiánban) megegyezik azzal, amit a vásznon
   mértünk.

Egy leg önmagában elhihető volna véletlenül is; a kettő együtt csak akkor
teljesül, ha a modell → vászon → mentés lánc végig ugyanazt az állapotot
hordozza.

## Három csapda, amit ez a fájl kikerül

* a `Repeater` delegáltjait a `findChild` **nem** találja meg — a VIZUÁLIS
  fát kell bejárni (`_walk`, a #651-es mintából);
* fejnélküli (offscreen) környezetben az elrendezés **nem** fut le egyetlen
  `processEvents()` után (#918), ezért minden mérés előtt `_var()` pörgeti
  az eseményeket határidővel;
* a `visible` öröklődik a szülőtől, ezért a fülsáv regresszió-mentességét
  nem láthatósággal, hanem a tartalomterület **helyével** állítjuk.
"""

from __future__ import annotations

import math
import time

import pytest
from PIL import Image
from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

# --------------------------------------------------------------------------
# Segédek
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
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő).

    #918: fejnélküli környezetben az elrendezés késik — egyetlen
    `processEvents()` után a méretek még a kezdeti állapotot mutatják."""
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


def _eger_le(window, pont: QPoint) -> None:
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )


def _eger_fel(window, pont: QPoint) -> None:
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )


def _eger_mozog(window, pont: QPoint) -> None:
    """Egérmozgás nyomva tartott bal gombbal (a `QTest.mouseMove` nem viszi)."""
    helyi = QPointF(pont)
    esemeny = QMouseEvent(
        QEvent.Type.MouseMove,
        helyi,
        helyi,
        QPointF(window.mapToGlobal(pont)),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QGuiApplication.sendEvent(window, esemeny)


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


def _tolts_fel(controller, tmp_path, qt_app, darab: int = 60) -> None:
    """A teszt-könyvtár feltöltése, hogy a feed TÉNYLEG görgethető legyen.

    A `qml_app` fixture két képet tesz be; azzal a `contentY` beállítása
    hatástalan (a `ListView` visszaszorítja 0-ra), tehát a görgetés-megőrzést
    állító teszt vakon menne át."""
    from picasapy.index import open_index, sync_tree
    from support.jpeg_factory import make_jpeg

    lib = tmp_path / "kepek"
    for i in range(darab):
        make_jpeg(lib / f"z{i:03d}.jpg", size=(48, 36))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload()
    controller.selectFolder(str(lib))
    qt_app.processEvents()


def _fulsav(window):
    return _elem(window, "documentTabStrip")


def _konyvtar_fulre(window, qt_app) -> None:
    """VALÓDI kattintás a rögzített Könyvtár fülre (nem property-írás)."""
    _kattints(window, _elem(window, "documentTabLibrary"), qt_app)


def _kollazs_fulre(window, qt_app) -> None:
    """VALÓDI kattintás az első projekt-fülre."""
    _kattints(window, _elem(window, "documentTab0"), qt_app)


def _lap(window) -> QQuickItem:
    return _elem(window, "collageSheet")


def _lap_arany(item: QQuickItem, lap: QQuickItem) -> tuple[float, float]:
    """Egy elem közepe a LAP arányában (0…1, 0…1) — ezt látja a felhasználó."""
    kozep_x, kozep_y = _kozeppont(item)
    lap_x, lap_y, lap_w, lap_h = _ablakban(lap)
    return ((kozep_x - lap_x) / lap_w, (kozep_y - lap_y) / lap_h)


# --------------------------------------------------------------------------
# 1. A vezérlő bekötése (`controller.py`)
# --------------------------------------------------------------------------
class TestAVezerloBekotese:
    """A `CollageMixin` (és vele a `CollageSaveMixin`) az `AppController`-ben."""

    def test_az_appcontroller_ismeri_a_kollazs_mixint(self, qml_app):
        from picasapy.app.collage_controller import CollageMixin

        controller = qml_app[1]
        assert isinstance(controller, CollageMixin), (
            "az AppController nem örökli a CollageMixin-t — a QML-ből "
            "egyetlen kollázs-slot sem érhető el"
        )

    def test_az_appcontroller_ismeri_a_mentes_mixint(self, qml_app):
        from picasapy.app.collage_save import CollageSaveMixin

        assert isinstance(qml_app[1], CollageSaveMixin), (
            "a mentes szelete (#949) nincs bekotve - a Kollazs letrehozasa "
            "gomb nem talál slotot"
        )

    @pytest.mark.parametrize(
        "slot",
        [
            "openCollage",
            "closeCollage",
            "createCollage",
            "saveCollageDraft",
            "addClips",
            "setCollageTheme",
            "setCollageBorder",
        ],
    )
    def test_a_slot_a_QML_felol_is_meghivhato(self, qml_app, slot):
        """A QML nem Python-metódust hív, hanem Qt-slotot — ezt kell állítani."""
        meta = qml_app[1].metaObject()
        nevek = {
            meta.method(i).name().data().decode()
            for i in range(meta.methodCount())
        }
        assert slot in nevek, f"a(z) {slot} nem látszik a QML meta-objektumban"

    def test_a_collageOpen_property_letezik_es_zart(self, qml_app):
        assert qml_app[1].property("collageOpen") is False


# --------------------------------------------------------------------------
# 2. A fülsáv — és a regresszió-mentesség
# --------------------------------------------------------------------------
class TestFulsavEsRegresszio:
    """Üres fülsávnál a MAI elrendezés egyetlen képponttal sem csúszhat el."""

    def test_a_fulsav_ott_van_a_jelenetben(self, qml_app, qt_app):
        window = qml_app[0]
        assert _var(qt_app, lambda: _keres(window, "documentTabStrip") is not None)

    def test_ures_fulsavnal_a_savmagassag_nulla(self, qml_app, qt_app):
        window = qml_app[0]
        sav = _elem(window, "documentTabStrip")
        assert _var(qt_app, lambda: sav.height() == 0), (
            f"a fülsáv üresen {sav.height()} px magas — lejjebb tolja a "
            "tartalomterületet, tehát a mai felület megváltozott"
        )

    @pytest.mark.parametrize("meret", [(800, 534), (1280, 800), (1920, 1080)])
    def test_ures_fulsavnal_a_tartalom_a_terulet_TETEJEN_kezdodik(
        self, qml_app, qt_app, meret
    ):
        """A bekötés ELŐTT a `SplitView` `anchors.fill: parent` volt.

        A négy horgonyra bontás után ugyanoda kell esnie: a szülő tetejére
        és a szülő teljes magasságára. Beégetett képpont-küszöb helyett a
        SZÜLŐHÖZ mérünk (a menüsor és az eszköztár magassága platformfüggő,
        a betűméret Linuxon 14, Windowson 12 px volt ugyanarra a szövegre)."""
        window = qml_app[0]
        window.resize(*meret)
        oszto = _elem(window, "mainSplit")
        assert _var(qt_app, lambda: oszto.height() > 0)
        szulo = oszto.parentItem()
        assert _var(qt_app, lambda: oszto.height() == szulo.height()), (
            f"a tartalomterület {oszto.height():.0f} px magas, a szülő "
            f"{szulo.height():.0f} — az üres fülsáv helyet foglal"
        )
        assert round(oszto.y()) == 0, (
            f"a tartalomterület a szülőn belül {oszto.y():.0f} px-nél "
            "kezdődik, nem a 0. soron"
        )

    def test_nyitott_lapnal_a_fulsav_a_sajat_magassagat_veszi_fel(
        self, qml_app, qt_app
    ):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        sav = _elem(window, "documentTabStrip")
        vart = sav.property("savMagassag")
        assert _var(qt_app, lambda: sav.height() == vart), (
            f"nyitott lapnál a sáv {sav.height()} px (várt: {vart})"
        )
        assert sav.isVisible() is True

    def test_nyitott_lapnal_a_tartalom_a_sav_ALATT_kezdodik(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        sav = _elem(window, "documentTabStrip")
        panel = _elem(window, "collagePanel")
        assert _var(qt_app, lambda: panel.height() > 0)
        _, sav_y, _, sav_h = _ablakban(sav)
        _, panel_y, _, _ = _ablakban(panel)
        assert round(panel_y) == round(sav_y + sav_h), (
            "a kollázs-panel nem a fülsáv alatt kezdődik"
        )


# --------------------------------------------------------------------------
# 3. A belépési pontok — a lap NYÍLIK meg, nem modális ablak
# --------------------------------------------------------------------------
class TestBelepesiPontok:
    def test_a_letrehozas_menu_MEGNYITJA_a_kollazs_lapot(self, qml_app, qt_app):
        window, controller = qml_app[0], qml_app[1]
        _kollazs_lapot_nyit(window, qt_app)
        assert _var(qt_app, lambda: controller.property("collageOpen") is True), (
            "a Létrehozás menü jelzése nem nyitotta meg a Kollázs lapot"
        )

    def test_a_lap_megnyitasakor_a_panel_LATSZIK(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        panel = _elem(window, "collagePanel")
        assert _var(qt_app, panel.isVisible), "a Kollázs-panel nem látszik"

    def test_a_lap_megnyitasakor_a_konyvtar_ELREJTOZIK(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        oszto = _elem(window, "mainSplit")
        assert _var(qt_app, lambda: oszto.isVisible() is False), (
            "a könyvtár tartalma a kollázs-lap alatt maradt — a két lap "
            "egyszerre látszik"
        )

    def test_a_kijelolt_kepek_kerulnek_a_vasznara(self, qml_app, qt_app):
        window, controller = qml_app[0], qml_app[1]
        _kollazs_lapot_nyit(window, qt_app, sorok=(0, 1))
        assert _var(qt_app, lambda: controller.property("collageClipCount") == 2), (
            "a kijelölés nem került át a kollázsba"
        )

    def test_a_talca_gombja_is_a_LAPOT_nyitja(self, qml_app, qt_app):
        """#361: a képtálca kollázs-gombja ugyanoda visz, mint a menü."""
        window, controller = qml_app[0], qml_app[1]
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        tray = window.property("footer")
        assert tray is not None, "nincs képtálca-sáv"
        tray.metaObject().invokeMethod(tray, "collageRequested")
        assert _var(qt_app, lambda: controller.property("collageOpen") is True), (
            "a tálca kollázs-gombja nem a Kollázs lapot nyitja"
        )


# --------------------------------------------------------------------------
# 4. Fülváltás — a könyvtár állapota TÚLÉLI
# --------------------------------------------------------------------------
class TestAKonyvtarAllapotaTulel:
    """Ezt rontaná el a `Loader.active`: a feed megsemmisülne.

    A három állítás pont azt a három dolgot méri, ami egy újraépített
    feednél elveszne: az OBJEKTUM azonossága, a görgetési hely és a
    kijelölés. Aki `visible` helyett `Loader.active`-ot ír, mind a hármat
    elbuktatja.
    """

    def test_a_feed_UGYANAZ_az_objektum_marad(self, qml_app, qt_app):
        window = qml_app[0]
        elotte = _elem(window, "photoGrid")
        _kollazs_lapot_nyit(window, qt_app)
        sav = _fulsav(window)
        assert _var(qt_app, lambda: sav.property("activeTabId") != "library")
        _konyvtar_fulre(window, qt_app)
        assert _var(qt_app, lambda: sav.property("activeTabId") == "library")
        utana = _elem(window, "photoGrid")
        assert utana is elotte, (
            "a könyvtár-feed újraépült a fülváltás során — a Loader.active "
            "megsemmisítette; `visible`-lel kellene kapcsolni"
        )

    def test_a_gorgetesi_pozicio_tulel(self, qml_app, qt_app, tmp_path):
        window, controller = qml_app[0], qml_app[1]
        # A fixture két képével a feed bele sem fér a görgethető tartományba
        # (a ListView a `contentY`-t azonnal 0-ra szorítja vissza) — az
        # állítás foga nélküle nem volna. Ezért töltjük fel a könyvtárat.
        _tolts_fel(controller, tmp_path, qt_app)
        feed = _elem(window, "photoGrid")
        assert _var(
            qt_app, lambda: feed.property("contentHeight") - feed.height() > 40
        ), "a feed nem görgethető — az állítás vakon menne át"

        feed.setProperty("contentY", 40.0)
        assert _var(qt_app, lambda: feed.property("contentY") > 0)
        elotte = feed.property("contentY")

        _kollazs_lapot_nyit(window, qt_app)
        sav = _fulsav(window)
        assert _var(qt_app, lambda: sav.property("activeTabId") != "library")
        _konyvtar_fulre(window, qt_app)
        assert _var(qt_app, lambda: sav.property("activeTabId") == "library")
        assert _elem(window, "photoGrid") is feed
        assert feed.property("contentY") == pytest.approx(elotte, abs=0.5), (
            "a görgetési hely elveszett a fülváltásnál"
        )

    def test_a_kollazs_fulre_visszakattintva_a_panel_jon_elo(self, qml_app, qt_app):
        """A fülsáv MINDKÉT iránya működik — nem csak a kollázs felé."""
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        sav = _fulsav(window)
        _konyvtar_fulre(window, qt_app)
        assert _var(qt_app, lambda: sav.property("activeTabId") == "library")
        panel = _elem(window, "collagePanel")
        assert _var(qt_app, lambda: panel.isVisible() is False)
        _kollazs_fulre(window, qt_app)
        assert _var(qt_app, panel.isVisible), (
            "a projekt-fülre visszakattintva nem jött elő a Kollázs-panel"
        )

    def test_a_kijeloles_tulel(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app, sorok=(1,))
        sav = _fulsav(window)
        assert _var(qt_app, lambda: sav.property("activeTabId") != "library")
        _konyvtar_fulre(window, qt_app)
        assert _var(qt_app, lambda: sav.property("activeTabId") == "library")
        assert list(window.property("selectedIndexes")) == [1]


# --------------------------------------------------------------------------
# 5. Vissza a kollazshoz gomb (spec 13., a #949 hagyta hatra)
# --------------------------------------------------------------------------
class TestVisszaAKollazshoz:
    def _klipek_lapra(self, window, qt_app):
        fulek = _elem(window, "collageTabBar")
        _kattints(window, _elem(window, "collageClipsTabButton"), qt_app)
        assert _var(qt_app, lambda: fulek.property("currentIndex") == 1)

    def test_a_tovabbiak_gomb_a_KONYVTAR_fulre_valt(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        sav = _elem(window, "documentTabStrip")
        assert _var(qt_app, lambda: sav.property("activeTabId") != "library")
        self._klipek_lapra(window, qt_app)
        _kattints(window, _elem(window, "collageGetMoreClips"), qt_app)
        assert _var(qt_app, lambda: sav.property("activeTabId") == "library"), (
            "a Tovabbiak... gomb nem valtott at a Konyvtar fulre"
        )

    def test_es_a_kollazs_lapja_NYITVA_marad(self, qml_app, qt_app):
        window, controller = qml_app[0], qml_app[1]
        _kollazs_lapot_nyit(window, qt_app)
        self._klipek_lapra(window, qt_app)
        _kattints(window, _elem(window, "collageGetMoreClips"), qt_app)
        assert controller.property("collageOpen") is True

    def test_megjelenik_a_vissza_a_kollazshoz_gomb(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        gomb = _keres(window, "backToCollageButton")
        assert gomb is None or gomb.isVisible() is False, (
            "a Vissza a kollazshoz gomb a Tovabbiak... ELOTT is latszik"
        )
        self._klipek_lapra(window, qt_app)
        _kattints(window, _elem(window, "collageGetMoreClips"), qt_app)
        gomb = _elem(window, "backToCollageButton")
        assert _var(qt_app, gomb.isVisible), (
            "a Konyvtar fulon nincs Vissza a kollazshoz gomb"
        )

    def test_a_gombra_kattintva_visszaterunk_a_kollazs_lapra(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        sav = _elem(window, "documentTabStrip")
        self._klipek_lapra(window, qt_app)
        _kattints(window, _elem(window, "collageGetMoreClips"), qt_app)
        gomb = _elem(window, "backToCollageButton")
        assert _var(qt_app, gomb.isVisible)
        _kattints(window, gomb, qt_app)
        assert _var(qt_app, lambda: sav.property("activeTabId") != "library"), (
            "a Vissza a kollazshoz gomb nem vitt vissza a lapra"
        )


# --------------------------------------------------------------------------
# 6. Bezárás — a lap eltűnik, a mai felület visszaáll
# --------------------------------------------------------------------------
class TestBezaras:
    def test_a_bezaras_gomb_visszaadja_a_konyvtarat(self, qml_app, qt_app):
        window, controller = qml_app[0], qml_app[1]
        _kollazs_lapot_nyit(window, qt_app)
        assert _var(qt_app, lambda: controller.property("collageOpen") is True)
        _kattints(window, _elem(window, "collageCloseButton"), qt_app)
        assert _var(qt_app, lambda: controller.property("collageOpen") is False)
        oszto = _elem(window, "mainSplit")
        assert _var(qt_app, oszto.isVisible), "a könyvtár nem jött vissza"

    def test_az_Esc_is_bezarja_a_lapot(self, qml_app, qt_app):
        """Spec 3.3 (`escapekey 1`) — a VALÓDI ablakban, valódi billentyűvel.

        Ez az az osztály, amit property-olvasással sosem lehet megfogni: a
        `Keys` csatolt kezelő `focus: true` nélkül soha nem tüzel, a
        `Shortcut` pedig aktív ablakot kíván. A #945 ezt a hibát a panelben
        egyszer már megtalálta — itt a gazda oldalán őrizzük."""
        window, controller = qml_app[0], qml_app[1]
        _kollazs_lapot_nyit(window, qt_app)
        assert _var(qt_app, lambda: controller.property("collageOpen") is True)
        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert _var(qt_app, lambda: controller.property("collageOpen") is False), (
            "az Esc nem zárta be a Kollázs lapot"
        )

    def test_bezaras_utan_a_fulsav_ismet_nulla_magas(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        sav = _elem(window, "documentTabStrip")
        assert _var(qt_app, lambda: sav.height() > 0)
        _kattints(window, _elem(window, "collageCloseButton"), qt_app)
        assert _var(qt_app, lambda: sav.height() == 0), (
            "bezárás után a fülsáv helyet foglal — a mai elrendezés nem állt "
            "vissza"
        )


# --------------------------------------------------------------------------
# 7. ⭐ A MÉRCE: a mentett kép az, amit a vásznon látott
# --------------------------------------------------------------------------
def _fesd_at(utvonal, szin) -> None:
    """A teszt-JPEG-et egyszínűre írjuk — MÉRET-tartóan.

    A `make_jpeg` minden képet pirosra fest, tehát a mentett kollázson nem
    lehetne megmondani, MELYIK kép került egy adott helyre. A méret marad,
    így az indexbeli szélesség/magasság érvényes."""
    with Image.open(utvonal) as kep:
        meret = kep.size
    Image.new("RGB", meret, szin).save(utvonal, "JPEG", quality=95)


def _folt(kep, x: int, y: int, sugar: int = 3) -> tuple[float, float, float]:
    """Egy kis folt ÁTLAGSZÍNE — a JPEG-tömörítés egyetlen képpontot elvisz."""
    pixelek = [
        kep.getpixel((cx, cy))
        for cx in range(max(0, x - sugar), min(kep.width, x + sugar + 1))
        for cy in range(max(0, y - sugar), min(kep.height, y + sugar + 1))
    ]
    return tuple(sum(csatorna) / len(pixelek) for csatorna in zip(*pixelek, strict=True))


class TestAMentettKepAzAmitLatott:
    """A #920 tényleges elfogadási feltétele, egyetlen láncban.

    Menü → lap → elrendezés-váltás → keretváltás → húzás → forgatás →
    mentés → a kimenet ellenőrzése. Minden lépés a felhasználó útján megy:
    valódi jelzés, valódi kattintás, valódi egérhúzás.
    """

    @pytest.fixture
    def lanc(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        from picasapy.app import collage_prefs as prefs

        # A kimenet SOHA nem mehet a felhasználó valódi Képek mappájába.
        controller._get_settings().setValue(
            prefs.OUTPUT_DIR_KEY, str(tmp_path / "kollazsok")
        )
        # #949 szándéka szerint: a teszt kisebb vásznon dolgozik (az éles
        # 5120 képpont másodperceket és tízmegabájtos tömböket jelentene).
        controller._collage_output_width = lambda: 400

        _fesd_at(tmp_path / "kepek" / "a.jpg", (0, 220, 0))
        _fesd_at(tmp_path / "kepek" / "b.jpg", (0, 0, 220))

        kesz: list[str] = []
        controller.collageDone.connect(kesz.append)

        _kollazs_lapot_nyit(window, qt_app, sorok=(0, 1))
        assert _var(qt_app, lambda: controller.property("collageClipCount") == 2)
        assert _var(qt_app, lambda: _keres(window, "collageNode0") is not None)
        return window, controller, kesz

    def test_a_teljes_lanc(self, lanc, qt_app):
        window, controller, kesz = lanc

        # --- 1. elrendezés-váltás (a téma-választó VALÓDI megnyitásával) ---
        _kattints(window, _elem(window, "collageThemeClosed"), qt_app)
        assert _var(qt_app, lambda: _keres(window, "collageThemeOption3") is not None)
        _kattints(window, _elem(window, "collageThemeOption3"), qt_app)
        assert _var(
            qt_app, lambda: controller.property("collageTheme") == "regulargrid"
        ), "az elrendezés-váltás nem ért el a vezérlőig"

        # vissza a Képkupacra: csak ott van gyűrű és szabad elhelyezés
        _kattints(window, _elem(window, "collageThemeClosed"), qt_app)
        assert _var(qt_app, lambda: _keres(window, "collageThemeOption0") is not None)
        _kattints(window, _elem(window, "collageThemeOption0"), qt_app)
        assert _var(
            qt_app, lambda: controller.property("collageTheme") == "picturepile"
        )

        # --- 2. keretváltás -------------------------------------------------
        _kattints(window, _elem(window, "collageBorder1"), qt_app)
        assert _var(
            qt_app, lambda: controller.property("collageBorder") == "whiteborder"
        ), "a keretváltás nem ért el a vezérlőig"

        # --- 3. megfogás és elhúzás ----------------------------------------
        lap = _lap(window)
        csomopont = _elem(window, "collageNode0")
        assert _var(qt_app, lambda: csomopont.width() > 0)
        honnan_x, honnan_y = _kozeppont(csomopont)
        lap_x, lap_y, lap_w, lap_h = _ablakban(lap)
        # cél: a lap bal felső negyedének közepe — biztosan a lapon belül
        cel = QPoint(round(lap_x + lap_w * 0.28), round(lap_y + lap_h * 0.30))
        honnan = QPoint(round(honnan_x), round(honnan_y))
        _eger_le(window, honnan)
        _eger_mozog(window, QPoint((honnan.x() + cel.x()) // 2, honnan.y()))
        _eger_mozog(window, cel)
        _eger_fel(window, cel)
        qt_app.processEvents()
        QTest.qWait(30)

        u_huzas, v_huzas = _lap_arany(csomopont, lap)
        assert 0.05 < u_huzas < 0.95 and 0.05 < v_huzas < 0.95, (
            f"a húzás után a kép a lapon kívülre került ({u_huzas}, {v_huzas})"
        )

        # --- 4. forgatás a gyűrű peremével (spec 7.4) ----------------------
        gyuru = _elem(window, "collageRing0")
        assert _var(qt_app, gyuru.isVisible), "a húzás után nincs kijelölés-gyűrű"
        gyuru_x, gyuru_y = _kozeppont(gyuru)
        sugar = 57  # a perem közepe (48 belső, 66 külső)
        kezdo = QPoint(round(gyuru_x), round(gyuru_y + sugar))
        vege = QPoint(round(gyuru_x + sugar), round(gyuru_y))
        _eger_le(window, kezdo)
        _eger_mozog(window, vege)
        _eger_fel(window, vege)
        qt_app.processEvents()
        QTest.qWait(30)

        modell = controller.collageNodes.nodes[0]
        assert abs(modell.theta) > 0.2, (
            f"a gyűrű pereme nem forgatott (theta={modell.theta})"
        )

        # a vásznon MÉRT hely (a forgatás után is a doboz közepe)
        u_lattam, v_lattam = _lap_arany(_elem(window, "collageNode0"), lap)

        # --- 5. mentés a VALÓDI gombbal ------------------------------------
        _kattints(window, _elem(window, "collageShareButton"), qt_app)
        assert _var(qt_app, lambda: bool(kesz), 30.0), (
            "a mentés nem fejeződött be (collageDone nem érkezett)"
        )
        from pathlib import Path

        mentett = Path(kesz[0])
        assert mentett.exists(), f"a mentett fájl nincs meg: {mentett}"

        # --- 6/a. KÉPPONT-LÁB ----------------------------------------------
        with Image.open(mentett) as kep:
            kep = kep.convert("RGB")
            x = min(kep.width - 1, max(0, round(u_lattam * kep.width)))
            y = min(kep.height - 1, max(0, round(v_lattam * kep.height)))
            piros, zold, kek = _folt(kep, x, y)
        assert zold > 120 and zold > piros + 40 and zold > kek + 40, (
            "a mentett képen NEM az a kép van ott, ahova a felhasználó "
            f"elhúzta: a ({u_lattam:.3f}, {v_lattam:.3f}) arányú helyen a "
            f"szín (r={piros:.0f}, g={zold:.0f}, b={kek:.0f}) — a zöld képet "
            "vártuk"
        )

        # --- 6/b. GEOMETRIA-LÁB (a JPEG mellé írt `.cxf`) ------------------
        from picasapy.collage.cxf import read_cxf

        projekt = read_cxf(mentett.with_suffix(".cxf"))
        assert projekt.theme == "picturepile"
        cxf_csomopont = projekt.nodes[0]
        assert cxf_csomopont.theme == "whiteborder", (
            "a keretváltás nem jutott el a mentett projektbe"
        )
        # ⚠️ A `.cxf` `x`/`y` a doboz BAL FELSŐ SARKA a lap arányában
        # (`draft.cxf_node_of`), nem a középpont — a vásznon a KÖZÉPPONTOT
        # mértük, tehát a fél szélességet/magasságot hozzá kell adni.
        cxf_kozep_u = cxf_csomopont.x + cxf_csomopont.w / 2.0
        cxf_kozep_v = cxf_csomopont.y + cxf_csomopont.h / 2.0
        assert cxf_kozep_u == pytest.approx(u_lattam, abs=0.02), (
            "a `.cxf` szerint máshol van a kép, mint amit a vásznon mértünk"
        )
        assert cxf_kozep_v == pytest.approx(v_lattam, abs=0.02)
        assert math.isclose(
            math.cos(cxf_csomopont.theta), math.cos(modell.theta), abs_tol=0.02
        ) and math.isclose(
            math.sin(cxf_csomopont.theta), math.sin(modell.theta), abs_tol=0.02
        ), "a mentett szög eltér attól, amit a vásznon beállítottunk"

"""A dokumentum-fülsáv KIRAJZOLVA — #944 (a Kollázs-panel 3/8. szelete).

## Miért kirajzolt teszt

A `PROTOKOLL.md` a #651 tanulsága óta kimondja: felületi viselkedéshez
valódi `QQuickView` kell, több ablakméretben, az **ablak** koordináta-
rendszerében mért állításokkal. Property-olvasással ez a jegy nem
ellenőrizhető, mert a három szerződése mind geometriai vagy interakciós:

1. **regresszió-mentesség** — nyitott projekt-lap nélkül a sáv NEM tolhatja
   lejjebb a tartalomterületet (a mai felület változatlan marad);
2. **állapotmegőrzés** — fülváltás után a rács kijelölése és görgetési
   helye megmarad, mert a feed `visible: false`-ra vált, nem semmisül meg;
3. **egy bezárási út** — az ✕ és az `Esc` UGYANAZT csinálja, mentetlen
   módosítással és anélkül is.

## Három csapda, amit ez a fájl kikerül

* a `Repeater` delegáltjait a `findChild` **nem** találja meg — a VIZUÁLIS
  fát kell bejárni (`_walk`, a #651-es mintából);
* a `visible` öröklődik a szülőtől, ezért nem láthatóságot állítunk, hanem
  **viselkedést**: a sáv magasságát és a tartalomterület helyét;
* fejnélküli (offscreen) környezetben az elrendezés NEM fut le egyetlen
  `processEvents()` után (#918 — mindkét CI-lábon elbukott emiatt), ezért
  minden mérés előtt `_wait_for` pörgeti az eseményeket határidővel.

A számokat nem beégetett képpont-küszöbhöz kötjük: a sávmagasságot magától
a komponenstől (`savMagassag`) kérdezzük, a regressziót pedig a sáv NÉLKÜLI
elrendezéssel VETJÜK ÖSSZE — így a mérés platformfüggetlen marad
(a betűméret Linuxon és Windowson eltér).
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPoint, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

#: A Qt a Python-oldali referenciák elfogyásakor lebontaná az ablakot és a
#: gyökérelemet — a #651-es minta szerint életben tartjuk őket.
_KEEPALIVE: list[object] = []

#: A jegy szerinti három ablakméret: az eredeti tervezési vászon, egy
#: tipikus asztali és egy teljes HD ablak.
_ABLAKMERETEK = [(800, 534), (1280, 800), (1920, 1080)]


# --------------------------------------------------------------------------
# Segédek
# --------------------------------------------------------------------------
def _view(qt_app, qml: str, width: int, height: int):
    """A QML valódi, aktivált ablakban — a layoutok tényleg lefutnak.

    Az aktiválás nem kozmetika: az `Esc` egy `Shortcut`, azt csak aktív
    ablak kapja meg. Offscreen platformon ez működik, de nem azonnal.
    """
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(qml.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    _KEEPALIVE.extend((view, root, component))
    view.show()
    view.requestActivate()
    assert _wait_for(qt_app, view.isActive), "#2408: a nezet nem lett aktiv idoben"
    return view, root


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `Repeater` elemei csak itt látszanak."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _child(root: QQuickItem, name: str) -> QQuickItem:
    for item in _walk(root):
        if item.objectName() == name:
            return item
    found = root.findChild(QObject, name)
    assert found is not None, f"{name} nem található a kirajzolt fában"
    return found


def _maybe_child(root: QQuickItem, name: str):
    for item in _walk(root):
        if item.objectName() == name:
            return item
    return root.findChild(QObject, name)


def _wait_for(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő).

    #918: fejnélküli környezetben az elrendezés késik — egyetlen
    `processEvents()` után a méretek még a kezdeti állapotot mutatják.
    """
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.005)
    return bool(feltetel())


def _log(root: QQuickItem, name: str) -> list:
    """A harness JS-tömb naplója Python-listaként.

    A QML `var` property PySide-ban `QJSValue`-ként érkezik — a nyers
    összehasonlítás mindig hamis lenne, akkor is, ha a tartalom stimmel.
    """
    value = root.property(name)
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value or [])


def _top_in_window(item: QQuickItem) -> float:
    """Az elem tetejének Y-koordinátája az ABLAK rendszerében."""
    return item.mapToScene(item.boundingRect().topLeft()).y()


def _center_in_window(item: QQuickItem) -> QPoint:
    point = item.mapToScene(item.boundingRect().center())
    return QPoint(round(point.x()), round(point.y()))


def _click(qt_app, view: QQuickView, item: QQuickItem) -> None:
    """Valódi egérkattintás az elem közepére, az ablak koordinátáiban."""
    assert _wait_for(qt_app, lambda: item.width() > 0 and item.height() > 0), (
        f"{item.objectName()!r} nulla méretű maradt — nincs mire kattintani"
    )
    QTest.mouseClick(
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _center_in_window(item),
    )
    qt_app.processEvents()


def _press_escape(qt_app, view: QQuickView) -> None:
    QTest.keyClick(view, Qt.Key.Key_Escape)
    qt_app.processEvents()


# --------------------------------------------------------------------------
# A vizsgált elrendezés: a Main.qml alakjának hű, de minimális mása
# --------------------------------------------------------------------------
#
# Szándékosan NEM a teljes `Main.qml` (az controllereket és indexet kérne):
# a #944 szempontjából a beágyazás ALAKJA a lényeg — eszköztár, alatta a
# fülsáv, alatta a tartalomterület a könyvtár-feeddel.
_HARNESS_QML = """
import QtQuick
import QtQuick.Layouts
import PicasaPy 1.0

Item {
    id: harness
    objectName: "harnessRoot"

    property var closeLog: []
    property var activateLog: []

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            objectName: "fakeToolbar"
            Layout.fillWidth: true
            Layout.preferredHeight: 37
            color: "#dddddd"
        }

        __STRIP__

        Item {
            objectName: "contentArea"
            Layout.fillWidth: true
            Layout.fillHeight: true

            GridView {
                id: feed
                objectName: "libraryFeed"
                anchors.fill: parent
                cellWidth: 80
                cellHeight: 80
                model: 400
                visible: __FEED_VISIBLE__
                delegate: Rectangle {
                    width: 76
                    height: 76
                    color: "#cccccc"
                    required property int index
                }
            }

            Rectangle {
                objectName: "projectPage"
                anchors.fill: parent
                color: "#ffffff"
                visible: !feed.visible
            }
        }
    }

    __CONNECTIONS__
}
"""

_STRIP_QML = """
        DocumentTabStrip {
            id: strip
            objectName: "documentTabStrip"
            Layout.fillWidth: true
            Layout.preferredHeight: strip.implicitHeight
            projectTabs: __TABS__
        }
"""

_CONNECTIONS_QML = """
    Connections {
        target: strip
        function onCloseAccepted(tabId, saveDraft) {
            harness.closeLog = harness.closeLog.concat(
                [tabId + ":" + (saveDraft ? "save" : "discard")])
        }
        function onTabActivated(tabId) {
            harness.activateLog = harness.activateLog.concat([tabId])
        }
    }
"""

#: Egy nyitott, MENTETT kollázs-lap.
_TISZTA_LAP = '[{ "id": "collage", "title": "Collage", "modified": false }]'
#: Egy nyitott, MENTETLEN módosítást tartalmazó kollázs-lap.
_PISZKOS_LAP = '[{ "id": "collage", "title": "Collage", "modified": true }]'


def _harness_qml(tabs: str | None = _TISZTA_LAP) -> str:
    """A vizsgált elrendezés. `tabs=None` esetén a sáv KI SEM KERÜL —
    ez a regresszió-összevetés alapállapota (a mai felület)."""
    if tabs is None:
        return (
            _HARNESS_QML.replace("__STRIP__", "")
            .replace("__CONNECTIONS__", "")
            .replace("__FEED_VISIBLE__", "true")
        )
    return (
        _HARNESS_QML.replace("__STRIP__", _STRIP_QML.replace("__TABS__", tabs))
        .replace("__CONNECTIONS__", _CONNECTIONS_QML)
        .replace("__FEED_VISIBLE__", "strip.activeTabId === strip.libraryTabId")
    )


#: A HIBÁS beágyazási alak: a feedet `Loader.active` kapcsolja ki-be, tehát
#: fülváltáskor ténylegesen MEGSEMMISÜL és újraépül. Ez a fájl azért írja le,
#: hogy a fenti állítás bizonyítottan meg tudjon bukni — máskülönben nem
#: tudnánk, hogy a zöld tesztnek van-e egyáltalán foga (#651 mintája).
_LOADER_HARNESS_QML = """
import QtQuick
import QtQuick.Layouts
import PicasaPy 1.0

Item {
    id: harness
    objectName: "harnessRoot"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        DocumentTabStrip {
            id: strip
            objectName: "documentTabStrip"
            Layout.fillWidth: true
            Layout.preferredHeight: strip.implicitHeight
            projectTabs: __TABS__
        }

        Item {
            objectName: "contentArea"
            Layout.fillWidth: true
            Layout.fillHeight: true

            Loader {
                anchors.fill: parent
                active: strip.activeTabId === strip.libraryTabId
                sourceComponent: GridView {
                    objectName: "libraryFeed"
                    cellWidth: 80
                    cellHeight: 80
                    model: 400
                    delegate: Rectangle {
                        width: 76
                        height: 76
                        color: "#cccccc"
                        required property int index
                    }
                }
            }
        }
    }
}
"""


def _laid_out(qt_app, root: QQuickItem) -> QQuickItem:
    """Megvárja, amíg a tartalomterület valódi méretet kap (#918)."""
    content = _child(root, "contentArea")
    assert _wait_for(qt_app, lambda: content.height() > 0), (
        "a tartalomterület nulla magas maradt — az elrendezés nem futott le"
    )
    return content


# --------------------------------------------------------------------------
# 1. Regresszió-mentesség
# --------------------------------------------------------------------------
class TestTheStripTakesNoSpaceWithoutProjectTabs:
    """„A sáv nyitott projekt-lap nélkül nem látszik, és a mai felület
    pixelre változatlan."""

    @pytest.mark.parametrize("width,height", _ABLAKMERETEK)
    def test_the_content_area_starts_exactly_where_it_used_to(
        self, qt_app, width, height
    ):
        """A mérce nem beégetett szám, hanem a sáv NÉLKÜLI elrendezés."""
        _, root_nelkul = _view(qt_app, _harness_qml(None), width, height)
        alap = _top_in_window(_laid_out(qt_app, root_nelkul))

        _, root_savval = _view(qt_app, _harness_qml("[]"), width, height)
        savval = _top_in_window(_laid_out(qt_app, root_savval))

        assert abs(savval - alap) < 0.5, (
            f"{width}×{height} ablakban a tartalomterület {savval:.1f} px-nél "
            f"kezdődik a fülsávval, {alap:.1f} px-nél nélküle — a sáv üresen "
            "is helyet foglal, ez regresszió a mai felületen (#944)"
        )

    @pytest.mark.parametrize("width,height", _ABLAKMERETEK)
    def test_the_strip_has_no_height_without_project_tabs(
        self, qt_app, width, height
    ):
        _, root = _view(qt_app, _harness_qml("[]"), width, height)
        _laid_out(qt_app, root)

        strip = _child(root, "documentTabStrip")

        assert strip.height() == 0, (
            f"a fülsáv {strip.height():.0f} px magas nyitott projekt-lap "
            "nélkül — a tartalomterületet lejjebb tolja"
        )

    @pytest.mark.parametrize("width,height", _ABLAKMERETEK)
    def test_a_project_tab_pushes_the_content_down_by_the_strip_height(
        self, qt_app, width, height
    ):
        """Nyitott lappal viszont pontosan a sávnyi helyet foglalja el."""
        _, root_ures = _view(qt_app, _harness_qml("[]"), width, height)
        ures = _top_in_window(_laid_out(qt_app, root_ures))

        _, root = _view(qt_app, _harness_qml(_TISZTA_LAP), width, height)
        content = _laid_out(qt_app, root)
        strip = _child(root, "documentTabStrip")
        savmagassag = strip.property("savMagassag")

        assert _wait_for(qt_app, lambda: strip.height() > 0)
        assert strip.height() == savmagassag
        assert abs(_top_in_window(content) - (ures + savmagassag)) < 0.5, (
            f"{width}×{height} ablakban a tartalom nem pontosan {savmagassag} "
            "px-szel csúszott lejjebb a fülsáv megjelenésekor"
        )

    def test_the_declared_strip_height_is_the_measured_29_px(self, qt_app):
        """`design-guide.md`: „felső fül-sáv 29 px" — a mért érték."""
        _, root = _view(qt_app, _harness_qml(_TISZTA_LAP), 1280, 800)
        _laid_out(qt_app, root)

        assert _child(root, "documentTabStrip").property("savMagassag") == 29

    @pytest.mark.parametrize("width,height", _ABLAKMERETEK)
    def test_both_tabs_are_drawn_side_by_side(self, qt_app, width, height):
        """Balra a rögzített „Könyvtár", mellette a projekt-lap."""
        _, root = _view(qt_app, _harness_qml(_TISZTA_LAP), width, height)
        _laid_out(qt_app, root)

        library = _child(root, "documentTabLibrary")
        project = _child(root, "documentTab0")
        assert _wait_for(qt_app, lambda: project.width() > 0)

        assert library.width() > 0 and library.height() > 0
        assert project.width() > 0 and project.height() > 0
        assert _center_in_window(library).x() < _center_in_window(project).x(), (
            "a Könyvtár fül nem a projekt-lap BALJÁN van"
        )

    def test_the_library_tab_cannot_be_closed(self, qt_app):
        """A rögzített fülön nincs ✕ — nincs is mit rákattintani."""
        _, root = _view(qt_app, _harness_qml(_TISZTA_LAP), 1280, 800)
        _laid_out(qt_app, root)

        library = _child(root, "documentTabLibrary")
        bezaro = _maybe_child(library, "documentTabLibraryClose")

        assert bezaro is None or bezaro.width() == 0, (
            "a Könyvtár fülön záró ✕ jelent meg — a könyvtár nem zárható"
        )


# --------------------------------------------------------------------------
# 2. Állapotmegőrzés fülváltáskor
# --------------------------------------------------------------------------
class TestSwitchingTabsKeepsTheLibraryAlive:
    """„Fülváltás után a rács kijelölése és görgetési helye megmarad."""

    def _feed_with_state(self, qt_app, root):
        feed = _child(root, "libraryFeed")
        assert _wait_for(qt_app, lambda: feed.property("contentHeight") > 800)
        feed.setProperty("currentIndex", 37)
        feed.setProperty("contentY", 400.0)
        qt_app.processEvents()
        return feed

    def test_the_grid_keeps_selection_and_scroll_across_a_round_trip(
        self, qt_app
    ):
        view, root = _view(qt_app, _harness_qml(_TISZTA_LAP), 1280, 800)
        _laid_out(qt_app, root)
        feed = self._feed_with_state(qt_app, root)

        _click(qt_app, view, _child(root, "documentTab0"))
        assert _wait_for(
            qt_app, lambda: not _child(root, "libraryFeed").isVisible()
        ), "a projekt-lapra váltva a könyvtár-rács még mindig látszik"

        _click(qt_app, view, _child(root, "documentTabLibrary"))
        assert _wait_for(qt_app, lambda: _child(root, "libraryFeed").isVisible())

        assert feed.property("currentIndex") == 37, (
            "a rács kijelölése elveszett a fülváltás során (#944)"
        )
        assert abs(feed.property("contentY") - 400.0) < 0.5, (
            "a rács görgetési helye elveszett a fülváltás során (#944)"
        )

    def test_a_destroying_host_really_loses_the_state(self, qt_app):
        """Az őrnek van foga: a HIBÁS alak tényleg elveszíti az állapotot.

        Ha ez a teszt zöldre vált (azaz a `Loader`-es változat is megőrizné a
        görgetést), akkor a fenti állítás elvesztette az élét — a mérés nem
        tudná megkülönböztetni a megőrzést az újraépítéstől.
        """
        view, root = _view(
            qt_app,
            _LOADER_HARNESS_QML.replace("__TABS__", _TISZTA_LAP),
            1280,
            800,
        )
        _laid_out(qt_app, root)
        self._feed_with_state(qt_app, root)

        _click(qt_app, view, _child(root, "documentTab0"))
        _click(qt_app, view, _child(root, "documentTabLibrary"))
        assert _wait_for(
            qt_app, lambda: _maybe_child(root, "libraryFeed") is not None
        )
        ujra = _child(root, "libraryFeed")

        assert ujra.property("currentIndex") != 37 or ujra.property("contentY") == 0.0, (
            "a megsemmisítő beágyazás mégis megőrizte az állapotot — a "
            "megőrzést állító teszt elvesztette az élét"
        )

    def test_the_feed_object_survives_the_switch(self, qt_app):
        """Nem újraépül, hanem elrejtőzik: UGYANAZ az objektum kerül elő."""
        view, root = _view(qt_app, _harness_qml(_TISZTA_LAP), 1280, 800)
        _laid_out(qt_app, root)
        elotte = _child(root, "libraryFeed")

        _click(qt_app, view, _child(root, "documentTab0"))
        _click(qt_app, view, _child(root, "documentTabLibrary"))

        assert _child(root, "libraryFeed") is elotte, (
            "a könyvtár-feed újraépült — a fülváltás megsemmisítette"
        )

    def test_the_project_page_takes_over_when_its_tab_is_active(self, qt_app):
        view, root = _view(qt_app, _harness_qml(_TISZTA_LAP), 1280, 800)
        _laid_out(qt_app, root)
        strip = _child(root, "documentTabStrip")

        _click(qt_app, view, _child(root, "documentTab0"))

        assert _wait_for(qt_app, lambda: strip.property("activeTabId") == "collage")
        assert _wait_for(qt_app, lambda: _child(root, "projectPage").isVisible())
        assert _log(root, "activateLog") == ["collage"], (
            "a fülváltás nem adott `tabActivated` jelzést"
        )

    def test_clicking_the_active_tab_again_changes_nothing(self, qt_app):
        """Nem ad fölösleges jelzést — a gazda nem épít újra semmit."""
        view, root = _view(qt_app, _harness_qml(_TISZTA_LAP), 1280, 800)
        _laid_out(qt_app, root)

        _click(qt_app, view, _child(root, "documentTabLibrary"))

        assert _log(root, "activateLog") == [], (
            "a már aktív fülre kattintva is `tabActivated` érkezett"
        )


# --------------------------------------------------------------------------
# 3. Egy bezárási út: ✕ és Esc
# --------------------------------------------------------------------------
def _dialog_button(root: QQuickItem, name: str) -> QQuickItem:
    dialog = root.findChild(QObject, "documentTabCloseConfirm")
    assert dialog is not None, "a megerősítő párbeszéd nincs a fában"
    button = dialog.findChild(QObject, name)
    assert button is not None, f"{name} nincs a párbeszédben"
    return button


def _trigger_close(qt_app, view, root, mod: str) -> None:
    """A két bezárási kapu — a tesztek mindkettőt ugyanúgy hajtják meg."""
    if mod == "x":
        _click(qt_app, view, _child(root, "documentTab0Close"))
    else:
        _press_escape(qt_app, view)


class TestTheCloseButtonAndEscapeShareOnePath:
    """„Az ✕ és az Esc ugyanazt a bezárási utat járja."""

    def _on_project_tab(self, qt_app, tabs: str):
        view, root = _view(qt_app, _harness_qml(tabs), 1280, 800)
        _laid_out(qt_app, root)
        _click(qt_app, view, _child(root, "documentTab0"))
        strip = _child(root, "documentTabStrip")
        assert _wait_for(qt_app, lambda: strip.property("activeTabId") == "collage")
        return view, root

    @pytest.mark.parametrize("mod", ["x", "esc"])
    def test_a_saved_tab_closes_without_a_question(self, qt_app, mod):
        view, root = self._on_project_tab(qt_app, _TISZTA_LAP)

        _trigger_close(qt_app, view, root, mod)

        assert _wait_for(qt_app, lambda: _log(root, "closeLog") != [])
        assert _log(root, "closeLog") == ["collage:discard"], (
            f"a(z) {mod!r} kapu nem zárta be a mentett lapot kérdés nélkül"
        )
        dialog = root.findChild(QObject, "documentTabCloseConfirm")
        assert not dialog.property("visible"), (
            "mentett lapnál is megjelent a mentetlen-módosítás kérdés"
        )

    @pytest.mark.parametrize("mod", ["x", "esc"])
    def test_an_unsaved_tab_asks_before_closing(self, qt_app, mod):
        view, root = self._on_project_tab(qt_app, _PISZKOS_LAP)

        _trigger_close(qt_app, view, root, mod)

        dialog = root.findChild(QObject, "documentTabCloseConfirm")
        assert _wait_for(qt_app, lambda: bool(dialog.property("visible"))), (
            f"a(z) {mod!r} kapu nem kérdezett rá a mentetlen módosításra"
        )
        assert _log(root, "closeLog") == [], (
            "a lap a kérdés megválaszolása ELŐTT bezárult"
        )

    @pytest.mark.parametrize("mod", ["x", "esc"])
    def test_save_draft_closes_the_tab_with_the_draft_flag(self, qt_app, mod):
        view, root = self._on_project_tab(qt_app, _PISZKOS_LAP)
        _trigger_close(qt_app, view, root, mod)

        _click(qt_app, view, _dialog_button(root, "documentTabSaveDraftButton"))

        assert _wait_for(qt_app, lambda: _log(root, "closeLog") != [])
        assert _log(root, "closeLog") == ["collage:save"], (
            "a Piszkozat mentése nem a mentő ágon zárta be a lapot"
        )

    @pytest.mark.parametrize("mod", ["x", "esc"])
    def test_discard_closes_the_tab_without_saving(self, qt_app, mod):
        view, root = self._on_project_tab(qt_app, _PISZKOS_LAP)
        _trigger_close(qt_app, view, root, mod)

        _click(qt_app, view, _dialog_button(root, "documentTabDiscardButton"))

        assert _wait_for(qt_app, lambda: _log(root, "closeLog") != [])
        assert _log(root, "closeLog") == ["collage:discard"]

    @pytest.mark.parametrize("mod", ["x", "esc"])
    def test_cancel_leaves_the_tab_open(self, qt_app, mod):
        view, root = self._on_project_tab(qt_app, _PISZKOS_LAP)
        _trigger_close(qt_app, view, root, mod)

        _click(qt_app, view, _dialog_button(root, "documentTabCancelButton"))

        dialog = root.findChild(QObject, "documentTabCloseConfirm")
        assert _wait_for(qt_app, lambda: not dialog.property("visible"))
        assert _log(root, "closeLog") == [], (
            "a Mégse mégis bezárta a lapot — a lapnak nyitva kell maradnia"
        )
        strip = _child(root, "documentTabStrip")
        assert strip.property("activeTabId") == "collage", (
            "a Mégse után a lap nem maradt aktív"
        )

    def test_escape_does_nothing_while_the_library_tab_is_active(self, qt_app):
        """Az Esc a LAPOT zárja — a könyvtárat soha."""
        view, root = _view(qt_app, _harness_qml(_TISZTA_LAP), 1280, 800)
        _laid_out(qt_app, root)

        _press_escape(qt_app, view)
        qt_app.processEvents()

        assert _log(root, "closeLog") == [], (
            "a könyvtár-fülön megnyomott Esc bezárta a projekt-lapot"
        )

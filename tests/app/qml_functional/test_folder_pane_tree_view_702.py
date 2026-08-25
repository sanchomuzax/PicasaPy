"""A fa-mappanézet BEKÖTVE a bal hasábba — #702, második lépcső.

Az első lépcső a `FolderHierarchyView.qml`-t és a mögötte álló, Qt-mentes
fa-építőt hozta létre (`test_folder_hierarchy_view_702.py`). Ez a fájl azt
méri, hogy a kész komponens tényleg a HASÁBBAN van-e: a Mappák gyűjtemény
lapos listája helyére lép, a hasáb egyetlen görgetője marad a
`paneFlickable` (#730), és a kiválasztás mindkét irányban átjár.

Miért kirajzolt `QQuickView`: a #730/#731/#732 pontosan attól maradt
hónapokig észrevétlen, hogy a hasábot sosem mértük valódi ablakban, valódi
mennyiségű tartalommal — a fa ugyanazt a hibaosztályt hozná vissza, ha csak
property-ket állítanánk.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView

from picasapy.app.folder_hierarchy_controller import FolderHierarchyController

try:
    from PySide6.QtTest import QTest

    _QTTEST_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    QTest = None
    _QTTEST_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTTEST_VAN,
    reason=(
        "a PySide6.QtTest modul hiányzik ezen a gépen. Debian/Ubuntu alatt "
        "így pótolható: sudo apt install python3-pyside6.qttest"
    ),
)

_KEEPALIVE: list[object] = []

#: A mért hasábszélesség és -magasság (#730: „230 px hasáb / 1280×800”).
_HASAB_SZELESSEG = 230
_HASAB_MAGASSAG = 800

#: Ugyanaz a mappakészlet, mint a komponens saját tesztjében — a lapos
#: listából öt egyszintű sor, a fából szintenként kibomló ágak.
_FOLDERS = [
    {"path": "/mnt/photo/Kepek/wallpapers/space", "count": 7},
    {"path": "/mnt/photo/Kepek/wallpapers/LEGO", "count": 5},
    {"path": "/mnt/photo/Kepek/wallpapers", "count": 18},
    {"path": "/mnt/photo/Kepek/AI", "count": 92},
    {"path": "/mnt/photo/Videok", "count": 3},
]


# --------------------------------------------------------------------------
# Várakozás — #1463
#
# Ebben a fájlban korábban három fali órás `QTest.qWait(N)` állt (a fixture
# 80 ms-a, a `_settle` 80 ms-a és a görgetés 300 ms-a). Mindhárom azt
# FELTÉTELEZTE, hogy N ezredmásodperc alatt megtörténik, amire várunk;
# terhelt, négymagos gépen ez valódi hiba nélkül ad pirosat. Helyette
# határidős poll: a VALÓDI feltételt figyeljük, és amint teljesül, azonnal
# továbbengedünk.
# --------------------------------------------------------------------------
def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    """Határidős várakozás: a feltételt figyeli, nem az órát (#1463).

    #918: fejnélküli környezetben az elrendezés késik — egyetlen
    `processEvents()` után a méretek még a kezdeti állapotot mutatják."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        time.sleep(0.01)
    qt_app.processEvents()
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _var_stabil(qt_app, minta, masodperc: float = 5.0) -> bool:
    """Megvárja, amíg a `minta()` KÉT EGYMÁST KÖVETŐ mérésben azonos.

    Ahol nincs egyetlen logikai feltétel, csak „álljon meg az elrendezés”,
    ott ez a helyes várakozás (a repóban már bevált idióma:
    `test_collage_view_and_edit_1001.py::_stabil_kozeppont`)."""
    elozo: list = []

    def _egyezik() -> bool:
        mostani = minta()
        stabil = bool(elozo) and elozo[0] == mostani
        elozo[:] = [mostani]
        return stabil

    return _var(qt_app, _egyezik, masodperc)


def _var_a_hasab_elrendezesere(qt_app, pane) -> None:
    """Megvárja, amíg a hasáb elrendezése MEGÁLL (#1463).

    A minta a hasáb tartalommagassága a két nézet (lapos lista, fa)
    magasságával együtt. Előbb megvárjuk, hogy legyen egyáltalán tartalom
    — enélkül a kezdeti csupa-0 minta két mérésben „stabilnak” látszana, és
    a poll a tördelés ELŐTT engedne tovább.

    Szándékosan nem a kirajzolt fasorokra várunk: lapos módban (`tree=False`)
    egyetlen fasor sincs, és pont ezt állítja a
    `test_a_lapos_lista_az_alapallapot`."""
    flickable = _child(pane, "folderPaneFlickable")
    lista = _child(pane, "folderListView")
    fa = _child(pane, "folderHierarchyView")
    _var(qt_app, lambda: flickable.property("contentHeight") > 0)
    _var_stabil(
        qt_app,
        lambda: (
            round(flickable.property("contentHeight"), 3),
            round(lista.property("height"), 3),
            round(fa.property("height"), 3),
        ),
    )


@pytest.fixture
def render_pane(qt_app):
    """Kirajzolt `QQuickView` a FolderPane-nel + egy élő fa-vezérlővel.

    Controller nélkül töltjük be (a hasáb minden controller-hivatkozása
    null-őrös, #305) — a fa adatforrását közvetlenül a property-n adjuk át,
    pontosan úgy, ahogy a `Main.qml` bekötése fogja."""
    import picasapy.app.application as app_module

    def _render(*, folders=None, tree: bool = False, height: int = _HASAB_MAGASSAG):
        hierarchy = FolderHierarchyController()
        hierarchy.setFolders(_FOLDERS if folders is None else folders)

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", None)
        url = QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
        )
        component = QQmlComponent(engine, url)
        pane = component.createWithInitialProperties(
            {"hierarchyController": hierarchy, "treeViewMode": tree}
        )
        errors = [error.toString() for error in component.errors()]
        assert errors == [], errors
        assert pane is not None

        view = QQuickView(engine, None)
        view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        view.setContent(url, component, pane)
        view.resize(_HASAB_SZELESSEG, height)
        view.show()
        QTest.qWaitForWindowExposed(view)
        # #1463: itt korábban `QTest.qWait(80)` állt — fali óra, ami azt
        # feltételezte, hogy a hasáb 80 ms alatt kitördeli magát. Terhelt,
        # négymagos gépen ez hamis pirosat ad; most magát az elrendezés
        # megállását várjuk ki.
        _var_a_hasab_elrendezesere(qt_app, pane)

        _KEEPALIVE.extend((engine, component, view, pane, hierarchy))
        return view, pane, hierarchy

    return _render


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a delegátumoknak nincs QObject-szülőjük."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _rendered_tree_paths(pane) -> set[str]:
    """A ténylegesen KIRAJZOLT fasorok útvonalai (a `visible` öröklődik,
    ezért az `isVisible()`-t és a valódi magasságot nézzük)."""
    prefix = "hierRow:"
    return {
        item.objectName()[len(prefix):]
        for item in _walk(pane)
        if item.objectName().startswith(prefix)
        and item.isVisible()
        and item.height() > 0
    }


def _settle(qt_app, pane):
    """A `ListView` a delegátumokat a következő polish-körben hozza létre —
    egyetlen `processEvents()` kevés hozzá.

    #1463: a helyén korábban `QTest.qWait(80)` állt. A kilenc hívó KÜLÖNBÖZŐ
    dolgokat állít be (kinyitás, csukás, kijelölés), ezért nincs egyetlen
    közös logikai feltétel — a közös igazság az, hogy a KIRAJZOLT fasorok
    halmaza álljon meg. Ezt figyeljük: két egymást követő mérésben legyen
    azonos a `_rendered_tree_paths(pane)`. Az, hogy MI lett a halmaz, marad
    a hívó teszt állítása — az őr foga tehát nem tompul."""
    _var_stabil(qt_app, lambda: _rendered_tree_paths(pane))


def _send_wheel(qt_app, view, item, *, angle_delta: int = -120):
    """VALÓDI görgő-esemény az elem tetejéhez közel.

    Szándékosan nem a KÖZEPÉRE: a kinyitott fa magasabb lehet az ablaknál
    (pont ez a #730 tétje), a közepe pedig ilyenkor kilóg a képernyőről."""
    center = item.mapToScene(QPointF(item.width() / 2, min(8, item.height() / 2)))
    assert 0 <= center.y() <= view.height(), (
        f"a mért pont ({center.y():.0f}) az ablakon kívülre esik"
    )
    event = QWheelEvent(
        center,
        center,
        QPoint(0, 0),
        QPoint(0, angle_delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QGuiApplication.sendEvent(view, event)
    qt_app.processEvents()


class TestAKetNezetmodKizarjaEgymast:
    """`thumbui/hviewtoggle`: lapos lista VAGY fa — sosem mindkettő."""

    def test_a_lapos_lista_az_alapallapot(self, render_pane):
        """Nézetmód-váltó még nincs (külön jegy), ezért a hasáb ugyanúgy
        indul, ahogy eddig."""
        _view, pane, _hierarchy = render_pane()

        assert pane.property("treeViewMode") is False
        assert _child(pane, "folderListView").property("visible") is True
        assert _rendered_tree_paths(pane) == set(), (
            "lapos módban a fa egyetlen sora sem rajzolódhat ki"
        )

    def test_fa_modban_a_lapos_lista_eltunik(self, render_pane, qt_app):
        """#1454: a várt sorhalmaz megváltozott — SZÁNDÉKOSAN.

        Korábban itt `{""}` állt: fa-módba lépve a hasáb egyetlen,
        ÖSSZECSUKOTT „Sajátgép" sorra zsugorodott. Ez akkor nem tűnt fel,
        mert a fanézet menüből elérhetetlen volt; amint a #1454 elérhetővé
        tette, kiderült, hogy az első kattintás élménye „a bal hasáb
        kiürült" lenne. A nézetmód-váltás azóta kinyitja a kijelölt
        mappáig az ágakat (`FolderPane.onTreeViewModeChanged`), kijelölés
        híján pedig magát a gyökeret — ezért látszik a gyökér EGYETLEN
        gyermeke (`/`) is.
        """
        _view, pane, _hierarchy = render_pane(tree=True)

        assert _child(pane, "folderListView").property("visible") is False
        assert _rendered_tree_paths(pane) == {"", "/"}, (
            "fa-módban a nézet-gyökér NYITVA látszik, nem összecsukva"
        )

    def test_a_csukott_gyujtemeny_a_fat_is_elrejti(self, render_pane, qt_app):
        _view, pane, _hierarchy = render_pane(tree=True)

        pane.setProperty("foldersCollapsed", True)
        _settle(qt_app, pane)

        assert _rendered_tree_paths(pane) == set(), (
            "a csukott Mappák gyűjtemény tartalma nem látszhat"
        )


class TestAFaAdataAVezerlobolJon:
    """A hasáb csak megjeleníti — a sorokat a `FolderHierarchyController`
    adja, már kilapítva."""

    def test_expand_all_utan_minden_mappa_kirajzolodik(self, render_pane, qt_app):
        _view, pane, hierarchy = render_pane(tree=True)

        hierarchy.expandAll()
        _settle(qt_app, pane)

        paths = _rendered_tree_paths(pane)
        for folder in _FOLDERS:
            assert folder["path"] in paths, (
                "az Expand All után hiányzik a fából: " + folder["path"]
            )

    def test_a_fa_magassaga_a_sorok_szama(self, render_pane, qt_app):
        """#730: a hasáb egyetlen görgetője a `paneFlickable`, ezért a fa a
        TELJES tartalmát kirakja — pont úgy, mint a lapos lista."""
        _view, pane, hierarchy = render_pane(tree=True)
        hierarchy.expandAll()
        _settle(qt_app, pane)

        tree_view = _child(pane, "folderHierarchyView")
        sorok = len(hierarchy.rows)
        assert sorok > 1
        assert tree_view.property("height") == sorok * pane.property("rowHeight")


class TestAKijelolesMindketIranybanAtjar:
    def test_a_faban_valasztott_mappa_eljut_a_hasab_jelzeseig(
        self, render_pane, qt_app
    ):
        _view, pane, hierarchy = render_pane(tree=True)
        hierarchy.expandAll()
        _settle(qt_app, pane)
        kapott: list[str] = []
        pane.folderChosen.connect(kapott.append)

        QMetaObject.invokeMethod(
            _child(pane, "folderHierarchyView"),
            "choose",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "/mnt/photo/Kepek/AI"),
        )
        qt_app.processEvents()

        assert kapott == ["/mnt/photo/Kepek/AI"]

    def test_a_kivulrol_erkezo_kijeloles_a_fara_is_atmegy(
        self, render_pane, qt_app
    ):
        """A kijelölés máshonnan is jöhet (kereső-javaslat, rács) — a fának
        követnie kell, és az őseit ki is kell nyitnia."""
        _view, pane, hierarchy = render_pane(tree=True)

        pane.setProperty("selectedPath", "/mnt/photo/Kepek/AI")
        _settle(qt_app, pane)

        tree_view = _child(pane, "folderHierarchyView")
        assert tree_view.property("selectedPath") == "/mnt/photo/Kepek/AI"
        assert "/mnt/photo/Kepek/AI" in _rendered_tree_paths(pane), (
            "a kijelölt mappa sorát a fának ki kell nyitnia (revealPath)"
        )


class TestAJobbklikkASorSajatMenujetAdja:
    """#732 ugyanaz a hibaosztálya: a hasáb gyökerén ülő `TapHandler` a
    rendezés-menüt nyitja meg mindenre, ami maga nem fogadja el a jobb
    gombot. A fa sorainak SAJÁT menüjük van (`HierFolder`, öt tétel)."""

    def test_a_fasor_a_hierfolder_menut_nyitja(self, render_pane, qt_app):
        view, pane, hierarchy = render_pane(tree=True)
        hierarchy.expandAll()
        _settle(qt_app, pane)

        sorok = {
            item.objectName()[len("hierRow:"):]: item
            for item in _walk(pane)
            if item.objectName().startswith("hierRow:")
        }
        sor = sorok["/mnt/photo/Videok"]
        kozep = sor.mapToScene(QPointF(sor.width() / 2, sor.height() / 2))
        assert 0 <= kozep.y() <= view.height()

        QTest.mouseClick(
            view,
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier,
            kozep.toPoint(),
        )
        # #1463: itt korábban `_settle(qt_app)` állt, ami fali órás
        # `QTest.qWait(80)`-at jelentett. A kirajzolt fasorokra várni itt
        # SEMMIT nem érne (a jobbklikk nem változtatja őket) — a valódi
        # feltétel az, hogy megjelenjen VALAMELYIK menü. Hogy a HELYES
        # nyílt-e meg, azt az alatta lévő két állítás mondja meg.
        hier_menu = _child(pane, "hierFolderContextMenu")
        lista_menu = _child(pane, "folderListContextMenu")
        _var(
            qt_app,
            lambda: hier_menu.property("visible")
            or lista_menu.property("visible"),
        )

        assert hier_menu.property("visible") is True, (
            "a fasor jobbklikkje nem a HierFolder menüt adta (#732-osztály)"
        )
        assert lista_menu.property("visible") is False, (
            "a hasáb rendezés-menüje nyílt meg a sor saját menüje helyett"
        )
        assert hier_menu.property("folderPath") == "/mnt/photo/Videok"


class TestAHasabEgyetlenGorgetojeMarad:
    """#730: a `paneFlickable` görget, nem a beágyazott lista."""

    @pytest.fixture
    def sok_mappa(self):
        return [
            {"path": f"/mnt/photo/m{index:03d}", "count": 1} for index in range(60)
        ]

    def test_a_fa_folott_a_gorgo_a_hasabot_gorgeti(
        self, render_pane, qt_app, sok_mappa
    ):
        view, pane, hierarchy = render_pane(folders=sok_mappa, tree=True)
        hierarchy.expandAll()
        _settle(qt_app, pane)

        flickable = _child(pane, "folderPaneFlickable")
        assert flickable.property("contentHeight") > view.height(), (
            "a próba csak akkor mér, ha a hasáb tényleg túlcsordul"
        )
        assert flickable.property("contentY") == 0

        _send_wheel(qt_app, view, _child(pane, "folderHierarchyView"))
        # #1463: itt korábban `QTest.qWait(300)` állt — a `Flickable`
        # lassulásának becsült ideje. A valódi feltétel maga az állítás
        # előfeltétele: elmozdult-e a tartalom.
        _var(qt_app, lambda: flickable.property("contentY") > 0)

        assert flickable.property("contentY") > 0, (
            "a fa elnyelte a görgő-eseményt — a hasáb nem mozdult (#730)"
        )

    def test_a_fa_nem_gorget_sajat_magaban(self, render_pane, qt_app, sok_mappa):
        """Ellenpróba: a beágyazott lista maga NEM görgethet, különben két
        görgető rétegünk lenne egymáson."""
        _view, pane, hierarchy = render_pane(folders=sok_mappa, tree=True)
        hierarchy.expandAll()
        _settle(qt_app, pane)

        lista = _child(pane, "folderHierarchyList")
        assert lista.property("interactive") is False

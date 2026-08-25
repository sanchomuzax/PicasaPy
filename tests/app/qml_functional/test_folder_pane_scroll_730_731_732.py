"""A bal hasáb (FolderPane) három MÉRT hibája: görgetés, görgő, jobbklikk.

- **#730** — a hasábot semmi nem görgeti: a `ColumnLayout` az ablakmagasságba
  préselődik, ezért 30 személynél a mappa-`ListView` magassága 0 lesz, az
  „Egyéb” fejléc pedig kicsúszik az ablakból.
- **#731** — a görgő-kezelő a hasáb GYÖKERÉN ült, ezért az egér görgője
  bárhol a hasáb fölött MÁSIK mappát nyitott meg görgetés helyett.
- **#732** — négy sor `MouseArea`-ja csak bal gombot fogadott, ezért a
  jobbklikk a hasáb rendezés-menüjét adta a sor saját menüje helyett.

**Miért ez a fájl így néz ki.** Mindhárom hiba hónapokig élt zöld CI mellett,
mert a meglévő FolderPane-tesztek 300×600-as hasábot töltenek 1–3 elemmel
(túlcsordulás sosem áll elő), a menü- és görgő-teszt pedig FÜGGVÉNYT hív
kattintás/görgetés helyett. Ez a fájl ezért kizárólag a VALÓDI úton mér:
kirajzolt `QQuickView`, sok elem, igazi `QWheelEvent` és igazi
`QTest.mouseClick` — a felhasználó kezéhez legközelebbi szint.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView

from picasapy.index import open_index, sync_tree

from support.jpeg_factory import make_jpeg

# #664: a QtTest a pip-es PySide6 wheelben benne van, a Debian/Ubuntu-féle
# rendszercsomagban külön modul — hiányában a fájl gyűjtési hibával dőlne el.
try:
    from PySide6.QtTest import QTest

    _QTTEST_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    QTest = None
    _QTTEST_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTTEST_VAN,
    reason=(
        "a PySide6.QtTest modul hiányzik ezen a gépen, ezért a bal hasáb "
        "egér-szimulációs tesztjei kimaradnak. Debian/Ubuntu alatt így "
        "pótolható: sudo apt install python3-pyside6.qttest"
    ),
)

_KEEPALIVE: list[object] = []

#: A mért hasábszélesség és -magasság (#730: „230 px hasáb / 1280×800”).
_HASAB_SZELESSEG = 230
_HASAB_MAGASSAG = 800

#: Ennyi mappa kerül a próbakönyvtárba — a görgő-léptetésnek (#77) kell
#: szomszéd, a mappalistának pedig mérhető magasság.
_MAPPA_DB = 8


# --------------------------------------------------------------------------
# Várakozás — #1463
#
# Ebben a fájlban korábban három fali órás `QTest.qWait(N)` állt (a
# `render_pane` fixture-ben 80 ms, a `_right_click`-ben 50 ms, a
# görgetés-tesztben 300 ms). A fali óra azt FELTÉTELEZI, hogy N
# ezredmásodperc alatt megtörténik, amire várunk. Négymagos gépen, két
# párhuzamos tesztfutás mellett ez nem igaz — a teszt valódi hiba nélkül
# vált pirosra. Helyette határidős poll: a VALÓDI feltételt figyeljük, és
# amint teljesül, azonnal továbbengedünk.
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

    A helyén korábban `QTest.qWait(80)` állt azzal az indokkal, hogy „a
    ColumnLayout az újratördelést a következő polish-körben végzi”. Az
    indok igaz, a 80 ms viszont találgatás.

    A mintánk a hasáb tartalommagassága és a mappalista magassága együtt;
    a poll akkor enged tovább, ha a pár két egymást követő mérésben azonos
    (és a hasábnak már van tartalma — enélkül a kezdeti 0-s állapot
    „stabilnak” látszana).

    Szándékosan NEM várunk arra, hogy `folderListView.height() > 0`: pont
    EZT állítja a `test_folder_list_keeps_a_usable_height` (#730). Ha a
    fixture is erre várna, egy valódi visszaesésnél minden eset a
    határidőt ülné végig, és a bukás a fixture-ből jönne a beszédes
    állítás helyett — vagyis az őr foga tompulna."""
    flickable = _child(pane, "folderPaneFlickable")
    lista = _child(pane, "folderListView")
    # előbb legyen egyáltalán tartalma (különben a kezdeti 0/0 pár két
    # mérésben „stabil”, és a poll a tördelés ELŐTT engedne tovább)
    _var(qt_app, lambda: flickable.property("contentHeight") > 0)
    _var_stabil(
        qt_app,
        lambda: (
            round(flickable.property("contentHeight"), 3),
            round(lista.property("height"), 3),
        ),
    )


@pytest.fixture
def library(tmp_path):
    """Nyolc mappa, mindegyikben egy apró JPEG — valódi index-tartalom."""
    root = tmp_path / "kepek"
    for index in range(_MAPPA_DB):
        folder = root / f"mappa{index}"
        folder.mkdir(parents=True)
        make_jpeg(folder / "a.jpg", size=(20, 20))
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


@pytest.fixture
def render_pane(qt_app, conn):
    """Kirajzolt `QQuickView` a FolderPane-nel — a hívó adja meg, hány
    személy/album/exportált mappa legyen benne.

    A `pane` fixture-ök (300×600, geometria nélkül) szándékosan NEM
    használhatók itt: a #730 pont attól maradt észrevétlen, hogy sosem
    mértünk valódi ablakban, valódi mennyiségű tartalommal."""
    import picasapy.app.application as app_module
    from picasapy.app.models import FolderListModel

    def _render(
        *,
        people: int = 0,
        albums: int = 1,
        exported: bool = False,
        collections: bool = False,
        unnamed: int = 0,
        ignored: int = 0,
        width: int = _HASAB_SZELESSEG,
        height: int = _HASAB_MAGASSAG,
    ):
        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        # controller nélkül: a hasáb minden controller-hivatkozása null-őrös
        # (#305), a modelleket közvetlenül a property-ken át adjuk
        engine.rootContext().setContextProperty("controller", None)
        url = QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
        )
        component = QQmlComponent(engine, url)
        folders_model = FolderListModel()
        folders_model.load(conn)
        pane = component.createWithInitialProperties(
            {"foldersModel": folders_model}
        )
        errors = [error.toString() for error in component.errors()]
        assert errors == [], errors
        assert pane is not None
        folders_model.setParent(pane)

        view = QQuickView(engine, None)
        view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        view.setContent(url, component, pane)
        view.resize(width, height)
        view.show()
        QTest.qWaitForWindowExposed(view)

        # minden gyűjtemény nyitva: a hiba pont a teli hasábon jelentkezik
        pane.setProperty("peopleCollapsed", False)
        pane.setProperty("projectsCollapsed", False)
        pane.setProperty("otherCollapsed", False)
        pane.setProperty(
            "albumsModel",
            [
                {"token": f"album{i}", "name": f"Album {i}", "count": i + 1}
                for i in range(albums)
            ],
        )
        pane.setProperty(
            "peopleModel",
            [{"name": f"Ember {i}", "count": i + 1} for i in range(people)],
        )
        pane.setProperty("unnamedFaceCount", unnamed)
        pane.setProperty("ignoredFaceCount", ignored)
        if exported:
            pane.setProperty(
                "exportedFolders", [{"path": "/export/nyar", "name": "nyar"}]
            )
        if collections:
            pane.setProperty(
                "customCollectionsModel",
                [{"name": "Nyaralások", "folders": ["/kepek/balaton"]}],
            )
        # a kijelölt mappa a lista közepéről: a görgő-léptetésnek (#77)
        # mindkét irányban legyen hova lépnie
        paths = list(folders_model.folder_paths())
        pane.setProperty("selectedPath", paths[len(paths) // 2])

        # a ColumnLayout az újratördelést a következő polish-körben végzi.
        # #1463: itt korábban `QTest.qWait(80)` állt — a 80 ms találgatás
        # volt; most magát az elrendezés megállását várjuk ki.
        _var_a_hasab_elrendezesere(qt_app, pane)

        _KEEPALIVE.extend((engine, component, view, pane, folders_model))
        return view, pane, paths

    return _render


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _repeater_item(pane, repeater_name, index):
    """A `Repeater` index. delegate-példánya.

    A Repeater-elemeket a `findChild` NEM látja (MEMORY 2026-07-31), a
    `Repeater.itemAt(int)` viszont visszaadja őket — PySide alól csak
    `QMetaObject.invokeMethod`-dal, explicit `Q_RETURN_ARG`-gal."""
    repeater = _child(pane, repeater_name)
    item = QMetaObject.invokeMethod(
        repeater,
        "itemAt",
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG(QQuickItem),
        Q_ARG(int, index),
    )
    assert item is not None, f"{repeater_name}[{index}] nem jött létre"
    return item


def _center_in_window(item):
    """Az elem középpontja az ABLAK koordinátarendszerében."""
    return item.mapToScene(QPointF(item.width() / 2, item.height() / 2))


def _send_wheel(qt_app, view, item, *, angle_delta: int = -120):
    """VALÓDI görgő-esemény az elem közepére (nem a `wheelStep` hívása)."""
    center = _center_in_window(item)
    assert 0 <= center.y() <= view.height(), (
        f"a mért pont ({center.y():.0f}) az ablakon kívülre esik — a teszt "
        "így nem mérne semmit"
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


#: A hasáb összes jobbklikk-menüje — a tesztek azt nézik, MELYIK nyílt meg.
_MENUK = (
    "folderContextMenu",
    "folderListContextMenu",
    "albumContextMenu",
    "peopleAlbumContextMenu",
    "collectionContextMenu",
)


def _open_menus(pane):
    return sorted(
        name
        for name in _MENUK
        if (menu := pane.findChild(QObject, name)) is not None
        and menu.property("visible")
    )


def _right_click(qt_app, view, pane, item):
    center = _center_in_window(item)
    assert 0 <= center.y() <= view.height(), (
        f"a kattintási pont ({center.y():.0f}) az ablakon kívülre esik"
    )
    QTest.mouseClick(
        view,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )
    # #1463: itt korábban `QTest.qWait(50)` állt — annak a feltevésnek a
    # fali órás alakja, hogy „50 ms alatt kinyílik a popup”. A VALÓDI
    # feltétel az, hogy megjelenjen VALAMELYIK menü; hogy a HELYES nyílt-e
    # meg, azt utána a hívó teszt állítja — az őr foga tehát megmarad.
    _var(qt_app, lambda: _open_menus(pane) != [])


class TestPaneScrollsAsAWhole:
    """#730: a hasáb egésze görgethető, a mappalista nem nyomódik nullára."""

    @pytest.mark.parametrize("people", [30, 40])
    def test_folder_list_keeps_a_usable_height(self, render_pane, people):
        """Mérve: 30 személynél a `folderListView` magassága 0 px volt."""
        _view, pane, _paths = render_pane(people=people)
        folder_list = _child(pane, "folderListView")
        assert folder_list.property("height") > 0, (
            f"{people} személynél a mappalista magassága "
            f"{folder_list.property('height')} px — a lista eltűnt (#730)"
        )

    @pytest.mark.parametrize("people", [30, 40])
    def test_the_other_header_can_be_scrolled_into_view(
        self, render_pane, qt_app, people
    ):
        """Mérve: 30 személynél az „Egyéb” fejléc y-ja 812 (ablak: 800),
        40-nél 1032 — és semmivel nem lehetett odagörgetni."""
        view, pane, _paths = render_pane(people=people)
        flickable = _child(pane, "folderPaneFlickable")

        # a hasáb aljára görgetve az utolsó fejlécnek látszania KELL
        flickable.setProperty(
            "contentY",
            max(
                0.0,
                flickable.property("contentHeight")
                - flickable.property("height"),
            ),
        )
        qt_app.processEvents()

        header = _child(pane, "otherHeaderRow")
        top = _center_in_window(header).y() - header.property("height") / 2
        bottom = top + header.property("height")
        assert 0 <= top and bottom <= view.height(), (
            f"{people} személynél az „Egyéb” fejléc a hasáb aljára görgetve "
            f"is az ablakon kívül van (y: {top:.0f}–{bottom:.0f}, ablak: "
            f"{view.height()} px) — #730"
        )

    def test_the_pane_has_its_own_scrollbar(self, render_pane):
        """Az eredetiben a bal panelnek SAJÁT görgetősávja van, ami akkor is
        látszik, amikor nem görgetünk (ui-audit-mainwindow.md 3.1)."""
        _view, pane, _paths = render_pane(people=30)
        scrollbar = _child(pane, "folderPaneScrollBar")
        assert scrollbar.property("visible") is True
        assert scrollbar.property("barVisible") is True

    def test_the_selected_folder_is_scrolled_into_view(
        self, render_pane, qt_app
    ):
        """A görgetés bevezetése nem veheti el a #10/#77 viselkedést: a
        kívülről (kereső-javaslat, feed) beállított kijelölés SORÁNAK
        látszania kell — a lista már nem görget, tehát a hasáb dolga."""
        view, pane, paths = render_pane(people=30)
        folder_list = _child(pane, "folderListView")

        pane.setProperty("selectedPath", paths[-1])
        qt_app.processEvents()

        # a modell évszám-sorokat is tartalmaz, ezért a sorindexet ő adja
        row = folder_list.property("model").rowOfPath(paths[-1])
        assert row >= 0
        row_top = (
            folder_list.mapToScene(QPointF(0, 0)).y()
            + row * pane.property("rowHeight")
        )
        assert 0 <= row_top <= view.height() - pane.property("rowHeight"), (
            f"a kijelölt mappa sora nem került látótérbe (y: {row_top:.0f}, "
            f"ablak: {view.height()} px) — #730"
        )


class TestWheelOverThePaneDoesNotJumpFolders:
    """#731: a görgő a hasáb fölött görget, nem MÁSIK mappát nyit meg."""

    @pytest.mark.parametrize(
        "zone",
        ["albumsHeaderRow", "peopleHeaderRow", "folderPaneHeaderRow"],
    )
    def test_wheel_over_a_header_does_not_choose_a_folder(
        self, render_pane, qt_app, zone
    ):
        view, pane, _paths = render_pane(people=3)
        received: list[str] = []
        pane.folderChosen.connect(received.append)

        _send_wheel(qt_app, view, _child(pane, zone))

        assert received == [], (
            f"a görgő a(z) {zone} fölött mappát nyitott meg: {received} "
            "(#731)"
        )

    @pytest.mark.parametrize(
        ("repeater", "index"),
        [("albumRepeater", 0), ("peopleRepeater", 0)],
    )
    def test_wheel_over_an_album_or_person_row_does_not_choose_a_folder(
        self, render_pane, qt_app, repeater, index
    ):
        view, pane, _paths = render_pane(people=3, albums=2)
        received: list[str] = []
        pane.folderChosen.connect(received.append)

        _send_wheel(qt_app, view, _repeater_item(pane, repeater, index))

        assert received == [], (
            f"a görgő a(z) {repeater}[{index}] sor fölött mappát nyitott "
            f"meg: {received} (#731)"
        )

    def test_wheel_over_a_header_scrolls_the_pane(self, render_pane, qt_app):
        """A görgetés helyébe lépő viselkedés: a hasáb TÉNYLEG mozdul."""
        view, pane, _paths = render_pane(people=30)
        flickable = _child(pane, "folderPaneFlickable")
        assert flickable.property("contentY") == 0

        _send_wheel(qt_app, view, _child(pane, "albumsHeaderRow"))
        # #1463: itt korábban `QTest.qWait(300)` állt — a `Flickable`
        # lassulásának becsült ideje. A valódi feltétel maga az állítás
        # előfeltétele: elmozdult-e a tartalom. Ha igen, azonnal
        # továbbmegyünk; ha nem, a határidő lejárta után az alatta lévő
        # állítás mondja meg, mi a baj (#730/#731).
        _var(qt_app, lambda: flickable.property("contentY") > 0)

        assert flickable.property("contentY") > 0, (
            "a görgő a hasáb fejléce fölött nem görgetett (#730/#731)"
        )

    def test_wheel_over_the_folder_list_still_steps(self, render_pane, qt_app):
        """#77 nem veszhet el: a mappalista fölött a görgő LÉPTET."""
        view, pane, paths = render_pane(people=3)
        received: list[str] = []
        pane.folderChosen.connect(received.append)

        _send_wheel(qt_app, view, _child(pane, "folderListView"))

        assert len(received) == 1, (
            f"a mappalista fölötti görgő nem léptetett: {received} (#77/#731)"
        )
        assert received[0] in paths


class TestRightClickOpensTheRowsOwnMenu:
    """#732: mind a négy sor a SAJÁT menüjét adja, nem a hasáb menüjét."""

    def test_exported_folder_row_opens_the_folder_menu(
        self, render_pane, qt_app
    ):
        view, pane, _paths = render_pane(exported=True)
        row = _repeater_item(pane, "exportedFolderRepeater", 0)

        _right_click(qt_app, view, pane, row)

        assert _open_menus(pane) == ["folderContextMenu"], (
            "az exportált mappa sora nem a mappa-menüt adta (#732)"
        )
        assert _child(pane, "folderContextMenu").property("folderPath") == (
            "/export/nyar"
        )

    def test_collection_folder_row_opens_the_folder_menu(
        self, render_pane, qt_app
    ):
        view, pane, _paths = render_pane(collections=True)
        collection = _repeater_item(pane, "customCollectionsRepeater", 0)
        row = QMetaObject.invokeMethod(
            _child(collection, "customCollectionFoldersRepeater_Nyaralások"),
            "itemAt",
            Qt.ConnectionType.DirectConnection,
            Q_RETURN_ARG(QQuickItem),
            Q_ARG(int, 0),
        )
        assert row is not None, "a gyűjtemény-mappa sora nem jött létre"

        _right_click(qt_app, view, pane, row)

        assert _open_menus(pane) == ["folderContextMenu"], (
            "a gyűjtemény-mappa sora nem a mappa-menüt adta (#732)"
        )
        assert _child(pane, "folderContextMenu").property("folderPath") == (
            "/kepek/balaton"
        )

    def test_unnamed_faces_row_opens_the_people_album_menu(
        self, render_pane, qt_app
    ):
        """A „Névtelenek” az eredetiben ALBUM (`PplAlbum`), tehát az
        Emberek-album menüjét kell adnia (ui-audit-context-menus.md A.2)."""
        view, pane, _paths = render_pane(unnamed=5)

        _right_click(qt_app, view, pane, _child(pane, "unnamedFacesItem"))

        assert _open_menus(pane) == ["peopleAlbumContextMenu"], (
            "a „Névtelenek” sor nem az Emberek-album menüjét adta (#732)"
        )

    def test_ignored_faces_row_opens_the_people_album_menu(
        self, render_pane, qt_app
    ):
        """A „Mellőzött emberek” ugyanúgy ALBUM (`CAlbumLabel::Ignored`)."""
        view, pane, _paths = render_pane(ignored=3)

        _right_click(qt_app, view, pane, _child(pane, "ignoredFacesItem"))

        assert _open_menus(pane) == ["peopleAlbumContextMenu"], (
            "a „Mellőzött emberek” sor nem az Emberek-album menüjét adta "
            "(#732)"
        )

"""QML-funkcionális teszt: az Emberek-panel EGY fejléce — #3566.

Az eredeti panel egyetlen fejlécet (`status_label`) és egyetlen listát
mutat; a fejlécet a `0x00647df0` választja (spec
`picasa-arcfelismeres.md` 9/b–9/d):

    EGYKÉPES ág — a szerkesztőben, VAGY (1 kép ÉS nem személy-album):
      van személy → „In this photo:"            (InThis)
      van kép     → „Who is in these photos?"   (Who)
      különben    → instructions 4 (Text5)
    TÖBBKÉPES ág — minden más:
      van személy → személy-album ? „Also in these photos:"   (Known1)
                                  : „People in these photos:" (Known2)
      van kép     → csoportosítva ? „Unnamed people in these photos:"
                                  : „Unnamed groups of people:"
      különben    → személy-album ? instructions 3 (Text4)
                                  : instructions 4 (Text5)

A „Név nélküliek" albumban 0 kijelölésnél instructions 2 (Text3).

A kijelölés VALÓDI kattintás a rács celláira (Ctrl-lal több kép) — nem a
panel property-jeinek felülírása.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg

_ANNA_ID = "1111111111111111"
_BELA_ID = "2222222222222222"
# a.jpg: Anna + Béla · b.jpg: Anna · c.jpg, d.jpg: senki megnevezett
_INI = (
    "[Contacts2]\n"
    f"{_ANNA_ID}=Anna;;\n"
    f"{_BELA_ID}=Béla;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID};"
    f"rect64(5000280075006e00),{_BELA_ID}\n"
    "[b.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID}\n"
)

TEXT3 = "No people have been found yet"
TEXT4 = "appear with the currently selected person"
TEXT5 = "People who appear in the currently selected photos"


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _settle(qt_app, rounds: int = 5):
    for _ in range(rounds):
        qt_app.processEvents()


def _library(window, controller, qt_app, tmp_path):
    from picasapy.app.worker_thread import wait_for_all_background_workers

    lib = tmp_path / "kepek"
    make_jpeg(lib / "c.jpg", size=(120, 90))
    make_jpeg(lib / "d.jpg", size=(120, 90))
    (lib / ".picasa.ini").write_text(_INI, encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    _settle(qt_app)
    # a panel megnyitása a Nézet menüből
    QMetaObject.invokeMethod(
        _child(window, "menuViewPeople"), "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    _settle(qt_app)
    return lib


def _unselect(window, qt_app):
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    _settle(qt_app)


def _cell(window, row: int) -> QQuickItem:
    for item in _walk(window.contentItem()):
        if item.objectName() != "thumbMouseArea" or not item.isVisible():
            continue
        cell = item.parentItem()
        if cell is not None and cell.property("index") == row:
            return item
    raise AssertionError(f"a(z) {row}. sor cellája nincs a rácson")


def _select(window, controller, qt_app, lib, *names: str):
    """Kattintás az első képre, Ctrl+kattintás a többire — a rácson."""
    _unselect(window, qt_app)
    for i, name in enumerate(names):
        row = controller.photos.rowOfPath(str(lib / name))
        assert row >= 0, f"{name} nincs a rácson"
        item = _cell(window, row)
        center = item.mapToScene(item.boundingRect().center())
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ControlModifier if i
            else Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        _settle(qt_app)
    kijelolt = window.property("selectedIndexes")
    if hasattr(kijelolt, "toVariant"):
        kijelolt = kijelolt.toVariant()
    assert len(kijelolt) == len(names)


def _visible_rows(panel) -> list[str]:
    return sorted(
        item.objectName().removeprefix("peoplePanelRow_")
        for item in _walk(panel)
        if item.objectName().startswith("peoplePanelRow_") and item.isVisible()
    )


def _header(window) -> str | None:
    label = _child(window, "peoplePanelHeader")
    return label.property("text") if label.property("visible") else None


def _empty_text(window) -> str | None:
    empty = _child(window, "peoplePanelEmptyText")
    return empty.property("text") if empty.property("visible") else None


def _person_album(controller, qt_app, name="Anna"):
    controller.showPerson(name)
    _settle(qt_app)


class TestFolderView:
    def test_one_photo_with_named_people(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)

        _select(window, controller, qt_app, lib, "a.jpg")

        assert _header(window) == "In this photo:"
        assert _visible_rows(_child(window, "peoplePanel")) == ["Anna", "Béla"]
        assert _empty_text(window) is None

    def test_several_photos_with_named_people(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)

        _select(window, controller, qt_app, lib, "a.jpg", "c.jpg")

        assert _header(window) == "People in these photos:"
        assert _visible_rows(_child(window, "peoplePanel")) == ["Anna", "Béla"]

    def test_one_photo_without_named_people_asks_who(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)

        _select(window, controller, qt_app, lib, "c.jpg")

        assert _header(window) == "Who is in these photos?"
        assert _visible_rows(_child(window, "peoplePanel")) == []
        assert _empty_text(window) is None

    def test_several_photos_without_named_people(
        self, qml_app, qt_app, tmp_path
    ):
        """A többképes ág „van kép" sora: a csoportosítás jelzője
        (`+0x2af`) csak a Név nélküliek albumban áll, máshol kibontott."""
        window, controller, _engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)

        _select(window, controller, qt_app, lib, "c.jpg", "d.jpg")

        assert _header(window) == "Unnamed groups of people:"
        assert _empty_text(window) is None

    def test_nothing_selected_is_text5_not_text3(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _library(window, controller, qt_app, tmp_path)

        _unselect(window, qt_app)

        assert _header(window) is None
        assert TEXT5 in _empty_text(window)


class TestPersonAlbum:
    def test_one_photo_is_also_in_these_photos(self, qml_app, qt_app, tmp_path):
        """Személy-albumban egy képnél is a többképes ág fut."""
        window, controller, _engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        _person_album(controller, qt_app)

        _select(window, controller, qt_app, lib, "a.jpg")

        assert _header(window) == "Also in these photos:"
        assert _visible_rows(_child(window, "peoplePanel")) == ["Anna", "Béla"]

    def test_one_header_one_list(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        _person_album(controller, qt_app)

        _select(window, controller, qt_app, lib, "a.jpg", "b.jpg")

        panel = _child(window, "peoplePanel")
        assert _header(window) == "Also in these photos:"
        # EGY lista: minden név egyszer szerepel, nincs második szakasz
        assert _visible_rows(panel) == ["Anna", "Béla"]
        visible_texts = [
            item.property("text") for item in _walk(panel)
            if item.isVisible() and item.property("text") in (
                "In this photo:", "People in these photos:",
                "Also in these photos:",
            )
        ]
        assert visible_texts == ["Also in these photos:"]

    def test_nothing_selected_is_text4(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        _library(window, controller, qt_app, tmp_path)
        _person_album(controller, qt_app)

        _unselect(window, qt_app)

        assert _header(window) is None
        assert TEXT4 in _empty_text(window)


class TestUnnamedAlbum:
    def _unnamed(self, window, qt_app, selected):
        _child(window, "folderPane").unnamedFacesChosen.emit()
        _settle(qt_app)
        _child(window, "unnamedFacesView").setProperty("selectedCount", selected)
        _settle(qt_app)

    def test_nothing_selected_is_text3(self, qml_app, qt_app, tmp_path):
        """A Text3 a „Név nélküliek" mód üres esete — csak ott."""
        window, controller, _engine = qml_app
        _library(window, controller, qt_app, tmp_path)

        self._unnamed(window, qt_app, 0)

        assert _header(window) is None
        assert TEXT3 in _empty_text(window)

    def test_one_face_asks_who(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        # a rács kijelölése (Anna képe) NEM számít: az albumban arcokat
        # jelölünk ki, és azok névtelenek
        _select(window, controller, qt_app, lib, "a.jpg")

        self._unnamed(window, qt_app, 1)

        assert _header(window) == "Who is in these photos?"
        assert _visible_rows(_child(window, "peoplePanel")) == []


class TestEditor:
    def test_the_viewer_is_always_the_single_photo_branch(
        self, qml_app, qt_app, tmp_path
    ):
        """A szerkesztő előnézeténél az egyképes ág fut — személy-albumban
        is „In this photo:", nem „Also in these photos:"."""
        window, controller, _engine = qml_app
        lib = _library(window, controller, qt_app, tmp_path)
        _person_album(controller, qt_app)
        _select(window, controller, qt_app, lib, "a.jpg")

        row = controller.photos.rowOfPath(str(lib / "a.jpg"))
        window.setProperty("viewerOpen", True)
        viewer = _child(window, "photoViewer")
        viewer.setProperty("currentIndex", row)
        window.setProperty("activeDrawerTab", "people")
        _settle(qt_app, 10)

        panel = _child(window, "viewerPeoplePanel")
        header = _child(panel, "peoplePanelHeader")
        assert header.property("visible") is True
        assert header.property("text") == "In this photo:"
        assert _visible_rows(panel) == ["Anna", "Béla"]

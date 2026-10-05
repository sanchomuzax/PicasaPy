"""#4258: a Reset Faces csak a kijelölt képek ini-arcait törli."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.app.faces_helper import FacesHelper
from picasapy.index import open_index, sync_tree
from picasapy.ini import load_document
from support.jpeg_factory import make_jpeg


def _two_folder_library(root):
    first = root / "album-a"
    second = root / "album-b"
    first.mkdir()
    second.mkdir()
    first_photo = first / "selected.jpg"
    second_photo = second / "untouched.jpg"
    make_jpeg(first_photo)
    make_jpeg(second_photo)
    (first / ".picasa.ini").write_text(
        "[selected.jpg]\ncaption=keep-selected\n", encoding="utf-8"
    )
    (second / ".picasa.ini").write_text(
        "[untouched.jpg]\ncaption=keep-untouched\n", encoding="utf-8"
    )

    helper = FacesHelper()
    assert helper.addFace(str(first_photo), 0.1, 0.2, 0.4, 0.6, "Ada")
    assert helper.addFace(str(second_photo), 0.2, 0.3, 0.5, 0.7, "Bela")


def _open_context_menu(window, qt_app, row):
    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None
    QMetaObject.invokeMethod(
        window,
        "openPhotoContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", row),
        Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5),
        Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    menu = window.findChild(QObject, "photoContextMenu")
    assert menu is not None and menu.property("visible") is True
    return menu


def _click_menu_item(item, qt_app):
    assert item.isEnabled()
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_reset_faces_menu_click_only_removes_selected_photo_ini_entry(
    qml_app, qt_app, tmp_path, height_offset
):
    """Két mappa, egy kijelölés: a tényleges menükattintás csak azt érinti."""
    window, controller, _engine = qml_app
    window.setHeight(window.height() + height_offset)
    qt_app.processEvents()
    library = tmp_path / "kepek"
    (library / "a.jpg").unlink()
    (library / "b.jpg").unlink()
    _two_folder_library(library)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload()
    qt_app.processEvents()

    first_photo = library / "album-a" / "selected.jpg"
    second_photo = library / "album-b" / "untouched.jpg"

    first_ini = first_photo.parent / ".picasa.ini"
    second_ini = second_photo.parent / ".picasa.ini"
    before_first = load_document(first_ini).section(first_photo.name).get("faces")
    before_second = load_document(second_ini).section(second_photo.name).get("faces")
    assert before_first
    assert before_second

    selected_row = controller.photos.rowOfPath(str(first_photo))
    untouched_row = controller.photos.rowOfPath(str(second_photo))
    assert selected_row >= 0 and untouched_row >= 0
    window.setProperty("selectedIndexes", [selected_row])
    window.setProperty("selectedIndex", selected_row)

    menu = _open_context_menu(window, qt_app, selected_row)
    item = menu.findChild(QObject, "contextMenuResetFaces")
    assert item is not None
    _click_menu_item(item, qt_app)

    after_first_document = load_document(first_ini)
    after_second_document = load_document(second_ini)
    after_first_section = after_first_document.section(first_photo.name)
    after_second_section = after_second_document.section(second_photo.name)
    after_first = after_first_section.get("faces") if after_first_section else None
    after_second = after_second_section.get("faces") if after_second_section else None
    assert after_first is None, "a kijelölt kép faces= bejegyzése megmaradt"
    assert after_first_section.get("caption") == "keep-selected"
    assert after_first_document.section("Contacts2") is not None
    assert after_second == before_second, "a másik mappa arcadata megváltozott"
    assert after_second_section.get("caption") == "keep-untouched"

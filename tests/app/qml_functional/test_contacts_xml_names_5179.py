"""#5179: a központi névjegy neve minden felületen ugyanaz."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import ContactXmlEntry, save_contacts_xml
from tests.support.varakozas import var_feltetelre

_CONTACT_ID = "00000000000000a1"
_PERSON_NAME = "Központi Név"
_FACE_RECT = "1e00280045006e00"
_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)


def _find_item(root, object_name):
    direct = root.findChild(QQuickItem, object_name)
    if direct is not None:
        return direct

    def walk(item):
        for child in item.childItems():
            if child.objectName() == object_name:
                return child
            nested = walk(child)
            if nested is not None:
                return nested
        return None

    return walk(root.contentItem())


def _click(qt_app, item):
    assert item is not None, "a kattintandó elem hiányzik"
    assert item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _invoke(obj, method):
    return QMetaObject.invokeMethod(
        obj, method, Qt.ConnectionType.DirectConnection
    )


def _prepare_center_only_face(qml_app, qt_app):
    window, controller, _engine = qml_app
    photo = Path(controller.photos.filePathAt(0))
    photo.parent.mkdir(parents=True, exist_ok=True)
    (photo.parent / ".picasa.ini").write_text(
        f"[{photo.name}]\nfaces=rect64({_FACE_RECT}),{_CONTACT_ID}\n",
        encoding="utf-8",
    )
    (photo.parent / "unrelated.jpg").write_bytes(photo.read_bytes())
    central = Path(controller._db_path).parent / "contacts" / "contacts.xml"
    save_contacts_xml(
        central,
        (
            ContactXmlEntry(
                person_id=_CONTACT_ID,
                name=_PERSON_NAME,
                modified_time="2026-10-17T10:00:00+02:00",
                local_contact="1",
            ),
        ),
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, photo.parent)
    controller._side_pane_stash = None
    controller._reload_after_sync()
    qt_app.processEvents()
    return window, controller, photo


def _visible(item):
    return item is not None and item.isVisible()


def _dialog(window):
    loader = window.findChild(QObject, "peopleManagerLoader")
    return loader.property("item") if loader is not None else None


def _dialog_item(window, object_name):
    dialog = _dialog(window)
    if dialog is not None:
        found = dialog.findChild(QObject, object_name)
        if found is not None:
            return found
    return _find_item(window, object_name)


def test_nezokeret_a_kizarolag_kozponti_nevjegy_nevet_mutatja(
    qml_app, qt_app
):
    window, _controller, _photo = _prepare_center_only_face(qml_app, qt_app)
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QQuickItem, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    _invoke(viewer, "toggleFacesEdit")
    qt_app.processEvents()
    assert viewer.property("facesVisible") is True

    overlay = window.findChild(QQuickItem, "facesOverlay")
    assert overlay is not None
    faces = overlay.property("faces")
    assert len(faces) == 1
    assert faces[0]["name"] == _PERSON_NAME


@pytest.mark.parametrize("height_delta", _WINDOW_HEIGHT_OFFSETS)
def test_embersor_kattintassal_a_kozponti_nevu_szemelyalbumot_nyitja(
    qml_app, qt_app, height_delta
):
    window, controller, photo = _prepare_center_only_face(qml_app, qt_app)
    window.setHeight(window.height() + height_delta)
    assert any(person["name"] == _PERSON_NAME for person in controller.people)
    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    qt_app.processEvents()

    row_name = f"personItem_{_PERSON_NAME}"
    assert var_feltetelre(
        qt_app,
        lambda: _visible(_find_item(window, row_name))
        and _find_item(window, row_name).width() > 0
        and _find_item(window, row_name).height() > 0,
        3.0,
    ), "a központi contacts.xml név nem jelent meg (méretezve) az Emberek sorban"
    _click(qt_app, _find_item(window, row_name))
    assert controller.currentPersonName == _PERSON_NAME
    assert controller.viewModeName == "person"
    assert var_feltetelre(
        qt_app,
        lambda: controller.photos.rowCount() == 3
        and photo in {
            Path(controller.photos.filePathAt(row))
            for row in range(controller.photos.rowCount())
        }
        and len(controller.personAlbumPhotos) == 1,
        3.0,
    ), "a teljes mappa-feed vagy a központi névhez tartozó arcsáv hiányzik"
    controller._reload_after_sync()
    assert var_feltetelre(
        qt_app,
        lambda: controller.photos.rowCount() == 3
        and photo in {
            Path(controller.photos.filePathAt(row))
            for row in range(controller.photos.rowCount())
        }
        and len(controller.personAlbumPhotos) == 1,
        3.0,
    ), "újratöltés után eltűnt a teljes mappa-feed vagy a személy arcsávja"


def _open_people_manager(window, qt_app):
    menu_bar = window.property("menuBar")
    headers = menu_bar.findChildren(QQuickItem)
    tools_header = next(
        (
            obj
            for obj in headers
            if "MenuBarItem" in obj.metaObject().className()
            and obj.property("text") in {"&Tools", "&Eszközök"}
        ),
        None,
    )
    assert tools_header is not None, "az Eszközök menüfejléce hiányzik"
    _click(qt_app, tools_header)
    assert var_feltetelre(
        qt_app,
        lambda: _find_item(window, "menuToolsPeopleManager") is not None,
        3.0,
    ), "a Személykezelő menüpont nem jelent meg"
    _click(qt_app, _find_item(window, "menuToolsPeopleManager"))
    assert var_feltetelre(
        qt_app,
        lambda: (
            (dialog := _dialog(window)) is not None
            and dialog.property("visible") is True
        ),
        3.0,
    ), "a Személykezelő nem nyílt meg"
    return _dialog(window)


@pytest.mark.parametrize("height_delta", _WINDOW_HEIGHT_OFFSETS)
def test_szemelykezelo_a_kozponti_nevhez_szamolja_az_arcot(
    qml_app, qt_app, height_delta
):
    window, _controller, _photo = _prepare_center_only_face(qml_app, qt_app)
    window.setHeight(window.height() + height_delta)
    dialog = _open_people_manager(window, qt_app)
    contact = _dialog_item(window, f"peopleManagerContact_{_PERSON_NAME}")
    assert contact is not None, "a központi név hiányzik a Személykezelőből"
    _click(qt_app, contact)

    name = _dialog_item(window, "peopleManagerNameField")
    photo_count = _dialog_item(window, "peopleManagerPhotoCount")
    assert name is not None and name.property("text") == _PERSON_NAME
    assert photo_count is not None and photo_count.property("text") == "1"
    assert dialog.property("visible") is True

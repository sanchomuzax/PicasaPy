"""#5182: a Choose útja és a kereséshez igazodó személy-kijelölés."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QSettings, Qt
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces
from picasapy.ini import contacts_of, load_document, parse_faces
from tests.support.varakozas import var_feltetelre

_PERSON_NAME = "Teszt Elek"


def _wait(qt_app, condition, seconds: float = 10.0) -> bool:
    return var_feltetelre(qt_app, condition, seconds)


def _find_object(root, name: str):
    return root.findChild(QObject, name)


def _walk_items(item):
    for child in item.childItems():
        yield child
        yield from _walk_items(child)


def _find_item(window, name: str):
    return next(
        (
            item
            for item in _walk_items(window.contentItem())
            if item.objectName() == name
        ),
        None,
    )


def _click(qt_app, item) -> None:
    assert item is not None, "A kattintandó felületi elem hiányzik."
    assert item.property("enabled") is not False
    assert item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _text_descendant(item, expected: str) -> bool:
    if item.property("text") == expected:
        return True
    return any(_text_descendant(child, expected) for child in item.childItems())


def _face(left: int, top: int, right: int, bottom: int) -> FaceDetection:
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    return FaceDetection(
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        score=0.99,
        landmarks=FaceLandmarks(
            right_eye=(center_x - 12, center_y - 12),
            left_eye=(center_x + 12, center_y - 12),
            nose=(center_x, center_y),
            mouth_right=(center_x - 8, center_y + 14),
            mouth_left=(center_x + 8, center_y + 14),
        ),
    )


def _seed_named_and_unnamed_faces(controller, face_scan):
    photo_path = Path(controller.photos.filePathAt(0))
    target_path = Path(controller.photos.filePathAt(1))
    with open_index(controller._db_path) as conn:
        photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = ?", (photo_path.name,)
        ).fetchone()["id"]
        target_photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = ?", (target_path.name,)
        ).fetchone()["id"]
        replace_faces(
            conn,
            photo_id,
            [_face(20, 12, 110, 130)],
        )
        replace_faces(
            conn,
            target_photo_id,
            [_face(15, 10, 85, 90)],
        )
        face_ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM face WHERE photo_id IN (?, ?) ORDER BY photo_id",
                (photo_id, target_photo_id),
            )
        ]
        assert len(face_ids) == 2
        conn.commit()

    assert face_scan.assignNameToFaces([face_ids[0]], _PERSON_NAME)
    controller.refreshCollections()
    face_scan.unnamedCountChanged.emit()
    return photo_path, target_path, face_ids[1]


@pytest.mark.parametrize("height_offset", (-5, 0, 5))
def test_unnamed_tile_choose_assigns_existing_person_without_duplicate_contact(
    qml_app, qt_app, height_offset, tmp_path
):
    window, controller, engine = qml_app
    initial_height = int(window.height())
    window.setHeight(initial_height + height_offset)
    assert _wait(
        qt_app, lambda: int(window.height()) == initial_height + height_offset
    )
    face_scan = engine.rootContext().contextProperty("faceScanController")
    # A Windows-CI-n a tesztkörnyezet alapértelmezett (natív, név nélküli)
    # QSettings-e nem írható (fileName='', AccessError), így az üdvözlőablak
    # jelzője nem mentődik, és az ablak eltakarja a csempe mezőjét (mint a
    # test_unnamed_faces_view_5183.py-ban); itt ideiglenes, fájlalapú tároló.
    if face_scan._settings.status() != QSettings.Status.NoError or not face_scan._settings.fileName():
        face_scan._settings = QSettings(str(tmp_path / "facescan.ini"), QSettings.Format.IniFormat)
    face_scan.markUnnamedWelcomeShown()
    assert face_scan.unnamedWelcomeHasBeenShown() is True
    photo_path, target_path, target_face_id = _seed_named_and_unnamed_faces(
        controller, face_scan
    )
    assert _wait(qt_app, lambda: face_scan.unnamedCount == 1)

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert _wait(qt_app, lambda: unnamed_row is not None and unnamed_row.width() > 0)
    _click(qt_app, unnamed_row)

    unnamed_view = _find_item(window, "unnamedFacesView")
    assert _wait(
        qt_app,
        lambda: unnamed_view is not None
        and unnamed_view.property("visible") is True,
    )
    name_field = _find_item(window, f"unnamedFaceNameField_{target_face_id}")
    assert _wait(qt_app, lambda: name_field is not None and name_field.width() > 0)
    _click(qt_app, name_field)
    for character in _PERSON_NAME:
        QTest.keyEvent(QTest.KeyAction.Click, name_field.window(), ord(character))
    QTest.keyClick(name_field.window(), Qt.Key.Key_Return)

    dialog = _find_object(window, "peopleManagerDialog")
    assert _wait(
        qt_app,
        lambda: dialog is not None and dialog.property("visible") is True,
    )
    selected_person = _find_item(window, "peopleManagerContact_Teszt Elek")
    choose_button = _find_item(window, "peopleManagerOkButton")
    assert selected_person is not None
    assert selected_person.property("highlighted") is True
    assert _find_item(window, "peopleManagerPhotoCount").property("text") == (
        "1 Photo in PicasaPy"
    )
    assert choose_button.property("text") == "Choose"

    ini_path = target_path.parent / ".picasa.ini"
    before = load_document(ini_path)
    existing_contacts = [
        contact for contact in contacts_of(before) if contact.name == _PERSON_NAME
    ]
    assert len(existing_contacts) == 1
    person_id = existing_contacts[0].person_id
    _click(qt_app, choose_button)

    assert _wait(
        qt_app,
        lambda: dialog.property("visible") is False
        and face_scan.unnamedCount == 0,
    )
    person_row = _find_item(window, "personItem_Teszt Elek")
    assert _wait(
        qt_app,
        lambda: person_row is not None
        and _text_descendant(person_row, "Teszt Elek (2)"),
    )

    saved = load_document(ini_path)
    saved_contacts = [
        contact for contact in contacts_of(saved) if contact.name == _PERSON_NAME
    ]
    assert len(saved_contacts) == 1
    assert saved_contacts[0].person_id == person_id
    assigned_faces = tuple(
        face
        for path in (photo_path, target_path)
        for face in parse_faces(saved.section(path.name).get("faces") or "")
    )
    assert len(assigned_faces) == 2
    assert all(face.contact_id == person_id for face in assigned_faces)


def _open_people_manager(window, qt_app) -> None:
    loader = _find_object(window, "peopleManagerLoader")
    assert loader is not None
    loader.setProperty("active", True)
    dialog = _find_object(window, "peopleManagerDialog")
    assert _wait(qt_app, lambda: dialog is not None)
    assert QMetaObject.invokeMethod(
        dialog, "open", Qt.ConnectionType.DirectConnection
    )
    assert _wait(
        qt_app,
        lambda: dialog is not None and dialog.property("visible") is True,
    )


def test_search_hides_selected_person_and_clears_highlight_and_details(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    assert controller.savePeopleManagerChanges(
        [
            {"action": "create", "name": "Anna", "email": ""},
            {"action": "create", "name": "Bela", "email": ""},
        ]
    )
    _open_people_manager(window, qt_app)

    selected_row = _find_item(window, "peopleManagerContact_Bela")
    assert _wait(qt_app, lambda: selected_row is not None and selected_row.width() > 0)
    _click(qt_app, selected_row)
    name_field = _find_item(window, "peopleManagerNameField")
    assert name_field.property("text") == "Bela"

    search_field = _find_item(window, "peopleManagerSearchField")
    _click(qt_app, search_field)
    QTest.keyClick(search_field.window(), Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    for character in "Anna":
        QTest.keyEvent(QTest.KeyAction.Click, search_field.window(), ord(character))
    assert _wait(qt_app, lambda: search_field.property("text") == "Anna")

    contact_list = _find_item(window, "peopleManagerContactList")
    email_field = _find_item(window, "peopleManagerEmailField")
    assert contact_list.property("currentIndex") == -1
    assert _find_object(window, "peopleManagerDialog").property("selectedKey") == ""
    assert name_field.property("text") == ""
    assert email_field.property("text") == ""
    assert _find_item(window, "peopleManagerPhotoStatus").property("visible") is False

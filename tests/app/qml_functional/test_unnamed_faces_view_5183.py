"""#5183: a Név nélküliek album eredeti Picasa-elrendezése és névadási útja."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import (
    all_photos,
    group_unnamed_faces,
    open_index,
    replace_faces,
    store_embedding,
)
from picasapy.ini import contacts_of, load_document, parse_faces
from support.fixture_guards import qml_warning_guard
from tests.support.varakozas import var_feltetelre

_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)


def _face(left: int, top: int, right: int, bottom: int) -> FaceDetection:
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    landmarks = FaceLandmarks(
        right_eye=(center_x - 20, center_y - 20),
        left_eye=(center_x + 20, center_y - 20),
        nose=(center_x, center_y),
        mouth_right=(center_x - 12, center_y + 24),
        mouth_left=(center_x + 12, center_y + 24),
    )
    return FaceDetection(
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        score=0.99,
        landmarks=landmarks,
    )


def _make_portrait_photos(library: Path) -> None:
    """A repo-beli műszaki próbaportréból három helyi tesztfotót készít."""
    source = Path(__file__).resolve().parents[2] / "fixtures" / "face_type_a_name_reference_en38.png"
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    assert image is not None, f"A próbaportré nem olvasható: {source}"
    portrait = image[138:572, 96:444]
    assert portrait.size > 0
    variants = (
        portrait,
        cv2.flip(portrait, 1),
        cv2.convertScaleAbs(portrait, alpha=0.92, beta=9),
    )
    for name, variant in zip(("a.jpg", "b.jpg", "c.jpg"), variants, strict=True):
        assert cv2.imwrite(str(library / name), variant)


def _seed_six_faces(db_path: Path) -> None:
    with open_index(db_path) as conn:
        photos = all_photos(conn)
        assert len(photos) == 3
        boxes = (
            ((18, 18, 270, 300), (72, 40, 330, 370)),
            ((16, 20, 264, 310), (68, 42, 328, 372)),
            ((20, 16, 268, 302), (70, 45, 326, 368)),
        )
        for photo, photo_boxes in zip(photos, boxes, strict=True):
            replace_faces(
                conn,
                photo.id,
                [_face(*box) for box in photo_boxes],
            )
        ids = [row[0] for row in conn.execute("SELECT id FROM face ORDER BY id")]
        assert len(ids) == 6
        for index, face_id in enumerate(ids):
            embedding = np.zeros(128, dtype=np.float32)
            embedding[index] = 1.0
            store_embedding(conn, face_id, embedding)
        assert group_unnamed_faces(conn) == 6
        conn.commit()


@pytest.fixture
def qml_app_5183(qt_app, tmp_path, monkeypatch, request):
    """Teljes app, valódi portré-bélyegképekkel és izolált felhasználói profillal."""
    isolated_home = tmp_path / "home"
    for variable, folder in (
        ("HOME", isolated_home),
        ("XDG_CONFIG_HOME", isolated_home / ".config"),
        ("XDG_DATA_HOME", isolated_home / ".local" / "share"),
        ("XDG_CACHE_HOME", isolated_home / ".cache"),
        ("XDG_STATE_HOME", isolated_home / ".local" / "state"),
    ):
        folder.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(variable, str(folder))

    builder_path = Path(__file__).with_name("conftest.py")
    spec = importlib.util.spec_from_file_location(
        "picasapy_qml_functional_builder_5183", builder_path
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    warning_guard = qml_warning_guard()
    next(warning_guard)
    try:
        yield from builder._build_qml_app(
            qt_app,
            tmp_path,
            kepeket_keszit=_make_portrait_photos,
            belyegkep_meret=220,
            valodi_belyegkep=True,
            keep_modul=request.module,
        )
    finally:
        try:
            next(warning_guard)
        except StopIteration:
            pass


def _find_item(root, object_name: str):
    found = root.findChild(QQuickItem, object_name)
    if found is not None:
        return found

    def walk(item):
        for child in item.childItems():
            if child.objectName() == object_name:
                return child
            nested = walk(child)
            if nested is not None:
                return nested
        return None

    return walk(root.contentItem())


def _find_object(root, object_name: str):
    return root.findChild(QObject, object_name)


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


def _save_window(window, filename: str) -> Path:
    image = window.grabWindow()
    assert not image.isNull()
    output = Path(__file__).resolve().parents[3] / ".bt" / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    assert image.save(str(output))
    return output


def _text_descendant(item, expected: str):
    if item.property("text") == expected:
        return item
    for child in item.childItems():
        found = _text_descendant(child, expected)
        if found is not None:
            return found
    return None


def test_unnamed_album_welcome_name_and_people_manager_flow(qml_app_5183, qt_app):
    window, _controller, engine = qml_app_5183
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(Path(_controller._db_path))
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 6, 3.0)

    sidebar_label = _find_item(window, "unnamedFacesLabel")
    assert sidebar_label is not None
    assert sidebar_label.property("text") == "Unnamed (6)"

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert unnamed_row is not None
    assert var_feltetelre(qt_app, lambda: unnamed_row.width() > 0, 3.0)
    _click(qt_app, unnamed_row)
    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app,
        lambda: view is not None and view.property("visible") is True,
        3.0,
    )

    welcome = _find_object(window, "unnamedWelcomeDialog")
    assert var_feltetelre(
        qt_app,
        lambda: welcome is not None and welcome.property("visible") is True,
        3.0,
    )
    assert _find_item(window, "unnamedWelcomeTitle").property("text").strip() == (
        "Welcome to the Unnamed people album!"
    )
    assert "A new People album will be created" in _find_item(
        window, "unnamedWelcomeBody"
    ).property("text")
    _save_window(window, "picasapy_5183_welcome.png")
    _click(qt_app, _find_item(window, "unnamedWelcomeCloseButton"))
    assert var_feltetelre(
        qt_app, lambda: welcome.property("visible") is False, 3.0
    )
    assert face_scan.unnamedWelcomeHasBeenShown() is True

    # Ismételt, valódi bal oldali kattintásra az üdvözlés már nem jön elő.
    window.setProperty("unnamedFacesOpen", False)
    qt_app.processEvents()
    _click(qt_app, unnamed_row)
    assert var_feltetelre(
        qt_app,
        lambda: view.property("visible") is True,
        3.0,
    )
    qt_app.processEvents()
    assert welcome.property("visible") is False

    title = _find_item(window, "unnamedAlbumTitle")
    subtitle = _find_item(window, "unnamedAlbumFaceCount")
    icon = _find_item(window, "unnamedTitleIcon")
    expand = _find_item(window, "clusterToggleButton")
    show_ignored = _find_item(window, "unknownfaceheaderpanel/showignored")
    instruction = _find_item(window, "unnamedInstructions")
    assert title is not None and title.property("text") == "Unnamed people"
    assert subtitle is not None and subtitle.property("text") == "6 Face(s)"
    assert icon is not None
    assert expand is not None and show_ignored is not None
    assert expand.property("visible") is True
    assert show_ignored.property("visible") is True
    assert show_ignored.property("enabled") is False
    assert instruction is not None
    assert 'click the "x" to ignore that person.' in instruction.property("text")
    assert _find_item(window, "unnamedNameField").property("visible") is False
    assert _find_item(window, "ignoreFacesButton").property("visible") is False
    assert _find_item(window, "moreSuggestionsButton").property("visible") is False
    assert _find_item(window, "addNameButton").property("visible") is False

    tile_items = [_find_item(window, f"faceTile_{face_id}") for face_id in range(1, 7)]
    name_fields = [
        _find_item(window, f"unnamedFaceNameField_{face_id}")
        for face_id in range(1, 7)
    ]
    assert all(item is not None for item in tile_items)
    assert all(item is not None for item in name_fields)
    assert all(item.property("placeholderText") == "Add a name" for item in name_fields)

    image = _find_item(window, "faceImage_1")
    ignore_x = _find_item(window, "faceIgnoreX_1")
    assert image is not None and ignore_x is not None
    assert abs(image.height() - name_fields[0].width()) <= 3
    assert abs(name_fields[0].width() - image.width() - 26) <= 3
    assert abs(ignore_x.width() - ignore_x.height()) <= 2
    metrics = {
        "window": {"width": window.width(), "height": window.height()},
        "face_tile": {"width": image.width(), "height": image.height()},
        "name_field": {
            "width": name_fields[0].width(),
            "height": name_fields[0].height(),
        },
        "ignore_x": {"width": ignore_x.width(), "height": ignore_x.height()},
        "tile_position": {
            "x": tile_items[0].mapToScene(QPointF(0, 0)).x(),
            "y": tile_items[0].mapToScene(QPointF(0, 0)).y(),
        },
    }
    metrics_path = (
        Path(__file__).resolve().parents[3] / ".bt" / "picasapy_5183_geometry.json"
    )
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _save_window(window, "picasapy_5183_1280x1005.png")

    name_field = name_fields[0]
    _click(qt_app, name_field)
    for character in "Teszt Elek":
        QTest.keyEvent(QTest.KeyAction.Click, name_field.window(), ord(character))
    qt_app.processEvents()
    assert name_field.property("text") == "Teszt Elek"
    QTest.keyClick(name_field.window(), Qt.Key.Key_Return)
    qt_app.processEvents()

    people_dialog = _find_object(window, "peopleManagerDialog")
    assert var_feltetelre(
        qt_app,
        lambda: people_dialog is not None and people_dialog.property("visible") is True,
        3.0,
    )
    search_field = _find_item(window, "peopleManagerSearchField")
    assert search_field is not None
    assert search_field.property("text") == "Teszt Elek"
    assert people_dialog.property("title") == "People"
    for object_name in (
        "peopleManagerDeleteButton",
        "peopleManagerNewButton",
        "peopleManagerNameField",
        "peopleManagerEmailField",
        "peopleManagerSyncCheck",
        "peopleManagerRevertButton",
        "peopleManagerOnlineButton",
        "peopleManagerRefreshButton",
        "peopleManagerOkButton",
        "peopleManagerCancelButton",
    ):
        assert _find_item(window, object_name) is not None
    _save_window(window, "picasapy_5183_people_search.png")

    new_person_button = _find_item(window, "peopleManagerNewButton")
    _click(qt_app, new_person_button)
    name_in_manager = _find_item(window, "peopleManagerNameField")
    assert var_feltetelre(
        qt_app,
        lambda: name_in_manager.property("text") == "Teszt Elek",
        3.0,
    )
    assert search_field.property("text") == "Teszt Elek"
    photo_count = _find_item(window, "peopleManagerPhotoCount")
    assert photo_count is not None
    assert photo_count.property("text") == "0 Photos in Picasa"
    contact_id = _find_item(window, "peopleManagerContactId")
    assert contact_id is not None
    assert contact_id.property("visible") is False
    _save_window(window, "picasapy_5183_people_new_person.png")

    _click(qt_app, _find_item(window, "peopleManagerOkButton"))
    assert var_feltetelre(
        qt_app,
        lambda: people_dialog.property("visible") is False
        and face_scan.unnamedCount == 5
        and _find_item(window, "personItem_Teszt Elek") is not None,
        3.0,
    )
    assert _find_item(window, "unnamedFacesLabel").property("text") == "Unnamed (5)"
    person_row = _find_item(window, "personItem_Teszt Elek")
    assert _text_descendant(person_row, "Teszt Elek (1)") is not None

    with open_index(Path(_controller._db_path)) as conn:
        photos = all_photos(conn)
    assert photos
    ini_paths = {
        Path(photo.folder_path) / ".picasa.ini" for photo in photos
    }
    ini_documents = [(path, load_document(path)) for path in ini_paths]
    contact = next(
        entry
        for _path, document in ini_documents
        for entry in contacts_of(document)
        if entry.name == "Teszt Elek"
    )
    assert len(contact.person_id) == 16
    assert contact.email == contact.gaia_id == ""
    assert any(
        face.contact_id == contact.person_id
        for photo in photos
        for path, document in ini_documents
        if path.parent == Path(photo.folder_path)
        for face in parse_faces(document.section(photo.name).get("faces"))
    )
    _save_window(window, "picasapy_5183_after_ok.png")

    _click(qt_app, person_row)
    assert var_feltetelre(
        qt_app,
        lambda: window.property("personAlbumName") == "Teszt Elek",
        3.0,
    )
    _save_window(window, "picasapy_5183_person_album.png")


@pytest.mark.parametrize("height_offset", _WINDOW_HEIGHT_OFFSETS)
def test_unnamed_album_layout_and_real_sidebar_click_at_adjacent_heights(
    qml_app_5183, qt_app, height_offset
):
    window, controller, engine = qml_app_5183
    window.setWidth(1280)
    window.setHeight(1005 + height_offset)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(Path(controller._db_path))
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 6, 3.0)
    folder_pane = _find_item(window, "folderPane")
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert var_feltetelre(qt_app, lambda: unnamed_row.width() > 0, 3.0)
    _click(qt_app, unnamed_row)

    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app,
        lambda: view is not None and view.property("visible") is True,
        3.0,
    )
    welcome_close = _find_item(window, "unnamedWelcomeCloseButton")
    assert var_feltetelre(
        qt_app,
        lambda: welcome_close is not None and welcome_close.width() > 0,
        3.0,
    )
    _click(qt_app, welcome_close)

    tile_items = [_find_item(window, f"faceTile_{face_id}") for face_id in range(1, 7)]
    name_fields = [
        _find_item(window, f"unnamedFaceNameField_{face_id}")
        for face_id in range(1, 7)
    ]
    assert all(item is not None for item in tile_items)
    assert all(item is not None for item in name_fields)
    image = _find_item(window, "faceImage_1")
    ignore_x = _find_item(window, "faceIgnoreX_1")
    assert image is not None and ignore_x is not None
    assert image.height() > image.width()
    assert name_fields[0].width() > image.width()
    assert abs(ignore_x.width() - ignore_x.height()) <= 2
    first_row_y = [item.mapToScene(QPointF(0, 0)).y() for item in tile_items[:5]]
    assert max(first_row_y) - min(first_row_y) <= 3
    sixth_y = tile_items[5].mapToScene(QPointF(0, 0)).y()
    assert sixth_y > first_row_y[0]

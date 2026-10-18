"""A Név nélküliek kibontott és Mellőzött nézetének Picasa-elrendezése (#5324)."""

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
from picasapy.index import all_photos, group_unnamed_faces, open_index, replace_faces, store_embedding
from support.fixture_guards import qml_warning_guard
from tests.support.varakozas import var_feltetelre


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
            right_eye=(center_x - 20, center_y - 20),
            left_eye=(center_x + 20, center_y - 20),
            nose=(center_x, center_y),
            mouth_right=(center_x - 12, center_y + 24),
            mouth_left=(center_x + 12, center_y + 24),
        ),
    )


def _make_photos(library: Path) -> None:
    source = Path(__file__).resolve().parents[2] / "fixtures" / "face_type_a_name_reference_en38.png"
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    assert image is not None, f"A próbaportré nem olvasható: {source}"
    portrait = image[138:572, 96:444]
    variants = (portrait, cv2.flip(portrait, 1), cv2.convertScaleAbs(portrait, alpha=0.92, beta=9))
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
            replace_faces(conn, photo.id, [_face(*box) for box in photo_boxes])
        ids = [row[0] for row in conn.execute("SELECT id FROM face ORDER BY id")]
        assert len(ids) == 6
        for index, face_id in enumerate(ids):
            embedding = np.zeros(128, dtype=np.float32)
            embedding[index] = 1.0
            store_embedding(conn, face_id, embedding)
        assert group_unnamed_faces(conn) == 6
        conn.commit()


@pytest.fixture
def qml_app_5324(qt_app, tmp_path, monkeypatch, request):
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

    spec = importlib.util.spec_from_file_location(
        "picasapy_qml_functional_builder_5324", Path(__file__).with_name("conftest.py")
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    guard = qml_warning_guard()
    next(guard)
    try:
        yield from builder._build_qml_app(
            qt_app,
            tmp_path,
            kepeket_keszit=_make_photos,
            belyegkep_meret=220,
            valodi_belyegkep=True,
            keep_modul=request.module,
        )
    finally:
        try:
            next(guard)
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


def _all_items(root):
    def walk(item):
        for child in item.childItems():
            yield child
            yield from walk(child)

    return list(walk(root.contentItem()))


def _click(window, qt_app, item) -> None:
    assert item is not None, "A kattintandó felületi elem hiányzik."
    assert item.property("enabled") is not False
    assert item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
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


def _geometry(root, face_ids):
    return {
        face_id: {
            "x": _find_item(root, f"faceImage_{face_id}").mapToScene(QPointF(0, 0)).x(),
            "y": _find_item(root, f"faceImage_{face_id}").mapToScene(QPointF(0, 0)).y(),
            "width": _find_item(root, f"faceImage_{face_id}").width(),
            "height": _find_item(root, f"faceImage_{face_id}").height(),
        }
        for face_id in face_ids
    }


def _face_state(db_path: Path, face_id: int) -> str | None:
    with open_index(db_path) as conn:
        row = conn.execute("SELECT state FROM face WHERE id = ?", (face_id,)).fetchone()
    return row[0] if row else None


def _dialog_button(window, qt_app, text):
    assert var_feltetelre(
        qt_app,
        lambda: any(
            item.property("text") == text
            and item.isVisible()
            and item.width() > 0
            and item.metaObject().indexOfSignal("clicked()") >= 0
            for item in _all_items(window)
        ),
        3.0,
    ), f"A(z) {text!r} gomb nem jelent meg."
    return next(
        item
        for item in _all_items(window)
        if item.property("text") == text
        and item.isVisible()
        and item.width() > 0
        and item.metaObject().indexOfSignal("clicked()") >= 0
    )


def test_a_kibontott_es_mellozott_nezet_a_referenciageometriat_hasznalja(
    qml_app_5324, qt_app
):
    window, controller, engine = qml_app_5324
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(Path(controller._db_path))
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 6, 3.0)

    folder_pane = _find_item(window, "folderPane")
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert var_feltetelre(qt_app, lambda: unnamed_row.width() > 0, 3.0)
    _click(window, qt_app, unnamed_row)
    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(qt_app, lambda: view.property("visible") is True, 3.0)

    welcome = window.findChild(QObject, "unnamedWelcomeDialog")
    assert var_feltetelre(qt_app, lambda: welcome.property("visible") is True, 3.0)
    _click(window, qt_app, _find_item(window, "unnamedWelcomeCloseButton"))
    assert var_feltetelre(qt_app, lambda: welcome.property("visible") is False, 3.0)
    assert var_feltetelre(
        qt_app,
        lambda: all(
            (image := _find_item(window, f"faceImage_{face_id}")) is not None
            and image.property("paintedWidth") > 0
            for face_id in range(1, 7)
        ),
        5.0,
    )

    # Az alapnézet mérete és 5+1-es sorosztása változatlan: ez a
    # j1_csoportositott.png referencia geometriai regresszió-ellenőrzése.
    grouped = _geometry(window, range(1, 7))
    for offset in (-5, 0, 5):
        window.setHeight(1005 + offset)
        grouped = _geometry(window, range(1, 7))
        assert all(abs(grouped[i]["width"] - 146) <= 3 for i in grouped)
        assert all(abs(grouped[i]["height"] - 172) <= 3 for i in grouped)
        assert len({round(grouped[i]["y"]) for i in range(1, 6)}) == 1
        assert grouped[6]["y"] > grouped[1]["y"]
    window.setHeight(1005)
    _save_window(window, "kep_5324_csoportositott.png")

    _click(window, qt_app, _find_item(window, "clusterToggleButton"))
    assert var_feltetelre(qt_app, lambda: view.property("grouped") is False, 3.0)
    header_name_field = _find_item(window, "unnamedNameField")
    ignore_button = _find_item(window, "ignoreFacesButton")
    assert header_name_field is not None
    assert ignore_button is not None
    assert abs(header_name_field.width() - 162) <= 3
    assert abs(header_name_field.height() - 20) <= 3
    header_field_x = header_name_field.mapToScene(QPointF(0, 0)).x()
    ignore_button_x = ignore_button.mapToScene(QPointF(0, 0)).x()
    assert abs(ignore_button_x - header_field_x - header_name_field.width() - 6) <= 3
    expanded = _geometry(window, range(1, 7))
    for offset in (-5, 0, 5):
        window.setHeight(1005 + offset)
        assert var_feltetelre(
            qt_app,
            lambda: all(
                (image := _find_item(window, f"faceImage_{i}")) is not None
                and image.property("paintedWidth") > 0
                for i in range(1, 7)
            ),
            5.0,
        )
        expanded = _geometry(window, range(1, 7))
        assert all(abs(expanded[i]["width"] - 120) <= 3 for i in expanded)
        assert all(abs(expanded[i]["height"] - 145) <= 3 for i in expanded)
        assert max(expanded[i]["y"] for i in expanded) - min(expanded[i]["y"] for i in expanded) <= 3
        assert len({round(expanded[i]["y"]) for i in expanded}) == 1
        assert sorted(expanded[i]["x"] for i in expanded) == [expanded[i]["x"] for i in range(1, 7)]
        assert all(abs(expanded[i + 1]["x"] - expanded[i]["x"] - 162) <= 3 for i in range(1, 6))
    window.setHeight(1005)
    _save_window(window, "kep_5324_kibontott.png")

    window.setHeight(1005)
    _click(window, qt_app, _find_item(window, "clusterToggleButton"))
    view = _find_item(window, "unnamedFacesView")
    _click(window, qt_app, _find_item(window, "faceIgnoreX_1"))
    dialog = window.findChild(QObject, "ignoreFacesDialog")
    assert var_feltetelre(qt_app, lambda: dialog is not None and dialog.property("visible") is True, 3.0)
    _click(window, qt_app, _dialog_button(window, qt_app, "Ignore Person"))
    assert var_feltetelre(qt_app, lambda: face_scan.ignoredCount() == 1, 5.0)

    _click(window, qt_app, _find_item(window, "unknownfaceheaderpanel/showignored"))
    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(qt_app, lambda: view.property("ignoredMode") is True, 3.0)
    title = _find_item(window, "unnamedAlbumTitle")
    count = _find_item(window, "unnamedAlbumFaceCount")
    back = _find_item(window, "unknownfaceheaderpanel/showunknown")
    expand = _find_item(window, "clusterToggleButton")
    name_field = _find_item(window, "ignoredFaceNameField_1")
    stop_ignoring = _find_item(window, "unignoreFacesButton")
    assert title is not None and title.property("text") == "Ignored people"
    assert count is not None and count.property("visible") is True
    assert count.property("text") == "1 Face(s)"
    assert back is not None and back.property("visible") is True
    assert expand is not None and expand.property("visible") is True
    assert name_field is not None and name_field.property("visible") is True
    assert name_field.property("placeholderText") == "Add a name"
    assert stop_ignoring is not None and stop_ignoring.property("visible") is False
    ignored_image = _find_item(window, "ignoredFaceImage_1")
    assert ignored_image is not None
    assert var_feltetelre(qt_app, lambda: ignored_image.property("paintedWidth") > 0, 5.0)
    icon = _find_item(window, "unnamedTitleIcon")
    instruction = _find_item(window, "unnamedInstructions")
    header = _find_item(window, "unknownFaceViewHeader")
    assert icon is not None and instruction is not None and header is not None
    for offset in (-5, 0, 5):
        window.setHeight(1005 + offset)
        assert abs(ignored_image.width() - 146) <= 3
        assert abs(ignored_image.height() - 172) <= 3
        assert abs(name_field.width() - 172) <= 3
        assert abs(name_field.height() - 20) <= 3
        tile_y = ignored_image.mapToScene(QPointF(0, 0)).y()
        field_y = name_field.mapToScene(QPointF(0, 0)).y()
        assert abs(field_y - tile_y - ignored_image.height() - 2) <= 3
        icon_x = icon.mapToScene(QPointF(0, 0)).x()
        count_x = count.mapToScene(QPointF(0, 0)).x()
        title_x = title.mapToScene(QPointF(0, 0)).x()
        instruction_x = instruction.mapToScene(QPointF(0, 0)).x()
        assert abs(icon_x - count_x) <= 2
        assert abs(title_x - icon_x - 40) <= 3
        assert abs(instruction_x - icon_x - 12) <= 3
        back_y = back.mapToScene(QPointF(0, 0)).y()
        expand_y = expand.mapToScene(QPointF(0, 0)).y()
        assert abs(back_y - expand_y) <= 2
        assert instruction.mapToScene(QPointF(0, 0)).y() >= header.mapToScene(QPointF(0, header.height())).y()
    window.setHeight(1005)
    _save_window(window, "kep_5324_mellozott.png")

    sent = []
    view.nameSubmitted.connect(lambda face_id, name: sent.append((face_id, name)))
    _click(window, qt_app, name_field)
    for character in "Teszt Elek":
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(character))
    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()
    assert sent == [(1, "Teszt Elek")]
    people_dialog = window.findChild(QObject, "peopleManagerDialog")
    assert var_feltetelre(
        qt_app,
        lambda: people_dialog is not None and people_dialog.property("visible") is True,
        3.0,
    )
    assert _find_item(window, "peopleManagerSearchField").property("text") == "Teszt Elek"
    _click(window, qt_app, _find_item(window, "peopleManagerNewButton"))
    assert _find_item(window, "peopleManagerNameField").property("text") == "Teszt Elek"
    _click(window, qt_app, _find_item(window, "peopleManagerOkButton"))
    assert var_feltetelre(
        qt_app,
        lambda: _face_state(Path(controller._db_path), 1) == "named",
        5.0,
    ), "A mellőzött arc névadása nem ért el a meglévő `nameSubmitted` út végéig."
    metrics_path = Path(__file__).resolve().parents[3] / ".bt" / "metrics_5324.json"
    metrics_path.write_text(
        json.dumps(
            {
                "grouped": grouped,
                "expanded": expanded,
                "expanded_header_name_field": {
                    "width": header_name_field.width(),
                    "height": header_name_field.height(),
                    "x": header_name_field.mapToScene(QPointF(0, 0)).x(),
                    "y": header_name_field.mapToScene(QPointF(0, 0)).y(),
                },
                "ignored": {
                    "image": {
                        "width": ignored_image.width(),
                        "height": ignored_image.height(),
                        "x": ignored_image.mapToScene(QPointF(0, 0)).x(),
                        "y": ignored_image.mapToScene(QPointF(0, 0)).y(),
                    },
                    "name_field": {
                        "width": name_field.width(),
                        "height": name_field.height(),
                        "x": name_field.mapToScene(QPointF(0, 0)).x(),
                        "y": name_field.mapToScene(QPointF(0, 0)).y(),
                    },
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

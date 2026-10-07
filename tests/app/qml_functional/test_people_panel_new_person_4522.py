"""#4522: named face rows and the New Person naming flow."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from picasapy.ini import contacts_of, load_document, parse_faces
from support.qt_wait import varj_feltetelre
from test_people_panel_26 import (
    _child,
    _draw_sample_faces,
    _image_betoltve,
    _named_item,
    _open,
    _select_photos,
)


_CONTACT_ID = "b8e4117cf1d6615b"
_NAME = "ada lovelace"
_EXISTING_NAME = "anna kis"


def _detection(left: float, top: float, right: float, bottom: float):
    return FaceDetection(
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        score=0.99,
        landmarks=FaceLandmarks(
            right_eye=(left + 0.30 * (right - left), top + 0.30 * (bottom - top)),
            left_eye=(left + 0.70 * (right - left), top + 0.30 * (bottom - top)),
            nose=((left + right) / 2, top + 0.55 * (bottom - top)),
            mouth_right=(left + 0.35 * (right - left), top + 0.77 * (bottom - top)),
            mouth_left=(left + 0.65 * (right - left), top + 0.77 * (bottom - top)),
        ),
    )


def _prepare_panel(qml_app_valodi_belyegkep, qt_app, tmp_path, *, named=False):
    from picasapy.app.worker_thread import wait_for_all_background_workers
    from picasapy.ini.rect64 import Rect64, encode_rect64

    window, controller, _engine = qml_app_valodi_belyegkep
    assert wait_for_all_background_workers(30.0)
    library = tmp_path / "kepek"
    photo_path = library / "a.jpg"
    _draw_sample_faces(photo_path)
    if named:
        (library / ".picasa.ini").write_text(
            "[Contacts2]\n"
            f"{_CONTACT_ID}={_EXISTING_NAME};;\n"
            "[a.jpg]\n"
            f"faces=rect64({encode_rect64(Rect64(0.08, 0.12, 0.34, 0.68))}),"
            f"{_CONTACT_ID};\n",
            encoding="utf-8",
        )

    detections = [_detection(150.0, 20.0, 250.0, 140.0)]
    if not named:
        detections.insert(0, _detection(25.0, 12.0, 84.0, 96.0))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = 'a.jpg'"
        ).fetchone()["id"]
        replace_faces(conn, photo_id, detections)
        conn.commit()
        unnamed_ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM face WHERE photo_id = ? ORDER BY rect_left",
                (photo_id,),
            )
        ]
    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    photo_row = controller.photos.rowOfPath(str(photo_path))
    assert photo_row >= 0
    _open(window, qt_app)
    _select_photos(window, controller, qt_app, [photo_path])
    panel = _child(window, "peoplePanel")
    assert varj_feltetelre(qt_app, lambda: panel.width() >= 275, 3.0)
    return window, controller, panel, library, photo_path, photo_row, unnamed_ids


def _click(window, item):
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def _enter_name(window, qt_app, field, name):
    _click(window, field)
    assert varj_feltetelre(qt_app, lambda: bool(field.property("activeFocus")), 3.0)
    for character in name:
        key = Qt.Key.Key_Space if character == " " else Qt.Key(ord(character.upper()))
        modifier = (
            Qt.KeyboardModifier.ShiftModifier
            if character.isupper()
            else Qt.KeyboardModifier.NoModifier
        )
        QTest.keyClick(window, key, modifier)
    assert field.property("text") == name
    QTest.keyClick(window, Qt.Key.Key_Return)


def test_named_row_matches_reference_and_9b_header_at_nearby_heights(
    qml_app_valodi_belyegkep, qt_app, tmp_path
):
    window, _controller, panel, _library, _photo, _photo_row, _unnamed_ids = (
        _prepare_panel(qml_app_valodi_belyegkep, qt_app, tmp_path, named=True)
    )
    window.setHeight(1024)
    assert varj_feltetelre(qt_app, lambda: int(window.height()) == 1024, 3.0)
    original_height = int(window.height())
    shot_dir = Path.cwd() / ".bt" / "4522-shots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    reference_path = Path.cwd() / ".codex-ref-megnevezett.png"
    assert reference_path.is_file()
    reference = QImage(str(reference_path))
    assert not reference.isNull()
    reference.copy(QRect(1006, 137, 270, 75)).save(
        str(shot_dir / "reference-named-row.png")
    )

    for delta in (-5, 0, 5):
        window.setHeight(original_height + delta)
        assert varj_feltetelre(
            qt_app,
            lambda target_height=original_height + delta:
                int(window.height()) == target_height,
            3.0,
        )
        row = _named_item(panel, f"peoplePanelRow_{_EXISTING_NAME}")
        assert row is not None and row.isVisible()
        image = _named_item(panel, f"peoplePanelFaceImage_{_EXISTING_NAME}")
        name = _named_item(panel, f"peoplePanelName_{_EXISTING_NAME}")
        ignore = _named_item(panel, f"peoplePanelIgnoreX_{_EXISTING_NAME}")
        assert image is not None and name is not None and ignore is not None
        assert varj_feltetelre(
            qt_app, lambda current_image=image: _image_betoltve(current_image), 3.0
        )

        # A sor méretét és szélét a tényleges panelgeometriából számoljuk.
        # A referencia kb. 5 px bal és 4 px jobb belső margót mutat.
        assert abs(float(row.property("width")) - (panel.width() - 10)) <= 1
        assert abs(float(row.property("height")) - 75) <= 3
        row_pos = row.mapToItem(panel, QPointF(0, 0))
        assert abs(row_pos.x() - 5) <= 3
        assert abs(panel.width() - row_pos.x() - row.width() - 4) <= 3
        image_pos = image.mapToItem(row, QPointF(0, 0))
        name_pos = name.mapToItem(row, QPointF(0, 0))
        ignore_pos = ignore.mapToItem(row, QPointF(0, 0))
        assert abs(image_pos.x() - 7) <= 2
        assert abs(image_pos.y() - (row.height() - image.height()) / 2) <= 2
        assert abs(name_pos.x() - (image_pos.x() + image.width() + 16)) <= 2
        assert abs(name_pos.y() - 7) <= 2
        assert ignore.isVisible()
        assert abs(ignore_pos.x() - (image_pos.x() + image.width() - ignore.width())) <= 2
        assert abs(ignore_pos.y() - image_pos.y()) <= 2
        assert QColor(name.property("color")).name() == "#ffffff"
        assert _child(panel, "peoplePanelHeader").property("text") == "In this photo:"

        if delta == 0:
            rendered = window.grabWindow()
            assert not rendered.isNull()
            rendered.save(str(shot_dir / "named-row-window.png"))
            origin = row.mapToScene(QPointF(0, 0))
            actual_crop = rendered.copy(
                QRect(
                    round(origin.x()),
                    round(origin.y()),
                    round(row.width()),
                    round(row.height()),
                )
            )
            reference_crop = reference.copy(QRect(1006, 137, 270, 75))
            side_by_side = QImage(
                reference_crop.width() + actual_crop.width(),
                max(reference_crop.height(), actual_crop.height()),
                QImage.Format.Format_ARGB32,
            )
            side_by_side.fill(Qt.GlobalColor.white)
            painter = QPainter(side_by_side)
            painter.drawImage(0, 0, reference_crop)
            painter.drawImage(reference_crop.width(), 0, actual_crop)
            painter.end()
            assert side_by_side.save(str(shot_dir / "named-row-comparison.png"))

    source = (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/qml/PicasaPy/PeoplePanelRow.qml"
    ).read_text(encoding="utf-8")
    assert re.search(r"font\.pixelSize\s*:\s*16\b", source)


def test_enter_routes_existing_names_directly_and_new_names_through_people_dialog(
    qml_app_valodi_belyegkep, qt_app, tmp_path
):
    window, controller, panel, library, photo_path, _photo_row, unnamed_ids = (
        _prepare_panel(qml_app_valodi_belyegkep, qt_app, tmp_path)
    )
    assert len(unnamed_ids) == 2
    (library / ".picasa.ini").write_text(
        "[Contacts2]\n"
        f"{_CONTACT_ID}={_EXISTING_NAME};;\n",
        encoding="utf-8",
    )

    existing_field = _named_item(panel, f"peoplePanelAddName_{unnamed_ids[0]}")
    assert existing_field is not None and existing_field.isVisible()
    _enter_name(window, qt_app, existing_field, _EXISTING_NAME)
    assert varj_feltetelre(
        qt_app,
        lambda: _named_item(panel, f"peoplePanelRow_{_EXISTING_NAME}") is not None,
        3.0,
    )
    loader = window.findChild(QObject, "peoplePanelPeopleManagerLoader")
    assert loader is None or not loader.property("active")

    new_field = _named_item(panel, f"peoplePanelAddName_{unnamed_ids[1]}")
    assert new_field is not None and new_field.isVisible()
    _enter_name(window, qt_app, new_field, _NAME)
    assert varj_feltetelre(
        qt_app,
        lambda: (
            (dialog := window.findChild(QObject, "peopleManagerDialog")) is not None
            and bool(dialog.property("visible"))
        ),
        3.0,
    )
    dialog = window.findChild(QObject, "peopleManagerDialog")
    search = window.findChild(QObject, "peopleManagerSearchField")
    new_button = window.findChild(QObject, "peopleManagerNewButton")
    assert dialog is not None and search is not None and new_button is not None
    assert search.property("text") == _NAME
    ini_path = library / ".picasa.ini"
    document = load_document(ini_path)
    contacts = {contact.person_id: contact.name for contact in contacts_of(document)}
    assert all(contact.name != _NAME for contact in contacts_of(document))
    assert all(
        contacts.get(face.contact_id, "") != _NAME
        for face in parse_faces(document.section(photo_path.name).get("faces") or "")
    )

    _click(window, new_button)
    name_field = window.findChild(QObject, "peopleManagerNameField")
    assert name_field is not None
    assert name_field.property("text") == _NAME
    assert all(
        contact.name != _NAME
        for contact in contacts_of(load_document(ini_path))
    )

    ok_button = window.findChild(QObject, "peopleManagerOkButton")
    assert ok_button is not None and ok_button.isEnabled()
    _click(window, ok_button)
    assert varj_feltetelre(
        qt_app,
        lambda: not bool(dialog.property("visible"))
        and _named_item(panel, f"peoplePanelRow_{_NAME}") is not None,
        3.0,
    )

    saved = load_document(ini_path)
    contacts = {contact.person_id: contact.name for contact in contacts_of(saved)}
    faces = parse_faces(saved.section(photo_path.name).get("faces") or "")
    assigned = [face for face in faces if face.contact_id in contacts]
    assert any(contacts[face.contact_id] == _NAME for face in assigned)
    assert re.fullmatch(r"[0-9a-f]{16}", next(
        face.contact_id for face in assigned if contacts[face.contact_id] == _NAME
    ))
    assert any(
        contact["name"] == _NAME for contact in controller.peopleManagerContacts()
    )

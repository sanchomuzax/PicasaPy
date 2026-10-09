"""#4572: a nézőben kattintással megnevezhető az index névtelen arca."""

from __future__ import annotations

import time

from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
import pytest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from support.jpeg_factory import make_jpeg

_REFERENCE = Path(__file__).parents[2] / "fixtures" / "face_type_a_name_reference_en38.png"


def _reference_face_rect():
    """A kivágott #38 képen látható keret normált koordinátái.

    A keretet a szövegmentes felső és oldalsó vonalakból mértük; a betűk
    képpontjai és mérete nem részei az összevetésnek.
    """
    reference = QImage(str(_REFERENCE))
    assert not reference.isNull()
    assert (reference.width(), reference.height()) == (538, 807)
    frame_left, frame_top, frame_right, frame_bottom = 85, 128, 455, 572
    return (
        frame_left / reference.width(),
        frame_top / reference.height(),
        frame_right / reference.width(),
        frame_bottom / reference.height(),
    )


def _wait_until(qt_app, predicate, *, timeout_ms=3000):
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(predicate())


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_clicking_detected_unnamed_face_opens_name_field_and_saves(
    qml_app, qt_app, tmp_path, height_delta
):
    """A kattintás megmutatja a keretet; a név az ini-be és az indexbe kerül."""
    db = tmp_path / "index.db"
    photo_path = tmp_path / "kepek" / "a.jpg"
    make_jpeg(photo_path, size=(240, 360))
    left, top, right, bottom = _reference_face_rect()
    face_left, face_top = round(left * 240), round(top * 360)
    face_right, face_bottom = round(right * 240), round(bottom * 360)
    with open_index(db) as conn:
        sync_tree(conn, photo_path.parent, incremental=False)
        photo = conn.execute("SELECT id FROM photos WHERE name = 'a.jpg'").fetchone()
        assert photo is not None
        replace_faces(
            conn,
            int(photo["id"]),
            [
                FaceDetection(
                    left=face_left,
                    top=face_top,
                    right=face_right,
                    bottom=face_bottom,
                    score=0.99,
                    landmarks=FaceLandmarks(
                        right_eye=(face_left + 45, face_top + 43),
                        left_eye=(face_left + 100, face_top + 43),
                        nose=(face_left + 73, face_top + 93),
                        mouth_right=(face_left + 50, face_top + 126),
                        mouth_left=(face_left + 96, face_top + 126),
                    ),
                )
            ],
        )
        conn.commit()

    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    controller._reload()
    qt_app.processEvents()
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    overlay = window.findChild(QObject, "facesOverlay")
    assert overlay is not None

    # A referencia arányait használó arcon a valódi overlay-geometriából
    # számoljuk a kattintást.
    target = overlay.mapToItem(
        window.contentItem(),
        QPointF(float(overlay.property("width")) * (left + right) / 2,
                float(overlay.property("height")) * (top + bottom) / 2),
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(target.x()), round(target.y())),
    )

    editor = window.findChild(QObject, "faceNameEditor")
    assert _wait_until(qt_app, lambda: editor.property("visible")), (
        "a felismert névtelen arc kattintására nem nyílt meg a névmező"
    )
    field = window.findChild(QObject, "faceNameField")
    assert field is not None
    assert field.property("placeholderText") == "Type a name"
    overlay_qml = (
        Path(__file__).parents[3]
        / "src/picasapy/app/qml/PicasaPy/FacesOverlay.qml"
    ).read_text(encoding="utf-8")
    assert "font.pixelSize: Theme.fontSize - 1" in overlay_qml

    assert window.findChild(QObject, "faceNameOk") is None
    assert window.findChild(QObject, "faceNameCancel") is None
    assert overlay.property("selectedDetectedFaceId") > 0

    # A referencia 538 px-es képszélességén a keret 370 px, az alatta
    # középre tett névsáv 204 × 20 px. A várt QML-geometriát mindig a tényleges
    # overlay-méretből számoljuk; ±3 px a platformok ablak- és betűeltérése.
    scale = float(overlay.property("width")) / 538
    editor_x = float(editor.property("x"))
    editor_y = float(editor.property("y"))
    editor_width = float(editor.property("width"))
    editor_height = float(editor.property("height"))
    expected_editor_width = 204 * scale
    expected_editor_height = 20 * scale
    expected_editor_x = (left + right) * float(overlay.property("width")) / 2
    expected_editor_x -= expected_editor_width / 2
    expected_editor_y = bottom * float(overlay.property("height"))
    assert abs(editor_x - expected_editor_x) <= 3
    assert abs(editor_y - expected_editor_y) <= 3
    assert abs(editor_width - expected_editor_width) <= 3
    assert abs(editor_height - expected_editor_height) <= 3

    # A referencia szövegmentes felső élén #d0d1d0 színű, egypixeles keret
    # látszik. A QML-forrásőr védi a színt/vonalvastagságot, a renderelt kép
    # pedig a tényleges képpontot ellenőrzi.
    rendered = window.grabWindow()
    assert not rendered.isNull()
    output = tmp_path / "viewer-unnamed-face-4572.png"
    assert rendered.save(str(output))
    origin = overlay.mapToItem(window.contentItem(), QPointF(0, 0))
    overlay_width = float(overlay.property("width"))
    overlay_height = float(overlay.property("height"))
    frame_left = origin.x() + overlay_width * left
    frame_right = origin.x() + overlay_width * right
    frame_top = origin.y() + overlay_height * top
    frame_middle_y = origin.y() + overlay_height * (top + bottom) / 2

    def has_reference_gray(center_x, center_y):
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                color = rendered.pixelColor(round(center_x) + dx, round(center_y) + dy)
                if (abs(color.red() - 208) <= 24
                        and abs(color.green() - 209) <= 24
                        and abs(color.blue() - 208) <= 24):
                    return True
        return False

    assert has_reference_gray((frame_left + frame_right) / 2, frame_top), (
        "a kattintott arc felső kerete nem a referencia halványszürke színével látszik"
    )
    assert has_reference_gray(frame_left, frame_middle_y)
    assert has_reference_gray(frame_right, frame_middle_y)
    assert "border.color: \"#d0d1d0\"" in overlay_qml
    assert "border.width: 1" in overlay_qml

    # Az Escape elveti a névadást; a következő kattintásra újból megnyílik.
    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert _wait_until(qt_app, lambda: not editor.property("visible"))
    assert not (tmp_path / "kepek" / ".picasa.ini").exists()
    with open_index(db) as conn:
        row = conn.execute("SELECT state FROM face WHERE id = 1").fetchone()
    assert row is not None and row["state"] == "unnamed"

    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(target.x()), round(target.y())),
    )
    assert _wait_until(qt_app, lambda: editor.property("visible"))
    field.setProperty("text", "Ada")
    QTest.keyClick(window, Qt.Key.Key_Return)
    assert _wait_until(qt_app, lambda: not editor.property("visible"))

    ini = tmp_path / "kepek" / ".picasa.ini"
    text = ini.read_text(encoding="utf-8")
    assert "[Contacts2]" in text
    assert "Ada;;" in text
    assert "[a.jpg]" in text and "faces=rect64(" in text
    with open_index(db) as conn:
        row = conn.execute("SELECT state FROM face WHERE id = 1").fetchone()
    assert row is not None and row["state"] == "named"


# rontás-kontroll: a DB-beli arckeretek QML-be kötésének kikapcsolása → 1 failed.

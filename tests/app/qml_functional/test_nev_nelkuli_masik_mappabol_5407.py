"""Másik mappából származó fotó arc-csempéje betölt a Névtelenek nézetben (#5407)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, photos_in_folder, replace_faces, sync_tree
from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


def _find_item(root, name: str):
    def walk(item):
        for child in item.childItems():
            if child.objectName() == name:
                return child
            nested = walk(child)
            if nested is not None:
                return nested
        return None

    return walk(root.contentItem())


def _click(window, qt_app, item) -> None:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _seed_other_folder(db_path: Path, folder: Path) -> int:
    folder.mkdir(parents=True)
    make_jpeg(folder / "outside.jpg", size=(320, 240))
    face = FaceDetection(
        left=50,
        top=40,
        right=270,
        bottom=210,
        score=0.99,
        landmarks=FaceLandmarks(
            right_eye=(110, 90),
            left_eye=(210, 90),
            nose=(160, 125),
            mouth_right=(125, 165),
            mouth_left=(195, 165),
        ),
    )
    with open_index(db_path) as conn:
        sync_tree(conn, folder)
        (photo,) = photos_in_folder(conn, folder)
        replace_faces(conn, photo.id, [face])
        conn.commit()
    return photo.id


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_unnamed_face_image_from_unopened_folder_is_ready_and_drawn(
    qml_app_valodi_belyegkep, qt_app, height_delta, tmp_path
):
    window, controller, engine = qml_app_valodi_belyegkep
    initial_height = int(window.height())
    window.setHeight(initial_height + height_delta)
    assert var_feltetelre(
        qt_app, lambda: int(window.height()) == initial_height + height_delta
    )

    other_folder = tmp_path / "another-folder"
    photo_id = _seed_other_folder(Path(controller._db_path), other_folder)
    provider = controller._provider
    assert provider.photo_record(str(photo_id)) is None, (
        "a próba elrontaná a reprodukciót: a szolgáltató már ismeri "
        "a megnyitott mappán kívüli fotót"
    )

    face_scan = engine.rootContext().contextProperty("faceScanController")
    face_scan.markUnnamedWelcomeShown()
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 1, 5.0)

    folder_pane = _find_item(window, "folderPane")
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert var_feltetelre(qt_app, lambda: unnamed_row.width() > 0, 5.0)
    _click(window, qt_app, unnamed_row)
    unnamed_view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app, lambda: unnamed_view.property("visible") is True, 5.0
    )

    faces = face_scan.unnamedGroups(True, False)[0]["faces"]
    assert len(faces) == 1
    face_image = _find_item(window, f"faceImage_{faces[0]['faceId']}")
    assert face_image is not None
    ready = QQmlExpression(
        engine.rootContext(), face_image, "status === Image.Ready"
    )
    assert var_feltetelre(
        qt_app, lambda: not ready.hasError() and bool(ready.evaluate()), 15.0
    ), f"a másik mappa csempéje nem Ready: {face_image.property('source')}"

    center = face_image.mapToScene(
        QPointF(face_image.width() / 2, face_image.height() / 2)
    )
    dpr = window.devicePixelRatio()

    def tile_pixel():
        rendered = window.grabWindow()
        return rendered.pixelColor(round(center.x() * dpr), round(center.y() * dpr))

    def has_photo_pixels():
        pixel = tile_pixel()
        return pixel.red() > pixel.green() + 40

    assert var_feltetelre(
        qt_app,
        has_photo_pixels,
        5.0,
    ), "az Image.Ready csempe képpontja helyettesítő kép maradt"
    assert window.grabWindow().save(str(tmp_path / "nevtelen_masik_mappa.png"))

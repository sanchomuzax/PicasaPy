"""Az Emberek-panel fejlécjelzője névadáskor pillanatkép (#4812)."""

from __future__ import annotations

import os

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, replace_faces, sync_tree
from picasapy.index.faces_detected import set_suggested_name
from support.qt_wait import varj_feltetelre
from test_people_panel_new_person_4522 import (
    _CONTACT_ID,
    _EXISTING_NAME,
    _child,
    _detection,
    _draw_sample_faces,
    _click as _click_item,
    _enter_name,
    _named_item,
    _open,
    _prepare_panel as _prepare_one_photo_panel,
    _select_photos,
)


def _pump_events(qt_app, ms=100):
    """A Qt.callLater-es frissítések lefutnak, mielőtt „nem változik" állítunk."""
    QTest.qWait(ms)
    qt_app.processEvents()


def _prepare_two_photos(qml_app_valodi_belyegkep, qt_app, tmp_path):
    from picasapy.app.worker_thread import wait_for_all_background_workers

    window, controller, _engine = qml_app_valodi_belyegkep
    assert wait_for_all_background_workers(30.0)
    library = tmp_path / "kepek"
    first_path = library / "a.jpg"
    second_path = library / "b.jpg"
    _draw_sample_faces(first_path)
    _draw_sample_faces(second_path)
    (library / ".picasa.ini").write_text(
        "[Contacts2]\n"
        f"{_CONTACT_ID}={_EXISTING_NAME};;\n",
        encoding="utf-8",
    )

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        first_id = conn.execute(
            "SELECT id FROM photos WHERE name = 'a.jpg'"
        ).fetchone()["id"]
        replace_faces(
            conn,
            first_id,
            [
                _detection(25.0, 12.0, 84.0, 96.0),
                _detection(150.0, 20.0, 250.0, 140.0),
            ],
        )
        conn.commit()
        unnamed_ids = [
            row["id"]
            for row in conn.execute(
                "SELECT id FROM face WHERE photo_id = ? ORDER BY rect_left",
                (first_id,),
            )
        ]

    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    first_row = controller.photos.rowOfPath(str(first_path))
    second_row = controller.photos.rowOfPath(str(second_path))
    assert first_row >= 0 and second_row >= 0
    _open(window, qt_app)
    _select_photos(window, controller, qt_app, [first_path])
    panel = _child(window, "peoplePanel")
    assert varj_feltetelre(qt_app, lambda: panel.width() >= 275, 3.0)
    return window, controller, panel, first_path, second_path, unnamed_ids


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_naming_keeps_header_until_selection_refresh_and_then_updates(
    qml_app_valodi_belyegkep, qt_app, tmp_path, height_delta
):
    window, controller, panel, first_path, second_path, unnamed_ids = (
        _prepare_two_photos(qml_app_valodi_belyegkep, qt_app, tmp_path)
    )
    target_height = int(window.height()) + height_delta
    window.setHeight(target_height)
    assert varj_feltetelre(
        qt_app, lambda: int(window.height()) == target_height, 3.0
    )
    assert len(unnamed_ids) == 2
    header = _child(panel, "peoplePanelHeader")
    assert header.property("text") == "Who is in these photos?"

    field = _named_item(panel, f"peoplePanelAddName_{unnamed_ids[0]}")
    assert field is not None and field.isVisible()
    _enter_name(window, qt_app, field, _EXISTING_NAME)
    assert varj_feltetelre(
        qt_app,
        lambda: _named_item(panel, f"peoplePanelRow_{_EXISTING_NAME}") is not None,
        3.0,
    )
    _pump_events(qt_app)
    assert header.property("text") == "Who is in these photos?"

    capture_path = os.environ.get("PICASAPY_CAPTURE_4812")
    if capture_path:
        screenshot = window.grabWindow()
        assert not screenshot.isNull()
        assert screenshot.save(capture_path, "PNG")

    _select_photos(window, controller, qt_app, [second_path])
    assert varj_feltetelre(
        qt_app,
        lambda: header.property("text") == "Who is in these photos?",
        3.0,
    )
    _select_photos(window, controller, qt_app, [first_path])
    assert varj_feltetelre(
        qt_app,
        lambda: header.property("text") == "In this photo:",
        3.0,
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_manually_added_named_face_refreshes_editor_header_immediately(
    qml_app_valodi_belyegkep, qt_app, tmp_path, height_delta
):
    window, controller, _engine = qml_app_valodi_belyegkep
    from picasapy.app.worker_thread import wait_for_all_background_workers

    assert wait_for_all_background_workers(30.0)
    library = tmp_path / "kepek"
    photo_path = library / "a.jpg"
    (library / ".picasa.ini").write_text(
        "[Contacts2]\n"
        f"{_CONTACT_ID}={_EXISTING_NAME};;\n",
        encoding="utf-8",
    )
    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    target_height = int(window.height()) + height_delta
    window.setHeight(target_height)
    assert varj_feltetelre(
        qt_app, lambda: int(window.height()) == target_height, 3.0
    )
    _open(window, qt_app)
    _select_photos(window, controller, qt_app, [photo_path])

    manual_button = _child(window, "peoplePanelManualAddButton")
    assert varj_feltetelre(
        qt_app,
        lambda: manual_button.isVisible() and manual_button.isEnabled(),
        3.0,
    )
    _click_item(window, manual_button)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    assert varj_feltetelre(
        qt_app,
        lambda: window.property("viewerOpen") is True
        and viewer.property("facesEditMode") is True,
        3.0,
    )
    panel = window.findChild(QObject, "viewerPeoplePanel")
    overlay = window.findChild(QQuickItem, "facesOverlay")
    create_area = window.findChild(QQuickItem, "facesCreateArea")
    assert panel is not None and overlay is not None and create_area is not None
    assert varj_feltetelre(
        qt_app,
        lambda: create_area.isVisible()
        and create_area.width() > 0
        and create_area.height() > 0,
        3.0,
    )

    start = create_area.mapToScene(
        QPointF(create_area.width() * 0.20, create_area.height() * 0.20)
    )
    end = create_area.mapToScene(
        QPointF(create_area.width() * 0.48, create_area.height() * 0.50)
    )
    start_point = QPoint(round(start.x()), round(start.y()))
    end_point = QPoint(round(end.x()), round(end.y()))
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        start_point,
    )
    QTest.mouseMove(window, end_point, 100)
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        end_point,
    )
    draft_name = window.findChild(QQuickItem, "faceDraftAddName")
    assert draft_name is not None
    assert varj_feltetelre(qt_app, lambda: draft_name.isVisible(), 3.0)
    _click_item(window, draft_name)

    field = window.findChild(QQuickItem, "faceNameField")
    assert field is not None
    assert varj_feltetelre(
        qt_app, lambda: field.isVisible() and bool(field.property("activeFocus")),
        3.0,
    )
    _enter_name(window, qt_app, field, _EXISTING_NAME)
    assert varj_feltetelre(
        qt_app,
        lambda: panel.property("headerText") == "In this photo:",
        3.0,
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_accepting_a_face_name_suggestion_in_album_refreshes_header_immediately(
    qml_app_valodi_belyegkep, qt_app, tmp_path, height_delta
):
    window, controller, panel, _library, _photo, _row, face_ids = (
        _prepare_one_photo_panel(qml_app_valodi_belyegkep, qt_app, tmp_path)
    )
    _rejected_id, accepted_id = face_ids
    with open_index(controller._db_path) as conn:
        set_suggested_name(conn, accepted_id, _EXISTING_NAME)
        conn.commit()

    face_scan = window.property("_faceScanController")
    assert face_scan is not None
    face_scan.unnamedCountChanged.emit()
    panel.setProperty("unnamedAlbumMode", True)
    target_height = int(window.height()) + height_delta
    window.setHeight(target_height)
    assert varj_feltetelre(
        qt_app, lambda: int(window.height()) == target_height, 3.0
    )
    qt_app.processEvents()

    header = _child(panel, "peoplePanelHeader")
    assert header.property("text") == "Who is in these photos?"
    suggestion = _named_item(
        panel, f"peoplePanelSuggestionYes_{accepted_id}"
    )
    assert suggestion is not None and suggestion.isVisible()
    _click_item(window, suggestion)
    assert varj_feltetelre(
        qt_app,
        lambda: header.property("text") == "In this photo:",
        3.0,
    )


def test_typed_name_in_unnamed_album_keeps_header_until_selection_refresh(
    qml_app_valodi_belyegkep, qt_app, tmp_path
):
    library = tmp_path / "kepek"
    library.mkdir(exist_ok=True)
    (library / ".picasa.ini").write_text(
        "[Contacts2]\n"
        f"{_CONTACT_ID}={_EXISTING_NAME};;\n",
        encoding="utf-8",
    )
    window, _controller, panel, _library, _photo, _row, face_ids = (
        _prepare_one_photo_panel(qml_app_valodi_belyegkep, qt_app, tmp_path)
    )
    _rejected_id, accepted_id = face_ids
    panel.setProperty("unnamedAlbumMode", True)
    assert varj_feltetelre(
        qt_app, lambda: panel.property("unnamedAlbumMode") is True, 3.0
    )
    _pump_events(qt_app)

    header = _child(panel, "peoplePanelHeader")
    assert header.property("text") == "Who is in these photos?"
    field = _named_item(panel, f"peoplePanelAddName_{accepted_id}")
    assert field is not None and field.isVisible()
    _enter_name(window, qt_app, field, _EXISTING_NAME)
    assert varj_feltetelre(
        qt_app,
        lambda: _named_item(panel, f"peoplePanelAddName_{accepted_id}") is None,
        3.0,
    )
    _pump_events(qt_app)
    assert header.property("text") == "Who is in these photos?"


def test_overlay_naming_of_unnamed_face_keeps_editor_header(
    qml_app_valodi_belyegkep, qt_app, tmp_path
):
    from PySide6.QtCore import QMetaObject, Q_ARG

    window, _controller, panel, _library, _photo, photo_row, _face_ids = (
        _prepare_one_photo_panel(qml_app_valodi_belyegkep, qt_app, tmp_path)
    )
    viewer = window.findChild(QObject, "photoViewer")
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", photo_row)
    qt_app.processEvents()
    QMetaObject.invokeMethod(viewer, "toggleFacesEdit")
    _pump_events(qt_app, 300)
    vpanel = window.findChild(QObject, "viewerPeoplePanel")
    overlay = window.findChild(QQuickItem, "facesOverlay")
    assert varj_feltetelre(qt_app, lambda: len(overlay.property("faces")) == 2, 3.0)
    assert vpanel.property("headerText") == "Who is in these photos?"

    face = overlay.property("faces")[0]
    QMetaObject.invokeMethod(
        overlay, "openEditorForDetected", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", face["left"]), Q_ARG("QVariant", face["top"]),
        Q_ARG("QVariant", face["right"]), Q_ARG("QVariant", face["bottom"]),
        Q_ARG("QVariant", face["faceId"]),
    )
    _pump_events(qt_app)
    field = window.findChild(QObject, "faceNameField")
    field.setProperty("text", _EXISTING_NAME)
    QMetaObject.invokeMethod(overlay, "commitEditor", Qt.ConnectionType.DirectConnection)
    assert varj_feltetelre(
        qt_app,
        lambda: overlay.property("faces")[0]["name"] == _EXISTING_NAME,
        3.0,
    )
    _pump_events(qt_app)
    assert vpanel.property("headerText") == "Who is in these photos?"

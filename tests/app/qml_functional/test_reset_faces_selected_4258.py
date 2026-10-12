"""#4258: a Reset Faces csak a kijelölt képek ini-arcait törli."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.app.faces_helper import FacesHelper
from picasapy.index import all_photos, open_index, sync_tree
from picasapy.ini import load_document
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre
from tests.app.test_face_scan_controller import _FakeDetector, _run


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

    face_scan = _engine.rootContext().contextProperty("faceScanController")
    detector = _FakeDetector()
    face_scan._detector = detector
    faces_helper = FacesHelper()
    assert faces_helper.removeAllFaces(str(first_photo))
    assert faces_helper.removeAllFaces(str(second_photo))
    _run(face_scan.scanFinished, face_scan.scanForFaces)
    assert face_scan.waitForBackgroundWorkers(5.0)
    assert len(detector.calls) == 2
    assert faces_helper.addFace(str(first_photo), 0.1, 0.2, 0.4, 0.6, "Ada")
    assert faces_helper.addFace(str(second_photo), 0.2, 0.3, 0.5, 0.7, "Bela")

    with open_index(tmp_path / "index.db") as conn:
        selected_id = next(
            photo.id for photo in all_photos(conn) if photo.name == "selected.jpg"
        )
        selected_count = conn.execute(
            "SELECT COUNT(*) FROM face WHERE photo_id = ?", (selected_id,)
        ).fetchone()[0]
        assert selected_count == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM face_scan WHERE photo_id = ?", (selected_id,)
        ).fetchone()[0] == 1

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
    assert len(detector.calls) == 2, "a kezdeti keresés nem a várt két fotót vizsgálta"
    _click_menu_item(item, qt_app)
    assert varj_feltetelre(
        qt_app,
        lambda: len(detector.calls) >= 3,
        3.0,
    ), "a helyi menüből resetelt kép nem került vissza a detektorhoz"
    assert face_scan.waitForBackgroundWorkers(5.0)

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

    with open_index(tmp_path / "index.db") as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM face WHERE photo_id = ?", (selected_id,)
        ).fetchone()[0] == 1
        face_state = conn.execute(
            "SELECT state FROM face WHERE photo_id = ?", (selected_id,)
        ).fetchone()[0]
        assert face_state == "unnamed"
    assert first_photo.name in {item["name"] for item in face_scan.unnamedAlbum()}


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_reset_faces_menu_shows_model_help_when_detector_is_unavailable(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, engine = qml_app
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

    selected_photo = library / "album-a" / "selected.jpg"
    selected_row = controller.photos.rowOfPath(str(selected_photo))
    assert selected_row >= 0
    window.setProperty("selectedIndexes", [selected_row])
    window.setProperty("selectedIndex", selected_row)
    engine.rootContext().contextProperty("faceScanController")._detector = (
        _FakeDetector(available=False)
    )

    menu = _open_context_menu(window, qt_app, selected_row)
    item = menu.findChild(QObject, "contextMenuResetFaces")
    assert item is not None
    _click_menu_item(item, qt_app)

    assert varj_feltetelre(
        qt_app,
        lambda: (
            window.findChild(QObject, "faceScanDialog") is not None
            and window.findChild(QObject, "faceScanDialog").property("visible")
        ),
        3.0,
    ), "modellhiánynál nem nyílt meg az érthető útmutatót mutató ablak"
    dialog = window.findChild(QObject, "faceScanDialog")
    reason = dialog.findChild(QObject, "faceScanUnavailableText")
    download = dialog.findChild(QObject, "faceScanDownloadButton")
    assert reason is not None and reason.property("visible") is True
    assert reason.property("text")
    assert download is not None and download.property("visible") is True

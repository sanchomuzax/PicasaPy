"""A könyvtár- és személyalbum bélyegképmérete külön mentődik (#7333)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.app.controller import AppController
from picasapy.index import open_index, sync_tree
from picasapy.ini import parse_document, update_document
from tests.support.varakozas import var_feltetelre

_PERSON_ID = "aaaaaaaaaaaaaaaa"
_FACE_RECT = "1e00280045006e00"
_HEIGHT_OFFSETS = (-5, 0, 5)


def _item(window, object_name: str) -> QQuickItem:
    item = window.findChild(QQuickItem, object_name)
    assert item is not None, f"{object_name} nem található a QML-ben"
    return item


def _wait(qt_app, condition, seconds: float = 10.0) -> bool:
    return var_feltetelre(qt_app, condition, seconds)


def _drag_thumb_slider(window, slider: QQuickItem, target: int) -> None:
    """A tényleges fogantyút húzza a tartomány célértékéhez."""
    handle = slider.property("handle")
    assert isinstance(handle, QQuickItem), "a csúszka fogantyúja hiányzik"
    low = float(slider.property("from"))
    high = float(slider.property("to"))
    fraction = (target - low) / (high - low)
    x = (
        float(slider.property("leftPadding"))
        + fraction * (float(slider.property("availableWidth")) - handle.width())
        + handle.width() / 2
    )
    y = slider.height() / 2
    start = handle.mapToScene(QPointF(handle.width() / 2, handle.height() / 2))
    finish = slider.mapToScene(QPointF(x, y))
    start_point = QPoint(round(start.x()), round(start.y()))
    finish_point = QPoint(round(finish.x()), round(finish.y()))

    QTest.mouseMove(window, start_point)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start_point)
    QTest.mouseMove(window, finish_point, delay=10)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=finish_point)


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_a_konyvtar_es_szemelyalbum_csuszkaerteke_kulon_mentodik_es_visszaall(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    window.show()
    window.setHeight(window.height() + height_offset)
    assert _wait(qt_app, lambda: window.isVisible())

    slider = _item(window, "traySizeSlider")
    assert _wait(qt_app, lambda: slider.isVisible() and slider.width() > 0)
    assert window.property("thumbSize") == 144

    settings = controller._get_settings()
    _drag_thumb_slider(window, slider, 196)
    assert _wait(qt_app, lambda: window.property("thumbSize") > 180)
    library_size = int(window.property("thumbSize"))
    assert settings.value("view/thumbScale", 0, int) == library_size

    photo_path = Path(controller.photos.filePathAt(0))
    update_document(
        photo_path.parent / ".picasa.ini",
        lambda _old: parse_document(
            "[Contacts2]\n"
            f"{_PERSON_ID}=Anna;;\n"
            "[a.jpg]\n"
            f"faces=rect64({_FACE_RECT}),{_PERSON_ID}\n"
        ),
        backup=False,
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, photo_path.parent)
    controller._reload_after_sync()
    controller.showPerson("Anna")
    assert _wait(
        qt_app,
        lambda: window.property("personAlbumName") == "Anna"
        and window.property("thumbSize") == 144,
    )

    _drag_thumb_slider(window, slider, 224)
    assert _wait(qt_app, lambda: window.property("thumbSize") > 210)
    people_size = int(window.property("thumbSize"))
    assert people_size != library_size
    assert settings.value("view/thumbScalePeople", 0, int) == people_size

    controller.clearFilter()
    assert _wait(
        qt_app,
        lambda: window.property("personAlbumName") == ""
        and window.property("thumbSize") == library_size,
    )
    controller.showPerson("Anna")
    assert _wait(
        qt_app,
        lambda: window.property("personAlbumName") == "Anna"
        and window.property("thumbSize") == people_size,
    )

    settings.sync()
    reopened_settings = QSettings(settings.fileName(), QSettings.Format.IniFormat)
    restarted_controller = AppController(
        controller._db_path,
        tuple(controller.watchedFolders),
        controller._provider,
        settings=reopened_settings,
    )
    try:
        assert restarted_controller.thumbScale == library_size
        restarted_controller.showPerson("Anna")
        assert restarted_controller.thumbScale == people_size
    finally:
        restarted_controller.deleteLater()
        qt_app.processEvents()

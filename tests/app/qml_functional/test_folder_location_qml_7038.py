"""#7038: a meglévő mappa Hely mezőjének valódi szerkesztési útja."""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import (
    load_or_empty,
    parse_document,
    read_folder_location,
    save_document,
    with_folder_location,
)
from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


def _open_folder_properties(pane, path, qt_app, dialog):
    QMetaObject.invokeMethod(
        pane,
        "openFolderDescription",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", str(path)),
    )
    assert var_feltetelre(qt_app, lambda: dialog.property("opened"), 3.0)


def _click(window, item):
    assert item is not None and item.property("enabled") is True
    center = item.mapToScene(
        QPointF(
            float(item.property("width")) / 2,
            float(item.property("height")) / 2,
        )
    )
    assert 0 <= center.x() < window.width()
    assert 0 <= center.y() < window.height()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def _replace_text(window, field, value):
    _click(window, field)
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(window, Qt.Key.Key_Backspace)
    for character in value:
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(character))


def test_meglevo_mappa_helye_ujranyitaskor_megmarad_es_uresen_torli(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    library = tmp_path / "kepek"
    folder = library / "nyar"
    folder.mkdir()
    make_jpeg(folder / "photo.jpg")
    ini_path = folder / ".picasa.ini"
    save_document(
        with_folder_location(parse_document(""), "Balaton"), ini_path
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload(preserve_scroll=True)
    controller.selectFolder(str(folder))

    pane = window.findChild(QObject, "folderPane")
    assert pane is not None
    dialog = window.findChild(QObject, "folderPropertiesDialog")
    assert dialog is not None
    field = window.findChild(QObject, "folderPropertiesLocation")
    assert field is not None
    ok = window.findChild(QObject, "folderPropertiesOkButton")
    assert ok is not None

    original_height = window.height()
    current_location = "Balaton"
    try:
        for delta, new_location in (
            (-5, "Tihany"),
            (0, "Keszthely"),
            (5, "Veszprem"),
        ):
            target_height = original_height + delta
            window.resize(window.width(), target_height)
            assert var_feltetelre(
                qt_app, lambda height=target_height: window.height() == height, 3.0
            ), f"az ablak nem vette fel a {target_height} px-es magasságot"

            _open_folder_properties(pane, folder, qt_app, dialog)
            assert field.property("enabled") is True
            assert field.property("text") == current_location
            _replace_text(window, field, new_location)
            assert field.property("text") == new_location
            _click(window, ok)
            assert var_feltetelre(
                qt_app, lambda: not dialog.property("opened"), 3.0
            )
            assert read_folder_location(load_or_empty(ini_path)) == new_location
            current_location = new_location

        _open_folder_properties(pane, folder, qt_app, dialog)
        assert field.property("text") == current_location
        _replace_text(window, field, "")
        _click(window, ok)
        assert var_feltetelre(
            qt_app, lambda: not dialog.property("opened"), 3.0
        )
        assert read_folder_location(load_or_empty(ini_path)) == ""

        _open_folder_properties(pane, folder, qt_app, dialog)
        assert field.property("text") == ""
        assert field.property("enabled") is True
    finally:
        window.resize(window.width(), original_height)

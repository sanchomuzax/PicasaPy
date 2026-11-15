"""#6966: tömeges átnevezés: jelölővel maradhat a név, hiba átugrása,
és a valódi Rename-gomb kattintás után minden sikeres kép kijelölve marad."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.qml_halasztott import epitsd_fel_ha_fileops
from support.qt_wait import wait_for_photo_op


def _child(window, name):
    epitsd_fel_ha_fileops(window, name)
    result = window.findChild(QObject, name)
    assert result is not None, f"{name} nem található"
    return result


def _list(value):
    return value.toVariant() if hasattr(value, "toVariant") else list(value)


def _open_rename_many(window, rows):
    dialog = _child(window, "renameManyDialog")
    QMetaObject.invokeMethod(
        dialog, "openFor", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", rows),
    )
    return dialog


def _rename_button(window, dialog):
    buttons = [
        item for item in dialog.findChildren(QQuickItem)
        if item.property("text") == "Rename"
        and item.isVisible()
        and item.width() > 0
        and item.height() > 0
    ]
    assert buttons, "a látható Rename gomb nem található"
    return buttons[-1]


def _click(window, button):
    point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )


def test_unchanged_name_is_enabled_only_when_a_suffix_is_selected(qml_app, qt_app):
    window, _controller, _engine = qml_app
    dialog = _open_rename_many(window, [0])
    field = _child(window, "renameManyField")
    date_check = _child(window, "renameManyDateCheck")
    size_check = _child(window, "renameManySizeCheck")
    button = _rename_button(window, dialog)

    assert field.property("text") == "a"
    assert not button.isEnabled()

    date_check.setProperty("checked", True)
    qt_app.processEvents()
    assert button.isEnabled()

    date_check.setProperty("checked", False)
    size_check.setProperty("checked", True)
    qt_app.processEvents()
    assert button.isEnabled()

    field.setProperty("text", "   ")
    qt_app.processEvents()
    assert not button.isEnabled()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_clicking_rename_keeps_all_renamed_photos_selected(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    library = Path(controller.currentFolder)
    window.setProperty("height", int(window.height()) + height_delta)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    dialog = _open_rename_many(window, [0, 1])
    field = _child(window, "renameManyField")
    field.setProperty("text", "nyaralas")
    qt_app.processEvents()
    button = _rename_button(window, dialog)
    assert button.isEnabled()

    wait_for_photo_op(controller, lambda: _click(window, button), qt_app=qt_app)

    assert (library / "nyaralas.jpg").exists()
    assert (library / "nyaralas-001.jpg").exists()
    selected_names = {
        controller.photos.photos[int(row)].name
        for row in _list(window.property("selectedIndexes"))
    }
    assert selected_names == {"nyaralas.jpg", "nyaralas-001.jpg"}


def test_skipped_file_is_named_in_the_visible_feedback(
    qml_app, qt_app, monkeypatch
):
    window, controller, _engine = qml_app
    library = Path(controller.currentFolder)
    import picasapy.fileops.rename as rename_module

    real_rename = rename_module._rename

    def fail_on_first(source, target):
        if source.name == "a.jpg":
            raise PermissionError("injected read-only file")
        real_rename(source, target)

    monkeypatch.setattr(rename_module, "_rename", fail_on_first)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    dialog = _open_rename_many(window, [0, 1])
    _child(window, "renameManyField").setProperty("text", "nyaralas")
    qt_app.processEvents()
    button = _rename_button(window, dialog)

    wait_for_photo_op(controller, lambda: _click(window, button), qt_app=qt_app)

    banner = _child(window, "errorBannerText")
    assert banner.property("text") == "Skipped: a.jpg"
    assert (library / "a.jpg").exists()
    assert (library / "nyaralas.jpg").exists()


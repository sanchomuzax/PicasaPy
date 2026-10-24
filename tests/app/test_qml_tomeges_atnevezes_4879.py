"""Tömeges átnevezés (#4879/#5702): VALÓDI kattintással és gépeléssel.

A Date és Image resolution jelölő a `rename.fen` rögzített mintáit mutatja,
a kiválasztott kép dátuma és mérete nem befolyásolja az Example sort. A
névmező szűri a tiltott karaktereket, és a két jelölő állása megmarad a
következő megnyitásig.

A jelölőkre és a mezőre `QTest` egéresemény/billentyű megy (a közvetlen
`setProperty` kikerülné a validatort és a kattintás-útvonalat).
"""

import dataclasses

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.qml_halasztott import epitsd_fel_ha_fileops


def _child(window, name):
    epitsd_fel_ha_fileops(window, name)
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nincs meg"
    return obj


def _open(window, qt_app):
    dialog = _child(window, "renameManyDialog")
    QMetaObject.invokeMethod(
        dialog, "openFor", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", [0, 1]),
    )
    QTest.qWait(250)
    qt_app.processEvents()
    assert dialog.property("visible") is True
    return dialog


def _close(dialog, qt_app):
    # Qt 6.11: az elfogadott QtQuick-dialógus nyitva maradhat
    QMetaObject.invokeMethod(dialog, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _click(window, item):
    quick_window = item.window()
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        quick_window, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier, QPoint(int(center.x()), int(center.y())),
    )
    QTest.qWait(50)


def _type(window, field, text):
    _click(window, field)
    for character in text:
        QTest.keyClick(field.window(), character)
    QTest.qWait(50)


class TestRenameManyDateAndFlags:
    @pytest.mark.parametrize("height_delta", [-5, 0, 5])
    def test_checkboxes_show_fixed_samples_after_real_clicks(
        self, qml_app, qt_app, tmp_path, height_delta
    ):
        window, controller, _lib, _engine = qml_app
        window.setHeight(window.height() + height_delta)
        # A kijelölt fájl valós adatai térjenek el a Picasa rögzített mintáitól.
        photos = controller.photos.photos
        controller.photos.set_photos(
            (dataclasses.replace(photos[0], taken_at="2023-12-17T17:08:09"),)
            + photos[1:]
        )
        dialog = _open(window, qt_app)
        try:
            _type(window, _child(window, "renameManyField"), "nyaralas")
            _click(window, _child(window, "renameManyDateCheck"))
            assert _child(window, "renameManyDateCheck").property("checked") is True
            sample = _child(window, "renameManySampleLabel").property("text")
            assert sample == "Example: nyaralas 08-01-2004 2-30-45 PM.jpg"

            _click(window, _child(window, "renameManySizeCheck"))
            sample = _child(window, "renameManySampleLabel").property("text")
            assert sample == (
                "Example: nyaralas 08-01-2004 2-30-45 PM 640x480.jpg"
            )

            _click(window, _child(window, "renameManyDateCheck"))
            sample = _child(window, "renameManySampleLabel").property("text")
            assert sample == "Example: nyaralas 640x480.jpg"

            if height_delta == 0:
                screenshot = window.grabWindow()
                assert not screenshot.isNull(), "üres lett a párbeszéd képe"
                assert screenshot.save(str(tmp_path / "rename-preview-5702.png"))
        finally:
            _close(dialog, qt_app)

    def test_forbidden_filename_characters_cannot_be_typed(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _open(window, qt_app)
        try:
            field = _child(window, "renameManyField")
            _type(window, field, 'a\\b/c:d*e?f"g<h>i|j k')
            assert field.property("text") == "abcdefghij k"
        finally:
            _close(dialog, qt_app)

    def test_name_length_is_limited(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _open(window, qt_app)
        try:
            field = _child(window, "renameManyField")
            _type(window, field, "a" * 210)
            assert len(field.property("text")) == 200
        finally:
            _close(dialog, qt_app)

    def test_flags_persist_until_next_open(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        dialog = _open(window, qt_app)
        try:
            assert _child(window, "renameManyDateCheck").property("checked") is False
            _click(window, _child(window, "renameManyDateCheck"))
            _click(window, _child(window, "renameManySizeCheck"))
        finally:
            _close(dialog, qt_app)
        assert controller.renameUseDate() is True
        assert controller.renameUseSize() is True
        dialog = _open(window, qt_app)
        try:
            assert _child(window, "renameManyDateCheck").property("checked") is True
            assert _child(window, "renameManySizeCheck").property("checked") is True
            _click(window, _child(window, "renameManyDateCheck"))
        finally:
            _close(dialog, qt_app)
        assert controller.renameUseDate() is False
        assert controller.renameUseSize() is True

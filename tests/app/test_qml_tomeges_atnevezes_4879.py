"""Tömeges átnevezés (#4879): VALÓDI kattintással és gépeléssel.

Három pont, a `rename.fen` szerint:
- a Dátum jelölő a felvétel dátumát ÉS idejét teszi a névbe (élő példasor);
- a névmezőbe tiltott fájlnév-karakter nem gépelhető be;
- a két jelölő állása a következő megnyitásig megmarad.

A jelölőkre és a mezőre `QTest` egéresemény/billentyű megy (a közvetlen
`setProperty` kikerülné a validatort és a kattintás-útvonalat); a mért
példasor a névképző azonos bemenetével számolt várható értéket kapja.
"""

import dataclasses

from PySide6.QtCore import Q_ARG, QLocale, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.fileops.rename import format_taken_at
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
    def test_date_checkbox_adds_date_and_time_to_live_example(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        # a fixture-képeknek nincs EXIF-dátumuk: az első sor kap egyet
        photos = controller.photos.photos
        controller.photos.set_photos(
            (dataclasses.replace(photos[0], taken_at="2004-08-01T14:30:45"),)
            + photos[1:]
        )
        dialog = _open(window, qt_app)
        try:
            _type(window, _child(window, "renameManyField"), "nyaralas")
            _click(window, _child(window, "renameManyDateCheck"))
            assert _child(window, "renameManyDateCheck").property("checked") is True
            expected_stamp = format_taken_at("2004-08-01T14:30:45", QLocale.system())
            sample = _child(window, "renameManySampleLabel").property("text")
            assert sample == f"Example: nyaralas {expected_stamp}.jpg"
            # a dátum ÉS az idő is benne van (nem csak az ISO-nap), tiltott jel nélkül
            assert "30" in expected_stamp and "45" in expected_stamp
            assert not set(expected_stamp) & set('\\/:*?"<>|')
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

"""Az e-mail címmező Automatikus kitöltés kapcsolója (#4636)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QSettings, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.app.email_controller import EmailController

_APP_DIR = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app"
_KEEPALIVE: list[object] = []


@pytest.fixture
def email_context(qt_app, tmp_path):
    settings_path = tmp_path / "picasapy.ini"
    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    controller = EmailController(photo_source=lambda: [], settings=settings)

    engine = QQmlEngine()
    engine.addImportPath(str(_APP_DIR / "qml"))
    engine.rootContext().setContextProperty("emailController", controller)
    source = """
        import QtQuick
        import QtQuick.Controls
        import QtQuick.Window
        import PicasaPy 1.0

        Window {
            id: root
            width: 360
            height: 160 + heightOffset
            visible: true
            property int heightOffset: 0

            function openRecipientMenu() {
                recipientContextArea.createContextMenu().popupFor(recipientField)
            }
            function openSubjectMenu() {
                subjectContextArea.createContextMenu().popupFor(subjectField)
            }

            TextField {
                id: recipientField
                objectName: "recipientField"
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                TextFieldContextArea {
                    id: recipientContextArea
                    objectName: "recipientContextArea"
                    autoCompleteSupported: true
                    autoCompleteController: emailController
                }
            }

            TextField {
                id: subjectField
                objectName: "subjectField"
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                TextFieldContextArea {
                    id: subjectContextArea
                    objectName: "subjectContextArea"
                    autoCompleteSupported: false
                    autoCompleteController: emailController
                }
            }
        }
    """
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    window = component.create()
    assert window is not None
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, window, controller, engine))
    window.show()
    qt_app.processEvents()

    yield window, controller, settings_path, qt_app

    window.close()
    engine.deleteLater()


def _menu(area):
    assert QMetaObject.invokeMethod(area, "createContextMenu", Qt.ConnectionType.DirectConnection)
    menu = area.property("contextMenu")
    assert menu is not None
    return menu


def test_email_autocomplete_defaults_on_and_survives_restart(tmp_path):
    settings_path = tmp_path / "settings.ini"
    first_settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    first = EmailController(photo_source=lambda: [], settings=first_settings)

    assert first.emailAutocompleteEnabled is True
    first.setEmailAutocompleteEnabled(False)
    first_settings.sync()
    assert first_settings.value("mail/EmailAutocomplete") is False

    reopened_settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    reopened = EmailController(photo_source=lambda: [], settings=reopened_settings)
    assert reopened.emailAutocompleteEnabled is False


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_only_recipient_context_menu_has_an_enabled_checkable_toggle(
    email_context, height_offset
):
    window, controller, settings_path, qt_app = email_context
    window.setProperty("heightOffset", height_offset)
    qt_app.processEvents()

    recipient_area = window.findChild(QObject, "recipientContextArea")
    subject_area = window.findChild(QObject, "subjectContextArea")
    recipient_menu = _menu(recipient_area)
    recipient_item = recipient_menu.findChild(QObject, "textMenuAutoComplete")

    assert recipient_item is not None
    assert QMetaObject.invokeMethod(
        window, "openRecipientMenu", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert recipient_item.property("visible") is True
    assert recipient_item.property("checkable") is True
    assert recipient_item.property("placeholder") is None
    assert recipient_item.property("enabled") is True
    assert recipient_item.property("checked") is True

    QMetaObject.invokeMethod(
        recipient_item, "toggle", Qt.ConnectionType.DirectConnection
    )
    QMetaObject.invokeMethod(
        recipient_item, "triggered", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()

    assert controller.emailAutocompleteEnabled is False
    assert recipient_item.property("checked") is False

    QMetaObject.invokeMethod(
        recipient_menu, "close", Qt.ConnectionType.DirectConnection
    )
    QMetaObject.invokeMethod(
        window, "openSubjectMenu", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    subject_menu = _menu(subject_area)
    subject_item = subject_menu.findChild(QObject, "textMenuAutoComplete")
    assert subject_item is not None
    assert subject_item.property("visible") is False

    reopened = EmailController(
        photo_source=lambda: [],
        settings=QSettings(str(settings_path), QSettings.Format.IniFormat),
    )
    assert reopened.emailAutocompleteEnabled is False

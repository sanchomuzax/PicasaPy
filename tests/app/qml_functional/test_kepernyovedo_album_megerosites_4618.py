"""A képernyővédő album-hozzáadásának megerősítése és visszajelzése (#4618)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest
from support.qt_wait import varj_feltetelre


_KERDES = "Are you sure you want to add all of the selected album's images?"


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _click(window, item, qt_app):
    assert item.isEnabled(), f"{item.objectName()}: a gomb le van tiltva"
    assert item.width() > 0 and item.height() > 0, (
        f"{item.objectName()}: nincs kattintható mérete"
    )
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )
    qt_app.processEvents()


def _add_from_create_menu(window, qt_app):
    menu_bar = window.property("menuBar")
    create_header = next(
        item
        for item in menu_bar.findChildren(QObject)
        if "MenuBarItem" in item.metaObject().className()
        and item.property("text") == "&Create"
    )
    _click(window, create_header, qt_app)

    action = _child(window, "menuCreateAddScreensaver")
    assert varj_feltetelre(
        qt_app, lambda: action.property("visible") is True, 3.0
    ), "a Létrehozás menü képernyővédő-tétele nem jelent meg"
    _click(window, action, qt_app)


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_album_hozzaadasa_megerositest_es_nullas_visszajelzest_ad(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    celmagassag = window.height() + height_delta
    window.resize(window.width(), celmagassag)
    assert varj_feltetelre(qt_app, lambda: window.height() == celmagassag, 3.0)

    token = controller.createAlbum("Képernyővédő próba", [0])
    assert token
    controller.showAlbum(token)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    _add_from_create_menu(window, qt_app)
    confirm = _child(window, "screensaverAlbumConfirmDialog")
    assert confirm.property("visible") is True
    assert _child(confirm, "screensaverAlbumConfirmMessageLabel").property("text") == _KERDES
    assert confirm.property("title") == "Confirm"
    yes_button = _child(confirm, "screensaverAlbumConfirmYesButton")
    no_button = _child(confirm, "screensaverAlbumConfirmNoButton")
    assert yes_button.property("text") == "Yes"
    assert no_button.property("text") == "No"

    _click(window, no_button, qt_app)
    assert not controller._screensaver_photo_paths(), (
        "a Nem kattintás a megerősítés ellenére hozzáadott képet"
    )

    path = controller.photos.filePathAt(0)
    _add_from_create_menu(window, qt_app)
    confirm = _child(window, "screensaverAlbumConfirmDialog")
    assert varj_feltetelre(qt_app, lambda: confirm.property("visible") is True, 3.0)
    _click(window, _child(confirm, "screensaverAlbumConfirmYesButton"), qt_app)

    banner_text = _child(window, "errorBannerText")
    assert varj_feltetelre(
        qt_app,
        lambda: banner_text.property("text") == "Added 1 pictures to Screensaver.",
        3.0,
    ), "az Igen kattintás nem adta hozzá a kijelölt képet"
    assert controller._screensaver_photo_paths() == [path]

    _add_from_create_menu(window, qt_app)
    confirm = _child(window, "screensaverAlbumConfirmDialog")
    assert varj_feltetelre(qt_app, lambda: confirm.property("visible") is True, 3.0)
    _click(window, _child(confirm, "screensaverAlbumConfirmYesButton"), qt_app)
    assert varj_feltetelre(
        qt_app,
        lambda: banner_text.property("text") == "Added 0 pictures to Screensaver.",
        3.0,
    ), "az ismételt kép után nem jelezte, hogy semmi új nem került be"

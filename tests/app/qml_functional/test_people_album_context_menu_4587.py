"""#4587: az Emberek-album helyi menüjének szerkesztő és törlő műveletei."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import contacts_of, load_document

_PERSON_ID = "aaaaaaaaaaaaaaaa"
_FACE_RECT = "1e00280045006e00"
_HEIGHT_OFFSETS = (-5, 0, 5)


def _wait(qt_app, condition, seconds: float = 3.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(condition())


def _find(root, object_name):
    return root.findChild(QObject, object_name)


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _visible_item(root, object_name):
    return next(
        (
            item
            for item in _walk(root.contentItem())
            if item.objectName() == object_name and item.isVisible()
        ),
        None,
    )


def _click(qt_app, item, button=Qt.MouseButton.LeftButton):
    assert item is not None, "a kattintandó felületi elem hiányzik"
    assert item.property("enabled") is not False, (
        f"{item.objectName()}: a művelet le van tiltva"
    )
    assert item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        button,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _prepare_person(window, controller, qt_app, tmp_path, height_offset):
    target_height = int(window.height()) + height_offset
    window.setHeight(target_height)
    assert _wait(qt_app, lambda: int(window.height()) == target_height)

    library = Path(controller.photos.filePathAt(0)).parent
    ini_path = library / ".picasa.ini"
    ini_path.write_text(
        "[Contacts2]\n"
        f"{_PERSON_ID}=Anna;anna@example.test;gaia-anna\n"
        "[a.jpg]\n"
        f"faces=rect64({_FACE_RECT}),{_PERSON_ID}\n",
        encoding="utf-8",
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, library)
    controller._reload_after_sync()

    pane = _find(window, "folderPane")
    assert pane is not None
    pane.setProperty("peopleCollapsed", False)
    assert _wait(
        qt_app,
        lambda: _visible_item(window, "personItem_Anna") is not None,
    ), "az Anna Emberek-album sora nem jelent meg"
    return pane, ini_path


def _open_person_menu(window, pane, qt_app, item_name):
    row = _visible_item(window, "personItem_Anna")
    _click(qt_app, row, Qt.MouseButton.RightButton)
    menu = _find(pane, "peopleAlbumContextMenu")
    assert _wait(
        qt_app, lambda: menu is not None and menu.property("visible") is True
    ), "az Emberek-album helyi menüje nem nyílt meg"
    assert menu.property("personName") == "Anna"
    item = _find(menu, item_name)
    assert item is not None, f"a menütétel hiányzik: {item_name}"
    _click(qt_app, item)


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_emberek_album_szerkesztes_a_kattintott_szemelyt_nyitja_meg(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    pane, _ini_path = _prepare_person(
        window, controller, qt_app, tmp_path, height_offset
    )
    _open_person_menu(window, pane, qt_app, "peopleAlbumMenuEdit")

    loader = _find(window, "peopleManagerLoader")
    assert loader is not None
    assert _wait(
        qt_app,
        lambda: (
            loader.property("item") is not None
            and loader.property("item").property("visible") is True
        ),
    ), "a People Manager nem nyílt meg"
    dialog = loader.property("item")
    name_field = _find(dialog, "peopleManagerNameField")
    assert name_field is not None
    assert name_field.property("text") == "Anna"
    assert dialog.property("selectedKey") == "contact:Anna"
    _click(qt_app, _find(dialog, "peopleManagerCancelButton"))


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_emberek_album_torles_megerositest_ker_es_torli_a_szemelyt(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    pane, ini_path = _prepare_person(
        window, controller, qt_app, tmp_path, height_offset
    )

    _open_person_menu(window, pane, qt_app, "peopleAlbumMenuDelete")
    confirmation = _find(pane, "peopleAlbumDeleteConfirmation")
    assert _wait(
        qt_app,
        lambda: confirmation is not None
        and confirmation.property("visible") is True,
    ), "a személy törléséhez nem jelent meg megerősítés"
    assert any(
        contact.name == "Anna" for contact in contacts_of(load_document(ini_path))
    ), "a személy a megerősítés előtt törlődött"

    decisions = []
    confirmation.accepted.connect(lambda: decisions.append("accepted"))
    confirmation.rejected.connect(lambda: decisions.append("rejected"))
    _click(qt_app, _find(confirmation, "peopleAlbumDeleteCancelButton"))
    assert _wait(qt_app, lambda: confirmation.property("visible") is False)
    assert decisions == ["rejected"]
    assert any(
        contact.name == "Anna" for contact in contacts_of(load_document(ini_path))
    ), "a Mégse gomb törölte a személyt"

    _open_person_menu(window, pane, qt_app, "peopleAlbumMenuDelete")
    assert _wait(qt_app, lambda: confirmation.property("visible") is True)
    _click(qt_app, _find(confirmation, "peopleAlbumDeleteConfirmButton"))

    assert _wait(
        qt_app,
        lambda: _visible_item(window, "personItem_Anna") is None,
    ), "a megerősített törlés után is megmaradt az Emberek-album"
    assert not any(
        contact.name == "Anna" for contact in contacts_of(load_document(ini_path))
    )

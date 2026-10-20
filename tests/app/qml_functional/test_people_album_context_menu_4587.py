"""#4587: az Emberek-album helyi menüjének szerkesztő és törlő műveletei."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import contacts_of, load_document
from tests.support.varakozas import var_feltetelre

_PERSON_ID = "aaaaaaaaaaaaaaaa"
_PERSON_NAME = "Teszt Elek"
_FACE_RECT = "1e00280045006e00"
_HEIGHT_OFFSETS = (-5, 0, 5)


def _wait(qt_app, condition, seconds: float = 10.0) -> bool:
    return var_feltetelre(qt_app, condition, seconds)


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
        f"{_PERSON_ID}={_PERSON_NAME};anna@example.test;gaia-anna\n"
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
        lambda: _visible_item(window, f"personItem_{_PERSON_NAME}") is not None,
    ), "a Teszt Elek Emberek-album sora nem jelent meg"
    return pane, ini_path


def _open_person_menu(window, pane, qt_app, item_name):
    row = _visible_item(window, f"personItem_{_PERSON_NAME}")
    _click(qt_app, row, Qt.MouseButton.RightButton)
    menu = _find(pane, "peopleAlbumContextMenu")
    assert _wait(
        qt_app, lambda: menu is not None and menu.property("visible") is True
    ), "az Emberek-album helyi menüje nem nyílt meg"
    assert menu.property("personName") == _PERSON_NAME
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
    assert name_field.property("text") == _PERSON_NAME
    assert dialog.property("selectedKey") == f"contact:{_PERSON_NAME}"
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
    cancel_button = _find(confirmation, "peopleAlbumDeleteCancelButton")
    assert cancel_button.property("activeFocus") is True, (
        "a Cancel nem az alapértelmezett billentyűfókusz"
    )
    if height_offset == 0:
        rendered = window.grabWindow()
        assert not rendered.isNull(), "a megerősítő ablak nem rajzolódott ki"
        assert rendered.save(str(tmp_path / "people-album-delete-5391.png"))
    assert any(
        contact.name == _PERSON_NAME for contact in contacts_of(load_document(ini_path))
    ), "a személy a megerősítés előtt törlődött"

    decisions = []
    confirmation.accepted.connect(lambda: decisions.append("accepted"))
    confirmation.rejected.connect(lambda: decisions.append("rejected"))

    # A valódi Return billentyűnek az eredeti párbeszéd alapértelmezett
    # Mégse gombját kell működtetnie, nem a törlést.
    QTest.keyClick(cancel_button.window(), Qt.Key.Key_Return)
    assert _wait(qt_app, lambda: confirmation.property("visible") is False)
    assert decisions == ["rejected"]
    assert any(
        contact.name == _PERSON_NAME for contact in contacts_of(load_document(ini_path))
    ), "a Return törölte a névjegyet"
    assert load_document(ini_path).section("a.jpg").get("faces") is not None, (
        "a Return törölte az arcot"
    )

    _open_person_menu(window, pane, qt_app, "peopleAlbumMenuDelete")
    assert _wait(qt_app, lambda: confirmation.property("visible") is True)
    assert confirmation.property("title") == "Remove People"
    assert _find(confirmation, "peopleAlbumDeleteMessage").property("text") == (
        f'Are you sure you want to delete the people album "{_PERSON_NAME}"?'
    )
    online_faces = _find(confirmation, "peopleAlbumDeleteOnlineFacesCheckBox")
    assert online_faces is not None
    assert online_faces.property("text") == (
        "Delete tagged faces from synced Picasa Web albums, too"
    )
    assert online_faces.property("checked") is False
    assert _find(confirmation, "peopleAlbumDeleteConfirmButton").property("text") == (
        "Delete Album"
    )
    assert _find(confirmation, "peopleAlbumDeleteCancelButton").property("text") == (
        "Cancel"
    )

    _click(qt_app, _find(confirmation, "peopleAlbumDeleteCancelButton"))
    assert _wait(qt_app, lambda: confirmation.property("visible") is False)
    assert decisions == ["rejected", "rejected"]
    assert any(
        contact.name == _PERSON_NAME for contact in contacts_of(load_document(ini_path))
    ), "a Mégse gomb törölte a személyt"

    _open_person_menu(window, pane, qt_app, "peopleAlbumMenuDelete")
    assert _wait(qt_app, lambda: confirmation.property("visible") is True)
    _click(qt_app, _find(confirmation, "peopleAlbumDeleteConfirmButton"))

    assert _wait(
        qt_app,
        lambda: _visible_item(window, f"personItem_{_PERSON_NAME}") is None,
    ), "a megerősített törlés után is megmaradt az Emberek-album"
    assert any(
        contact.name == _PERSON_NAME for contact in contacts_of(load_document(ini_path))
    ), "a törlés eltávolította a [Contacts2] névjegyet"
    deleted_section = load_document(ini_path).section("a.jpg")
    assert deleted_section is None or deleted_section.get("faces") is None

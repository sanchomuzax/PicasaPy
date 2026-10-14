"""#4536: valódi fotó-helyi-menü kattintásból mentett személy-indexkép."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import parse_document, update_document
from tests.support.varakozas import var_feltetelre

_PERSON_ID = "aaaaaaaaaaaaaaaa"
_RECT = "1e00280045006e00"
_HEIGHT_OFFSETS = (-5, 0, 5)


def _wait(qt_app, condition, seconds: float = 3.0) -> bool:
    return var_feltetelre(qt_app, condition, seconds)


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _find_item(window, object_name):
    return next(
        (item for item in _walk(window.contentItem())
         if item.objectName() == object_name),
        None,
    )


def _first_thumb_mouse_area(window):
    matches = [
        item for item in _walk(window.contentItem())
        if item.objectName() == "thumbMouseArea"
        and item.parentItem() is not None
        and item.parentItem().property("index") == 0
    ]
    assert len(matches) == 1, f"az első rácsfotó egérterülete: {len(matches)}"
    return matches[0]


def _click_item(item, button=Qt.MouseButton.LeftButton):
    assert item is not None
    assert item.isVisible() and item.width() > 0 and item.height() > 0
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        button,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def test_photo_menu_sets_and_persists_the_person_face_thumbnail(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    photo_path = controller.photos.filePathAt(0)
    library = Path(photo_path).parent
    update_document(
        library / ".picasa.ini",
        lambda _old: parse_document(
            "[Contacts2]\n"
            f"{_PERSON_ID}=Anna;;\n"
            "[a.jpg]\n"
            f"faces=rect64({_RECT}),{_PERSON_ID}\n"
        ),
        backup=False,
    )
    db = controller._db_path
    with open_index(db) as conn:
        sync_tree(conn, library)
    controller._reload_after_sync()
    controller.showPerson("Anna")
    assert _wait(qt_app, lambda: controller.currentPersonName == "Anna")

    original_height = int(window.height())
    for offset in _HEIGHT_OFFSETS:
        target_height = original_height + offset
        window.setHeight(target_height)
        assert _wait(
            qt_app, lambda height=target_height: int(window.height()) == height
        )

        target = _first_thumb_mouse_area(window)
        _click_item(target, Qt.MouseButton.RightButton)
        menu = window.findChild(QObject, "photoContextMenu")
        assert menu is not None
        item = window.findChild(
            QQuickItem, "contextMenuSetAsPeopleAlbumThumbnail"
        )
        assert item is not None
        assert _wait(
            qt_app,
            lambda target_menu=menu, target_item=item: (
                target_menu.property("visible") is True
                and target_item.isVisible()
            ),
        )
        assert item.property("enabled") is True, (
            "a névvel ellátott arc indexképként választható kell legyen"
        )
        _click_item(item)
        assert _wait(
            qt_app, lambda target_menu=menu: target_menu.property("visible") is False
        )

        from picasapy.index import person_thumbnail

        with open_index(db) as conn:
            saved = person_thumbnail(conn, "Anna")
        assert saved is not None
        assert saved.photo_id == int(controller.photos.idAt(0))

        avatar = _find_item(window, "personThumbnailImage_Anna")
        assert avatar is not None
        source = avatar.property("source").toString()
        assert source.startswith(f"image://thumbs/{saved.photo_id}?")
        assert "&fz=" in source

        row = _find_item(window, "personItem_Anna")
        assert row is not None

    window.setHeight(original_height)
    assert _wait(qt_app, lambda: int(window.height()) == original_height)

"""A 30 fölötti címkék több tokenje külön megerősítést kap (#7138)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre, varj_kattinthatora


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    found = window.findChild(QObject, name)
    assert found is not None, f"A felületen nincs ilyen elem: {name}"
    return found


def _click(window, item, qt_app):
    varj_kattinthatora(window, item)
    center = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    ).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=center)
    qt_app.processEvents()


def _type_and_enter(window, qt_app, text: str) -> None:
    field = _item(window, "tagInput")
    _click(window, field, qt_app)
    assert varj_feltetelre(
        qt_app, lambda: field.property("activeFocus") is True, 3.0
    ), "a címkemező nem kapott fókuszt"
    assert field.property("text") == ""
    for character in text:
        if character == " ":
            key = Qt.Key.Key_Space
        elif character == ",":
            key = Qt.Key.Key_Comma
        else:
            key = Qt.Key(ord(character.upper()))
        QTest.keyClick(window, key)
    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()


def _has_tag(controller, rows, tag: str) -> bool:
    wanted = tag.casefold()
    return all(
        wanted in {
            value.strip().casefold()
            for value in (controller.photos.photos[row].keywords or "").split(",")
        }
        for row in rows
    )


def _lacks_tag(controller, rows, tag: str) -> bool:
    unwanted = tag.casefold()
    return all(
        unwanted not in {
            value.strip().casefold()
            for value in (controller.photos.photos[row].keywords or "").split(",")
        }
        for row in rows
    )


def test_minden_token_sajat_kerdest_kap_es_varja_az_elozot(qml_app, qt_app):
    window, controller, _engine = qml_app
    library = Path(controller._roots[0])
    for index in range(29):
        make_jpeg(library / f"tag7138_{index:02d}.jpg", size=(120, 90))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, str(library))
    controller._reload()
    controller.selectFolder(str(library))
    window.setProperty("activeDrawerTab", "tags")
    assert varj_feltetelre(
        qt_app, lambda: controller.photos.rowCount() == 31, 15.0
    ), "a tesztkönyvtárnak 31 képet kell tartalmaznia"

    ablakmagassag = int(window.height())
    sorok31 = list(range(31))
    window.setProperty("selectedIndexes", sorok31)
    window.setProperty("selectedIndex", 0)
    window.setHeight(ablakmagassag - 5)
    qt_app.processEvents()

    # Mindkét Igen után a két címke mind a 31 képre kerül.
    _type_and_enter(window, qt_app, "tag1, tag2")
    dialog = window.findChild(QObject, "bulkTagConfirmDialog")
    assert dialog is not None, "31 kijelölt képnél meg kell jelennie a kérdésnek"
    assert varj_feltetelre(
        qt_app,
        lambda: bool(dialog.property("visible"))
        and dialog.property("keyword") == "tag1",
        3.0,
    ), "az első kérdésnek a tag1 címkéről kell szólnia"
    assert "31 items" in dialog.property("message")

    _click(window, _item(window, "bulkTagConfirmOkButton"), qt_app)
    assert varj_feltetelre(
        qt_app,
        lambda: bool(dialog.property("visible"))
        and dialog.property("keyword") == "tag2",
        3.0,
    ), "a tag2 kérdése csak a tag1 kérdés lezárása után jelenhet meg"
    _click(window, _item(window, "bulkTagConfirmOkButton"), qt_app)
    assert varj_feltetelre(
        qt_app,
        lambda: _has_tag(controller, sorok31, "tag1")
        and _has_tag(controller, sorok31, "tag2"),
        15.0,
    ), "mindkét elfogadott címkének mind a 31 képre fel kell kerülnie"

    # Az első Mégse csak a tag3-at hagyja ki; a tag4 külön kérdésként követi.
    window.setHeight(ablakmagassag)
    _type_and_enter(window, qt_app, "tag3, tag4")
    assert varj_feltetelre(
        qt_app,
        lambda: bool(dialog.property("visible"))
        and dialog.property("keyword") == "tag3",
        3.0,
    ), "a Mégse-próba első kérdése a tag3 címkéről szóljon"
    _click(window, _item(window, "bulkTagConfirmCancelButton"), qt_app)
    assert varj_feltetelre(
        qt_app,
        lambda: bool(dialog.property("visible"))
        and dialog.property("keyword") == "tag4",
        3.0,
    ), "a tag3 elutasítása után a tag4 kérdésének kell következnie"
    _click(window, _item(window, "bulkTagConfirmOkButton"), qt_app)
    assert varj_feltetelre(
        qt_app,
        lambda: _lacks_tag(controller, sorok31, "tag3")
        and _has_tag(controller, sorok31, "tag4"),
        15.0,
    ), "a Mégse csak a tag3-at hagyhatja ki"

    # Harminc képnél mindkét token azonnal felkerül, kérdés nélkül.
    sorok30 = list(range(30))
    window.setProperty("selectedIndexes", sorok30)
    window.setHeight(ablakmagassag + 5)
    qt_app.processEvents()
    _type_and_enter(window, qt_app, "tag30a, tag30b")
    assert not dialog.property("visible"), "30 képnél nem kell megerősítés"
    assert varj_feltetelre(
        qt_app,
        lambda: _has_tag(controller, sorok30, "tag30a")
        and _has_tag(controller, sorok30, "tag30b")
        and _lacks_tag(controller, [30], "tag30a")
        and _lacks_tag(controller, [30], "tag30b"),
        15.0,
    ), "30 képnél mindkét címke csak a kijelölt képekre kerüljön fel"

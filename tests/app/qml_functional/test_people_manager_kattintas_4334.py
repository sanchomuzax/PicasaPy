"""#4334: az Eszközök ▸ People Manager valódi adatműveletei."""

# rontás-kontroll: People Manager helyfoglaló → 4 failed

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import all_photos, open_index, sync_tree
from picasapy.ini import (
    contacts_of,
    encode_rect64,
    load_contacts_xml,
    load_document,
    parse_faces,
)

_PERSON_ID = "aaaaaaaaaaaaaaaa"
_FACE_RECT = "1e00280045006e00"
_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)


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


def _dialog(window):
    loader = _find(window, "peopleManagerLoader")
    if loader is not None:
        return loader.property("item")
    return _find(window, "peopleManagerDialog")


def _dialog_item(window, object_name):
    dialog = _dialog(window)
    if dialog is None:
        return None
    found = dialog.findChild(QObject, object_name)
    if found is not None:
        return found

    def walk(item: QQuickItem):
        for child in item.childItems():
            if child.objectName() == object_name:
                return child
            nested = walk(child)
            if nested is not None:
                return nested
        return None

    # A ListView owns its delegates through a Repeater, so QObject.findChild
    # cannot see them; follow the rendered QQuickItem tree as the click target.
    return walk(window.contentItem())


def _click(qt_app, item) -> None:
    assert item is not None, "a kattintandó felületi elem hiányzik"
    assert item.property("enabled") is not False, (
        f"{item.objectName()}: a művelet le van tiltva"
    )
    assert item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _open_manager(window, qt_app) -> None:
    menu_bar = window.property("menuBar")
    headers = menu_bar.findChildren(QObject)
    tools_menu = next(
        (
            obj for obj in headers
            if obj.property("title") in {"&Tools", "&Eszközök"}
        ),
        None,
    )
    tools_header = next(
        (
            obj for obj in headers
            if "MenuBarItem" in obj.metaObject().className()
            and obj.property("text") in {"&Tools", "&Eszközök"}
        ),
        None,
    )
    assert tools_menu is not None, "az Eszközök menü hiányzik"
    assert tools_header is not None, "az Eszközök menüfejléc hiányzik"
    _click(qt_app, tools_header)
    assert _wait(
        qt_app,
        lambda: tools_menu.property("opened") is True
        and _find(window, "menuToolsPeopleManager") is not None,
    ), "a People Manager menüpont nem jelent meg"
    _click(qt_app, _find(window, "menuToolsPeopleManager"))
    assert _wait(
        qt_app,
        lambda: (
            _dialog(window) is not None
            and _dialog(window).property("visible") is True
        ),
    ), "a People Manager párbeszédablak nem nyílt meg"


def _select_contact(window, qt_app, name: str) -> None:
    assert _dialog_item(window, f"peopleManagerContact_{name}") is not None
    field = _dialog_item(window, "peopleManagerNameField")
    assert field.property("text") == name


def _replace_text(qt_app, item, value: str) -> None:
    _click(qt_app, item)
    window = item.window()
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    for character in value:
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(character))
    qt_app.processEvents()


@pytest.mark.parametrize("height_offset", _WINDOW_HEIGHT_OFFSETS)
def test_eszközök_kattintas_kezelovel_menti_a_neveket_es_emberek_albumokat(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    window.setHeight(window.height() + height_offset)
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
    qt_app.processEvents()

    _open_manager(window, qt_app)
    manager_loader = _find(window, "peopleManagerLoader")
    manager_dialog = manager_loader.property("item")
    assert manager_dialog is not None
    _select_contact(window, qt_app, "Anna")
    assert _dialog_item(window, "peopleManagerPhotoCount").property("text") == "1"
    assert (
        _dialog_item(window, "peopleManagerContactId").property("text")
        == _PERSON_ID
    )
    if height_offset == -5:
        image = window.grabWindow()
        assert not image.isNull(), "a People Manager képernyőképe üres"
        assert image.save(str(tmp_path / "people_manager_4334.png"))
    _replace_text(qt_app, _dialog_item(window, "peopleManagerNameField"), "Anita")
    _replace_text(
        qt_app,
        _dialog_item(window, "peopleManagerEmailField"),
        "anita@example.test",
    )
    _click(qt_app, _dialog_item(window, "peopleManagerOkButton"))
    assert _wait(
        qt_app,
        lambda: _dialog(window).property("visible") is False,
    )

    document = load_document(ini_path)
    contact = next(c for c in contacts_of(document) if c.person_id == _PERSON_ID)
    assert (contact.name, contact.email, contact.gaia_id) == (
        "Anita", "anita@example.test", "gaia-anna"
    )
    faces = parse_faces(document.section("a.jpg").get("faces"))
    assert [(encode_rect64(face.rect), face.contact_id) for face in faces] == [
        (_FACE_RECT, _PERSON_ID)
    ]

    _open_manager(window, qt_app)
    _click(qt_app, _dialog_item(window, "peopleManagerNewButton"))
    assert _dialog_item(window, "peopleManagerEmailField").property("enabled") is False
    _replace_text(qt_app, _dialog_item(window, "peopleManagerNameField"), "Bela")
    entries = manager_dialog.property("entries").toVariant()
    assert entries[-1]["name"] == "Bela", (
        entries,
        manager_dialog.property("selectedKey"),
    )
    before_create = ini_path.read_bytes()
    _click(qt_app, _dialog_item(window, "peopleManagerOkButton"))
    assert _wait(
        qt_app,
        lambda: _dialog(window).property("visible") is False,
    )
    assert ini_path.read_bytes() == before_create
    central_path = Path(controller._db_path).parent / "contacts" / "contacts.xml"
    assert any(c.name == "Bela" for c in load_contacts_xml(central_path))
    document = load_document(ini_path)
    assert document.section("a.jpg").get("faces") == (
        f"rect64({_FACE_RECT}),{_PERSON_ID}"
    )

    _open_manager(window, qt_app)
    _select_contact(window, qt_app, "Anita")
    _click(qt_app, _dialog_item(window, "peopleManagerDeleteButton"))
    _click(qt_app, _dialog_item(window, "peopleManagerOkButton"))
    assert _wait(
        qt_app,
        lambda: _dialog(window).property("visible") is False,
    )

    document = load_document(ini_path)
    assert not any(c.name == "Anita" for c in contacts_of(document))
    section = document.section("a.jpg")
    assert section is None or section.get("faces") is None
    assert all(c.name != "Anita" for c in load_contacts_xml(central_path))


def test_eszközök_megnyit_es_megse_bajtra_valtozatlanul_hagyja_a_mappa_ini_ket(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    first = Path(controller.photos.filePathAt(0)).parent
    first_ini = first / ".picasa.ini"
    first_ini.write_text(
        f"[Contacts2]\n{_PERSON_ID}=Anna;;\n"
        f"[a.jpg]\nfaces=rect64({_FACE_RECT}),{_PERSON_ID}\n",
        encoding="utf-8",
    )

    second = tmp_path / "masik-mappa"
    second.mkdir()
    from support.jpeg_factory import make_jpeg

    make_jpeg(second / "c.jpg")
    second_ini = second / ".picasa.ini"
    second_ini.write_text(
        "[Contacts2]\nbbbbbbbbbbbbbbbb=Bea;;\n[c.jpg]\nstar=yes\n",
        encoding="utf-8",
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, second)
    controller._reload_after_sync()
    qt_app.processEvents()
    with open_index(controller._db_path) as conn:
        folder_paths = {Path(photo.folder_path) for photo in all_photos(conn)}
    ini_paths = {folder / ".picasa.ini" for folder in folder_paths}
    ini_before = {
        path: path.read_bytes() if path.exists() else None for path in ini_paths
    }

    _open_manager(window, qt_app)
    QTest.keyClick(window, Qt.Key.Key_Escape)
    qt_app.processEvents()
    assert _wait(qt_app, lambda: _dialog(window).property("visible") is False)

    ini_after = {
        path: path.read_bytes() if path.exists() else None for path in ini_paths
    }
    assert ini_after == ini_before
    assert all(not path.with_name(path.name + ".bak").exists() for path in ini_before)

"""Az Album/Mappa főmenü Delete... tétele albumnézetben (#7181)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from tests.support.varakozas import var_feltetelre

_ALBUM_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_PERSON_NAME = "Teszt Elek"
_PERSON_ID = "0123456789abcdef"
_FACE_RECT = "1e00280045006e00"
_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)


def _wait(qt_app, condition, label: str, timeout: float = 10.0) -> None:
    assert var_feltetelre(qt_app, condition, timeout), (
        f"határidőn belül nem teljesült: {label}"
    )


def _child(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"a(z) {name} nem található"
    return item


def _click(window, qt_app, item) -> None:
    """Valódi kattintás az elem aktuális, ablakhoz leképzett közepére."""
    assert item is not None and item.width() > 0 and item.height() > 0
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _open_delete_item(window, qt_app):
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a menüsáv nem található"
    album_view = bool(menu_bar.property("currentAlbumToken"))
    titles = {"&Album"} if album_view else {"F&older", "&Folder", "&Mappa"}
    menu = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if item.property("title") in titles
        ),
        None,
    )
    assert menu is not None, "a Mappa/Album menü nem található"
    header = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if "MenuBarItem" in item.metaObject().className()
            and item.property("text") in titles
        ),
        None,
    )
    assert header is not None, "a Mappa/Album menü fejléce nem található"
    if menu.property("opened") is not True:
        _click(window, qt_app, header)
    _wait(
        qt_app,
        lambda: menu.property("opened") is True,
        "a Mappa/Album menü megnyitása",
    )
    item = _child(window, "menuFolderDelete")
    _wait(qt_app, lambda: item.property("visible") is True, "a Delete... tétel")
    return item


def _sync_library(lib: Path, tmp_path, controller, qt_app) -> None:
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    qt_app.processEvents()


def _create_album_with_member(lib: Path, tmp_path, controller, qt_app) -> None:
    (lib / ".picasa.ini").write_text(
        f"[.album:{_ALBUM_TOKEN}]\n"
        "name=Nyaralás\n"
        f"token={_ALBUM_TOKEN}\n"
        "[Contacts2]\n"
        f"{_PERSON_ID}={_PERSON_NAME};;\n"
        "[a.jpg]\n"
        f"albums={_ALBUM_TOKEN}\n"
        f"faces=rect64({_FACE_RECT}),{_PERSON_ID};\n",
        encoding="utf-8",
    )
    _sync_library(lib, tmp_path, controller, qt_app)
    controller.showAlbum(_ALBUM_TOKEN)
    _wait(
        qt_app,
        lambda: controller.currentAlbumToken == _ALBUM_TOKEN,
        "a felhasználói album megnyitása",
    )


def test_user_album_delete_click_removes_album_and_preserves_photos(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    library = Path(controller.currentFolder)
    _create_album_with_member(library, tmp_path, controller, qt_app)
    original_height = int(window.height())

    for offset in _WINDOW_HEIGHT_OFFSETS:
        target_height = original_height + offset
        window.setHeight(target_height)
        _wait(
            qt_app,
            lambda target_height=target_height: window.height() == target_height,
            f"ablakmagasság {offset:+} px eltéréssel",
        )

        delete_item = _open_delete_item(window, qt_app)
        assert delete_item.property("enabled") is True, (
            "a megnyitott felhasználói albumnál a Delete... szürke"
        )
        _click(window, qt_app, delete_item)

        dialog = _child(window, "deleteAlbumDialog")
        _wait(
            qt_app,
            lambda dialog=dialog: dialog.property("visible") is True,
            "Delete Album ablak",
        )
        assert dialog.property("title") == "Delete Album"
        message = _child(window, "deleteAlbumMessageLabel")
        assert "Nyaralás" in message.property("text")
        no_button = _child(window, "deleteAlbumNoButton")
        remember = _child(window, "deleteAlbumRememberCheck")
        assert no_button.property("text") == "No"
        assert no_button.property("activeFocus") is True
        assert remember.property("visible") is False
        assert remember.property("checked") is False

        if offset != _WINDOW_HEIGHT_OFFSETS[-1]:
            _click(window, qt_app, no_button)
            _wait(
                qt_app,
                lambda dialog=dialog: dialog.property("visible") is False,
                "No elutasítás",
            )
            assert any(album["token"] == _ALBUM_TOKEN for album in controller.albums)

    _click(window, qt_app, _child(window, "deleteAlbumYesButton"))
    _wait(
        qt_app,
        lambda: not any(
            album["token"] == _ALBUM_TOKEN for album in controller.albums
        ),
        "az album eltávolítása a bal hasáb modelljéből",
    )
    assert (library / "a.jpg").is_file()
    assert (library / "b.jpg").is_file()
    ini = (library / ".picasa.ini").read_text(encoding="utf-8")
    assert f"faces=rect64({_FACE_RECT}),{_PERSON_ID};" in ini
    # #7208: a [.album:<token>] szakasz megmarad, csak a token= sorral
    assert f"[.album:{_ALBUM_TOKEN}]" in ini
    assert f"token={_ALBUM_TOKEN}" in ini
    assert f"albums={_ALBUM_TOKEN}" not in ini


def test_empty_user_album_delete_click_removes_album(qml_app, qt_app):
    window, controller, _engine = qml_app
    library = Path(controller.currentFolder)
    token = controller.createEmptyAlbum(
        "Üres album", str(library), "", "", "", False, ""
    )
    assert token
    controller.showAlbum(token)
    _wait(qt_app, lambda: controller.currentAlbumToken == token, "üres album megnyitása")
    original_height = int(window.height())

    for offset in _WINDOW_HEIGHT_OFFSETS:
        target_height = original_height + offset
        window.setHeight(target_height)
        _wait(
            qt_app,
            lambda target_height=target_height: window.height() == target_height,
            f"ablakmagasság {offset:+} px eltéréssel",
        )
        delete_item = _open_delete_item(window, qt_app)
        assert delete_item.property("enabled") is True
        _click(window, qt_app, delete_item)
        dialog = _child(window, "deleteAlbumDialog")
        _wait(
            qt_app,
            lambda dialog=dialog: dialog.property("visible") is True,
            "Delete Album ablak",
        )
        if offset != _WINDOW_HEIGHT_OFFSETS[-1]:
            _click(window, qt_app, _child(window, "deleteAlbumNoButton"))
            _wait(
                qt_app,
                lambda dialog=dialog: dialog.property("visible") is False,
                "No elutasítás",
            )

    _click(window, qt_app, _child(window, "deleteAlbumYesButton"))
    _wait(
        qt_app,
        lambda: not any(album["token"] == token for album in controller.albums),
        "az üres album eltávolítása",
    )
    assert (library / "a.jpg").is_file()
    assert (library / "b.jpg").is_file()


def test_people_album_delete_click_uses_remove_people_dialog(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    library = Path(controller.currentFolder)
    (library / ".picasa.ini").write_text(
        "[Contacts2]\n"
        f"{_PERSON_ID}={_PERSON_NAME};;\n"
        "[a.jpg]\n"
        f"faces=rect64({_FACE_RECT}),{_PERSON_ID};\n",
        encoding="utf-8",
    )
    _sync_library(library, tmp_path, controller, qt_app)
    controller.showPerson(_PERSON_NAME)
    _wait(
        qt_app,
        lambda: controller.currentPersonName == _PERSON_NAME,
        "a személyalbum megnyitása",
    )
    original_height = int(window.height())

    for offset in _WINDOW_HEIGHT_OFFSETS:
        target_height = original_height + offset
        window.setHeight(target_height)
        _wait(
            qt_app,
            lambda target_height=target_height: window.height() == target_height,
            f"ablakmagasság {offset:+} px eltéréssel",
        )
        delete_item = _open_delete_item(window, qt_app)
        assert delete_item.property("enabled") is True, (
            "a megnyitott személyalbumnál a Delete... szürke"
        )
        _click(window, qt_app, delete_item)

        dialog = _child(window, "peopleAlbumDeleteConfirmation")
        _wait(
            qt_app,
            lambda dialog=dialog: dialog.property("visible") is True,
            "Remove People ablak",
        )
        assert dialog.property("title") == "Remove People"
        cancel = _child(window, "peopleAlbumDeleteCancelButton")
        checkbox = _child(window, "peopleAlbumDeleteOnlineFacesCheckBox")
        assert cancel.property("text") == "Cancel"
        assert cancel.property("activeFocus") is True
        assert checkbox.property("checked") is False

        if offset != _WINDOW_HEIGHT_OFFSETS[-1]:
            _click(window, qt_app, cancel)
            _wait(
                qt_app,
                lambda dialog=dialog: dialog.property("visible") is False,
                "Cancel",
            )

    _click(window, qt_app, _child(window, "peopleAlbumDeleteConfirmButton"))
    _wait(
        qt_app,
        lambda: "faces=" not in (library / ".picasa.ini").read_text(
            encoding="utf-8"
        ),
        "a személyalbum arcainak eltávolítása",
    )
    assert (library / "a.jpg").is_file()


def test_internal_album_tokens_keep_delete_disabled(qml_app, qt_app):
    window, controller, _engine = qml_app

    controller.showStarredAlbum()
    _wait(qt_app, lambda: controller.currentAlbumToken == "]star", "Starred Photos nézet")
    assert _open_delete_item(window, qt_app).property("enabled") is False

    controller.showAlbum("]screensaver")
    _wait(
        qt_app,
        lambda: controller.currentAlbumToken == "]screensaver",
        "Screensaver nézet",
    )
    assert _open_delete_item(window, qt_app).property("enabled") is False

    controller.showAlbum("]internal")
    _wait(qt_app, lambda: controller.currentAlbumToken == "]internal", "belső album")
    assert _open_delete_item(window, qt_app).property("enabled") is False


def test_search_results_and_missing_location_keep_delete_disabled(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    controller.search("a")
    _wait(qt_app, lambda: controller.searchActive is True, "keresési találatok")
    assert controller.currentFolder
    assert _open_delete_item(window, qt_app).property("enabled") is False

    controller.search("")
    _wait(qt_app, lambda: controller.searchActive is False, "visszatérés a mappanézetbe")
    picture = Path(controller.currentFolder) / "a.jpg"
    assert controller.begin_quick_view([str(picture)]) is True
    _wait(qt_app, lambda: controller.currentFolder == "", "hely nélküli nézet")
    controller.statusChanged.emit()
    _wait(
        qt_app,
        lambda: window.property("menuBar").property("currentFolder") == "",
        "a menüsáv értesítése a hely nélküli állapotról",
    )
    assert _open_delete_item(window, qt_app).property("enabled") is False


def test_folder_delete_remains_clickable_in_folder_view(qml_app, qt_app):
    window, controller, _engine = qml_app
    assert controller.currentAlbumToken == ""
    assert controller.currentPersonName == ""
    original_height = int(window.height())

    for offset in _WINDOW_HEIGHT_OFFSETS:
        target_height = original_height + offset
        window.setHeight(target_height)
        _wait(
            qt_app,
            lambda target_height=target_height: window.height() == target_height,
            f"ablakmagasság {offset:+} px eltéréssel",
        )
        delete_item = _open_delete_item(window, qt_app)
        assert delete_item.property("enabled") is True
        _click(window, qt_app, delete_item)
        dialog = _child(window, "deleteFolderConfirmDialog")
        _wait(
            qt_app,
            lambda dialog=dialog: dialog.property("visible") is True,
            "Delete Folder ablak",
        )
        if offset != _WINDOW_HEIGHT_OFFSETS[-1]:
            _click(window, qt_app, _child(window, "deleteFolderConfirmNoButton"))
            _wait(
                qt_app,
                lambda dialog=dialog: dialog.property("visible") is False,
                "No elutasítás",
            )

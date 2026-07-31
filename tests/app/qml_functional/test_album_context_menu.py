"""QML-funkcionális teszt: a fotó-kontextusmenü albumtagság-almenüje (#9,
2. lépés) — a `PhotoContextMenu` bekötése a `controller.albums` listájához
és az `addRowsToAlbum` / `removeRowsFromAlbum` / `createAlbum` vezérlő-
slotokhoz (`Main.qml`).

A vezérlő-oldal tényleges ini-írását a
`tests/app/test_album_write_controller.py` teszteli részletesen — itt a
QML-bekötést ellenőrizzük: a menü a `controller.albums` listáját mutatja
(a `FolderPane.qml` albumRepeater mintája, `test_folder_pane_albums.py`), a
menüpontok a helyes controller-hívást váltják ki, és az „Új album"
dialógus a `FileOpsDialogs.qml` átnevezés-dialógusának mintáját követi.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from picasapy.index import open_index, sync_tree

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _select_row(window, qt_app, row):
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    qt_app.processEvents()


def _open_context_menu(window, qt_app, row):
    """A menüt TÉNYLEGESEN megnyitja (`window.openPhotoContextMenu`, a
    `test_qml_fileops_export.py` mintája) — a `MenuItem.visible` csak
    nyitott popupban tükrözi hűen a kötést (a Qt/QML `visible` a
    tényleges (ős-lánccal együtt számolt) láthatóságot adja vissza, zárt
    popupban minden gyerek-elem `False`-t adna, kötéstől függetlenül)."""
    grid = _child(window, "photoGrid")
    QMetaObject.invokeMethod(
        window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", row), Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()


def _close_context_menu(window, qt_app):
    menu = _child(window, "photoContextMenu")
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _add_album_membership(lib, tmp_path, controller, qt_app):
    """A megosztott `qml_app` fixture mappájába (a.jpg, b.jpg) ír egy
    albumot a.jpg taggal, majd resyncel — a `test_folder_pane_albums.py`
    `_add_album`/`_sync_with_album` mintája."""
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\n"
        f"name=Nyaralás\n"
        f"token={_TOKEN}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    qt_app.processEvents()


class TestMenuAlbumBinding:
    def test_menu_reflects_controller_albums(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _add_album_membership(lib, tmp_path, controller, qt_app)

        menu = _child(window, "photoContextMenu")
        albums = menu.property("albums")
        if hasattr(albums, "toVariant"):
            albums = albums.toVariant()
        assert {"token": _TOKEN, "name": "Nyaralás", "count": 1} in albums

        repeater = _child(window, "contextMenuAddToAlbumRepeater")
        assert repeater.property("count") == 1

    def test_remove_from_album_hidden_outside_album_view(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        assert controller.currentAlbumToken == ""
        _open_context_menu(window, qt_app, 0)
        remove_item = _child(window, "contextMenuRemoveFromAlbum")
        assert remove_item.property("visible") is False
        _close_context_menu(window, qt_app)

    def test_remove_from_album_visible_in_album_view(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _add_album_membership(lib, tmp_path, controller, qt_app)
        controller.showAlbum(_TOKEN)
        qt_app.processEvents()

        menu = _child(window, "photoContextMenu")
        assert menu.property("currentAlbumToken") == _TOKEN
        _open_context_menu(window, qt_app, 0)
        remove_item = _child(window, "contextMenuRemoveFromAlbum")
        assert remove_item.property("visible") is True
        _close_context_menu(window, qt_app)


class TestAddToAlbumWiring:
    def test_choosing_an_album_adds_the_selected_row(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _add_album_membership(lib, tmp_path, controller, qt_app)
        _select_row(window, qt_app, 1)  # b.jpg, még nem tagja

        menu = _child(window, "photoContextMenu")
        menu.addToAlbumRequested.emit(_TOKEN)
        qt_app.processEvents()

        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"[b.jpg]\nalbums={_TOKEN}" in ini
        by_token = {a["token"]: a for a in controller.albums}
        assert by_token[_TOKEN]["count"] == 2


class TestRemoveFromAlbumWiring:
    def test_remove_uses_the_active_album_token(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _add_album_membership(lib, tmp_path, controller, qt_app)
        controller.showAlbum(_TOKEN)
        qt_app.processEvents()
        _select_row(window, qt_app, 0)  # a.jpg (az egyetlen tag)

        menu = _child(window, "photoContextMenu")
        menu.removeFromAlbumRequested.emit()
        qt_app.processEvents()

        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={_TOKEN}" not in ini


class TestNewAlbumDialog:
    def test_new_album_requested_opens_dialog(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _select_row(window, qt_app, 0)

        menu = _child(window, "photoContextMenu")
        menu.newAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _child(window, "newAlbumDialog")
        assert dialog.property("visible") is True

    def test_accepting_creates_album_with_selected_rows(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _select_row(window, qt_app, 0)

        menu = _child(window, "photoContextMenu")
        menu.newAlbumRequested.emit()
        qt_app.processEvents()

        field = _child(window, "newAlbumField")
        field.setProperty("text", "Friss album")
        dialog = _child(window, "newAlbumDialog")
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert any(a["name"] == "Friss album" for a in controller.albums)
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert "name=Friss album" in ini

    def test_empty_selection_does_not_open_dialog(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        qt_app.processEvents()

        menu = _child(window, "photoContextMenu")
        menu.newAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _child(window, "newAlbumDialog")
        assert dialog.property("visible") is False

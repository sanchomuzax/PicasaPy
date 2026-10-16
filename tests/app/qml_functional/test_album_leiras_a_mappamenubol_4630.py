"""#4630: az Album menü az éppen megnyitott album leírását szerkeszti.

A forrás a `picasa-menu-parancsok-viselkedes.md` kontextusfüggő
`ID_ALBUM_EDITCAPTIONS` táblája. A menüsor albumágának a tényleges
`AlbumContextMenu` útvonalat és az `album.fen` módú párbeszédet kell használnia.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt

from picasapy.index import open_index, sync_tree

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_LEIRAS = "A megnyitott album leírása"


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _folder_menu(window):
    for obj in window.findChildren(QObject):
        if obj.property("title") in {"F&older", "&Album"}:
            return obj
    raise AssertionError("a felső Mappa/Album menü nem található")


def test_album_menu_a_megnyitott_album_leirasat_nyitja(
    qml_app_email, qt_app, tmp_path
):
    window, controller, _engine = qml_app_email
    lib = tmp_path / "kepek"
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\n"
        f"name=Nyaralás\n"
        f"token={_TOKEN}\n"
        f"description={_LEIRAS}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()

    assert controller.currentAlbumToken == _TOKEN
    alapmagassag = int(window.height())

    for eltolás in (-5, 0, 5):
        window.setHeight(alapmagassag + eltolás)
        qt_app.processEvents()
        assert int(window.height()) == alapmagassag + eltolás
        assert _folder_menu(window).property("title") == "&Album"
        assert any(
            "MenuBarItem" in obj.metaObject().className()
            and obj.property("text") == "&Album"
            for obj in window.property("menuBar").findChildren(QObject)
        )

        item = _child(window, "menuFolderEditDescription")
        assert item.property("enabled") is True
        assert item.property("text") == "&Albumleírás szerkesztése..."
        QMetaObject.invokeMethod(item, "click", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        dialog = _child(window, "folderPropertiesDialog")
        try:
            assert dialog.property("opened") is True
            assert dialog.property("mode") == "album"
            assert dialog.property("albumToken") == _TOKEN
            assert dialog.property("albumName") == "Nyaralás"
            assert dialog.property("currentDescription") == _LEIRAS
        finally:
            QMetaObject.invokeMethod(dialog, "close", Qt.ConnectionType.DirectConnection)
            qt_app.processEvents()

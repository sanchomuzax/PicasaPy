"""QML-funkcionális teszt: fogd-és-vidd az albumlistára — #455.

Az eredeti Picasa albumlistáján ott állt: *„You can drag and drop pictures
here to make a new album."* Két külön dolog van:

* a listára (a hívogató sorra) ejtve **új album** készül — ugyanazzal a
  névkérő párbeszéddel, mint a menüből indított új album;
* egy **meglévő album sorára** ejtve a képek abba az albumba kerülnek.

A húzás a rácsban csak MÁR KIJELÖLT képről indul — a ki nem jelölt
területről továbbra is lasszó lesz, különben elveszne a rács legfontosabb
kijelölő gesztusa.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _emit(obj, signal, *args):
    QMetaObject.invokeMethod(obj, signal, Qt.ConnectionType.DirectConnection, *args)


class TestDropTargets:
    def test_the_invitation_is_visible_in_the_album_list(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        pane = _child(window, "folderPane")
        pane.setProperty("albumsCollapsed", False)
        qt_app.processEvents()

        hint = _child(window, "albumDropHintText")

        assert hint.property("visible") is True
        assert "album" in hint.property("text").lower()

    def test_dropping_on_the_list_opens_the_new_album_dialog(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0])

        _emit(_child(window, "folderPane"), "newAlbumDropped")
        qt_app.processEvents()

        assert _child(window, "newAlbumDialog").property("visible") is True

    def test_an_empty_selection_opens_nothing(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [])

        _emit(_child(window, "folderPane"), "newAlbumDropped")
        qt_app.processEvents()

        assert _child(window, "newAlbumDialog").property("visible") is False

    def test_dropping_on_an_existing_album_adds_the_photos_to_it(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        token = controller.createAlbum("Nyaralás", [0])
        assert token
        qt_app.processEvents()

        # a MÁSODIK kép ejtése ugyanarra az albumra
        window.setProperty("selectedIndexes", [1])
        _emit(
            _child(window, "folderPane"),
            "photosDroppedOnAlbum",
            Q_ARG("QString", token),
        )
        qt_app.processEvents()

        counts = {a["token"]: a["count"] for a in controller.albums}
        assert counts.get(token) == 2

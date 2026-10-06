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


def _visual_items(root):
    for child in root.childItems():
        yield child
        yield from _visual_items(child)


def _attached_drag(item):
    return next(
        child
        for child in item.children()
        if child.metaObject().className() == "QQuickDragAttached"
    )


class TestDropTargets:
    def test_drag_mime_is_exactly_the_grid_and_tray_selection(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        rows = [0, 1]
        window.setProperty("selectedIndexes", rows)
        qt_app.processEvents()

        expected_grid = controller.fileUriList(
            [controller.photos.filePathAt(row) for row in rows]
        )
        proxy = next(
            item
            for item in _visual_items(window.contentItem())
            if item.objectName() == "thumbDragProxy"
            and int(item.parentItem().property("index")) == rows[0]
        )
        assert _attached_drag(proxy).property("mimeData") == {
            "text/uri-list": expected_grid
        }

        controller.selectTrayIndex(1, False, False)
        qt_app.processEvents()
        tray_thumb = next(
            item
            for item in _visual_items(window.contentItem())
            if item.objectName() == "trayPreviewThumb"
            and int(item.property("index")) == 1
        )
        expected_tray = controller.fileUriList(
            [controller.trayItems[1]["path"]]
        )
        assert _attached_drag(tray_thumb).property("mimeData") == {
            "text/uri-list": expected_tray
        }

        eredeti_magassag = window.height()
        try:
            for magassag in (
                eredeti_magassag - 5,
                eredeti_magassag,
                eredeti_magassag + 5,
            ):
                window.resize(window.width(), magassag)
                qt_app.processEvents()
                assert _attached_drag(proxy).property("mimeData") == {
                    "text/uri-list": expected_grid
                }
                assert _attached_drag(tray_thumb).property("mimeData") == {
                    "text/uri-list": expected_tray
                }
        finally:
            window.resize(window.width(), eredeti_magassag)

    def test_the_invitation_is_visible_in_the_album_list(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        pane = _child(window, "folderPane")
        pane.setProperty("albumsCollapsed", False)
        qt_app.processEvents()

        hint = _child(window, "albumDropHintText")

        assert hint.property("visible") is True
        assert "album" in hint.property("text").lower()

    def test_a_listara_ejtes_LETREHOZZA_az_albumot(self, qml_app, qt_app):
        """#2911: a négy belépő egyike — párbeszéd nélkül, „Untitled" néven.

        ⚠️ Korábban azt állította, hogy megnyílik a `newAlbumDialog`. A
        SZÁNDÉK ugyanaz (az ejtés indítja az album-készítést); a mért
        eredetiben viszont ezen az úton nincs névbekérő."""
        window, controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0])

        _emit(_child(window, "folderPane"), "newAlbumDropped")
        qt_app.processEvents()

        assert [a["name"] for a in controller.albums] == ["Untitled"]

    def test_ures_kijelolesnel_nem_tortenik_semmi(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        window.setProperty("selectedIndexes", [])

        _emit(_child(window, "folderPane"), "newAlbumDropped")
        qt_app.processEvents()

        assert controller.albums == []

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

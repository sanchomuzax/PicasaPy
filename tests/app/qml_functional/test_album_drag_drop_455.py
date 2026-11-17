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

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QDateTime, QMetaObject, QObject, Qt

from tests.support.varakozas import var_feltetelre


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
        # #5105: a húzás az egeret követő belső elemen él
        tray_proxy = next(
            item
            for item in _visual_items(tray_thumb)
            if item.objectName() == "trayDragProxy"
        )
        assert _attached_drag(tray_proxy).property("mimeData") == {
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
                assert _attached_drag(tray_proxy).property("mimeData") == {
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

    @pytest.mark.parametrize("height_offset", [-5, 0, 5])
    def test_a_helyorzo_sorra_ejtes_album_properties_parbeszedet_nyit_es_ok_utan_letrehoz(
        self, qml_app, qt_app, height_offset
    ):
        """#7102: a createAlbumFromDrop renderelt Album Properties ablakot nyit."""
        window, controller, _engine = qml_app
        vart_magassag = window.height() + height_offset
        window.setHeight(vart_magassag)
        assert var_feltetelre(
            qt_app, lambda: window.height() == vart_magassag, 5.0
        )
        assert var_feltetelre(qt_app, lambda: controller.photos.rowCount() >= 1, 5.0)

        before_date = QDateTime.currentDateTime().addSecs(-1).date()
        window.setProperty("selectedIndexes", [0])
        _emit(
            _child(window, "folderPane"),
            "newAlbumPhotosDropped",
            Q_ARG("QVariant", [0]),
        )

        dialog = _child(window, "toolbarNewAlbumPropertiesDialog")
        assert var_feltetelre(
            qt_app, lambda: dialog.property("opened") is True, 5.0
        ), "a helyőrző sorra ejtés nem nyitotta meg az Album Properties ablakot"
        assert dialog.property("title") == "Album Properties"
        assert controller.albums == [], "az album az OK előtt létrejött"
        assert _child(dialog, "folderPropertiesNameField").property("text") == "Untitled"
        assert dialog.property("currentDate") == before_date.toString(
            Qt.DateFormat.ISODate
        )
        assert _child(dialog, "folderPropertiesDateField").property("text")
        assert dialog.property("_dateValid") is True
        assert _child(dialog, "folderPropertiesLocation").property("text") == ""
        assert _child(dialog, "folderPropertiesDescription").property("text") == ""
        assert _child(dialog, "folderPropertiesUseMusic").property("checked") is False

        _emit(_child(dialog, "folderPropertiesOkButton"), "clicked")
        assert var_feltetelre(qt_app, lambda: len(controller.albums) == 1, 5.0), (
            "az OK nem hozta létre az albumot"
        )
        album = controller.albums[0]
        assert album["name"] == "Untitled"
        assert album["count"] == 1, "a ledobott kép nem lett albumtag"
        assert var_feltetelre(
            qt_app, lambda: controller.currentAlbumToken == album["token"], 5.0
        ), "az OK után nem az új album nyílt meg"
        assert controller.viewModeName == "album"
        assert controller.photos.rowCount() == 1

        photo_ini = Path(controller.photos.filePathAt(0)).parent / ".picasa.ini"
        assert f"albums={album['token']}" in photo_ini.read_text(encoding="utf-8")

    @pytest.mark.parametrize("height_offset", [-5, 0, 5])
    def test_a_helyorzo_sorra_ejtes_megse_utan_nem_valtoztat_semmin(
        self, qml_app, qt_app, height_offset
    ):
        window, controller, _engine = qml_app
        vart_magassag = window.height() + height_offset
        window.setHeight(vart_magassag)
        assert var_feltetelre(
            qt_app, lambda: window.height() == vart_magassag, 5.0
        )
        assert var_feltetelre(qt_app, lambda: controller.photos.rowCount() >= 1, 5.0)
        window.setProperty("selectedIndexes", [0])
        mappa = controller.currentFolder
        photo_ini = Path(mappa) / ".picasa.ini"
        ini_elotte = photo_ini.read_bytes() if photo_ini.exists() else None

        _emit(
            _child(window, "folderPane"),
            "newAlbumPhotosDropped",
            Q_ARG("QVariant", [0]),
        )
        dialog = _child(window, "toolbarNewAlbumPropertiesDialog")
        assert var_feltetelre(
            qt_app, lambda: dialog.property("opened") is True, 5.0
        ), "a helyőrző sorra ejtés nem nyitotta meg az Album Properties ablakot"
        assert controller.albums == []

        _emit(_child(dialog, "folderPropertiesCancelButton"), "clicked")
        assert var_feltetelre(
            qt_app, lambda: dialog.property("opened") is False, 5.0
        ), "a Mégse nem zárta be az Album Properties ablakot"
        assert controller.albums == []
        assert controller.currentAlbumToken == ""
        assert controller.viewModeName == "folder"
        assert controller.currentFolder == mappa
        assert controller.photos.rowCount() >= 1
        selected = window.property("selectedIndexes")
        if hasattr(selected, "toVariant"):
            selected = selected.toVariant()
        assert list(selected) == [0], "a Mégse megváltoztatta a kijelölést"
        assert (photo_ini.read_bytes() if photo_ini.exists() else None) == ini_elotte

    def test_ures_kijelolesnel_nem_tortenik_semmi(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        window.setProperty("selectedIndexes", [])

        _emit(
            _child(window, "folderPane"),
            "newAlbumPhotosDropped",
            Q_ARG("QVariant", []),
        )
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
            Q_ARG("QVariant", [1]),
        )
        qt_app.processEvents()

        counts = {a["token"]: a["count"] for a in controller.albums}
        assert counts.get(token) == 2

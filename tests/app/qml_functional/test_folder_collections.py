"""#320 első lépése: a bal hasáb öt Picasa-hű gyűjtemény-fejléce.

Az audit (docs/specs/ui-audit-mainwindow.md, mappafa szakasz) szerint a bal
hasáb gyökerén öt önálló, csukható gyűjtemény áll egymás alatt (Albumok,
Emberek, Projektek, Mappák, Egyéb), és csak a Mappák gyűjtemény tagolt
évszám-szakaszokra. Ez a teszt a FolderPane.qml öt fejlécét, a
nyitva/csukva állapot perzisztálását és a Mappák-tartalom sértetlenségét
ellenőrzi.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, QPointF


def _visual_items(item):
    for child in item.childItems():
        yield child
        yield from _visual_items(child)


class TestFiveCollectionHeaders:
    def test_five_headers_present_in_picasa_order(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        names = (
            "albumsHeader",
            "peopleHeader",
            "projectsHeader",
            "folderPaneHeader",
            "otherHeader",
        )
        headers = [window.findChild(QObject, name) for name in names]
        for name, header in zip(names, headers, strict=True):
            assert header is not None, f"{name} nem található"

        #: #1407: a Mappák fejléce a hasáb GYÖKERÉT nevezi meg (spec 4.2) —
        #: lapos nézetben „Default View", nem a gyűjtemény neve.
        labels = ("Albums", "People", "Projects", "Default View", "Other")
        for header, label in zip(headers, labels, strict=True):
            assert label in header.property("text")

    def test_default_collapsed_state_matches_spec(self, qml_app, qt_app):
        # collections.DEFAULT_COLLAPSED: albums+projects+folders nyitva, a
        # többi (tartalom nélküli) csukva. #1029: a Projektek azóta NEM
        # tartalom nélküli — a `P2category=Projects (internal)` mappák benne
        # állnak —, ezért az eredetihez hasonlóan nyitva indul.
        window, _controller, _ = qml_app
        expectations = {
            "albumsHeaderRow": False,
            "peopleHeaderRow": True,
            "projectsHeaderRow": False,
            "folderPaneHeaderRow": False,
            "otherHeaderRow": True,
        }
        for row_name, expected_collapsed in expectations.items():
            row = window.findChild(QObject, row_name)
            assert row is not None, f"{row_name} nem található"
            assert row.property("collapsed") is expected_collapsed


class TestCollectionToggle:
    def test_toggle_flips_state_and_persists_via_controller(self, qml_app, qt_app):
        window, controller, _ = qml_app
        row = window.findChild(QObject, "peopleHeaderRow")
        assert row is not None, "peopleHeaderRow nem található"
        assert controller.isCollectionCollapsed("people") is True

        QMetaObject.invokeMethod(row, "toggled")
        qt_app.processEvents()

        assert row.property("collapsed") is False
        assert controller.isCollectionCollapsed("people") is False

        QMetaObject.invokeMethod(row, "toggled")
        qt_app.processEvents()

        assert row.property("collapsed") is True
        assert controller.isCollectionCollapsed("people") is True

    def test_toggle_albums_hides_starred_row(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        starred = window.findChild(QObject, "starredItem")
        assert starred is not None, "starredItem nem található"
        assert starred.property("visible") is True

        row = window.findChild(QObject, "albumsHeaderRow")
        QMetaObject.invokeMethod(row, "toggled")
        qt_app.processEvents()

        assert starred.property("visible") is False

    def test_toggle_folders_hides_folder_list(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        folder_list = window.findChild(QObject, "folderListView")
        assert folder_list is not None, "folderListView nem található"
        assert folder_list.property("visible") is True

        row = window.findChild(QObject, "folderPaneHeaderRow")
        QMetaObject.invokeMethod(row, "toggled")
        qt_app.processEvents()

        assert folder_list.property("visible") is False


class TestFolderContentUnaffected:
    def test_search_result_row_precedes_starred_and_existing_albums(
        self, qml_app, qt_app
    ):
        window, controller, _ = qml_app
        header = window.findChild(QObject, "folderPaneHeader")
        assert header is not None, "folderPaneHeader nem található"
        #: #1407: a Mappák fejléce a hasáb GYÖKERÉT nevezi meg — lapos
        #: nézetben a mért „Default View" (spec 4.2)
        assert "Default View" in header.property("text")

        pane = window.findChild(QObject, "folderPane")
        albums_header = window.findChild(QObject, "albumsHeaderRow")
        assert pane is not None and albums_header is not None
        pane.setProperty(
            "albumsModel",
            [{"token": "existing-album", "name": "Existing album", "count": 2}],
        )
        qt_app.processEvents()
        album_count_before_search = albums_header.property("itemCount")

        controller.search("a")
        qt_app.processEvents()
        assert "Search results for" not in header.property("text")
        search_row = window.findChild(QObject, "searchResultsAlbumRow")
        search_text = window.findChild(QObject, "searchResultsAlbumText")
        starred_row = window.findChild(QObject, "starredItem")
        existing_album_row = next(
            item
            for item in _visual_items(window.contentItem())
            if item.objectName() == "albumItem_existing-album"
        )
        assert search_row is not None and search_row.isVisible()
        assert search_text is not None
        assert search_text.property("text") == 'Search results for "a" (1)'
        assert starred_row is not None and starred_row.isVisible()
        search_y = search_row.mapToScene(QPointF(0, 0)).y()
        starred_y = starred_row.mapToScene(QPointF(0, 0)).y()
        existing_album_y = existing_album_row.mapToScene(QPointF(0, 0)).y()
        assert search_y < starred_y < existing_album_y
        assert albums_header.property("itemCount") == album_count_before_search + 1

        controller.search("")
        qt_app.processEvents()
        assert not search_row.isVisible()
        assert starred_row.isVisible()
        #: #1407: a Mappák fejléce a hasáb GYÖKERÉT nevezi meg — lapos
        #: nézetben a mért „Default View" (spec 4.2)
        assert "Default View" in header.property("text")

    def test_empty_collections_show_zero_and_do_not_crash(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        for name in ("peopleHeader", "projectsHeader", "otherHeader"):
            header = window.findChild(QObject, name)
            assert header.property("text").endswith("(0)")
